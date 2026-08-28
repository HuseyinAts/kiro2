"""`learning_path_student_profiles` ORM <-> DB kolon paritesi (S255).

NEDEN VAR
---------
27 Agu 2026'da olculdu: DB'de **35** kolon vardi, ORM modelinde **34**.
Fark tek bir kolondu -- `neuro_inclusive_mode` (boolean, NOT NULL,
server_default YOK) -- ve modelde HIC TANIMLI DEGILDI. Sonuc:

    ORM INSERT kolonu ATLIYOR
    PG'nin dolduracagi default YOK
    -> asyncpg.exceptions.NotNullViolationError
    -> POST /api/v1/learning-path/create-profile HTTP 500

Bu tek kolon iki Golden Flow'u birden dusuruyordu (GF10 dogrudan, GF24 onu
on kosul olarak kullandigi icin) ve ustelik `learning_path`in TUM alt
sistemini kilitliyordu: profil olusturulamayinca `verify_student_access`
her istegi 403 ile reddediyordu.

KOLONU OLUSTURAN BIR ALEMBIC MIGRATION YOK (olculdu: `grep -rl
neuro_inclusive_mode backend/alembic` -> 0 dosya). Yani kolon alembic
DISINDA eklenmis; `.claude/rules/audit-methodology.md`'nin "raw SQL
migration yazildiysa information_schema ile DOGRULA" kuralinin ihlali.

NEDEN BU TEST
-------------
Depoda `scripts/audit_orm_vs_db_parity.py` VAR ama o BASKA bir sey olcuyor
(S209: kirli agactaki iki MODEL SURUMUNDEN hangisinin DB'ye uydugu) ve
hicbir test/CI onu kosmuyor. Yani bu kayma sinifinin bekcisi YOKTU.

Kapsam BILEREK tek tablo: depo genelinde bir parite testi bugun onlarca
bilinen kaymayi birden kirmiziya cevirir ve gurultuye bogulur. Bu test
duzeltilen tabloyu civiler; kapsam genisletmek ayri bir karardir.
"""

from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from models.learning_path_models import LearningPathStudentProfile
from tests.integration.conftest import canli_dsn_cozumle

pytestmark = [pytest.mark.integration]

TABLO = LearningPathStudentProfile.__tablename__

KOLON_SQL = text(
    "SELECT column_name, is_nullable, coalesce(column_default, '') "
    "FROM information_schema.columns WHERE table_name = :t"
)


@pytest.fixture
async def db_kolonlari() -> dict[str, tuple[bool, str]]:
    dsn = canli_dsn_cozumle()
    if not dsn:
        pytest.skip("Canli DSN cozulemedi -- ORM<->DB paritesi olculemez")

    motor = create_async_engine(dsn)
    try:
        async with motor.connect() as baglanti:
            satirlar = (await baglanti.execute(KOLON_SQL, {"t": TABLO})).all()
    finally:
        await motor.dispose()

    return {ad: (nullable == "YES", dflt) for ad, nullable, dflt in satirlar}


async def test_alet_dogrulamasi_tablo_okunabiliyor(db_kolonlari) -> None:
    """KONTROL KOLU: tablo okunamazsa asagidaki 'ihlal yok' sonucu SAHTEDIR.

    Bos sozluk donerse parite testi BOS KUMEDE gecer -- bu depoda defalarca
    yasanmis yanlis-sifir sinifi.
    """
    assert len(db_kolonlari) >= 30, (
        f"`{TABLO}` icin yalniz {len(db_kolonlari)} kolon okundu. Tablo adi "
        "degismis veya baglanti yanlis veritabanina gidiyor olabilir."
    )


async def test_db_deki_her_kolon_orm_de_tanimli(db_kolonlari) -> None:
    """DB'de olup ORM'de olmayan kolon = INSERT'in ATLADIGI kolon.

    NOT NULL + default'suz ise her INSERT duser (S255 vakasi). Nullable ise
    sessizce hep NULL kalir -- daha sinsi, cunku hicbir hata uretmez.

    MUTASYON: modelden `neuro_inclusive_mode` satirini silmek bu testi
    DUSURUR.
    """
    orm_kolonlari = {c.name for c in LearningPathStudentProfile.__table__.columns}
    eksik = sorted(set(db_kolonlari) - orm_kolonlari)

    ayrinti = [
        f"{ad} (nullable={db_kolonlari[ad][0]}, "
        f"default={db_kolonlari[ad][1] or '<YOK>'})"
        for ad in eksik
    ]
    assert not eksik, (
        f"`{TABLO}` DB'de olup ORM modelinde OLMAYAN kolon(lar): {ayrinti}. "
        "NOT NULL + default'suz olan her INSERT'i dusurur "
        "(NotNullViolationError); nullable olan sessizce hep NULL kalir."
    )


async def test_orm_deki_her_kolon_db_de_var(db_kolonlari) -> None:
    """Ters yon: ORM'de olup DB'de olmayan kolon SELECT'i patlatir.

    (`UndefinedColumnError` -- ve o hata calisma aninda, uretimde cikar.)
    """
    orm_kolonlari = {c.name for c in LearningPathStudentProfile.__table__.columns}
    fazla = sorted(orm_kolonlari - set(db_kolonlari))
    assert not fazla, (
        f"ORM'de tanimli ama `{TABLO}` tablosunda OLMAYAN kolon(lar): {fazla}. "
        "Bu kolonlari secen her sorgu UndefinedColumnError ile duser."
    )


async def test_not_null_default_suz_kolonlarin_orm_karsiligi_var(db_kolonlari) -> None:
    """NOT NULL + DB default'suz her kolon icin ORM bir deger URETEBILMELI.

    Ya Python-tarafi `default`, ya `server_default`, ya da uygulamanin her
    INSERT'te acikca doldurdugu bir alan olmali. Sonuncusu statik olarak
    dogrulanamaz; bu yuzden test SADECE `nullable=False` olan ORM kolonlarini
    sinar ve bilinen "uygulama doldurur" alanlarini haric tutar.
    """
    # Olculdu (27 Agu 2026): bu uc alani `create_student_profile` her cagrida
    # acikca gonderiyor (INSERT parametrelerinde gorunuyor).
    UYGULAMA_DOLDURUYOR = {"student_id", "name", "grade", "exam_target"}

    orm = {c.name: c for c in LearningPathStudentProfile.__table__.columns}
    sucular = []
    for ad, (nullable, dflt) in db_kolonlari.items():
        if nullable or dflt or ad in UYGULAMA_DOLDURUYOR:
            continue
        c = orm.get(ad)
        if c is None:
            continue  # ustteki test zaten yakaliyor
        if c.default is None and c.server_default is None:
            sucular.append(ad)

    assert not sucular, (
        f"`{TABLO}`: DB'de NOT NULL + default'suz, ORM'de de deger uretmeyen "
        f"kolon(lar): {sucular}. Bu kolonu doldurmayan her INSERT duser."
    )
