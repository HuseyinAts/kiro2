"""`meb_curriculum_nodes` / `misconception_matrix` / `misconception_remedies`
ORM <-> DB kolon paritesi (pedagogy_models.py backlog kurtarma, 30 Ağu 2026).

NEDEN VAR
---------
`backend/models/pedagogy_models.py` (MEBCurriculumNode, MisconceptionMatrix,
MisconceptionRemedy) SS10.7 grubundan untracked bir dosyaydı; hiçbir servis/
API/test tarafından çağrılmıyor (git grep ile doğrulandı -- dosyanın kendi
dışında sıfır eşleşme). Ama 3 tablosu da canlı Postgres'te GERÇEKTEN VAR
(alembic/versions_archive/d23f7afe5e9a_*.py onları oluşturmuş,
alembic/baseline/0001_baseline_schema.sql şemayı doğruluyor). 30 Ağu 2026
ölçümü: 3 tablonun tümünde ORM<->DB kolon sayısı ve isimleri BİREBİR
eşleşiyor (drift yok) -- ama S255 vakası da başlangıçta öyle görünüp
sonradan kayabildiğini gösterdi. Bu test o pariteyi kalıcı, otomatik bir
bekçiye çevirir (aksi halde bir sonraki elle-yazılmış migration sessizce
kayma yaratabilir, hiçbir çağıran olmadığı için de kimse fark etmez).

KAPSAM: `test_learning_path_profile_sema_paritesi.py` (S255) ile aynı desen,
3 tabloya genelleştirildi. O dosyadaki 4. test (NOT NULL + default'suz
kolonların ORM karşılığı var mı) BİLEREK atlandı: bu 3 referans-veri
tablosunun NOT NULL alanlarının neredeyse tümü (code, description,
subject_area, title, misconception_id, remedy_type, ...) tasarım gereği
"çağıran açıkça sağlamalı" alanlar -- app-doldurur istisna listesi
neredeyse tüm kolonları kapsardı ve gerçek bir sinyal üretmezdi. İlk 3
test (okunabilirlik kontrol kolu + DB-fazlası + ORM-fazlası) asıl S255
sınıfı riski (sessiz kayma) zaten tam kapsıyor.
"""

from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from models.pedagogy_models import (
    MEBCurriculumNode,
    MisconceptionMatrix,
    MisconceptionRemedy,
)
from tests.integration.conftest import canli_dsn_cozumle

pytestmark = [pytest.mark.integration]

MODELLER = [MEBCurriculumNode, MisconceptionMatrix, MisconceptionRemedy]

KOLON_SQL = text(
    "SELECT column_name FROM information_schema.columns WHERE table_name = :t"
)


@pytest.fixture
async def db_tablo_kolonlari() -> dict[str, set[str]]:
    dsn = canli_dsn_cozumle()
    if not dsn:
        pytest.skip("Canli DSN cozulemedi -- ORM<->DB paritesi olculemez")

    motor = create_async_engine(dsn)
    try:
        async with motor.connect() as baglanti:
            sonuc: dict[str, set[str]] = {}
            for model in MODELLER:
                tablo = model.__tablename__
                satirlar = (await baglanti.execute(KOLON_SQL, {"t": tablo})).all()
                sonuc[tablo] = {ad for (ad,) in satirlar}
    finally:
        await motor.dispose()

    return sonuc


async def test_alet_dogrulamasi_tablolar_okunabiliyor(db_tablo_kolonlari) -> None:
    """KONTROL KOLU: bir tablo okunamazsa asagidaki 'ihlal yok' sonucu SAHTEDIR.

    Bos kume donerse parite testleri BOS KUMEDE gecer -- bu depoda defalarca
    yasanmis yanlis-sifir sinifi.
    """
    for model in MODELLER:
        tablo = model.__tablename__
        kolonlar = db_tablo_kolonlari.get(tablo, set())
        assert len(kolonlar) >= 5, (
            f"`{tablo}` icin yalniz {len(kolonlar)} kolon okundu. Tablo adi "
            "degismis veya baglanti yanlis veritabanina gidiyor olabilir."
        )


@pytest.mark.parametrize("model", MODELLER, ids=lambda m: m.__tablename__)
async def test_db_deki_her_kolon_orm_de_tanimli(model, db_tablo_kolonlari) -> None:
    """DB'de olup ORM'de olmayan kolon = sorgunun sessizce atladigi kolon.

    NOT NULL + default'suz ise her INSERT duser (S255 vakasi). Nullable ise
    sessizce hep NULL kalir -- daha sinsi, cunku hicbir hata uretmez.
    """
    tablo = model.__tablename__
    orm_kolonlari = {c.name for c in model.__table__.columns}
    eksik = sorted(db_tablo_kolonlari[tablo] - orm_kolonlari)
    assert not eksik, (
        f"`{tablo}` DB'de olup ORM modelinde OLMAYAN kolon(lar): {eksik}. "
        "NOT NULL + default'suz olan her INSERT'i dusurur; nullable olan "
        "sessizce hep NULL kalir."
    )


@pytest.mark.parametrize("model", MODELLER, ids=lambda m: m.__tablename__)
async def test_orm_deki_her_kolon_db_de_var(model, db_tablo_kolonlari) -> None:
    """Ters yon: ORM'de olup DB'de olmayan kolon SELECT'i patlatir.

    (`UndefinedColumnError` -- ve o hata calisma aninda, uretimde cikar.)
    """
    tablo = model.__tablename__
    orm_kolonlari = {c.name for c in model.__table__.columns}
    fazla = sorted(orm_kolonlari - db_tablo_kolonlari[tablo])
    assert not fazla, (
        f"ORM'de tanimli ama `{tablo}` tablosunda OLMAYAN kolon(lar): {fazla}. "
        "Bu kolonlari secen her sorgu UndefinedColumnError ile duser."
    )
