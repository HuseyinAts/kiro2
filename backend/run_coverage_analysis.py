"""
Test Coverage Runner ve Reporter
Teknofest 2025 - YKS Hazırlık Platformu
"""

import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict


class CoverageRunner:
    """Test coverage çalıştırıcı ve raporlayıcı"""

    def __init__(self):
        self.backend_dir = Path.cwd()
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.report_dir = self.backend_dir / "coverage_reports"
        self.html_dir = self.backend_dir / "htmlcov"

        # Rapor dizinini oluştur
        self.report_dir.mkdir(exist_ok=True)

    def run_tests_with_coverage(self) -> Dict:
        """Testleri coverage ile çalıştır"""
        print("\n" + "=" * 80)
        print("🧪 TEST COVERAGE ÇALIŞTIRILIYOR")
        print("=" * 80)

        try:
            # Coverage'ı temizle
            subprocess.run(["python", "-m", "coverage", "erase"], capture_output=True)
            print("✅ Coverage cache temizlendi")

            # Testleri çalıştır
            print("\n📊 Testler çalıştırılıyor...")
            result = subprocess.run(
                [
                    "python",
                    "-m",
                    "coverage",
                    "run",
                    "--source",
                    ".",
                    "--omit",
                    "*/tests/*,*/test_*.py,*/venv/*,*/__pycache__/*",
                    "-m",
                    "pytest",
                    "tests/",
                    "-v",
                    "--tb=short",
                    "--ignore=tests/fixtures",
                    "--ignore=tests/performance",
                ],
                capture_output=True,
                text=True,
            )

            # JSON raporu oluştur
            subprocess.run(["python", "-m", "coverage", "json"], capture_output=True)

            # HTML raporu oluştur
            subprocess.run(["python", "-m", "coverage", "html"], capture_output=True)

            # Terminal raporu
            coverage_result = subprocess.run(
                ["python", "-m", "coverage", "report"], capture_output=True, text=True
            )

            print("\n📈 Coverage Raporu:")
            print(coverage_result.stdout)

            # Coverage.json oku
            coverage_file = self.backend_dir / "coverage.json"
            if coverage_file.exists():
                with open(coverage_file, "r") as f:
                    coverage_data = json.load(f)

                return coverage_data

        except Exception as e:
            print(f"❌ Hata: {e}")
            return {}

    def analyze_coverage(self, coverage_data: Dict) -> Dict:
        """Coverage verilerini analiz et"""
        print("\n" + "=" * 80)
        print("📊 COVERAGE ANALİZİ")
        print("=" * 80)

        analysis = {
            "total_coverage": 0,
            "high_coverage_modules": [],
            "low_coverage_modules": [],
            "zero_coverage_modules": [],
            "module_details": {},
        }

        if not coverage_data:
            return analysis

        # Genel coverage
        analysis["total_coverage"] = coverage_data.get("totals", {}).get(
            "percent_covered", 0
        )

        # Modül bazlı analiz
        files = coverage_data.get("files", {})

        for file_path, file_data in files.items():
            # Sadece proje dosyalarını al (test dosyalarını hariç tut)
            if "test" in file_path or "venv" in file_path:
                continue

            coverage_percent = file_data.get("summary", {}).get("percent_covered", 0)
            module_name = Path(file_path).name

            analysis["module_details"][module_name] = {
                "path": file_path,
                "coverage": coverage_percent,
                "missing_lines": file_data.get("summary", {}).get("missing_lines", 0),
                "covered_lines": file_data.get("summary", {}).get("covered_lines", 0),
            }

            # Kategorize et
            if coverage_percent >= 80:
                analysis["high_coverage_modules"].append(
                    {"name": module_name, "coverage": coverage_percent}
                )
            elif coverage_percent == 0:
                analysis["zero_coverage_modules"].append(
                    {"name": module_name, "path": file_path}
                )
            elif coverage_percent < 30:
                analysis["low_coverage_modules"].append(
                    {"name": module_name, "coverage": coverage_percent}
                )

        # Sıralama
        analysis["high_coverage_modules"].sort(
            key=lambda x: x["coverage"], reverse=True
        )
        analysis["low_coverage_modules"].sort(key=lambda x: x["coverage"])

        return analysis

    def generate_detailed_report(self, analysis: Dict):
        """Detaylı rapor oluştur"""
        report_file = self.report_dir / f"coverage_report_{self.timestamp}.md"

        report_content = f"""# Test Coverage Report
**Tarih:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Proje:** Teknofest 2025 - YKS Hazırlık Platformu

## 📊 Genel Özet

| Metrik | Değer |
|--------|-------|
| **Toplam Coverage** | %{analysis['total_coverage']:.2f} |
| **Hedef Coverage** | %80 |
| **Durum** | {'✅ Başarılı' if analysis['total_coverage'] >= 80 else '⚠️ İyileştirme Gerekli'} |

## 🏆 Yüksek Coverage Modülleri (≥80%)

| Modül | Coverage |
|-------|----------|
"""

        for module in analysis["high_coverage_modules"][:10]:
            report_content += f"| {module['name']} | %{module['coverage']:.2f} |\n"

        report_content += """

## ⚠️ Düşük Coverage Modülleri (<30%)

| Modül | Coverage | Öncelik |
|-------|----------|---------|
"""

        for module in analysis["low_coverage_modules"][:10]:
            priority = "🔴 Yüksek" if "service" in module["name"].lower() else "🟡 Orta"
            report_content += (
                f"| {module['name']} | %{module['coverage']:.2f} | {priority} |\n"
            )

        report_content += """

## ❌ Test Edilmemiş Modüller

| Modül | Yol |
|-------|-----|
"""

        for module in analysis["zero_coverage_modules"][:10]:
            report_content += f"| {module['name']} | {module['path']} |\n"

        # Kritik servisler analizi
        critical_services = [
            "sinav_motoru_service.py",
            "learning_style_service.py",
            "zpd_maarif_service.py",
            "irt_morfoloji_service.py",
            "soru_bankasi_service.py",
        ]

        report_content += """

## 🎯 Kritik Servisler Durumu

| Servis | Coverage | Durum |
|--------|----------|-------|
"""

        for service in critical_services:
            if service in analysis["module_details"]:
                cov = analysis["module_details"][service]["coverage"]
                status = "✅" if cov >= 80 else "⚠️" if cov >= 50 else "❌"
                report_content += f"| {service} | %{cov:.2f} | {status} |\n"
            else:
                report_content += f"| {service} | N/A | ❓ |\n"

        # Öneriler
        report_content += """

## 📈 İyileştirme Önerileri

"""

        if analysis["total_coverage"] < 30:
            report_content += """
### 🔴 Acil Eylem Gerekli
1. **Test Coverage %30'un altında!**
2. Kritik servislere odaklanın
3. Unit test sayısını artırın
4. Mock kullanımını geliştirin
"""
        elif analysis["total_coverage"] < 60:
            report_content += """
### 🟡 Orta Seviye İyileştirme
1. Integration testleri ekleyin
2. Edge case'leri test edin
3. Error handling testlerini artırın
"""
        else:
            report_content += """
### 🟢 İyi Durumda
1. Performance testleri ekleyin
2. End-to-end testleri geliştirin
3. Test kalitesini artırın
"""

        # Sonraki adımlar
        report_content += f"""

## 🚀 Sonraki Adımlar

1. **Kısa Vade (1 hafta)**
   - [ ] Zero coverage modülleri için temel testler
   - [ ] Kritik servislerde %50+ coverage
   - [ ] CI/CD pipeline entegrasyonu

2. **Orta Vade (2-4 hafta)**
   - [ ] Tüm servislerde %70+ coverage
   - [ ] Integration test suite
   - [ ] Performance benchmarks

3. **Uzun Vade (1-2 ay)**
   - [ ] %80+ genel coverage
   - [ ] Mutation testing
   - [ ] Full E2E test suite

## 📁 Raporlar

- **HTML Rapor:** {self.html_dir}/index.html
- **JSON Rapor:** coverage.json
- **Bu Rapor:** {report_file}

---
*Otomatik olarak oluşturulmuştur*
"""

        # Raporu kaydet
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report_content)

        print(f"\n✅ Detaylı rapor kaydedildi: {report_file}")

        return report_file

    def create_github_badge(self, coverage_percent: float):
        """GitHub için coverage badge oluştur"""
        color = "red"
        if coverage_percent >= 80:
            color = "brightgreen"
        elif coverage_percent >= 60:
            color = "yellow"
        elif coverage_percent >= 40:
            color = "orange"

        badge_url = (
            f"https://img.shields.io/badge/coverage-{coverage_percent:.1f}%25-{color}"
        )

        badge_md = f"[![Coverage]({badge_url})](htmlcov/index.html)"

        # README'ye ekle
        readme_path = self.backend_dir / "README.md"
        if readme_path.exists():
            with open(readme_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Badge'i güncelle veya ekle
            import re

            pattern = r"\[\!\[Coverage\]\(.*?\)\]\(.*?\)"

            if re.search(pattern, content):
                content = re.sub(pattern, badge_md, content)
            else:
                # README'nin başına ekle
                content = f"{badge_md}\n\n{content}"

            with open(readme_path, "w", encoding="utf-8") as f:
                f.write(content)

            print(f"✅ Coverage badge güncellendi: {coverage_percent:.1f}%")

    def run_comprehensive_coverage(self):
        """Kapsamlı coverage analizi çalıştır"""
        print("\n" + "=" * 80)
        print("🚀 KAPSAMLı TEST COVERAGE ANALİZİ")
        print("=" * 80)

        # 1. Testleri çalıştır
        coverage_data = self.run_tests_with_coverage()

        if not coverage_data:
            print("❌ Coverage verisi alınamadı!")
            return

        # 2. Analiz yap
        analysis = self.analyze_coverage(coverage_data)

        # 3. Özet göster
        print("\n" + "=" * 80)
        print("📊 COVERAGE ÖZETİ")
        print("=" * 80)
        print(f"Toplam Coverage: %{analysis['total_coverage']:.2f}")
        print(f"Yüksek Coverage Modülleri: {len(analysis['high_coverage_modules'])}")
        print(f"Düşük Coverage Modülleri: {len(analysis['low_coverage_modules'])}")
        print(f"Test Edilmemiş Modüller: {len(analysis['zero_coverage_modules'])}")

        # 4. Detaylı rapor oluştur
        report_file = self.generate_detailed_report(analysis)

        # 5. GitHub badge oluştur
        self.create_github_badge(analysis["total_coverage"])

        # 6. Başarı durumunu kontrol et
        if analysis["total_coverage"] >= 80:
            print("\n" + "=" * 80)
            print("🎉 BAŞARILI! Coverage hedefi aşıldı!")
            print("=" * 80)
            return True
        else:
            improvement_needed = 80 - analysis["total_coverage"]
            print("\n" + "=" * 80)
            print(f"⚠️ Coverage hedefine %{improvement_needed:.2f} kaldı!")
            print("=" * 80)

            # En kritik 5 modülü göster
            print("\n🎯 Öncelikli olarak test edilmesi gereken modüller:")
            for i, module in enumerate(analysis["zero_coverage_modules"][:5], 1):
                print(f"{i}. {module['name']}")

            return False


if __name__ == "__main__":
    runner = CoverageRunner()
    success = runner.run_comprehensive_coverage()
    sys.exit(0 if success else 1)
