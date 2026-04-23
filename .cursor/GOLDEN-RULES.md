# 🏆 KIRO2 Cursor Altın Kuralları

Günlük kullanımda en çok kaçırılan, en yüksek ROI'li 3 kural. Bunlar
kurulumun **kalbi** — diğer her şey bu üçünün üstüne inşa edilmiş.

---

## 1. Hüseyin Doğrudan İş Verir

**Kural:** Hüseyin Cursor Agent mode'a doğrudan iş verir. Claude Desktop
isteğe bağlı danışmandır — strateji, mimari analiz, karmaşık karar için.
Her iş için plan beklemek YASAK.

**Ne zaman Claude Desktop'a danış:**
- Mimari karar (hangi yaklaşım?)
- Risk analizi (migration, auth değişikliği)
- Borç önceliklendirme (sıralama kararı)
- Sapma analizi (Composer 2 çıktısı şüpheli)

**Ne zaman doğrudan Agent'a ver:**
- Bug fix, feature, config değişikliği
- Smoke test, doğrulama
- Dosya oluşturma/düzenleme
- Commit hijyeni

**Güvenlik katmanı (DB/migration/auth işleri):**
- pg_dump backup Hüseyin yapar
- Agent commit atar, Hüseyin push yapar
- Migration upgrade Hüseyin yapar
- `.cursor/skills/pilot-protocol/` sapma koruması sağlar

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

**Yeni session'da kullanım:**
```
@Past Chats:IRT calibration
```
→ Agent selective olarak ilgili geçmişi çeker, kopyala-yapıştır YASAK.

---

## 3. `/best-of-n` Kıt Kullan

**Kural:** `/best-of-n`'i **sadece gerçekten belirsiz kararlar** için çalıştır.
Günlük CRUD'da Composer 2 yeter.

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

---

## 🎯 Günlük Refleks

Her task'a başlarken:

```
1. Bu işi doğrudan Agent'a verebilir miyim?  → çoğu zaman EVET
2. Chat'imin adı var mı?                     → her chat için ZORUNLU
3. Bu task /best-of-n'e değer mi?            → nadiren EVET
```

---

## 📍 Bu Kurallar Nerede Geçiyor

Bu kurallar tek **source of truth** burada. Diğer dosyalar buraya referans:

- `.cursor/rules/00-core.mdc` — agent her prompt'ta görür
- `.cursor/README.md` — üstte vurgulu blok (insan)
- `.cursor/skills/pilot-protocol/SKILL.md` — sapma koruması
