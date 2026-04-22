# Worktree Başlat — İzole Paralel Agent

Cursor 3.0 ile gelen native `/worktree` komutu. Her agent kendi git
worktree'sinde çalışır — dosyalar izole, birbirine çarpmaz.

## Ne Zaman Kullanılmalı

- **Uzun süren task'ı başlatırken** ama diğer işlere de devam etmek istediğinde
- **Risky experiment** — main branch'e dokunmadan denemek istediğin değişiklik
- **Paralel feature development** — 2 feature'ı aynı anda geliştirmek
- **Refactor**: mevcut çalışır durumunu korurken büyük değişiklik
- **Best-of-N**: paralel model karşılaştırma (otomatik worktree kullanır)

## Nasıl Kullanılır

Agents Window'da:
```
/worktree
[sonra task'ı yaz]
```

Cursor otomatik:
1. `git worktree add` ile yeni branch ve dizin oluşturur
2. Agent o worktree'de çalışır (senin ana dizininde değil)
3. Agent bitince **Apply** tıkla → değişiklikler working branch'e merge olur
4. Veya **Discard** → worktree silinir, ana branch hiç etkilenmez

Worktree dizini genelde: `../kiro2-worktrees/<feature-name>/`

## KIRO2 Use Case'leri

### Use Case 1: Experimental Algorithm Change

```
/worktree

Task: IRT discrimination parametresinin alt sınırını 0.2'den 0.15'e
düşürmenin golden dataset üzerindeki etkisini test et. Değişikliği:
- backend/app/services/irt/validator.py
- tests/irt/test_calibration_golden.py (expected values güncelle)

Worktree'de: branch adı "experiment/irt-discrimination-lower-bound"
```

Ana branch (main) bozulmaz, KIRO2 deploy devam edebilir. Experiment
başarılı → Apply. Başarısız → Discard.

### Use Case 2: Uzun Refactor

```
/worktree

Task: Tüm FastAPI endpoint'lerinde manuel Depends(get_current_user) +
ownership check pattern'ını custom dependency'ye çevir.

Etkilenen: backend/app/api/v1/*.py (~25 endpoint)
Branch: refactor/auth-dependency-consolidation
```

Sen bu sırada başka bir feature üzerinde ana branch'te çalışmaya devam
edebilirsin — worktree izole.

### Use Case 3: Risky Dependency Update

```
/worktree

Task: SQLAlchemy 2.0 → 2.0.35 güncelle. async_session API değişikliklerini
KIRO2 pattern'larına uygula. Tüm testlerin geçtiğini doğrula.

Branch: deps/sqlalchemy-2-0-35
```

## Worktree Yönetimi (Cursor Dışında)

Komut satırından görmek istersen:
```powershell
cd C:\Users\husey\kiro2
git worktree list
```

Manuel temizlemek (Cursor silmezse):
```powershell
git worktree remove ../kiro2-worktrees/experiment-xyz
git branch -d experiment/irt-discrimination-lower-bound  # opsiyonel
```

## KIRO2-Özel Uyarılar

### Database Isolation

Worktree'ler ayrı dizin ama **aynı PostgreSQL** kullanır (port 5434). Yani
worktree'de yapılan migration ana branch'i de etkiler. Strateji:

**Seçenek A — Shared DB (varsayılan)**:
- Hızlı, disk tasarruflu
- Migration yapma worktree'de — sadece kod değişikliği
- Data değişikliği varsa dikkat

**Seçenek B — Isolated DB (Docker override)**:
- Worktree'de `.env.local` ile farklı port (örn. 5435)
- `docker-compose.worktree.yml` ile kendi PG container'ı
- Schema experiments için güvenli

Experiment DB schema değişikliği içeriyorsa **Seçenek B** kullan.

### Redis/Elasticsearch

Aynı mantık — paylaşılan instance. Cache key namespace kullan:
```python
KIRO2_WORKTREE = os.getenv("KIRO2_WORKTREE", "main")
cache_key = f"kiro2:{KIRO2_WORKTREE}:questions:{id}"
```

### Node Modules

Her worktree kendi `node_modules/` ister (disk pahalı):
```bash
# Worktree'ye geçtikten sonra
cd ../kiro2-worktrees/experiment-xyz/frontend
npm install  # veya pnpm, hızlı
```

## Anti-pattern'lar

- **Tek satır fix için worktree** — overkill, ana branch'te yap
- **Aynı anda 5+ worktree** — context switching kabusu
- **Worktree'yi uzun süre açık tutmak** — stale hale gelir, merge conflict
- **Worktree'de production secret kullanmak** — .env kopyalamadan önce düşün

## Referans

- Cursor 3.0 changelog: Editor'den Agents Window'a taşındı
- Resmi doc: https://cursor.com/docs/configuration/worktrees
- `.cursor/commands/best-of-n.md` — worktree ile paralel model
