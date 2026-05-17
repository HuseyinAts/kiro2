# Faz 2.6 — İlk 4 Hafta Baseline Scoring

**Plan v1 referans:** Faz 2.6 (Audit Harness — baseline)
**Başlangıç:** 17 May 2026 (W20)
**Bitiş:** 14 Jun 2026 (W23)
**Trigger:** Faz 5+6 alternative pool composition değişti, yeni baseline kurulması zorunlu

---

## Methodology

**Sample seçimi (post-Faz-5+6 pool):**

| Pool | Source | Size (17 May) | Amaç |
|---|---|---|---|
| **gold** | `v_safe_for_beta` view | 22,325 | Student'ın gördüğü Gold pool — baseline kalite |
| **reject** | `quality_review_status='rejected'` | 21,329 | False-negative kontrol (filter "iyi soruyu yanlışlıkla reddetti mi?") |
| **manual_queue** | `bronze_clean` (Edebiyat Sokagi) | 197 | Solution-leak manual review queue |

Her hafta:
- **gold** pool'dan 30 random sample (deterministic seed=ISO_year+week+gold)
- **reject** pool'dan 30 random sample (W21+)
- Hüseyin manuel scoring (1-2 saat × 2 pool = 2-4 saat / hafta)

**Komut:**
```bash
# Pazar 09:00 (Task Scheduler tetikler veya manuel)
python -m backend.scripts.quality.weekly_audit --pool gold
python -m backend.scripts.quality.weekly_audit --pool reject
```

---

## 4-Hafta Schedule

| Hafta | Tarih | Gold | Reject | Manual Queue | Cumulative analysis |
|---|---|---|---|---|---|
| **W20** | 17 May | ✅ üretildi | ✅ üretildi | — | Hüseyin scoring |
| **W21** | 24 May | 30 sample | 30 sample | opt. 30 sample | İlk 2-hafta drift dashboard |
| **W22** | 31 May | 30 sample | 30 sample | — | 3-hafta trend |
| **W23** | 7 Jun | 30 sample | 30 sample | — | **Baseline lock** — 4-hafta MA |
| Audit | 14 Jun | — | — | — | Retrospective Faz 7.3 |

**Toplam sample (4 hafta):** ~240 (120 gold + 120 reject + opt. 30 manual_queue)

---

## Acceptance Criteria

Baseline lock'da (14 Jun) hedeflenen metrikler:

| Metrik | Hedef | Plan v1 referans |
|---|---|---|
| **Gold pass rate** (verdict=pass / total) | ≥ 0.80 | Faz 4.1 vision (priority biased): %38; random Gold daha yüksek beklenir |
| **Reject false-negative rate** (verdict=pass / reject) | ≤ 0.10 | Rule-based filter conservative; <%10 hatalı reject |
| **4-hafta MA drift** (∆ pass% hafta-hafta) | ≤ 5pp | ma_tracker --baseline lock için |
| **Wrong_topic ratio** (Aromat sistemic) | ≤ 0.05 in Gold | Faz 4.1: Aromat zaten reject pool'da |
| **Solution-visible** | ≤ 0.02 in Gold | Edebiyat Sokagi manual_queue'da izole |

**Eğer Gold pass <0.65:** Faz 5+6 rule-based filter yetersiz → Faz 6.1 LLM judge tetiklenir (API key gerekli).
**Eğer Reject false-negative >0.20:** Filter conservative değil, Plan v1 Faz 5+6 doğrulanmadı → R1-R4 kuralları gözden geçirilir.

---

## Audit Akışı (her hafta)

1. **Pazar 09:00** — `run_weekly_audit.ps1` (Task Scheduler) veya manuel
2. **TSV üretilir** — `backend/_pilots/<YYYYMMDD>_weekly_<pool>_RAW.tsv`
3. **SCORING.tsv** auto-chain — `scoring_template --prepare` ile 3 boş kolon (verdict, error_type, notes)
4. **Hüseyin doldurur** — Excel/LibreOffice, 1-2 saat
5. **`drift_dashboard.py`** — kümülatif markdown rapor üretir
6. **`ma_tracker.py`** — 30-gün rolling avg + alarm flag
7. **Commit** — `_pilots/*.tsv` git-tracked, RESULT.md eklenir

---

## Pre-flight Kontroller (her hafta başında)

```bash
# 1. v_safe_for_beta view canlı mı?
psql -p 5434 -d kiro2 -c "SELECT COUNT(*) FROM v_safe_for_beta"

# 2. Pool composition drift kontrolü
psql -p 5434 -d kiro2 -c "SELECT quality_review_status, COUNT(*) FROM question_bank WHERE is_active=true GROUP BY 1 ORDER BY 2 DESC"

# 3. Önceki hafta scoring tamamlandı mı?
ls backend/_pilots/$(date -d "last sunday" +%Y%m%d)_weekly_*_SCORING.tsv

# 4. Task Scheduler aktif mi?
schtasks /Query /TN KIRO2_Weekly_Audit
```

---

## Bilinen Riskler

| Risk | Olasılık | Mitigasyon |
|---|---|---|
| **LLM-circular bias**: ground truth Claude AI ürettiğinden filter yapay yüksek pass verebilir | MED | Reject pool false-negative + beta student feedback ile cross-check |
| **Hüseyin scoring bottleneck**: haftada 2-4 saat | MED | Sample 30→20 düşürülebilir, ama MA stabilite kaybeder |
| **Pool size drift**: yeni soru import → composition değişir | LOW | Pre-flight kontrol step #2 |
| **Aromat sistemic carry-over**: filter eksik yakaladıysa Gold pool'a sızar | MED | Wrong_topic ratio metric tetiklenir, R2 rule revize |

---

## İlişkili Çıktılar

| Dosya | İçerik |
|---|---|
| `backend/scripts/quality/weekly_audit.py` | Sample üretici, `--pool gold|reject|manual_queue` |
| `backend/scripts/quality/scoring_template.py` | RAW → SCORING.tsv prepare + summarize |
| `backend/scripts/quality/drift_dashboard.py` | Kümülatif trend markdown |
| `backend/scripts/quality/ma_tracker.py` | 30-gün MA + alarm flag |
| `backend/scripts/quality/SCHEDULER_SETUP.md` | Task Scheduler kurulum talimatı |
| `backend/_pilots/20260517_weekly_gold_RAW.tsv` | W20 ilk Gold sample (30 satır) |
| `backend/_pilots/20260517_weekly_reject_RAW.tsv` | W20 ilk Reject sample (30 satır) |
| `backend/_pilots/_legacy_bronze_pool/` | Faz 5+6 öncesi 16 May sample (obsolete) |

---

## Faz 2.6 → Faz 7.3 Bağlantı

Baseline locked (14 Jun) sonrası retrospective rapor (#40 Faz 7.3):

1. 4-hafta drift dashboard tüm metrikler
2. Beta student feedback flag'leriyle Gold pass rate karşılaştırma
3. Filter precision/recall final değerlendirme
4. Faz 6.1 LLM judge devam mı, vazgeçildi mi karar

---

*Generated: 17 May 2026, Session 178 (Faz 2.6 baseline tracking kickoff).*
