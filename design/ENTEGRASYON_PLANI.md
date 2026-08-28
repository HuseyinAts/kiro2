# KIRO2 — Gerçek Backend Entegrasyon Planı (repo-temelli, dosya-dosya)

> 2026-07-22 · Kaynak keşif: `HuseyinAts/kiro2@master` (backend FastAPI + frontend Vite/React/TS).
> Bu plan, tasarım sözleşmesini (openapi.yaml) REPODAKİ GERÇEK koda bağlar. Yürütücü: Claude Code (repoda).
> Prototip DC'leri piksel + kopya referansıdır; motorlar SUNUCUDA (kanon).

## 0 · Keşif bulguları — sözleşmeyi gerçeğe uyarlayan 5 karar

| # | Tasarım varsayımı | Repo gerçeği | Karar |
|---|---|---|---|
| 1 | Bearer JWT (`Authorization` header) | **httpOnly cookie** auth: `/api/v1/auth/login/secure`, `refresh/secure`, `logout/secure`; axios `withCredentials:true` (`services/apiClient.ts`) | Cookie auth KALIR (XSS yüzeyi yok — daha iyi). openapi.yaml güvenlik şeması `cookieAuth`a revize edilir; **ADR-001 de güncellenir** (kendi JWT — cookie-taşımalı). |
| 2 | Hata zarfı `{error:{code,message}}` | FastAPI `detail` + 422 Pydantic dizisi; merkezi `constants/errorMessages.ts` haritası | Zarf ZORLANMAZ. Kaygı-duyarlı mesajlar (kiro-api.js'tekiler) `errorMessages.ts`'e taşınır — tek harita. |
| 3 | camelCase alanlar (`tytNet`, `kaygiTonu`) | snake_case + Türkçe karışık (`ad_soyad`, `sifre`, `question_id`, `new_stability`) | Sınır katmanında mapper (`utils/questionMappers.ts` deseni). types.ts (design) → repo `types/index.ts` eşleme tablosu §H3. |
| 4 | Base path `api.kiro2.app/v1` | `${config.api.baseURL}/api/v1/*` | Path'ler `/api/v1/*`; design openapi'deki kısa yollar bu prefix'e maplenir. |
| 5 | UI yığını serbest | MUI + lucide + emotion (kanon yasağı) `Modern*Page`'lerde | ADR-000 retrofit: yeni ekranlar `frontend/src/kiro/**` altında tokens.css + ui-starter ile; `Modern*` sayfalar ROTA ROTA değiştirilir, tek seferde silinmez. |

## A · Auth & hesap (Sprint 1-2)

| İş | Backend dosyası | Frontend dosyası | Prototip referans |
|---|---|---|---|
| Giriş | `backend/api/auth.py` → `POST /api/v1/auth/login/secure` (VAR) | `services/authService.ts` (VAR, dokunma) · `store/authStore.ts` · YENİ `kiro/screens/GirisPage.tsx` (`ModernLoginPage.tsx`'in yerini alır) | `KIRO2 Giris.dc.html` |
| Kayıt | `auth.py` → `POST /register` — `ad_soyad`+`sifre`+`rol`+`veli_email` bekler (VAR) | `authService.register` mapper'ı ZATEN yazılmış | `KIRO2 Giris` kayıt sekmesi |
| Kurtarma | `auth.py` → `forgot-password` / `reset-password` (VAR) | `authService` (VAR) · YENİ `kiro/screens/HesapKurtarmaPage.tsx` | `KIRO2 Hesap Kurtarma.dc.html` (3 adım state-machine) |
| Onboarding kaygı-tonu | YENİ: `register` payload'ına `kaygi_tonu` (agir/gelgit/sakin, nullable) + `misafir_yerlestirme{theta}` alanı | YENİ `kiro/screens/OnboardingPage.tsx` (ton → ölçüm → payoff); ton+θ `usePlacementSession.ts` sonrası kayıtta taşınır | `KIRO2 Onboarding.dc.html` Adım 1 (onaylı kopyalar) |
| Veli bağlama (KVKK) | `auth.py` `veli-onay/verify·withdraw` (VAR — token/e-posta akışı). YENİ: kod-temelli çift onay 3 ucu (`POST /parent/link {kod}` · `/parent/link/consent` · `/me/parent-link/approve`) bu dosyaya ya da `api/parent_*`'a eklenir; mevcut veli-onay tokeni altyapı olarak yeniden kullanılır | `services/parentService.ts` (baseUrl `/api/v1/parent`) genişler · YENİ `kiro/screens/VeliBaglamaPage.tsx` | `KIRO2 Veli Baglama.dc.html` (çift taraflı onay + "asla görmezsiniz" listeleri) |

## B · Çekirdek döngü (Sprint 3-5) — motorlar zaten sunucuda ✓

| İş | Backend | Frontend | Prototip |
|---|---|---|---|
| FSRS due/review/stats | `backend/app/api/fsrs.py`: `GET /api/v1/fsrs/due` · `POST /review` · `GET /stats` (VAR, düz JSON). YENİ: `ReviewRequest`'e `grade:int(1-4)` ekle — şu an `is_correct` ikili; kanon 4 derece. NOT: `fsrs.py`'deki eski `/flashcards/*` dict-wrapper seti KANONİK DEĞİL — kullanılmaz, deprecate | `services/fsrsService.ts` (uyum yorumları hazır) · `FSRSReviewPage.tsx` → Şafak reskini | `KIRO2 FSRS Tekrar.dc.html` (4 derece + aralık etiketi sunucudan) |
| CAT oturumu | `backend/app/api/cat.py` (session start/answer/status/delete — VAR) + `app/services/cat_session.py`(35KB) · `irt_engine.py` | `hooks/useCATSession.ts` · `CATPage.tsx` → reskin | `KIRO2 Adaptif Test.dc.html`; YENİ: answer şemasına `secim:null` ("Emin değilim") |
| Misafir yerleştirme | `backend/app/api/placement.py` (VAR — start/answer/result) + `placement_service.py` | `hooks/usePlacementSession.ts` → Onboarding akışına | `KIRO2 Onboarding.dc.html` ölçüm adımı |
| Soru çözme + deneme oturumu | `/api/v1/osym-exam/*` (create/start/current-question/save-answer/navigate/complete/performance — VAR, `services/examService.ts` 20KB eşli) | `examService.ts` (dokunma) · `ModernExamStartPage/ExamPage` → `kiro/screens/SoruCozmePage.tsx` | `KIRO2 Soru Cozme.dc.html` + `KIRO2 Harmanlanmis Deneme.dc.html` |
| DOĞRULA (kanon) | `save-answer` yanıtı doğru cevabı oturum bitmeden SIZDIRMAMALI — `osym_exam` router'ında denetle; sızdırıyorsa yanıttan çıkar | — | "dogru yalnız answer/complete yanıtında" |
| Neden geri bildirim | `alternative_solutions_api.py` + soru çözüm alanları (`content_api.py`) | YENİ `kiro/components/NedenPanel.tsx` | `KIRO2 Neden Geri Bildirim.dc.html` (terracotta, suçlamasız) |
| Sınav sonuç | `/api/v1/sinav/history·results` + `student-dashboard/istatistikler` (VAR) | `ModernExamResultsPage` → reskin: net-birincil | `KIRO2 Sinav Sonuc.dc.html` ("yalnız yön göstergesi" etiketi asla kalkmaz) |
| Öğrenme yolu + haftalık plan | `backend/app/api/learning_path_daily.py`: `/status` `/today` `/next` `/weekly` `/goal` (HEPSİ VAR — design `/plan/week` ihtiyacını karşılar) · `learning_path_dungeon.py` | `hooks/useLearningPath.ts` · `ModernLearningPathPage`(41KB) → parçala + reskin | `KIRO2 Ogrenme Yolu` · `KIRO2 Haftalik Plan` · `KIRO Bilgi Atomlari` |
| Sıralama tahmini | `backend/app/api/estimator.py` + `yks_estimator.py` (VAR) | Panel hero'suna | `KIRO2 Ogrenci Paneli.dc.html` |

## C · Oyunlaştırma (Sprint 6-8)

| İş | Backend | Frontend | Prototip |
|---|---|---|---|
| Seri | `backend/api/birlikte_streak_api.py` (VAR — ortak seri!) + YENİ `POST /streak/checkin` (yoksa günlük aktiviteden türet) | `hooks/useGamification.ts` · `BirlikteStreakPage.tsx` | `KIRO2 Seri Dondurma` + `KIRO2 Arkadas Serisi` |
| Lig | gamification servisi (`services/socialService.ts` 14KB) — S8 başında KEŞİF: lig ucu backend'de doğrulanır, yoksa YENİ `/league`; sakinMod + **"Sıralamayı gizle"** kullanıcı ayarı olarak settings'e | `LeaguePage.tsx` → reskin | `KIRO2 Lig.dc.html` (KARARLAR: rekabet opsiyonel) |
| Düello | `backend/api/cozum_duellosu_api.py` (VAR) — ASENKRON karar: senkron akış poll'a (15sn, ADR-003) çevrilir; Güçler MVP-dışı | `DuelPage.tsx` + `CozumDuellosuPage.tsx` → TEKLEŞTİR + reskin (iki sayfa aynı işin iki kuşağı) | `KIRO2 Duello.dc.html` |
| Boss | `BossFightPage.tsx` VAR; tema = en zayıf konu (learning_path `/status`) | reskin | `KIRO2 Boss Savasi.dc.html` (`kanon-allow: boss-arena`) |
| Kutlama/rozet | `daily_quest_api.py` + gamification | YENİ `kiro/screens/KutlamaPage.tsx` (4 tür) | `KIRO2 Kutlama` · `KIRO2 Basarimlar` |

## D · Roller (Sprint 11)

| İş | Backend | Frontend | Prototip |
|---|---|---|---|
| Sınıf kur + kod | `backend/app/api/teacher_classroom.py`: `GET/POST /api/v1/teacher/classes` (VAR!). ÖNCE POST şeması okunur — `katilim_kodu` yoksa YENİ: yanıta eklenir + `POST /classes/{id}/code/rotate` + öğrenci ucu `POST /me/class/join {kod}`; sınıf varsayılanları (sıralama yayınlanmaz · risk bayrağı inmez) SUNUCU yazar | `ModernTeacherClassesPage.tsx` → `kiro/screens/SinifKurulumPage.tsx` | `KIRO2 Sinif Kurulum.dc.html` (A3 spec, SPRINT11) |
| Ödev döngüsü | `teacher_classroom.py`: `GET/POST/DELETE /assignments` (VAR). YENİ: öğrenci ucu `GET /assignments/me` + `POST /assignments/{id}/progress`; durum dili "bekliyor" sunucu sözleşmesine | `ModernTeacherAssignmentsPage` → reskin · YENİ `OdevlerimPage` | `KIRO2 Odev Atama` · `KIRO2 Odevlerim` |
| Öğrenci özeti (salt-okur) | YENİ `GET /api/v1/teacher/students/{id}/summary` (`teacher_classroom.py`'ye; `/students` listesi VAR) — GİZLİLİK: sohbet/mood/tekil cevap ASLA; risk sinyali sunucuda | YENİ `kiro/screens/OgrenciOzetPage.tsx` | `KIRO2 Ogretmen Ogrenci Ozet.dc.html` |
| Veli paneli + haftalık özet | `services/parentService.ts` `/api/v1/parent` (VAR) + `ModernParent*` 4 sayfa; YENİ: haftalık özet e-postası (backend rapor + mailer cron; veri yoksa GÖNDERME) | reskin | `KIRO2 Veli Paneli` · e-posta: `KIRO2 Eposta Bildirim.dc.html` §A |

## E · Ticari (Sprint 10)

- `backend/api/billing_api.py` (4.5KB — iskelet): `GET /billing/plans` · `POST /billing/trial` (`dogrulama_gerekli`+`clientSecret` 3DS) · `GET/DELETE/reactivate /billing/subscription` uçlarını aç; **Stripe birincil (ADR-002)**, webhook → subscription state.
- Frontend: ham kart formu TAŞINMAZ → **Stripe Elements** + appearance eşlemesi (SPRINT10 spec); `KIRO2 Odeme.dc.html` faz=3ds bekleme durumu birebir; `KIRO2 Plan Yonetimi.dc.html` (iptal tek adım + "Geri aç"); fiyat yalnız veli yüzünde.

## F · Bildirim · senkron · çevrimdışı (Sprint 12)

- VAR: `services/backgroundSyncService.ts` → `/api/v1/sync/exam-sessions` + `/sync/progress` + `/push/subscribe`; `offlineStorageService.ts` → `/api/v1/questions/download`; `sw.ts` + workbox; `OfflineModeUI.tsx`.
- İŞ: K1 kararı (bant + cevap kuyruğu + FSRS önbelleği) — mevcut sync altyapısına `KIRO2 Cevrimdisi.dc.html` yüzü; push ADR-004 gereği flag'le KAPALI (uç dursun); bildirim listesi `student-dashboard/bildirimler` (VAR) → `KIRO2 Bildirim Merkezi.dc.html`; kopya formülleri `KIRO2 Eposta Bildirim.dc.html` §B'den `errorMessages.ts` yanına `notificationCopy.ts`.

## G · AI (Sprint 9)

- VAR: `backend/api/ai_chat_routes.py` + `/api/v1/enhanced-chat` (+`/stream`, sessions) · `services/chatService.ts` · `StreamingChat.tsx`.
- İŞ: Sokratik sistem-prompt sunucu tarafına (cevabı vermeden yönlendir; merdiven tespiti sunucuda — SPRINT9); "Koç şu an toparlanıyor…" ErrorState; vision Faz 4.5 flag.
- İNCELE: `backend/api/bilge_alp.py` (koç kişiliği adayı — Sokratik prompt'un evi olabilir) · `backend/api/diary_api.py` (mood/günlük — KARARLAR #5 `POST /me/mood` buraya bağlanabilir; yoksa YENİ uç).
- Kaygı Ölçüm (STAI-S): araştırma aracı, feature-flag arkasında; STAI lisansı ÖN KOŞUL (S9 spec).

## H · Kesişen teknik işler

1. **`frontend/src/kiro/` iskeleti:** `tokens.css`+`tokens.ts` (handoff) → `kiro/tokens/`; `ui-starter/` 20 bileşen → `kiro/ui/` (Faz 2 kalite kapısı: tip + test + Storybook); ekranlar `kiro/screens/`.
2. **kanon-lint CI:** `design/scripts/kanon-lint.mjs` → frontend lint pipeline'ına (`package.json` script + CI job). MUI/lucide importu = ihlal → `Modern*` dosyaları başlangıçta allow-list'te, rota değiştikçe listeden düşer.
3. **Tip eşleme:** design `types.ts` ↔ repo `frontend/src/types/index.ts`: `Persona↔User`, `tytNet↔snake/istatistikler alanları`, `ReviewItem↔DueItemResponse(question_id,stem,options,retrievability…)`, `SeviyeBilgi↔gamification`. Mapper'lar `kiro/api/mappers.ts` — UI katmanı design tipleriyle konuşur.
4. **openapi.yaml revizyonu (tek commit):** cookieAuth · `/api/v1` prefix · snake_case gerçek şemalar · VAR/YENİ etiketleri bu plandan; path düzeltmesi: öğrenci-özet `/teacher/student/{id}` → `/teacher/students/{id}` (repo çoğul deseni).
5. **Smoke test:** `KIRO2 API Konsol.dc.html`'deki çağrı listesi = MSW handler seti + Playwright API smoke (mock kaynağı: `design/kiro-api.js`).

## I · Yürütme sırası (mevcut sprint spec'leriyle hizalı)

S0 kurulum (design/ klasörü + kiro/ iskeleti + kanon-lint) → S1 Giriş&Kayıt+Ödevlerim (auth.py VAR, assignments öğrenci ucu YENİ) → S2 Kurtarma+Onboarding (placement.py VAR)+Panel (estimator VAR) → S3 Soru Çözme+Neden+FSRS (grade alanı YENİ) → S4 Adaptif+Deneme+Sonuç (osym-exam VAR) → S5 Plan+Yol (learning_path_daily VAR) → S6-7 duygusal çekirdek (yüz işi) → S8 sosyal (duel asenkronlaştır) → S9 AI (enhanced-chat VAR) → S10 ticari (billing_api doldur + Stripe) → S11 roller (teacher_classroom VAR + summary/kod YENİ + veli e-postası) → S12 platform (sync VAR, K1 yüzü).

Mobil (Expo) bu planın KAPSAMI DIŞINDA (ADR-004; `KIRO2 Mobil.dc.html` yalnız 390pt QA referansı).

**Her sprintte DoD:** PORT_DURUM satırı + kanon-lint temiz + API Konsolu smoke seti yeşil + piksel referans = DC.

## J · Backend'e eklenecek YENİ uçların tam listesi (özet)

`register.kaygi_tonu+misafir_yerlestirme` · `parent/link ×3` (veli-onay altyapısını yeniden kullan) · `fsrs grade:1-4` · `cat answer secim:null` · `teacher classes katilim_kodu + code/rotate` · `me/class/join` · `assignments/me + progress` · `teacher/students/{id}/summary` · `streak/checkin` (yoksa) · `me/mood` (önce diary_api incele) · `league` (S8 keşfinde uç çıkmazsa) · `billing trial/plans/subscription` doldur · veli haftalık özet cron. Geri kalan her şey REPODA ZATEN VAR — iş çoğunlukla yüz (Şafak reskini) + sözleşme hizalama.
