# Commit

KIRO2 değişikliklerini stage et ve commit yap. Kullanıcı commit mesajını komut
sonrasında belirtecek.

## Adımlar

1. Terminal'den `git status --short` çalıştır ve dosya durumunu raporla
2. `git diff --stat HEAD` ile diff özetini göster
3. Kullanıcıdan gelen mesajı conventional commit formatına uygun düzenle
4. `git add -A` ile stage et
5. `git commit -m "<formatted_message>"` ile commit

## Commit Convention (KIRO2)

Format: `<type>(<scope>): <description>`

### Types

- `feat`: Yeni özellik
- `fix`: Bug düzeltme
- `docs`: Dokümantasyon
- `style`: Format (kod değişmez)
- `refactor`: Yeniden yapılandırma
- `test`: Test
- `chore`: Build/CI/tooling
- `perf`: Performans

### Scopes (KIRO2)

`backend`, `frontend`, `ai`, `db`, `auth`, `exam`, `content`, `ocr`, `api`

### Örnekler

```
feat(auth): add 2FA support for admin users
fix(exam): resolve timer sync issue
perf(db): optimize question query with index
test(backend): add unit tests for exam service
```

## Kurallar

- Kullanıcı sadece özet verdiyse type/scope'u koddan çıkar
- 50 karakteri geçen mesaj satırı yasak (ilk satır için)
- Breaking change varsa `!` ekle: `feat(auth)!: remove password grant flow`
