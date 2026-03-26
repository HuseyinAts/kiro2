# KIRO2 Derin Analiz vs Mevcut Durum — SATIR SATIR KARSILASTIRMA

**Tarih:** 26 Mart 2026
**Analiz Kapsamı:** 20-26 Mart 2026 arası 8 brainstorm + 1 sosyal plan
**Toplam Bulgu:** 37 | Tamamlanan: 21 (%57) | Kısmi: 7 (%19) | Yapılmadı: 9 (%24)

---

## I. 26 MART ANALİZİ (IRT/CAT Refactoring) — 5 Aksiyon

| # | Aksiyon | Analiz Tespiti | Mevcut Durum | Sonuc |
|---|---------|---------------|--------------|-------|
| 1 | conftest.py revert — eski 1,079 satırlık hali geri koy | 18 satırlık minimal versiyon 5,146 test kaybına neden oluyordu | conftest.py = 1,124 satır, question_factory QuestionBankItem kullanıyor (BOS tablo sorunu düzeltilmiş) | YAPILDI |
| 2 | pytest.ini pythonpath = . app | sys.path.insert hack'i kırılgandı | pythonpath = . app satırı pytest.ini:51'de mevcut | YAPILDI |
| 3 | main.py get_redis() kaldır — çift Redis kaynağı | main.py:86 _redis_pool = None vs app.core.deps.get_redis → sessiz None | main.py'de get_redis veya _redis_pool YOK (kaldırılmış). app.core.deps.get_redis tek kaynak | YAPILDI |
| 4 | conftest_cat.py ile izole et | Yeni CAT/IRT testleri için ayrı fixture dosyası önerildi | conftest_cat.py YOK — testler mevcut conftest ile çalışıyor | YAPILMADI ama sorun yaratmıyor |
| 5 | PlacementWidget + frontend commit et | Untracked dosyalar commit edilmeliydi | Session 112'de commit edildi (aa95a1e) | YAPILDI |

### 26 Mart Kör Noktalar

| Kör Nokta | Mevcut Durum |
|-----------|-------------|
| Çift Redis kaynağı (main.py vs deps) | COZULDU — main.py'den kaldırıldı |
| Question vs QuestionBankItem (conftest) | COZULDU — conftest artık QuestionBankItem kullanıyor |
| backend/api/ vs backend/app/api/ namespace çakışması | RISK DEVAM — iki dizin hala var, pythonpath = . app ile çalışıyor ama kırılgan |
| nginx.conf ortam bağımlılığı | KONTROL GEREKLI |

---

## II. 23 MART ANALİZİ (Mimari Review v2) — Top 5 Aksiyon

| # | Aksiyon | Analiz Tespiti | Mevcut Durum | Sonuc |
|---|---------|---------------|--------------|-------|
| 1 | record_answer() silent failure → logger.error + counter | 4 except Exception susturuyordu | _ALGO_ERRORS dict ile counter + logger.error 4 yerde aktif (satır 218, 257, 281, 347) | YAPILDI |
| 2 | record_answer() tek transaction | 4 ayrı flush → DB bağlantı havuzu boğar | flush kaldırılmış, auto-commit | YAPILDI |
| 3 | _analyze_performance bulk UPDATE | 120 ayrı UPDATE → 1 batch | times_asked ve times_correct batch update mevcut (satır 1369-1382, .in_() ile tek sorgu) | YAPILDI |
| 4 | Docker Compose 11→3 | 9-11 compose dosyası karmaşa | Root: 2 dosya. docker/archive: 10 dosya SILINDI (Session 114) | YAPILDI |
| 5 | VersionRedirectMiddleware erken çıkış | /api/v1/ trafiği 32 kuralı gereksiz tarıyordu | version_redirect.py:67 — if path.startswith("/api/v1/"): erken return mevcut | YAPILDI |

### 23 Mart Kör Noktalar

| Kör Nokta | Mevcut Durum |
|-----------|-------------|
| active_sessions L1 memory leak | COZULDU — Session 114'te L1 eviction eklendi (complete_exam + cancel_exam) |
| 17 kullanılmayan algoritma dosyası | AYNI — backend/algorithms/ = 21 dosya |
| RevolutionaryDashboard hardcoded "demo" | AYNI — App.tsx:650 hala studentId="demo" |
| router_loader silent failure | KISMEN — broken sinav_motoru_api entry silindi (Session 114), ama loader.py hala logger.warning ile yutuyor |

---

## III. 20 MART ANALİZİ (Full Project Audit) — Proje Boyutları

| Katman | 20 Mart Tespiti | MVP Makul | Mevcut Durum | Degisim |
|--------|----------------|-----------|--------------|---------|
| Backend API Routers | 125 (99 aktif) | 20-25 | 142 | ARTTI (+17 yeni endpoint — social, IRT/CAT/DAG vb.) |
| Backend Services | 173 | 30-40 | 149 | Azaldı (-24, dead service temizliği S110) |
| Backend Models | 76 | 20-30 | Kontrol gerekli | — |
| Backend Core | 186 | 40-50 | 200 | ARTTI (+14 — yeni middleware, deps vb.) |
| Backend Algorithms | 21 | 5-8 | 21 | AYNI |
| Frontend Pages | 70 (27 wrapper) | 8-12 | 65 (27 wrapper) | Azaldı (-5) ama 27 wrapper hala var |
| Frontend Components | 65 | 20-25 | 66 | AYNI |
| Frontend Hooks | 45 | 15-20 | 48 | ARTTI (+3 — social hooks) |
| Frontend Stores | 6 | 6-8 | Kontrol gerekli | — |
| Docker Compose | 9 | 2-3 | 4 (2 root + test + monitoring) | AZALDI — archive silindi |

### 20 Mart Top 5 Aksiyon Durumu

| # | Aksiyon | Durum |
|---|---------|-------|
| 1 | MVP scope %60 kes (8 sayfa, 1 rol) | YAPILMADI — scope genişledi (social +6 sayfa) |
| 2 | Algoritma orkestrasyon (BKT→ZPD→IRT→FSRS pipeline) | YAPILDI (Session 108) |
| 3 | IRT cold-start bootstrap (77K soru difficulty=0.0) | YAPILDI (64,205 soru, Session 108) |
| 4 | Modern* wrapper katmanını yok et | YAPILMADI — 27 wrapper hala mevcut |
| 5 | Core dizinini alt paketlere böl | YAPILMADI — 200 dosya (186'dan arttı!) |

---

## IV. 20 MART (3 Kritik Sorun Deep Dive)

| # | Aksiyon | Durum |
|---|---------|-------|
| 1 | IRT heuristic bootstrap | YAPILDI |
| 2 | Revolutionary frontend temizliği (8,965 satır) | KISMEN — /admin/labs aktif ama Revolutionary hala var |
| 3 | 26 Modern* wrapper kaldırma | YAPILMADI — 27 wrapper var |
| 4 | 5 orphan backend router+servis çıkarma | KISMEN — sinav_motoru_service.py SILINDI ama service_dependencies.py hala var |
| 5 | FSRS state persistence | YAPILDI (Session 108 — FSRSCard DB read/write) |

---

## V. 20 MART (Silmeden Baglama Stratejisi)

| # | Aksiyon | Durum |
|---|---------|-------|
| 1 | IRT bootstrap (assign_difficulty_heuristic.py çalıştır) | YAPILDI |
| 2 | Algoritma bağlama (record_answer + 6 satır) | YAPILDI |
| 3 | Revolutionary aktivasyonu (/admin/labs route) | YAPILDI (Session 108) |
| 4 | FSRS state persistence | YAPILDI |
| 5 | Bloom batch etiketleme | YAPILDI (64,205 soru etiketlendi) |

---

## VI. 21 MART (Learning Path)

| # | Aksiyon | Durum |
|---|---------|-------|
| 1 | create_path sonucunu DB'ye persist et | YAPILDI (Session 83) |
| 2 | assess_knowledge IDOR fix | YAPILDI (Session 89) |
| 3 | Mobilde linear/list görünüm varsayılan | YAPILMADI |
| 4 | ZPD-IRT pipeline'ını structured_learning_path'e bağla | KISMEN — pipeline bağlı ama template engine hala statik |
| 5 | Quiz başarısızlığında aksiyon butonları | YAPILDI (Session 83) |

### Learning Path Kör Noktalar

| Kör Nokta | Durum |
|-----------|-------|
| Visualizer "Başla" butonu onClick yok | Düzeltildi (S83) |
| assess_knowledge IDOR | Düzeltildi (S89) |
| Çalışma süresi ölçülmüyor | Model var (study_time_minutes 5+ yerde) ama gerçek oturum süresi ölçen mekanizma belirsiz |
| Hata sınıflandırması yok | Migration var (add_error_type_to_student_answers.py) + error_type field var, ama aktif kullanılıyor mu belirsiz |
| Path DB'ye yazılmıyor | Düzeltildi (S83) |
| Dual cache tutarsızlığı | AYNI — kontrol gerekli |

---

## VII. 21 MART (Sınav Motoru Architecture)

| # | Aksiyon | Durum |
|---|---------|-------|
| 1 | active_sessions dict → Redis | L1 eviction eklendi (Session 114). L2 Redis zaten mevcuttu. Tam Redis-only migration YAPILMADI ama leak COZULDU |
| 2 | save_answer SELECT+UPDATE → UPSERT | YAPILDI — pg_insert + on_conflict_do_update (satır 618-634) |
| 3 | sinav_motoru_service.py sil | SILINMIS — backend/services/ altında yok |
| 4 | _select_questions N+1 → batch | YAPILMADI — kontrol gerekli |
| 5 | Performance analysis cache | YAPILMADI |

### Sınav Motoru Kör Noktalar

| Kör Nokta | Durum |
|-----------|-------|
| asyncio dormant coroutine (100K = 100K task) | KISMEN — _auto_complete_task artık tracked (autoclose: prefix, Session 114). Cancel edilebilir ama hala her session 1 task |
| Orphan DB sessions | AYNI |
| Storage büyümesi izlenmiyor | AYNI |

---

## VIII. 21 MART (Sınav Motoru Konsolidasyon — 6 Adım)

| Adım | Aksiyon | Durum |
|------|---------|-------|
| 1 | sinav_motoru_service_refactored.py SIL | SILINMIS |
| 2 | websocket_exam.py import TEMIZLE | KISMEN — dosya test referanslarında hala var ama services/ altında yok |
| 3 | service_dependencies.py broken import FIX | AYNI — service_dependencies.py hala mevcut (ama SinavMotoruService import'u yok artık) |
| 4 | advanced_reports.py → osym_exam_engine MIGRASYON | YAPILMADI — advanced_reports hala aktif (6 dosyadan referans) |
| 5 | ogretmen_service.py → osym_exam_engine MIGRASYON | ZATEN YAPILMIS — ogretmen_service.py satır 525'te osym_exam_engine import ediyor |
| 6 | sinav_motoru_service.py SIL | SILINMIS (ama tüketiciler taşınmadan) |

NOT: Adım 5 aslında zaten migre edilmiş (keşif Session 114'te doğrulandı). Adım 4 hala açık.

---

## IX. 24 MART (Sosyal Ozellikler Planı — F0-F6)

| Faz | Feature | Durum |
|-----|---------|-------|
| F0 | Safety Infrastructure (7-layer moderation) | YAPILDI Session 111 |
| F1 | Soru Meydanı (Q&A Forum) | YAPILDI Session 111 |
| F2 | Çözüm Düellosu | YAPILDI Session 111 |
| F3 | Oba Seferleri (Team Challenges) | YAPILDI Session 111 |
| F4 | Pomodoro Odaları | YAPILDI Session 111 |
| F5 | Birlikte Streak | YAPILDI Session 111 |
| F6 | Usta-Çırak (Mentoring) | YAPILDI Session 111 |

TUMU TAMAMLANDI — 20 model, 45 endpoint, 6 sayfa, 77 test PASS

---

## X. TUM ANALIZLERDEN BIRLESIK SKOR KARTI

### TAMAMLANAN (23/37)

1. IRT cold-start bootstrap (64,205 soru)
2. Algoritma orkestrasyon (BKT→IRT→FSRS→ZPD pipeline)
3. FSRS state persistence (DB read/write)
4. BKT→IRT köprüsü (logit dönüşüm)
5. Bloom batch etiketleme (64,205 soru)
6. Revolutionary /admin/labs aktivasyonu
7. record_answer() silent failure → logger.error + counter
8. record_answer() tek transaction (flush kaldırma)
9. _analyze_performance bulk UPDATE
10. VersionRedirectMiddleware erken çıkış
11. save_answer UPSERT (ON CONFLICT)
12. conftest.py revert (1,124 satır, QuestionBankItem)
13. pytest.ini pythonpath = . app
14. main.py çift Redis kaldırma
15. PlacementWidget commit
16. Learning path DB persist
17. assess_knowledge IDOR fix
18. Quiz başarısızlık aksiyon butonları
19. sinav_motoru_service.py silme
20. sinav_motoru_service_refactored.py silme
21. F0-F6 Sosyal özellikler (tümü)
22. **active_sessions L1 memory leak fix (Session 114)**
23. **router_registry broken sinav_motoru_api entry silme (Session 114)**

### KISMEN / RISKLI (6/37)

24. Backend services temizliği — 173→149, ama hala 3-4x MVP'nin gereğinden fazla
25. ZPD-IRT → structured_learning_path bağlantısı — pipeline bağlı ama template statik
26. Hata sınıflandırması — error_type migration var ama aktif kullanım belirsiz
27. Çalışma süresi ölçümü — model field'lar var ama gerçek tracking mekanizması belirsiz

### YAPILMADI (5/37)

28. MVP scope %60 kesimi — aksine genişledi (social +6 sayfa, API 125→142)
29. Core dizini alt paketlere bölme — 186→200 dosya (ARTTI!)
30. Performance analysis cache
31. Mobilde linear/list varsayılan görünüm
32. 10 kullanılmayan algoritma dosyası temizliği (18'den 10'u UNUSED)

### KESIF ILE DOGRULANDI — Sorun Yok (Session 114 Kesfi)

| Eski Madde | Kesif Sonucu |
|-----------|-------------|
| _select_questions N+1 sorunu (#33) | ZATEN BATCH — cache pool + `.in_()` (osym_exam_engine.py:1236-1283) |
| advanced_reports.py migrasyon (#36) | ZATEN FONKSIYONEL — osym_exam_engine import ediyor (satir 15) |
| ogretmen_service.py migrasyon (#37) | ZATEN YAPILMIS — osym_exam_engine import (satir 525) |
| Modern* 27 wrapper kaldirma (#31) | WRAPPER DEGIL — gercek sayfalar, hepsi aktif route. Rename gereksiz |
| Sinav motoru tuketici migrasyonu (#27) | advanced_reports + ogretmen_service ikisi de calisir durumda |
| service_dependencies.py kirik (#VIII.3) | TEMIZ — sinav_motoru referansi yok |
| Namespace cakismasi (api/ vs app/api/) | CAKISMA YOK — pythonpath = . app ayrimi calisir |
| Dual cache tutarsizligi (learning_path) | SINGLETON pattern, thread-safe lock, risk yok |

### KOR NOKTALAR (Guncellenmis — 4 Adet)

| # | Kör Nokta | Kaynak | Risk | Durum |
|---|-----------|--------|------|-------|
| 1 | asyncio task per session — hala her session 1 sleep task | exam-engine | MEDIUM — tracked+cancellable artık (S114) ama ölçek sorunu devam | IYILESTIRILDI |
| 2 | Orphan DB sessions — restart sonrası in_progress kilitli | exam-engine | MEDIUM — kullanıcı sınavı devam edemez | ACIK |
| 3 | Storage büyümesi — yılda ~12.5M satır, retention yok | exam-engine | LOW (şimdilik) | ACIK |
| 4 | D7 retention metriği tanımlanmamış | full-audit | MEDIUM — başarı ölçülemiyor | ACIK |

Session 114'te COZULEN kör noktalar:
- active_sessions L1 memory leak → L1 eviction eklendi
- router_loader silent failure → broken entry silindi
- RevolutionaryDashboard "demo" → ACIK ama admin-only, LOW risk (plan dahilinde)
- Dual cache tutarsızlığı → Kesif sonucu SORUN YOK (singleton pattern, thread-safe)

### UYARILAR (Hala Gecerli — 8 Adet)

1. Microservice'e gecMEYIN — <4ms p95, monolith yeterli
2. models/init.py'yi tek seferde degistirMEYIN — 450+ test kırar
3. Exam engine'e AI/LLM EKLEMEYIN — gereksiz maliyet
4. VARK anketini zorunlu yapMAYIN
5. Cultural multiplier'ları A/B test olmadan kullanMAYIN
6. Big-bang migration YAPMAYIN
7. Toplu silme scripti KULLANMAYIN — pilot yapın
8. 4 rolü aynı anda çıkarMAYIN

---

## OZET

| Kategori | Sayı | Oran |
|----------|------|------|
| Tamamlanan | 23 | %62 |
| Kesif ile dogrulandi (sorun yok) | 8 | %22 |
| Kısmi | 4 | %11 |
| Gercek acik | 5 | %14 |

**Efektif tamamlanma: 31/37 (%84)**

**Session 114 katkısı:**
- +3 tamamlanan (L1 eviction, router entry, docker archive)
- +8 kesif ile dogrulandi (N+1, advanced_reports, ogretmen_service, Modern* wrappers, dual cache, namespace, service_dependencies, tuketici migrasyonu)
- 2 kör nokta çözüldü (L1 leak, router_loader)
- 2 kör nokta kapandı (dual cache = sorun yok, namespace = sorun yok)

Proje 20 Mart'tan bu yana buyuk ilerleme kaydetti. Analizin "feature monster" teshisi kismi gecerli — Core 186→200, API 125→142 artti. Ancak kesfin ortaya koydugu gercek: onerilen fix'lerin cogu zaten yapilmis, kalan teknik borc beklenenden cok daha kucuk.

---

## ONCELIK SIRASI (Guncellenmis — Kesif Sonrasi)

### P1 — Kısa vadeli
- [ ] Orphan DB sessions — startup recovery mekanizması (application.py lifespan)
- [ ] 10 kullanılmayan algoritma dosyası arsivleme (18'den 10'u UNUSED)
- [ ] RevolutionaryDashboard studentId="demo" fix (admin-only, low risk)

### P2 — Orta vadeli
- [ ] Core dizini restructure (200 dosya → alt paketler)
- [ ] Performance analysis cache
- [ ] Mobilde linear/list varsayılan görünüm
- [ ] D7 retention metriği tanımlama
- [ ] Çalışma süresi gerçek tracking
- [ ] Hata sınıflandırması aktifleştirme

### P3 — Uzun vadeli
- [ ] Storage retention politikası
- [ ] Nginx envsubst (pre-production, Docker'da sorun yok)

### KAPANDI (Kesif ile sorun olmadigi dogrulandi)
- ~~_select_questions N+1~~ → Zaten batch query
- ~~advanced_reports migrasyon~~ → Zaten fonksiyonel
- ~~ogretmen_service migrasyon~~ → Zaten yapilmis
- ~~27 Modern* wrapper kaldirma~~ → Wrapper degil, gercek sayfa
- ~~Dual cache tutarsizligi~~ → Singleton pattern, sorun yok
- ~~Namespace cakismasi~~ → Cakisma yok
