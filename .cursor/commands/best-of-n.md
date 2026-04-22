# Best-of-N — Paralel Multi-Model Karşılaştırma

Aynı task'ı birden çok modelde paralel çalıştırır, ayrı worktree'lerde
izole eder, sonuçları karşılaştırır. Cursor en iyisini önerir.

## Ne Zaman Kullanılmalı

Cost ve süre trade-off'u yüksek — sadece **değen** işler için:

- **Zor algoritma değişikliği**: IRT kalibrasyonu, FSRS parametre tuning,
  ZPD threshold ayarı
- **Güvenlik-kritik kod**: Auth flow, JWT validation, IDOR koruması
- **Mimari karar**: 3+ dosyayı etkileyen refactor
- **Belirsiz yaklaşım**: "Acaba şöyle mi böyle mi?" olduğun durum

## Ne Zaman KULLANMA

- Mekanik fix (format, typo, basit bug)
- Tek model zaten yeterince iyi yapacak iş
- Bütçe sıkıntısı varsa — her model ayrı kredi tüketir
- Basit CRUD endpoint

## Protokol (Cursor 3.x Native)

### Option A — `/best-of-n` komutu (önerilen)

Agents Window'da:
```
/best-of-n
[sonra task'ı yaz]
```

Cursor otomatik:
1. Ayrı worktree'ler oluşturur (her model için 1)
2. Her worktree'de aynı prompt'u farklı modelde çalıştırır
3. Tamamlananları diff olarak gösterir
4. Hangi sonucun iyi olduğunu önerir

### Option B — Manuel (model dropdown'dan)

Agent dropdown'dan birden çok modeli seç (Ctrl/Cmd+tıkla):
- Composer 2 (Cursor'un modeli, Pro'da cömert havuz)
- Opus 4.6 (Anthropic, derin reasoning)
- GPT-5.4 (OpenAI)
- Gemini 3 Pro (Google)

Tek prompt submit et → side-by-side compare.

## KIRO2 Kullanım Senaryoları

### Senaryo 1: IRT Parametre Kalibrasyonu

```
/best-of-n

Task: IRT 3PL parametrelerinin MLE estimation'ında convergence sorunu var.
Öğrenci yanıtı az (<20) olduğunda Platt scaling fallback kullanıyoruz ama
skewed dağılımda bias üretiyor. Empirical bucketing ile karşılaştır ve
daha robust bir fallback öner.

Kısıtlar:
- Golden dataset testi: tests/irt/test_calibration_golden.py
- Latency bütçesi: <50ms / soru (CAT için)
- Session 48 dersi: Platt yerine empirical-first (>10 örnek varsa)
```

Beklenen: 3-4 farklı yaklaşım alırsın (farklı model, farklı bias). En
iyiyi seç veya en iyi 2'yi birleştir.

### Senaryo 2: Güvenlik-kritik Endpoint

```
/best-of-n

Task: POST /api/v1/exams/{exam_id}/submit endpoint'ini güvenli hale getir.
- JWT validation
- exam.user_id == current_user.id (IDOR)
- Time window check: submitted_at <= started_at + exam.duration
- Rate limit: 5 submit / minute / user
- Audit log: user_id, exam_id, ip, user_agent

Mevcut kod: backend/app/api/v1/exams.py line 180-220.
```

Farklı modeller farklı güvenlik pattern'ları önerecek. En sıkısını seç.

### Senaryo 3: Belirsiz Mimari Karar

```
/best-of-n

Task: KIRO2'nin question generation pipeline'ı şu an Redis queue + Celery
worker kullanıyor. Throughput yetersiz (~5 q/s). Alternatifler:
A) Celery horizontal scaling (+5 worker pod)
B) RQ'ya geçiş (daha light)
C) Direkt asyncio task queue (in-process)
D) Redpanda + Kafka streaming

Her biri için: complexity, latency, KIRO2 stack uyumu, migration maliyeti.
Öner ve karşılaştır.
```

## Maliyet Uyarısı

- Her model ayrı kredi tüketir → 4 model = 4x maliyet
- Composer 2 Pro'da cömert havuzda → onu dahil et
- Frontier modeller (Opus 4.6, GPT-5.4) Pro'da kredi yer
- Pro+ ($60) veya Ultra ($200) plan'da `/best-of-n` pratik olarak sınırsız

## Çıktı Yorumlama

Cursor "best" önerdiği şunlara bakarak:
- Test passing oranı
- Lint/type error sayısı
- Edit kapsamı (minimum değişiklik tercih)
- Code quality heuristic'leri

Ama bu bir **öneri** — sen kontrol etmelisin. Özellikle:
- Test coverage yüksek ama mantık yanlış olabilir (reward hacking)
- Fewer edits iyi görünür ama incomplete olabilir
- Composer 2 KIRO2 conventions'a daha hakim olabilir (Türkçe, KIRO2-özel pattern)

## Anti-pattern'lar

- **Her task için /best-of-n** — maliyet patlar, değer eklemez
- **Sonuçları merge etmek** — model stilleri karışır, sonuç tutarsız
- **Tek model zaten biliyor** — örneğin basit CRUD'da Composer 2 yeter

## Referans

- Cursor 3.0 changelog: /best-of-n ve /worktree komutları
- `.cursor/skills/kiro2-specific/SKILL.md` — KIRO2 pattern'ları
- Resmi doc: https://cursor.com/docs/configuration/worktrees
