# KIRO2 Sosyal Ortam Implementation Plan

> Tarih: 2026-03-24
> Durum: PLAN TAMAMLANDI — Implementasyon bekliyor
> Toplam: 7 feature, 6 faz, ~70-90 dev-day

---

## Dependency Graph

```
                    +----------------------------+
                    |  F0: Safety Infrastructure |
                    |  (7-Layer Moderation)      |
                    +-------------+--------------+
                                  |
           +----------------------+----------------------+
           |                      |                      |
           v                      v                      v
+------------------+  +------------------+  +------------------+
| F1: Soru Meydani |  | F2: Cozum        |  | F4: Pomodoro     |
| (Q&A Forum)      |  | Duellosu         |  | Odalari          |
+--------+---------+  +--------+---------+  +--------+---------+
         |                      |                      |
         v                      v                      v
+------------------+  +------------------+  +------------------+
| F6: Usta-Cirak   |  | F5: Birlikte     |  | F3: Oba Seferleri|
| (Mentoring)      |  | Streak           |  | (Team Challenges)|
+------------------+  +------------------+  +------------------+
```

---

## Phase Plan (6 Faz, 2 Haftalik Sprintler)

| Faz | Hafta | Feature | Effort | Mevcut Altyapi |
|-----|-------|---------|--------|----------------|
| 1 | 1-2 | F0: Safety Infrastructure | XL | turkish_content_filter.py (video), student_review.py |
| 2 | 3-4 | F1: Soru Meydani (Q&A Forum) | L | Yok (yeni) |
| 3 | 5-6 | F2: Cozum Duellosu (Enhanced) | M | duel.py, duel_api.py, DuelPage.tsx (%80 mevcut) |
| 4 | 7-8 | F4: Pomodoro + F5: Birlikte Streak | XL+S | study_room.py (12 tablo), Streak model |
| 5 | 9-10 | F3: Oba Seferleri | L | oba_api.py, Oba/ObaUye modelleri |
| 6 | 11-12 | F6: Usta-Cirak (Mentoring) | XL | StudentAbility, LeagueMembership |

---

## MVP Cut (4 Hafta)

En hizli deger ureten 3 feature:
1. **F0 (minimal)**: 3-layer filter (wordlist + report + manual review)
2. **F2 (enhanced duel)**: Theta matching + mevcut duel altyapisi (%80 hazir)
3. **F5 (group streak)**: Streak modelleri mevcut, minimal yeni kod

---

## F0: Safety Infrastructure (FOUNDATION)

### 7-Layer Content Moderation Pipeline

| Layer | Kontrol | Aksiyon |
|-------|---------|---------|
| 1 | Length check (bos, >2000 char) | BLOCK |
| 2 | Turkish blacklist (kufur/hakaret) | BLOCK |
| 3 | Anti-flirt patterns (sevgilim, numarani ver, instagram) | BLOCK |
| 4 | Personal info regex (telefon, email, TC kimlik, adres) | BLOCK + sanitize |
| 5 | Emoji abuse (>10 arka arkaya, uygunsuz emoji) | FLAG |
| 6 | Spam (tekrar, ALL CAPS, coklu URL) | BLOCK |
| 7 | AI classification (Qwen3-8B, 500ms timeout) | FLAG (optional) |

### DB Tablolari (5 yeni)

1. `content_reports` — Icerik raporlama
2. `moderation_actions` — Moderator aksiyonlari (uyari/mute/ban)
3. `blocked_users` — Kullanici engelleme (UniqueConstraint pair)
4. `parent_social_settings` — Veli kontrolleri (sosyal acik/kapali, saat kisitlamasi)
5. `message_audit_log` — Mesaj denetim logu (hash, flag, pipeline_ms)

### Backend Dosyalari

| Dosya | Icerik |
|-------|--------|
| `backend/models/social_safety.py` | 5 SQLAlchemy model + 7 enum |
| `backend/services/social_content_filter.py` | 7-layer pipeline, FilterResult dataclass |
| `backend/schemas/social_safety_schemas.py` | Pydantic request/response modelleri |
| `backend/api/moderation_api.py` | 12 endpoint (report, action, block, filter-test) |
| `backend/api/parent_social_api.py` | 6 endpoint (settings CRUD, activity, emergency disable) |
| `backend/migrations/add_social_safety_tables.sql` | DDL + indexes |

### Turkish NLP Patterns

**Flirt detection regex kategorileri:**
- `endearments`: sevgilim, askim, canim, bebegim, tatlim...
- `solicitation`: numarani ver, bulusak, tanisalim, cikalim...
- `compliments_excessive`: cok guzelsin, cok yakisiklisin...
- `social_media_request`: instagram, snapchat, whatsapp, telegram, dm yaz, ozelden gel...

**Personal info regex:**
- Turk telefon: `05XX XXX XX XX` (cesitli separator'lar)
- Email: standart regex
- TC Kimlik: 11 haneli sayi (non-zero baslayan)
- Adres: mahalle, sokak, cadde, apartman anahtar kelimeleri

### Test: 40+ test (3 dosya)

---

## F1: Soru Meydani (Q&A Forum)

### DB Tablolari (4 yeni)

1. `shared_questions` — Paylasilan sorular (question_bank FK, context_note, status)
2. `shared_solutions` — Cozumler (solution_text, latex, vote_score, is_best)
3. `solution_votes` — Oylar (merit-weighted, UniqueConstraint voter+solution)
4. `forum_reports` — Forum raporlama

### API: `/api/v1/forum` (10 endpoint)

| Method | Path | Ozet |
|--------|------|------|
| POST | `/questions` | Soru paylas (question_bank'tan) |
| GET | `/questions` | Paylasilan sorulari listele (subject/exam filtre) |
| GET | `/questions/{id}` | Detay + cozumler |
| POST | `/questions/{id}/solutions` | Cozum yaz |
| POST | `/solutions/{id}/vote` | Oy ver (up/down) |
| POST | `/questions/{id}/best` | En iyi cozumu sec (XP odul) |
| POST | `/report` | Icerik raporla |
| GET | `/my/questions` | Benim sorularim |
| GET | `/my/solutions` | Benim cozumlerim |
| GET | `/stats` | Forum istatistikleri |

### XP Odul Yapisi

| Aksiyon | XP | Source |
|---------|---:|--------|
| Soru paylas | +5 | forum_share |
| Cozum yaz | +10 | forum_solution |
| En iyi cozum secildi | +50 | forum_best |
| Upvote alindi | +3 | forum_upvote |
| Gunun ilk cozumu | +5 bonus | forum_daily_first |

### Anti-Abuse

- Max 5 soru/gun, 20 cozum/gun
- Kendi sorusuna cevap veremez
- Kendi cozumune oy veremez
- Merit-weighted oylar (iyi cozumculerin oyu 1.5x agirlikta)
- 3+ rapor → otomatik flag
- Yeni hesaplar (<7 gun) kisitli

### Frontend: 11 component + 1 page + 1 hook

### Test: 20+ test

---

## F2: Cozum Duellosu (Solution Duel)

### DB Tablolari (3 yeni)

1. `solution_duels` — Duello oturumu (theta snapshot, status state machine)
2. `duel_submissions` — Cevap + cozum yaklasimi (time_taken_ms)
3. `solution_duel_stats` — Istatistik cache (wins, losses, streak)

### State Machine

```
matching -> solving -> reviewing -> completed
                                -> cancelled
```

### Theta-Based Matching

1. Ogrencinin theta'sini `student_abilities`'den al
2. Redis queue: `sduel:queue:{subject}:{theta_bracket}` (0.5 aralikla)
3. Bracket expansion: exact -> +/-0.5 -> +/-1.0 -> anyone (90s timeout)
4. Theta fark guardi: |t1-t2| <= 1.5
5. Soru secimi: avg(theta) +/- 0.5 zorlukta, is_active=True

### Winner Logic

- Ikisi de dogru → hizli olan kazanir
- Biri dogru → dogru olan kazanir
- Ikisi de yanlis → berabere

### XP: Max 70/duel (katilim 10 + kazanma 30 + dogru 15 + review 5 + kalite 10)

### API: `/api/v1/solution-duel` (10 endpoint)

### Frontend: 11 component + 1 page + 1 hook

### Test: 21+ test

---

## F4: Pomodoro Odalari (Co-Study Rooms)

### DB Tablolari (3 yeni)

1. `pomodoro_rooms` — Oda (subject, phase, max 5 kisi)
2. `pomodoro_room_members` — Uyeler (focus_score)
3. `pomodoro_session_logs` — Oturum logu (pomodoros, xp)

### Redis Key Design

```
pomodoro:room:{room_id}:state    -> JSON {phase, timer_end_at}  TTL:3h
pomodoro:room:{room_id}:members  -> SET of student_ids          TTL:3h
pomodoro:student:{id}:room       -> room_id                     TTL:3h
pomodoro:focus:{id}              -> "1"                         TTL:30min
pomodoro:events:{room_id}        -> PUB/SUB channel
```

### SSE Events

- `connected`, `member_joined`, `member_left`
- `pomodoro_started`, `break_started`, `pomodoro_completed`
- `room_dissolved`, heartbeat (30s)

### XP: 15/pomodoro, 1.5x focus bonus (>0.9), +25 full set (4 pomodoro)

### API: `/api/v1/pomodoro` (8 endpoint)

### Frontend: 6 component + 1 page + 1 hook

### Test: 23+ test

---

## F5: Birlikte Streak (Group Streaks)

### DB Tablolari (4 yeni)

1. `streak_groups` — Grup (target_exam, current/best streak, grace_period)
2. `streak_group_members` — Uyeler (max 4, leader/member)
3. `streak_daily_logs` — Gunluk calisma logu (studied, minutes, sources)
4. `streak_group_badges` — Milestone rozetleri (7/30/100 gun)

### Grace Period

- Bir uye calismazsa → 24 saat grace period
- Grace suresi dolarsa ve hala calismamissa → streak sifirlanir
- HICBIR uye calismazsa → aninda sifirlanir (grace yok)

### Milestone Odulleri

| Gun | Rozet | XP/kisi |
|-----|-------|---------|
| 7 | Hafta Savascisi | 100 |
| 30 | Ay Yildizi | 500 |
| 100 | Efsane Takim | 2000 |

### API: `/api/v1/streak-group` (7 endpoint)

### Celery: Gunluk 02:00 (TR) streak islemesi

### Frontend: 5 component + 1 page + 1 hook

### Test: 33+ test

---

## F3: Oba Seferleri (Team Challenges)

### DB Tablolari (3 yeni)

1. `team_challenges` — Haftalik gorev (type, target, start/end date)
2. `team_challenge_progress` — Oba ilerlemesi (current_value, completed)
3. `team_challenge_contributions` — Bireysel katki

### Challenge Tipleri

- `total_questions` — Toplam soru coz
- `avg_accuracy` — Ortalama dogruluk
- `streak_days` — Streak gunleri
- `subject_mastery` — Konu hakimiyeti

### Odul: Top 1: 500 XP pool + 100/uye, Top 2: 300+60, Top 3: 150+30

### Integration: `learning_event_service.py`'ye hook — quiz/exam tamamlandiginda otomatik contribution

### API: `/api/v1/oba/seferleri` (6 endpoint)

### Celery: Haftalik Pazartesi 00:00 (TR) rotation + 15dk progress sync

### Test: 19+ test

---

## F6: Usta-Cirak (Mentor System)

### DB Tablolari (4 yeni)

1. `mentor_pairs` — Eslesme (mentor_id, mentee_id, subject, theta snapshot)
2. `mentor_messages` — Sablon mesajlar (template_id + params)
3. `mentor_ratings` — Degerlendirme (1-5, anonim)
4. `message_templates` — 8 onceden tanimli sablon

### Matching Algorithm

1. Mentee theta'si al (StudentAbility)
2. Mentor adaylari: theta_gap 1.0-3.0, <3 aktif mentee, son 14 gunde aktif
3. Skorlama: theta_gap_normalized(0.4) + availability(0.3) + recency(0.3)
4. Top 5 aday sun veya otomatik eslestir

### Sablon Mesajlar (FREE TEXT YOK)

| Kategori | Sablon |
|----------|--------|
| suggestion | "Bu konuyu tekrar et: {konu}" |
| focus | "Su soru tipine odaklan: {tip}" |
| encouragement | "Harika ilerleme! Devam et!" |
| video | "Bu konuda video izlemeni oneriyorum" |
| suggestion | "{konu} konusunda 10 soru coz" |
| encouragement | "Bu haftaki gelisimin cok iyi!" |
| focus | "Yanlis yaptigin sorulari tekrar incele" |
| suggestion | "Gunluk hedefini {hedef} soru olarak belirle" |

### Anti-Abuse

- Max 3 mentee/mentor
- 7 gun inaktiflik → otomatik dissolve (Celery)
- 7 gun cooldown (ayni pair yeniden eslenemez)
- Param validation (max 100 char, no HTML)
- 20 mesaj/gun rate limit

### API: `/api/v1/mentor` (10 endpoint)

### Test: 29+ test

---

## Risk Matrix

| Risk | Olasilik | Etki | Onlem |
|------|----------|------|-------|
| Uygunsuz icerik filtreyi gecer | HIGH | CRITICAL | 7-layer + report + manual review |
| Flort/dating davranisi | HIGH | HIGH | DM yok, sablon mesaj, telefon/social regex |
| Siber zorbalik | MEDIUM | CRITICAL | 3-strike auto-ban, veli bildirimi |
| SSE olceklenme | MEDIUM | HIGH | Redis pub/sub, connection limit |
| Feature adoption basarisizligi | MEDIUM | MEDIUM | Feature flag, A/B test, 2 hafta burn-in |

---

## Feature Flags

```
SOCIAL_CONTENT_FILTER      # F0
SOCIAL_USER_BLOCKING       # F0
SOCIAL_PARENT_CONTROLS     # F0
SOCIAL_FORUM               # F1
SOCIAL_DUEL_THETA_MATCH    # F2
SOCIAL_DUEL_SOLUTION       # F2
SOCIAL_POMODORO_ROOMS      # F4
SOCIAL_GROUP_STREAK        # F5
SOCIAL_OBA_CHALLENGES      # F3
SOCIAL_MENTORING           # F6
```

### Rollout: Internal (0%) → Alpha (5%) → Beta (25%) → GA (100%)

---

## Legal (KVKK/GDPR)

- <18 kullanicilar: Veli onayi ZORUNLU (sosyal feature acilmadan)
- Icerik izleme: Acik riza popup (ilk kullanimda)
- Silme hakki: "Tum sosyal verimi sil" endpoint
- Kisisel bilgi filtreleme: Telefon, email, TC kimlik, adres otomatik engel
- Veri saklama: Deaktif edilen kullanicinin sosyal verisi 30 gun icinde silinir

---

## Toplam Dosya Sayisi

| Katman | Yeni Dosya | Aciklama |
|--------|-----------|----------|
| Models | 7 | social_safety, forum, solution_duel, pomodoro_room, streak_group, team_challenge, mentor |
| Services | 6 | social_content_filter, forum_service, solution_duel_service, pomodoro_service, streak_group_service, mentor_service |
| API | 7 | moderation, parent_social, forum, solution_duel, pomodoro, streak_group, mentor |
| Schemas | 4 | social_safety, pomodoro, streak_group, (inline for others) |
| Celery Tasks | 3 | duel_tasks, streak_daily_task, mentor_tasks, team_challenge_tasks |
| Migrations | 6 | Her feature icin 1 SQL |
| Frontend Pages | 6 | ForumPage, SolutionDuelPage, PomodoroRoomPage, StreakGroupPage, ObaSeferleriPage, MentorPage |
| Frontend Hooks | 6 | useForum, useSolutionDuel, usePomodoroRoom, useStreakGroup, useObaSeferleri, useMentor |
| Frontend Components | ~50 | Her feature icin 6-11 component |
| Tests | 7 | Her feature icin 1 test dosyasi (toplam ~185+ test) |
| **TOPLAM** | **~100 dosya** | |

---

## ASLA YAPILMAYACAKLAR (Red List)

- DM (ozel mesaj)
- Profil fotografi
- Serbest metin chat
- Kullanici arama/kesfet
- "Online" durumu (sadece oda icinde gorunur)
- Takip sistemi
- Begeni butonu (sadece cozum oylama)
- Cinsiyet gosterimi
- Konum paylasimi
- Kullanici profil ziyareti

---

*Bu plan 5 paralel agent tarafindan olusturuldu (24 Mart 2026)*
*Implementasyon icin kullanici onayi bekleniyor*
