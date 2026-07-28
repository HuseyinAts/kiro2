## Session Handoff — 2026-07-28 (blocker #1)

**Branch:** feature/self-evolution-optimization
**Son commit:** `65721e890` test(auth): şifre kurtarma paketi ortam değişkenine bağlıydı
**Önceki:** `9275f84b0` feat(auth): şifre kurtarma uçtan uca çalışıyor — blocker #1
**Uncommitted:** temiz · **Push: YAPILMADI** (2 commit bekliyor)

### Yapilanlar

**Blocker #1 (şifre kurtarma) KAPANDI — kod tarafı.**

- Başlangıç ölçümü: `auth.py:1463` sadece TODO (mail gitmiyor, "gönderildi" deniyor);
  `HesapKurtarmaPage` tasarımı bitmiş+testli ama **%100 mock** (kodu istemcide doğruluyor,
  3. adımda sunucuya hiç gitmiyor); **hiçbir rotaya bağlı değil** (iki giriş linki de ölü);
  `api-client` **var olmayan** `/auth/recover` uçunu çağırıyor.
- Akış: `forgot-password` → **`verify-reset-code` (YENİ)** → `reset-password`.
  Kod→token→şifre; çalışan `reset-password` ucuna DOKUNULMADI.
- Yeni: `backend/core/password_reset_codes.py` (hash'li 6 hane, atomik INCR sayaç,
  hesap başına saatte 3 kod).
- Tasarım incelemesinde **4 kendi hatam** düzeltildi: 6 hane global ad alanına düşemez;
  IP limiti kaba kuvvete yetmez (100 IP → %72) → hesap-bazlı limit; SMTP'yi `await`
  etmek **zamanlama üzerinden numaralandırma** açar → fire-and-forget; sayaç atomik.
- **Planda olmayan 4 bulgu:** `_get_token_store()` her çağrıda YENİ store üretiyordu →
  Redis'siz her kurulumda sıfırlama ZATEN ölüydü; ekran şifre kuralları sunucudan
  farklıydı (3 vs 5, `Guclu2024` yeşil ama sunucu red) ve **test bu yanlış sözleşmeyi
  sabitlemişti**; `/giris` ölü rota; "Panele dön" CTA'sı yalandı.

### Doğrulama

- unit **26** (13×2 backend: gerçek Redis + bellek) · integration **7** → **33/33**,
  iki ortam ve iki sırayla ayrı ayrı koşuldu.
- **mutasyon 6/6 yakalandı** (`backend/scripts/mutation_check_password_reset.py`).
  Tur GERÇEK boşluk buldu: iki yedekli kontrol testte birbirini maskeliyordu →
  beyaz-kutu testi + "ikisi birden" mutasyonu eklendi.
- frontend **8/8** (canlı-mod sözleşme testi 3 ucun yol+gövdesini sabitliyor), tsc 0.
- Rota 1249 → **1250** (tam +1), auth router yükleniyor.

### Fail Eden Testler
YOK. (`tests/fast/test_api_coverage_batch9.py` >600 s sürüyor — kendi yavaşlığı,
bu değişiklikle ilgisiz, koşturulmadı.)

### Engelleyiciler
YOK — ama özellik SMTP olmadan kullanıcıya mail göndermez (dev'de kod log'a düşer).

### Sonraki Adimlar (maks 5)
1. **Push** (2 commit bekliyor).
2. **SMTP kimlik bilgisi** `.env`'e (operatör) + `docker cp`/rebuild + gerçek zincir
   duman testi: kayıt → şifremi unuttum → gelen kutusu → yeni şifre → giriş. (görev #441)
3. **#433 ES reindex** — xfail(strict) mühürlü, reindex olunca paket kırmızıya döner.
4. **#6 roster yazma uçları** (~22h) · **#5 öğretmen/admin panoları mock**.
5. `.pre-commit-config.yaml`'a `types-redis` ekle → auth.py'deki mypy ignore'ları kaldır.

### Kararlar (gelecek session tekrar tartismasin)
- **6 haneli kod**, magic link DEĞİL (ekran onaylı tasarımı için; backend uyduruldu).
- **Numaralandırma > gönderim geri bildirimi**: kullanıcı mailin gidip gitmediğini
  ASLA öğrenmez; operatör log'dan öğrenir.
- **bandit B105 hook'ta atlandı** — ruff `S` seti aynı denetimi yapıyor, ÖLÇÜLDÜ
  (sahte `API_TOKEN` `backend/api/` altında S105 ile yakalandı). 3 B110 gerekçeli nosec.
- auth.py bu hook zincirinden geçemiyordu; 4 ihlal de ÖNCEDEN vardı, gerekçeli işaretlendi.
- **Kapsam dışı, ayrı iş:** sıfırlama sonrası oturum düşürme (refresh-token iptali YOK),
  e-posta case-sensitivity (login de öyle), reset token'ın düz metin saklanması.
