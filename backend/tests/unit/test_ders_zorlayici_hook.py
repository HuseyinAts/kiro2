"""`ders_zorlayici_kos.py` bekcisinin kendi bekcisi — S232.

NEDEN VAR
---------
Bu hook artik enforcement'in belkemigi: pre-push'ta kosacak test listesini
`.claude/lessons/ders_kaydi.yaml` icindeki `zorlayici:` alanlarindan TURETIR.
Yani "bir derse zorlayici yazmak" = "onu otomatik kapiya baglamak".

Belkemigi olmasi onu kirilgan da yapiyor: iki sessiz bozulma yolu var ve
ikisi de kapiyi ETKISIZ birakir, kirmizi vermeden:

  1. Ayristirici bozulur  -> liste BOS -> hicbir bekci kosmaz
  2. Bicim kapisi bozulur -> defterdeki bir satir pytest BAYRAGINA donusur
     (`-p no:cacheprovider`, `--co`) -> pytest hicbir sey kosmadan cikar

Deponun kendi dersi (`L-s219-yorum-cida-dusmez`): mesajdaki bilgi kaybolur,
yorumdaki bilgi silinebilir, yalnizca TEST kapida duser.

OZYINELEME YOK
--------------
`main()` sonunda pytest cagiriyor. Bu dosya defterde `zorlayici` olarak
kayitli, yani hook onu KOSUYOR. O yuzden burada `main()` DEGIL yalnizca saf
fonksiyonlar (`zorlayicilari_topla`, `bicim_gecersizleri`) sinaniyor.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

DEPO_KOKU = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(DEPO_KOKU / "backend" / "hooks"))

from ders_zorlayici_kos import (  # noqa: E402
    DEFTER,
    bicim_gecersizleri,
    dsn_maskele,
    dsn_ortami_uret,
    zorlayicilari_topla,
)

# Testlerde kullanilan SAHTE DSN'ler — gercek kimlik bilgisi DEGIL.
# (Gercek deger `backend/.env`'den runtime'da okunur, koda GOMULMEZ.)
_SAHTE_PG = (
    "postgresql://kullanici:parola@localhost:5434/kiro2"  # pragma: allowlist secret
)
_SAHTE_SQLITE = "sqlite+aiosqlite:///:memory:"

# ---------------------------------------------------------------------------
# BICIM KAPISI — pytest ARGV'sine gitmesi guvenli olmayan degerler
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "kotu",
    [
        pytest.param("-p no:cacheprovider", id="pytest-bayragi"),
        pytest.param("--co", id="pytest-uzun-bayragi"),
        pytest.param("backend/../../etc/passwd.py", id="ust-dizine-kacis"),
        pytest.param("backend/tests/../../../x.py", id="gomulu-ust-dizin"),
        pytest.param("frontend/src/x.py", id="backend-disi"),
        pytest.param("backend/tests/unit", id="dosya-degil-dizin"),
        pytest.param("backend/tests/unit/x.txt", id="py-degil"),
    ],
)
def test_bicim_kapisi_guvensiz_degeri_reddeder(kotu: str):
    """Bu degerlerden biri gecerse pytest hicbir bekci kosmadan yesil donebilir."""
    assert bicim_gecersizleri([kotu]) == [kotu], (
        f"{kotu!r} bicim kapisindan GECTI — pytest ARGV'sine boyle bir deger "
        "girerse kapi sessizce etkisizlesir (bayrak olarak yorumlanir veya "
        "depo disina isaret eder)."
    )


@pytest.mark.parametrize(
    "iyi",
    [
        "backend/tests/unit/test_ders_kaydi.py",
        "backend/tests/db/test_question_bank_invariants.py",
        "backend/tests/integration/test_icerik_gecerliligi.py",
    ],
)
def test_bicim_kapisi_mesru_yolu_kabul_eder(iyi: str):
    """Kontrol kolu: kapi cok siki olursa gercek bekcileri kilitler."""
    assert bicim_gecersizleri([iyi]) == []


def test_bicim_kapisi_yalniz_kotu_olani_ayiklar():
    """Karisik listede iyi/kotu ayrimi — hepsini reddetmek de bir kusurdur."""
    iyi = "backend/tests/unit/test_ders_kaydi.py"
    assert bicim_gecersizleri([iyi, "-p x", "backend/a/../b.py"]) == [
        "-p x",
        "backend/a/../b.py",
    ]


# ---------------------------------------------------------------------------
# AYRISTIRICI — defterden liste turetme
# ---------------------------------------------------------------------------


def test_defter_ayristirici_bos_donmemeli():
    """Bos liste bir BULGU degil, ALET ARIZASI adayidir.

    S219 dersi: bir olcum aletinde YANLIS-SIFIR tek kabul edilemez hata
    turudur — isi sessizce 'bitmis' gosterir. Burada da bos liste
    'enforcement yok' demektir ama kirmizi vermez.
    """
    yollar = zorlayicilari_topla()
    assert yollar, (
        "Defterden hic `zorlayici` turetilemedi. Ya ayristirici regex'i bozuldu "
        "ya defterin girinti bicimi degisti. Her iki halde de pre-push kapisi "
        "HICBIR bekci kosmuyor demektir."
    )


def test_defterdeki_her_zorlayici_diskte_var():
    """Defter YALAN SOYLEYEMEZ: isaret ettigi dosya var olmali.

    Silinen/tasinan bir bekci dosyasi defterde kalirsa hook her push'ta
    patlar; bu test o durumu push'tan ONCE gosterir.
    """
    eksik = [y for y in zorlayicilari_topla() if not (DEPO_KOKU / y).exists()]
    assert not eksik, (
        f"Defterde var, diskte YOK: {eksik}. Ders ya duzeltilmeli ya "
        "`zorlayici: null` yapilmali (bosluk gorunur kalsin)."
    )


def test_defterden_turetilen_liste_tekil_ve_sirali():
    """Ayni dosyayi iki kez kosmak bosa zaman; sira determinizm icin."""
    yollar = zorlayicilari_topla()
    assert len(yollar) == len(set(yollar)), "liste tekil degil"
    assert yollar == sorted(yollar), "liste sirali degil"


def test_ayristirici_null_ve_bos_degerleri_atlar(tmp_path, monkeypatch):
    """`zorlayici: null` bir bosluk isaretidir — yol olarak ISLENMEMELI.

    141 dersin 101'i null; biri bile yol sanilirsa hook her push'ta duser.
    """
    sahte = tmp_path / "ders_kaydi.yaml"
    sahte.write_text(
        "- id: A\n"
        "  zorlayici: null\n"
        "- id: B\n"
        "  zorlayici: ~\n"
        "- id: C\n"
        "  zorlayici: backend/tests/unit/test_ders_kaydi.py\n"
        "- id: D\n"
        "  zorlayici: backend/tests/unit/test_ders_kaydi.py\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("ders_zorlayici_kos.DEFTER", sahte)

    assert zorlayicilari_topla() == ["backend/tests/unit/test_ders_kaydi.py"]


def test_defter_gercek_dosya_ve_okunabilir():
    """Hook'un okudugu defter, bu depodaki gercek defter olmali."""
    assert DEFTER.exists(), f"ders defteri yok: {DEFTER}"
    assert DEFTER.name == "ders_kaydi.yaml"


# ---------------------------------------------------------------------------
# DSN ENJEKSIYONU — A3 (19 Agu 2026)
#
# OLCULEN KUSUR: kapi 19 bekci dosyasi kosuyordu ama
# `tests/db/test_question_bank_invariants.py` her push'ta **3/3 SKIP** veriyordu:
#
#     pytest tests/db/test_question_bank_invariants.py -q -rs   ->  sss / EXIT=0
#     SKIPPED :102  Gevsek mod (KIRO2_STRICT_DB_INVARIANTS yok)
#     SKIPPED :138  Gercek PostgreSQL yok (DSN yok)
#     SKIPPED :169  ayni
#
# Yani "19 bekci her push'ta kosuyor" bir DOSYA sayimiydi, ASSERT sayimi degil.
# Hacim ve benzersizlik invaryantlari -- tam da Y11 gocu sirasinda ihtiyac
# duyulacak olanlar -- kapali duruyordu.
#
# NEDEN STRICT VARSAYILAN ACIK DEGIL: dosyanin kendi docstring'i (12 Agu) taze
# bir gelistirme makinesinde icerigin OLMAMASININ mesru oldugunu belgeliyor.
# O karar korunuyor: STRICT yalnizca GERCEK bir postgres DSN cozulebildiginde
# aciliyor. Cozulemezse hook gurultulu uyarir ama push'u bloklamaz.
# ---------------------------------------------------------------------------


def test_env_dosyasindaki_postgres_dsni_cozulur():
    """Kapi DSN'i `backend/.env`'den okumali — koda GOMULMEMELI."""
    ortam = dsn_ortami_uret({}, f"DATABASE_URL={_SAHTE_PG}\n")
    assert ortam.get("KVKK_VERIFY_DSN") == _SAHTE_PG


def test_dsn_cozulunce_strict_mod_da_acilir():
    """DSN tek basina YETMEZ: `test_invaryant_olculebilir_olmali` STRICT ister.

    Ikisinden biri eksikse bekci yine skip eder ve kapi yalan soyler.
    """
    ortam = dsn_ortami_uret({}, f"DATABASE_URL={_SAHTE_PG}\n")
    assert ortam.get("KIRO2_STRICT_DB_INVARIANTS") == "1"


def test_sqlite_dsni_reddedilir():
    """Sessizce sqlite'a DUSULMEZ (`L-s229-test-dsn-sessizce-sqlite-olur`).

    S229'da 11 test `no such table: information_schema.columns` ile dustu:
    cozucu `DATABASE_URL`e guvenmisti, test ortami onu sqlite'a eziyordu.
    Burada sqlite gorulurse DSN YOK sayilir -- yanlis bir DB'yi olcmektense
    olcmemek yeglenir.
    """
    ortam = dsn_ortami_uret({}, f"DATABASE_URL={_SAHTE_SQLITE}\n")
    assert ortam == {}, f"sqlite DSN kabul edildi: {ortam}"


def test_dsn_yoksa_strict_acilmaz():
    """Taze makinede icerik olmamasi MESRU — her push'u kirmak gurultu olur.

    Kontrol kolu niteliginde: bu assert olmazsa `dsn_ortami_uret` her zaman
    STRICT dondurup DB'siz makinelerde push'u bloklardi.
    """
    assert dsn_ortami_uret({}, None) == {}
    assert dsn_ortami_uret({}, "BASKA_ANAHTAR=1\n") == {}


def test_mevcut_ortam_env_dosyasindan_oncelikli():
    """Operator elle DSN verdiyse dosya onu EZMEMELI."""
    elle = "postgresql://x:y@baska-host:5555/baska_db"
    ortam = dsn_ortami_uret({"KVKK_VERIFY_DSN": elle}, f"DATABASE_URL={_SAHTE_PG}\n")
    assert ortam.get("KVKK_VERIFY_DSN") == elle


def test_sqlite_database_url_postgres_kvkk_yi_golgelemez():
    """Dosyada ikisi de varsa postgres olan kazanir.

    `backend/conftest.py` DATABASE_URL'i sqlite'a eziyor; bu satir gercek
    bir DSN'i golgeleyebilecek tek yer.
    """
    icerik = f"DATABASE_URL={_SAHTE_SQLITE}\nKVKK_VERIFY_DSN={_SAHTE_PG}\n"
    assert dsn_ortami_uret({}, icerik).get("KVKK_VERIFY_DSN") == _SAHTE_PG


def test_dsn_asyncpg_ye_cevrilmez():
    """Surucu donusumu tuketicinin isi (`tests/e2e/pg_dsn.py::resolve_pg_dsn`).

    Burada da cevirmek ikinci bir tanim olurdu; iki tanim ayrisirsa hangisinin
    kosulmakta oldugu olculemez hale gelir.
    """
    ortam = dsn_ortami_uret({}, f"DATABASE_URL={_SAHTE_PG}\n")
    assert "asyncpg" not in ortam["KVKK_VERIFY_DSN"]


def test_dsn_loglanirken_parola_maskelenir():
    """Kapi her push'ta stdout'a yaziyor — DSN parolasi oraya DUSMEMELI.

    Bu depoda bir kez yasandi: celery logunda duz-metin DB parolasi (#475).
    Ayni sinif, farkli kanal.
    """
    maskeli = dsn_maskele(_SAHTE_PG)
    assert "parola" not in maskeli, f"parola sizdi: {maskeli}"
    assert "localhost:5434" in maskeli, "maske teshis degerini de yok etmemeli"
