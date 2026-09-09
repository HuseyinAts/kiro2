#!/usr/bin/env python
"""20 Agu 2026 `*_cop_yedek_20260820` tablolarini arsivle (dump -> dogrula -> dusur).

NEDEN (docs/veritabani-denetimi-20260909.md madde 1, 9 Eyl 2026 olcumu)
------------------------------------------------------------------------
question_bank/content/metadata/statistics'in 20 Agu halusinasyon temizligi
oncesi kopyalari (36.967 satir x 4, ~34,7 MB) canli DB'de duruyor; FK/view
bagimliligi yok, ORM'de modeli yok, hicbir kod okumuyor. Karar: pg_dump ile
arsivle, GERI YUKLENEBILIRLIGI olc, ancak ondan sonra dusur. DROP yalnizca
kullanici "sil" derse ve manifest "dogrulandi" ise calisir.

`pg_dump -t` tek basina yeterli DEGIL (19 Agu dersi, yedek_onkosul_uret.py):
enum/uzanti tipleri dump'ta yok; onkosul dosyasi birlikte uretilir ve
dogrulama gercek bir gecici DB'ye restore ederek satir sayar.

KULLANIM
--------
    python backend/scripts/quality/cop_yedek_arsivle.py dump
        -> backups/cop_yedek_20260820_<ts>.dump, .prereq.sql, .manifest.json
    python backend/scripts/quality/cop_yedek_arsivle.py verify backups/<ad>.manifest.json
        -> gecici DB'ye restore, satir sayilari esit mi; manifest["dogrulandi"]=true
    python backend/scripts/quality/cop_yedek_arsivle.py drop backups/<ad>.manifest.json --onay SIL
        -> yalnizca dogrulanmis manifest ile, 4 tablo tek transaction'da DROP

Ortam: KIRO2_DSN (varsayilan yerel 5434), PG_BIN (pg_dump/pg_restore dizini).
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess  # nosec B404 - argv LISTE, shell yok; sabit pg_dump/pg_restore
import sys
from datetime import UTC, datetime
from pathlib import Path

import psycopg

_BURASI = Path(__file__).resolve()
sys.path.insert(0, str(_BURASI.parents[2]))
from scripts.quality.yedek_onkosul_uret import (  # noqa: E402
    _SORGU_ENUM,
    _SORGU_UZANTI,
    onkosul_sql,
)

KOK = _BURASI.parents[3]
YEDEK_DIZINI = KOK / "backups"
VARSAYILAN_DSN = (
    "postgresql://postgres:postgres@localhost:5434/kiro2"  # pragma: allowlist secret
)
DOGRULAMA_DB = "kiro2_cop_yedek_dogrulama"

COP_YEDEK_TABLOLARI = (
    "question_bank_cop_yedek_20260820",
    "question_content_cop_yedek_20260820",
    "question_metadata_cop_yedek_20260820",
    "question_statistics_cop_yedek_20260820",
)


def _dsn() -> str:
    return os.environ.get("KIRO2_DSN", VARSAYILAN_DSN)


def _pg_bin(arac: str) -> str:
    aday = os.environ.get("PG_BIN")
    if aday and (Path(aday) / f"{arac}.exe").exists():
        return str(Path(aday) / f"{arac}.exe")
    if aday and (Path(aday) / arac).exists():
        return str(Path(aday) / arac)
    yol = shutil.which(arac)
    if yol:
        return yol
    for surum in ("18", "17", "16"):
        p = Path(rf"C:\Program Files\PostgreSQL\{surum}\bin\{arac}.exe")
        if p.exists():
            return str(p)
    raise SystemExit(f"HATA: {arac} bulunamadi; PG_BIN ver.")


def _satir_sayilari(dsn: str, tablolar: tuple[str, ...]) -> dict[str, int]:
    with psycopg.connect(dsn) as conn:
        return {
            t: conn.execute(f'SELECT count(*) FROM "{t}"').fetchone()[0]  # nosec B608
            for t in tablolar
        }


def _onkosul(dsn: str) -> str:
    """Kopya tablolarin enum/uzanti onkosulu -- ayni sorgular, farkli tablo kumesi."""
    tablolar = list(COP_YEDEK_TABLOLARI)
    # SQLAlchemy `:tablolar` -> psycopg `%(tablolar)s`
    sorgu_uzanti = str(_SORGU_UZANTI).replace(":tablolar", "%(tablolar)s")
    sorgu_enum = str(_SORGU_ENUM).replace(":tablolar", "%(tablolar)s")
    with psycopg.connect(dsn) as conn:
        uzantilar = {r[0] for r in conn.execute(sorgu_uzanti, {"tablolar": tablolar})}
        enumlar: dict[str, list[str]] = {}
        for ad, etiket in conn.execute(sorgu_enum, {"tablolar": tablolar}):
            enumlar.setdefault(ad, []).append(etiket)
    sql: str = onkosul_sql({"uzantilar": uzantilar, "enumlar": enumlar})
    return sql


def dump(args: argparse.Namespace) -> None:
    dsn = _dsn()
    YEDEK_DIZINI.mkdir(exist_ok=True)
    ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    govde = YEDEK_DIZINI / f"cop_yedek_20260820_{ts}"
    dump_yolu = govde.with_suffix(".dump")
    onkosul_yolu = govde.with_suffix(".prereq.sql")
    manifest_yolu = govde.with_suffix(".manifest.json")

    sayilar = _satir_sayilari(dsn, COP_YEDEK_TABLOLARI)
    onkosul_yolu.write_text(_onkosul(dsn), encoding="utf-8")
    komut = [
        _pg_bin("pg_dump"),
        "--dbname",
        dsn,
        "-F",
        "c",
        "--no-owner",
        "--no-privileges",
    ]
    for t in COP_YEDEK_TABLOLARI:
        komut += ["-t", f"public.{t}"]
    komut += ["-f", str(dump_yolu)]
    sonuc = subprocess.run(komut, capture_output=True, text=True, check=False)  # nosec B603
    if sonuc.returncode != 0:
        raise SystemExit(f"pg_dump basarisiz (rc={sonuc.returncode}):\n{sonuc.stderr}")
    manifest = {
        "olusturma": ts,
        "dsn_host": dsn.split("@")[-1],
        "tablolar": list(COP_YEDEK_TABLOLARI),
        "satir_sayilari": sayilar,
        "dump": dump_yolu.name,
        "dump_bayt": dump_yolu.stat().st_size,
        "onkosul": onkosul_yolu.name,
        "dogrulandi": False,
    }
    manifest_yolu.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"dump: {dump_yolu} ({manifest['dump_bayt']:,} bayt)")
    print(f"satirlar: {sayilar}")
    print(f"manifest: {manifest_yolu}  (dogrulandi=false -- simdi `verify`)")


def _bakim_dsn(dsn: str, db: str) -> str:
    on, _, _son = dsn.rpartition("/")
    return f"{on}/{db}"


def verify(args: argparse.Namespace) -> None:
    manifest_yolu = Path(args.manifest)
    manifest = json.loads(manifest_yolu.read_text(encoding="utf-8"))
    dump_yolu = manifest_yolu.with_name(manifest["dump"])
    onkosul_yolu = manifest_yolu.with_name(manifest["onkosul"])
    dsn = _dsn()
    bakim = _bakim_dsn(dsn, "postgres")
    hedef = _bakim_dsn(dsn, DOGRULAMA_DB)

    with psycopg.connect(bakim, autocommit=True) as conn:
        conn.execute(f'DROP DATABASE IF EXISTS "{DOGRULAMA_DB}"')
        conn.execute(f'CREATE DATABASE "{DOGRULAMA_DB}"')
    try:
        with psycopg.connect(hedef, autocommit=True) as conn:
            conn.execute(onkosul_yolu.read_text(encoding="utf-8"))
        komut = [
            _pg_bin("pg_restore"),
            "--dbname",
            hedef,
            "--no-owner",
            "--no-privileges",
            "--exit-on-error",
            str(dump_yolu),
        ]
        sonuc = subprocess.run(komut, capture_output=True, text=True, check=False)  # nosec B603
        if sonuc.returncode != 0:
            raise SystemExit(
                f"pg_restore basarisiz (rc={sonuc.returncode}):\n{sonuc.stderr}"
            )
        geri = _satir_sayilari(hedef, tuple(manifest["tablolar"]))
    finally:
        with psycopg.connect(bakim, autocommit=True) as conn:
            conn.execute(f'DROP DATABASE IF EXISTS "{DOGRULAMA_DB}"')

    beklenen = manifest["satir_sayilari"]
    fark = {
        t: (beklenen[t], geri.get(t)) for t in beklenen if beklenen[t] != geri.get(t)
    }
    if fark:
        raise SystemExit(f"DOGRULAMA BASARISIZ -- satir farki: {fark}")
    manifest["dogrulandi"] = True
    manifest["dogrulama_zamani"] = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    manifest["geri_yuklenen_satirlar"] = geri
    manifest_yolu.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"DOGRULANDI: {geri} == manifest; gecici DB dusuruldu")


def drop(args: argparse.Namespace) -> None:
    manifest_yolu = Path(args.manifest)
    manifest = json.loads(manifest_yolu.read_text(encoding="utf-8"))
    if args.onay != "SIL":
        raise SystemExit("DROP icin --onay SIL gerekli (kullanici karari).")
    if not manifest.get("dogrulandi"):
        raise SystemExit("Manifest dogrulanmamis -- once `verify`.")
    if not manifest_yolu.with_name(manifest["dump"]).exists():
        raise SystemExit("Dump dosyasi yerinde degil -- DROP reddedildi.")
    dsn = _dsn()
    simdiki = _satir_sayilari(dsn, tuple(manifest["tablolar"]))
    if simdiki != manifest["satir_sayilari"]:
        raise SystemExit(
            f"Tablolar dump'tan beri degismis: {simdiki} != {manifest['satir_sayilari']}"
        )
    with psycopg.connect(dsn) as conn:
        for t in manifest["tablolar"]:
            conn.execute(f'DROP TABLE "{t}"')
        conn.commit()
    manifest["dusurme_zamani"] = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    manifest_yolu.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(
        f"DUSURULDU: {manifest['tablolar']}; geri yukleme: prereq + pg_restore {manifest['dump']}"
    )


def main() -> None:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    alt = p.add_subparsers(dest="komut", required=True)
    alt.add_parser("dump").set_defaults(fn=dump)
    v = alt.add_parser("verify")
    v.add_argument("manifest")
    v.set_defaults(fn=verify)
    d = alt.add_parser("drop")
    d.add_argument("manifest")
    d.add_argument("--onay", default="")
    d.set_defaults(fn=drop)
    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
