## Session Handoff — 2026-07-31 (S200 · eksiklik doğrulama turu)

**Branch:** feature/self-evolution-optimization
**Son commit:** (bu commit) — durum doğrulama belgesi
**Uncommitted:** yok

### ⚠️ ÖNCE BUNU OKU

**`docs/audits/2026-07-31_eksiklik_durum_dogrulamasi.md`** — 30-31 Tem denetiminin
113 bulgusunun + 29 Tem'in 12 kaleminin **doğrulanmış** durum tablosu ve kontrol listesi.
Bu belge, listedeki kalemler kapanana kadar **tek referans durum tablosudur**.
Görev eşlemesi §3.0'da (#460-#471).

### Yapılanlar

- 13 paralel ajan (11 küme + 2 skeptik tur) + 1 bağımsız ajan, **salt okunur**
  doğrulama: her verdict commit hash / `dosya:satır` / grep çıktısı ankrajı taşıyor.
  Oturum notları ve commit mesajları **kanıt sayılmadı**, iddia sayıldı.
- Sonuç: ✅16 KAPANDI · 🟡13 KISMEN · 🔴59 AÇIK · 👻8 FANTOM · 🔵17 CANLI-ÖLÇÜM.
  Açık P0 = 6 (+ 29 Tem'den K1 = 7).
- **Skeptik tur 2 "KAPANDI" verdict'ini düşürdü:** `ad1236cad` (Persona nullable —
  8 ekranın tamamı taranmamış, `DuelloPage` çıplak basıyor) ve `#444-fe`
  ("kod tarafı tam" çürüdü, ekleme yolu testsiz).
- **~20 YENİ bulgu** doğrulama sırasında çıktı (denetimde hiç yoktu): `Y1`-`Y4` ES,
  `F21-yeni`, `B4-x`, `N1`-`N5`, `YENI-1`…`YENI-7`, `F17b`, `DUELLO`.
- 12 görev açıldı (#460-#471), her biri belgenin bir bölümüne bağlı.

### En ağır bulgu (yeni, P0)

**K1 — `user_item_fsrs` tablosu yok ama `/api/v1/fsrs` canlıda kayıtlı.**
`c555a10f4b93_sync_db_changes.py:182` DROP ediyor; 27 Tem restore migration 6 tablo
getirirken bunu almadı. `fsrs_service.py`'deki **5 raw SQL sabiti** (42/81/119/129/153)
+ `app/api/fsrs.py:248` bu tabloya vuruyor, router `loader.py:63`'te kayıtlı.
`cat_session.py:1015` FSRS yazma hatasını `except Exception` ile yutuyor → tekrar
sistemi **sessizce** çökük olabilir. `K4.4` bunun neden fark edilmediğini açıklıyor:
mercy'yi "koruyan" 3 test servisi tamamen mock'luyor, metot silinse yeşil kalır.

### Fail Eden Testler

- Bu turda test KOŞULMADI (salt okunur ölçüm). Önceden bilinen: `tests/unit`
  27 FAILED + `pytest_asyncio` teardown deadlock (T1/T2, belgede açık).

### Engelleyiciler

- SMTP 6/6 env UNSET (#441, operatör) · `gh` CLI yok (#390/#436, operatör)
- 17 kalem canlı stack olmadan kapanamaz → **#460 canlı ölçüm turu ilk iş**

### Sonraki Adımlar (maks 5)

1. **#460** — 6 komutluk canlı ölçüm turu (§3.2). 4 P0'ı kesinleştirir, hepsi salt okunur.
2. **#461** — K1 `user_item_fsrs` restore (ölçüm `to_regclass` NULL derse).
3. **#463** — hızlı kazanç paketi (~1 saat, depo-kanıtlı). En acil kalem:
   `verification.md:101` preflight yolu `/api/v1/health` → `/health` — şu hâliyle
   **sağlıklı backend'i "çöktü" diye teşhis ettiriyor**.
4. **#462** — Golden Flow merge kapısı (şu an 429→skip, kapı fiilen boş).
5. **#464** — RLS; ama önce #460'ın 5. komutu (`organizations` count >1 ise derhal P0).

### Kararlar (gelecek session tekrar tartışmasın)

- **Fantom listesi (§5) 8 kalem — bunlarla UĞRAŞILMAZ.** Özellikle `#458a-2`
  (`test_turkish_nlp.py` mojibake'si kasıtlı fixture, düzeltmek testi kırar: `fixes` 3→0)
  ve `#447-schema` (`backend/schemas/persona.py` hiç olmadı, plan öyle diyordu).
- **§4'teki 16 kapanış yeniden açılmaz** — ankrajları var.
- `B4-x` Ek A'da P1 ölçüldü, kontrol listesinde P0 bloğuna **editoryal terfi** ile
  alındı (B4'ün yükselticisi). Bu ayrım belgede açıkça yazılı — severity de bir ölçümdür.
- 29 Tem'in üç sayısı (**6 mount / 53 yol / 28 eksik**) ölçüm aletinden yanlıştı;
  gerçek **9 / 70 / ~43**. Eski sayıları kullanma.
- Git Bash'te `git grep` deseni `/` içerirse MSYS yol dönüşümüne takılıp **var olan
  metne 0 isabet** döner. Kontrol kolu koymadan olumsuz bulgu raporlama.
