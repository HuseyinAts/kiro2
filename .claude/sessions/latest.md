## Session Handoff — 2026-07-30 (PC kapanması sonrası kurtarma + bekçi kök nedeni)
**Branch:** feature/self-evolution-optimization
**Son commit:** `c8792f022` fix(ci): reward-hacking bekçisi string literal ile kodu ayırt etmiyordu
**Uncommitted:** temiz · **PUSH EDİLDİ** — `23538d9fc..c8792f022` origin'de

### Bu oturum: yarım kalan #446 + bekçinin 3. ve 4. kusuru

PC kapandığında `backend/hooks/reward_hacking/` altında 3 dosya staged ama
commit'siz duruyordu (#446 `in_progress`). Zincir açıldıkça iki kusur daha çıktı.

**`c690854c5` — 3. kusur: uyarıda exit 1 push'u blokluyordu.**
a278ec1c8 severity'yi düzeltmişti ama `elif warning_count > 0: WARNING(1)` dalı
kalmıştı; pre-commit çerçevesi sıfır olmayan HER kodu başarısızlık sayar.
O commit'in mesajı "exit 1 (uyarı, geçiyor)" diyerek yanlış varsayımı belgelemiş.
Kanıt: gerçek kapı iki yönlü (advisory→Passed exit 0, `assert True`→Failed exit 2)
+ MUTASYON (elif geri konuldu → kapı `Failed exit code 1`).

**`20e5057e0` — bare-except testi yanlış gövdeyi ölçüyordu.**
Kırık DEDEKTÖR değil TESTTİ: gövdesi `except Exception: handle_error()`, yani ne
bare ne boş → 0 bulgu doğru cevaptı, REQ-6.4 hiç ölçülmüyordu. Dedektör yeteneği
5 vakayla ölçüldü (`_detect_bare_except` var ve çalışıyor). Sayı yerine KİMLİK
iddiası + negatif kontrol eklendi, mutasyonla kanıtlandı.

**`c8792f022` — 4. kusur (KÖK NEDEN, kullanıcı kararı): literal/yorum farkındalığı.**
20e5057e0 push'ta reddedildi: bekçi kendi fixture korpusunu ihlal sayıyordu
(12 critical). Kontrollü A/B: dosya BENDEN ÖNCE de exit 2 veriyordu → gizli tuzak.
Yeni `hooks/reward_hacking/literal_spans.py`: tokenize tabanlı literal+yorum span'i.
- `ast` DEĞİL çünkü `col_offset` UTF-8 **bayt** (Türkçe'de span kayar; ölçüldü:
  end_col 38 > satır 32 karakter)
- SATIR değil KARAKTER granülerliği (`assert True, "mesaj"` gerçek ihlaldir)
- Yorum bastırma DESEN BAZLI: desen `#` içeriyorsa (pragma/noqa/TODO) yorumda
  eşleşmesi meşru. Desen dağılımı ölçüldü.
- Yalnız `.py` (tokenize Python çözümleyicisi) · sözcüksel hatada FAIL-OPEN

**Körleşme kanıtı (250 gerçek test dosyası, filtre AÇIK vs KAPALI):**
1032→1016 bulgu, 726→717 critical. **16 bastırıldı, 16/16'sı literal içeren
satırda, ŞÜPHELİ 0, yeni eklenen 0.** Uygulama kodunda (80 dosya) delta 0.
Gerçek kapı 3 yönlü: korpus Passed · gerçek ihlal Failed exit 2 · yalnız-literal Passed.

### Fail Eden Testler
YOK. `pytest tests/hooks/reward_hacking/` → **96 passed, 0 failed** (88'den).
Paket bu oturumdan önce 1 kırmızıyla koşuyordu.

### Kapının zorunlu kıldığı önceden var olan düzeltmeler (hepsi A/B ölçüldü)
RUF012 ×5 · mypy `isinstance(result, Exception)`→`BaseException` (CancelledError
Exception alt sınıfı değil, latent TypeError) · N802 gerekçeli noqa · PTH108/110 ×4
→ pathlib · RUF034 ölü koşul (`".py" if ... else ".py"`) · **bandit B110 ×2 —
dedektörlerin KENDİ AST yolunda `except: pass` vardı, artık loglanıyor** ·
detect-secrets ×1 fixture (`pragma: allowlist secret`).

### KARAR BEKLEYEN (kullanıcı)
1. **`getMe()` — Persona'nın backend karşılığı HİÇ YOK** (#447). `api-client.ts:182`
   `live('/me')` çağırıyor, `/api/v1/me` 404. `/auth/me` yalnız `{id,email,ad,soyad,rol}`;
   `Persona` xp/seviye/seri/hedefUni/yksTarihi… istiyor. **31 dosya getMe kullanıyor**,
   `DuelloPage.tsx:155` `Promise.all` içinde → düello ekranı hata veriyor.
   Seçenekler: (a) agregasyon ucu, (b) istemcide birleştir, (c) hibrit. **Tasarım kararı.**
2. 12-oturum gözden geçirme raporu docs/audits altına yazılsın mı?

### Sonraki Adımlar (maks 5)
1. **Rebuild** — son 6 commit canlıda YOK (imajlar 29 Tem 13:30'dan):
   `docker compose build backend frontend celery-worker celery-beat && docker compose up -d`
2. **#449** bare-except politika çelişkisi: `_detect_bare_except` loglanan bare
   except'i de CRITICAL veriyor, oysa SAFE_PATTERNS onu güvenli listeliyor.
   Ölçüldü: 31 bare except, 9'u loglanmış (hepsi `_scripts/`), 18'i `pass`. P0 değil.
3. **`user_item_fsrs`** — tablo YOK, `/fsrs-review` rotası 500.
   `c555a10f4b93_sync_db_changes.py` upgrade()'i 145 DROP TABLE taşıyor. **1-2 gün**
4. **ES bypass (#433)** — mv kapısı 25.127, aktif havuz 110.858, ES 64.270 dok. **1 gün**
5. **route_contract_check.py** — mount'lu ekranların `live()` yollarını canlı openapi
   ile karşılaştıran pre-push kapısı; "backend düzeldi ama kullanıcıya ulaşmıyor"
   desenini (13 kez) kapatır. `if kontrol==0: exit 1` koy.

### Kararlar / Tuzaklar
- **`git stash pop` index'e DEĞİL çalışma ağacına koyar.** `--staged` ile gizlenip
  pop'lanan iş, sonraki `git checkout -- <dosya>` ile silindi. Kurtarma:
  `git fsck --unreachable` → "index on <branch>" commit'i → `git show <sha>:<yol>`.
  Mutasyonda artık `cp` yedeği kullan.
- **Biçimlendirici hook kullanılmayan import'u siler** → kullanımı ÖNCE yaz,
  import'u SONRA (3 kez tekrarladı).
- **A/B'yi GERÇEK yolda ölç**: `/tmp`'ye kopyalamak `per-file-ignores` ve dosya-adı
  bağımlı dedektörleri devre dışı bırakıp yanlış sonuç verdi (iki kez yakalandı).
- Bekçi gevşetilirken **iki yönlü + mutasyon + depo-geneli delta** zorunlu.
