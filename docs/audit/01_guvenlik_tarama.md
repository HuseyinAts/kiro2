# FAZ 1a: Guvenlik Tarama Raporu

**Tarih:** 2026-03-21
**Branch:** audit/fullstack-20260321
**Yontem:** Statik kod analizi (grep + agent tarama)

---

## Genel Durum

| Metrik | Deger |
|--------|-------|
| Toplam backend endpoint | 1,108 |
| Auth guard'li endpoint | 574 (%51.8) |
| Auth'suz endpoint | 534 (%48.2) |
| CRITICAL guvenlik bulgusu | 5 |
| HIGH guvenlik bulgusu | 12 |
| MEDIUM guvenlik bulgusu | 18 |
| LOW/INFO | 25+ |

---

## CRITICAL Bulgular

### C1: student_dashboard.py — Turkce Auth Guard (FALSE POSITIVE)
**Durum:** KAPALI — `mevcut_kullanici_getir` ile 12/12 endpoint korunuyor.
**Not:** Ilk taramada `get_current_user` arandi, Turkce guard kacti. Duzeltildi.

### C2: visual_supports_api.py — IDOR via Query Param (16 acik endpoint)
**Dosya:** `backend/api/visual_supports_api.py`
**Sorun:** `user_id = Query(...)` ile kullanici kimligini URL'den aliyor, auth guard yok
**Etki:** Herhangi biri baskasinin gorsel destek tercihlerini okuyabilir/degistirebilir
**Ornek:** `GET /api/v1/visual-supports/vocabulary-cards/progress/user123`
**Ciddiyet:** CRITICAL (IDOR + 0 auth)

### C3: content_management.py — 18 CMS Endpoint Acik
**Dosya:** `backend/api/content_management.py`
**Sorun:** 19 endpoint, sadece 1'inde auth var. Icerik CRUD tamamen acik.
**Etki:** Herkes egitim icerigini degistirebilir/silebilir
**Ciddiyet:** CRITICAL

### C4: veli.py — 9 Veli Paneli Endpoint Acik
**Dosya:** `backend/api/veli.py`
**Sorun:** 0/9 endpoint'te auth guard var
**Etki:** Herkes herhangi bir velinin verilerine erisebilir
**Ciddiyet:** CRITICAL

### C5: ogretmen.py — Kismi Koruma
**Dosya:** `backend/api/ogretmen.py`
**Sorun:** `ogretmen_yetkisi_kontrol` guard var ama alt endpoint'lerde eksik
**Etki:** Bazi ogretmen islemleri auth'suz erisime acik
**Ciddiyet:** CRITICAL

---

## HIGH Bulgular

### H1: zpd_maarif.py — 17 Endpoint Acik (Ogrenci ZPD Verisi)
Ogrencinin ZPD (Zone of Proximal Development) verisi, ogrenme durumu iceriyor.
0/17 auth guard.

### H2: content_api.py — 15 Endpoint Acik (Icerik)
Soru icerigi ve egitim materyallerine erisim tamamen acik.

### H3: config_routes.py — 7 Endpoint Acik (Sistem Konfigurasyonu)
Sistem ayarlarini okuma/yazma auth'suz.

### H4: diary_api.py — 18 Endpoint Acik (Gunluk Verileri)
48 endpoint'in 30'u auth'lu, 18'i acik. Kullanici gunluk verileri erisime acik olabilir.

### H5: question_bank_v2_routes.py — 12 Endpoint Acik (Soru Bankasi v2)
Soru bankasi CRUD islemleri tamamen acik.

### H6: enhanced_chat.py — 5 Endpoint Acik (Chat Verileri)
AI sohbet verilerine auth'suz erisim.

### H7: sequential_reasoning_api.py — cache/invalidate Acik
`POST /api/v1/reasoning/cache/invalidate` auth'suz — herkes cache temizleyebilir.

### H8: live_session_routes.py — 11 Endpoint Acik (Canli Ders)
Canli ders session'lari ile ilgili veriler acik.

### H9: teacher_routes.py — 11 Endpoint Acik
25 endpoint'in 14'u auth'lu ama 11'i acik.

### H10: ai_chat_routes.py — 7 Endpoint Acik
`mevcut_kullanici_getir` guard var ama bazi alt endpoint'ler korumasiz.

### H11: berturk_api.py — cache/clear Auth'suz
`POST /api/v1/berturk/cache/clear` auth guard yok.

### H12: question_crud_api.py — 9 Endpoint Acik (Soru CRUD)
Soru ekleme/silme/guncelleme islemleri kismi auth.

---

## MEDIUM Bulgular

### M1-M18: Utility/AI/Integration Endpoint'leri Acik
Asagidaki dosyalarda auth eksik ama dogrudan kullanici verisi dondurmuyor:

| Dosya | Acik | Fonksiyon |
|-------|------|-----------|
| multisensory_learning_api.py | 17 | Multisensory icerik |
| curriculum_compliance.py | 13 | Mufredat uyumluluk |
| math_solution_steps.py | 11 | Matematik cozum |
| preference_simulation_routes.py | 11 | Tercih simulasyonu |
| video_analytics_routes.py | 10 | Video analitik |
| ocr_api.py | 9 | OCR isleme |
| difficulty_classification_api.py | 8 | Zorluk siniflandirma |
| eba_routes.py | 7 | EBA entegrasyon |
| ebatv.py | 7 | EBA TV |
| vision_api.py | 7 | Goruntu AI |
| pdf_processing_api.py | 6 | PDF isleme |
| wave2b_quality_routes.py | 5 | Kalite kontrol |
| team_challenges_api.py | 5 | Takim yarismasi |
| osym_questions_api.py | 5 | OSYM sorulari |
| learning_style.py | 5 | Ogrenme stili |
| alternative_solutions_api.py | 5 | Alternatif cozum |
| text_simplification.py | 4 | Metin basitlestirme |
| celery_tasks_api.py | 4 | Arkaplan gorevleri |

---

## Frontend Credential Eksiklikleri

### axios `withCredentials` Eksik (~53 cagri)
Onceden duzeltilmis dosyalar disinda kalan axios cagrilerinde `withCredentials: true` yok.

### fetch `credentials: 'include'` Eksik (~116 cagri)
268 fetch cagrisindan 152'sinde credentials mevcut, ~116'sinda eksik.

---

## IDOR Riskleri

| Dosya | Parametre | Guard | Risk |
|-------|-----------|-------|------|
| visual_supports_api.py | `user_id: Query(...)` | YOK | CRITICAL |
| sentry_demo.py | `user_id: Query(...)` | YOK | LOW (demo) |
| tracing_example.py | `user_id: str` Path | YOK | LOW (demo) |
| elasticsearch.py | `user_id: Path(...)` | YOK | HIGH |
| audit_api.py | `user_id: Query(None)` | VAR (admin) | OK |

---

## Hardcoded Secret/URL Riskleri

| Dosya | Sorun | Risk |
|-------|-------|------|
| YOLODetectionPage.tsx | `http://localhost:8000` hardcoded | LOW (prod'da calismaz) |
| SystemSettings.tsx | `https://localhost:3000` | LOW (default) |
| berturk_api.py cache/clear | Auth yok | HIGH |

---

## STATUS: TAMAM
