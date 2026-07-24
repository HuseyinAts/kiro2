## Session Handoff — 2026-07-25 (F4-S1b AI yüzeyi — CANLI PASS)
**Branch:** feature/self-evolution-optimization · **PUSH YOK**
**Son commit:** d1ffa2cde (F4-S1b AI fix + mount)
**Kod zinciri:** b8626be6a (F4-S0) → c9c771e0e (Düello) → 24cac0bcc (login wiring, henüz mount değil) → 14f53afe1 (full-bleed) → d1ffa2cde (AI yüzeyi)
**Frontend docker :3000:** tüm zincir DEPLOY (rebuild edildi, healthy).

### 🎯 CANLI KANITLAR (docker :3000, bu turda)
- **422 fix**: `POST /enhanced-chat/stream` artık **403** dönüyor (422 DEĞİL) — `student_id` artık gövdede, Pydantic geçiyor. 403 = dokümante edilmiş kapsam-dışı IDOR (bkz aşağı).
- **session-unwrap fix**: `/chat` sayfa yüklemesinde GERÇEK geçmiş oturum (`00f34a29-...`, sessions[0]=en güncel) + gerçek mesajlar (`merhaba` → AI yanıtı, bu oturumun BAŞINDA curl ile oluşturduğum session) doğru render oldu. `/sokratik` aynı kod yolunu paylaşıyor, aynı 200/200.
- **Full-bleed**: `/chat` ve `/sokratik` App shell'siz, kiro SideNav ile tam-ekran.
- **403 zarif ele alındı**: ErrorState + "Tekrar dene" (çökme yok, onError doğru tetiklendi).

### Yapılanlar (commit'li, bu turda: d1ffa2cde)
- **Backend keşif (canlı curl kanıtlı)**: `student_id` gövdede eksikti → HER ZAMAN 422. `GET /sessions` `{success,sessions}` zarfı merkezi unwrapData'nın anladığı `data` anahtarını kullanmıyor → mesajlar hep boş + `sessions[length-1]` (EN ESKİ oturum) alınıyordu.
- **Kritik mimari bulgu**: backend IDOR guard `student_id`'nin `users.id` DEĞİL `learning_path_student_profiles.student_id` (`STU_xxx`) olmasını şart koşuyor (curl: users.id→403, STU_→200). Bu, **mevcut prod `ModernChatPage`/`chatService.ts`'de de aynı sorun** (`student_id: user?.id`) — kiro'nun icat ettiği bir kontrat değil. **Bilinçli kapsam dışı bırakıldı** — backend/DB değişikliği bu turda yapılmadı.
- **Fix**: `getSohbet` → `sessions` zarfını açıkça çöz + `sessions[0]` (en güncel) + mesajları AYRI uçtan (`/enhanced-chat/sessions/{id}/messages`) çek. `postSohbetMesaj`/`streamSohbet` → `student_id: args.studentId` gövdeye eklendi.
- **Wiring**: `SohbetStreamArgs.studentId?` (additive) · `AISohbetPage`/`SokratikPage` `studentId?` prop (additive) · YENİ `kiro/routes/KiroAISohbetRoute.tsx` + `KiroSokratikRoute.tsx` (authStore.user.id → studentId, ekran store-bağımsız kalır).
- **Mount**: App.tsx `/chat` kademeli-swap (ModernChatPage→kiro AISohbetPage) + yeni `/sokratik` route. `kiroRoutes.ts` KIRO_FULLBLEED_ROUTES += `/chat`, `/sokratik`.

### Gate
tsc 0 · **kiro vitest 501/501** (74 dosya, +10 bu oturumda: sohbet.test +4, wrapper testleri +2 yeni dosya, GirisPage.test +4 önceki turdan) · vite build OK.

### Sonraki Adımlar
1. **F4-S1a tamamlama (A2.2b)**: `/login` → GirisPage swap (henüz mount değil — sadece wiring hazır, commit 24cac0bcc). Link hizala (`/hesap-kurtarma`→`/forgot-password`, `/onboarding`→`/register`) + register field-set (soyad/birth_date/rol/veli_email KVKK).
2. **İnteraktifCozumPage**: 3. AI ekranı (kapsam dışı bırakıldı, App'te karşılığı yok, aynı pattern uygulanabilir).
3. **Backend/veri sorunu (ayrı, büyük scope)**: `learning_path_student_profiles` linkajı — chat'in gerçekten çalışması için (mevcut prod dahil) bu tabloya satır gerekiyor. Onboarding akışı mı oluşturuyor, yoksa eksik mi — araştırılmalı.
4. F4-S2+ backend yüzeyler: Çevrimdışı · Veli (mapVeliCocuk bug + ParentDashboard alanları) · KVKK.

### Seed test kullanıcı
test@kiro2.com / Kiro2Beta2026@x (STUDENT). users.id=`0d3b011a-8be9-49cb-9a87-f8a8317ccc3d`, gerçek learning-path student_id=`STU_d04020744222` (DB'den, chat 200 için gerekli).

### Operasyonel ders (tekrar): PWA service worker
Her frontend docker rebuild sonrası smoke ÖNCESİ SW unregister + `caches.delete` ZORUNLU (Playwright: `navigator.serviceWorker.getRegistrations()→unregister` + `caches.keys()→delete`).
