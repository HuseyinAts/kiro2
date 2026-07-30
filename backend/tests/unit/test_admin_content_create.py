"""POST /api/v1/admin/content/questions — cakisan soruyu "eklendi" diye raporluyordu.

30 TEM 2026 OLCUMU
------------------
Canli logda su ikili art arda gorundu:

    Duplicate question detected (IntegrityError on soru_hash).
    Returning existing question.
    ... 200 OK

ve DB'de o gun eklenen satir sayisi 0 (max(created_at) = 2026-06-22).

KOK NEDEN
---------
`services/soru_bankasi_service.py:344` IntegrityError'i yakalayip MEVCUT
satiri donduruyor (bilincli: toplu ice-aktarma yolu icin idempotentlik).
`api/admin.py` ise donen nesneye bakmadan kosulsuz "Soru basariyla eklendi"
zarfini kuruyor. Servis dogru davraniyor, ROUTER YALAN SOYLUYOR.

NEDEN A-1'DEN SONRA ONEMLI HALE GELDI
-------------------------------------
Bugune kadar zararsizdi cunku DELETE ucu zaten 500 veriyordu. A-1 DELETE'i
calisir hale getirdi; artik "ekledim" denen id gercekte BASKASININ sorusu
olabilir ve admin onu iyi niyetle silebilir. Yani sahte sahiplik artik bir
VERI KAYBI yoluna baglaniyor. Iki fix'in sirasi bu yuzden zorunlu.

NEDEN SERVISE `duplicate_ok=False` EKLENMEDI
--------------------------------------------
`soru_ekle`nin 6 cagirani var (toplu ice-aktarma dahil, admin_service.py:732).
Servisi istisna atar hale getirmek o yollari kirardi. Onun yerine servis
donen nesneye gecici bir `zaten_mevcuttu` bayragi koyuyor: hicbir imza
degismiyor, hicbir cagiran etkilenmiyor, ama router GERCEGI ogreniyor.

GF6w HAKKINDA (bu turda kesfedildi)
-----------------------------------
`tests/e2e/test_golden_flows.py` GF6w SABIT bir yuk gonderiyor
("Golden Flow write test: 2+2 kac eder?"). Ayni metin -> ayni soru_hash ->
ILK basarili kosumdan sonra HER kosumda cakisma. Yani "admin soru olusturma"
golden flow'u aylardir olusturmayi DEGIL cakisma yolunu test ediyordu ve
200 aldigi icin sessizce yesildi. Yuku benzersizlestirmek her CI kosumunda
uretim tablosuna satir yazardi; onun yerine GF6w artik 200 VEYA 409'u kabul
ediyor — golden-flows.md'nin kendi kurali da bunu soyluyor ("semantik durum,
asla 500").
"""

from __future__ import annotations

import pytest

pytestmark = [pytest.mark.unit]

ADMIN_ID = "admin-42"
MEVCUT_ID = "zaten-var-0001"
YENI_ID = "yeni-0002"

YUK = {
    "soru_metni": "2 + 2 kac eder?",
    "secenekler": ["A) 3", "B) 4", "C) 5", "D) 6"],
    "dogru_cevap": "B",
    "konu": "Matematik",
    "zorluk_seviyesi": "kolay",
    "sinav_tipi": "TYT",
}


class _SahteAdmin:
    id = ADMIN_ID
    role = "ADMIN"


class _SahteSoru:
    """Servisin dondurdugu ORM nesnesinin router'in okudugu alanlari."""

    def __init__(self, soru_id: str, zaten_mevcuttu: bool):
        self.id = soru_id
        self.zaten_mevcuttu = zaten_mevcuttu
        self.question_text = YUK["soru_metni"]
        self.subject_area = "MATEMATIK"
        self.difficulty_level = "kolay"
        self.exam_type = "TYT"
        self.correct_answer = "B"
        # Router bunu okuyor (admin.py:374); eksikse AttributeError -> 500 ve
        # test "aleti eksik" yuzunden yanlis sebeple kirmizi olurdu.
        self.created_at = None


@pytest.fixture
def admin_client(client):
    from api.admin import admin_kullanici_getir
    from main import app

    app.dependency_overrides[admin_kullanici_getir] = lambda: _SahteAdmin()
    try:
        yield client
    finally:
        app.dependency_overrides.pop(admin_kullanici_getir, None)


def _ekle_taklidi(monkeypatch, zaten_mevcuttu: bool):
    from services.soru_bankasi_service import soru_bankasi_servisi

    async def _ekle(soru_data):
        return _SahteSoru(MEVCUT_ID if zaten_mevcuttu else YENI_ID, zaten_mevcuttu)

    monkeypatch.setattr(soru_bankasi_servisi, "soru_ekle", _ekle)


def test_cakisan_soru_409_doner_ve_mevcut_id_yi_soyler(admin_client, monkeypatch):
    """Sahte sahiplik kapaniyor.

    Fix ONCESI: router donen nesneye bakmaz, 200 + "Soru basariyla eklendi"
    doner ve cagiran BASKASININ sorusunun id'sini kendi olusturdugu sanir.
    """
    _ekle_taklidi(monkeypatch, zaten_mevcuttu=True)

    yanit = admin_client.post("/api/v1/admin/content/questions", json=YUK)

    assert (
        yanit.status_code == 409
    ), f"cakisma hala 'basarili' raporlaniyor: {yanit.status_code} {yanit.text[:300]}"
    assert (
        MEVCUT_ID in yanit.text
    ), f"mevcut sorunun kimligi cagirana soylenmiyor: {yanit.text[:300]}"


def test_yeni_soru_hala_200_doner(admin_client, monkeypatch):
    """KORLESME GUVENCESI: fix, gercek olusturmayi bozmamali.

    Bu test olmasaydi "her zaman 409 don" gibi bir sadelestirme ustteki testi
    gecirir ve ucu tamamen islevsiz birakirdi.
    """
    _ekle_taklidi(monkeypatch, zaten_mevcuttu=False)

    yanit = admin_client.post("/api/v1/admin/content/questions", json=YUK)

    assert yanit.status_code == 200, f"{yanit.status_code} {yanit.text[:300]}"
    assert YENI_ID in yanit.text


def test_bayrak_yoksa_olusturuldu_sayilir(admin_client, monkeypatch):
    """Geriye donuk uyum: bayragi tasimayan bir donus 200 vermeli.

    `zaten_mevcuttu` GECICI bir nitelik; servisin baska bir yolu (veya bir
    test taklidi) onu hic set etmeyebilir. O durumda uc, cakisma VARSAYMAMALI
    — aksi halde saglam olusturma yollari 409 ile kirilirdi.
    """
    from services.soru_bankasi_service import soru_bankasi_servisi

    class _BayraksizSoru:
        id = YENI_ID
        question_text = YUK["soru_metni"]
        exam_type = "TYT"
        subject_area = "MATEMATIK"
        difficulty_level = "kolay"
        created_at = None

    async def _ekle(soru_data):
        return _BayraksizSoru()

    monkeypatch.setattr(soru_bankasi_servisi, "soru_ekle", _ekle)

    yanit = admin_client.post("/api/v1/admin/content/questions", json=YUK)
    assert yanit.status_code == 200, f"{yanit.status_code} {yanit.text[:300]}"
