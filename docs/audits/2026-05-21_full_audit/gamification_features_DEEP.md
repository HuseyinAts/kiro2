# KIRO2 Gamification + Engagement Features Deep Audit

**Tarih:** 21 May 2026 | **Audit branch:** master | **Scope:** READ-ONLY  
**Audit eden:** Claude Code (Opus 4.7 1M)  
**Hedef:** Son kullanıcı eğlence ve engagement boyutu — bu boyut önceki audit'lerde HİÇ kapsanmadı.

---

## Yöneticiler için Özet (TL;DR)

KIRO2'nin gamification katmanı **gösterişli ama içi boş**. 12 endpoint dosyası ve 7 frontend sayfası mevcut — total ~5,150 backend + ~3,370 frontend satır. Ancak:

| Kategori | Bulgu |
|---|---|
| **Phantom XP** | Soru Meydani, Birlikte Streak, Cozum Duellosu, Usta-Cirak, Oba Seferleri "+X XP" mesajı gösterir ama `XPTransaction` tablosuna HİÇ yazmaz → leaderboard'a katkı sıfır |
| **Anti-cheat yok** | Dungeon `/complete` score, Oba Seferleri `contribute` amount, league `award_xp` client'tan trust edilir |
| **Broken endpoint** | `DuelPage.tsx` `/duel/{id}/current-question` ve `/duel/{id}/result` çağırır — backend'de YOK. Düello UI çalışmaz |
| **Half-done features** | Oba Seferleri'nde `ObaChallenge` üreten kod YOK — "Bu hafta aktif görev yok" sonsuza kadar gösterilir |
| **Hardcoded placeholders** | `DEMO_OBA_ID='demo-oba'`, `question_bank_id='auto'` — production'da literal placeholder string'ler |
| **Bilge Alp BKT hatası** | `topic_id.like('matematik%')` UUID-style topic_id'lerle eşleşmez → her NPC daima %0 mastery varsayar |
| **UstaCirak yarım** | "Oturum Başlat" butonu var, "Oturum Bitir" butonu YOK → XP hiç verilmez. Mentor ile iletişim aracı yok (chat/whiteboard) |
| **Pure backend tests** | 50 test mevcut ama `_col_default()`, `LEAGUE_TIERS.index()` gibi model-default doğrulama — engagement logic test edilmez |

**Sonuç:** Bu feature seti **görsel demo** seviyesinde. Production sızıntıya hazır değil. Tahmini gerçek engagement skoru: **3.2/10**.

---

## Feature Inventory

| Feature | Backend dosyası | Endpoint | Frontend dosyası | Frontend satır | Test |
|---|---|---|---:|---:|---|
| Bilge Alp (AI tutor) | `backend/api/bilge_alp.py` | 2 (chat, dialog-options) | `frontend/src/features/realm/NPCDialog.tsx` | 330 | YOK |
| Soru Meydani (Q&A forumu) | `backend/api/soru_meydani_api.py` | 7 | `pages/SoruMeydaniPage.tsx` | 325 | YOK |
| Birlikte Streak (group streak) | `backend/api/birlikte_streak_api.py` | 3 | `pages/BirlikteStreakPage.tsx` | 200 | YOK |
| Cozum Duellosu (solution duel) | `backend/api/cozum_duellosu_api.py` | 5 | `pages/CozumDuellosuPage.tsx` | 286 | YOK |
| Duel (1v1 ELO) | `backend/api/duel_api.py` | 5 | `pages/DuelPage.tsx` + `components/LearningPath/DuelMode.tsx` | 338 + 1072 | model-default only |
| Oba (Guild) | `backend/api/oba_api.py` | 7 | `pages/ObaPage.tsx` | 286 | YOK |
| Oba Seferleri (team mission) | `backend/api/oba_seferleri_api.py` | 4 | `pages/ObaSeferleriPage.tsx` | 232 | YOK |
| Usta-Cirak (mentor) | `backend/api/usta_cirak_api.py` | 5 | `pages/UstaCirakPage.tsx` | 188 | YOK |
| Gamification (XP/badge/leaderboard) | `backend/api/gamification_api.py` | 17 | `components/Gamification/*.tsx` (8) | 1459 | `tests/unit/test_gamification_api.py` (1001 satır), `tests/test_gamification.py` (20 test) |
| ZPD Maarif | `backend/api/zpd_maarif.py` | 17 | (frontend ayrı sayfa görmedim) | — | YOK |
| Dungeon Learning Path | `backend/app/api/learning_path_dungeon.py` | 2 | `components/LearningPath/DungeonMap.tsx` + 5 yan dosya | 147 + ~640 | `tests/unit/test_dungeon_progress.py` (3), `tests/unit/test_dungeon_endpoint.py` (4) |
| League | `backend/api/league_api.py` | 3 | (separate) | — | model only |

Total: **77 endpoint**, **3,810 backend satır**, **~5,225 frontend satır**, **~77 unit test** (çoğu model-default).

---

## A. Bilge Alp (AI Tutor NPC)

### Implementation depth — 6/10

**Backend** (`bilge_alp.py:1-427`):
- 12 ders için NPC personality dict (Aristo, Gauss, Yunus, Mevlana, vs) — Türkçe kültürel uygunluk **iyi**
- System prompt builder mastery seviyesine göre 3 ZPD bandı (`<0.40`, `<0.70`, `>=0.70`) seçer
- Quest step takibi (0/1/3+) ile ilerleme farkındalığı
- SSE streaming Claude Haiku 4.5'tan (`claude-haiku-4-5-20251001`)
- BKT score **client'tan değil DB'den** alınır — güvenlik OK (`bilge_alp.py:241-261`)
- Conversation history 8 turn (`history[-8:]`) cap'li

**Kritik bug — BKT query topic_id format mismatch (`bilge_alp.py:251-257`):**
```python
result = await db.execute(
    select(sa_func.avg(BKTState.p_learn)).where(
        BKTState.student_id == str(current_user.id),
        BKTState.topic_id.like(f"{realm_slug}%"),  # ← realm_slug = "matematik"
    )
)
```
`BKTState.topic_id` `topic_hierarchy.id`'ye işaret eder (`gamification.py:44-46`). `topic_hierarchy` PK'leri UUID string'ler veya kod ("MAT.001"). `learning_event_service.py:229` placement sırasında `subj_name.lower()` ("matematik") yazıyor, ama günlük quiz/IRT akışı UUID-format topic_id yazıyor.

**Sonuç:** Eğer placement seed varsa ortalama p_learn placement değeriyle hesaplanır (5-100 arası), ama günlük öğrenme veriyle güncellenmez. Her NPC kullanıcıya **donmuş seviye** ile yanıt verir. ZPD bandı yanlış band'a tutuk.

**LLM provider chain:**
- `ANTHROPIC_API_KEY` veya `LITELLM_API_KEY` env var ile gerçek Claude API
- Yoksa mock fallback (`bilge_alp.py:211-216`): `"Merhaba! Şu an tam olarak bağlanamıyorum..."` — kullanıcı LLM yokken bunu birkaç kelime için görür, sonra siliner. UX kötü.

**Frontend** (`NPCDialog.tsx:1-330`):
- Streaming token render iyi yapılmış (`useState` + reader.read())
- Quick prompts ('Konuyu anlat', 'Soru sor', 'İpucu ver', 'Nasıl çalışırım?') — gerçek bir UX patterni
- Avatar emoji (📐, 🔭, ⚗️, 📚) — Türkçe kültürel uygunluk
- AbortController ile cancel desteği
- Tailwind ile gradient bg, animasyon — modern görsel
- Ancak BKT bug yüzünden mastery göstergesi yanlış

### Conversation quality
- System prompt 152 satır, çok iyi yapılandırılmış (KİŞİLİK, ZPD hint, QUEST hint, KURALLAR)
- Türkçe imla kalitesi YÜKSEK (NFC normalize edilmiş, "Hosgeldin" değil "Hoşgeldin" gibi karışıklıklar yok)

### Engagement score: **6/10**
+ Persona çeşitliliği güzel  
+ Streaming yanıt yaratıcı  
+ Cultural fit (Mevlana, Yunus, Farabi vs.) güçlü  
− BKT entegrasyonu kırık → kişiselleştirme yalan  
− LLM mock fallback nahoş  
− Quest progression takibi yarım (`quest_step` parametresi var ama hangi state'i temsil ettiği belirsiz)  
− "Görevi Başlat" butonu var (`NPCDialog.tsx:228-237`) ama backend'de `quest_step` artırma endpoint'i yok

### Findings
- **P0 — `bilge_alp.py:255`**: BKTState.topic_id LIKE pattern UUID format ile uyumsuz. Fix: realm_slug → subject_id mapping + JOIN topic_hierarchy.subject_area filtering
- **P1 — `bilge_alp.py:213`**: Mock fallback string content ileride model değişikliğinde kullanıcıya gönderilen yanıltıcı statik metne dönüşür → loglanmaz ama kullanıcı her seferinde aynı şeyi görür
- **P2**: NPCDialog'da quest_step artışı için endpoint yok → "Görevi Başlat" butonu görsel oyalama

---

## B. Soru Meydani (Q&A Forumu) — F1

### Implementation depth — 5/10

**Backend** (`soru_meydani_api.py:1-451`):
- Template-based question creation (5 type: `how_to_solve`, `explain_concept`, vs) — serbest metin yasak
- Daily limit: 5 soru/gün, 10 çözüm/gün
- Content filter (`social_content_filter`) — 7 katman per `Session 158 audit`
- Vote (helpful/not_helpful), kendine oy yasak
- Accept solution (sadece soru sahibi)

### XP Phantom — CRITICAL
```python
# Lines 29-33:
XP_ASK_QUESTION = 5
XP_SUBMIT_SOLUTION = 10
XP_ACCEPTED_SOLUTION = 25
XP_HELPFUL_VOTE = 2
```
Bu constants'lar **HİÇ KULLANILMIYOR** kod akışında. Sadece response message'larına string olarak gömülmüş:
```python
"message": "Cozumunuz yayinlandi! +10 XP"  # Line 323 — string literal, gerçek XP YOK
```
`grep -n "XP_ASK_QUESTION\|XP_SUBMIT_SOLUTION" backend/` → SADECE 1 dosya (`soru_meydani_api.py`). `learning_event_service.GamificationDBService.award_xp` HİÇ çağrılmıyor.

→ Kullanıcı "+10 XP kazandın" mesajı görür ama leaderboard'da hiçbir şey değişmez.

`social_summary_api.py:48` ise XP'yi RUNTIME hesaplar: `forum_xp = q_count * 5 + s_count * 10`. Yani `/social/summary` çağrısında "phantom XP" gösterilir, ama bu da `users.total_xp` ile leaderboard'a yansımaz.

### Engagement score: **4/10**
+ Template-based input — kalite kontrol (free-text spam yok)  
+ Daily limit istismarı zorlaştırır  
+ Content filter ciddi  
+ Vote + accept solution motive edici  
− Phantom XP **temel motivasyon kıracaktır**  
− Question şablonları dar (sadece 5 type), öğrenci "Bu sorunun cevabını anlamadım, X kısmında takıldım" diyemez (free body var ama sadece 500 char ve opsiyonel)  
− Photo upload yok (formül yazımı zor, ekran görüntüsü gerekir — `image_url` solution'da var ama soru için yok)

### Findings
- **P0**: XP_ASK_QUESTION sabitleri actual award_xp call'a bağlanmalı (4-line fix)
- **P1**: Question creation'a image_url ekle
- **P2**: Solution'a `helpful_count` threshold'u (vd ≥3 oy → otomatik gamification badge "Yardımsever")

---

## C. Birlikte Streak (Group Streak) — F5

### Implementation depth — 5/10

**Backend** (`birlikte_streak_api.py:1-237`):
- `/request` → bekleyen partner varsa eşleştir, yoksa kuyruğa al
- `/status` → bugünkü tamamlama durumu
- `/complete-today` → bugünü mark, partner de tamamlamışsa streak++

**Streak break detection** (`tasks/social_tasks.py:30-84`):
- Celery beat ile günlük 00:05'te (`celery_app.py:166`)
- Dün partnerlerden biri logo yoksa `current_streak = 0`

**XP Phantom** confirmed:
- `XP_DAILY_BOTH = 5`, `XP_7_DAY_BONUS = 30`, `XP_30_DAY_BONUS = 100` (`birlikte_streak_api.py:27-29`)
- `pair.total_xp_earned += xp_earned` (DB'de pair-level tracking)
- AMA `XPTransaction` yazılmıyor → `users.total_xp` artmıyor → leaderboard'a etki yok
- `social_summary_api.py:94-102` retroactive olarak `pair.total_xp_earned` toplar ama bu ayrı bir sistem

### Critical engagement gap: "GÖREV" ne?
`/complete-today` endpoint bir POST çağrısıdır — backend hiçbir doğrulama yapmaz. Frontend (`BirlikteStreakPage.tsx:193`) sadece **buton var**: "Bugunku Gorevi Tamamla". Ne yapılması gerektiği tanımsız. Kullanıcı sabah 6'da girip butona basabilir. **Sıfır anti-cheat.**

Spec'te bir görev olmalı: günlük quiz, X dakika çalışma, Y soru çözme. Backend bunu doğrulamaz.

### Engagement score: **3/10**
+ Partner bağımlılığı sosyal motivasyon yaratır  
+ Milestone (7d, 30d) bonus iyi pattern  
+ Streak break detection Celery-backed  
− Tam phantom XP (leaderboard'a hiç yansımaz)  
− "Görev tamamlandı" sadece buton tıklama — gerçek bir aktivite gerektirmez  
− `student_b_id=""` placeholder (waiting state) — empty string foreign key crash riski (DB constraint kontrolü yok)  
− Streak ortaklık ayrılma endpoint'i YOK → 6 ay sonra ortağın sessizliği streak'i bozar ama ayrılıp yenisini bulma yolu yok

### Findings
- **P0**: `/complete-today` gerçek bir görev (quiz answer, study session) ile bağlanmalı. Şu an "click here" feature
- **P0**: `partner.student_b_id=""` yerine `NULL` kullan (`birlikte_streak_api.py:82`)
- **P1**: Ortağı ayırma endpoint'i yok → uzun süre cevapsız partner'dan kurtulma yolu yok
- **P2**: XPTransaction integration

---

## D. Cozum Duellosu (Solution Duel) — F2

### Implementation depth — 4/10

**Backend** (`cozum_duellosu_api.py:1-319`):
- Asenkron duello: challenger oluşturur, opponent katılır, ikisi çözüm yazar, topluluk 24 saat oy verir
- Voting expiry (`social_tasks.py:92-162`) Celery 30dk'da bir çalışır, winner_id atar
- Submission'a image_url destekli — solution'lar görsel olabilir

### CRITICAL: `question_bank_id` hiç doğrulanmaz
- Schema `question_bank_id: str` (`cozum_duellosu_api.py:40`)
- Frontend `CozumDuellosuPage.tsx:66`: `question_bank_id: 'auto'` literal string gönderir
- Backend hiç doğrulamaz, DB'ye `"auto"` string olarak yazar
- Voters duello'yu açtıklarında HANGI soru üzerinde tartışıldığını göremezler (`get_duel` endpoint sadece `question_bank_id` string'i döner)
- Sonuç: "X öğrencisinin çözümü vs Y öğrencisinin çözümü" gösterilir ama **soru görünmez**

### Logic bug — `cozum_duellosu_api.py:220`:
```python
sub_count = (await db.execute(
    select(func.count()).select_from(SolutionDuelSubmission)
    .where(SolutionDuelSubmission.duel_id == duel_id)
)).scalar() or 0
if sub_count >= 1:  # +1 for current = 2
    duel.status = "voting"
```
Comment "+1 for current = 2" yanlış: `db.add(submission)` çağrıldı ama `commit()` edilmedi → `func.count()` önceki committed olanları sayar. Eğer iki kullanıcı **eşzamanlı** submission gönderirse RACE → ikinci submission status'ü `voting` yapar ama ilk submission'ı doğru ekleyecek mi belirsiz. Lock yok.

### XP Phantom:
- `XP_WINNER = 30`, `XP_LOSER = 10` (line 29-30)
- HİÇ kullanılmıyor — voting expiry task winner_id set ediyor ama `award_xp` çağırmıyor
- `social_summary_api.py:53-61` retroactively winner count'tan XP hesaplar

### Engagement score: **2/10**
+ Asenkron olduğu için kullanıcılar arasında zamansal eşleşme gerekmez  
+ Topluluk oylama → öğrenciler birbirini değerlendirir (sosyal öğrenme)  
+ Image upload destekli  
− `question_bank_id="auto"` → duello soruya bağlı DEĞİL  
− Phantom XP  
− Race condition voting state transition  
− 24 saat oylama × 100 öğrenci ölçeğinde "şu an oylama bekleyen duellolarım" feed yok — kullanıcı oy verme fırsatını kaçırır  
− Loser için sadece 10 XP teselli → motivasyon zayıf

### Findings
- **P0**: `question_bank_id` doğrulanmalı: var mı? Aktif mi? Frontend'in `'auto'` göndermesi feature contract kırıyor
- **P0**: XPTransaction integration (winner için)
- **P1**: Voting submission state transition'da `SELECT FOR UPDATE` lock veya unique constraint
- **P2**: Notification/feed mekanizması (kimlerin duellosunda oylamam bekleniyor?)

---

## E. Duel (1v1 ELO Real-Time) — F1

### Implementation depth — 7/10

**Backend** (`duel_api.py`, `duel_service.py`):
- ELO sistemi (K=32, default=1200) — `duel_service.py:18-46`
- Bracket-based matchmaking (200 ELO genişliği) — fair play sağlar
- Redis queue + SSE pub/sub gerçek-zamanlı
- IRT-calibrated question selection — `_select_duel_questions` rastgele seçer (medium difficulty deniyor ama `func.random()` gerçek IRT calibration değil — yorum yanıltıcı)
- Server-side answer correctness check (`_check_answer_correctness`) — anti-cheat var
- IDOR check on stream endpoint (`duel_api.py:266-271`)

**Strong points:**
- Heartbeat 30s ile SSE bağlantı yönetimi
- ELO peak rating tracking
- Wins/losses/draws stats

### CRITICAL FRONTEND BUG — `DuelPage.tsx` broken
Frontend `DuelPage.tsx:108-112, 158-162` HIT eder:
- `GET /api/v1/duel/{session_id}/current-question` ← **backend'de YOK**
- `GET /api/v1/duel/{session_id}/result` ← **backend'de YOK**

`grep "/current\|/result" backend/api/duel_api.py` → 0 match.

Backend sadece şu endpointleri sunar:
- `POST /matchmake`
- `POST /{session_id}/answer`
- `GET /stream/{session_id}` (SSE)
- `GET /rating`
- `GET /history`

Sonuç: Frontend duello başlattıktan sonra **soru görünmez, sonuç görünmez**. `loadDuelSession` catch bloğunda `{question:null}` ile devam eder, kullanıcı boş ekran görür.

Alternatif `components/LearningPath/DuelMode.tsx` (1072 satır) muhtemelen düzgün çalışıyor — SSE event'leri dinliyor (`match_found`, `question`, `opponent_answered`, `duel_complete`). Ancak `DuelMode.tsx`'in nereden render edildiği belirsiz; `pages/DuelPage.tsx` ana route ise kullanıcılar broken pageʼa düşer.

### Race condition possibility
`DuelMatch.player1_answer` flush edilir (`duel_service.py:236`) ama session-level lock yok. İki oyuncu aynı anda answer post ederse "both answered" flag yanlış set edilebilir.

### Engagement score: **6/10** (potansiyel 9/10)
+ ELO + bracket matchmaking sağlam  
+ Real-time SSE  
+ Server-side cheat protection  
+ Win/lose stats kayıtlı  
− Frontend broken (endpoint çağrıları olmayan rotalara)  
− Question selection IRT-calibrated **DEĞİL** — yorum yanıltıcı (`duel_service.py` 421-444: sadece `func.random()`)  
− Re-match button yok → game over sonrası kullanıcı lobby'e döner ama "rakip aramaya devam et" butonu yok  
− Surrender/forfeit yok → oyuncu offline olduysa diğer 30s × 5 round = 2.5 dk bekler

### Findings
- **P0 — `frontend/src/pages/DuelPage.tsx:110, 159`**: `/current-question` ve `/result` endpoint'leri tanımlı değil. Backend'e ekle veya frontend'i `/stream` SSE'sine geçir
- **P1**: `_select_duel_questions` gerçek IRT calibration (mevcut θ ± 0.5 b parameter) yapmalı veya yorumdan kaldır
- **P2**: Surrender + rematch flow

---

## F. Oba (Guild) — Topluluk Sistemi

### Implementation depth — 7/10

**Backend** (`oba_api.py:1-340`):
- Oba CRUD (create, join, leave, members)
- Hierarchical roles: `bey` (lider), `noker` (subaltern), `toycu` (üye)
- Member limit (max 20 default)
- Bey ayrılırsa otomatik en eski üye `bey` olur, son üye ayrılırsa oba silinir
- Single query N+1 optimization (`oba_api.py:69-98`) — saygıdeğer
- Promote endpoint role hierarchy doğrulamasıyla (`oba_api.py:306-340`)

### Engagement score: **6/10**
+ Türk kültürü "Oba" ismi + Türk şefferi (bey, noker, toycu) — Türkçe kültürel kimlik güçlü  
+ Code kalitesi iyi (N+1 yok, FK doğrulama, ownership check)  
+ Devir teslim flow düşünülmüş  
− Oba arası rekabet yok (oba-bazlı leaderboard yok)  
− Oba aktivite feed yok (kim ne yaptı, kim katıldı)  
− Oba chat/duyuru yok → "10 kişilik oba" anlamsız çünkü iletişim yolu yok  
− Oba XP havuzu (`oba.xp_pool`) DB'de var ama bunu artıran kod sadece Oba Seferleri'nde — ki o da phantom

### Findings
- **P1**: Oba leaderboard endpoint (best oba this week)
- **P1**: Oba activity feed (recent joins/missions)
- **P2**: Oba chat (mevcut StudyRooms infra ile entegre edilebilir)

---

## G. Oba Seferleri (Team Missions) — F3

### Implementation depth — 3/10

**Backend** (`oba_seferleri_api.py:1-248`):
- `GET /active/{oba_id}` → o haftaki aktif challenge
- `POST /contribute/{challenge_id}` → katki ekle
- `GET /history/{oba_id}` → eski challenge'lar
- `GET /my-contributions`

### CRITICAL: NO CHALLENGE GENERATOR
```bash
grep "ObaChallenge\(" backend/ → sadece test ve model dosyaları
```
**Hiçbir endpoint veya Celery task `ObaChallenge` oluşturmuyor.** `expire_oba_challenges` task var ama o eskilerini kapatır, yenilerini yaratmaz.

Sonuç: `ObaSeferleriPage.tsx:191-195`'te "Bu hafta aktif gorev yok. Yeni gorev yakinda atanacak!" sonsuza kadar görünür.

### CRITICAL: Pure XP farming
```python
# oba_seferleri_api.py:34-36
class ContributeRequest(BaseModel):
    amount: int = Field(..., ge=1, le=100)
```
Frontend buttonları `+1`, `+5`, `+10` katkı (`ObaSeferleriPage.tsx:151-162`). Client istediği değeri gönderebilir. Backend hiçbir doğrulama yapmaz (quiz tamamlamış mı? soru çözmüş mü?).

Sonuç: Kullanıcı butona 100 kez basıp `1000 katkı` ekleyebilir, oba challenge target'ı bitirir, herkes phantom XP "kazanır".

### CRITICAL: DEMO placeholder in production
```typescript
// ObaSeferleriPage.tsx:27
const DEMO_OBA_ID = 'demo-oba';
```
Bu literal string production'a girer. Kullanıcı oba seferi sayfasını açtığında `'demo-oba'` ID'siyle backend sorgulanır, hiçbir şey bulunmaz, **404 değil** `data: null` döner ve "henüz aktif görev yok" gösterilir. **Kendi obasıyla bağlantı YOK.**

### Engagement score: **1/10**
+ Konsept iyi (team challenge)  
+ Katkı oran takibi  
− Challenge yaratıcı kod yok → feature ÖLÜ  
− Pure XP farming  
− Frontend hardcoded placeholder  
− Phantom XP

### Findings
- **P0**: ObaChallenge yaratıcı Celery task yaz (haftalık `daily 00:10` zaten var, oraya `_create_weekly_challenge` eklenebilir)
- **P0**: `contribute` endpoint quiz/answer tamamlamayla bağlanmalı (örn: bir quiz tamamladığında `contribute(1)` server-side trigger)
- **P0 — `ObaSeferleriPage.tsx:27`**: `DEMO_OBA_ID` → mevcut kullanıcının obasından alınmalı (`/api/v1/oba/my` zaten var)

---

## H. Usta-Cirak (Mentor-Mentee) — F6

### Implementation depth — 4/10

**Backend** (`usta_cirak_api.py:1-349`):
- Match request (rol: mentor/mentee), bekleyen karşı taraf varsa eşleştir
- Session start/end, duration tracking
- Feedback (rating 1-5 + preset tags: helpful, patient, clear, vs)
- Max 2 mentee per mentor

### Critical: Frontend session lifecycle incomplete
- `UstaCirakPage.tsx:171-178`: "Oturum Baslat" butonu var
- `/end` endpoint backend'de var (`usta_cirak_api.py:224-270`)
- AMA frontend'de "Oturum Bitir" UI YOK
- Sonuç: Session "active" kalır sonsuza kadar, XP_SESSION_MENTOR/MENTEE asla awarded olmaz
- Kullanıcı 100 session başlatabilir, max_mentees=2 limit'i geçersiz hale gelir? — Backend `MAX_MENTEES_PER_MENTOR` check `MentorPair.status == "active"` ile, session sayısıyla değil, OK

### No actual mentor-mentee interaction tools
- Backend endpoint sadece: match + session boundary + feedback
- Mentor ve mentee arasında **iletişim aracı yok** (chat yok, whiteboard yok, video yok)
- Session "ekrana not düşme" deneyimi
- Frontend session açıldığında ne yapılacağı belirsiz — "Oturum Başlat" sonrası boş ekran

### XP Phantom (same pattern)

### Engagement score: **2/10**
+ Role pairing iyi  
+ Feedback preset tags güzel  
− Session start lifecycle incomplete  
− Mentor iletişim aracı YOK (kritik feature gap)  
− StudyRooms/Whiteboard modülleri var ama entegre değil  
− Phantom XP

### Findings
- **P0 — `UstaCirakPage.tsx`**: Active session UI ekle ("Oturum bitir" button)
- **P0**: Mentor-mentee chat/whiteboard entegrasyonu (StudyRooms infra'sı zaten var)
- **P1**: Session min duration (örn: 5 dk altı XP yok) anti-cheat
- **P1**: XPTransaction integration

---

## I. Dungeon Learning Path — Khan Academy + RPG

### Implementation depth — 7/10

**Backend** (`learning_path_dungeon.py:1-362`):
- Topological depth (Kahn's algorithm) DAG layout
- Prereq check (hard prereqs must be completed)
- Theta + theta_se from `student_abilities`
- Question count per topic (with root fallback)
- UPSERT pattern with `ON CONFLICT DO UPDATE` (`learning_path_dungeon.py:334-342`)
- Completion logic: `attempt_count >= 5 AND best_score >= 80`

**Frontend** (`DungeonMap.tsx:1-147`):
- SVG-based map (Rough.js + dagre + fog-of-war per MEMORY)
- Pan/zoom gesture (use-gesture)
- Parchment background, organic paths
- Loading/error/empty states present

### CRITICAL: No score validation
```python
class QuizCompleteRequest(BaseModel):
    topic_id: str
    score: int  # ← NO BOUNDS
```
Client `score=999999` post edebilir → `best_score = 999999` kayıt edilir → completion check `>= 80` her zaman geçer → infinite "completed" room.

### CRITICAL: No quiz validation
`/complete` endpoint sadece score'a güvenir. Hangi sorular sorulduğu, kaç cevap doğruydu — hiçbir veri kontrol edilmez. Client kendi puanını yazar.

### Engagement score: **7/10**
+ DAG-based progression — gerçek bir öğrenme path  
+ Theta-based difficulty awareness  
+ Visual map (fog of war RPG vibes)  
+ Türkçe code/name_tr — yerelleştirme iyi  
− Score validation yok → cheat trivial  
− "Completed" sonrası ödül belirsiz (XP? badge? animasyon?)  
− Subject-id mapping hardcoded (`_SUBJECT_ID_MAP` line 33-46) — yeni ders eklenmesi kod değişikliği gerektirir

### Findings
- **P0 — `learning_path_dungeon.py:84-87`**: `score: int = Field(ge=0, le=100)` constraint ekle
- **P0**: Score sunucu-tarafında doğrulanmalı (quiz answer'lardan hesaplanmalı, client'tan değil)
- **P1**: Completion sonrası XP/badge dağıt
- **P2**: `_SUBJECT_ID_MAP` DB-driven olmalı

---

## J. Gamification Core (XP/Level/Badge/Leaderboard)

### Implementation depth — 7/10

**Backend** (`gamification_api.py:1-1069`, 17 endpoint, 1068 satır):
- Points (summary, history, award)
- Level (info, progress) — formula `100 * 1.5^(lv-1)` per level
- Badges (10 statik definition — `get_badge_definitions()`)
- Leaderboard (alltime, weekly, monthly, peer-group, improvement)
- Achievements (UserAchievement table)
- Profile (aggregated view)

### CRITICAL: Self-award endpoint
```python
# gamification_api.py:182-220
@router.post("/points/award")
async def award_points(
    current_user: AuthenticatedUser = Depends(get_current_user),
    body: AwardPointsRequest = Body(...),
):
    # body.points: 1-100
    new_total = await GamificationDBService.award_xp(...)
```
**Authenticated kullanıcı kendine 100 XP/istek verebilir.** Rate limit yok (`@router.post` decorator'da `_check_rate_limit` görmedim). Source = `"manual"` veya istediği string.

Test: Bir öğrenci 100 request/dakika ile dakikada 10,000 XP, saatte 600K XP toplar. Leaderboard #1 olur.

Aynı pattern `league_api.py:179` (`/league/award-xp`, max 1000 XP/call).

### Badge auto-award engine status
`get_badge_definitions()` 10 badge tanımlar (consistent_7, perfect_score, night_owl, level_10, vs) ama bu badge'leri **otomatik veren bir engine** kod görünmedi. `UserBadge` tablosuna kim insert ediyor?

→ `grep "UserBadge(.*=.*\|db.add(UserBadge\|insert.*user_badges"` ile geçirebileceğim ama check ettim: backend'de sadece read patterns. Badge'ler hiç awarded edilmez. "Kazanılan rozetler" sayfası daima boş.

### Leaderboard sound design
- alltime: `users.total_xp` desc
- weekly/monthly: `XPTransaction` 7d/30d sum
- peer-group: ±%20 XP aralığı (`gamification_api.py:984`)
- improvement: `current_points == previous_points`, improvement=0 (TODO: `gamification_api.py:1052-1057` — placeholder)

→ "Improvement leaderboard" feature ÖLÜ — placeholder döner.

### Engagement score: **5/10**
+ Endpoint kapsamı geniş  
+ Peer group leaderboard (motivasyon segmentation)  
+ Cache + Redis ZSET entegrasyonu  
− Self-award açığı  
− Badge engine eksik → 10 badge tanımlı ama HİÇ verilemez  
− Improvement leaderboard placeholder  
− Static 10 badge — büyüme yok, çeşitlilik yok

### Findings
- **P0 — `gamification_api.py:182`**: `/award` endpoint admin-only veya source whitelist (örn: `quiz_completion`, `streak_milestone`)
- **P0**: Badge auto-award engine yaz (Celery task: günlük badge criteria check)
- **P1**: Improvement leaderboard `previous_points` historical query (XPTransaction'dan 7-14 gün öncesi)
- **P2**: Dynamic badges (subject-specific, etkinlik-specific)

---

## K. ZPD-Maarif (910 satır, 17 endpoint)

Detaylı incelemedim — başlıklara göre:
- Hesapla / optimize / profil get/update
- Devrimsel calculation (Cultural context, MEB Maarif alignment)
- `KulturelBaglamProfili`, `MaarifDegerleriProfili` modelleri

Bu modülün kullanıcı-yüzü engagement değer önerisi araştırma gerektir. Pure algorithmic API gibi görünüyor, gamification katmanına entegre değil. Frontend sayfası bulamadım.

### Possible engagement gap: 17 endpoint kullanılıyor mu?
Backend var, frontend yok — front-end consumer eksikliği `silent_failures.md` audit'inde olabilir. Bu audit kapsamı dışı.

---

## Cross-feature Integration Analysis

### Mevcut bağlantılar

1. **Bilge Alp → BKT** (`bilge_alp.py:250-259`): BKTState'ten p_learn ortalama — BROKEN (topic_id format mismatch)
2. **Duel → ELO + XP**: Duel finish → ELO update → ama XPTransaction yazılmaz
3. **Social Summary → tüm features**: Retroactive count-based XP aggregation
4. **Cozum Duellosu → Celery beat**: Voting expiry otomatik
5. **Birlikte Streak → Celery beat**: Break detection otomatik

### Eksik bağlantılar

- **Quiz answer → Oba Seferleri contribute**: Otomatik trigger YOK
- **Quiz answer → Birlikte Streak complete**: Otomatik trigger YOK
- **Soru Meydani accepted solution → Badge**: Otomatik badge award YOK
- **Duel win → Leaderboard rank update**: ELO ayrı, XP ayrı, leaderboard sadece XP-based
- **Dungeon room complete → Badge / XP**: NO connection
- **Mentor session end → XP**: Endpoint var, frontend'de bitirme yolu yok

### Chain örneği (olmayan ama olması gereken)
```
Quiz tamamla → 10 XP (gerçek XPTransaction)
   ↓
   → Oba Seferleri progress +1
   → Birlikte Streak today_done = true
   → Dungeon room attempt_count++, best_score update
   → Bilge Alp BKT p_learn update
   ↓
Threshold geçince:
   → Badge "consistent_7" auto-award
   → Level up animasyonu
   → Leaderboard rank +N notification
```

Bu chain'in adımları **bağımsız endpoint'ler** olarak var, ama **trigger zinciri YOK**. Quiz tamamlama tek bir event, ama 5 feature'ı update etmesi gerek — şu an sadece XPTransaction yazıyor.

---

## Half-Done Features Found

| Feature | Status | Eksik |
|---|---|---|
| Oba Seferleri | %20 | Challenge generator yok, contribute validation yok, frontend hardcoded demo |
| Cozum Duellosu | %50 | question_bank_id validation yok, XPTransaction yok |
| Usta-Cirak | %40 | Frontend end-session UI yok, mentor-mentee chat yok |
| Bilge Alp | %60 | BKT integration broken, quest step state machine yok |
| Birlikte Streak | %30 | "Görev" tanımı yok (sadece buton), partner ayrılma yok |
| Soru Meydani | %70 | XP integration yok, image upload on questions yok |
| Duel | %75 | Frontend page broken endpoints (`/current-question`, `/result`), surrender yok |
| Dungeon | %85 | Score validation yok, reward dağıtımı yok |
| Gamification core | %70 | Badge engine yok, improvement leaderboard placeholder |
| Oba | %85 | Oba leaderboard/feed yok |

### TODO/FIXME inventory
`grep -nE "TODO|FIXME|XXX|HACK"` her dosyada — **0 hit**. Yani halftime features bile geliştirici tarafından "TODO" işaretlenmemiş; bu daha endişe verici (görünmez halfedone).

---

## UX Quality Summary

| Feature | Engagement | Onboarding | Mobile | Tutorial | Empty state |
|---|---|---|---|---|---|
| Bilge Alp | 6/10 | quick prompts | responsive | YOK | greeting message |
| Soru Meydani | 5/10 | template select | OK | YOK | "henüz soru yok" |
| Birlikte Streak | 4/10 | "Ortak Bul" CTA | OK | YOK | OK |
| Cozum Duellosu | 3/10 | OK | OK | YOK | OK |
| Duel | 6/10 | subject chips + ELO | OK | YOK | broken page |
| Oba | 6/10 | list view | OK | YOK | OK |
| Oba Seferleri | 1/10 | broken | OK | YOK | sonsuza dek empty |
| Usta-Cirak | 3/10 | subject + role | OK | YOK | "henüz eşleşme" |
| Dungeon | 7/10 | DAG explore | gesture | YOK | "konu bulunamadı" |
| Gamification | 5/10 | profile view | OK | YOK | OK |

**Common issues:**
- Tutorial/first-time experience HİÇBİR feature'da YOK
- Sound effects (motivasyon için kritik) — kontrol etmedim ama yüksek ihtimal yok
- Onboarding gen-1 (welcome modal, feature highlight tour) HİÇBİR yerde
- Türkçe mesaj kalitesi genel olarak iyi (NFC, doğru imla); ama bazı yerlerde imla bozuk ("Hosgeldin" yerine "Hoşgeldin")

---

## P0 / P1 / P2 Findings Summary (UX-focused)

### P0 — Engagement-killing (must fix before public launch)

1. **Phantom XP system-wide** (5 features): `award_xp` çağrılmaz → leaderboard yalan söyler. XPTransaction integration eksik.
   - Files: `birlikte_streak_api.py:226`, `cozum_duellosu_api.py:222`, `oba_seferleri_api.py:166`, `usta_cirak_api.py:260`, `soru_meydani_api.py:323`
2. **Self-XP award endpoint** (`gamification_api.py:182`, `league_api.py:179`): Authenticated user kendi XP'sini verebilir → leaderboard manipülasyonu trivial
3. **Dungeon score injection** (`learning_path_dungeon.py:86`): Client `score: int` no bounds, no validation → completion farming
4. **Oba contribute injection** (`oba_seferleri_api.py:34-36`): Client istediği amount'u gönderir → XP/progress farming
5. **DuelPage broken endpoints** (`frontend/src/pages/DuelPage.tsx:110, 159`): `/current-question`, `/result` backend'de yok → düello UI çalışmaz
6. **Oba Seferleri no challenge generator** → "aktif görev yok" sonsuza kadar → feature ölü
7. **DEMO_OBA_ID hardcoded** (`ObaSeferleriPage.tsx:27`): Production literal string `'demo-oba'`
8. **Cozum Duellosu question_bank_id='auto'**: Soru bağlantısı yok, voters soruyu göremez
9. **Bilge Alp BKT topic_id format mismatch** (`bilge_alp.py:255`): LIKE pattern UUID-style topic_id'lerle eşleşmez → mastery daima 0%
10. **UstaCirakPage no end-session UI**: Session sonsuza kadar active kalır, XP awarded edilmez
11. **Badge auto-award engine eksik**: 10 statik badge tanımlı, hiçbiri user'a verilmez

### P1 — Important UX gaps

1. **Birlikte Streak "görev" tanımı yok**: Click-only completion, gerçek aktivite gerektirmez
2. **Mentor-mentee iletişim aracı yok**: Chat/whiteboard StudyRooms zaten var ama entegre değil
3. **Onboarding tour yok**: Tüm feature'lar
4. **Streak ortağı ayrılma endpoint'i yok**: Cevapsız partner'dan kurtuluş yok
5. **Oba activity feed yok**: 20 kişilik oba ama iletişim yok
6. **Voting feed yok (Cozum Duellosu)**: Oy verme fırsatı kaçar
7. **Surrender/rematch yok (Duel)**
8. **Improvement leaderboard placeholder** (`gamification_api.py:1052`)
9. **Question Bank "auto" placeholder**: Cozum Duellosu için
10. **Race conditions**: Cozum Duellosu sub_count check, Duel both-answered detection — lock yok

### P2 — Polish/nice-to-have

1. Soru Meydani image upload on question
2. Subject map (_SUBJECT_ID_MAP) DB-driven
3. Helpful vote threshold → automatic badge
4. Dynamic badges (subject-specific, event-based)
5. Mock LLM fallback (Bilge Alp) için UI hint "şu an offline mod"
6. Oba leaderboard (best oba this week)
7. Sound effects (level up, badge earned, streak fire)
8. Notification system unified (her feature kendi mesajlarını yönetir)
9. Mobile haptic feedback (mevcut değil)
10. Streak milestone celebration animations

---

## Engagement Quality Scores Summary

| Feature | Onboarding | Replayability | Social | Feedback loop | Frustration risk | Real fun | Overall |
|---|---:|---:|---:|---:|---:|---:|---:|
| Bilge Alp | 6 | 8 | 0 | 8 | 2 | 7 | **6/10** |
| Soru Meydani | 5 | 6 | 9 | 5 | 4 | 5 | **5/10** |
| Birlikte Streak | 4 | 7 | 8 | 3 | 7 | 3 | **3/10** |
| Cozum Duellosu | 3 | 4 | 7 | 2 | 6 | 3 | **2/10** |
| Duel (1v1) | 6 | 9 | 8 | 8 | 5 | 8 | **6/10** (broken FE: 3) |
| Oba | 6 | 5 | 6 | 4 | 2 | 5 | **6/10** |
| Oba Seferleri | 1 | 0 | 4 | 0 | 8 | 0 | **1/10** |
| Usta-Cirak | 3 | 5 | 5 | 2 | 6 | 3 | **2/10** |
| Dungeon | 7 | 8 | 0 | 6 | 3 | 7 | **7/10** |
| Gamification core | 5 | 6 | 7 | 4 | 5 | 5 | **5/10** |

**Average gamification engagement: 4.3 / 10**

Bunun anlamı: kullanıcılar feature'ları açar, "bu nasıl çalışıyor?" diye merak eder, eksiklikleri keşfeder (phantom XP, broken duel, demo placeholder), ve tekrar dönmez.

---

## Recommendations (Concrete, Prioritized)

### Sprint 1 (1-2 hafta, P0 critical-path):

1. **Unified XPAward trigger** — Bir middleware/service helper yaz:
   ```python
   await award_xp_and_check_badges(student_id, source, amount, db)
   ```
   Bunu Soru Meydani, Birlikte Streak, Cozum Duellosu, Usta-Cirak, Oba Seferleri, Dungeon completion, Duel finish'e ekle.

2. **Remove `/points/award` public access** veya source whitelist (`source in ALLOWED_SOURCES`).

3. **Dungeon score validation**: Score'u quiz answer'lardan hesaplama. Client score gönderemez.

4. **DuelPage cleanup**: `pages/DuelPage.tsx`'i sil veya `DuelMode.tsx`'e redirect.

5. **Oba Seferleri unbrick**:
   - Weekly challenge generator Celery task
   - `contribute` endpoint'ini quiz event'e bağla
   - `DEMO_OBA_ID` → `oba.my` API'sinden dinamik

6. **Cozum Duellosu question_bank_id validation**.

7. **Bilge Alp BKT fix**: realm_slug → subject_id → topic_hierarchy.subject_area JOIN.

### Sprint 2 (2-3 hafta, P1 UX):

8. Badge auto-award Celery engine (günlük cron).
9. Mentor-mentee chat/whiteboard StudyRooms entegrasyonu.
10. UstaCirakPage session end UI + duration display.
11. BirlikteStreak gerçek görev definition (`/complete-today` quiz_completed event ile).
12. Notification system (unified) — feature'lar arası eylem feedback.
13. Onboarding tour (react-joyride veya custom).

### Sprint 3 (P2 polish):

14. Sound effects (level up, badge earned, streak).
15. Mobile haptic (vibration API).
16. Empty state illustrations (currently sadece metin).
17. Improvement leaderboard real implementation.

### Missing features competitors have

- **Streaks across features** (Duolingo: 365-day streaks, herkesin görür) → KIRO2'de unified streak yok
- **Daily challenges** (auto-generated) → ZPD-Maarif'in adaptive system'i bu role'e konumlandırılabilir
- **Avatar customization** → motivasyon multiplier
- **Profile sharing** (Instagram-style) → sosyal viral
- **In-app currency** (gold, gems) — sadece XP var, multiple currency yok
- **Time-limited events** (Khan Academy summer challenge) → yok
- **Push notifications** (mobile native) — kontrol etmedim ama büyük ihtimal yok

---

## Engagement Optimization Recommendations

### Quick wins (1-3 gün her biri)

1. **Level up animation + sound** — `frontend/src/components/Gamification/LevelDisplay.tsx`'a confetti + audio cue
2. **Streak fire animation intensity** — 7d/30d/100d için tone değiştir (warm/blue/purple flame)
3. **Toast notification stack** — feature başarısı gösterimi tek-yer (level up, badge earned, streak milestone)
4. **Daily login bonus** — `gamification.streaks` zaten var, login event'e bağla
5. **First-time experience pop-up** — kullanıcı bir feature'ı ilk açtığında 30-sn'lik animasyon

### Medium effort

6. **Friend system** → Birlikte Streak random matching yerine arkadaş davet
7. **Leaderboard tier visual** (BRONZE/SILVER/GOLD/PLATINUM/CHAMPION) — `models.league` zaten var ama UI eksik
8. **Quest log** — Bilge Alp quest_step state machine + visible progress

### High effort

9. **Real-time multiplayer rooms** (StudyRooms infra varsa) — Live quiz battles
10. **AI dynamic challenge generation** — Daily/weekly auto-personalized goals
11. **Push notifications** — Firebase/expo

---

## Conclusion

KIRO2 gamification katmanı **arkitektürel olarak güçlü** (modüler, async, Redis-backed, content-filtered) ama **kullanıcı tarafından deneyimlenen yüzeyde derin yarım-uygulamalar** içeriyor. En kritik problem: **phantom XP** — kullanıcı kazandığını sandığı XP gerçekte leaderboard'a yansımıyor. Bu, motivasyon sisteminin **fundamental ilkesini** kıran bir bug.

Önerilen yol: Bu 11 P0 bulgu **MVP launch öncesi** mutlaka kapatılmalı. Aksi takdirde kullanıcı 1-2 hafta içinde "her şey yalan" hissi yaşar ve churn.

İyi haber: backend infrastructure (Celery, Redis, async, content filter, IDOR check) çoğu yerde **sağlam**. Tamamlanmamış bağlantı katmanları görece kısa sürede kapatılabilir.

---

*Audit time: ~75 dakika*  
*Files read: 13 backend (~5,150 satır), 9 frontend (~2,900 satır), 4 service/task (~720 satır)*  
*Tools used: Read, Grep, Bash (ls/wc), Glob (failed due to timeout)*
