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
`get_current_tenant` ise **2** router dosyasinda (`api/org_api.py`,
`api/org_billing_api.py`). Olcum komutlari (1 Agu 2026, backend/ icinden):

    ls api/*.py app/api/*.py | wc -l                    -> 153
    grep -rl 'APIRouter(' api/ app/api/ routers/ | wc -l -> 155
    grep -rl 'get_current_tenant' api/ app/api/          -> 2 (+2 .pyc artefakti)

Onceki surumde yazan "163 router" hicbir sayma yonteminden cikmiyordu (A.4).

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

Yani "ileride patlayacak" iddiasi, patlamanin GERCEKLESTIGI anda olculebilir
hale gelmis oluyor.

BU BEKCI NEREDE FIILEN KOSUYOR (A.4 — iddia duzeltmesi)
--------------------------------------------------------
Onceki surum "CI'i durdurur / is durur" diyordu. Olculdu, DOGRU DEGILDI:

  - `ci.yml:281` testleri marker filtresiz kosuyor, yani bu dosya TOPLANIR —
    ama `ci.yml` `on:` = [main, master, develop]; aktif dal master'dan 334
    commit onde ve PR yok, dolayisiyla is HIC tetiklenmedi (#468 / F8-b).
  - `deploy.yml:225` `-m integration` bacagina sahip, ama tetigi
    `push: tags: v*.*.*` ve eslesen tag sayisi **0** -> hic kosmadi.
  - Kosarsa bile `psycopg2` CI'da kurulu degildi; artik `importorskip` ile
    ERROR yerine SKIP'e dusuyor (bkz. tests/test_ci_collection_guard.py).

Yani bugun bu dosya **yalniz PG:5434'e erisebilen ortamlarda** (gelistirici
makinesi, DB'li bir is) kirmiziya donebilir. Merge kapisi olmasi #468'e bagli.
Bu bir eksiklik degil, BILINEN ve olculmus bir kapsam sinniridir.
"""

from __future__ import annotations

import pytest

# `psycopg2-binary` CI'da KURULU DEGIL (requirements.txt psycopg v3 kuruyor;
# sqlalchemy'de psycopg2 yalniz [postgresql*] extra'sinda). ci.yml:281 testleri
# marker filtresiz + `-x` ile kostugu icin korumasiz import TUM job'u dusururdu.
# Bekci: tests/test_ci_collection_guard.py
psycopg2 = pytest.importorskip("psycopg2")

pytestmark = [pytest.mark.integration, pytest.mark.security]

# Yerel gelistirme DSN'i — uretim kimligi DEGIL (bkz. test_fsrs_schema_contract.py).
DSN = "postgresql://postgres:postgres@localhost:5434/kiro2"  # pragma: allowlist secret

# RLS + FORCE RLS tasidigi 1 Agu 2026'da dogrulanan ornek tablo.
ORNEK_TABLO = "refresh_tokens"
OLMAYAN_ORG = "00000000-0000-0000-0000-000000000000"

# 1 Agu 2026 canli olcumu (psql -p 5434 -d kiro2):
#   pg_policies (public)                        -> 79
#   permissive kalip (IS NULL + = '')           -> 79
#   relrowsecurity / relforcerowsecurity tablo  -> 79 / 79
#
# TABAN neden gerekli (A.4b): onceki surum yalniz `toplam == permissive`
# assert ediyordu — bu bir ORAN esitligi. 79 politikadan 78'i DROP edilse
# `toplam=1, permissive=1` olur ve test YESIL kalirdi; yani RLS kapsaminin
# neredeyse tamamen kaldirilmasi fark edilmeden gecerdi.
# Bu sabiti dusurmek BILINCLI bir karar olmali (#464 durum tablosuna yaz).
#
# 041a9181271c (13 Agu 2026) ile kalip TEK TIP OLMAKTAN CIKTI: ad6ba3bbe485
# kapsamindaki 73 tablo fail-closed, kapsam disindaki 6 tablo (billing 4 +
# organizations + parent_link_codes) permissive-when-unset kaldi. Asagidaki
# iki sabit bu bilincli ayrimi sabitler.
FAIL_CLOSED_TABAN = 73
PERMISSIVE_TABAN = 6
POLITIKA_TABANI = FAIL_CLOSED_TABAN + PERMISSIVE_TABAN


def _kiracilik_yargisi(org_sayisi: int) -> str:
    """`organizations` sayimini yoruma cevirir: 'kor' | 'tek' | 'cok'.

    Saf fonksiyon olmasinin sebebi (A.4c): canli DB'de org sayisi 1'dir ve
    0 URETILEMEZ, dolayisiyla korluk dali calisma zamaninda hic tetiklenemez —
    civilenmemis bir assert olurdu. Ayrilinca uc dal da sinanabiliyor
    (`test_alet_dogrulamasi_sifir_organizasyon_korluk_sayilir`).

    Onceki surum `org_sayisi <= 1` yaziyordu ve 0 ile 1'i AYNI kefeye koyuyordu:
    sayim RLS/rol yuzunden susturulsa dedektor sessizce "tek kiraci" der,
    "sizinti yok" sonucu anlamsiz olurdu.
    """
    if org_sayisi < 1:
        return "kor"
    if org_sayisi == 1:
        return "tek"
    return "cok"


def _kalip_ihlali(
    toplam: int, permissive: int, taban: int, beklenen_permissive: int
) -> str | None:
    """Politika kalibi ihlalini aciklar; ihlal yoksa None.

    Saf fonksiyon olmasinin sebebi: "78 politika silinirse yesil kalir"
    vakumu canli DB'de UYGULANAMAZ (79 politikayi silip geri koymak yikici).
    Mantik ayrildigi icin ayni senaryo sentetik girdiyle SINANABILIR —
    bkz. `test_alet_dogrulamasi_oran_esitligi_tek_basina_yetmiyor`.

    041a9181271c'den (13 Agu 2026) itibaren kalip TEK TIP DEGIL: bir kismi
    permissive-when-unset, geri kalani fail-closed. Bu yuzden "hepsi permissive
    olmali" yerine "permissive SAYISI TAM beklenen_permissive olmali" kontrol
    edilir — ne fail-closed'a fazladan gecis (permissive azalir) ne de
    fail-closed'in geri sokulmesi (permissive artar) fark edilmeden gecsin.
    `taban`/`beklenen_permissive` caller'dan gelir (bkz. test_politika_kalibi_korundu
    -- bu ortamdaki bilinen tablo/kolon eksikligine gore ayarlanir).
    """
    if toplam < taban:
        return (
            f"Politika sayisi {toplam}, taban {taban}. RLS kapsami daraltilmis "
            "olabilir — oran esitligi bunu GIZLER (A.4b)."
        )
    if permissive != beklenen_permissive:
        return (
            f"Permissive politika sayisi {permissive}, beklenen "
            f"{beklenen_permissive}. Fail-closed/permissive ayrimi degismis "
            "(041a9181271c kapsamini kontrol et)."
        )
    return None


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


def test_fail_closed_dal_bugunku_davranisi_belgelenir(taban_satir: int) -> None:
    """041a9181271c'den itibaren ORNEK_TABLO FAIL-CLOSED — OLCULEN olgu.

    Onceki surum burada PERMISSIVE davranisi belgeliyordu (GUC yok/bos ->
    tum satirlar gorunur); ad6ba3bbe485'in ALL_RLS_TABLES kapsamindaki 73
    tablo (ORNEK_TABLO=refresh_tokens dahil) artik FAIL-CLOSED: GUC yok/bos
    ise HICBIR satir gorunmez, sadece DOGRU org GUC'u satirlari acar.

    Bu bir "gecmeli" test degil, bir KAYIT. Davranis degisirse (ornegin biri
    permissive'e geri donerse) bu test kirmiziya doner ve degisikligin
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
    assert guc_yok == 0, (
        f"GUC'suz gorunum {guc_yok} satir gosterdi (0 bekleniyordu) — "
        "fail-closed politika artik uygulanmiyor olabilir."
    )
    assert guc_bos == 0, f"Bos-GUC gorunumu {guc_bos} satir gosterdi (0 bekleniyordu)."

    dogru_org = _sorgula(f"SELECT organization_id FROM {ORNEK_TABLO} LIMIT 1")  # noqa: S608
    guc_dogru = _sorgula(
        f"SELECT count(*) FROM {ORNEK_TABLO}",  # noqa: S608
        kurulum=["SET ROLE kiro2_app", f"SET LOCAL app.current_org_id = '{dogru_org}'"],
    )
    assert guc_dogru == taban_satir, (
        f"Dogru org GUC'u ile {guc_dogru} satir goruldu (taban {taban_satir} "
        "bekleniyordu) — fail-closed politika 'hepsini engelle' ile 'dogru "
        "filtrele' arasinda farkli davraniyor olabilir."
    )


def test_alet_dogrulamasi_sifir_organizasyon_korluk_sayilir() -> None:
    """A.4c KORLUGU SENTETIK OLARAK URETILIR.

    Canli DB'de `organizations` 1 satir ve 0 uretilemez; bu yuzden korluk
    dali calisma zamaninda hic tetiklenemez. Yargi ayrildigi icin uc dal da
    burada sinanir — ozellikle 0 ile 1'in AYRI yargilar oldugu.
    """
    assert _kiracilik_yargisi(0) == "kor", (
        "0 organizasyon 'kor' sayilmadi -> onceki `<= 1` davranisi geri gelmis; "
        "susturulmus bir sayim sessizce 'tek kiraci' diye gecer"
    )
    assert (
        _kiracilik_yargisi(1) == "tek"
    ), "1 organizasyon 'tek' sayilmadi -> tek-kiracili kurulum yanlis raporlanir"
    assert (
        _kiracilik_yargisi(2) == "cok"
    ), "2 organizasyon 'cok' sayilmadi -> tuzak dedektoru hic atesleyemez"


def test_ikinci_organizasyon_permissive_dali_aktif_sizintiya_cevirir(
    db_hazir: None,
) -> None:
    """TUZAK DEDEKTORU — bu dosyanin varlik sebebi.

    Permissive dal bugun zararsiz cunku TEK organizasyon var. Ikinci
    organizasyon eklendigi an, GUC set etmeyen 151 router dosyasindan
    (153'un 2'si haric) gelen her istek DIGER kiracinin satirlarini da gorur.

    O an bu test KIRMIZIYA doner. Nerede kirmiziya donebilecegi icin modul
    docstring'indeki "BU BEKCI NEREDE FIILEN KOSUYOR" bolumune bak — "is
    durur" iddiasi olculdu ve duzeltildi (A.4).

    `db_hazir` fixture'i A.4 icin eklendi: onceki surum HICBIR fixture
    almiyordu, dolayisiyla PG:5434 erisilemeyen ortamda (CI runner'i, ikinci
    gelistirici makinesi) SKIP degil `OperationalError` -> ERROR veriyordu.
    Dosyadaki diger bes test zaten korunuyordu; yalniz bu biri aciktaydi.
    """
    org_sayisi = _sorgula("SELECT count(*) FROM organizations")
    yargi = _kiracilik_yargisi(org_sayisi)

    # KONTROL KOLU (A.4c): 0 saglikli bir kurulumda imkansizdir.
    assert yargi != "kor", (
        "organizations 0 satir gorundu — dedektor kor. Sayim RLS/rol yuzunden "
        "susturulmus olabilir; 'sizinti yok' sonucu ANLAMSIZ."
    )
    if yargi == "tek":
        # Tek kiracili kurulum: permissive dal kabul edilebilir borc.
        return

    guc_yok = _sorgula(
        f"SELECT count(*) FROM {ORNEK_TABLO}",  # noqa: S608
        kurulum=["SET ROLE kiro2_app"],
    )
    # 041a9181271c'den itibaren ORNEK_TABLO (refresh_tokens) fail-closed —
    # GUC'suz sorgu 0 satir gorur, gercek sizinti YOK. Kosulsuz fail() burada
    # yanlis-pozitif uretirdi; artik gercekten sizan (guc_yok>0) durumda tetiklenir.
    if guc_yok == 0:
        return
    pytest.fail(
        f"{org_sayisi} organizasyon var ve GUC'suz sorgu {guc_yok} satir goruyor.\n"
        "Permissive RLS dali artik 'zararsiz borc' DEGIL, AKTIF capraz-kiraci "
        "sizintisidir (#464/B5).\n"
        "YAPILACAK: (a) politikalarin ilk iki dalini kaldir (fail-closed), VE\n"
        "           (b) GUC'u router-basina Depends yerine tek bir middleware/\n"
        "               session katmaninda set et (bugun yalniz\n"
        "               core/dependencies.py:456; get_current_tenant 153\n"
        "               router dosyasinin 2'sinde)."
    )


def test_alet_dogrulamasi_oran_esitligi_tek_basina_yetmiyor() -> None:
    """A.4b VAKUMU SENTETIK OLARAK URETILIR (73 fail-closed + 6 permissive kalibi).

    (1, 1) girdisi "73 fail-closed politika silinmis, sadece 1 permissive
    kalmis" durumudur: taban asilmiyor. Ayrica saglikli kalipta (79, 6) VE
    permissive sayisi bir yonde de kaysa (5 veya 7) ihlal yakalanmali —
    "hepsi ayni olmali" degil "TAM 6 permissive olmali" kontrolu.
    """
    assert (
        _kalip_ihlali(1, 1, POLITIKA_TABANI, PERMISSIVE_TABAN) is not None
    ), "Taban altina dusen senaryo ihlal SAYILMADI -> taban assert'i yuk tasimiyor"
    assert (
        _kalip_ihlali(
            POLITIKA_TABANI, PERMISSIVE_TABAN, POLITIKA_TABANI, PERMISSIVE_TABAN
        )
        is None
    ), "Saglikli 73 fail-closed + 6 permissive kalibi ihlal sayildi -> yanlis-pozitif"
    assert (
        _kalip_ihlali(
            POLITIKA_TABANI, PERMISSIVE_TABAN - 1, POLITIKA_TABANI, PERMISSIVE_TABAN
        )
        is not None
    ), "Bir permissive politika fail-closed'a kaymis -> kalip kontrolu kayboldu"
    assert (
        _kalip_ihlali(
            POLITIKA_TABANI, PERMISSIVE_TABAN + 1, POLITIKA_TABANI, PERMISSIVE_TABAN
        )
        is not None
    ), "Bir fail-closed politika permissive'e geri sokulmus -> kalip kontrolu kayboldu"


# 13 Agu 2026 - 041a9181271c 3 tablo (daily_plans, learning_progress_daily,
# yks_exam_goals) + 1 kolonun (data_processing_agreements.organization_id) bu
# ortamda eksik oldugunu UYARI ile bildirmisti. cdea871deea9 hepsini yaratti/
# ekledi (bkz. test_learning_path_daily_tables.py) -- drift KAPANDI. Bu sayilar
# yeniden pozitif olursa `alembic upgrade head` ciktisindaki UYARI satirlarindan
# guncelle -- tahmin etme.
BILINEN_EKSIK_TABLO_SAYISI = 0
BILINEN_EKSIK_KOLON_SAYISI = 0


def test_politika_kalibi_korundu(db_hazir: None) -> None:
    """F7: politika sayisi bu ortamin GERCEK tabaninin altina dusmedi VE kalip korundu.

    Iki ayri sey olculur (A.4b):
      - KAPSAM: `toplam >= beklenen_taban`          — politikalar sessizce silinmesin
      - KALIP : `permissive == beklenen_permissive` — ayrim kaymasin

    `beklenen_taban`/`beklenen_permissive` sabit 79/6 DEGIL -- bu ortamdaki
    bilinen tablo/kolon eksikligi (BILINEN_EKSIK_*) dusulerek hesaplanir,
    041a9181271c'nin kendi introspeksiyonuyla TUTARLI kalsin diye.
    """
    toplam = _sorgula("SELECT count(*) FROM pg_policies WHERE schemaname='public'")
    permissive = _sorgula(
        "SELECT count(*) FROM pg_policies WHERE schemaname='public' "
        "AND qual LIKE '%IS NULL%' AND qual LIKE '%= ''''%'"
    )
    beklenen_taban = (
        POLITIKA_TABANI - BILINEN_EKSIK_TABLO_SAYISI - BILINEN_EKSIK_KOLON_SAYISI
    )
    beklenen_permissive = PERMISSIVE_TABAN - BILINEN_EKSIK_KOLON_SAYISI
    ihlal = _kalip_ihlali(toplam, permissive, beklenen_taban, beklenen_permissive)
    assert ihlal is None, ihlal


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
