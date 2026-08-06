## Session Handoff — 2026-08-07 (S205: FAZ 0 + Cursor planları + loader/App kararları)

**Dal:** feature/self-evolution-optimization · **Son commit:** `af99079c2`

### ✅ Tamamlanan iş (9 commit bu oturumda)
`1091db7ab` question_bank mühür+invaryant · `6f3380072` celery DSN+parola ·
`eb40cb30d` streak organization_id · `d5bf6c339` takipsiz migration ·
`b84bdc503` scratch gitignore · `d9f6953f6` teacher-copilot mock-etiketli ·
`0fb271e97` DISABLED_ROUTERS envanteri · `0d17f924f` 6 router açıldı ·
`af99079c2` /login regresyon geri alımı + copilot rotası mount

### İçerik kurtarma
`question_bank` **2.304/21 → 187.835/182.519** (aktif 110.858), kapı **25.127**.
Celery: 3 seri bağlı kusur (DSN çözümü, parola sızıntısı, organization_id) çözüldü,
görev ilk kez çalıştı (`sent: 4`).

### loader.py kararı — UYGULANDI
110 router'ın 110'unu da frontend çağırıyor (envanter: `docs/audits/2026-08-07_disabled_routers_envanteri.md`).
6 yasal/ticari kritik açıldı: kvkk_consent/privacy/notice, org_billing, audit,
ferpa_coppa_compliance. **Doğrulandı** (create_app() canlı route tablosu): 6/6 yüklendi,
toplam yol 318→369. `test_router_registration.py` 3/3.
**Kalan 104 router kasıtlı kapalı** — açılış maliyeti (import süresi/bellek) ölçülmedi.

### App.tsx kararı — UYGULANDI
`/login` regresyonu (KiroLoginRoute→ModernLoginPage) geri alındı (görev #419 emsali).
`/teacher/copilot` rotası mount edildi. tsc + build geçti. `git stash` ile App.tsx
çıkarılıp aynı kırık test tekrar koşuldu — **aynı şekilde kırık**, yani 28 dosya/111
test kırığı App.tsx'ten bağımsız, önceden var olan durum.

### 6 Cursor planı — nihai durum
| Plan | Durum |
|---|---|
| P4 PWA offline sync | BİTMİŞ — 26/26 test |
| P2 CI paralelleştirme | BİTMİŞ — pytest.ini + vite pool zaten yeterli |
| P6 Teacher Co-Pilot | TESLİM — mock etiketli, rota mount edildi |
| P3 Code-splitting | YARIM — `vendor-mui-core` 794 kB + `vendor-prism` 619 kB kalıyor |
| P1 Alembic round-trip | YARIM — 9 test statik denetim, gerçek upgrade→downgrade→upgrade YOK |
| P5 Sokratik AI | KISMEN AÇILDI — `enhanced_chat` artık açık ama guard hâlâ bağlanmadı |

### ⚠️ Doğrulanmamış — dokunulmadı, açıkça işaretlendi
`AnimatedRoutes`, `GlobalCognitiveWrapper`, `SocraticAIAvatar` (App.tsx'te mount
edilen 3 yeni bileşen, Cursor 5 Ağu) — kendi test dosyaları YOK. tsc+build geçiyor
ama runtime davranışı doğrulanmadı.

### Önceden var olan kırıklık (yeni bulundu, bu oturumun kapsamı dışı)
Frontend: 28 test dosyası / 111 test App.tsx'ten bağımsız olarak kırık
(`VideoResourceGrid.test.tsx` örneğiyle kanıtlandı — App.tsx stash'lense de aynı).
Kök neden araştırılmadı.

### Sonraki adımlar
1. P5: guard'ı `enhanced_chat.py`'ye bağla (router artık açık)
2. Önceden var olan 111 test kırığının kök nedeni (ayrı, büyük iş — belki deep-audit)
3. P1: gerçek `alembic upgrade head && downgrade -1 && upgrade head` testi
4. P3: `vendor-mui-core`/`vendor-prism` opsiyonel bölme
5. Kalan 104 router: açılış maliyeti ölçümü, sonra kademeli açma kararı

### Açık kalemler (FAZ 0'dan, henüz kapanmadı)
- Celery fix konteynere `docker cp` ile kondu, **imajda yok** — sonraki deploy'da rebuild şart
- `kiro2_app` parola rotasyonu kararı kullanıcıda
- `questions` legacy tablosu silik kalacak (karar verildi)
