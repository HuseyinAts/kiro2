"""
KIRO2 -- Temiz Kopya Guvenlik Olcumu (PR #62 sonrasi backlog, Faz 4)

`docs/guvenlik-borcu.md`'nin kendi "Olcum yontemi" notunu script'e doker:
canli/kirli calisma dizini (ornek: 16.339 dosya, `.venv` dahil) yerine HEAD'in
(veya verilen bir ref'in) temiz bir `git worktree` kopyasini cikarir --
CI'nin `actions/checkout` ile gordugu kumeyle ayni (dogrulanan ornek: 2604
takipli `backend/**/*.py` dosyasi) -- ve bandit + checkov'u ORADA calistirir.

Belgelenmis CI komutlari (docs/guvenlik-borcu.md SS 1-2), degistirilmeden
korunur, sadece JSON cikti icin `-f json`/`-o json` eklenir:

    Bandit  : bandit -r backend/ -ll                (MEDIUM+ siddet)
    Checkov : checkov -d . --framework all

NOT: Bandit/checkov bulgu bulunca (bos olmayan sonuc) exit code'u NONZERO
dondurur -- bu bir ARAC HATASI DEGIL, beklenen davranistir. Bu script bir
CI kapisi degil, bir OLCUM aracidir: exit 0, "bulgu yok" anlamina gelmez --
ciktidaki `toplam_bulgu`/`toplam_failed` sayilarina bak.

Checkov'un `-o json --output-file-path <dir>` ciktisi AMPIRIK OLARAK
dogrulandi (29 Agu 2026, /tmp/verify_test ve /tmp/verify_test2):
  - Her zaman tam olarak `<dir>/results_json.json` adiyla yazilir.
  - Tek framework eslesirse TEK dict, birden fazla framework (ornek:
    dockerfile + github_actions) eslesirse dict LISTESI yazar. Konsol
    stdout'u da bulgu miktarina gore degisken/guvenilmez oldugundan
    (bos sonucta kompakt ozet, dolu sonucta tam JSON dokumu) bu script
    SADECE dosyayi okur, stdout'a guvenmez.

Kullanim:
    python backend/scripts/temiz_kopya_guvenlik_olcumu.py
    python backend/scripts/temiz_kopya_guvenlik_olcumu.py --ref HEAD~1
    python backend/scripts/temiz_kopya_guvenlik_olcumu.py --keep-worktree
    python backend/scripts/temiz_kopya_guvenlik_olcumu.py --out-dir /tmp/deneme
"""

from __future__ import annotations

# nosec B404 gerekcesi: ic arac scripti; asagidaki tum subprocess cagrilari
# sabit literal komut listeleri calistirir (git/bandit/checkov), shell=True
# yok, kullanici girdisi komut argumanlarina hic ulasmaz.
import argparse
import json
import subprocess  # nosec B404
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Saf ozetleme fonksiyonlari -- disk/subprocess YOK, dogrudan unit-test edilebilir.
# ---------------------------------------------------------------------------


def bandit_json_ozetle(veri: dict[str, Any]) -> dict[str, Any]:
    """Bandit'in `-f json` ciktisini (yuklenmis dict) ozetler."""
    sonuclar = veri.get("results", [])
    siddet_dagilimi: dict[str, int] = {}
    for r in sonuclar:
        siddet = r.get("issue_severity", "UNKNOWN")
        siddet_dagilimi[siddet] = siddet_dagilimi.get(siddet, 0) + 1
    return {
        "toplam_bulgu": len(sonuclar),
        "siddet_dagilimi": siddet_dagilimi,
        "arac_hatasi_sayisi": len(veri.get("errors", [])),
        "bulgular": [
            {
                "test_id": r.get("test_id"),
                "siddet": r.get("issue_severity"),
                "guven": r.get("issue_confidence"),
                "dosya": r.get("filename"),
                "satir": r.get("line_number"),
                "mesaj": r.get("issue_text"),
            }
            for r in sonuclar
        ],
    }


def checkov_json_ozetle(veri: Any) -> dict[str, Any]:
    """Checkov'un `-o json` ciktisini ozetler.

    `veri`, tek bir dict OYA da dict listesi olabilir (bkz. modul docstring'i
    -- ampirik olarak dogrulanan checkov davranisi). Her iki bicimi de kabul
    eder; tekil dict'i tek elemanli listeye normalize ederek isler.
    """
    parcalar = veri if isinstance(veri, list) else [veri]
    framework_ozetleri = []
    toplam_passed = 0
    toplam_failed = 0
    toplam_skipped = 0
    basarisiz_kontroller = []
    for parca in parcalar:
        framework = parca.get("check_type", "bilinmeyen")
        ozet = parca.get("summary", {})
        toplam_passed += ozet.get("passed", 0)
        toplam_failed += ozet.get("failed", 0)
        toplam_skipped += ozet.get("skipped", 0)
        framework_ozetleri.append({"framework": framework, "ozet": ozet})
        for fc in parca.get("results", {}).get("failed_checks", []):
            basarisiz_kontroller.append(
                {
                    "framework": framework,
                    "check_id": fc.get("check_id"),
                    "check_name": fc.get("check_name"),
                    "dosya": fc.get("file_path"),
                    "kaynak": fc.get("resource"),
                }
            )
    return {
        "toplam_passed": toplam_passed,
        "toplam_failed": toplam_failed,
        "toplam_skipped": toplam_skipped,
        "framework_sayisi": len(parcalar),
        "framework_ozetleri": framework_ozetleri,
        "basarisiz_kontroller": basarisiz_kontroller,
    }


# ---------------------------------------------------------------------------
# Orkestrasyon -- git worktree, subprocess, dosya IO.
# ---------------------------------------------------------------------------


def _calistir(komut: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    """Alt-komutu calistirir. `check=True` KULLANILMAZ: bandit/checkov bulgu
    varliginda nonzero exit dondurur, bu bir calisma hatasi degildir. Binary
    yoksa `FileNotFoundError` dogal olarak yukari firlar -- bu GERCEK bir
    hatadir ve sessizce yutulmamalidir (audit-methodology.md: "sessiz
    varsayilan donmemeli, yol gosteren hata vermeli")."""
    # nosec B603 -- `komut` bu dosyadaki cagiran fonksiyonlarin hepsinde sabit
    # literal liste (git/bandit/checkov + sabit bayraklar), hicbir zaman
    # kullanici girdisinden/string birlestirmeden gelmiyor; shell=True yok.
    return subprocess.run(komut, cwd=cwd, capture_output=True, text=True, check=False)  # nosec B603


def _repo_kokunu_bul() -> Path:
    """Bu dosyanin bulundugu git deposunun kokunu dondurur. Surecin fiili
    `cwd`'sine guvenmez -- script nereden cagrilirsa cagrilsin calisir."""
    # nosec B603 B607 -- 'git' PATH'ten cozulur (repo genelinde zaten boyle
    # cagriliyor), argumanlar sabit literal, kullanici girdisi yok.
    sonuc = subprocess.run(  # nosec B603 B607
        ["git", "rev-parse", "--show-toplevel"],
        cwd=Path(__file__).resolve().parent,
        capture_output=True,
        text=True,
        check=True,
    )
    return Path(sonuc.stdout.strip())


def temiz_worktree_olustur(repo_kok: Path, ref: str, hedef: Path) -> None:
    """`ref`'in HEAD'i icin `hedef` yolunda ayrik (detached) bir git worktree
    olusturur. `--detach` kullanilir cunku `ref` su an checkout edilmis bir
    dal olabilir -- normal worktree add bu durumda "already checked out"
    hatasi verir."""
    sonuc = _calistir(["git", "worktree", "add", "--detach", str(hedef), ref], repo_kok)
    if sonuc.returncode != 0:
        raise RuntimeError(f"git worktree add basarisiz (ref={ref!r}):\n{sonuc.stderr}")


def temiz_worktree_sil(repo_kok: Path, hedef: Path) -> None:
    sonuc = _calistir(["git", "worktree", "remove", "--force", str(hedef)], repo_kok)
    if sonuc.returncode != 0:
        # Olcum sonucu zaten diskte -- worktree temizligi basarisiz olsa bile
        # bunu fatal yapmiyoruz, sadece uyariyoruz.
        print(
            f"[uyari] git worktree remove basarisiz oldu: {sonuc.stderr}",
            file=sys.stderr,
        )


def olcum_calistir(worktree: Path, cikti_dir: Path) -> dict[str, Any]:
    """Bandit + checkov'u `worktree` icinde calistirir, sonuclari `cikti_dir`
    altina (worktree DISINDA, kalici bir yola) yazar ve ozetler."""
    cikti_dir.mkdir(parents=True, exist_ok=True)

    # --- Bandit: docs/guvenlik-borcu.md SS 1 -- `bandit -r backend/ -ll` ---
    bandit_dosya = cikti_dir / "bandit_sonuc.json"
    bandit_calisma = _calistir(
        ["bandit", "-r", "backend/", "-ll", "-f", "json", "-o", str(bandit_dosya)],
        worktree,
    )
    if not bandit_dosya.exists():
        raise RuntimeError(
            "bandit JSON ciktisi olusturulamadi (olcum aleti arizasi).\n"
            f"returncode={bandit_calisma.returncode}\n"
            f"stdout={bandit_calisma.stdout[-2000:]}\n"
            f"stderr={bandit_calisma.stderr[-2000:]}"
        )
    bandit_veri = json.loads(bandit_dosya.read_text(encoding="utf-8"))

    # --- Checkov: docs/guvenlik-borcu.md SS 2 -- `checkov -d . --framework all` ---
    checkov_dir = cikti_dir / "checkov_sonuc"
    checkov_calisma = _calistir(
        [
            "checkov",
            "-d",
            ".",
            "--framework",
            "all",
            "-o",
            "json",
            "--output-file-path",
            str(checkov_dir),
        ],
        worktree,
    )
    checkov_dosya = checkov_dir / "results_json.json"
    if not checkov_dosya.exists():
        raise RuntimeError(
            "checkov JSON ciktisi olusturulamadi (olcum aleti arizasi).\n"
            f"returncode={checkov_calisma.returncode}\n"
            f"stdout={checkov_calisma.stdout[-2000:]}\n"
            f"stderr={checkov_calisma.stderr[-2000:]}"
        )
    checkov_veri = json.loads(checkov_dosya.read_text(encoding="utf-8"))

    return {
        "bandit": bandit_json_ozetle(bandit_veri),
        "checkov": checkov_json_ozetle(checkov_veri),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Temiz git-worktree kopyasinda bandit+checkov guvenlik olcumu.",
    )
    ap.add_argument(
        "--ref", default="HEAD", help="Olculecek git ref (varsayilan: HEAD)"
    )
    ap.add_argument(
        "--out-dir",
        default=None,
        help=(
            "Sonuc JSON'larinin yazilacagi dizin. Varsayilan: "
            "docs/audits/guvenlik-olcum-<zaman-damgasi>/ (kalici, silinmez)."
        ),
    )
    ap.add_argument(
        "--keep-worktree",
        action="store_true",
        help="Olcum sonrasi gecici worktree'yi silme (hata ayiklama icin).",
    )
    args = ap.parse_args(argv)

    repo_kok = _repo_kokunu_bul()

    if args.out_dir:
        cikti_dir = Path(args.out_dir).resolve()
    else:
        zaman_damgasi = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
        cikti_dir = repo_kok / "docs" / "audits" / f"guvenlik-olcum-{zaman_damgasi}"

    worktree = Path(tempfile.mkdtemp(prefix="kiro2_guvenlik_olcum_"))
    # mkdtemp dizini ONCEDEN olusturur; `git worktree add` hedefin VAR OLMAMASINI
    # ister -- bu yuzden bos dizini silip sadece yolu ayirtiyoruz.
    worktree.rmdir()

    print(f"[bilgi] repo: {repo_kok}")
    print(f"[bilgi] ref: {args.ref}")
    print(f"[bilgi] temiz worktree: {worktree}")
    print(f"[bilgi] cikti dizini: {cikti_dir}")

    try:
        temiz_worktree_olustur(repo_kok, args.ref, worktree)
        sonuc = olcum_calistir(worktree, cikti_dir)
    finally:
        if args.keep_worktree:
            print(f"[bilgi] --keep-worktree verildi, worktree SILINMEDI: {worktree}")
        else:
            temiz_worktree_sil(repo_kok, worktree)

    sonuc["olcum_zamani_utc"] = datetime.now(UTC).isoformat()
    sonuc["ref"] = args.ref
    ozet_dosya = cikti_dir / "ozet.json"
    ozet_dosya.write_text(
        json.dumps(sonuc, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    b = sonuc["bandit"]
    c = sonuc["checkov"]
    print()
    print("=== Bandit (MEDIUM+ siddet) ===")
    print(f"  toplam bulgu    : {b['toplam_bulgu']}")
    print(f"  siddet dagilimi : {b['siddet_dagilimi']}")
    if b["arac_hatasi_sayisi"]:
        print(f"  [uyari] arac hatasi sayisi: {b['arac_hatasi_sayisi']}")
    print("=== Checkov (--framework all) ===")
    print(f"  framework sayisi: {c['framework_sayisi']}")
    print(
        f"  passed / failed / skipped: {c['toplam_passed']} / {c['toplam_failed']} / {c['toplam_skipped']}"
    )
    print()
    print(f"[bilgi] tam sonuc: {ozet_dosya}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
