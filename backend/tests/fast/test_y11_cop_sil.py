"""`y11_cop_sil` bekçisi — saf SQL üretimi + kapı mantığı, DB'siz.

Bu modül 36.967 satır SİLİYOR. Ölçülebilir tek yeri SQL metni ve kapı
fonksiyonu; ikisi de saf tutuldu ki gerçek Postgres olmadan çivilenebilsin.
Canlıya karşı doğrulama ayrı adım (PROVA = `--kalici` verilmeden koşum).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts" / "quality"))

from y11_cop_sil import (
    COP_PREDIKATI,
    TABLOLAR,
    beklenti_ihlalleri,
    cop_sil,
    damga_dogrula,
    dogrulama_sorgulari,
    silme_ifadesi,
    yedek_ifadeleri,
    yedek_tablo_adi,
)

DAMGA = "20260820"
COP = 36_967
KALAN = 3_616


def _temiz_olcum() -> dict[str, int]:
    olcum = {f"yedek_{t}": COP for t in TABLOLAR}
    olcum.update(
        {
            "kalan_bank": KALAN,
            "kalan_content": KALAN,
            "kalan_metadata": KALAN,
            "kalan_statistics": KALAN,
            "kalan_kitapsiz": 0,
            "kalan_y11_damgali": KALAN,
            "yetim_content": 0,
            "yetim_metadata": 0,
            "yetim_statistics": 0,
        }
    )
    return olcum


# --------------------------------------------------------------- damga


@pytest.mark.parametrize(
    "kotu",
    [
        "2026-08-20",  # tire
        "x; DROP TABLE question_bank",  # enjeksiyon
        "20260820'",  # tirnak
        "ab",  # cok kisa
        "A20260820",  # buyuk harf
        "",  # bos
        "a" * 41,  # cok uzun
    ],
)
def test_damga_kotu_girdiyi_reddeder(kotu: str) -> None:
    """Damga tablo adına gömülüyor — parametreleştirilemez, beyaz liste şart."""
    with pytest.raises(ValueError):
        damga_dogrula(kotu)


@pytest.mark.parametrize("iyi", ["20260820", "cop_temizlik_1", "abcd"])
def test_damga_iyi_girdiyi_gecirir(iyi: str) -> None:
    assert damga_dogrula(iyi) == iyi


def test_yedek_tablo_adi_bilinmeyen_tabloyu_reddeder() -> None:
    with pytest.raises(ValueError):
        yedek_tablo_adi("users", DAMGA)


# --------------------------------------------------------------- yedek


def test_yedek_dort_tablo_uretir() -> None:
    ifadeler = yedek_ifadeleri(DAMGA)
    assert len(ifadeler) == 4
    for tablo in TABLOLAR:
        assert any(yedek_tablo_adi(tablo, DAMGA) in i for i in ifadeler), tablo


def test_metadata_yedegi_ilk_sirada() -> None:
    """Ayırıcı kolon metadata'da; diğer üçü id kümesini ondan türetir.

    Sıra bozulursa üç CTAS henüz var olmayan tabloya bakar.
    """
    ilk = yedek_ifadeleri(DAMGA)[0]
    assert yedek_tablo_adi("question_metadata", DAMGA) in ilk
    assert COP_PREDIKATI in ilk


def test_yalniz_metadata_predikati_degerlendirir() -> None:
    """Predikat DÖRT kez ayrı ayrı değerlendirilmemeli.

    Değerlendirilseydi dört yedek farklı id kümesi taşıyabilirdi (satır
    arasında değişen veri, farklı plan). Üçü metadata yedeğinden okur.
    """
    ifadeler = yedek_ifadeleri(DAMGA)
    predikatli = [i for i in ifadeler if COP_PREDIKATI in i]
    assert len(predikatli) == 1, f"predikat {len(predikatli)} kez gecti"
    meta = yedek_tablo_adi("question_metadata", DAMGA)
    for i in ifadeler[1:]:
        assert meta in i
        assert "SELECT id FROM" in i


# --------------------------------------------------------------- silme


def test_silme_id_kumesini_yedekten_alir() -> None:
    """Silinen küme == yedeklenen küme, inşa gereği.

    Predikat yeniden değerlendirilseydi yedeklenmemiş bir satır silinebilirdi.
    """
    sql = silme_ifadesi(DAMGA)
    assert yedek_tablo_adi("question_bank", DAMGA) in sql
    assert COP_PREDIKATI not in sql


def test_silme_yalniz_ebeveyni_hedefler() -> None:
    """Yavrular ve 11 FK çocuğu CASCADE ile gider; elle silinmez.

    İki iddia birlikte yeterli: tek bir silme var VE hedefi `question_bank`.
    Yavruyu ayrıca aramaya gerek yok — sayı 1'ken ikinci bir hedef olamaz.
    """
    sql = silme_ifadesi(DAMGA)
    assert sql.count("DELETE FROM") == 1
    assert "DELETE FROM question_bank " in sql


# --------------------------------------------------------------- kapi


def test_temiz_olcum_ihlal_uretmez() -> None:
    assert (
        beklenti_ihlalleri(_temiz_olcum(), beklenen_cop=COP, beklenen_kalan=KALAN) == []
    )


def test_eksik_yedek_yakalanir() -> None:
    """Yedek beklenenden azsa geri alma yolu eksik demektir — KALICI YAZILMAZ."""
    olcum = _temiz_olcum()
    olcum["yedek_question_content"] = COP - 1
    ihlaller = beklenti_ihlalleri(olcum, beklenen_cop=COP, beklenen_kalan=KALAN)
    assert any("yedek_question_content" in i for i in ihlaller)


def test_eksik_silme_yakalanir() -> None:
    """Tek bir kitapsız satır bile kalırsa temizlik tamamlanmamıştır."""
    olcum = _temiz_olcum()
    olcum["kalan_kitapsiz"] = 1
    assert any(
        "kalan_kitapsiz" in i
        for i in beklenti_ihlalleri(olcum, beklenen_cop=COP, beklenen_kalan=KALAN)
    )


def test_y11_partisine_dokunulmasi_yakalanir() -> None:
    """Asıl felaket senaryosu: ayırıcı ters dönüp GERÇEK içeriği silmek."""
    olcum = _temiz_olcum()
    olcum["kalan_y11_damgali"] = 0
    olcum["kalan_bank"] = 0
    ihlaller = beklenti_ihlalleri(olcum, beklenen_cop=COP, beklenen_kalan=KALAN)
    assert any("kalan_y11_damgali" in i for i in ihlaller)


@pytest.mark.parametrize(
    "anahtar", ["yetim_content", "yetim_metadata", "yetim_statistics"]
)
def test_yetim_yakalanir(anahtar: str) -> None:
    olcum = _temiz_olcum()
    olcum[anahtar] = 5
    assert any(
        anahtar in i
        for i in beklenti_ihlalleri(olcum, beklenen_cop=COP, beklenen_kalan=KALAN)
    )


def test_dogrulama_sorgulari_tum_anahtarlari_kapsar() -> None:
    """Kapının okuduğu her anahtar gerçekten sorgulanıyor olmalı.

    Sorgulanmayan anahtar `olcum.get()` ile `None` gelir ve ihlal üretir —
    ama sessiz bir eksik yerine burada yakalansın.
    """
    sorgular = dogrulama_sorgulari(DAMGA)
    for anahtar in _temiz_olcum():
        assert anahtar in sorgular, f"{anahtar} sorgulanmiyor"


# --------------------------------------------------------------- transaction


class _SahteIslem:
    def __init__(self) -> None:
        self.commit_edildi = False
        self.geri_alindi = False

    async def start(self) -> None:
        pass

    async def commit(self) -> None:
        self.commit_edildi = True

    async def rollback(self) -> None:
        self.geri_alindi = True


class _SahteBaglanti:
    def __init__(self, patlat: bool = False) -> None:
        self.islem = _SahteIslem()
        self.ifadeler: list[str] = []
        self.patlat = patlat

    def transaction(self) -> _SahteIslem:
        return self.islem

    async def execute(self, sql: str) -> str:
        if self.patlat and sql.startswith("DELETE"):
            raise RuntimeError("simule hata")
        self.ifadeler.append(sql)
        return "DELETE 36967"


@pytest.mark.asyncio
async def test_varsayilan_geri_alir() -> None:
    """`--kalici` verilmezse prova. Yanlış varsayılan sessizce kalıcı yazardı."""
    b = _SahteBaglanti()
    rapor = await cop_sil(b, DAMGA)
    assert b.islem.geri_alindi is True
    assert b.islem.commit_edildi is False
    assert rapor["kalici"] is False


@pytest.mark.asyncio
async def test_kalici_commit_eder() -> None:
    b = _SahteBaglanti()
    await cop_sil(b, DAMGA, kalici=True)
    assert b.islem.commit_edildi is True
    assert b.islem.geri_alindi is False


@pytest.mark.asyncio
async def test_hata_halinde_geri_alir_ve_yukseltir() -> None:
    b = _SahteBaglanti(patlat=True)
    with pytest.raises(RuntimeError):
        await cop_sil(b, DAMGA, kalici=True)
    assert b.islem.geri_alindi is True
    assert b.islem.commit_edildi is False


@pytest.mark.asyncio
async def test_dogrulayici_geri_alimdan_once_kosar() -> None:
    """Ölçüm transaction içinde alınmazsa prova hiçbir şey ölçmez."""
    b = _SahteBaglanti()
    goruldu: dict[str, bool] = {}

    async def dogrula(_b: object) -> dict[str, int]:
        goruldu["commit"] = b.islem.commit_edildi
        goruldu["rollback"] = b.islem.geri_alindi
        return {"kalan_bank": KALAN}

    rapor = await cop_sil(b, DAMGA, dogrulayici=dogrula)
    assert goruldu == {"commit": False, "rollback": False}
    assert rapor["olcum"] == {"kalan_bank": KALAN}


@pytest.mark.asyncio
async def test_yedekler_silmeden_once_kosar() -> None:
    """Sıra ters olsaydı yedek boş kalırdı — geri alma yolu yok demek."""
    b = _SahteBaglanti()
    await cop_sil(b, DAMGA)
    ctas = [i for i, s in enumerate(b.ifadeler) if s.startswith("CREATE TABLE")]
    delete = [i for i, s in enumerate(b.ifadeler) if s.startswith("DELETE")]
    assert len(ctas) == 4 and len(delete) == 1
    assert max(ctas) < delete[0]
