---
name: pilot-protocol
description: KIRO2 pilot akışı kuralları — sapma örüntüleri (D-8..D-13), yasak listesi, DUR sinyalleri, commit hijyeni. Migration veya pilot plan dosyası düzenlendiğinde otomatik yüklenir.
globs:
  - ".cursor/plans/**"
  - "backend/alembic/versions/**"
  - "backend/_pilots/**"
---

# Pilot Protocol — Cursor Agent Skill

Bu skill pilot plan dosyası veya migration düzenlendiğinde otomatik yüklenir.

## Sapma Örüntüleri (D-8..D-13)

Önceki pilotlarda tekrar eden sapmalar. Farkında ol:

- **D-8**: Raw SQL yerine ORM model kullan. Raw SQL plan istemedikçe YASAK.
- **D-9**: Plan-dışı test ekleme YASAK.
- **D-10**: ADIM 0 / state.md atlanabilir ama bilinçli karar olmalı.
- **D-11**: Alembic down_revision yanlış yazılabilir → `alembic heads` ile teyit zorunlu.
- **D-12**: Container deploy drift → `docker cp` + `grep` doğrulama zorunlu.
- **D-13**: Sayı hedefine göre commit üretme YASAK, başka branch'ten cherry-pick YASAK.

## YASAK Listesi

- `git add -A` (seçici stage zorunlu)
- `git push --force`
- `alembic revision --autogenerate` (IRT kolon DROP riski)
- `git commit` Cursor UI ile (footer riski — Agent mode terminal kullan)
- `/commit` slash komutu (`git add -A` yapar)
- `/deploy` slash komutu (pilot container-sync manuel)
- Plan-dışı test eklemek (D-9)
- Başka branch'ten cherry-pick (D-13)
- Sayı hedefine göre eksik tamamlama (D-13)
- Kolon adı varsayma (postgres MCP ile sorgula önce)
- Container'a deploy etmeden smoke PASS demek (D-12)
- Plan-dışı dosya düzenlemek
- Kapsam genişletmek

## DUR Sinyalleri

Aşağıdakilerden biri olursa DUR + raporla, devam etme:

- Beklenmeyen tablo, kolon veya çelişki
- Çift alembic head
- Migration dosyası 30+ satır (kapsam genişlemesi)
- `docker exec grep` sayısı 0 (deploy başarısız)
- Smoke herhangi senaryo FAIL
- Plan-dışı dosya değiştirme ihtiyacı
- Commit sayısı beklenen listeden farklıysa
- Beklenen container kapalıysa
- PostgreSQL bağlantısı başarısız

## Commit Hijyeni

```bash
# Hook bypass
git -c core.hooksPath=.git/hooks-empty commit -m "<subject>" --no-verify

# Kontrol
git log -1 --format='%H%n%s%n---%n%b'
# --- altı boş olmalı, footer varsa amend et
```

Subject 50 char altı, conventional commit formatı.
Seçici `git add <dosya>`, `-A` yasak.
