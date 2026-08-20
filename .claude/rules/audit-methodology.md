---
name: audit-methodology
description: Ölçüm disiplini — varsayımı ölçümden ayırma kuralları
---

# Ölçüm Disiplini

> **Her oturumda bağlama yükleniyor** (`paths:` frontmatter'ı yok). Bu yüzden yalnız
> **kural** tutar. Her kuralın arkasındaki vaka, ölçüm çıktısı ve tarih:
> **`docs/dersler/2026_olcum-hatalari-arsiv.md`** (1.022 satır, birebir korundu,
> 20 Ağu 2026'da ayrıldı). Bir kuralı tartışmaya açmadan önce arşivdeki vakasını oku —
> çoğu, tam tersi savunulduğu için oraya yazıldı.

## Altın kural

**İddia ≠ ölçüm.** Bir şeyi raporlamadan önce sor: *bu iddianın yanlış olduğunu
gösterecek tek bir ölçüm var mı?* Varsa **onu yap**.

Bu, sanılandan fazlasını kapsar. Hepsi bu depoda en az bir kez yanlış çıktı:

| İddia türü | Onu çürütecek ölçüm |
|---|---|
| **Sayı** ("61K garble var") | Etiket satır-bazında sorgulanabiliyor mu? Sorgulanamıyorsa o sayı tahmindir |
| **Severity** ("P0/acil", "güvenli", "temiz") | Sızmış anahtar hâlâ geçerli mi? Kapı gerçekten blokluyor mu? Atlatmayı DENE |
| **Kök neden** ("sebebi şu dal") | Y'yi **kaldır** — X kayboluyor mu? Kaybolmuyorsa Y sebep değil (veya tek sebep değil) |
| **Kalan iş** ("N erişim kaldı") | Sayaç AST tabanlı mı? Alias/yorum/kwarg görüyor mu? |
| **Fix'in değeri** | Kaç bulgu değişiyor? **+0 ise fix yapılmaz** — hole'un varlığı kapatmak için gerekçe değil |
| **Kapsam** ("bu kural şunu kapsar") | Kaç satıra dokunuyor? Bir kural 4.419'un **27**'sini kapsıyordu ve uyardığı kusuru üretiyordu |

## Ölçüm aletini doğrula

**Kontrol kolu bilinen sonucu vermiyorsa ölçüm bitmiştir — bulgu değil, alet arızası vardır.**

- **Yanlış-SIFIR** bir ilerleme sayacında tek kabul edilemez hata türüdür: işi sessizce bitmiş gösterir.
- Aracın çıktısını okumak, aracın **girdiyi değiştirmediği** anlamına gelmez (`pre-commit run` auto-fix yazar).
- Bir aracın **yokluğu** değil **yavaşlığı** da sessiz boşaltır: `timeout=3`'e karşı **7,11 sn** soğuk `bash` spawn, hook'un tüm alanlarını boşalttı (20 Ağu 2026).
- Beklenmedik "0 test / 0 bulgu" → önce **`pwd`**. Kabuk `cd`'si kalıcıdır.
- Boru hattında **`$?` son halkayı** ölçer: `git commit … | tail` sonrası `$?` **0** görünür ama commit düşmüş olabilir. Çıkış kodunu ayrı değişkene al.
- Bir deseni **anlatan yorum**, o deseni **içerir** — dedektör onu kusur sanar. Kusur aramadan önce yorumları at; bozuk görünen veriyi düzeltmeden önce **tüketicisine** bak (bir test onu *onarmak* için mi kullanıyor?).

## Örneklem ve rapor

- Audit örneği üretirken metni **TRUNCATE ETME** (yapay kesik, OCR cut-off sanılır). Örneklem boyutunu düşür.
- Truncate şartsa `…[TRUNCATED]` + `original_len` ile **açıkça işaretle**.
- Şüphe varsa **DB'den re-verify** et (`RIGHT(text, 50)`), gözle tahmin etme.
- Örneklem istatistiğini **evren-bazlı** SQL ile doğrula. Tutmuyorsa bias veya ölçüm hatası var — RESULT'a yaz.
- Her RESULT başında **Methodology**: örnek SQL · N · seçim/seed · truncation · reproducible mi.
- **Hacim bir vekil ölçümdür.** 27.073 satır her invaryantı geçti, içerik **0/40** çıktı. Havuza dayanan işi "değer üretiyor" saymadan önce **örneklemi OKU**.
- **Tek değerli bayrak yargı değil varsayımdır.** Dağılımı sorgula; tek değer = o yargı hiç yapılmadı.
- **"Sürükleme var/yok" EVREN-BAĞIMLI bir iddiadır.** Hangi evrende ölçtüğünü YAZ.

## Metrik / ucuz filtre uygulamadan önce

İki zorunlu test — geçemeyen metrikle **aksiyon alma**:

1. **Bilinen-iyi vs bilinen-kötü** ayrımı yapıyor mu? Medyanlar çakışıyorsa metrik kördür.
2. **Sentetik bozma**: temiz veriye bilinen hata enjekte et, skor yükselmeli.

Ucuz deterministik filtreyle **içerik silerken** (Türkçe STEM'de yanlış-pozitif riski yüksek):

- **Pozitif kanıt** ara, yokluk değil ("İngilizce kelime VAR" ≠ "Türkçe karakter yok").
- Türkçe karakter (ç/ğ/ı/ö/ş/ü) içereni silme listesinden **zorunlu çıkar**.
- **Yargılanmamışı silme.** `unverified` = incelenmemiş; silmek varsayımdır. Yalnız **yargılanmış-kötü** silinir.

## Şema göçü / sorgu değişikliği — 4 ölçüm (biri atlanırsa kusur sessizce girer)

1. Sorguyu **derle** (`compile(dialect=postgresql, literal_binds)`) — bazıları çalışma anında değil **kurulurken** patlar.
2. Kartezyeni **`stmt.get_final_froms()`** ile say — metinsel virgül kontrolü alt-sorguya takılır.
3. **WHERE iddiasını yalnız `stmt.whereclause`'da ara** — `select(Entity)` tüm kolonları SELECT'e koyar, filtre silinse bile dize tam SQL'de durur (mutasyon hayatta kalır).
4. **Gerçek modele** karşı test yaz. `sys.modules` stub'lı test kırık kodda da yeşil kalır.

Yan kurallar:

- Eager-load gerekliliğini sorgudan değil **tüketiciden** ölç: `select(Model.alan, …)` `Row` döner (risk yok); `select(Model)` + delege okuma async'te `MissingGreenlet`.
- `.select_from()` **koşulludur**: SELECT listesi split-only ise zorunlu; `Model.id` de içeriyorsa süs (çivilenemez ağırlık ekleme).
- Sayaç **sınıf düzeyini** sayar, **örnek düzeyini** görmez → çıktısı **alt sınırdır**.
- `server_default` beyanı DDL'de **olmayabilir** — `information_schema.column_default` + kolonu **atlayan** INSERT ile ölç.
- Alan taşırken biçimlendirici kullanılmayan import'u siler: **kullanımı önce yaz**, import'u sonra doğrula.
- Uyumluluk katmanı (shim/strangler) kör noktasında **sessiz varsayılan dönmemeli**, yol gösteren hata vermeli — yoksa borç ölçülemez olur.

## Test, mutasyon, bekçi

- **Test paketi de bir dilim ölçer.** Tek parametreyle (`MATEMATIK`) yazılmış test başka dalı (`TURKCE`) hiç koşmaz.
- **"Göç ettin mi" ≠ "koruduğun mu"**: bir filtreyi taşıyan test, filtrenin **hâlâ etkili** olduğunu da assert etmeli (koşul **sayısı**, "sorgu kuruldu" değil).
- **Mutasyon bir alettir ve o da yanılır:** `error` ise ölçüm **geçersiz** (syntax bozulmuş) · **hangi assert** öldürdü ve **tek başına** yük taşıyor mu? · mutasyon kümesinin **dokunmadığı dal = ölçülmemiş dal** · ankraj **tekil** mi? · mutasyonun **uygulandığını bağımsız ölç** (uygulayan komut sessizce reddedilmiş olabilir) · **commit SONRASI** koş — commit'siz iş mutasyona sokulmaz, geri alım onu siler.
- **"Bu assert gereksiz" de bir iddiadır** — silmeden önce onu **tek başına** öldüren bir mutasyon ara.
- **Bekçi haklı olabilir.** "Hep fantom" bir ölçüm değil. Ayırt edici tek soru: **bulgu benim bu turda yazdığım satırda mı?** Evetse SKIP tartışması yok.
- **Bir kez geçmiş olmak güvenlik kanıtı değildir** — dedektör o biçimi görmemiş olabilir. Sır tespiti `grep` ile doğrulanır.
- **Yorum CI'da düşmez.** Mesaj kaybolur → yorum silinir → yalnız **test** kalır. Yük taşıyan bilgiyi teste yaz.

## Kapı (pre-commit) ve commit

- Kapıyı **depo kökünden** ölç (`cd <root> && pre-commit run --files …`); alt dizinden koşmak **farklı config** yükler.
- **Aynı aracın üç sürümü var ve kapıyı en eskisi tutuyor** (kabuk + PostToolUse `ruff 0.14.13`, kapı **0.7.1**). "Biçim temiz" demeden önce **kapının sürümüyle** biçimlendir ve **sabit noktayı** doğrula. Kural iki yönde de ısırır: 0.7.1'de var olan `UP038`, 0.14.13'te **kaldırılmış**.
- **`--amend` sessizce iptal olur** ve `git log` aynı hash'i gösterir → **hash'in değiştiğini** ölç.
- **Exit 0 + yeni hash ≠ her şey girdi** → `git show --stat HEAD` ile **ne girdiğini** oku. Yarım commit'in artığı takipsiz gürültüde kaybolur; oturum sonunda **takipli-kirli** sayısını ölç.
- **SKIP bir muafiyet değil, ölçülmüş bir ertelemedir.** Üçü de gerekli: (a) benim kodum temiz mi — kapının sürümüyle, (b) kontrol kolu — `git show HEAD:<dosya>`'da da var mı, (c) yaygınlık — sistemik mi. Ve SKIP **ayrı bir açık iş** olarak kaydedilir.
- Kirli ağaçta **pathspec'siz `git stash` kullanma** → `git stash push -- <dosya>`.
- Geçici düzenleme/mutasyonda **`read_bytes`/`write_bytes`** kullan: `write_text` CRLF'i çevirir ve `git status` dosyayı yanlışlıkla kirli gösterir. Aynı sebeple **çok satırlı ankraj CRLF içermeli** (LF ankraj CRLF dosyada eşleşmez).
- Geri alım bir iddiadır: `git checkout HEAD -- <yol> && git status --short` → çıktı **boş** olmalı.
- **"Ağaç kirli" süpürme gerekçesi değildir** — `git stash push -- <dosya>`yı DENE. Süpürme kaçınılmazsa davranış değiştirip değiştirmediğini **ölç** ve commit mesajına yaz.

## Ortam (Windows / Git Bash)

- Git Bash **mutlak yolu yeniden yazar**: `docker exec … /app/x` → `C:/Program Files/Git/app/x`. Container yolu içeren komuttan gelen "dosya yok" önce **yol dönüşümü** kontrolü ister → `MSYS_NO_PATHCONV=1`.
- NTFS'te Türkçe `İ/ı/ğ` **NFC-NFD** farkı: bash `[ -f ]` var olan dosyaya "yok" der. Aynı soruyu **ikinci bir araca** sor (container'dan `os.path.isfile`).
- Türkçe içerikli SQL: `psql -f dosya.sql` (inline `-c` `0xfe` hatası verir).
- Bu depoda `git status` takipsiz taramayla **>60 sn** (528.651 crop PNG); `--untracked-files=no` ile **0,09 sn**.
- Test DSN'i `DATABASE_URL`'e güvenemez — sessizce **sqlite'a düşer**. Postgres olmayan DSN'i **reddet + skip**.
- **Grafiği sorduğun derleyici kadar görürsün**: `tsc` (tip) ≠ `vite build` (paketleyici) ≠ çalışma zamanı. Biri "temiz" dediğinde bitmiş sayma.

## İlişkili

`systematic-debugging.md` (phantom filtresi) · `debugging-first.md` (root cause tablosu) ·
`verification.md` (doğrulama standartları) · `testing.md` (#31 servis sızıntısı) ·
`.claude/lessons/ders_kaydi.yaml` (ders yaşam döngüsü) ·
**`docs/dersler/2026_olcum-hatalari-arsiv.md`** (vaka kanıtları + tarihli hata tablosu)
