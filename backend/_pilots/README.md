# `backend/_pilots/` — Router Aktivasyon Pilotları

Bu dizin, KIRO2'deki router/feature aktivasyon çalışmalarının **teknik durum raporlarını** tutar. Her pilot için tek bir snapshot: çalışmaya başladığımızda ortamın ne halde olduğu.

## Amaç

KIRO2'de briefing'ler ("13 disabled router") ile kod (`DISABLED_ROUTERS = {}`) arasında zamana göre **çelişki** oluşabiliyor. Her pilot öncesi **ADIM 0 — Gerçek Durum Tespiti** yapıyoruz. Bu dizin o tespitlerin arşivi.

Sonraki pilotlar için bu artifact'ler **prior knowledge** olarak okunmalı — aynı soruları tekrar sormaya gerek kalmasın.

## İsim Konvansiyonu

```
YYYYMMDD_<router_or_feature>_state.md
```

Örnekler:
- `20260420_diary_api_state.md` — diary pilot ADIM 0
- `20260421_live_session_state.md` — live session öncesi
- `20260422_batch_router_state.md` — 12 router topluca ADIM 0

## Plan ↔ Artifact Eşleşmesi

| Faz | Nerede |
|---|---|
| **Plan** (öncesi) | `.cursor/plans/YYYYMMDD_<name>.md` |
| **State** (ADIM 0 çıktısı) | `backend/_pilots/YYYYMMDD_<name>_state.md` (bu dizin) |
| **Result** (sonrası) | `.cursor/plans/YYYYMMDD_<name>_RESULT.md` |

## İçeriğe Ne Koyulur

ADIM 0 raporunun tipik bölümleri:

1. **Ön koşullar** — backup, git durumu, log taraması
2. **Tablolar var mı?** — PostgreSQL `information_schema` sorgu çıktıları
3. **FK/PK tip uyumu** — briefing "users.id VARCHAR" kuralına uyum
4. **Alembic durumu** — `current`, `heads`, `history` özeti
5. **Router yükleniyor mu?** — `docker logs` + `loader.py` durumu
6. **Aşama önerisi** — A/B/C/D kararı (insan onayı öncesi)

## Ne Konulmaz

- Production secret, API key, token (briefing bile yazmıyor)
- Büyük binary çıktılar (SQL dump'lar, JSONL)
- Kullanıcı verisi (PII)

## Git İzleme

Bu dizindeki `.md` dosyaları **tracked** edilir (pilot tarihçesi değerli). Ancak bir sebeple tutulmaması gereken pilot varsa (hassas bilgi), `.gitignore`'a özel dosya adıyla eklenebilir.

## Sonraki Pilot için Composer 2 İpucu

Yeni pilot başlatırken prompt'una ekle:

```
Prior knowledge: backend/_pilots/ dizinindeki tüm _state.md dosyalarını oku.
Aynı ortamdaki önceki tespitleri prior olarak kullan.
Örn. "diary_api pilotunda users.id VARCHAR teyit edildi" — tekrar sorma.
```

Böylece her pilotta psql sorgularını baştan yürütmezsin; sadece delta sorularına odaklanırsın.
