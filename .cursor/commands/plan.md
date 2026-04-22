# Plan Mode Başlat

**Not:** Plan Mode'un doğal tetikleyicisi `Shift+Tab` (agent input'unda). Bu
komut, Shift+Tab unutulduğunda veya plan'ı workspace'e kaydetmek istediğinde
kullanılır.

## Ne Zaman Kullanılmalı

- KIRO2'de 3+ dosyayı etkileyen değişiklik
- Yeni API endpoint (tek dosya bile olsa — `api-endpoint.md` ile birleşir)
- Alembic migration (schema değişikliği)
- IRT/FSRS/BKT algoritma parametre değişikliği
- Frontend'de yeni component + state yönetimi
- "Nereden başlayayım?" diye düşündüğün her durum

## Ne Zaman Atlanabilir

- Tek satır bug fix
- Format/lint-only değişiklikler
- Zaten planlanmış işin uygulanması
- Daha önce 10+ kez yapmış olduğun mekanik task

## Protokol

1. **Agent input'una Shift+Tab bas** — Plan Mode'a geç
2. Task'ı tanımla; gerekirse gereksinim detaylarını ver
3. Agent clarifying soruları sorarsa cevapla
4. Üretilen Markdown planı review et — dosya yolları, kod referansları doğru mu?
5. Yanlış/eksik varsa inline düzenle
6. **"Save to workspace"** tıkla → `.cursor/plans/<tarih>_<konu>.md` olarak saklanır
7. Plan onaylandığında **Build** tuşuna bas → Agent Mode'a geçer, uygular

## KIRO2-Özel Plan Kontrol Listesi

Plan onaylamadan önce bunları kontrol et:

- [ ] Hangi tabloya erişiliyor? `question_bank` (77K) mi `questions` (boş legacy) mi? (Dual Table Trap)
- [ ] `is_active == True` filtresi var mı?
- [ ] IDOR koruması var mı? (`resource.user_id == current_user.id`)
- [ ] Yeni endpoint ise `get_current_user` Depends + loader.py ROUTER_MAPPING kaydı
- [ ] Migration ise Alembic, CONCURRENTLY index (Session 120-121 dersleri)
- [ ] Middleware ise HTTPException yerine JSONResponse (Session 148)
- [ ] Türkçe string işlem var mı? `turkish_upper/lower` kullanılmış mı?
- [ ] IRT parametre değişikliği ise golden dataset testi güncelleniyor mu?

## Planı "Save to Workspace" — Neden Önemli

- **Team documentation**: Başkaları ne yaptığını görür
- **Interrupted work**: Yarım kalan işe geri dönmek kolay
- **Future agent context**: Sonraki session'da plan referans olarak kullanılır
- **Audit trail**: Neden şu yaklaşımı seçtin, hangi alternatifleri değerlendirdin

## Plan Revizyonu (Başa Dön)

Agent plan'a göre kod yazdı ama beğenmedin mi?
1. Değişiklikleri **revert** et (git reset --hard HEAD veya Apply'ı geri al)
2. Plan dosyasına dön (`.cursor/plans/<dosya>.md`)
3. Eksik olan detayları ekle, fazla olanları çıkar
4. Agent'a "planı güncelledim, tekrar uygula" de

Takip prompt'larıyla in-progress agent'ı düzeltmeye çalışmaktan **çok daha hızlı**
ve daha temiz sonuç verir.

## Referans

- `.cursor/skills/plan-mode/SKILL.md` — plan template'i
- Resmi doc: https://cursor.com/docs/agent/plan-mode
- Cursor ekibinin önerdiği #1 best practice
