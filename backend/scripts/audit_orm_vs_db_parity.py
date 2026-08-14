#!/usr/bin/env python
"""S209: Kirli agactaki ORM modellerinin HANGI SURUMUNUN canli DB'ye uydugunu olcer.

NEDEN
-----
`backend/models/question_bank.py` vakasi (S209, P0-B) "commit'siz = cop" varsayimini
tersine cevirdi: commit'siz surum `question_bank`i 12 kolonluk govde + 3 uydu tabloya
bolmustu ve **canli DB tam da oyleydi**; HEAD'deki commit'li model ise DB'de olmayan
`question_bank.question_text` kolonunu bekliyordu. Yani o dosyada dogru olan
commit'siz surumdu.

Bu yuzden 110 YAPISAL dosyanin model olanlarinda karar "okuyup begenmek" degil
OLCUM olmali: iki surumu de canli `information_schema`ya karsi sina, hangisi
uyuyorsa o dogrudur.

YONTEM
------
Model dosyalari IMPORT EDILMEZ (33 dosyayi import etmek SQLAlchemy kayit defterinde
"Table already defined" cakismasi ve yan etki riski demek). Bunun yerine `ast` ile
`__tablename__` ve kolon adlari cikarilir:

    ad = Column("acik_ad", ...)   -> "acik_ad"   (ilk konumsal dize varsa o)
    ad = Column(Text, ...)        -> "ad"
    ad: Mapped[str] = mapped_column(...)  -> ayni kural

KULLANIM
--------
    python backend/scripts/audit_orm_vs_db_parity.py --dsn "postgresql://..."
    python backend/scripts/audit_orm_vs_db_parity.py --tsv rapor.tsv

Salt-okunurdur: DB'ye yalnizca SELECT atar, dosya degistirmez.
"""

from __future__ import annotations

import argparse
import ast
import os
import subprocess  # nosec B404 - sabit `git` argumanlari, kullanici girdisi yok (salt-okunur denetim aleti)
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO = Path(__file__).resolve().parents[2]
KOLON_CAGRILARI = {"Column", "mapped_column"}


def _git(*args: str) -> str:
    return subprocess.run(  # nosec B603 B607 - sabit `git` argumanlari, kullanici girdisi yok (salt-okunur denetim aleti)
        ["git", *args],
        cwd=REPO,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    ).stdout


def _tablo_adi(stmt: ast.stmt) -> str | None:
    """`__tablename__ = "x"` ise "x", degilse None."""
    if (
        isinstance(stmt, ast.Assign)
        and len(stmt.targets) == 1
        and isinstance(stmt.targets[0], ast.Name)
        and stmt.targets[0].id == "__tablename__"
        and isinstance(stmt.value, ast.Constant)
        and isinstance(stmt.value.value, str)
    ):
        return stmt.value.value
    return None


def _kolon_adi(stmt: ast.stmt) -> str | None:
    """`ad = Column(...)` / `ad: Mapped[...] = mapped_column(...)` -> kolon adi."""
    if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
        hedef, deger = stmt.targets[0], stmt.value
    elif isinstance(stmt, ast.AnnAssign) and stmt.value is not None:
        hedef, deger = stmt.target, stmt.value
    else:
        return None
    if not isinstance(hedef, ast.Name) or hedef.id.startswith("__"):
        return None
    if not isinstance(deger, ast.Call):
        return None
    fn = deger.func
    ad = fn.id if isinstance(fn, ast.Name) else getattr(fn, "attr", "")
    if ad not in KOLON_CAGRILARI:
        return None
    # Column("acik_ad", ...) -> ilk konumsal dize kolonun GERCEK adidir
    if (
        deger.args
        and isinstance(deger.args[0], ast.Constant)
        and isinstance(deger.args[0].value, str)
    ):
        return deger.args[0].value
    return hedef.id


def tablolari_cikar(src: str) -> dict[str, set[str]]:
    """Kaynak metinden {tablo_adi: {kolon adlari}} uret (import etmeden)."""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return {}

    out: dict[str, set[str]] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        tablo = None
        kolonlar: set[str] = set()
        for stmt in node.body:
            ad = _tablo_adi(stmt)
            if ad is not None:
                tablo = ad
                continue
            kolon = _kolon_adi(stmt)
            if kolon is not None:
                kolonlar.add(kolon)
        if tablo:
            out.setdefault(tablo, set()).update(kolonlar)
    return out


def db_semasi(dsn: str) -> dict[str, set[str]]:
    import psycopg2

    with psycopg2.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT table_name, column_name FROM information_schema.columns "
            "WHERE table_schema='public'"
        )
        sema: dict[str, set[str]] = {}
        for tablo, kolon in cur.fetchall():
            sema.setdefault(tablo, set()).add(kolon)
    return sema


def _skor(
    model: dict[str, set[str]], sema: dict[str, set[str]]
) -> tuple[int, int, int]:
    """(eksik_tablo, eksik_kolon, toplam_kolon) -- kucuk daha iyi."""
    eksik_tablo = eksik_kolon = toplam = 0
    for tablo, kolonlar in model.items():
        toplam += len(kolonlar)
        if tablo not in sema:
            eksik_tablo += 1
            eksik_kolon += len(kolonlar)
            continue
        eksik_kolon += len(kolonlar - sema[tablo])
    return eksik_tablo, eksik_kolon, toplam


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dsn", default=os.environ.get("KVKK_VERIFY_DSN"))
    ap.add_argument("--tsv", default=None)
    ap.add_argument(
        "--only-dirty",
        action="store_true",
        default=True,
        help="yalnizca kirli agactaki M dosyalari (varsayilan)",
    )
    args = ap.parse_args()
    if not args.dsn:
        print("DSN gerekli: --dsn veya KVKK_VERIFY_DSN", file=sys.stderr)
        return 2

    sema = db_semasi(args.dsn)
    print(f"canli sema: {len(sema)} tablo\n")

    satirlar = []
    for line in _git("status", "--porcelain").splitlines():
        kod, rel = line[:2].strip(), line[3:].strip().strip('"')
        if kod != "M" or not rel.endswith(".py"):
            continue
        disk_src = (REPO / rel).read_text(encoding="utf-8", errors="replace")
        head_src = _git("show", f"HEAD:{rel}")
        d_model, h_model = tablolari_cikar(disk_src), tablolari_cikar(head_src)
        if not d_model and not h_model:
            continue  # ORM modeli yok

        d = _skor(d_model, sema)
        h = _skor(h_model, sema)
        if d[:2] == h[:2]:
            karar = "ESIT"
        elif d[:2] < h[:2]:
            karar = "DISK_DOGRU"
        else:
            karar = "HEAD_DOGRU"
        satirlar.append(
            {
                "karar": karar,
                "yol": rel,
                "disk": f"{d[0]} eksik tablo / {d[1]} eksik kolon / {d[2]}",
                "head": f"{h[0]} eksik tablo / {h[1]} eksik kolon / {h[2]}",
            }
        )

    oncelik = {"DISK_DOGRU": 0, "HEAD_DOGRU": 1, "ESIT": 2}
    satirlar.sort(key=lambda r: (oncelik[r["karar"]], r["yol"]))

    for karar in ("DISK_DOGRU", "HEAD_DOGRU", "ESIT"):
        grup = [r for r in satirlar if r["karar"] == karar]
        print(f"=== {karar} ({len(grup)}) ===")
        for r in grup:
            print(f"  {r['yol']}")
            if karar != "ESIT":
                print(f"      disk: {r['disk']}   |   HEAD: {r['head']}")
        print()

    if args.tsv:
        with Path(args.tsv).open("w", encoding="utf-8", newline="") as fh:
            fh.write("karar\tyol\tdisk\thead\n")
            for r in satirlar:
                fh.write(f"{r['karar']}\t{r['yol']}\t{r['disk']}\t{r['head']}\n")
        print(f"TSV: {args.tsv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
