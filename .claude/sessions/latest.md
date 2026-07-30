## Session Handoff — 2026-07-30 05:57
**Branch:** feature/self-evolution-optimization
**Son commit:** `38c116764` docs(rules): 30 Tem hatalarından 4 kalıcı kural
**Uncommitted:** temiz · origin ile 0 fark (8 commit push edildi: `c690854c5`..`38c116764`)

### Yapilanlar
- `backend/hooks/reward_hacking/hook_manager.py:251` — uyarı dalı kaldırıldı; exit 1
  push'u blokluyordu (pre-commit sıfır olmayan her kodu fail sayar). `c690854c5`
- `backend/tests/hooks/reward_hacking/test_detectors.py:315` — bare-except testinin
  gövdesi `except Exception:` idi, REQ-6.4 hiç ölçülmüyordu. `20e5057e0`
- `backend/hooks/reward_hacking/literal_spans.py` (YENİ) — tokenize tabanlı
  literal+yorum span'i; `base_detector.py:198` + 3 dedektörde 6 tarama noktası.
  `ast` değil: `col_offset` UTF-8 bayt (Türkçe'de kayar). `c8792f022`
- `.../test_string_literal_immunity.py` (YENİ, 13 test) — 8 literal/körleşme +
  3 yorum kuralı + 1 `CancelledError` + 1 xfail(strict). `c8792f022`+`eddd419a1`
- `backend/hooks/reward_hacking/base_detector.py:105` — #451 ölçümü yorum olarak
  yazıldı (kod değişmedi): kaba docstring sayacı yük taşıyor, kaldırılamaz. `19e317549`
- `.claude/rules/audit-methodology.md` + `verification.md` — 4 kalıcı kural. `38c116764`
- Docker rebuild: 4 imaj, `down` + `up -d`, 5/5 healthy. `553b60e09`

### Fail Eden Testler
YOK. `pytest tests/hooks/reward_hacking/ tests/unit/test_hooks/` → **279 passed,
1 xfailed** (xfail = #451 açığının yaşayan işaretçisi, strict).

### Engelleyiciler
- SMTP kimliği yok (3 compose'da da) → şifre kurtarma canlı çalışmaz (#441) ·
  `user_item_fsrs` tablosu YOK → `/fsrs-review` rotası 500

### Sonraki Adimlar (maks 5)
1. **#453 bekçi desen kalibrasyonu** — mock/hardcoded idiyomları CRITICAL sayıyor
   (231 ölçüldü). Sıra: kalibrasyon ÖNCE, docstring dalı kaldırma SONRA.
2. **#447 `getMe` tasarım kararı** — 31 dosya kullanıyor, `/api/v1/me` 404,
   `DuelloPage.tsx:155` hata veriyor. Fix değil, karar: agregasyon ucu / istemcide
   birleştirme / hibrit.
3. **#452** `.claude/hooks/pre-tool-use.py` literal farkındalığı (fixture yazmayı bloklıyor)
4. **#449** bare-except politika çelişkisi (9 loglanmış bare except, hepsi `_scripts/`)
5. **#433** ES indeksini `v_safe_for_beta`'dan kur (ES kapıyı tanımıyor)

### Kararlar (gelecek session tekrar tartismasin)
- **#451 UYGULANMADI, ölçümle**: yorum dalını kaldırmanın kazancı 250 dosyada +0;
  docstring dalını kaldırmanın bedeli +231 CRITICAL (sıradan test deyimleri).
  Hatalı heuristik bekçiyi kullanılabilir tutuyor. Asıl iş kalibrasyon (#453).
- **Yanlış davranış teste çivilenmez**: bilinen açık `xfail(strict=True)` ile
  işaretlenir; kapanınca test kırmızıya döner ve güncellemeye zorlar.
- **Geri alım**: `git checkout HEAD -- <yol>` + `git status` (aynı komutta doğrula).
  `cp /tmp` YASAK — bash `/tmp` (MSYS) ≠ Python `/tmp` (`C:\tmp`), veri kaybı oldu.
- **Commit mesajı**: `` ` ``/`$` içeren mesajlarda `-F <dosya>`; inline `-m`
  komut ikamesi tetikleyip mesajı sessizce bozdu.
- **Ortak tabana dokununca** (`base_detector` = 8 dedektörün yolu) tüketici test
  paketi de koşulur: `tests/unit/test_hooks/` (179 test).
