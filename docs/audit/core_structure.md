# Core Dizin Yapisi Analizi

Tarih: 2026-03-23 | Yontem: Dosya adi keyword kategorizasyonu

## Ozet

| Metrik | Deger |
|--------|-------|
| Toplam dosya | 247 |
| Toplam satir | ~123,605 |
| Kategori sayisi | 11 |

## Kategori Dagilimi

| Kategori | Dosya | Satir | Durum |
|----------|-------|-------|-------|
| **other (siniflandirilmamis)** | 103 | 43,656 | Incelenmeli |
| **domain_misplaced** | 31 | 19,654 | YANLIS YERDE — services/'e tasinmali |
| **auth** | 19 | 13,722 | Cogu duplike/kullanilmiyor |
| **security** | 22 | 11,893 | Cogu duplike |
| **monitoring** | 23 | 9,437 | 5-6 aktif, geri kalan dead |
| **cache** | 15 | 6,507 | 2-3 aktif |
| **database** | 9 | 5,553 | Cogu optimizer/enhancer dead |
| **utils** | 8 | 3,652 | Buyuk kismi aktif |
| **middleware** | 6 | 3,631 | Cogu aktif |
| **nlp** | 5 | 3,264 | Aktif |
| **config** | 6 | 2,636 | Aktif |

## En Buyuk Dosyalar (core/ top 10)

| Dosya | Satir | Kategori | Aktif? |
|-------|-------|----------|--------|
| osym_exam_engine.py | 1,642 | domain_misplaced | EVET — ana sinav motoru |
| assessment_system.py | 1,634 | other | Muhtemelen dead |
| enhanced_authentication.py | 1,441 | auth | Muhtemelen dead (unified_auth aktif) |
| learning_style_detector.py | 1,437 | other | Muhtemelen dead |
| passwordless_auth.py | 1,371 | auth | Dead (implementasyon yok) |
| account_security.py | 1,349 | security | Kismi aktif |
| turkish_nlp_chat_system.py | 1,327 | nlp | Muhtemelen dead (ai_chat_service aktif) |
| automated_question_generator.py | 1,251 | domain_misplaced | Dead |
| rbac_system.py | 1,251 | auth | Kismi aktif |
| kvkk_compliance.py | 1,185 | other | Dead placeholder |

## Domain Misplaced (core/ icinde olmamasi gereken 31 dosya)

Bu dosyalar domain-spesifik is mantigi icerir, `services/` altinda olmali:

- `osym_exam_engine.py` (1,642 satir) — AKTIF, tasima RISKLI
- `automated_question_generator.py` (1,251)
- `sso_saml_service.py` (1,132)
- `rag_service.py` (1,034)
- `berturk_service.py` (942)
- ... +26 daha (toplam 19,654 satir)

**UYARI:** `osym_exam_engine.py` 50+ import referansi var, tasimak session-bazli plan gerektirir.

## Auth Duplikasyonu (19 dosya, 13,722 satir)

| Dosya | Satir | Aktif? |
|-------|-------|--------|
| enhanced_authentication.py | 1,441 | Dead |
| passwordless_auth.py | 1,371 | Dead |
| rbac_system.py | 1,251 | Kismi |
| unified_auth_service.py | 1,098 | AKTIF |
| auth_middleware.py | 1,000 | AKTIF |
| jwt_auth.py | ~400 | AKTIF |
| dependencies.py | ~600 | AKTIF |

Aktif: 4 dosya (~3,100 satir). Dead: ~10,600 satir auth kodu.

## Oneriler

1. **Tasinma YAPMA** — 450+ import kirar, ayri plan session'i gerektirir
2. **Dead code tespit** — `other` kategorisinin %80'i muhtemelen dead
3. **Auth temizligi** — `enhanced_authentication`, `passwordless_auth` dead, unified_auth AKTIF
4. **Gelecek plan:** core/ -> core/{auth, cache, db, monitoring, middleware, nlp} + services/{misplaced}
