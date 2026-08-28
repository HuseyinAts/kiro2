"""Cevap alanlarını rol kapısından geçiren yardımcının bekçisi.

NEDEN VAR (S241, 20 Ağu 2026 — ölçüldü):
Düz öğrenci token'ıyla `GET /sorular?limit=3` **HTTP 200** dönüyordu ve gövdede
`correct_answer` + tam `explanation` vardı. Dönen üç cevap `question_content`'teki
gerçek değerlerle **3/3 birebir** tuttu ve üç sorunun üçü de öğrenci kapısındaydı
(`mv_safe_for_beta`). Aynı sınıf iki uçta daha: `/api/v1/osym/questions` ve
`/api/v1/osym/random-questions` (ikincisinde `with_answers` **istemci kontrollü**
ve varsayılanı `True` idi).

Etki: bu açıkken platformun ölçtüğü hiçbir şey geçerli değil — öğrenci soruyu
çözmeden cevabı okuyabilir. Denetim: `docs/audits/2026-08-20_a1_altin_yol_olcum.md` B2.

Emsal: aynı sınıf kusur #432'de Elasticsearch katmanında kapatılmıştı
(`core/es_index_schema.py:51` `YASAKLI_ALANLAR`). Kavram vardı, HTTP katmanına
hiç uygulanmamıştı.
"""

from __future__ import annotations

import pytest

from core.cevap_kapisi import (
    CEVAP_ALANLARI,
    cevap_gorebilir,
    cevaplari_ele,
)
from models.enums_db import UserRole


class TestCevapGorebilir:
    """Hangi rol cevabı görebilir — kapının kendisi."""

    def test_ogrenci_cevap_goremez(self):
        assert cevap_gorebilir(UserRole.STUDENT) is False

    @pytest.mark.parametrize("rol", [UserRole.TEACHER, UserRole.ADMIN])
    def test_ogretmen_ve_admin_cevap_gorebilir(self, rol):
        """KONTROL KOLU: kapı her şeyi kesmiyor, yalnız öğrenciyi kesiyor.

        Bu assert olmadan `return False` yazan bir gövde de testi geçerdi.
        """
        assert cevap_gorebilir(rol) is True

    def test_veli_cevap_goremez(self):
        """Veli çocuğunun sınavını göremez — cevap anahtarı da göremez."""
        assert cevap_gorebilir(UserRole.PARENT) is False

    def test_bilinmeyen_rol_kapali_varsayilir(self):
        """Fail-closed: tanınmayan rol cevabı GÖREMEZ.

        Yeni bir rol eklendiğinde varsayılan davranış sızdırmak değil kesmek
        olmalı. Bu depoda bunun tersi (fail-open) daha önce ısırdı.
        """
        assert cevap_gorebilir("yepyeni_rol") is False
        assert cevap_gorebilir(None) is False


class TestCevaplariEle:
    """Sözlükten cevap alanlarını çıkarma."""

    @staticmethod
    def _ornek() -> dict:
        return {
            "id": "f98e4492-a9e8-5de4-ab1e-ea91a2cc35e2",
            "question_text": "Bir N doğal sayısında bulunan farklı rakamların sayısı…",
            "options": {"A": "1", "B": "2", "C": "3", "D": "4", "E": "5"},
            "correct_answer": "B",
            "explanation": "Verilen toplama işleminde basamak değerleri…",
            "exam_type": "TYT",
        }

    def test_ogrenciye_cevap_alanlari_cikarilir(self):
        temiz = cevaplari_ele(self._ornek(), UserRole.STUDENT)
        assert "correct_answer" not in temiz
        assert "explanation" not in temiz

    def test_ogrenciye_diger_alanlar_korunur(self):
        """Kapı yalnız cevabı kesmeli; soruyu da kesen bir gövde işe yaramaz."""
        temiz = cevaplari_ele(self._ornek(), UserRole.STUDENT)
        assert temiz["id"] == "f98e4492-a9e8-5de4-ab1e-ea91a2cc35e2"
        assert temiz["question_text"].startswith("Bir N doğal sayısında")
        assert temiz["options"]["B"] == "2"
        assert temiz["exam_type"] == "TYT"

    def test_ogretmene_cevap_alanlari_korunur(self):
        """KONTROL KOLU: her rolde silen bir gövde bu testte düşer."""
        temiz = cevaplari_ele(self._ornek(), UserRole.TEACHER)
        assert temiz["correct_answer"] == "B"
        assert temiz["explanation"].startswith("Verilen toplama işleminde")

    def test_girdi_sozlugu_degistirilmez(self):
        """Saf dönüşüm: cache'teki tam payload yerinde bozulmamalı.

        `/sorular` cache'li (MultiLayerCache, TTL 1 sa) ve cache TAM payload'ı
        tutuyor. Temizleme cache'ten OKUDUKTAN sonra yapılıyor; yerinde mutasyon
        cache girdisini kalıcı olarak sakatlar ve bir sonraki öğretmen isteği
        cevabı göremez.
        """
        kaynak = self._ornek()
        cevaplari_ele(kaynak, UserRole.STUDENT)
        assert kaynak["correct_answer"] == "B"
        assert kaynak["explanation"].startswith("Verilen toplama işleminde")

    def test_ic_ice_sozlukte_de_temizler(self):
        """Sızıntı üst düzeyde olmak zorunda değil."""
        veri = {"data": [{"stem": "soru", "correct_answer": "C"}], "success": True}
        temiz = cevaplari_ele(veri, UserRole.STUDENT)
        assert "correct_answer" not in temiz["data"][0]
        assert temiz["data"][0]["stem"] == "soru"
        assert temiz["success"] is True

    def test_liste_govdesi_de_temizlenir(self):
        """`/sorular` üst düzeyde LİSTE döndürüyor, sözlük değil."""
        veri = [{"id": "1", "correct_answer": "A"}, {"id": "2", "correct_answer": "B"}]
        temiz = cevaplari_ele(veri, UserRole.STUDENT)
        assert all("correct_answer" not in q for q in temiz)
        assert [q["id"] for q in temiz] == ["1", "2"]

    def test_cevap_alani_yoksa_hata_vermez(self):
        temiz = cevaplari_ele({"id": "1"}, UserRole.STUDENT)
        assert temiz == {"id": "1"}


def test_kanonik_alan_kumesi():
    """Alan kümesi tek kaynaktan gelmeli, çağrı yerlerinde tekrar yazılmamalı."""
    assert frozenset({"correct_answer", "explanation"}) == CEVAP_ALANLARI
