"""Faz 1 Katman A — yüksek-PII tablolara organization_id retrofit.

9 tablo: org_id NOT NULL + FK + backfill (0 NULL). Cross-tenant izolasyon,
BaseRepository org-scoped model olarak muamele için hazır (ORM wiring ayrı tur).
"""

# ruff: noqa: N999
# N999 (gecersiz modul adi: `katmanA` camelCase): dosya adi degistirilmedi.
# Neden: bu ad iki yerde daha geciyor (`.bandit-baseline.json` girdisi ve
# depo icindeki Faz-1 notlari); yeniden adlandirma testin OLCTUGU seyi
# degistirmez ama bu referanslari bayatlatir. Kural burada bilincli olarak
# susturuluyor -- modul hicbir yerden ADIYLA import EDILMIYOR (olculdu:
# `git grep test_faz1_katmanA` -> yalniz baseline dosyasi), yani N999'un
# korudugu sey (import edilebilirlik) burada risk altinda degil.

from sqlalchemy import text

from tests.pg_sync import sync_pg_engine

KATMAN_A = [
    "fsrs_cards",
    "fsrs_reviews",
    "fsrs_schedules",
    "student_abilities",
    "bkt_states",
    "student_knowledge_states",
    "performance_history",
    "kvkk_consents",
    "exam_sessions",
]


def _engine():
    # Ortak tanim: tests/pg_sync.py -- oradaki dosya basi yorumunda hem
    # `database="kiro2"` sabitinin (CI'da ad `kiro2_test`) hem de varsayilan
    # psycopg2 surucusunun (CI'da yalniz psycopg v3 kurulu) neden CI'da
    # dustugu olcumleriyle yazili.
    return sync_pg_engine()


def test_org_id_column_notnull():
    eng = _engine()
    with eng.connect() as c:
        for t in KATMAN_A:
            nn = c.execute(
                text(
                    "SELECT is_nullable FROM information_schema.columns "
                    "WHERE table_name=:t AND column_name='organization_id'"
                ),
                {"t": t},
            ).scalar()
            assert nn == "NO", f"{t}.organization_id yok/nullable ({nn})"


def test_no_null_org_id():
    eng = _engine()
    with eng.connect() as c:
        for t in KATMAN_A:
            # S608: tablo adi KULLANICI GIRDISI DEGIL -- yukaridaki sabit
            # KATMAN_A listesinden geliyor. Tablo adi SQL'de bind parametresi
            # olamaz, bu yuzden f-string zorunlu.
            n = c.execute(
                text(f"SELECT count(*) FROM {t} WHERE organization_id IS NULL")  # noqa: S608
            ).scalar()
            assert n == 0, f"{t}: {n} NULL org_id"


def test_fk_to_organizations():
    eng = _engine()
    with eng.connect() as c:
        for t in KATMAN_A:
            fk = c.execute(
                text(
                    "SELECT count(*) FROM information_schema.key_column_usage kcu "
                    "JOIN information_schema.table_constraints tc "
                    "  ON tc.constraint_name=kcu.constraint_name "
                    "WHERE tc.table_name=:t AND tc.constraint_type='FOREIGN KEY' "
                    "  AND kcu.column_name='organization_id'"
                ),
                {"t": t},
            ).scalar()
            assert fk >= 1, f"{t}.organization_id FK yok"


def test_server_default_legacy():
    eng = _engine()
    with eng.connect() as c:
        for t in KATMAN_A:
            d = c.execute(
                text(
                    "SELECT column_default FROM information_schema.columns "
                    "WHERE table_name=:t AND column_name='organization_id'"
                ),
                {"t": t},
            ).scalar()
            assert d and "org_legacy_default" in d, f"{t} server_default yok"
