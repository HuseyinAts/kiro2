# Sır Tarama Bekçisi — Runbook

**Son doğrulama:** 27 Temmuz 2026
**Enforcement:** `backend/tests/test_secret_scanning_guard.py` (14 test)

---

## Neden bu doküman var

Depoya **11 anahtar sızdı** (10 Google + 1 HuggingFace). Sızıntı "birinin
dikkatsizliği" değildi — **üst üste binmiş dört sessiz kusur** vardı ve
hiçbiri hata vermiyordu:

| # | Kusur | Etki |
|---|---|---|
| 1 | `core.hooksPath = nul` (Windows NUL aygıtı) | **Hiçbir git hook'u çalışmıyordu.** Koşulsuz `exit 1` yapan bir pre-commit hook'u bile commit'i bloklamadı (canlı deneyle ölçüldü). Git hook bulamayınca SESSİZCE devam eder. |
| 2 | Kurulu hook `backend/.pre-commit-config.yaml`'ı çağırıyordu | O config'de sır taraması **hiç yok** — ne `detect-secrets` ne özel dedektör. |
| 3 | Kök config `default_language_version: python3.11` pin'liyordu | O yorumlayıcı makinede yok (PEP-514 registry kaydı bozuk) → kök config'i kullanan her koşum `failed to find interpreter` ile çöküyordu. Muhtemelen 2 numaranın sebebi de bu. |
| 4 | Dedektörün kendi kusurları | `types: [python]` → sadece `.py` taranıyordu; `stages: [commit]` pre-commit 4.x'te geçersiz ad; ve dedektör **yorum satırlarını atlıyordu** → `# GEMINI_API_KEY=AIza...` taramadan geçiyordu. |

Ayrıca dedektörün kendisi bir güvenlik kusuru taşıyordu: bulgu önizlemesi
satırın ilk 60 karakterini **olduğu gibi basıyordu**, yani sır tarayıcısı sırrı
stdout'a / CI log'una sızdırıyordu.

---

## Bugünkü durum — kanıt

Sentetik bir Google API anahtarı (`AIza…`, 39 karakter) içeren dosya
stage'lenip **gerçek `git commit`** denendi. Karışıklık olmasın diye diğer tüm
hook'lar `SKIP` ile devre dışı bırakıldı:

```
check for merge conflicts................................................Passed
check for added large files..............................................Passed
detect private key.......................................................Passed
check for case conflicts.................................................Passed
Ruff linter.............................................................Skipped
...
KIRO2 Secret Detector....................................................Failed
- hook id: kiro2-secret-detector
- duration: 0.11s
- exit code: 2

[SECRET DETECTED] docs\runbooks\_leak_probe.md:4
  Type: Google API Key
  Match: AIza…00 (len=39)
============================================================
[ERROR] 1 hardcoded secret(s) detected!
============================================================

>>> COMMIT BLOKLANDI — HEAD degismedi (9ff825023)
```

Dikkat: `Match:` maskeli. Tarayıcı çıktısı sırrın kendisini içermiyor.

---

## Tasarım kararı: iki katmanlı desen seti

Bloklayan bir kapıda **kesinlik, kapsamdan önce gelir**. Kurt masalı anlatan
bekçi kapatılır — bu depoda tam olarak öyle olmuş.

| Katman | Davranış | İçerik |
|---|---|---|
| **BLOCKING** (exit 2) | Commit'i durdurur | `AIza…`, `hf_…`, `sk-ant-api…`, `sk-proj-…`, OpenAI `sk-…`, `ghp_…`, `xox[baprs]-…`, KIRO2'ye özgü sızmış literaller |
| **WARNING** (exit 0) | Rapor eder, durdurmaz | jenerik `password = "..."`, jenerik `api_key = "sk-..."` |

Gerekçe — depodaki tüm izlenen dosyaların taraması:

```
toplam 110 bulgu
  99  jenerik password  <- test fixture'ı / yerel DSN — GÜRÜLTÜ
   4  KIRO2 DB parolası (literal)
   3  Google API anahtarı  <- ...XX/YY/ZZ ile biten doküman örneği
   2  jenerik api_key
   1  KIRO2 JWT secret
   1  OpenAI anahtarı  <- sk-abc...78, örnek
```

Sızan 11 anahtarın ikisi de kesin formatlı. Jenerik parola sezgiselinin o
sınıfa katkısı **sıfır**, gürültüsü 99.

---

## Meşru dokümantasyon örneği nasıl yazılır

Dosya bazlı beyaz liste **kullanma** — bir dosyayı topluca muaf tutmak, o
dosyaya sonradan giren gerçek anahtarı da muaf tutar. (`CLAUDE.md` böyle
muaftı; içine konan sentetik anahtar taramadan geçiyordu.)

Satır sonuna işaret koy:

```python
api_key = "AIzaSyEXAMPLE..."  # pragma: allowlist secret
```

`detect-secrets` ile aynı sözdizimi, iki araç tek işareti paylaşır.

---

## Yeni makinede / yeni klonda kurulum

```bash
cd C:\Users\husey\kiro2
git config --get core.hooksPath          # BOŞ olmalı. "nul" ise:
git config --unset core.hooksPath
pre-commit install -c .pre-commit-config.yaml --overwrite
```

Doğrula:

```bash
cd backend && python -m pytest tests/test_secret_scanning_guard.py -q
# 14 passed bekleniyor
```

`test_git_hooks_are_not_disabled` ve `test_installed_hook_points_at_root_config`
kurulumun bozulduğunu yakalar.

---

## Bilinen sürtünme (kapı açıldığında ortaya çıkan borç)

Kök config artık gerçekten koştuğu için uzun süredir koşmamış hook'lar da
devreye girdi. Bir commit `ruff` / `trailing-whitespace` / `mixed-line-ending`
tarafından bloklanabilir. **Bu bekçinin bozulması değil, borcun görünür
olmasıdır.** Sır taraması dışındaki bir hook engel oluyorsa ya düzelt ya da
o commit için hedefli `SKIP=<hook-id>` kullan — `--no-verify` KULLANMA, o
sır taramasını da kapatır.

---

## İlişkili

- `backend/hooks/secret_detector.py` — desenler ve maskeleme
- `backend/tests/test_secret_scanning_guard.py` — enforcement (14 test, mutasyon-doğrulamalı)
- `.pre-commit-config.yaml` — kök config (sır taraması BURADA)
- `.claude/rules/security.md` — sır yönetimi kuralları
- `.claude/rules/testing.md` #15 — "öğrenilen dersleri ENFORCE et"

> **Anahtar rotasyonu ayrı iştir.** Geçmiş temizliği (git purge) ifşayı geri
> almaz; sızmış 11 anahtar sağlayıcı konsollarından döndürülmelidir.
