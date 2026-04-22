# .cursor/plans/ — Plan Mode Çıktıları

Bu dizin Plan Mode (Shift+Tab) ile üretilen implementation plan'larının
"Save to workspace" ile kaydedildiği yer.

## Amaç

- **Future context**: Sonraki agent session'da `@<plan-adı>` ile referans
- **Team documentation**: Ne düşünüldü, hangi alternatifler değerlendirildi
- **Interrupt recovery**: Yarım kalan iş → hızlı devralma
- **Decision archaeology**: "Neden bu yaklaşım?" sorusuna kaynak

## İsimlendirme

Format: `YYYYMMDD_kısa_konu.md`

Örnekler:
- `20260420_add_exam_submit_endpoint.md`
- `20260422_irt_calibration_platt_to_empirical.md`
- `20260425_migrate_sqlalchemy_2035.md`

Kötü isim: `plan1.md`, `new.md`, `untitled.md`

## Yaşam Döngüsü

1. **Plan Mode** — Shift+Tab ile plan üret
2. **Review + düzenle** — inline plan'ı düzenle
3. **Save to workspace** — bu dizine yazılır
4. **Build** — Agent planı uygular
5. **Archive** — uygulandıktan sonra silmek YERİNE:
   - `archived/` alt dizinine taşı, veya
   - git log'da kalsın (commit ile silme)

## Git Stratejisi

`.cursor/plans/` **version control'e dahil**. Neden?

- Takım arkadaşları aynı plan'a erişir
- `git log .cursor/plans/` ile karar geçmişi
- Plan + implementation diff'i birlikte review

`.gitignore`'a EKLEME.

## Mevcut Plan'lar

_Henüz kaydedilmiş plan yok. İlk Plan Mode kullanımınla burada listelenecek._

## Template

Yeni plan için tipik yapı:

```markdown
# Plan: [task özeti]

## Context
- Konu: [ne yapılacak]
- Gerekçe: [neden]
- Etkilenen alan: [backend/frontend/algoritma]

## Araştırma Özeti
- İlgili dosyalar: ...
- Benzer pattern: ...
- Etkilenen endpoint/tablo: ...

## Uygulama Adımları
### 1. [Adım] — [dosya]
- [ ] task 1
- [ ] task 2

## Edge Cases
- [ ] ...

## Test Stratejisi
- Unit:
- Integration:
- Regression:

## Rollback Planı
- ...

## KIRO2 Sağlık Kontrolü
- [ ] Dual Table (question_bank)
- [ ] is_active filtresi
- [ ] IDOR koruması
- [ ] Router kaydı
- [ ] Migration Alembic
- [ ] Middleware JSONResponse
- [ ] Türkçe string helper
- [ ] IRT aralık kontrolleri
```

## Referans

- `.cursor/commands/plan.md` — Plan Mode workflow komutu
- `.cursor/skills/plan-mode/SKILL.md` — plan template + KIRO2 kontrol listesi
- Resmi doc: https://cursor.com/docs/agent/plan-mode
