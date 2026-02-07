# FERPA/COPPA Compliance Guide

## Overview

KIRO2 platformu artık FERPA ve COPPA mevzuatlarına tam uyumludur.

## FERPA (Family Educational Rights and Privacy Act)

### Kapsam
- Egitim kayitlarinin gizliligi
- Ebeveyn erisim haklari
- Ucuncu taraflara bilgi paylasimi kurallari

### Implementasyon

#### 1. Egitim Kayitlari Korunmasi
```python
from models.ferpa_coppa_models import FERPAConsent, EducationalRecordType

# FERPA consent olusturma
consent = FERPAConsent(
    student_id=student_id,
    parent_id=parent_id,
    record_types="academic_performance,attendance",
    allow_third_party_disclosure=False
)
```

#### 2. Erisim Loglama
Tum egitim kayitlarina erisim otomatik olarak loglanir:
```python
from models.ferpa_coppa_models import EducationalRecordAccess

access_log = EducationalRecordAccess(
    student_id=student_id,
    accessor_id=teacher_id,
    accessor_role="teacher",
    record_type=EducationalRecordType.ACADEMIC_PERFORMANCE,
    access_purpose="Grade review"
)
```

## COPPA (Children's Online Privacy Protection Act)

### Kapsam
- 13 yas alti cocuklar icin ebeveyn onay mekanizmasi
- Veri toplama kisitlamalari
- Ebeveyn hakları

### Implementasyon

#### 1. Yas Kontrolu
```python
from datetime import date

def check_coppa_required(birth_date: date) -> bool:
    today = date.today()
    age = today.year - birth_date.year
    return age < 13
```

#### 2. Ebeveyn Onay Alma
```python
# API call
POST /api/v1/compliance/coppa/parental-consent
{
    "child_id": 123,
    "parent_id": 456,
    "child_date_of_birth": "2015-05-15",
    "verification_method": "email_plus_consent",
    "allow_data_collection": true
}
```

#### 3. Onay Dogrulama
```python
POST /api/v1/compliance/coppa/verify-consent/{consent_id}
{
    "verification_method": "email_verification",
    "verification_document": "path/to/signed_consent.pdf"
}
```

## API Endpoints

### COPPA Endpoints
- `POST /api/v1/compliance/coppa/parental-consent` - Request parental consent
- `POST /api/v1/compliance/coppa/verify-consent/{consent_id}` - Verify consent
- `GET /api/v1/compliance/coppa/consent/{child_id}` - Get consent status
- `DELETE /api/v1/compliance/coppa/withdraw-consent/{consent_id}` - Withdraw consent

### FERPA Endpoints
- `POST /api/v1/compliance/ferpa/consent` - Request FERPA consent
- `GET /api/v1/compliance/ferpa/access-log/{student_id}` - Get access log

## Compliance Checklist

### FERPA
- [x] Educational records encryption
- [x] Access logging
- [x] Parental consent mechanism
- [x] Third-party disclosure controls
- [x] Data retention policies

### COPPA
- [x] Age verification
- [x] Verifiable parental consent
- [x] Data collection limitations
- [x] Parental access rights
- [x] Data deletion on consent withdrawal

## Best Practices

1. **Yas Kontrolu**: Her kayit sirasinda dogum tarihi dogrulamasi
2. **Otomatik Ebeveyn Onay**: 13 yas alti kullanicilar icin otomatik ebeveyn onay sureci
3. **Veri Minimizasyonu**: Sadece gerekli bilgileri toplama
4. **Seffaflik**: Ebeveynlere toplanan veri hakkinda acik bilgi

## Audit ve Raporlama

```python
# FERPA erisim loglari
GET /api/v1/compliance/ferpa/access-log/123

# COPPA consent durumu
GET /api/v1/compliance/coppa/consent/456
```

## Uyumluluk Durumu

| Gereklilik | Durum | Implementasyon |
|------------|-------|----------------|
| FERPA Records Protection | ✅ | FERPAConsent model |
| COPPA Parental Consent | ✅ | COPPAParentalConsent model |
| Access Logging | ✅ | EducationalRecordAccess |
| Data Retention | ✅ | DataRetentionPolicy |
| Third-Party Agreements | ✅ | DataProcessingAgreement |

---

**Son Guncelleme**: 2025-01
**Compliance Level**: FULL
