"""Alembic autogenerate emniyeti — yansitilmis ama yonetilmeyen nesneyi DUSURME.

NEDEN VAR (1 Agu 2026 olcumu)
-----------------------------
`alembic/env.py:22` yalnizca `from models.database import Base` import ediyor ve
`:58` `target_metadata = Base.metadata`. Ama model modullerinin bir kismi o
zincire hic girmiyor. Canli olcum:

    Base.metadata tablo sayisi : 123
    Canli PostgreSQL (public)  : 210
    metadata'da YOK            :  87

Autogenerate "DB'de var, metadata'da yok" farkini **silinmesi gereken sey**
diye yorumlar.

BU BIR VARSAYIM DEGIL, YASANMIS BIR OLAY
-----------------------------------------
`alembic/versions/c555a10f4b93_sync_db_changes.py` `upgrade()` icinde
**145 adet** `op.execute('DROP TABLE IF EXISTS ... CASCADE')` var. (Grep'te
`drop_table` aramak bos doner — raw SQL kullanilmis.) GF-K1'deki 6 tablo ve
`user_item_fsrs` o gocte dustu.

TABLOLAR ZATEN KORUNUYORDU — ASIL ACIK INDEX'LERDE
---------------------------------------------------
`alembic/env.py` 27 Tem 2026'da bu kurali ZATEN eklemis:

    if type_ == "table" and reflected and compare_to is None:
        return False

Ilk olcumum bu filtreyi UYGULAMADAN yapildigi icin "86 tablo dusecek" dedi;
bu **alembic'in hic kullanmadigi** bir konfigurasyondu. Gercek yol olculunce:

    filtre YOK                 -> remove_table=86  remove_index=134
    env.py'nin GERCEK filtresi -> remove_table= 0  remove_index= 65

Yani tablo tarafi kapaliydi, **index tarafi acik**: kural `type_ == "table"`
ile sinirliydi, yonetilmeyen tablolarin index'lerini kapsamiyordu. 65 index
DROP'u uretiliyordu (A1.1 gocuyle eklenen hot-path index'leri dahil olabilir).

NE YAPAR
--------
Ayni kurali **tur ayrimi yapmadan** uygular: nesne yansitilmis (DB'den okundu)
ve metadata'da karsiligi yoksa gocten dislanir. Alembic'in kismi-yonetilen
semalar icin standart yordami.

NEDEN AYRI MODUL: `alembic/env.py` import edilemez (alembic calisma zamaninda
`context` kurar), dolayisiyla icindeki yuklem TEST EDILEMEZDI. Kural buraya
alindi, env.py delege ediyor — boylece test **gercek yolu** olcuyor, kopyayi
degil.

BILINCLI ODUNLESIM
------------------
Bu filtre autogenerate'in **hicbir** DROP onermemesini saglar. Gercekten bir
tablo/kolon silinecekse migration ELLE yazilmalidir. Bu, "otomatik uretildi,
normaldir" diye 145 DROP'un incelemeden gecmesinden iyidir.

ASIL DUZELTME AYRI KALEM: 87 tablonun model modullerini metadata'ya kaydetmek.
O yapilana kadar bu filtre emniyet kilidi. Ilerleme olcusu:
`tests/integration/test_alembic_autogen_guard.py`.
"""

from __future__ import annotations

from typing import Any


def yonetilmeyeni_disla(
    nesne: Any,
    ad: str | None,
    tur: str,
    yansitilmis: bool,
    karsilastirilan: Any,
) -> bool:
    """Alembic `include_object` yuklemi. True = gocte yer alsin.

    Tek kural: nesne DB'den **yansitilmis** ve metadata'da **karsiligi yok**
    ise gocten cikar. Alembic bu durumu aksi halde "sil" diye yorumlar.

    `tur` ayrimi yapilmaz — ayni mantik tablo, index ve kolon icin gecerlidir
    (1 Agu olcumu: filtresiz 86 remove_table **ve** 134 remove_index).
    """
    return not (yansitilmis and karsilastirilan is None)
