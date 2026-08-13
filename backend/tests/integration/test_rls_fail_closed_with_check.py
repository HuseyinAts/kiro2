"""RLS fail-closed gecisinin YAZMA yolunu da kapattigini olcer (#464 devami).

NEDEN VAR
---------
`ad6ba3bbe485_fix_rls_fail_closed_policy` politikalari permissive'den
fail-closed'a cevirir. Ama `ALTER POLICY ... USING (...)` PostgreSQL'de
**`WITH CHECK` ifadesine DOKUNMAZ** — o, `CREATE POLICY` anindaki permissive
haliyle kalir.

13 Agu 2026 CANLI OLCUMU (kod okunmadi, atlatma DENENDI — psql :5434/kiro2):

    CREATE POLICY ... USING (permissive) WITH CHECK (permissive)
    ALTER  POLICY ... USING (fail-closed)          <- migration'in yaptigi

    pg_policies.qual       -> organization_id = current_setting(...)   [siki]
    pg_policies.with_check -> ... IS NULL OR ... = '' OR ...           [GEVSEK]

    SET ROLE kiro2_app; -- app'in uretim rolu, GUC set EDILMEDEN
    INSERT INTO _rls_probe_tmp VALUES (1, 'ORG-FOREIGN');  -> INSERT 0 1  (GECTI)
    SELECT count(*) FROM _rls_probe_tmp;                   -> 0
    RESET ROLE; SELECT count(*) FROM _rls_probe_tmp;       -> 1

Yani sonuc **yaz-serbest / oku-kapali**: GUC'u set etmeyen bir istek yabanci
bir organizasyona satir ENJEKTE edebilir ve yazdigini goremedigi icin geri
bildirim de alamaz. Okuma tarafi kapali oldugu icin bu, duz fail-open'dan
daha sessiz bir bozulmadir.

BU DOSYANIN TASARIMI
--------------------
Uretim tablolarina DOKUNULMAZ. Her test kendi sentetik tablosunu kurar ve
islem sonunda geri alinir (fixture `rollback`). Olculen sey migration'in
URETTIGI SQL'dir — test SQL'i kendi yazmaz, `alter_policy_sql`'i migration
modulunden import eder; aksi halde migration degisince test sessizce
alakasizlasirdi.

`test_alet_dogrulamasi_*` KONTROL KOLUDUR: fix'ten once de sonra da yesil
olmali. Yesil degilse olcum duzeneginin kendisi bozuktur ve diger uc testin
sonucu gecersizdir (bkz. `.claude/rules/audit-methodology.md` — "Olcum
aletini dogrula").
"""

from __future__ import annotations

import importlib.util
from collections.abc import Iterator
from pathlib import Path

import pytest

# `psycopg2-binary` CI'da kurulu DEGIL — korumasiz import `-x` ile kosan job'u
# dusururdu (bkz. test_rls_tenant_isolation_guard.py ayni gerekce).
psycopg2 = pytest.importorskip("psycopg2")

pytestmark = [pytest.mark.integration, pytest.mark.security]

# Yerel gelistirme DSN'i — uretim kimligi DEGIL.
DSN = "postgresql://postgres:postgres@localhost:5434/kiro2"  # pragma: allowlist secret

PROBE = "_rls_fail_closed_probe"
YABANCI_ORG = "ORG-YABANCI"
KENDI_ORG = "ORG-KENDI"

# PostgreSQL: "new row violates row-level security policy" -> 42501
RLS_YAZMA_REDDI = "42501"


def _migration_modulu():
    """Migration'i dosya yolundan yukler (alembic/versions paket degil)."""
    yol = (
        Path(__file__).resolve().parents[2]
        / "alembic"
        / "versions"
        / "ad6ba3bbe485_fix_rls_fail_closed_policy.py"
    )
    if not yol.exists():  # pragma: no cover - dosya tasinirsa haber ver
        pytest.fail(f"Migration bulunamadi: {yol}")
    spec = importlib.util.spec_from_file_location(yol.stem, yol)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


MIGRATION = _migration_modulu()


@pytest.fixture
def imlec() -> Iterator:
    """Islem icinde imlec; test bitince HER SEY geri alinir."""
    try:
        baglanti = psycopg2.connect(DSN)
    except psycopg2.OperationalError as hata:
        pytest.skip(f"PostgreSQL :5434 erisilemez ({hata.__class__.__name__})")
    baglanti.autocommit = False
    try:
        with baglanti.cursor() as c:
            c.execute("SELECT count(*) FROM pg_roles WHERE rolname='kiro2_app'")
            if not c.fetchone()[0]:
                pytest.skip("`kiro2_app` rolu yok — RLS kurulumu bu ortamda gecersiz")
            yield c
    finally:
        baglanti.rollback()
        baglanti.close()


def _permissive_politikali_tablo_kur(c) -> None:
    """`faz1_rls_20260704`'un ILK kurdugu hali: USING + WITH CHECK permissive."""
    pred = MIGRATION.PERMISSIVE_PRED
    c.execute(f"CREATE TABLE {PROBE} (id int, organization_id varchar NOT NULL)")
    c.execute(f"ALTER TABLE {PROBE} ENABLE ROW LEVEL SECURITY")
    c.execute(f"ALTER TABLE {PROBE} FORCE ROW LEVEL SECURITY")
    c.execute(
        f"CREATE POLICY tenant_isolation ON {PROBE} FOR ALL "
        f"USING ({pred}) WITH CHECK ({pred})"
    )
    c.execute(f"GRANT ALL ON {PROBE} TO kiro2_app")


def _fail_closed_migrasyonu_uygula(c) -> None:
    """Migration'in URETTIGI SQL'i kosar — test kendi SQL'ini yazmaz."""
    c.execute(MIGRATION.alter_policy_sql(PROBE, MIGRATION.FAIL_CLOSED_PRED))


def _guc_suz_yabanci_yazim_gecti_mi(c) -> bool:
    """kiro2_app olarak, GUC set EDILMEDEN yabanci org'a INSERT denenir."""
    c.execute("SAVEPOINT deneme")
    c.execute("SET LOCAL ROLE kiro2_app")
    try:
        c.execute(f"INSERT INTO {PROBE} VALUES (1, %s)", (YABANCI_ORG,))  # noqa: S608
    except psycopg2.Error as hata:
        assert hata.pgcode == RLS_YAZMA_REDDI, (
            f"INSERT beklenmedik hatayla dustu (pgcode={hata.pgcode}): {hata}. "
            "Bu bir RLS reddi degil — olcum gecersiz."
        )
        c.execute("ROLLBACK TO SAVEPOINT deneme")
        return False
    c.execute("ROLLBACK TO SAVEPOINT deneme")
    return True


def test_alet_dogrulamasi_permissive_politika_yabanci_yazima_izin_verir(imlec) -> None:
    """KONTROL KOLU: duzenek fix ONCESI durumu gercekten uretebiliyor mu.

    Bu test kirmiziya donerse asagidaki uc olcumun hicbiri gecerli degildir —
    ya RLS zorlanmiyor ya rol/grant kurulumu farkli.
    """
    _permissive_politikali_tablo_kur(imlec)
    assert _guc_suz_yabanci_yazim_gecti_mi(imlec), (
        "Permissive politikayla bile GUC'suz yazim reddedildi -> olcum duzenegi "
        "bozuk (RLS zorlanmiyor ya da kiro2_app grant'i eksik)"
    )


def test_fail_closed_gecisi_yabanci_org_yazimini_engeller(imlec) -> None:
    """ASIL IDDIA: fail-closed'a gecince GUC'suz yabanci yazim REDDEDILMELI.

    13 Agu 2026'da bu test kirmizidir: `ALTER POLICY ... USING` yalniz okuma
    yolunu kapatir, `WITH CHECK` permissive kalir ve INSERT gecer.
    """
    _permissive_politikali_tablo_kur(imlec)
    _fail_closed_migrasyonu_uygula(imlec)
    assert not _guc_suz_yabanci_yazim_gecti_mi(imlec), (
        "GUC set EDILMEDEN yabanci organizasyona INSERT GECTI. "
        "`ALTER POLICY ... USING (...)` WITH CHECK'i degistirmez; migration "
        "WITH CHECK'i de fail-closed yapmali (yaz-serbest/oku-kapali sizinti)."
    )


def test_fail_closed_gecisi_with_check_ifadesini_de_gunceller(imlec) -> None:
    """`pg_policies.with_check` icinde permissive dallar KALMAMALI."""
    _permissive_politikali_tablo_kur(imlec)
    _fail_closed_migrasyonu_uygula(imlec)
    imlec.execute(
        "SELECT qual, with_check FROM pg_policies "
        "WHERE tablename = %s AND policyname = 'tenant_isolation'",
        (PROBE,),
    )
    qual, with_check = imlec.fetchone()
    assert "IS NULL" not in qual, f"Okuma yolu fail-closed degil: {qual}"
    assert "IS NULL" not in with_check, (
        f"Yazma yolu HALA permissive: {with_check}. "
        "Okuma kapali + yazma acik = sessiz capraz-kiraci enjeksiyonu."
    )


def test_dogru_guc_ile_yazim_calismaya_devam_eder(imlec) -> None:
    """ASIRI-DUZELTME BEKCISI: mesru kiraci hala kendi org'una yazabilmeli."""
    _permissive_politikali_tablo_kur(imlec)
    _fail_closed_migrasyonu_uygula(imlec)
    imlec.execute("SET LOCAL ROLE kiro2_app")
    imlec.execute(f"SET LOCAL app.current_org_id = '{KENDI_ORG}'")
    imlec.execute(f"INSERT INTO {PROBE} VALUES (1, %s)", (KENDI_ORG,))  # noqa: S608
    imlec.execute(f"SELECT count(*) FROM {PROBE}")  # noqa: S608
    assert imlec.fetchone()[0] == 1, (
        "Dogru GUC ile yazilan satir kiracinin kendisine gorunmuyor -> "
        "fail-closed gecisi mesru trafigi de kirdi"
    )


def test_alter_policy_sql_with_check_iceriyor() -> None:
    """DB'siz bekci: CI'da PostgreSQL olmasa da bu invaryant korunur.

    Yukaridaki uc test PG:5434 gerektirdigi icin CI'da SKIP olur. Bu test
    SKIP olmaz — regresyon hic kimse DB'ye baglanmadan da yakalanir.
    """
    sql = MIGRATION.alter_policy_sql("ornek_tablo", MIGRATION.FAIL_CLOSED_PRED)
    assert "USING" in sql, "ALTER POLICY okuma yolunu (USING) hic yazmiyor"
    assert "WITH CHECK" in sql, (
        "Uretilen ALTER POLICY yalniz USING yaziyor. PostgreSQL WITH CHECK'i "
        "DOKUNULMAMIS birakir -> yazma yolu permissive kalir."
    )
