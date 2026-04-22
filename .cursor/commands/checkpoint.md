# Checkpoint — Progressive Context Save

Commit sonrası veya önemli milestone'da SESSION_STATE.md ve gerekirse
MEMORY.md günceller. `/handoff` session kapatırken, `/checkpoint` çalışma
sırasında ilerleme kaydeder.

## `/handoff` vs `/checkpoint` Farkı

| | `/handoff` | `/checkpoint` |
|---|---|---|
| Ne zaman | Session kapatırken | Commit sonrası, mid-session |
| Süre | 50 satır limit | Max 50 satır (SESSION_STATE'e) |
| MEMORY.md | Tek satır session özeti | Sadece milestone'da |
| Yeni session | Açılmaz (imkansız) | Devam eder |
| Git commit | "chore: session handoff" | Zaten commit var, checkpoint takip |

## Ne Zaman Kullanılmalı

- **Her önemli commit sonrası** (ZORUNLU pattern)
- Büyük değişiklik tamamlandığında
- `/compact` komutundan önce (context özetlenecek)
- Session ortasında context kaybı riski varsa
- Milestone: feature tamamlandı, önemli bug fix, mimari karar

## Protokol

### 1. Git Durumu Oku

```bash
git log --oneline -5
git status --short
git diff --cached --stat
```

### 2. Mevcut State Oku

- `.claude/sessions/latest.md` (SESSION_STATE) oku
- Eski veya boş ise sıfırdan oluştur

### 3. SESSION_STATE Güncelle

Max 50 satır, atomic write:

```markdown
# Session State (checkpoint: 2026-04-20 14:30)

## Quick Resume
- **Branch:** feature/exam-submit
- **Last commit:** a1b2c3d feat(api): add exam submit endpoint
- **Uncommitted:** 0 files
- **Production:** 77,336 questions, 916 passing tests

## Bu Session'da Yapılanlar
- backend/app/api/v1/exams.py:180-220 — submit endpoint eklendi (a1b2c3d)
- tests/api/test_exam_submit.py — 12 test case (a1b2c3d)
- alembic/versions/005_add_exam_submissions.py — migration (b4e5f6g)
- backend/app/models/exam_submission.py — yeni model

## Bekleyen İşler
1. Frontend ExamPlayer.tsx'te submit handler
2. Rate limit middleware (5 submit/dk)
3. Email notification (opsiyonel — sprint sonra)

## Test Durumu
- Backend: 928/928 passed (+12 yeni)
- Frontend: tsc 0 error
- Migration round-trip: PASS

## Son Dokunulan Dosyalar
- backend/app/api/v1/exams.py
- tests/api/test_exam_submit.py
- alembic/versions/005_add_exam_submissions.py
```

### 4. MEMORY.md Session Index (Milestone'larda)

Sadece önemli milestone'larda ekle:
- Yeni feature tamamlandı
- Büyük bug fix
- Mimari değişiklik
- Algoritma revizyonu

Format:
```
- Session 149: Exam submit endpoint eklendi + migration 005 (commit a1b2c3d)
```

### 5. Onay Mesajı

```
✅ Checkpoint saved: a1b2c3d
- SESSION_STATE.md güncellendi (45 satır)
- 4 yapılan iş, 3 bekleyen iş
- Test: 928/928 passing
```

## Cursor 3.x ile Entegrasyon

### Plan Mode + Checkpoint

Plan'ı uyguladıktan sonra:
1. Commit at (`/commit`)
2. `/checkpoint` — ilerleme kaydet
3. Plan dosyasını (`.cursor/plans/`) güncelle — tamamlanan adımları işaretle
4. Yarım kalan adımları `Bekleyen İşler`'e taşı

### @Past Chats + Checkpoint

Sonraki session'da:
```
@Past Chats:exam submit endpoint checkpoint
```
Ve SESSION_STATE.md'ye referans:
```
@.claude/sessions/latest.md
```
İkisini birleştir → tam context restore.

## Kurallar

- **SESSION_STATE.md 50 satırı GEÇMEZ** — özet olmalı, transkript değil
- **Atomic write**: geçici dosyaya yaz, sonra rename
- **MEMORY.md'ye her checkpoint'te EKLEME** — sadece milestone'larda
- **Checkpoint session-save hook'unu TETİKLEMEZ** (çift yazma önlenir)
- **Commit hash'i referansla** — "backend/app/X.py (a1b2c3)" formatı

## Anti-pattern'lar

- Checkpoint **commit öncesi** — henüz değişiklik tamam değil, stale bilgi
- Tüm değişiklikleri kopyalamak — SESSION_STATE özet olmalı
- Her saat başı checkpoint — noise, commit bazlı yeter
- Branch değiştirdikten sonra checkpoint'i unutma — yeni state ile başla

## Detaylı Referans

- `.claude/skills/checkpoint/SKILL.md` — canonical detay
- `.claude/skills/handoff/SKILL.md` — session kapatma alternatifi
- `.cursor/commands/handoff.md` — session kapatma komutu
- `.cursor/commands/compact.md` — context özetleme (checkpoint öncesi)
