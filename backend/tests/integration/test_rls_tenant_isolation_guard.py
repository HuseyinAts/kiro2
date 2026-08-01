"""RLS cok-kiracili izolasyon bekcisi (#464 / B5 · F7 · N3).

NEDEN VAR
---------
30 Tem 2026 denetimi B5'i "satis blokeri" ilan etti; 1 Agu dogrulamasi
`N3` olarak sunu olctu: **hicbir test GUC/RLS davranisini sinamiyordu.**
Var olan iki test yalnizca IMZA kontrol ediyor
(`test_org_notnull_and_tenant_resolver.py` -> `callable(get_current_tenant)`)
veya YAPISAL guvence veriyor (`test_golden_flows.py` -> "ucta org parametresi
yok"). Ikisi de ikinci bir organizasyonla capraz-kiraci sizinti DENEMIYOR.

1 AGU 2026 CANLI OLCUMU (atlatma DENENDI, kod okunmadi)
--------------------------------------------------------
    superuser (taban)            5.664 satir
    kiro2_app, GUC YOK           5.664   <- TAM ATLATMA
    kiro2_app, GUC = ''          5.664   <- TAM ATLATMA
    kiro2_app, GUC = yanlis-org      0   <- IZOLASYON CALISIYOR

Yani mekanizma SAGLAM; eksik olan GUC'un her istekte set edilmesi.
Politika kalibi (79/79, fail-closed 0):

    current_setting('app.current_org_id', true) IS NULL
    OR current_setting('app.current_org_id', true) = ''
    OR organization_id::text = current_setting('app.current_org_id', true)

Ilk iki dal, GUC set edilmeyen her istegi TUM satirlara aciyor.
GUC'u set eden tek uretim satiri `core/dependencies.py:456`, ona ulasan
`get_current_tenant` ise 163 router dosyasinin 2'sinde.

BU DOSYANIN TASARIMI — NEDEN BUGUN YESIL
-----------------------------------------
Permissive dal bugun ZARAR VERMIYOR cunku `organizations` tablosunda **1**
satir var ve RLS'li tablolardaki tum satirlar ona ait. Yani bugun
capraz-kiraci sizintisi FIZIKSEL OLARAK imkansiz.

Testi bugun kirmizi yapmak CI'i, cozulmesi bir mimari sprint suren bir is
icin bloke ederdi. Onun yerine bu dosya bir **TUZAK DEDEKTORU**:

  - Mekanizmanin calistigini SUREKLI dogrular (yanlis org -> 0 satir).
  - Permissive dalin bugunku davranisini BELGELER (varsayim degil, olcum).
  - **Ikinci organizasyon eklendigi an KIRMIZIYA doner.** O an permissive
    dal artik "zararsiz borc" degil, AKTIF sizintidir.

Yani "ileride patlayacak" iddiasi, patlamanin GERCEKLESTIGI anda CI'i
durduran bir olcume cevrilmis oluyor.
"""

from __future__ import annotations

import psycopg2
import pytest

pytestmark = [pytest.mark.integration, pytest.mark.security]

# Yerel gelistirme DSN'i — uretim kimligi DEGIL (bkz. test_fsrs_schema_contract.py).
DSN = "postgresql://postgres:postgres@localhost:5434/kiro2"  # pragma: allowlist secret

# RLS + FORCE RLS tasidigi 1 Agu 2026'da dogrulanan ornek tablo.
ORNEK_TABLO = "refresh_tokens"
OLMAYAN_ORG = "00000000-0000-0000-0000-000000000000"


def _sorgula(
    sql: str,
    kurulum: list[str] | None = None,
    parametreler: tuple | None = None,
) -> int:
    """Tek sayi donduren sorguyu, istege bagli oturum kurulumuyla kosar.

    Deger enjeksiyonu icin DAIMA `parametreler` kullan. Tablo adlari
    parametrelenemez; onlar modul sabiti (kullanici girdisi DEGIL) ve
    `# noqa: S608` ile isaretli.
    """
    with psycopg2.connect(DSN) as baglanti, baglanti.cursor() as imlec:
        for komut in kurulum or []:
            imlec.execute(komut)
        imlec.execute(sql, parametreler)
        return imlec.fetchone()[0]


@pytest.fixture(scope="module")
def db_hazir() -> None:
    """DB veya `kiro2_app` rolu yoksa TUM modulu atla (testing.md #7)."""
    try:
        rol_var = _sorgula("SELECT count(*) FROM pg_roles WHERE rolname='kiro2_app'")
    except psycopg2.OperationalError as hata:
        pytest.skip(f"PostgreSQL :5434 erisilemez ({hata.__class__.__name__})")
    if not rol_var:
        pytest.skip("`kiro2_app` rolu yok — RLS kurulumu bu ortamda gecerli degil")


@pytest.fixture(scope="module")
def taban_satir(db_hazir: None) -> int:
    """Superuser'in gordugu satir sayisi — kiyaslamanin referansi."""
    n = _sorgula(f"SELECT count(*) FROM {ORNEK_TABLO}")  # noqa: S608
    if n == 0:
        pytest.skip(f"{ORNEK_TABLO} bos — atlatma olcumu anlamsiz olur")
    return n


def test_alet_dogrulamasi_ornek_tablo_rls_tasiyor(db_hazir: None) -> None:
    """KONTROL KOLU: olctugumuz tablo gercekten RLS+FORCE tasiyor mu.

    Tasimiyorsa asagidaki "atlatma" sonuclari anlamsizdir — RLS'siz bir
    tabloda herkes zaten her satiri gorur.
    """
    korumali = _sorgula(
        "SELECT count(*) FROM pg_class "
        "WHERE relname = %s AND relrowsecurity AND relforcerowsecurity",
        parametreler=(ORNEK_TABLO,),
    )
    assert (
        korumali == 1
    ), f"{ORNEK_TABLO} RLS/FORCE tasimiyor -> bu dosyadaki hicbir olcum gecerli degil"


def test_dogru_guc_ile_izolasyon_calisiyor(taban_satir: int) -> None:
    """MEKANIZMA SAGLAM MI: var olmayan bir org GUC'u 0 satir gormeli.

    Bu test kirmiziya donerse RLS motoru bozulmus demektir — permissive dal
    tartismasindan cok daha agir bir durum.
    """
    gorunen = _sorgula(
        f"SELECT count(*) FROM {ORNEK_TABLO}",  # noqa: S608
        kurulum=[
            "SET ROLE kiro2_app",
            f"SET LOCAL app.current_org_id = '{OLMAYAN_ORG}'",
        ],
    )
    assert gorunen == 0, (
        f"Yanlis org GUC'u ile {gorunen} satir goruldu (0 bekleniyordu) — "
        "RLS izolasyonu FIILEN CALISMIYOR"
    )


def test_permissive_dal_bugunku_davranisi_belgelenir(taban_satir: int) -> None:
    """GUC set EDILMEZSE politika her satiri geciriyor — OLCULEN olgu.

    Bu bir "gecmeli" test degil, bir KAYIT. Davranis degisirse (ornegin biri
    politikalari fail-closed yaparsa) bu test kirmiziya doner ve degisikligin
    bilincli olup olmadigi sorulur.
    """
    guc_yok = _sorgula(
        f"SELECT count(*) FROM {ORNEK_TABLO}",  # noqa: S608
        kurulum=["SET ROLE kiro2_app"],
    )
    guc_bos = _sorgula(
        f"SELECT count(*) FROM {ORNEK_TABLO}",  # noqa: S608
        kurulum=["SET ROLE kiro2_app", "SET LOCAL app.current_org_id = ''"],
    )
    assert guc_yok == taban_satir, (
        f"GUC'suz gorunum degisti: {guc_yok} != taban {taban_satir}. "
        "Politikalar fail-closed yapildiysa bu dosya guncellenmeli (#464)."
    )
    assert (
        guc_bos == taban_satir
    ), f"Bos-GUC gorunumu degisti: {guc_bos} != taban {taban_satir}."


def test_ikinci_organizasyon_permissive_dali_aktif_sizintiya_cevirir() -> None:
    """TUZAK DEDEKTORU — bu dosyanin varlik sebebi.

    Permissive dal bugun zararsiz cunku TEK organizasyon var. Ikinci
    organizasyon eklendigi an, GUC set etmeyen 161 router dosyasindan gelen
    her istek DIGER kiracinin satirlarini da gorur.

    O an bu test KIRMIZIYA doner ve is durur. "Ileride patlayacak" iddiasi
    boylece patlamanin gerceklestigi anda olculebilir hale gelir.
    """
    org_sayisi = _sorgula("SELECT count(*) FROM organizations")
    if org_sayisi <= 1:
        # Tek kiracili kurulum: permissive dal kabul edilebilir borc.
        return

    guc_yok = _sorgula(
        f"SELECT count(*) FROM {ORNEK_TABLO}",  # noqa: S608
        kurulum=["SET ROLE kiro2_app"],
    )
    pytest.fail(
        f"{org_sayisi} organizasyon var ve GUC'suz sorgu {guc_yok} satir goruyor.\n"
        "Permissive RLS dali artik 'zararsiz borc' DEGIL, AKTIF capraz-kiraci "
        "sizintisidir (#464/B5).\n"
        "YAPILACAK: (a) politikalarin ilk iki dalini kaldir (fail-closed), VE\n"
        "           (b) GUC'u router-basina Depends yerine tek bir middleware/\n"
        "               session katmaninda set et (bugun yalniz\n"
        "               core/dependencies.py:456, 163 router'in 2'sinde)."
    )


def test_politika_kalibi_tek_tip_kaldi(db_hazir: None) -> None:
    """F7: 79/79 politika ayni permissive kalipta, fail-closed SIFIR.

    Bir tablo fail-closed yapilirsa bu test kirmiziya doner — o da iyi bir
    sey: kismi gecis fark edilmeden ilerlememeli.
    """
    toplam = _sorgula("SELECT count(*) FROM pg_policies WHERE schemaname='public'")
    permissive = _sorgula(
        "SELECT count(*) FROM pg_policies WHERE schemaname='public' "
        "AND qual LIKE '%IS NULL%' AND qual LIKE '%= ''''%'"
    )
    assert toplam == permissive, (
        f"{toplam - permissive} politika artik permissive kalipta DEGIL. "
        "Fail-closed'a gecis basladiysa #464 planı ve bu dosya guncellenmeli."
    )


def test_kritik_tablolarin_rls_disinda_oldugu_belgelenir(db_hazir: None) -> None:
    """B5-c: users / question_bank / student_answers hic RLS tasimiyor.

    `question_bank` global icerik oldugu icin bu mesru olabilir; `users` ve
    `student_answers` icin migration'larda YAZILI bir gerekce YOK.
    Durum degisirse (RLS eklenirse) test kirmiziya doner ve karar belgelenir.
    """
    korumasiz = _sorgula(
        "SELECT count(*) FROM pg_class "
        "WHERE relname IN ('users','question_bank','student_answers') "
        "AND NOT relrowsecurity"
    )
    assert korumasiz == 3, (
        f"{3 - korumasiz} kritik tabloya RLS eklenmis. Bu bilincli bir karar "
        "ise #464 durum tablosuna ve migration docstring'ine gerekce yazilmali."
    )
