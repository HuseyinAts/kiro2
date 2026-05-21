# Curator Buffer Policy (Faz 7.6)

**Status:** Active (Session 178, 21 May 2026)
**Owner:** Hüseyin

## Amaç

Curator (insan) emek harcaması ile beta öğrenci çekişi arasında **sağlıklı
bir reserve buffer** koruyarak:

1. Pipeline'a kesinti olmaması (öğrenci queue tükenmesin)
2. Curator'un yetişememesi durumunda yedek elde olması
3. Quality drift erken sinyal vermesi

## Buffer Tanımı

```
buffer = v_safe_for_beta - estimated_consumption_30d
       = 12,362 - (100 öğrenci × 50 soru/gün × 30 gün × 0.3 unique-rate)
       = 12,362 - 45,000 × 0.3 = 12,362 - 13,500
       = -1,138 (KISA)
```

> **Not (21 May 2026):** Şu an `v_safe_for_beta = 12,362`, ama bu R1 restore
> tarafından yeni geldi ve henüz Curator UI ile audit edilmedi (Sapphire = 0).
> 30 günlük 30-50 daily target (Faz 7.4) ile ay sonu Sapphire pool ~1000-1500
> olur. Sonra buffer pozitife geçer.

## Threshold'lar

| Durum | Threshold | Aksiyon |
|---|---|---|
| **GREEN** | buffer > 5,000 | Normal işleyiş |
| **YELLOW** | 1,000 < buffer < 5,000 | Curator quota ↑ 40/gün, ayrıca [[Faz 6.3]] judge run düşün |
| **RED** | buffer < 1,000 | Acil yedek üretim: judge full run + manuel curator marathon |
| **CRITICAL** | buffer < 0 | Beta yeni öğrenci kabulü dondur, sadece mevcut öğrencilere içerik akış |

## Curator Burnout Önleme

**İnsan emek monitoring:**

- Curator günlük 30-50 verdict üst sınırı (Faz 7.4)
- Haftalık 6 gün × 90 dakika = **9 saat/hafta** sınırı
- 1 hafta tatil her 8 haftada
- Curator velocity p90 > 300s ⇒ molali oturum öner

**Multi-curator:**

- Beta sonrası 2. curator alımı önerilir (inter-rater dogrulama için)
- Inter-rater kappa < 0.7 ⇒ spec/training revisited

## Buffer Refill Stratejileri

Buffer < 5,000 düştüğünde sırayla:

1. **Curator quota** 40 → 50/gün artır
2. **Judge pilot run** (Faz 6.1, ~1000 satır, ~$15) — gold pool'u %20 artırır
3. **Judge full run** (Faz 6.3, ~80K Bronze, ~$1,500) — büyük refill
4. **External curator hire** (kalifiye Türkçe öğretmen, $50-100/saat)

## Ölçüm

```bash
# Buffer state
python backend/scripts/quality/curator_velocity_check.py --since 30 | grep "Daily avg"

# v_safe_for_beta count
psql -p 5434 -d kiro2 -c "SELECT COUNT(*) FROM v_safe_for_beta"
```

## İlişkili

- [[curator_quota.md]] — Günlük hedef (Faz 7.4)
- [[Faz 6.1 judge pilot]] — Buffer refill alternatif
- [[v_safe_for_beta]] — Convention v2 view
