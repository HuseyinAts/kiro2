"""İstek-kapsamlı kiracı bağlamı — RLS GUC'unun tek kaynağı.

NEDEN VAR (S241 B1, `docs/audits/2026-08-20_a1_altin_yol_olcum.md`):
79 tabloda RLS açık ve politikalar **fail-closed**. GUC `app.current_org_id`
set edilmemiş bir bağlantıda `current_setting(...,true)` NULL döner, karşılaştırma
NULL olur ve satır reddedilir. Backend `kiro2_app` rolüyle bağlı
(`rolsuper=f, rolbypassrls=f`) → RLS gerçekten uygulanıyor.

Sonuç ölçüldü: `exam_sessions` tablosunda **bugüne kadar 0 satır**. GUC'u set eden
tek yer `core/dependencies.py:455`'ti ve *transaction-local* olduğu için yalnız
istek oturumunu kapsıyordu; sınav motoru (`core/osym_exam_engine.py:441`) ve
21 yer daha **ayrı bağlantı** açıyor.

Bu modül GUC'u çağrı yerlerine değil **oturum fabrikasına** bağlar
(`core/database.py`, `after_begin` dinleyicisi) — böylece bugünkü 22 çağrı yeri
ve gelecekte eklenecekler tek noktadan kapanır.

Bekçiler:
  `backend/tests/unit/test_tenant_context.py`
  `backend/tests/integration/test_rls_guc_transaction.py`
"""

from __future__ import annotations

from contextvars import ContextVar
from typing import Any

# İsteği koşturan kullanıcının kimliği. `get_current_user` yazar (her kimlikli uçta
# koşar); arka plan işlerinde (Celery, startup, script) BOŞ kalır ve o zaman GUC
# set EDİLMEZ — bugünkü davranış korunur, regresyon üretilmez.
_aktif_kullanici: ContextVar[str | None] = ContextVar(
    "kiro2_aktif_kullanici", default=None
)

# GUC'u kuran ifade. İki özelliği de güvenlik taşır, ikisi de testle çivili:
#
#  1. `true` (is_local) → transaction-local. `false` olsaydı GUC bağlantı ömrü
#     boyunca kalır, havuzdan o bağlantıyı alan BİR SONRAKİ kullanıcı önceki
#     kiracının org'uyla sorgu koşardı: düzeltmenin kendisi kiracı sızıntısı olurdu.
#  2. Org **istemciden değil** `users` tablosundan türetilir. İstemciden alınsaydı
#     bir öğrenci başka kiracının org'unu göndererek RLS'i atlatabilirdi.
#
# Kullanıcı bulunamazsa alt-sorgu NULL döner; `set_config(..., NULL, true)` hata
# vermez (canlıda ölçüldü) ve GUC kurulmamış kalır → fail-closed, doğru taraf.
GUC_KUR_SQL = (
    "SELECT set_config('app.current_org_id', "
    "(SELECT organization_id FROM users WHERE id = $1), true)"
)


def aktif_kullaniciyi_kur(kullanici_id: Any) -> None:
    """İstek bağlamına aktif kullanıcıyı yaz.

    `None`, boş dize ve yalnız boşluktan oluşan dize **kimlik sayılmaz** → bağlam
    temizlenir. `AuthenticatedUser.id` int de olabilir (`users.id` VARCHAR olsa da),
    bu yüzden dizeye çevrilir.
    """
    if kullanici_id is None:
        _aktif_kullanici.set(None)
        return
    metin = str(kullanici_id).strip()
    _aktif_kullanici.set(metin or None)


def aktif_kullaniciyi_getir() -> str | None:
    """Aktif kullanıcı kimliği; bağlam yoksa `None`."""
    return _aktif_kullanici.get()


def kiraci_baglamini_temizle() -> None:
    """Bağlamı boşalt (test izolasyonu ve arka plan işleri için)."""
    _aktif_kullanici.set(None)
