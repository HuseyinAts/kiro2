"""Kitabin DB durumu: ithal satiri / aktif / agac dugumu / eski hat aktif (round-trip kontrolu).

python -m scripts.kitap.kitap_hat.db_durum --profil K
"""

from __future__ import annotations

import argparse
import os
from types import ModuleType

import psycopg

from scripts.kitap.kitap_hat import ortak

VARSAYILAN_DSN = (
    "postgresql://postgres:postgres@localhost:5434/kiro2"  # pragma: allowlist secret
)
DSN = os.environ.get("KIRO2_DSN", VARSAYILAN_DSN)


def durum(p: ModuleType) -> dict[str, int]:
    with psycopg.connect(DSN) as c:
        r = c.execute(
            """SELECT count(*), count(*) FILTER (WHERE b.is_active)
               FROM question_bank b JOIN question_metadata m ON m.id = b.id
               WHERE m.source_book = %s AND m.pipeline_metadata->>'ithal_araci' = %s""",
            (p.KAYNAK_ADI, "scripts/kitap/kitap_hat/ithal.py"),
        ).fetchone()
        dugum = c.execute(
            "SELECT count(*) FROM topic_hierarchy WHERE code LIKE %s",
            (p.KOD_ONEKI + "-%",),
        ).fetchone()
        eski = c.execute(
            """SELECT count(*), count(*) FILTER (WHERE b.is_active)
               FROM question_bank b JOIN question_metadata m ON m.id = b.id
               WHERE m.source_book = ANY(%s)""",
            (list(p.ESKI_KAYNAKLAR),),
        ).fetchone()
    if not (r and dugum and eski):
        raise RuntimeError("sayim sorgusu satir dondurmedi")
    return {
        "ithal": r[0],
        "ithal_aktif": r[1],
        "agac_dugum": dugum[0],
        "eski_hat": eski[0],
        "eski_hat_aktif": eski[1],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profil", required=True)
    print(durum(ortak.profil(ap.parse_args().profil)))


if __name__ == "__main__":
    main()
