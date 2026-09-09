"""KVKK yas esigi -- `is_minor` (9 Eyl 2026: modulun geri kalani emekli).

Bu dosya 1.213 satirdi: kendi `declarative_base()` uzerinde dort ORM modeli
(`kvkk_consents`, `kvkk_data_processing_logs`, `kvkk_data_subject_requests`,
`kvkk_data_breaches`), bir PII sifreleme sinifi, pydantic istek modelleri ve
1.200 satirlik `KVKKComplianceManager`. Olculdu (rapor madde 13, git
ls-files uzerinden AST/regex sayimi): uretim kodunda bu modulden yalnizca
`is_minor` import ediliyor (application/commands/auth.py); geri kalanini
sadece kendi testleri cagiriyordu. Canli `kvkk_consents` tablosu
models/kvkk_models.py (uuid7 anahtarli, kanonik) ile uyusuyor; buradaki
Integer anahtarli ikiz sema ORM'de ayni tabloyu iddia eden ikinci Base'di.

Kayit tutma yukumlulugu etkilenmedi: tablo ve kanonik model oldugu gibi
duruyor; kaldirilan sey hic baglanmamis ikinci bir katmandi. Bekci:
tests/fast/test_kvkk_tek_model.py (tek Base `kvkk_consents` iddia eder).
"""

from datetime import date, datetime
from zoneinfo import ZoneInfo

# KVKK reşitlik yaşı — 18 yaşından küçük kullanıcı için veli onayı zorunlu.
KVKK_RESIT_YASI = 18


def is_minor(birth_date: date, today: date | None = None) -> bool:
    """Kullanıcı KVKK'ya göre reşit değil mi (veli onayı gerekir mi)?

    18 yaşından küçükse True. 18. doğum gününü dolduran reşit sayılır.
    """
    if today is None:
        # Turkiye gunu: KVKK resitlik Turk hukukuna gore, sunucu/UTC gunu degil
        # (DTZ011: naive date.today() gece yarisi cevresinde bir gun sapabilir).
        today = datetime.now(ZoneInfo("Europe/Istanbul")).date()
    age = (
        today.year
        - birth_date.year
        - ((today.month, today.day) < (birth_date.month, birth_date.day))
    )
    return age < KVKK_RESIT_YASI
