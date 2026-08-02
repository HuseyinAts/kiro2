## Session Handoff — 2026-08-02 (S203)
**Branch:** feature/self-evolution-optimization
**Son commit:** `ee6d7c820` fix(fsrs): /due tip uyumsuzlugu (YENI P0) + gf130 410 Gone
**Uncommitted:** temiz · **push EDILMEDI** (3 commit yerelde)

### Yapilanlar — Golden Flow 3 kirik -> 1, listede olmayan 1 P0 kapandi
- **gf88** `295f34d9d` — `core/osym_exam_engine.py:1080` `finally:` blogu kosulsuz
  `session.status` okuyordu; uc katman (L1/L2/L3) da bos donerse `session` None
  kalir. `finally` icindeki istisna NORMAL DONUSUN YERINE GECER -> fonksiyon
  None dondurEMEZ, caginin `if not session_data: 404` dali OLU kalir.
  **Yaricap 28 cagri yeri** (16'si `api/sinav.py`). RED 3 -> GREEN 4/4.
  Mutasyon M1 (kapiyi kaldir) -> 3 failed = dogru sinyal.
- **gf25** `9ea03d8c9` — **UC SERI BAGLI SEBEP**, her biri oncekini maskeliyordu:
  1. `student_engagement_signals.recorded_at` DB'de DEFAULT YOK ama ORM
     `server_default` saniyor -> NotNullViolationError
  2. 5 kolonda tz kaymasi (`coaching_events`'in DORDU **kacan kardes**)
  3. `RecordSignalResponse.id: int` ama kimlik VARCHAR -> satir YAZILDIKTAN
     sonra 500 (8 istek -> 8 satir, 28->37 olculdu, sekizi de 500)
  Kardes supurmesi `audit_logs_api.py:24`'u de yakaladi; `oba_api.py:40`
  olculunce DOGRU cikti (yanlis fix onlendi).
- **gf130** `ee6d7c820` — legacy `/fsrs/flashcards*` (3 uc) **410 Gone**.
  Frontend tuketicisi YOK (olculdu). `fsrs_cards` (122 satir) DB'de KALIR.
- **FSRS-P0 (listede HIC YOKTU)** `ee6d7c820` — `GET /api/v1/fsrs/due` 500:
  `operator does not exist: character varying = uuid`. `question_id` uuid,
  `question_bank.id` varchar -> sorgu **hic calismamis**. Frontend bu ucu
  dogrudan cagiriyor (`FSRSReviewPage.tsx:46`). Migration UUID->VARCHAR +
  FK `NOT VALID` (yetim satir var, onaysiz veri silme YAPILMADI).

### Bekci guclendirmeleri (asil kalici deger)
- `test_fsrs_schema_contract.py` artik SQL sabitlerini **canliya karsi
  KOSTURUYOR** (rollback'li) — "tablo var" bir VEKIL olcumdu, bu yuzden
  tip uyumsuzlugu 164 yesilin arkasinda saklandi.
- `test_coaching_schema_contract.py` (YENI) — modul butunu: ORM
  `server_default` -> DB DEFAULT var mi · ORM tz-aware -> DB timestamptz mi.
- `test_kimlik_tipi_sozlesmesi.py` (YENI) — VARCHAR kimlik `int` tiplenmez.
- `test_exam_session_lookup.py` (YENI) — bilinmeyen oturum None doner.
- Hepsinde **alet dogrulama kollari** var.

### Fail Eden Testler
- Golden Flow **1 kirik** (oturum basi 3, bundan onceki olcum 12):
  `gf82` learning-style — `can't subtract offset-naive and offset-aware
  datetimes`. **Dun `4ab90f809` ile kapatilmisti.** Benim regresyonum DEGIL
  (olculdu: konteynerde dunku fix VAR; learning_style coaching tablolarina
  dokunmuyor). Kismi kok neden: `HybridLearningProfile.updated_at` Pydantic
  varsayilani **naive** (`models/learning_style_models.py:221`), servis
  **aware** atiyor (`services/learning_style_service.py:145`). Cikarma
  satiri BULUNAMADI -> kaldirma testi olmadan kok neden ILAN EDILMEDI.
  Hipotez (olculmedi): veriye bagli, ilk cagri yesil / ikinci cagri kirmizi.

### Engelleyiciler
- `#468` CI tetiklenmiyor: dal master'dan 334+ commit onde,
  `on: [main,master,develop]`. Yazilan kapilarin CI degeri SIFIR.
- **3 commit push EDILMEDI.**

### Sonraki Adimlar (maks 5)
1. `GF-K6` — `gf82`: cikarma satirini bul (kaldirma testi), sonra fix
2. `FSRS-K1` — deprecated servis 7 ucta; `/recommendations` `/statistics`
   `/study-sessions/start` hala 500 ve **sonuncusunu frontend cagiriyor**
   (`useLearningPath.ts:395,412`) -> **urun karari** gerek
3. `GF-K4`/`GF-K5` — 87 tablo metadata'da yok / 67 tablo DB'de yok
4. FAZ 0 kalani: `A.3` -> `A.5` -> `A.6` -> `A.6b`
5. Push + `#468` CI tetikleme

### Kararlar (gelecek session tekrar tartismasin)
- **"Tablo var" bir VEKIL olcumdur.** Sema bekcisi ad karsilastirmasiyla
  yetinmez; sorguyu canliya karsi KOSTURUR. Tip uyumsuzlugu ad kontrolune
  yapisal olarak gorunmez.
- **Tek sebep varsayma.** gf25'te UC sebep seri bagliydi; her biri ancak
  onceki kapaninca gorundu.
- **Onaysiz veri silme yok.** FK dogrulanamiyorsa `NOT VALID` ile ekle,
  yetimi silme.
- **Bicimlendirici import siler** (F401, kullanim henuz yokken). Kullanimi
  ONCE yaz, import'u SONRA. Bu oturumda IKI KEZ dustu.
- **Pre-commit'in ruff surumu yereldekinden farkli bicimlendiriyor** — hook
  ciktisini esas al, uzerine yerel `ruff format` calistirma (dongu olur).
- **Geri alimi HER ZAMAN depo kokunden yap.** `cd backend` icindeyken
  `git checkout HEAD -- backend/...` "pathspec did not match" ile SESSIZCE
  dustu ve mutasyon dosyada kaldi (deponun kayitli tuzagi, yine yasandi).
- **`MSYS_NO_PATHCONV=1`** olmadan `docker exec ... /app` yolu MSYS tarafindan
  Windows yoluna cevrilir (`C:/Program Files/Git/app`).
