# .cursor/ — KIRO2 Cursor Yapılandırması

Bu dizin, Cursor 3.x'in KIRO2 projesine özgü yapılandırmasını içerir.
Tüm dosyalar **git'e dahildir** ve takım arkadaşlarınla paylaşılır.

---

## 🏆 ÖNCE ŞUNU OKU — 3 Altın Kural

Günlük kullanımda en çok kaçırılan, en yüksek ROI'li 3 refleks. Bunlar
**Cursor Pro'nun değerini alıp alamayacağını** belirliyor. Detaylı açıklama:
[`GOLDEN-RULES.md`](./GOLDEN-RULES.md)

### 1. `Shift+Tab` = Kas Hafızası
> Karmaşık task'a başlamadan önce **daima** Plan Mode'a geç. Cursor ekibinin
> resmi #1 best practice'i. Plan'ı `.cursor/plans/`'a kaydet.

### 2. Chat'leri İsimlendir
> Her yeni chat için sağ tık → **Rename**. `20260420_konu_adı` formatı.
> 2 hafta sonra `@Past Chats` gerçekten işe yarar — isimsiz chat'ler kaybolur.

### 3. `/best-of-n` Kıt Kullan
> Sadece **gerçekten belirsiz** kararlar için (algoritma-kritik, güvenlik-kritik,
> mimari). Günlük CRUD'da Composer 2 yeter. Her model ayrı kredi = 4x maliyet.

**Refleks testi:** Bu 3 şey kas hafızasına girdiyse → Cursor Pro'nun gerçek
değerini alıyorsun. Girmezse → Copilot seviyesinde kullanıyorsun.

---

## 🗺️ Yapı

```
.cursor/
├── README.md                  ← Bu dosya
├── GOLDEN-RULES.md            ← 🏆 3 Altın Kural (source of truth)
├── BUGBOT.md                  ← BugBot PR review kuralları
├── MIGRATION-NIGHTLY.md       ← Senin yapacağın GUI adımları
│
├── rules/                     ← Otomatik yüklenen context kuralları
│   ├── 00-core.mdc            ← alwaysApply:true, her prompt'ta
│   ├── 10-backend.mdc         ← backend/**/*.py açıldığında
│   ├── 20-frontend.mdc        ← frontend/**/*.ts* açıldığında
│   ├── 30-migrations.mdc      ← alembic/versions açıldığında
│   └── 40-algorithms.mdc      ← FSRS/IRT/BKT/ai_ml açıldığında
│
├── commands/                  ← /slash komutları (19 adet)
│   ├── plan.md                ← Plan Mode workflow 🆕
│   ├── debug-mode.md          ← Debug Mode pattern 🆕
│   ├── best-of-n.md           ← Paralel multi-model 🆕
│   ├── worktree.md            ← İzole worktree 🆕
│   ├── analyze.md             ← Tek dosya deep analiz 🆕
│   ├── component.md           ← React component iskeleti 🆕
│   ├── checkpoint.md          ← Progressive context save 🆕
│   ├── ocr.md                 ← KIRO2 OCR pipeline 🆕
│   ├── commit.md              ← Conventional commit
│   ├── pr.md                  ← GitHub PR açma
│   ├── test.md                ← pytest (scope ile)
│   ├── deploy.md              ← staging/production
│   ├── review.md              ← son değişiklik review
│   ├── handoff.md             ← session kapatma
│   ├── compact.md             ← context özetleme
│   ├── api-endpoint.md        ← yeni FastAPI endpoint
│   ├── db.md                  ← Alembic migration
│   ├── status.md              ← sistem sağlık
│   └── lint.md                ← ruff + mypy + eslint
│
├── skills/                    ← Dinamik yüklenen 12 skill (Nightly)
│   ├── kiro2-skill-index/     ← Tüm skill/command dizini
│   ├── plan-mode/             ← Plan Mode rehberi 🆕
│   ├── design-mode/           ← Design Mode rehberi 🆕
│   ├── past-chats/            ← @Past Chats rehberi 🆕
│   ├── education-algorithms/  ← IRT/FSRS/BKT/ZPD
│   ├── irt-validation/        ← IRT 3PL detaylı
│   ├── kiro2-specific/        ← Platform kuralları
│   ├── turkish-nlp/           ← I/ı, UTF-8, Zemberek
│   ├── tdd-loop/              ← Self-correcting TDD
│   ├── yks-generator/         ← Soru üretimi
│   ├── code-review/           ← PR review protokolü
│   └── debug-bug/             ← INFRA-FIRST debug
│
├── plans/                     ← Plan Mode çıktıları
│   └── README.md              ← Plan yönetimi rehberi
│
├── hooks/                     ← Otomatik çalışan scriptler
│   ├── post-edit-ruff.py      ← .py save sonrası ruff format
│   └── guard-shell.py         ← rm -rf, DROP TABLE, force-push block
│
├── hooks.json                 ← Hook konfigürasyonu
└── mcp.json                   ← MCP server listesi (4 aktif)
```

🆕 = Nisan 2026'da eklenen (Cursor 3.x uyumu)

## 🎯 Kullanım Protokolü

### Günlük İş Akışı

1. **Basit task** → Direkt agent prompt yaz, Cursor modu seçer
2. **Karmaşık task (3+ dosya)** → `Shift+Tab` Plan Mode ⬅️ **ALTIN KURAL 1**
3. **Bug/failing test** → `/debug-mode` komutu
4. **Belirsiz yaklaşım** → `/best-of-n` komutu (kıt kullan) ⬅️ **ALTIN KURAL 3**
5. **UI iteration** → Integrated Browser + `⌘+Shift+D` Design Mode
6. **Session kapatırken** → `/handoff` komutu
7. **Commit sonrası** → `/checkpoint` komutu
8. **Yeni chat** → Sağ tık → Rename ⬅️ **ALTIN KURAL 2**

### Komut Seçim Matrixi

| Durum | Komut | Alternatif |
|---|---|---|
| Yeni feature | `/plan` | Shift+Tab |
| Bug reproduce + fix | `/debug-mode` | `/test` + iter |
| Belirsiz karar | `/best-of-n` | Manuel model switch |
| Risky experiment | `/worktree` | git branch |
| Tek dosya anla | `/analyze` | @file + soru |
| Yeni React component | `/component` | Manuel scaffold |
| Backend endpoint | `/api-endpoint` | Manuel |
| Alembic migration | `/db` | Manuel |
| Tests çalıştır | `/test` | Terminal |
| Lint + typecheck | `/lint` | Pre-commit |
| Commit oluştur | `/commit` | git commit |
| PR aç | `/pr` | gh pr create |
| Session kapat | `/handoff` | Manuel |
| Hızlı durum | `/status` | git status |
| Context özetle | `/compact` | Yeni chat |
| Progressive save | `/checkpoint` | Manuel |
| Production deploy | `/deploy` | CI/CD |
| Son değişiklik review | `/review` | Agent Review |
| OCR pipeline | `/ocr` | Manuel |

## 🔗 İlgili Dosyalar

### Senin için (insan)
- **`GOLDEN-RULES.md`** — 🏆 3 altın kural (günlük refleks)
- `MIGRATION-NIGHTLY.md` — GUI aksiyonları, kararlar, 6-testlik doğrulama
- `plans/README.md` — Plan Mode çıktıları yönetimi
- `/CLAUDE.md` — KIRO2 proje genel talimatları (üst dizin)
- `/.claude/rules/*.md` — 11 detaylı rule (Session 6-148 dersleri)

### Cursor AI için (runtime)
- `rules/00-core.mdc` — her prompt'ta aktif (Altın Kurallar dahil)
- `rules/10-backend.mdc` — backend dosyalarında
- `rules/20-frontend.mdc` — frontend dosyalarında
- `rules/30-migrations.mdc` — migration dosyalarında
- `rules/40-algorithms.mdc` — algoritma dosyalarında
- `skills/<n>/SKILL.md` — dinamik context yükleme
- `commands/<n>.md` — slash komut workflow

### Claude Code AI için (runtime, paralel ekosistem)
- `/.claude/rules/` — 11 rule
- `/.claude/skills/` — 24 skill (canonical versiyonlar)
- `/.claude/commands/` — 23 command
- `/.claude/hooks/` — 8 Python hook

## 🔄 Single Source of Truth

**Altın Kurallar** için canonical versiyon `GOLDEN-RULES.md`'de.
`00-core.mdc` ve bu README dosyası ona **referans eder** — bir kural
değişince sadece `GOLDEN-RULES.md`'yi güncelle.

**Skills** için canonical versiyon `/.claude/skills/<n>/SKILL.md`'de.
`.cursor/skills/` altındakiler **thin wrapper** — kritik bilgiyi inline
verir, derin içerik için `.claude/`'ya pointer eder.

**Rules** için canonical versiyon `.cursor/rules/`'dadır. `/.claude/rules/`
daha ayrıntılı, session-specific dersleri içerir.

**Commands** için her iki yerde paralel. Cursor tarafı Cursor-native syntax
(`/command`), Claude Code tarafı CLI-native.

## 🛡️ Güvenlik

- Hooks **otomatik** çalışır. `guard-shell.py` yasak komutları engelliyor:
  - `rm -rf /` ve variant'ları
  - `DROP TABLE`, `TRUNCATE`
  - `git push --force` main/master'a
  - `.env` leak
- MCP postgres **sadece localhost:5434** — production DB'ye bağlanmaz
- Privacy Mode `MIGRATION-NIGHTLY.md §2`'de anlatıldığı gibi ENABLE olmalı

## 🆕 Son Güncellemeler (Nisan 2026)

### Cursor 3.0 (2 Nisan) desteği
- Agents Window referansları
- Plan Mode workflow'u (Shift+Tab)
- Design Mode (⌘+Shift+D)
- `/worktree` ve `/best-of-n` komutları

### Cursor 3.1 (13 Nisan) desteği
- Tiled Layout referansı
- Voice Input (Ctrl+M)
- Element tree navigation Design Mode'da
- `@Past Chats` skill rehberi

### BugBot (8 Nisan) desteği
- Learned Rules awareness
- MCP support (Teams/Enterprise)
- KIRO2-critical rule tanımları

### Canvases (15 Nisan)
- Henüz proje-özel kural yok — ihtiyaç oldukça eklenecek

### 3 Altın Kural Kalıcı Yerleştirme (20 Nisan)
- `GOLDEN-RULES.md` oluşturuldu (source of truth)
- `00-core.mdc`'de agent refleks bölümü
- Bu README'nin üstünde vurgulu blok

## 📝 Değiştirmek İstersen

Bu dizindeki dosyalar **senin**. Değiştirmekte özgürsün. Ama bilmeni isterim:

- `GOLDEN-RULES.md` değişince → `00-core.mdc` ve README'deki referansı da güncelle
- `rules/*.mdc` değişince tüm KIRO2 agent'ları etkilenir
- `skills/*/SKILL.md` için canonical versiyon `.claude/skills/`'te — ikisini sync tut
- `hooks/*.py` otomatik çalışır, syntax error production'ı durdurur
- `mcp.json` değişince restart gerekir

Agent hatası gördüğünde:
1. Hatayı logla (`/handoff` veya manuel not)
2. İlgili rule/skill'i güncelle
3. Git commit: `chore(cursor): <rule/skill> güncelleme gerekçesi`

## 🆘 Sorun

- **Skills trigger etmiyor**: Nightly'a geçtiğini kontrol et (`MIGRATION-NIGHTLY.md §1`)
- **MCP kırmızı**: `cmd /c npx ...` manuel test yap
- **Hook fail**: `.cursor/hooks.json` JSON validate et
- **Rule uygulanmıyor**: glob pattern doğru mu, `alwaysApply` değeri doğru mu
- **Composer 2 yok**: Cursor 2.0+ versiyon gerekli

Detaylı troubleshooting: `MIGRATION-NIGHTLY.md §12`

## 📞 Referans

- Cursor 3 tanıtım: https://cursor.com/blog/cursor-3
- Best practices: https://cursor.com/blog/agent-best-practices
- Plan Mode: https://cursor.com/blog/plan-mode
- Composer 2: https://cursor.com/blog/composer-2
- BugBot: https://cursor.com/docs/bugbot
- Hooks: https://cursor.com/docs/agent/hooks
- Rules: https://cursor.com/docs/rules
- MCP: https://cursor.com/docs/mcp

Sorularda: hi@cursor.com veya https://forum.cursor.com
