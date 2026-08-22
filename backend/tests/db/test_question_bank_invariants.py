"""question_bank hacim + benzersizlik invaryantı — 5 Ağu 2026 içerik kaybının bekçisi.

NEDEN VAR
---------
5 Ağu 2026'da `backend/scripts/clean_import_question_bank.py` (takipsiz, o gün hiç
commit yok) `TRUNCATE TABLE question_bank CASCADE` çalıştırıp yerine 21 sentetik
tohum sorusu yazdı. Tablo 187.835 satırdan 2.304 satıra düştü. Öğrenci kapısı
`mv_safe_for_beta` 2.200 satır göstermeye devam etti — ama o 2.200 satırın altında
**19 benzersiz soru** vardı. Fizik, Biyoloji ve Kimya birer soruya inmişti.

Kayıp bir gün fark edilmedi, çünkü hiçbir kontrol ÇEŞİTLİLİĞE bakmıyordu:

  - satır sayısı (2.304) "veri var" gibi görünüyordu;
  - benzersizlik kısıtı `uq_qb_soru_hash_active` ölü DEĞİLDİ, çalışıyordu — ama
    script `soru_hash`'i kimlik-tuzlu (`soru_id + metin`) ürettiği için her kopya
    farklı hash aldı ve kısıtın ETRAFINDAN dolaşıldı.

Bu yüzden iki ayrı eşik var ve ikisi birbirinden bağımsız düşer:

    hacim tabanı       :   2.304  <  150.000   -> DÜŞER
    benzersizlik oranı :   0,009  <  0,90      -> DÜŞER

Tek eşik yetmezdi:

  - yalnız hacim  -> 150.000 satırın hepsi aynı metnin kopyası olsa GEÇERDİ;
  - yalnız oran   -> 187.835'ten 20.000'e meşru görünümlü bir küçülme KAÇARDI.

Ders: **hacim ≠ çeşitlilik.** Sağlıklı görünen bir satır sayısı, arkasında kaç
farklı soru olduğunu söylemez.

Bu test gerçek PostgreSQL'e karşı koşar. Vekil ölçüm (tablo var mı, kolon var mı)
kasıtlı olarak kullanılmadı: S203'te "tablo var" vekili aylarca yeşil kalırken
`/fsrs/due` canlıda 500 dönüyordu.
"""

from __future__ import annotations

import asyncio
import inspect
import os
import sys

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from tests.e2e.pg_dsn import SKIP_REASON, resolve_pg_dsn

pytestmark = pytest.mark.db_invariant

# 187.835'in ~%80'i. Meşru kalite elemesi için pay bırakır, felaketi yakalar.
MIN_SATIR = 150_000

# benzersiz / satır. Sağlıklı havuzda ~0,99; 5 Ağu'da 0,009 idi.
MIN_BENZERSIZLIK = 0.90


# ---------------------------------------------------------------------------
# SIKI MOD — 12 Ağu 2026, X10
#
# ÖLÇÜLEN KUSUR: 12 Ağu'da question_bank GERÇEKTEN 0 satırken bu dosya koşuldu
# ve `2 skipped` verdi. FAIL yok. Bekçi, korumak için yazıldığı felaketin tam
# ortasında sustu. Sebep basit: DSN ortam değişkeni yoktu, fixture skip etti.
#
# Kanıt (aynı gün, aynı DB):
#     pytest tests/db/test_question_bank_invariants.py            -> 2 skipped
#     KVKK_VERIFY_DSN=postgresql://...:5434/kiro2 pytest ...      -> 2 failed
#                     "question_bank 0 satır < taban 150.000"
# Yani eşikler DOĞRU; eşiğe HİÇ VARILMIYORDU.
#
# Bu, bu depoda aynı yapısal kusurun ÜÇÜNCÜ örneği:
#   1. Golden Flow _login: 429 -> pytest.skip            (#462'de onarıldı)
#   2. tests/test_migrations.py:37 skipif(True) KOŞULSUZ  (U25, 16 skipped)
#   3. bu dosya                                           (X10)
# golden-flows.md ve rapor §D.1/#16: "skip ASLA FAIL üretmez."
#
# NEDEN VARSAYILAN AÇIK DEĞİL: taze bir geliştirme makinesinde içeriğin
# olmaması MEŞRUDUR (12 Ağu ortam ölçümü: question_bank 0, d-dataset/ yok,
# users 3 -> kullanıcı "farklı/taze ortam" diye sınıflandırdı). Orada her
# koşumu kırmak gürültü olur. Sıkı mod, içeriğin OLMASI GEREKEN ortamlar
# içindir: CI, staging, üretim-yakını.
#
# AÇMAK İÇİN:  KIRO2_STRICT_DB_INVARIANTS=1 pytest tests/db/ -m db_invariant
# ---------------------------------------------------------------------------
STRICT = os.getenv("KIRO2_STRICT_DB_INVARIANTS") == "1"


@pytest.mark.asyncio
async def test_invaryant_olculebilir_olmali():
    """SIKI modda bekçi ÖLÇEBİLİR olmalı — ölçememek de bir alarmdır.

    NEDEN AYRI (ve fixture'sız) BİR TEST:
    Sıkı kontrolü `db_session` fixture'ının içine koymak denendi; `pytest.fail()`
    bir fixture içinde ERROR üretiyor, FAILED değil. `.claude/rules/
    audit-methodology.md` (1 Ağu 2026): "Mutasyon sonucu `failed` DEĞİL `error`
    ise ölçüm GEÇERSİZ." Aynı titizlik üretim kapısı için de geçerli: ERROR,
    altyapı arızasıyla karışır — ki bu belirsizlik zaten bu hata sınıfının
    kaynağı. Bu yüzden kontrol, bağımlılığı olmayan düz bir teste taşındı:
    temiz FAILED üretir.

    ÖLÇÜLDÜ (12 Ağu): fixture içinde -> `2 errors`; burada -> `1 failed`.

    22 AĞU 2026 — İKİNCİ KOL: "DSN var" ölçüm DEĞİL, VEKİLDİR.
    12 Ağu'daki sürüm yalnız `assert resolve_pg_dsn()` diyordu. `pg_dsn.py`
    hiç bağlanmaz, sadece dize inceler. Ölçüldü:

        STRICT=1 + KVKK_VERIFY_DSN=...@localhost:5999/kiro2 (ölü port)
            -> 1 passed, 2 skipped        EXIT=0

    Yani sessiz skip, sessiz bir VEKİLLE değiştirilmişti; bekçi yine
    "korumak için yazıldığı felaketin ortasında" susabiliyordu. Bu dosyanın
    kendi docstring'i vekil ölçümü zaten yasaklıyor (S203). Bu yüzden artık
    DSN'e GERÇEKTEN bağlanılıp `question_bank` sayılıyor.

    `SELECT 1` YETMEZ, kasıtlı olarak `question_bank` sayılıyor: 19 Ağu'da
    ölçüldüğü gibi (aşağıdaki benzersizlik testinin notu) S210 split'i
    sorguyu koşulamaz hale getirmişti ve bunu kimse görmedi. Doğru tabloya
    dokunmayan bir canlılık ölçümü o sınıfı kaçırır.
    """
    if not STRICT:
        pytest.skip(
            "Gevşek mod. Sıkı kontrol için: KIRO2_STRICT_DB_INVARIANTS=1 "
            "(içeriğin bulunması GEREKEN ortamlarda: CI, staging, üretim-yakını)"
        )
    dsn = resolve_pg_dsn()
    assert dsn, (
        "SIKI MOD: question_bank invaryant bekçisi ÖLÇEMEDİ — gerçek PostgreSQL "
        f"DSN'i yok.\n{SKIP_REASON}\n"
        "Bu ortam içerik taşımıyorsa KIRO2_STRICT_DB_INVARIANTS'ı set etme; "
        "taşıyorsa DSN ver. Sessiz skip yasak: 12 Ağu 2026'da question_bank "
        "0 satırken bu paket '2 skipped' verdi ve hiçbir alarm çalmadı."
    )

    hata: Exception | None = None
    engine = create_async_engine(dsn, poolclass=NullPool)
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT count(*) FROM question_bank"))
    except Exception as exc:
        hata = exc
    finally:
        await engine.dispose()

    # `@` öncesi ATILIYOR: DSN parolası assert mesajına ve oradan CI log'una
    # düşmemeli (bu depoda bir kez düştü — FAZ 0-4, Celery log'u).
    assert hata is None, (
        "SIKI MOD: question_bank invaryant bekçisi ÖLÇEMEDİ — DSN çözüldü ama "
        f"DB'ye ULAŞILAMADI: {dsn.rsplit('@', 1)[-1]} -> "
        f"{type(hata).__name__}: {hata}\n"
        "Bekçinin susması ile içeriğin sağlam olması AYNI ŞEY DEĞİLDİR: "
        "aşağıdaki iki invaryant bu koşumda skip oldu, yani hacim ve "
        "çeşitlilik BU KOŞUMDA ÖLÇÜLMEDİ. Postgres'i ayağa kaldır (port 5434) "
        "veya bu ortam içerik taşımıyorsa KIRO2_STRICT_DB_INVARIANTS'ı set etme."
    )


@pytest_asyncio.fixture
async def db_session():
    dsn = resolve_pg_dsn()
    if not dsn:
        pytest.skip(SKIP_REASON)

    engine = create_async_engine(dsn, poolclass=NullPool)
    try:
        conn = await engine.connect()
    except Exception as exc:
        await engine.dispose()
        pytest.skip(f"DB erişilemiyor: {type(exc).__name__}")

    maker = async_sessionmaker(bind=conn, class_=AsyncSession, expire_on_commit=False)
    session = maker()
    try:
        yield session
    finally:
        await session.close()
        await conn.close()
        await engine.dispose()


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Y11 AÇIK: canlı question_bank 3.616 satır, taban 150.000 (o 36.967 satır 20 Ağu 2026'da SİLİNDİ — S238, yedek `*_cop_yedek_20260820`). Bu KIRMIZI "
        "DOĞRU — 17 Ağu 2026'da içerik sentetik dolguyla ikame edildi (S231/S232, "
        "40/40 okundu, 0 servis edilebilir). Eşik BAYAT DEĞİL: 187.835'e göre "
        "kalibre edilmiş ve `kiro2_temp` bugün tam o sayıyı taşıyor.\n"
        "Bu işaret, bekçiyi pre-push kapısına bağlayabilmek için kondu — aksi "
        "halde doğru bir alarm her push'u bloklar ve SKIP alışkanlığa dönüşür "
        "(S215/S228/S229-B'de ölçülen desen).\n"
        "⚠️ Y11 göçü hacmi 150.000'in üstüne çıkarınca XPASS verip KIRACAK; o "
        "an bu işaret KALDIRILMALI. Eşik de o gün yeniden ölçülmeli: yalnız "
        "KABUL edilen içerik taşınıyor (~%83), yani tam göç ~140-155K arasına "
        "düşebilir ve 150.000 sınırda kalır."
    ),
)
@pytest.mark.asyncio
async def test_question_bank_hacim_tabani(db_session):
    """question_bank toplu bir silmeyle boşaltılmamış olmalı."""
    satir = (
        await db_session.execute(text("SELECT count(*) FROM question_bank"))
    ).scalar_one()

    assert satir >= MIN_SATIR, (
        f"question_bank {satir:,} satır — taban {MIN_SATIR:,}. "
        "Toplu silme/TRUNCATE şüphesi. Kurtarma: "
        "backups/kiro2_pre_schema_restore_20260727.dump (pg_restore -a -t question_bank). "
        "Mühürlü script: backend/scripts/clean_import_question_bank.py"
    )


@pytest.mark.asyncio
async def test_question_bank_benzersizlik_orani(db_session):
    """Satırların ezici çoğunluğu birbirinden farklı soru metni olmalı.

    Hacim tabanını tek başına geçen bir kopya-doldurma (aynı metnin N kopyası)
    bu kapıda düşer — 5 Ağu'daki başarısızlık tam olarak buydu.
    """
    # ⚠️ 19 Ağu 2026: bu sorgu `FROM question_bank` idi ve S210'un 69-alan
    # split'inden (`0fd9b8413`) beri KOŞULAMIYORDU:
    #     asyncpg.UndefinedColumnError: column "question_text" does not exist
    # `question_text` `question_content`'e taşındı; `question_bank` artık 12
    # kolon. Yani benzersizlik invaryantı split'ten bu yana HİÇ ÖLÇMEDİ —
    # ve bunu kimse görmedi, çünkü DSN'siz koşumda test zaten skip oluyordu
    # (iki kusur üst üste: sessiz skip + bayat şema).
    satir, benzersiz = (
        await db_session.execute(
            text(
                "SELECT count(*), count(DISTINCT qc.question_text) "
                "FROM question_bank qb "
                "JOIN question_content qc ON qc.id = qb.id"
            )
        )
    ).one()

    assert satir > 0, "question_bank BOŞ — hacim testi de düşmüş olmalı."

    oran = benzersiz / satir
    assert oran >= MIN_BENZERSIZLIK, (
        f"question_bank {satir:,} satır ama yalnız {benzersiz:,} benzersiz metin "
        f"(oran {oran:.3f}, taban {MIN_BENZERSIZLIK}). "
        "Hacim sağlıklı görünse bile içerik çeşitliliği çökmüş. "
        "5 Ağu 2026: 2.304 satır / 21 benzersiz."
    )


# ===========================================================================
# BEKÇİNİN BEKÇİSİ — 22 Ağu 2026, X10'un kapanmamış kolu
#
# `27c8fff02` X10'un *DSN-yok* kolunu kapattı. Açık kalan kol ÖLÇÜLDÜ:
#
#   KIRO2_STRICT_DB_INVARIANTS=1 \
#   KVKK_VERIFY_DSN=postgresql://postgres@localhost:5999/kiro2 \
#   pytest tests/db/test_question_bank_invariants.py
#       -> 1 passed, 2 skipped        EXIT=0
#
# Sıkı mod AÇIKKEN, bekçi YEŞİL, ölçülen şey YOK. Sebep: sıkı kontrol
# `assert resolve_pg_dsn()` diyordu — ve `pg_dsn.py` yalnızca DİZE inceler,
# hiç bağlanmaz. Yani sessiz skip, bir VEKİL ÖLÇÜMLE değiştirilmişti; oysa
# bu dosyanın kendi docstring'i vekil ölçümü açıkça yasaklıyor (S203:
# "tablo var" vekili aylarca yeşilken `/fsrs/due` canlıda 500 dönüyordu).
#
# Bu, laboratuvar senaryosu DEĞİL: pre-push kapısı (`backend/hooks/
# ders_zorlayici_kos.py:161-169`) DSN'i `backend/.env`'den DİZE olarak çözüp
# STRICT'i 1 yapıyor — o da hiç bağlanmıyor. Postgres durduğu an kapı yeşil
# kalır. Bu depoda PG18'in durduğu ölçülmüş bir durum (3 Tem, topoloji drift).
#
# Aşağıdaki dörtlü gerçek DB İSTEMEZ (ölü porta bağlanmayı dener), bu yüzden
# DSN'siz bir makinede de KOŞAR. Ölçüldü: varsayılan koşum 3 skipped / 0
# assert idi -> 4 passed / 3 skipped.
# ===========================================================================
_BU_MODUL = sys.modules[__name__]

# 5999'da bir Postgres dinlemiyor. Başka bir şey dinliyor olsa bile asyncpg
# protokol hatasıyla yükselir; test yine doğru tarafa düşer. 127.0.0.1
# bilinçli: `localhost` çift-yığın (::1) yeniden denemesiyle 4,11 sn sürüyor,
# 127.0.0.1 2,26 sn (ölçüldü).
OLU_DSN = "postgresql://postgres@127.0.0.1:5999/kiro2"


def _bekciyi_kostur():
    """Sıkı kontrolü doğrudan çağır; senkron ya da async olmasına bakma.

    Şekle bağlanmamak bilinçli: aksi halde bekçiyi async'e çevirmek meta
    testleri `ValueError: a coroutine was expected` ile düşürür ve bu, kusuru
    ölçmüş gibi görünen bir ALET ARIZASI olur.
    """
    sonuc = test_invaryant_olculebilir_olmali()
    if inspect.isawaitable(sonuc):
        asyncio.run(sonuc)


def test_alet_dsn_cozumu_erisilebilirlik_tanigi_degil(monkeypatch):
    """ALET DOĞRULAMASI — kusurun premisi: DSN çözümü BAĞLANMAZ.

    Bu düşerse kapatılacak bir şey yoktur: `resolve_pg_dsn()` erişilebilirliği
    zaten doğruluyor demektir ve `assert resolve_pg_dsn()` vekil değil gerçek
    ölçüm olurdu.
    """
    monkeypatch.setenv("KVKK_VERIFY_DSN", OLU_DSN)
    cozulen = resolve_pg_dsn()

    assert cozulen, "Ölü porta bakan DSN bile çözülüyor olmalı (premis)."
    assert "5999" in cozulen, (
        "Çözülen DSN ölü portu taşımalı — yani çözücü yalnız dize işliyor, "
        "hiçbir soket açmıyor."
    )


def test_bekci_db_erisilemezken_sessizce_gecemez(monkeypatch):
    """RED — sıkı mod + DSN var + DB erişilemez: bekçi DÜŞMELİ.

    Kusur tam buradaydı: DSN dizesi çözüldüğü için sıkı kontrol GEÇİYOR,
    iki gerçek invaryant ise fixture'da skip oluyordu -> EXIT=0.
    """
    monkeypatch.setattr(_BU_MODUL, "STRICT", True)
    monkeypatch.setenv("KVKK_VERIFY_DSN", OLU_DSN)

    with pytest.raises(AssertionError) as yakalanan:
        _bekciyi_kostur()

    mesaj = str(yakalanan.value)

    # ⚠️ Burada önce `"5999" in mesaj` yazılmıştı ve MUTASYON HAYATTA KALDI:
    # port, maskeden BAĞIMSIZ olarak asyncpg'nin kendi metninde de geçiyor
    # ("Connect call failed ('127.0.0.1', 5999)"). Ankraj TEKİL DEĞİLDİ.
    # `/kiro2` ise yalnız maskenin ürettiği parçada var.
    assert "127.0.0.1:5999/kiro2" in mesaj, (
        "Mesaj ölçülemeyen hedefi (host:port/db) göstermeli ki operatör nereye "
        "bakacağını bilsin."
    )
    # Maskenin VARLIK SEBEBİ: `@` öncesi kimlik bilgisi mesaja DÜŞMEMELİ —
    # bu depoda DB parolası bir kez log'a düştü (FAZ 0-4, Celery).
    assert (
        "postgres@" not in mesaj
    ), "DSN'in kimlik bilgisi kısmı mesaja sızdı — maske kaldırılmış olmalı."


def test_gevsek_modda_bekci_hala_sessiz(monkeypatch):
    """KONTROL KOLU — 'her koşumda kırmızı' çözümünü öldürür.

    Sıkı mod kapalıyken (taze geliştirme makinesi) bekçi SKIP vermeli.
    Bu assert olmadan `pytest.fail()`'i koşulsuz çağıran bir 'fix' de
    diğer testlerin hepsini geçerdi — ve bekçi gürültüye dönüp devre dışı
    bırakılırdı (S215/S228/S229-B'de ölçülen desen).
    """
    monkeypatch.setattr(_BU_MODUL, "STRICT", False)
    monkeypatch.setenv("KVKK_VERIFY_DSN", OLU_DSN)

    with pytest.raises(pytest.skip.Exception):
        _bekciyi_kostur()


def test_dsn_yokken_sikida_hala_duser(monkeypatch):
    """KONTROL KOLU — `27c8fff02`'nin kapattığı kol GERİLEMEMELİ.

    Yeni erişilebilirlik ölçümü, DSN-yok dalının YERİNE geçmemeli; ONA
    EKLENMELİ. İkisi bağımsız yük taşır.
    """
    monkeypatch.setattr(_BU_MODUL, "STRICT", True)
    for anahtar in ("KVKK_VERIFY_DSN", "DATABASE_URL_SYNC", "DATABASE_URL"):
        monkeypatch.delenv(anahtar, raising=False)

    with pytest.raises(AssertionError) as yakalanan:
        _bekciyi_kostur()

    # "DSN" demek YETMEZ: erişilemezlik mesajı da o kelimeyi içeriyor. Bu dalı
    # ayırt eden ifadeyi ara, yoksa `dsn = <sabit>` mutasyonu hayatta kalır.
    assert "DSN'i yok" in str(yakalanan.value)
