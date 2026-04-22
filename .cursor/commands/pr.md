# Pull Request Oluştur

Mevcut branch için GitHub'da PR aç.

## Adımlar

1. Önce durum kontrolü:
   - `git branch --show-current` → current branch
   - `git log main..HEAD --oneline` → main'e göre commit farkı
   - `git diff main --stat` → değişen dosyalar
2. Branch henüz push edilmemişse: `git push origin HEAD`
3. `gh pr create --fill` ile PR oluştur, GitHub CLI template'i doldursun
4. Kullanıcıya PR URL'sini ver

## PR Body Template (KIRO2)

Eğer `gh pr create --fill` yeterli değilse bu template kullan:

```markdown
## Değişiklik Özeti
[Kısa açıklama — 2-3 cümle]

## Değişiklik Tipi
- [ ] feat: Yeni özellik
- [ ] fix: Bug düzeltme
- [ ] refactor: Kod iyileştirme
- [ ] docs: Dokümantasyon
- [ ] test: Test

## Test Edildi mi?
- [ ] `pytest -x` tam pass
- [ ] Frontend testler geçti (uygulanabiliyorsa)
- [ ] Manuel smoke test

## Checklist
- [ ] ruff check + format geçti
- [ ] mypy hatası yok (baseline üzerinde)
- [ ] Yeni endpoint varsa AuthGuard + IDOR check
- [ ] Yeni migration reversible
- [ ] CLAUDE.md / progress.md güncel
```

## Etiket Önerileri

Değişen dosyalara göre otomatik etiketle:

- `backend/**` → `backend`
- `frontend/**` → `frontend`
- `ai_ml/**` → `ai-ml`
- `alembic/**` → `migration`
- Yeni test sayısı > 10 → `testing`
- Production DB'ye etki varsa → `P0-critical`

## BugBot Entegrasyonu

PR açıldıktan sonra BugBot otomatik review yapacak (`.cursor/BUGBOT.md` kuralları).
Bug çıkarsa "Fix in Cursor" linkine tıkla veya PR'a `bugbot run` yorum at.
