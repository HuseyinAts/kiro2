#!/usr/bin/env python3
"""Bekci severity sayimi — #453 kalibrasyonunun ONCE/SONRA olcumu.

Neden bu script var: "mock/hardcoded idiyomlari CRITICAL sayiliyor" bir IDDIA.
Iddiayi kodu okuyarak degil, dedektoru KOSARAK dogrulamak gerekir
(.claude/rules/audit-methodology.md — "Kok neden de bir olcumdur").

Kullanim (backend/ dizininden):
    python scripts/quality/guard_severity_census.py
    python scripts/quality/guard_severity_census.py --corpus tests --limit 250

Cikti: (dedektor x severity) matrisi + bloklanan dosya sayisi. Fix oncesi ve
sonrasi ayni komut kosulur; fark FIX'IN DEGERIDIR.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import inspect
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]

from hooks.reward_hacking.base_detector import BaseDetector  # noqa: E402
from hooks.reward_hacking.detectors import (  # noqa: E402
    AssertTrueDetector,
    HardcodedTestDataDetector,
    MockAbuseDetector,
)
from hooks.reward_hacking.hook_manager import HookManager  # noqa: E402
from hooks.reward_hacking.models.detection_result import (  # noqa: E402
    DetectorConfig,
    GlobalConfig,
)

BACKEND = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# M1 — KALDIRMA DENEYI: `default_severity` dali erisilebilir mi?
# ---------------------------------------------------------------------------
def m1_default_severity_erisilebilir_mi() -> None:
    print("=" * 72)
    print("M1  default_severity dali ERISILEBILIR MI?")
    print("=" * 72)

    kaynak = inspect.getsource(BaseDetector._create_result)
    satir = next(s.strip() for s in kaynak.splitlines() if "severity =" in s)
    print(f"  yuklenen surum (inspect.getsource): {satir}")

    # Dalin kosulu: `if self.config`. Falsy olabilecek bir girdi var mi?
    print(f"  bool(DetectorConfig())            : {bool(DetectorConfig())}")
    d_none = MockAbuseDetector(config=None)
    print(
        f"  config=None -> self.config        : {type(d_none.config).__name__}"
        f" (bool={bool(d_none.config)})"
    )

    for cls in (MockAbuseDetector, HardcodedTestDataDetector, AssertTrueDetector):
        det = cls()
        sonuc = det._create_result(
            file_path="tests/test_x.py",
            line_number=1,
            code_snippet="MagicMock()",
            message="olcum",
            confidence=0.95,
        )
        print(
            f"  {cls.__name__:28s} beyan={det.default_severity:8s}"
            f" -> uretilen={sonuc.severity}"
            f"  {'ESLESMIYOR (dal olu)' if sonuc.severity != det.default_severity else 'eslesiyor'}"
        )

    # Paket YAML'i #454'te SILINDI. Gerekce olculdu: pre-push `--config`
    # gecmiyordu (GlobalConfig().detectors bos), ve elle yuklendiginde sonuc
    # birebir ayniydi (crit 64 / warn 658 / toplam 722, kume farki 0) — yani
    # tam no-op. Ayni severity'nin iki yerde yazili kalmasi #453'te kapatilan
    # "iki yerde yazili niyet, biri olu" kusurunun aynisiydi.
    print(
        f"\n  GlobalConfig().detectors          : {GlobalConfig().detectors!r}"
        "   <- bos: tek kaynak sinif beyani (#454)"
    )
    print()


# ---------------------------------------------------------------------------
# M2 — GERCEK KORPUS SAYIMI
# ---------------------------------------------------------------------------
# Bu gorevin KENDI urettigi dosyalar korpustan cikarilir. Aksi halde sirali
# ilk-N penceresi kayar ve ONCE/SONRA kollari FARKLI dosya kumesi olcer —
# ilk denemede tam bu oldu (hardcoded toplami 327 -> 325, fix'ten degil
# pencere kaymasindan). Bkz .claude/rules/audit-methodology.md
# "Olcum aletini dogrula": kontrol kolu bilinen sonucu vermiyorsa alet arizali.
_HARIC = ("test_severity_calibration.py",)


async def m2_korpus(corpus: str, limit: int) -> None:
    kok = BACKEND / corpus
    dosyalar = sorted(
        str(p)
        for p in kok.rglob("*.py")
        if "__pycache__" not in str(p) and p.name not in _HARIC
    )
    dosyalar = dosyalar[:limit]

    # Korpus imzasi: iki kol ayni imzayi vermiyorsa karsilastirma GECERSIZDIR.
    goreli = "\n".join(str(Path(d).relative_to(BACKEND)) for d in dosyalar)
    imza = hashlib.sha256(goreli.encode("utf-8")).hexdigest()[:12]

    print("=" * 72)
    print(f"M2  KORPUS SAYIMI  corpus={corpus}  dosya={len(dosyalar)}")
    print(f"    korpus imzasi: sha256[:12]={imza}  (kollar arasi AYNI olmali)")
    print("=" * 72)

    yonetici = HookManager(config=GlobalConfig(max_files=len(dosyalar) + 1))
    sonuc = await yonetici.run_hooks(dosyalar)

    matris: Counter[tuple[str, str]] = Counter()
    for r in sonuc.results:
        matris[(str(r.pattern_type), str(r.severity))] += 1

    tipler = sorted({t for t, _ in matris})
    print(f"  {'pattern_type':24s} {'CRITICAL':>9s} {'WARNING':>8s} {'INFO':>6s}")
    for t in tipler:
        print(
            f"  {t:24s} {matris[(t, 'CRITICAL')]:9d}"
            f" {matris[(t, 'WARNING')]:8d} {matris[(t, 'INFO')]:6d}"
        )
    print(f"  {'-' * 50}")
    print(
        f"  {'TOPLAM':24s} {sonuc.critical_count:9d}"
        f" {sonuc.warning_count:8d} {sonuc.info_count:6d}"
    )
    print(f"  exit_code={int(sonuc.exit_code)}  analiz_edilen={sonuc.files_analyzed}")

    # Dosya-bazli: kac dosya TEK BASINA push'u bloklar?
    bloklu = 0
    for dosya in dosyalar:
        tekil = await yonetici.run_hooks([dosya])
        if tekil.critical_count > 0:
            bloklu += 1
    print(f"  TEK BASINA push'u bloklayan dosya : {bloklu}/{len(dosyalar)}")
    print()


# ---------------------------------------------------------------------------
# M3 — IKI YONLU KANIT: gercek ihlal hala bloklar mi?
# ---------------------------------------------------------------------------
async def m3_iki_yonlu(tmp: Path) -> None:
    print("=" * 72)
    print("M3  IKI YONLU KANIT")
    print("=" * 72)

    ornekler = {
        "gercek_ihlal_assert_true": "def test_a():\n    assert True\n",
        "gercek_ihlal_bare_except": "def f():\n    try:\n        g()\n    except:\n        pass\n",
        "mock_idiyomu": (
            "from unittest.mock import MagicMock, patch\n\n\n"
            "def test_b():\n"
            "    m = MagicMock()\n"
            "    m.return_value = True\n"
            "    assert m() is True\n"
        ),
        "hardcoded_idiyomu": (
            "def test_c():\n"
            '    email = "test@test.com"\n'
            '    password = "test1234"\n'  # pragma: allowlist secret
            "    user_id = 1\n"
            "    assert email and password and user_id\n"
        ),
    }

    tmp.mkdir(parents=True, exist_ok=True)
    yonetici = HookManager()
    for ad, icerik in ornekler.items():
        dosya = tmp / f"test_{ad}.py"
        dosya.write_text(icerik, encoding="utf-8")
        sonuc = await yonetici.run_hooks([str(dosya)])
        etiket = "BLOKLAR" if sonuc.critical_count else "gecirir"
        print(
            f"  {ad:26s} exit={int(sonuc.exit_code)} crit={sonuc.critical_count:2d}"
            f" warn={sonuc.warning_count:2d}  -> {etiket}"
        )
        dosya.unlink()

    # Uretim kodunda hardcoded/mock dedektoru hic kosuyor mu?
    uretim = tmp / "servis.py"
    # pragma: allowlist secret  (asagidaki atama SAHTE — dedektorun test-disi
    # dosyayi hic taramadigini gostermek icin var; gercek bir kimlik bilgisi degil)
    uretim_kodu = 'def f():\n    password = "test1234"\n    return password\n'  # pragma: allowlist secret
    uretim.write_text(uretim_kodu, encoding="utf-8")
    sonuc = await HookManager().run_hooks([str(uretim)])
    print(
        f"  {'uretim_kodu_password':26s} exit={int(sonuc.exit_code)}"
        f" crit={sonuc.critical_count:2d} warn={sonuc.warning_count:2d}"
        "  <- hardcoded dedektoru test-disi dosyayi atlar"
    )
    uretim.unlink()
    print()


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default="tests")
    ap.add_argument("--limit", type=int, default=250)
    ap.add_argument("--skip-census", action="store_true")
    args = ap.parse_args()

    m1_default_severity_erisilebilir_mi()
    await m3_iki_yonlu(BACKEND / "scripts/quality/_census_tmp")
    if not args.skip_census:
        await m2_korpus(args.corpus, args.limit)
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
