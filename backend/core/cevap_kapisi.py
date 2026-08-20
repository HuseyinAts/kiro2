"""Cevap alanlarını rol kapısından geçiren tek kaynak.

NEDEN VAR (S241, 20 Ağu 2026 — ölçüldü, `docs/audits/2026-08-20_a1_altin_yol_olcum.md` B2):
Düz öğrenci token'ıyla üç uç `correct_answer` ve `explanation` döndürüyordu:

    GET /sorular                        -> correct_answer + explanation
    GET /api/v1/osym/questions          -> correct_answer
    GET /api/v1/osym/random-questions   -> correct_answer  (with_answers=True varsayılan)

Dönen cevaplar `question_content`'teki gerçek değerlerle 3/3 birebir tuttu ve üç
sorunun üçü de öğrenci kapısındaydı (`mv_safe_for_beta`). Bu açıkken platformun
ölçtüğü hiçbir şey geçerli değil.

Emsal: aynı sınıf kusur #432'de Elasticsearch katmanında kapatıldı
(`core/es_index_schema.py:51` `YASAKLI_ALANLAR` + sızıntı bekçisi). Kavram vardı,
HTTP katmanına hiç uygulanmamıştı. Bu modül onu HTTP katmanına taşır.

**Alan kümesi neden `es_index_schema`den import edilmiyor?** İki küme farklı işe
bakıyor: ES kümesi `is_active`'i de dışlıyor (bayat bayrak riski, indeksleme
kaygısı), HTTP kapısının `is_active`'le derdi yok. Ortak isim altında birleştirmek
iki farklı kararı tek anahtara bağlar ve birini değiştiren diğerini sessizce bozar.

Bekçi: `backend/tests/unit/test_cevap_kapisi.py`
"""

from __future__ import annotations

from typing import Any

from models.enums_db import UserRole

# Öğrenciden gizlenecek alanlar. Çağrı yerlerinde TEKRAR YAZILMAZ — tek kaynak burası.
CEVAP_ALANLARI: frozenset[str] = frozenset({"correct_answer", "explanation"})

# Cevabı görmeye yetkili roller. Liste **beyaz liste**: burada olmayan her rol
# (yeni eklenen roller dahil) cevabı GÖREMEZ.
_YETKILI_ROLLER: frozenset[str] = frozenset(
    {UserRole.TEACHER.value, UserRole.ADMIN.value}
)


def cevap_gorebilir(rol: Any) -> bool:
    """Bu rol `correct_answer` / `explanation` görebilir mi?

    FAIL-CLOSED: tanınmayan rol, `None`, boş dize -> **False**. Yeni bir rol
    eklendiğinde varsayılan davranış sızdırmak değil kesmek olmalı.
    """
    if rol is None:
        return False
    ham = getattr(rol, "value", rol)
    if not isinstance(ham, str):
        return False
    return ham.upper() in _YETKILI_ROLLER


def cevaplari_ele(veri: Any, rol: Any) -> Any:
    """`veri`nin cevap alanlarından arındırılmış bir KOPYASINI döndür.

    Rol yetkiliyse `veri` olduğu gibi döner (kopya bile alınmaz).

    Saf dönüşümdür — girdi **yerinde değiştirilmez**. Bu isteğe bağlı bir zarafet
    değil, zorunluluk: `/sorular` yanıtı `MultiLayerCache`'te TAM payload olarak
    tutuluyor ve temizleme cache'ten OKUNDUKTAN sonra yapılıyor. Yerinde mutasyon
    cache girdisini kalıcı sakatlar ve sonraki öğretmen isteği cevabı göremez.

    Sözlük, liste ve iç içe yapıları özyinelemeli tarar — sızıntının üst düzeyde
    olması gerekmiyor (`{"data": [{...}]}` sarmalayıcısı yaygın).
    """
    if cevap_gorebilir(rol):
        return veri
    return _ele(veri)


def _ele(veri: Any) -> Any:
    if isinstance(veri, dict):
        return {a: _ele(d) for a, d in veri.items() if a not in CEVAP_ALANLARI}
    if isinstance(veri, list):
        return [_ele(o) for o in veri]
    if isinstance(veri, tuple):
        return tuple(_ele(o) for o in veri)
    return veri
