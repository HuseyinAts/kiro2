## Session Handoff — 2026-08-02 (S203)
**Branch:** feature/self-evolution-optimization
**Geri donus noktasi:** `git tag demo-baslangic-20260802`
**Demo:** 2 Agu 20:00 yatirimci sunumu — `docs/DEMO_RUNBOOK_20260802.md`

### Demo durumu (18:25 olcumu)
- **Demo yolu: 22 uc, 0 adet 5xx, 0 adet 4xx.** Iki prova ayni sonucu verdi
  (biri restart sonrasi = L1 soguk). Tum uclar <= 11 ms.
- **Golden Flow: 175 gecti / 1 dustu / 2 atlandi** (oturum basi 164/12/2).
- Prova komutu: `python backend/scripts/demo_yolu_probu.py --kisa` (exit 1 = 5xx var)

### Bu oturumda kapananlar
- **gf88** `295f34d9d` — `finally:` blogu None'a dokunuyordu; **28 cagri yeri**
  var olmayan oturum icin 404 yerine 500 veriyordu.
- **gf25** `9ea03d8c9` — UC SERI BAGLI sebep: DB DEFAULT yok · tz kaymasi
  (5 kolon, `coaching_events` kacan kardes) · VARCHAR kimlik `int` tiplenmis
  (8 istek 8 satir yazdi ve 8'i de 500 dondu).
- **gf130 + FSRS-P0** `ee6d7c820` — legacy flashcard katmani 410 Gone;
  `/fsrs/due` `varchar = uuid` yuzunden HIC calismamisti (frontend tekrar
  sayfasi). Bekci artik SQL'i canliya karsi KOSTURUYOR.
- **Cookie kimlik paritesi + L2 onbellek** `9035ad854` —
  (a) `learning_style` 7 ucu yalniz Bearer kabul ediyordu, frontend cookie
      kullaniyor -> tarayicida 401.
  (b) `json.dumps(..., default=str)` Pydantic modelini repr DIZESINE
      ceviriyordu -> L1 sicak 200 / L1 soguk + L2 sicak 500. "Tikla calisir,
      tekrar tikla patlar". `MultiLayerCache` 7 dosyada kullaniliyor.

### Fail Eden Testler
- `gf82` learning-style/behavioral-data — **1 kirik**. Iki ayri kusur:
  `users.id` gonderilince `can't subtract offset-naive and offset-aware
  datetimes`; gecerli `STU_` ile `ForeignKeyViolationError`. Cikarma satiri
  BULUNAMADI -> kok neden ILAN EDILMEDI. Demo ekraninda degil (arka plan
  telemetrisi), runbook'ta GOSTERME listesinde.

### Sonraki Adimlar (maks 5)
1. `GF-K6` gf82 — iki kusur, ikisi de ayri: datetime naive/aware + FK ihlali
2. `FSRS-K1` — `/recommendations` `/statistics` `/study-sessions/start` 500;
   sonuncusunu **frontend cagiriyor** (`useLearningPath.ts:395,412`) -> urun karari
3. `GF-K4`/`GF-K5` — 87 tablo metadata'da yok / 67 tablo DB'de yok
4. FAZ 0 kalani: `A.3` -> `A.5` -> `A.6` -> `A.6b`
5. `#468` CI tetikleme (dal master'dan 334+ commit onde)

### Kararlar (gelecek session tekrar tartismasin)
- **Bearer'la olcum tarayiciyi TEMSIL ETMEZ.** Frontend `/auth/login/secure`
  ile cookie kullaniyor. Demo/e2e olcumleri cookie ile yapilir.
- **"Tablo var" bir VEKIL olcumdur.** Sema bekcisi sorguyu canliya karsi
  KOSTURUR; tip uyumsuzlugu ad kontrolune yapisal olarak gorunmez.
- **Tek sebep varsayma.** gf25'te uc, gf82'de iki sebep seri bagliydi.
- **Onaysiz veri silme yok.** FK dogrulanamiyorsa `NOT VALID` ile ekle.
- **Olcum aletini once dogrula.** Bu oturumda 6 "bulgu" alet hatasi cikti
  (4 yanlis yol/metot · `users.id` vs `STU_` · `::text` cast'i parametre sanma).
- **`git checkout HEAD --` commit'siz fix'i siler** — mutasyondan ONCE commit.
- **`MSYS_NO_PATHCONV=1`** olmadan `docker exec ... /app` Windows yoluna cevrilir.
- **Pre-commit ruff surumu yerelden FARKLI bicimlendiriyor** — hook ciktisini
  esas al, uzerine yerel `ruff format` calistirma (dongu olur).
