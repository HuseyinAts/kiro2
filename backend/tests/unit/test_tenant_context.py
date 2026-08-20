"""İstek-kapsamlı kiracı bağlamının bekçisi.

NEDEN VAR (S241 B1, 20-21 Ağu 2026 — ölçüldü):
`exam_sessions` üzerindeki `tenant_isolation` politikası **fail-closed**:
`WITH CHECK (organization_id::text = current_setting('app.current_org_id', true))`.
GUC set edilmemiş bir bağlantıda `current_setting(...,true)` **NULL** döner ve
`'org_legacy_default' = NULL` → NULL → INSERT **reddedilir**. Backend `kiro2_app`
rolüyle bağlı (`rolsuper=f, rolbypassrls=f`), yani RLS gerçekten uygulanıyor.

Sonuç: `exam_sessions` tablosunda **bugüne kadar 0 satır** — hiçbir öğrenci tek bir
sınav başlatamadı. GUC'u set eden tek yer `core/dependencies.py:455` ve o
*transaction-local*, istek oturumuna bağlı; sınav motoru
`core/osym_exam_engine.py:441`'de **ayrı bağlantı** açıyor.

Ölçülen kapsam: **79 tabloda RLS açık**; motor **16**, komut/API **6** yerde kendi
oturumunu açıyor. Bu yüzden düzeltme çağrı yerlerine değil, tek boğaz noktası olan
oturum fabrikasına konuyor.

Denetim: `docs/audits/2026-08-20_a1_altin_yol_olcum.md` B1
"""

from __future__ import annotations

import pytest

from core.tenant_context import (
    aktif_kullaniciyi_getir,
    aktif_kullaniciyi_kur,
    kiraci_baglamini_temizle,
)


@pytest.fixture(autouse=True)
def _temiz_baglam():
    """Her test kendi bağlamıyla başlasın — sızan ContextVar testi yalancı yeşil yapar."""
    kiraci_baglamini_temizle()
    yield
    kiraci_baglamini_temizle()


class TestAktifKullanici:
    def test_varsayilan_bostur(self):
        """Arka plan işleri (Celery, startup) kullanıcı bağlamı taşımaz."""
        assert aktif_kullaniciyi_getir() is None

    def test_kurulan_deger_geri_okunur(self):
        aktif_kullaniciyi_kur("001f4676-33e7-4f77-8771-b184bb56b561")
        assert aktif_kullaniciyi_getir() == "001f4676-33e7-4f77-8771-b184bb56b561"

    def test_temizleme_bosaltir(self):
        """KONTROL KOLU: `kur` her zaman True dönen bir gövdeyle de geçerdi."""
        aktif_kullaniciyi_kur("abc")
        assert aktif_kullaniciyi_getir() == "abc"
        kiraci_baglamini_temizle()
        assert aktif_kullaniciyi_getir() is None

    def test_bos_dize_none_sayilir(self):
        """Boş dize bir kimlik değildir; GUC'a boş yazmak fail-open'a yakındır."""
        aktif_kullaniciyi_kur("")
        assert aktif_kullaniciyi_getir() is None

    def test_int_kimlik_dizeye_cevrilir(self):
        """`users.id` VARCHAR ama `AuthenticatedUser.id` int de olabilir."""
        aktif_kullaniciyi_kur(42)
        assert aktif_kullaniciyi_getir() == "42"

    def test_none_kurmak_temizler(self):
        aktif_kullaniciyi_kur("abc")
        aktif_kullaniciyi_kur(None)
        assert aktif_kullaniciyi_getir() is None


class TestGucIfadesi:
    """GUC'u kuran SQL'in şekli — dize olarak çivilenir ki sessizce değişmesin."""

    def test_ifade_transaction_local(self):
        """`is_local=true` ZORUNLU.

        `false` olsaydı GUC bağlantı ömrü boyunca kalırdı ve havuzdan o bağlantıyı
        alan BİR SONRAKİ kullanıcı önceki kiracının org'uyla sorgu koşardı —
        yani düzeltmenin kendisi bir kiracı sızıntısı üretirdi.
        """
        from core.tenant_context import GUC_KUR_SQL

        assert "set_config" in GUC_KUR_SQL
        assert "app.current_org_id" in GUC_KUR_SQL
        assert "true" in GUC_KUR_SQL.lower().split("set_config")[1]

    def test_ifade_org_u_kullanicidan_turetir(self):
        """Org istemciden değil `users` tablosundan gelir.

        İstemciden alınsaydı bir öğrenci başka kiracının org'unu göndererek
        RLS'i atlatabilirdi.
        """
        from core.tenant_context import GUC_KUR_SQL

        assert "FROM users" in GUC_KUR_SQL
        assert "organization_id" in GUC_KUR_SQL
