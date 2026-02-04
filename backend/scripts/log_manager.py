"""
Log Management CLI Tool - Teknofest 2025 Eğitim Eylemci Platformu
Log dosyalarının yönetimi ve analizi için komut satırı aracı
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import click

# Backend modüllerini import et
sys.path.append(str(Path(__file__).parent.parent))

from core.log_config import LogAnalyzer, LogRetentionManager
from core.structured_logger import LogCategory


@click.group()
def cli():
    """Teknofest 2025 Eğitim Eylemci Platformu - Log Yönetim Aracı"""


@cli.command()
@click.option("--log-dir", default="logs", help="Log dosyalarının bulunduğu dizin")
@click.option("--retention-days", default=30, help="Kaç günlük log saklanacak")
@click.option(
    "--dry-run", is_flag=True, help="Sadece hangi dosyaların silineceğini göster"
)
def cleanup(log_dir: str, retention_days: int, dry_run: bool):
    """Eski log dosyalarını temizle"""

    click.echo(f"🧹 Log temizliği başlatılıyor...")
    click.echo(f"[FOLDER] Log dizini: {log_dir}")
    click.echo(f"📅 Saklama süresi: {retention_days} gün")

    manager = LogRetentionManager(log_dir)

    if dry_run:
        click.echo("[MAG] Dry-run modu: Sadece analiz yapılıyor...")

        # Silinecek dosyaları listele
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        log_path = Path(log_dir)

        if not log_path.exists():
            click.echo("[X] Log dizini bulunamadı!")
            return

        old_files = []
        for log_file in log_path.glob("*.log*"):
            try:
                file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
                if file_time < cutoff_date:
                    old_files.append(
                        {
                            "file": str(log_file),
                            "size": log_file.stat().st_size,
                            "modified": file_time.isoformat(),
                        }
                    )
            except Exception:
                continue

        if old_files:
            click.echo(f"🗑️  Silinecek dosyalar ({len(old_files)} adet):")
            for file_info in old_files:
                size_mb = file_info["size"] / (1024 * 1024)
                click.echo(
                    f"   - {file_info['file']} ({size_mb:.2f} MB, {file_info['modified']})"
                )
        else:
            click.echo("[CHECK] Silinecek eski dosya bulunamadı")

    else:
        deleted_files = manager.cleanup_old_logs(retention_days)

        if deleted_files:
            click.echo(f"[CHECK] {len(deleted_files)} dosya silindi:")
            for file_path in deleted_files:
                click.echo(f"   - {file_path}")
        else:
            click.echo("[CHECK] Silinecek eski dosya bulunamadı")


@cli.command()
@click.option("--log-dir", default="logs", help="Log dosyalarının bulunduğu dizin")
@click.option("--days-old", default=7, help="Kaç günden eski dosyalar sıkıştırılacak")
def compress(log_dir: str, days_old: int):
    """Eski log dosyalarını sıkıştır"""

    click.echo(f"🗜️  Log sıkıştırma başlatılıyor...")
    click.echo(f"[FOLDER] Log dizini: {log_dir}")
    click.echo(f"📅 Sıkıştırma yaşı: {days_old} gün")

    manager = LogRetentionManager(log_dir)
    compressed_files = manager.compress_old_logs(days_old)

    if compressed_files:
        click.echo(f"[CHECK] {len(compressed_files)} dosya sıkıştırıldı:")
        for file_path in compressed_files:
            click.echo(f"   - {file_path}")
    else:
        click.echo("[CHECK] Sıkıştırılacak dosya bulunamadı")


@cli.command()
@click.option("--log-dir", default="logs", help="Log dosyalarının bulunduğu dizin")
def sizes(log_dir: str):
    """Log dosya boyutlarını göster"""

    click.echo(f"[CHART] Log dosya boyutları:")
    click.echo(f"[FOLDER] Log dizini: {log_dir}")

    manager = LogRetentionManager(log_dir)
    file_sizes = manager.get_log_file_sizes()

    if not file_sizes:
        click.echo("[X] Log dosyası bulunamadı!")
        return

    total_size = 0
    sorted_files = sorted(file_sizes.items(), key=lambda x: x[1], reverse=True)

    click.echo("\n[CLIPBOARD] Dosya listesi (boyuta göre sıralı):")
    for file_path, size in sorted_files:
        size_mb = size / (1024 * 1024)
        total_size += size
        click.echo(f"   {size_mb:8.2f} MB - {Path(file_path).name}")

    total_mb = total_size / (1024 * 1024)
    click.echo(f"\n[FLOPPY] Toplam boyut: {total_mb:.2f} MB ({len(file_sizes)} dosya)")


@cli.command()
@click.option("--log-dir", default="logs", help="Log dosyalarının bulunduğu dizin")
@click.option("--hours", default=24, help="Kaç saatlik veri analiz edilecek")
@click.option("--output", help="Sonuçları JSON dosyasına kaydet")
def analyze_errors(log_dir: str, hours: int, output: str):
    """Hata kalıplarını analiz et"""

    click.echo(f"[MAG] Hata analizi başlatılıyor...")
    click.echo(f"[FOLDER] Log dizini: {log_dir}")
    click.echo(f"⏰ Analiz süresi: Son {hours} saat")

    analyzer = LogAnalyzer(log_dir)
    patterns = analyzer.analyze_error_patterns(hours)

    click.echo(f"\n[CHART] Hata Analizi Sonuçları:")
    click.echo(f"🔴 Toplam hata sayısı: {patterns['total_errors']}")

    if patterns["error_types"]:
        click.echo(f"\n🏷️  En çok görülen hata tipleri:")
        for error_type, count in patterns["top_errors"][:5]:
            click.echo(f"   {count:3d}x - {error_type}")

    if patterns["error_endpoints"]:
        click.echo(f"\n[GLOBE] En çok hata alan endpoint'ler:")
        sorted_endpoints = sorted(
            patterns["error_endpoints"].items(), key=lambda x: x[1], reverse=True
        )[:5]
        for endpoint, count in sorted_endpoints:
            click.echo(f"   {count:3d}x - {endpoint}")

    if patterns["error_timeline"]:
        click.echo(f"\n[TRENDING_UP] Saatlik hata dağılımı:")
        for timeline_entry in patterns["error_timeline"][-12:]:  # Son 12 saat
            click.echo(f"   {timeline_entry['hour']}: {timeline_entry['count']} hata")

    # JSON çıktısı
    if output:
        with open(output, "w", encoding="utf-8") as f:
            json.dump(patterns, f, ensure_ascii=False, indent=2, default=str)
        click.echo(f"\n[FLOPPY] Sonuçlar kaydedildi: {output}")


@cli.command()
@click.option("--log-dir", default="logs", help="Log dosyalarının bulunduğu dizin")
@click.option("--hours", default=24, help="Kaç saatlik veri analiz edilecek")
@click.option("--output", help="Sonuçları JSON dosyasına kaydet")
def analyze_performance(log_dir: str, hours: int, output: str):
    """Performans metriklerini analiz et"""

    click.echo(f"[LIGHTNING] Performans analizi başlatılıyor...")
    click.echo(f"[FOLDER] Log dizini: {log_dir}")
    click.echo(f"⏰ Analiz süresi: Son {hours} saat")

    analyzer = LogAnalyzer(log_dir)
    metrics = analyzer.get_performance_metrics(hours)

    click.echo(f"\n[CHART] Performans Analizi Sonuçları:")
    click.echo(f"[TRENDING_UP] Toplam istek sayısı: {metrics['request_count']}")
    click.echo(f"⏱️  Ortalama yanıt süresi: {metrics['avg_response_time']:.2f} ms")

    if metrics["status_codes"]:
        click.echo(f"\n🚦 HTTP Status Code Dağılımı:")
        for status_code, count in sorted(metrics["status_codes"].items()):
            percentage = (
                (count / metrics["request_count"]) * 100
                if metrics["request_count"] > 0
                else 0
            )
            click.echo(f"   {status_code}: {count:4d} ({percentage:5.1f}%)")

    if metrics["slow_requests"]:
        click.echo(
            f"\n🐌 Yavaş istekler (>2 saniye) - {len(metrics['slow_requests'])} adet:"
        )
        for slow_req in metrics["slow_requests"][:10]:  # İlk 10 tanesi
            click.echo(
                f"   {slow_req['duration_ms']:7.0f}ms - {slow_req['method']} {slow_req['endpoint']}"
            )

    if metrics["endpoint_performance"]:
        click.echo(f"\n[TARGET] En yavaş endpoint'ler:")
        sorted_endpoints = sorted(
            metrics["endpoint_performance"].items(),
            key=lambda x: x[1]["avg_time"],
            reverse=True,
        )[:10]

        for endpoint, perf_data in sorted_endpoints:
            if perf_data["count"] > 0:
                click.echo(
                    f"   {perf_data['avg_time']:7.1f}ms - {endpoint} ({perf_data['count']} istek)"
                )

    # JSON çıktısı
    if output:
        with open(output, "w", encoding="utf-8") as f:
            json.dump(metrics, f, ensure_ascii=False, indent=2, default=str)
        click.echo(f"\n[FLOPPY] Sonuçlar kaydedildi: {output}")


@cli.command()
@click.option("--log-dir", default="logs", help="Log dosyalarının bulunduğu dizin")
@click.option(
    "--level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    help="Filtrelenecek log seviyesi",
)
@click.option(
    "--category",
    type=click.Choice([cat.value for cat in LogCategory]),
    help="Filtrelenecek log kategorisi",
)
@click.option("--hours", default=1, help="Kaç saatlik veri gösterilecek")
@click.option("--tail", default=50, help="Kaç satır gösterilecek")
def tail_logs(log_dir: str, level: str, category: str, hours: int, tail: int):
    """Log dosyalarını canlı takip et"""

    click.echo(f"👁️  Log takibi başlatılıyor...")
    click.echo(f"[FOLDER] Log dizini: {log_dir}")

    if level:
        click.echo(f"🏷️  Seviye filtresi: {level}")
    if category:
        click.echo(f"📂 Kategori filtresi: {category}")

    log_file = Path(log_dir) / "teknofest-platform.log"

    if not log_file.exists():
        click.echo("[X] Log dosyası bulunamadı!")
        return

    cutoff_time = datetime.now() - timedelta(hours=hours)

    try:
        with open(log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

            # Son N satırı al ve filtrele
            recent_logs = []
            for line in lines[-tail * 2 :]:  # Biraz fazla al, filtreleyeceğiz
                try:
                    log_data = json.loads(line.strip())

                    # Zaman filtresi
                    log_time = datetime.fromisoformat(log_data.get("timestamp", ""))
                    if log_time < cutoff_time:
                        continue

                    # Seviye filtresi
                    if level and log_data.get("level") != level:
                        continue

                    # Kategori filtresi
                    if category and log_data.get("category") != category:
                        continue

                    recent_logs.append(log_data)

                except (json.JSONDecodeError, ValueError):
                    continue

            # Son N tanesini göster
            recent_logs = recent_logs[-tail:]

            click.echo(f"\n[CLIPBOARD] Son {len(recent_logs)} log kaydı:")
            click.echo("=" * 80)

            for log_entry in recent_logs:
                timestamp = log_entry.get("timestamp", "")
                level_str = log_entry.get("level", "INFO")
                message = log_entry.get("message", "")
                category_str = log_entry.get("category", "system")

                # Renk kodları
                level_colors = {
                    "DEBUG": "blue",
                    "INFO": "green",
                    "WARNING": "yellow",
                    "ERROR": "red",
                    "CRITICAL": "magenta",
                }

                color = level_colors.get(level_str, "white")

                click.echo(
                    f"{timestamp} "
                    f"{click.style(level_str, fg=color, bold=True):8s} "
                    f"{category_str:12s} "
                    f"{message}"
                )

                # Ek bilgiler varsa göster
                extra_info = []
                if "user_id" in log_entry:
                    extra_info.append(f"user:{log_entry['user_id']}")
                if "request_id" in log_entry:
                    extra_info.append(f"req:{log_entry['request_id'][:8]}")
                if "duration_ms" in log_entry:
                    extra_info.append(f"duration:{log_entry['duration_ms']:.1f}ms")

                if extra_info:
                    click.echo(f"{'':25s} └─ {' | '.join(extra_info)}")

    except Exception as e:
        click.echo(f"[X] Log okuma hatası: {e}")


@cli.command()
@click.option("--log-dir", default="logs", help="Log dosyalarının bulunduğu dizin")
def dashboard(log_dir: str):
    """Log dashboard - genel durum özeti"""

    click.echo("🎛️  Teknofest 2025 Eğitim Eylemci Platformu - Log Dashboard")
    click.echo("=" * 70)

    # Dosya boyutları
    manager = LogRetentionManager(log_dir)
    file_sizes = manager.get_log_file_sizes()

    if file_sizes:
        total_size = sum(file_sizes.values()) / (1024 * 1024)
        click.echo(
            f"[FLOPPY] Toplam log boyutu: {total_size:.2f} MB ({len(file_sizes)} dosya)"
        )
    else:
        click.echo("[X] Log dosyası bulunamadı!")
        return

    # Son 24 saatlik hata analizi
    analyzer = LogAnalyzer(log_dir)
    error_patterns = analyzer.analyze_error_patterns(24)

    click.echo(f"🔴 Son 24 saatte {error_patterns['total_errors']} hata")

    if error_patterns["top_errors"]:
        top_error = error_patterns["top_errors"][0]
        click.echo(f"🏷️  En çok görülen hata: {top_error[0]} ({top_error[1]}x)")

    # Performans metrikleri
    perf_metrics = analyzer.get_performance_metrics(24)

    click.echo(
        f"[TRENDING_UP] Son 24 saatte {perf_metrics['request_count']} API çağrısı"
    )
    click.echo(f"⏱️  Ortalama yanıt süresi: {perf_metrics['avg_response_time']:.2f} ms")

    if perf_metrics["slow_requests"]:
        click.echo(f"🐌 {len(perf_metrics['slow_requests'])} yavaş istek (>2s)")

    # Sistem durumu
    success_rate = 0
    if perf_metrics["status_codes"]:
        total_requests = sum(perf_metrics["status_codes"].values())
        success_requests = sum(
            count
            for status, count in perf_metrics["status_codes"].items()
            if 200 <= int(status) < 400
        )
        success_rate = (
            (success_requests / total_requests) * 100 if total_requests > 0 else 0
        )

    status_color = (
        "green" if success_rate >= 95 else "yellow" if success_rate >= 90 else "red"
    )
    click.echo(
        f"[CHECK] Başarı oranı: {click.style(f'{success_rate:.1f}%', fg=status_color, bold=True)}"
    )

    click.echo("=" * 70)


if __name__ == "__main__":
    cli()
