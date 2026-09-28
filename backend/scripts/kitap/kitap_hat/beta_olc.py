"""Beta kapisi yukunu olcer (agac + ithal + eski hat pasif SONRASI, yerel DB).

Cikti: migration_uret'in --beta-olcum dosyasi (ASCII metin) ve 'N/M' hedefi.
Kural beta migration'inin _HEDEF_SQL'iyle birebir (orada duz yazili).

KULLANIM (backend dizininden)
-----------------------------
    python -m scripts.kitap.kitap_hat.beta_olc --profil K --cikti olcum.txt
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import psycopg

from scripts.kitap.kitap_hat import ortak

VARSAYILAN_DSN = (
    "postgresql://postgres:postgres@localhost:5434/kiro2"  # pragma: allowlist secret
)
DSN = os.environ.get("KIRO2_DSN", VARSAYILAN_DSN)
ARAC = "scripts/kitap/kitap_hat/ithal.py"

_TEMEL = """
FROM question_bank qb JOIN question_metadata qm ON qm.id = qb.id
JOIN question_content qc ON qc.id = qb.id
LEFT JOIN question_statistics qs ON qs.id = qb.id
WHERE qm.source_book = %(k)s AND qm.pipeline_metadata::jsonb ->> 'ithal_araci' = %(a)s
"""
_BAYRAK = "(qm.pipeline_metadata::jsonb -> 'bayraklar') ? %s"
_ISARET = (
    "(qc.question_text LIKE '%%[??]%%' OR qc.option_a LIKE '%%[??]%%' OR qc.option_b LIKE '%%[??]%%'"
    " OR qc.option_c LIKE '%%[??]%%' OR qc.option_d LIKE '%%[??]%%' OR qc.option_e LIKE '%%[??]%%')"
)
_HASH = (
    "EXISTS (SELECT 1 FROM question_bank o WHERE o.soru_hash = qb.soru_hash"
    " AND o.is_active IS TRUE AND o.id <> qb.id)"
)
_IKIZ = (
    "EXISTS (SELECT 1 FROM jsonb_array_elements_text(CASE WHEN jsonb_typeof(qm.pipeline_metadata::jsonb"
    " -> 'modern_kitap_ikizi') = 'array' THEN qm.pipeline_metadata::jsonb -> 'modern_kitap_ikizi'"
    " ELSE '[]'::jsonb END) AS ikiz(id) JOIN question_bank o ON o.id::text = ikiz.id WHERE o.is_active IS TRUE)"
)
SERVIS_DISI = (
    "sik_bos",
    "gorsel_yok_sekilli",
    "gosterilemez_gorsel_sik_kirpimsiz",
    "sik_okunamadi",
    "ortak_oncul_kirpimda_yok",
)


def olc(kaynak: str) -> dict[str, int]:
    p = {"k": kaynak, "a": ARAC}
    out: dict[str, int] = {}
    with psycopg.connect(DSN) as c:

        def say(kosul: str) -> int:
            r = c.execute(f"SELECT count(*) {_TEMEL} AND {kosul}", p).fetchone()
            return int(r[0]) if r else 0

        out["toplam"] = say("TRUE")
        out["pending"] = say("qs.quality_review_status = 'pending'")
        out["kilit"] = say(
            "qb.is_ai_generated IS TRUE AND qb.review_status = 'PENDING'"
        )
        for b in SERVIS_DISI:
            r = c.execute(
                f"SELECT count(*) {_TEMEL} AND (qm.pipeline_metadata::jsonb -> 'bayraklar') ? %(b)s",
                {**p, "b": b},
            ).fetchone()
            out[b] = int(r[0]) if r else 0
        out["isaret"] = say(_ISARET)
        out["hash_ikizi_aktif"] = say(_HASH)
        out["modern_ikiz_aktif"] = say(_IKIZ)
        dis = " OR ".join(
            [
                f"(qm.pipeline_metadata::jsonb -> 'bayraklar') ? '{b}'"
                for b in SERVIS_DISI
            ]
            + [_ISARET, _HASH, _IKIZ]
        )
        out["hedef"] = say(f"qb.is_active IS NOT TRUE AND NOT ({dis})")
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profil", required=True)
    ap.add_argument("--cikti", required=True)
    a = ap.parse_args()
    pr = ortak.profil(a.profil)
    o = olc(pr.KAYNAK_ADI)
    satir = [
        f"Kitap {pr.BEKLENEN_SORU} soru; ithalin yazdigi {o['toplam']} satirda:",
        f"    quality_review_status 'pending' ............ {o['pending']}/{o['toplam']} (kilit)",
        f"    is_ai_generated=true, review 'PENDING' ..... {o['kilit']}/{o['toplam']} (kilit)",
    ]
    for b in SERVIS_DISI:
        satir.append(
            f"    bayrak {b} {'.' * max(1, 34 - len(b))} {o[b]:4d}  -> DISLANIR"
        )
    satir += [
        f"    ogrenciye gorunen alti alanda `[??]` ....... {o['isaret']:4d}  -> DISLANIR",
        f"    aktif satirlarla soru_hash cakismasi ....... {o['hash_ikizi_aktif']:4d}  -> DISLANIR",
        f"    modern_kitap_ikizi, ikizi AKTIF ............ {o['modern_ikiz_aktif']:4d}  -> DISLANIR",
        f"HEDEF: {o['hedef']}/{o['toplam']}",
    ]
    Path(a.cikti).write_text("\n".join(satir) + "\n", "ascii")
    print("\n".join(satir))
    print(f"--beta-hedef {o['hedef']}/{o['toplam']}")


if __name__ == "__main__":
    main()
