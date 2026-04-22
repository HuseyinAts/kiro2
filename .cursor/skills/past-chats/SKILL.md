---
name: past-chats
description: @Past Chats tool'uyla önceki conversation'lardan context çekme rehberi. Copy-paste yerine selective reference — KIRO2 session continuity için.
---

# @Past Chats — Önceki Çalışmaya Referans

Cursor'un native `@Past Chats` tool'u: Yeni conversation başlatırken önceki
işi kopyala-yapıştır yerine **referans** olarak bağlarsın. Agent gerekli
kısımları selective olarak okur.

## Ne Zaman Yüklenmeli

- Yeni session başladı ama önceki iş bitmemişti
- "Geçen seferki gibi yap" senaryosu
- Context compaction sonrası kritik kararlar kayboldu
- Handoff sonrası devralma
- Benzer problem → önceki çözüm referans

## Ne Zaman KULLANMA

- Tamamen farklı task (önceki iş ilgisiz noise yapar)
- Çok kısa basit soru ("syntax error nedir?")
- İlk kez yapılan iş (referans yok)

## Kullanım

Agent input'unda:
```
@Past Chats
```

→ Liste açılır: son conversation'lar, konuya göre filtrelenebilir.

Veya doğrudan isme referans:
```
@Past Chats:20260420_irt_calibration
```

Agent:
1. İlgili chat'i tarar
2. Sadece gerekli kısımları extract eder
3. Mevcut prompt'la birleştirir

## KIRO2 Session Continuity Pattern

### Kötü Pattern (kopyala-yapıştır)

```
Yeni session:
"Geçen sprintte IRT kalibrasyonu yapmıştık. Platt scaling'den vazgeçip
empirical bucketing seçmiştik çünkü [uzun açıklama]. Golden dataset
tests/irt/test_calibration_golden.py'da [başka uzun açıklama]. Şimdi
FSRS entegrasyonu..."
```

Problems: 500+ token harcanır, context window şişer, agent stale bilgi alabilir.

### İyi Pattern (@Past Chats)

```
Yeni session:
@Past Chats:IRT kalibrasyon kararları

Şimdi FSRS entegrasyonu yapmamız lazım. IRT'de aldığımız empirical
yaklaşımı FSRS stability tahminine uyarlayabilir miyiz?
```

Agent önceki kararı okur, relevant kısmı özetler, yeni task'a uygular.

## Handoff + @Past Chats Birleşimi

Eski workflow (`.claude/skills/handoff/`):
1. Session sonunda SESSION_STATE.md yaz
2. Yeni session başında manuel oku

Yeni Cursor 3+ workflow:
1. Session sonunda `/handoff` komutu (mevcut)
2. Plan'ı `.cursor/plans/` kaydet (Plan Mode)
3. **Yeni session'da `@Past Chats` + `@plan:son-plan`** kombinasyonu

Manuel SESSION_STATE.md tutmak artık **opsiyonel** — Cursor handle ediyor.

## KIRO2 Kullanım Senaryoları

### Senaryo 1: Yarım kalan feature

```
@Past Chats:Exam submit endpoint

Kaldığımız yerden devam et. Validation kısmını bitirmiştik, rate
limit henüz eklenmedi. Testleri de yazalım.
```

### Senaryo 2: Benzer problem, farklı domain

```
@Past Chats:Question caching strategy

Question caching için Redis TTL + invalidation pattern'ı kurmuştuk.
Aynı stratejiyi exam session caching'e uyarla.
```

### Senaryo 3: Karar arkeolojisi

```
@Past Chats:Why question_bank not questions

"questions" tablosunu yerine "question_bank" seçme gerekçemiz neydi?
Yeni ekip üyesine anlatmak lazım.
```

### Senaryo 4: Hata öğrenme

```
@Past Chats:Middleware HTTPException 500 hatası

Bu hatayı Session 148'de çözmüştük. Yeni middleware yazıyorum,
aynı tuzağa düşmek istemiyorum. Pattern'ı hatırlat.
```

## Chat İsimlendirme (Future-Proof)

İyi isim: `20260420_exam_submit_endpoint` veya `IRT calibration Platt vs empirical`
Kötü isim: `Chat`, `Untitled`, `Test`

Agents Window'da chat'in sağ tıklayıp "Rename" ile güzel isim ver.

## Tool Limitleri

- `@Past Chats` sadece **senin** chat'lerine bakar (team değil)
- Team-wide sharing için Teams plan'da shared chats var
- Privacy mode: aktifse chat'ler local kalır, cloud search sınırlı

## Anti-pattern'lar

- **@Past Chats'ı her prompt'ta kullanmak** — agent confused olur
- **İsimsiz chat'lere referans vermek** — bulamaz
- **Çok geniş referans** ("all chats") — noise patlar
- **Kopyala-yapıştır + @Past Chats birlikte** — redundant, çelişki riski

## Compaction ile İlişki

Cursor chat compaction yaptığında detay kaybedilir. Alternatifler:

1. **Önemli kararı plan'a yaz** (`.cursor/plans/`) → compaction'dan etkilenmez
2. **`/handoff` ile SESSION_STATE.md yaz** → manuel ama güvenli
3. **Chat'i rename edip `@Past Chats` ile bağla** → selective retrieval

En iyisi üçünü birleştirmek: plan + handoff + named chat.

## Referans

- Resmi best practices: https://cursor.com/blog/agent-best-practices
- `.cursor/commands/handoff.md` — session kapatma workflow'u
- `.cursor/skills/plan-mode/SKILL.md` — plan'ı referans olarak kullanma
