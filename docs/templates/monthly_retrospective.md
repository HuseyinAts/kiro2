# KIRO2 Aylık Retrospektif — {YYYY-MM}

**Periyot:** {YYYY-MM-01} → {YYYY-MM-31}
**Yazan:** Hüseyin
**Status:** Draft / Final
**İlişkili:** [Faz 7.3 retrospective task]

## 1. Sayısal Özet

### 1.1 Gold pool

| Metrik | Period başı | Period sonu | Δ |
|---|---|---|---|
| auto_judged_high (Sapphire+pre) | _ | _ | _ |
| bronze_clean | _ | _ | _ |
| rejected | _ | _ | _ |
| v_safe_for_beta | _ | _ | _ |

Komut:
```bash
PGPASSWORD=1470 psql -p 5434 -d kiro2 -c "\
  SELECT quality_review_status, COUNT(*) \
  FROM question_bank WHERE is_active=TRUE \
  GROUP BY quality_review_status ORDER BY COUNT(*) DESC"
```

### 1.2 Curator throughput

```bash
python backend/scripts/quality/curator_velocity_check.py --since 30
```

| Metrik | Değer | Hedef | Status |
|---|---|---|---|
| Daily avg verdict | _ | 30-50 | _ |
| Velocity median | _ | ≤ 90s | _ |
| Velocity p90 | _ | ≤ 180s | _ |
| Outlier (Z>2) sayısı | _ | < %5 toplam | _ |

### 1.3 Beta öğrenci aktivite

- Toplam aktif öğrenci: _
- Toplam soru çözüldü: _
- Ortalama günlük çekiş: _ soru/öğrenci
- Hata flag sayısı: _ (komut: `psql -c "SELECT COUNT(*) FROM student_question_flags WHERE created_at > NOW() - INTERVAL '30 days'"`)

### 1.4 Engineering metrics

- Commit sayısı: `git log --since='YYYY-MM-01' --oneline | wc -l`
- Test PASS oranı: pytest --cov çıktısı
- Coverage % (statement): _
- Lint/typecheck violation: _
- CI gate fail sayısı: _

## 2. Bu Ay Yapılanlar

### Tamamlanan Faz/Task
- (Major work items, max 10 satır)

### Major commits
- `<hash>` <subject>
- ...

### Tespit edilen production bug
- (örn: SQLAlchemy func.case bug 21 May)
- Yakalanma yöntemi: smoke test / CI gate / öğrenci flag

## 3. Bu Ay Öğrenilenler

- (Pattern, anti-pattern, surprise) — 3-5 madde
- `.claude/rules/*.md`'e taşınacak olanları işaretle

## 4. Tekrarlayan Sorunlar (Pattern Detection)

İki+ session'da tekrarlayan friction:

| Sorun | Sıklık | Root cause | Aksiyon |
|---|---|---|---|
| _ | _ | _ | _ |

## 5. Sonraki Ay Hedefleri

- (3-5 P0/P1 hedef)
- Buffer refill ihtiyacı (Faz 7.6) varsa not düş

## 6. Risk Register

| Risk | Olasılık | Etki | Mitigasyon |
|---|---|---|---|
| Curator burnout | _ | _ | _ |
| Gold pool tükenmesi | _ | _ | _ |
| Quality drift | _ | _ | _ |

## 7. Eklemeler / Notlar

(Stakeholder feedback, surprise events, vb.)

---

**Template version:** 1.0 (Session 178 init)
**Üretim komutları arşivi:** `backend/scripts/quality/curator_velocity_check.py`,
`drift_dashboard.py`, `ma_tracker.py` (Faz 2.3, 2.4)
