# Curator Quota Policy (Faz 7.4)

**Status:** Active (Session 178, 21 May 2026)
**Owner:** Hüseyin (project lead)

## Hedef

Beta launch sonrası **gold pool'u haftalık 200-350 satır büyütmek** —
yani günlük **30-50 yeni Sapphire (auto_judged_high → human_verified)**
curator review hedefi.

## Neden bu aralık?

| Faktör | Değer |
|---|---|
| Curator UI velocity (Faz 4.3 ölçümü) | hedef p50 ≤ 90s/soru |
| Curator günlük efor üst sınırı | ~1.5 saat (60 verdict/saat × 1.5h = 90 verdict üst sınır) |
| Beta öğrenci günlük çekiş | ~10 soru × 10 öğrenci = 100 soru/gün |
| Sapphire reserve (1 hafta) | 350 yeni satır 1 haftalık tampon |

**Tabandan:** 30/gün — düşük (curator atlama, motivasyon kaybı riski)
**Üstten:** 50/gün — yüksek (curator burnout, kalite düşüşü riski)

## Ölçüm

```bash
# Günlük throughput
python backend/scripts/quality/curator_velocity_check.py --since 1

# Haftalık trend (Faz 7.4 quota signal)
python backend/scripts/quality/curator_velocity_check.py --since 7
```

Script çıktısında "Quota signal" satırı ✅ (30-50/gün), ⚠️ LOW (<30), 🔥 HIGH (>50).

## Alarm Kuralları

| Durum | Aksiyon |
|---|---|
| < 30/gün (3 gün üst üste) | Curator UI sorununu araştır (latency, UX) veya queue tükenmesi |
| > 50/gün (3 gün üst üste) | Velocity düşmüş mü kontrol et — hızlı tıklama = düşük kalite |
| Velocity p90 > 180s | Soru türü zorluk artmış mı? Curator yorgun mu? |
| Velocity p10 < 10s | Bot davranışı veya distraction — kalite şüphesi |

## Quota Adjustment

Hedef 30-50 sabit değil — Sapphire pool durumuna göre:

| Sapphire pool durumu | Günlük hedef |
|---|---|
| < 200 (kritik düşük) | 50/gün (sprint mode) |
| 200-500 | 40/gün (steady) |
| 500-1000 | 30/gün (maintenance) |
| > 1000 (yeterli reserve) | 20/gün (selective curation) |

## İlişkili

- [[Curator UI Faz 3.1-3.6]] — `/admin/curator` endpoint set
- [[curator_buffer.md]] — Buffer policy (insan emek monitoring)
- [[Faz 4.3 velocity check]] — `curator_velocity_check.py`
