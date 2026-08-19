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

import os

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


def test_invaryant_olculebilir_olmali():
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
    """
    if not STRICT:
        pytest.skip(
            "Gevşek mod. Sıkı kontrol için: KIRO2_STRICT_DB_INVARIANTS=1 "
            "(içeriğin bulunması GEREKEN ortamlarda: CI, staging, üretim-yakını)"
        )
    assert resolve_pg_dsn(), (
        "SIKI MOD: question_bank invaryant bekçisi ÖLÇEMEDİ — gerçek PostgreSQL "
        f"DSN'i yok.\n{SKIP_REASON}\n"
        "Bu ortam içerik taşımıyorsa KIRO2_STRICT_DB_INVARIANTS'ı set etme; "
        "taşıyorsa DSN ver. Sessiz skip yasak: 12 Ağu 2026'da question_bank "
        "0 satırken bu paket '2 skipped' verdi ve hiçbir alarm çalmadı."
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
        "Y11 AÇIK: canlı question_bank 36.967 satır, taban 150.000. Bu KIRMIZI "
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
