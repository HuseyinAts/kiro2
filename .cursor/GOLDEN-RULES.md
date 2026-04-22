# 🏆 KIRO2 Cursor Altın Kuralları

Günlük kullanımda en çok kaçırılan, en yüksek ROI'li 3 kural. Bunlar
kurulumun **kalbi** — diğer her şey bu üçünün üstüne inşa edilmiş.

---

## 1. `Shift+Tab` = Kas Hafızası

**Kural:** Karmaşık task'a başlamadan önce **daima** `Shift+Tab` ile Plan Mode'a geç.

**Neden:**
- Cursor ekibinin **resmi #1 best practice**'i
- Chicago Üniversitesi çalışması: deneyimli developer'lar plan yapıyor
- Plan → onay → Build disiplini, revert'ten hızlı sonuç verir
- Agent "concrete goal" ile çok daha iyi kod üretir

**Ne zaman atla:**
- Tek satır bug fix
- Format/lint-only değişiklik
- 10+ kez yapılan mekanik task

**Ne zaman ZORUNLU:**
- 3+ dosya etkileyen değişiklik
- Yeni endpoint / migration / algoritma parametresi
- Belirsiz yaklaşım ("nereden başlasam?")
- KIRO2 IRT/FSRS/BKT dokunuşları

**Plan'ı daima kaydet:** "Save to workspace" → `.cursor/plans/YYYYMMDD_konu.md`

**Refleks testi:** Agent input'una tıkladıktan sonra parmağın **otomatik
Shift+Tab'a gidiyorsa** doğru yoldasın.

---

## 2. Chat'leri İsimlendir

**Kural:** Agents Window'da **her chat'e sağ tık → Rename** ile anlamlı isim ver.

**Neden:**
- 2 hafta sonra `@Past Chats` gerçekten işe yarar (isimsiz chat'ler kaybolur)
- Session continuity manuel SESSION_STATE.md'ye alternatif
- Team review / arkeoloji — "şu kararı ne zaman almıştık?"

**İyi isim formatı:**
- `20260420_exam_submit_endpoint`
- `IRT calibration Platt vs empirical`
- `Dual Table Trap debug - question_bank 0 row`

**Kötü isim:**
- `Chat`, `Untitled`, `Test`, `New conversation`
- Sadece tarih (`2026-04-20`)
- Sadece emoji (`🔥`)

**Pattern:**
- `tarih_konu` (yeni work için)
- `konu_debug` (bug fix için)
- `konu_decision` (mimari karar için)

**Yeni session'da kullanım:**
```
@Past Chats:IRT calibration
```
→ Agent selective olarak ilgili geçmişi çeker, kopyala-yapıştır YASAK.

---

## 3. `/best-of-n` Kıt Kullan

**Kural:** `/best-of-n`'i **sadece gerçekten belirsiz kararlar** için çalıştır.
Günlük CRUD'da Composer 2 yeter.

**Neden:**
- Her model ayrı kredi → 4x maliyet
- Composer 2 KIRO2 pattern'larına zaten hakim (Pro'da cömert havuz)
- Yanlış kullanırsa kredi havuzunu 1 haftada yakarsın

**Ne zaman KULLAN:**
- ✅ IRT kalibrasyonu / FSRS parametre tuning (algoritma-kritik)
- ✅ Güvenlik-kritik kod (auth flow, IDOR, JWT)
- ✅ Mimari karar (3+ dosya etkileyen refactor)
- ✅ Belirsiz yaklaşım ("A mı B mi?")

**Ne zaman KULLANMA:**
- ❌ Basit CRUD endpoint
- ❌ Format/lint fix
- ❌ Tek satır bug fix
- ❌ Daha önce yapılmış benzer task
- ❌ Composer 2'nin zaten iyi yapacağı iş

**Budget rehberi:**
- Haftada 1-2 kez → Pro ($20) yeter
- Haftada 3+ kez → Pro+ ($60) değer
- Günde 2+ kez → kötü kullanım, gözden geçir

**Composer 2 default refleks ol:**
Çoğu KIRO2 task'ında Composer 2 yeter. Auto mode'u aç, sadece gerçek
engel gördüğünde manuel modele geç.

---

## 🎯 Günlük Refleks Döngüsü

Her task'a başlarken bu 3 soruyu sor:

```
1. Shift+Tab'a bastım mı?        → karmaşıksa ZORUNLU
2. Chat'imin adı var mı?          → her chat için ZORUNLU
3. Bu task /best-of-n'e değer mi? → nadiren EVET
```

Bu 3 refleks kas hafızasına girdiğinde Cursor Pro'nun gerçek değerini
alıyorsun. Girmezse ayda $20 veriyorsun ama Copilot seviyesinde kullanıyorsun.

---

## 📍 Bu Kurallar Nerede Geçiyor

Bu kurallar tek **source of truth** burada. Diğer dosyalar buraya referans:

- `.cursor/rules/00-core.mdc` — agent her prompt'ta görür
- `.cursor/README.md` — üstte vurgulu blok (insan)
- `.cursor/MIGRATION-NIGHTLY.md` — kurulum rehberinde §9 Kısayollar

Bir kuralı değiştirmek istersen **sadece bu dosyayı** güncelle. Diğerleri
referans eder.

---

## 🔗 İlgili Derin İçerik

- `.cursor/skills/plan-mode/SKILL.md` — Plan Mode workflow + KIRO2 checklist
- `.cursor/skills/past-chats/SKILL.md` — @Past Chats kullanım senaryoları
- `.cursor/commands/best-of-n.md` — /best-of-n workflow + KIRO2 senaryoları
- `.cursor/commands/plan.md` — Plan Mode komutu
- https://cursor.com/blog/agent-best-practices — Cursor ekibinin resmi rehberi
