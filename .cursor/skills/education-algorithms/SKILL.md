---
name: education-algorithms
description: IRT 3PL, FSRS, BKT, ZPD parametre doğrulama ve implementasyon. Eğitim algoritmaları kodlanırken/değiştirilirken yüklenir.
---

# Education Algorithms — KIRO2

KIRO2'nin çekirdek eğitim algoritmaları: IRT (Item Response Theory), FSRS (Free
Spaced Repetition Scheduler), BKT (Bayesian Knowledge Tracing), ZPD (Zone of
Proximal Development).

## Ne Zaman Yüklenmeli

- `backend/app/services/fsrs/**`, `backend/app/services/irt/**`, `backend/app/services/bkt/**` üzerinde çalışırken
- Soru seçim algoritması tasarlarken/düzenlerken
- Kalibrasyon parametrelerini değiştirirken
- YKS zorluk dağılımı ayarlarken

## Hızlı Referans — Parametre Sınırları

| Alg. | Parametre | Aralık | Tipik |
|---|---|---|---|
| IRT | difficulty (b) | [-4.0, 4.0] | 0 |
| IRT | discrimination (a) | [0.2, 4.0] | 1.0-1.5 |
| IRT | guessing (c) | [0.0, 0.35] | 0.2 (5 şıklı MCQ) |
| IRT | ability (θ) | [-4.0, 4.0] | 0 |
| FSRS | stability (S) | [0.1, 3650 gün] | - |
| FSRS | difficulty (D) | [0, 10] | - |
| FSRS | retrievability (R) | [0, 1] | - |
| ZPD | optimal başarı | [0.15, 0.85] | 0.5 |

## Kritik Formüller

**IRT 3PL:**
```
P(θ) = c + (1-c) / (1 + exp(-a(θ-b)))
```

**FSRS retrievability:**
```
R(t) = exp(-t/S)
```

**ZPD bölgeleri:**
- `p > 0.85` → TOO_EASY (öğrenme potansiyeli düşük)
- `0.15 ≤ p ≤ 0.85` → OPTIMAL (ideal)
- `p < 0.15` → TOO_HARD (motivasyon düşüşü)

## YKS Zorluk Dağılımı (ÖSYM Kalıpları)

| Seviye | Hedef oran | IRT b |
|---|---|---|
| Kolay | ~30% | b < -1.0 |
| Orta | ~40% | -1.0 ≤ b ≤ 1.0 |
| Zor | ~25% | 1.0 < b ≤ 2.5 |
| Çok Zor | ~5% | b > 2.5 |

## Kod Değişikliği Kuralları

1. Parametre değiştirmeden önce golden dataset testi (`tests/irt/`, `tests/fsrs/`) durumunu kontrol et
2. Pydantic validator'ları kullan — silent accept yasak
3. NaN/Inf kontrolü: `math.isnan(x) or math.isinf(x)` → REJECT
4. Platt scaling yerine empirical-first (>10 örnek varsa bucket mean), Session 48 dersi

## Detaylı Rehber

Derin içerik, Pydantic model template'leri, CAT entegrasyonu, Fisher Information:
- `.claude/skills/education-algorithms/SKILL.md` (KIRO2-özel)
- `.claude/skills/irt-validation/SKILL.md` (IRT detayı, CAT, MLE)

İhtiyaç duyarsan yukarıdaki dosyalardan birini `@` ile attach et.
