"""İddia kütüğü bekçisini MUTASYONLA çivile.

NEDEN
-----
`.claude/rules/audit-methodology.md` (1 Ağu 2026): geçen bir test, yük taşıdığını
KANITLAMAZ. 8 testin 6'sı fix'ten ÖNCE de geçiyordu ("vakum test").

Ayrıca aynı kural: mutasyonu KABUK TIRNAĞIYLA uygulamak dosyaya syntax hatası
yazar; sonuç `failed` değil `error` olur ve ölçüm GEÇERSİZDİR. Bu yüzden
mutasyon Python ile, dosya içeriği üzerinden yapılır.

KULLANIM
--------
    python scripts/mutate_iddia_kutugu.py

Her mutasyon: uygula -> pytest koştur -> `failed` mi `error` mi bak -> GERİ AL
-> git ile geri alımı DOĞRULA (verification.md: "Geri alım bir iddiadır").
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DEPO = Path(__file__).resolve().parents[1]
KUTUK = DEPO / "docs" / "audits" / "2026-08-12_25uzman" / "iddialar.yaml"
TEST = "tests/audit/test_iddia_kutugu.py"

# (ad, hedef_test, eski_metin, yeni_metin)
MUTASYONLAR = [
    (
        "M1 kanitsiz durum",
        "test_kanitsiz_durum_yasak",
        "  severity_olculen: null\n  durum: beklemede\n  dogrulama:\n    - \"sed -n '1,60p' backend/core/osym_exam_engine.py",
        "  severity_olculen: null\n  durum: dogrulandi\n  dogrulama:\n    - \"sed -n '1,60p' backend/core/osym_exam_engine.py",
    ),
    (
        "M2 gecersiz severity",
        "test_severity_gecerli",
        "  severity_iddia: P0\n  severity_olculen: null\n  durum: beklemede\n  on_bulgu: |\n    12 Ağu ön ölçümü: socratic",
        "  severity_iddia: P9\n  severity_olculen: null\n  durum: beklemede\n  on_bulgu: |\n    12 Ağu ön ölçümü: socratic",
    ),
    (
        "M3 tekrarlanan id",
        "test_id_benzersiz",
        "- id: U02\n  uzman: \"Piotr Woźniak",
        "- id: U01\n  uzman: \"Piotr Woźniak",
    ),
    (
        "M4 uygulandi ama commitsiz",
        "test_uygulandi_commit_ve_test_ister",
        "  durum: dogrulandi\n  kanit: \"sed -n '61p' .claude/settings.json",
        "  durum: uygulandi\n  kanit: \"sed -n '61p' .claude/settings.json",
    ),
    (
        "M5 stakes dili degistirildi",
        "test_stakes_sabit",
        "Bulgun ne olursa olsun kimse cezalandırılmaz",
        "Bulgun yanlissa sorumlusun ve gorev iptal edilir",
    ),
    (
        "M6 ankraj dosyasi yok",
        "test_ankraj_dosyalari_var",
        'ankraj: "backend/core/quality_gate.py:68-80',
        'ankraj: "backend/core/OLMAYAN_DOSYA.py:68-80',
    ),
]


def kostur(test_adi: str) -> tuple[bool, bool, str]:
    """(failed_var, error_var, ozet) döndürür."""
    p = subprocess.run(
        # DIKKAT: xdist'i KAPATMA. backend/pytest.ini addopts icinde
        # `-n --dist=loadscope` var; xdist kapatilinca pytest "unrecognized
        # arguments" usage-error verir ve olcum GECERSIZ olur (1 Agu 2026 dersi:
        # 'error' donen mutasyon testin yuk tasidigini KANITLAMAZ).
        [sys.executable, "-m", "pytest", f"{TEST}::{test_adi}", "-q", "--no-header",
         "-p", "no:cacheprovider"],
        cwd=DEPO / "backend",
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    cikti = (p.stdout or "") + (p.stderr or "")
    son = [s for s in cikti.splitlines() if s.strip()][-1] if cikti.strip() else "<bos>"
    return ("failed" in cikti), ("error" in cikti.lower() and "failed" not in cikti), son


def geri_alim_dogru(orijinal: str) -> bool:
    """Geri alim BIR IDDIADIR — icerigi birebir karsilastirarak DOGRULA.

    Not: kutuk henuz git-takipli olmayabilir; `git checkout --` bu durumda
    sessizce hicbir sey yapmaz. Bu yuzden dogrulama icerik uzerinden yapilir
    (verification.md: "diff ile dogrulanmayan geri alim yapilmis sayilmaz").
    """
    return KUTUK.read_text(encoding="utf-8") == orijinal


def main() -> int:
    orijinal = KUTUK.read_text(encoding="utf-8")
    print(f"Kutuk: {KUTUK.relative_to(DEPO)}  ({len(orijinal)} bayt)\n")

    gecerli = gecersiz = 0
    for ad, test_adi, eski, yeni in MUTASYONLAR:
        if eski not in orijinal:
            print(f"[ANKRAJ YOK] {ad:34} -> mutasyon uygulanamadi, OLCUM GECERSIZ")
            gecersiz += 1
            continue

        KUTUK.write_text(orijinal.replace(eski, yeni, 1), encoding="utf-8")
        failed, error, son = kostur(test_adi)
        KUTUK.write_text(orijinal, encoding="utf-8")

        if error:
            print(f"[GECERSIZ ] {ad:34} -> 'error' (failed degil): {son}")
            gecersiz += 1
        elif failed:
            print(f"[CIVILENDI] {ad:34} -> {test_adi} FAIL verdi")
            gecerli += 1
        else:
            print(f"[VAKUM    ] {ad:34} -> mutasyona ragmen GECTI, test yuk TASIMIYOR")
            gecersiz += 1

    # Son durum: dosya birebir orijinal mi
    KUTUK.write_text(orijinal, encoding="utf-8")
    temiz = geri_alim_dogru(orijinal)
    print(f"\nCivilenen: {gecerli}/{len(MUTASYONLAR)}   Gecersiz: {gecersiz}")
    print(f"Geri alim DOGRULANDI (icerik birebir): {temiz}")
    return 0 if (gecerli == len(MUTASYONLAR) and temiz) else 1


if __name__ == "__main__":
    raise SystemExit(main())
