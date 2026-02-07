#!/usr/bin/env python3
"""
KIRO2 Evaluation Runner

Tüm eval YAML dosyalarını okur ve çalıştırır.
Sonuçları JSON formatında raporlar.

Kullanım:
    python .claude/evals/runner.py                    # Tüm eval'leri çalıştır
    python .claude/evals/runner.py --eval security   # Belirli eval çalıştır
    python .claude/evals/runner.py --output results/ # Çıktı dizini belirt
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import subprocess
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@dataclass
class CheckResult:
    """Tek bir kontrol sonucu."""

    name: str
    description: str
    status: str  # pass, warn, fail, skip, error
    output: str = ""
    error: str = ""
    duration_ms: int = 0
    score: float = 0.0
    weight: int = 0
    threshold: float | None = None
    actual_value: float | None = None


@dataclass
class EvalResult:
    """Eval sonucu."""

    name: str
    description: str
    version: str
    timestamp: str
    status: str  # pass, warn, fail
    total_score: float
    max_score: float
    percentage: float
    checks: list[CheckResult] = field(default_factory=list)
    duration_ms: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class EvalRunner:
    """
    Evaluation runner sınıfı.

    YAML formatındaki eval tanımlarını okur ve çalıştırır.
    """

    def __init__(
        self,
        evals_dir: Path | str = ".claude/evals",
        output_dir: Path | str = ".claude/evals/results",
    ) -> None:
        """
        Runner başlat.

        Args:
            evals_dir: Eval YAML dosyalarının bulunduğu dizin
            output_dir: Sonuçların yazılacağı dizin
        """
        self.evals_dir = Path(evals_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results: list[EvalResult] = []

    def load_eval(self, name: str) -> dict[str, Any]:
        """
        Eval YAML dosyasını yükle.

        Args:
            name: Eval adı (dosya adı .yaml olmadan)

        Returns:
            Eval yapılandırması
        """
        yaml_path = self.evals_dir / f"{name}.yaml"

        if not yaml_path.exists():
            raise FileNotFoundError(f"Eval not found: {yaml_path}")

        with open(yaml_path, encoding="utf-8") as f:
            return yaml.safe_load(f)

    def list_evals(self) -> list[str]:
        """Mevcut eval listesi."""
        return [
            f.stem for f in self.evals_dir.glob("*.yaml")
            if not f.stem.startswith("_")
        ]

    async def run_check(self, check: dict[str, Any]) -> CheckResult:
        """
        Tek bir kontrol çalıştır.

        Args:
            check: Kontrol yapılandırması

        Returns:
            CheckResult
        """
        name = check.get("name", "unknown")
        description = check.get("description", "")
        command = check.get("command", "")
        timeout_ms = check.get("timeout", 60000)
        threshold = check.get("threshold")
        weight = check.get("weight", 1)

        start_time = time.time()

        try:
            # Komutu çalıştır
            result = await asyncio.wait_for(
                asyncio.create_subprocess_shell(
                    command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                ),
                timeout=timeout_ms / 1000,
            )

            stdout, stderr = await result.communicate()
            output = stdout.decode("utf-8", errors="replace")
            error = stderr.decode("utf-8", errors="replace")

            duration_ms = int((time.time() - start_time) * 1000)

            # Sonucu değerlendir
            if result.returncode == 0:
                status = "pass"
                score = float(weight)
            else:
                status = "fail"
                score = 0.0

            # Threshold kontrolü
            actual_value = None
            if threshold is not None:
                try:
                    # Output'tan sayısal değer çıkar
                    actual_value = float(output.strip().split()[-1].rstrip("%MKG"))
                    if actual_value <= threshold:
                        status = "pass"
                        score = float(weight)
                    else:
                        status = "fail"
                        score = 0.0
                except (ValueError, IndexError):
                    pass

            return CheckResult(
                name=name,
                description=description,
                status=status,
                output=output[:1000],  # Truncate
                error=error[:500] if error else "",
                duration_ms=duration_ms,
                score=score,
                weight=weight,
                threshold=threshold,
                actual_value=actual_value,
            )

        except asyncio.TimeoutError:
            return CheckResult(
                name=name,
                description=description,
                status="error",
                error=f"Timeout after {timeout_ms}ms",
                duration_ms=timeout_ms,
                score=0.0,
                weight=weight,
            )

        except Exception as e:
            return CheckResult(
                name=name,
                description=description,
                status="error",
                error=str(e),
                duration_ms=int((time.time() - start_time) * 1000),
                score=0.0,
                weight=weight,
            )

    async def run_eval(self, name: str) -> EvalResult:
        """
        Eval çalıştır.

        Args:
            name: Eval adı

        Returns:
            EvalResult
        """
        logger.info(f"Running eval: {name}")
        start_time = time.time()

        try:
            config = self.load_eval(name)
        except FileNotFoundError as e:
            return EvalResult(
                name=name,
                description="",
                version="",
                timestamp=datetime.now().isoformat(),
                status="error",
                total_score=0,
                max_score=0,
                percentage=0,
                metadata={"error": str(e)},
            )

        checks = config.get("checks", [])
        scoring = config.get("scoring", {})

        # Kontrolleri çalıştır
        check_results = []
        for check in checks:
            result = await self.run_check(check)
            check_results.append(result)
            logger.info(f"  {result.name}: {result.status}")

        # Skor hesapla
        total_score = sum(c.score for c in check_results)
        max_score = sum(c.weight for c in check_results)
        percentage = (total_score / max_score * 100) if max_score > 0 else 0

        # Durum belirle
        pass_threshold = scoring.get("pass", 80)
        warn_threshold = scoring.get("warn", 60)

        if percentage >= pass_threshold:
            status = "pass"
        elif percentage >= warn_threshold:
            status = "warn"
        else:
            status = "fail"

        duration_ms = int((time.time() - start_time) * 1000)

        eval_result = EvalResult(
            name=name,
            description=config.get("description", ""),
            version=config.get("version", "1.0.0"),
            timestamp=datetime.now().isoformat(),
            status=status,
            total_score=total_score,
            max_score=max_score,
            percentage=round(percentage, 2),
            checks=check_results,
            duration_ms=duration_ms,
        )

        self.results.append(eval_result)
        return eval_result

    async def run_all(self, eval_names: list[str] | None = None) -> list[EvalResult]:
        """
        Tüm eval'leri çalıştır.

        Args:
            eval_names: Çalıştırılacak eval listesi (None=hepsi)

        Returns:
            Sonuç listesi
        """
        if eval_names is None:
            eval_names = self.list_evals()

        results = []
        for name in eval_names:
            result = await self.run_eval(name)
            results.append(result)

        return results

    def save_results(self, filename: str | None = None) -> Path:
        """
        Sonuçları kaydet.

        Args:
            filename: Dosya adı (opsiyonel)

        Returns:
            Kaydedilen dosya yolu
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"eval-results-{timestamp}.json"

        output_path = self.output_dir / filename

        results_data = {
            "timestamp": datetime.now().isoformat(),
            "total_evals": len(self.results),
            "passed": sum(1 for r in self.results if r.status == "pass"),
            "warned": sum(1 for r in self.results if r.status == "warn"),
            "failed": sum(1 for r in self.results if r.status == "fail"),
            "results": [asdict(r) for r in self.results],
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Results saved to: {output_path}")
        return output_path

    def print_summary(self) -> None:
        """Özet yazdır."""
        print("\n" + "=" * 60)
        print("KIRO2 EVALUATION SUMMARY")
        print("=" * 60)

        for result in self.results:
            status_icon = {
                "pass": "✅",
                "warn": "⚠️",
                "fail": "❌",
                "error": "💥",
            }.get(result.status, "❓")

            print(f"\n{status_icon} {result.name}: {result.status.upper()}")
            print(f"   Score: {result.total_score}/{result.max_score} ({result.percentage}%)")
            print(f"   Duration: {result.duration_ms}ms")

            for check in result.checks:
                check_icon = "✓" if check.status == "pass" else "✗"
                print(f"     {check_icon} {check.name}: {check.status}")

        print("\n" + "=" * 60)
        passed = sum(1 for r in self.results if r.status == "pass")
        total = len(self.results)
        print(f"Total: {passed}/{total} passed")
        print("=" * 60 + "\n")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="KIRO2 Evaluation Runner")
    parser.add_argument(
        "--eval", "-e",
        type=str,
        nargs="*",
        help="Specific eval(s) to run",
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List available evals",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=".claude/evals/results",
        help="Output directory",
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Don't save results to file",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Quiet mode (less output)",
    )

    args = parser.parse_args()

    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)

    runner = EvalRunner(output_dir=args.output)

    if args.list:
        print("Available evals:")
        for name in runner.list_evals():
            print(f"  - {name}")
        return

    # Eval'leri çalıştır
    eval_names = args.eval if args.eval else None
    await runner.run_all(eval_names)

    # Özet yazdır
    runner.print_summary()

    # Sonuçları kaydet
    if not args.no_save:
        runner.save_results()

    # Exit code
    failed = any(r.status == "fail" for r in runner.results)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    asyncio.run(main())
