## Session Handoff — 2026-07-30 (akşam)
**Branch:** feature/self-evolution-optimization · **Son commit:** `d9e5c8f58`
**Push:** `688e42377..d9e5c8f58` edildi, origin SENKRON · **Uncommitted:** temiz

### Kapatilanlar (hepsi ölçümle, hepsi push'lu)
- **#453** `DetectorConfig.severity` varsayılanı **None**. Kaldırma deneyi:
  `bool(DetectorConfig())` True, `config=None` bile model üretiyor → `default_severity`
  dalına ulaşan **hiçbir girdi yoktu**, iki dedektörün `=WARNING` beyanı ölüydü.
  250 dosya: CRITICAL **474→64**, bloklayan dosya **68/250→19/250**, toplam bulgu 727=727
  (susturma yok). 15/15 mutasyonla çivili. `b9d4fb967`
- **.gitignore ankraj** `models/`→`/models/`: ankrajsız hali 3 paketi izlemiyordu; taze
  worktree'de `ModuleNotFoundError ...reward_hacking.models` → **bekçi hiçbir makinede
  koşamıyordu**. +10 dosya, çöp 0.
- **#455** `@patch(...)` çift sayımı (zaten `ast.Call`, ayrı `decorator_list` döngüsü
  tekrar sayıyordu). 2 dekoratörlü dosyada **%200** ölçüldü. 11 test, 10'u çivili. `5cede288a`
- **#454** ölü `reward_hacking_config.yaml` silindi — yüklemek **no-op** (64/658/722 =
  64/658/722, küme farkı 0). Görev notundaki "min_confidence 0.8→0.7 bulguyu artırır"
  tahmini YANLIŞ çıktı. `a9429896b`
- **#457** `collect_files`→`sorted()`; **6 seed → 5 farklı sıra** ölçüldü. Sıralama BOM'lu
  dosyayı dilime soktu → `--json` hiç ayrışmıyordu → 8 uyarı `stderr`'e. 4/4 çivili. `0b7c6b6ee`
- **#449** iki yönlü çelişki: loglu bare→CRITICAL (yanlış-poz), `pass`+yakın log→INFO
  (yanlış-**negatif**). Log taraması artık handler gövdesiyle sınırlı; loglu bare→WARNING.
  5/5 çivili; 31 bare except var, üretimde 0. `d9e5c8f58`
- **#456** 2 BOM silindi + `test_source_hygiene.py` bekçisi. **BOM gerçek bir ihlali
  örtüyormuş**: kalkınca `except Exception: pass` çıktı (exit 2), düzeltildi. `36d2b4685`
  Ayrıca `backend/backend/` **6592 izlenen dosya** takipten çıktı (6590'ı BOŞ metrics
  JSON, 9.8 MB, 0 referans) + ankrajlı ignore. `9d373730c`

### Fail Eden Testler
YOK. 3 paket (reward_hacking + test_hooks + source_hygiene) → **316 passed, 1 xfailed** (xfail=#451); 35 yeni test.

### Sonraki Adimlar (plan sırası korunuyor)
1. **#452** `.claude/hooks/pre-tool-use.py` literal farkındalığı yok (ölçüldü: 0 referans).
2. **#447** `getMe` — 40 dosya, `/api/v1/me` **404 doğrulandı**. Karar + uygulama.
3. **#444** Öğretmen Öğrenciler UI (backend hazır) · **#458** 2 temizlik adayı ·
   **#433** ES index (docker ps'te **elasticsearch YOK** → fiilen bloklu).
**Operatör-bloklu:** #270 · #390 · #436 · #441 · #445.

### Kararlar (tekrar tartışılmasın)
- **Mock/hardcoded WARNING'dir** — hardcoded dedektörü `_is_test_file` kapısı yüzünden
  üretim kodunu HİÇ taramıyor (0 bulgu), yani CRITICAL tek sır yakalamıyordu.
- **Ruff SÜRÜM ÇATIŞMASI**: pre-commit **0.7.1** pinli, yerel **0.14.13**. 0.7.1 UP038
  istiyor, 0.14 kaldırmış → per-file-ignore. Uzun `assert X, (f"...")` satırını ikisi ZIT
  biçimlendirip commit'i salınıma sokuyor → mesajı ayrı değişkene al.
- **`cmd | grep | tail && rm` KALINI YASAK**: `&&` git'in değil **tail'in** çıkış kodunu
  görür; commit mesajı dosyası 3 kez silindi. Doğrusu: `oncesi=$(git rev-parse HEAD)` …
  `[ "$oncesi" != "$sonrasi" ]` ile HEAD'in kıpırdadığını doğrula.
- **Daima mutlak `cd`**: `cd backend` iki kez koşulunca `backend/backend`e kayıyordu
  (5 kez oldu, 3 ölçümü geçersiz kıldı). O dizin artık silindi ama kural kalıcı.
- **`ruff format <dizin>` YASAK**: 5 ilgisiz dosyayı (306 satır) biçimlendirdi, geri alındı.
