## Session Handoff — 2026-07-28 (kalite kapısı canlı + 2 cevap sızıntısı kapandı)

**Branch:** feature/self-evolution-optimization
**Son commit:** `fbb8c30e6`
**Push:** YAPILMADI — **11 commit** lokalde bekliyor
**Test:** `tests/e2e` 42 passed / 151 skipped / 1 xfailed / **0 failed**

### Bu oturumda kapatılanlar

**1. #7 kalite kapısı CANLIDA** (`bb57a6676`, `c6725435b`)
- `mv_safe_for_beta` migration uygulandı: 25.127 = v_safe_for_beta, UNIQUE index,
  `refresh_safe_for_beta()` SECURITY DEFINER; `SET ROLE kiro2_app` (rolsuper=f) ile
  hem SELECT hem refresh çalıştı.
- xfail(strict) marker'ı XPASS ile tetikledi → kaldırıldı.
- Mutasyon: kapı no-op yapıldı → PF 20/20, CAT 13/30 sızıntı. Geri alındı.
- Backend+celery rebuild: kapı çağrı yeri container'da **2 → 16**.
- Canlı E2E: PF 201, CAT 201, duel 200; dönen 9 uuid'in 6'sı soru, **6/6 matview içinde**.
- Celery: `refresh_safe_pool` kayıtlı, worker `features` kuyruğunu tüketiyor,
  canlı tetik → `{'refreshed': True, 'rows': 25127}`.

**2. ES cevap anahtarı sızıntısı** (`f605f1e93`)
- Öğrenci token'ıyla `/elasticsearch/questions/search` → `correct_answer` +
  `explanation` (64.270/64.270 dokümanda dolu). `/similar` de aynısı, ayrı kod yolu.
- `explanation` ARAMA ALANIYDI → ayrı oracle ("Doğru cevap: E" sorgusu ilk 10'un 4'ünü
  E yaptı). Arama alanlarından çıkarıldı.
- Beyaz liste (`STUDENT_SAFE_QUESTION_FIELDS`, 17 alan) + ES `source_includes` +
  API katmanında ikinci süzgeç. Mutasyonla kanıtlandı.

**3. ÖSYM uçları auth'suz** (`84efb746f`)
- **Hiçbir token olmadan** `/osym-inspired/examples/{subject}` → 200 + `correct_answer`.
  `/statistics` 110.858 sayısı, `/style-guide` kök metin analizi.
- `require_role("teacher","admin","super_admin")` eklendi. Doğrulama iki yönlü:
  auth yok→403, öğrenci→403, **öğretmen→200, admin→200** (kapı ayırt ediyor).
- Mutasyon: kapı yalnız `/examples`'tan kaldırıldı → tam o ucu kapsayan 3 test kırmızı,
  diğer 3'ü yeşil.

**4. Sınıf bekçisi** (`fbb8c30e6`)
- Canlı auth'suz GET taraması: 647 GET → **465 korunuyor (%72)**, 89 açık, **0 hassas**.
  Statik AST'nin bulduğu "367 auth'suz uç" büyük ölçüde fantomdu.
- 89'un tamamı gözden geçirildi: health/yetenek/public katalog. Sınıf sistemik DEĞİL.
- `scripts/audit_unauthenticated_get.py` (yalnız GET) + paket içi bekçi testi.

**5. Yan tamirler**
- `ac3bec8b8` bandit hook'u kurulamıyordu → **hiçbir commit geçmiyordu**; PyPI wheel'ine
  çevrildi. Tüm hook zinciri (bandit + sır tarayıcı + mypy) ilk kez uçtan uca yeşil.
- `api/sinav_temp.py` UTF-16 kaydedilmiş (16.740 baytın 8.364'ü null) → silindi;
  `_smoke_api_imports` 154/1-fail → **154/0-fail**.

### Sonraki (maks 5)

1. **Push** — 11 commit bekliyor (anahtar rotasyonu/purge kararıyla birlikte)
2. **ES index'ini v_safe_for_beta'dan yeniden kur** — görev #433. Örneklemde ES
   dokümanlarının %93.6'sı kapı dışı, %41'i `is_active=false`. Öğrenci aramada hâlâ
   reddedilmiş soru görüyor. `test_es_answer_leak.py` içinde xfail(strict) ile mühürlü.
3. **11 anahtar rotasyonu** (10 Google + 1 HF) — sende; `kiro2_purge.git` push bekliyor
4. **Kapı 1 / #8** şifre kurtarma (~8h) · **#9-10** roster yazma uçları (~22h)
5. **P2 bilgi sızıntıları**: `/api/v1/ocr/health` iç Python hata metni,
   `/api/v1/monitoring/quality/health` iç metrik (auth'suz)

### Kararlar (tekrar tartışılmayacak)

- Havuz yetersizse **boş dön + "henüz doğrulanmış soru yok"** — gevşetme YOK
- Matview + zamanlı yenileme; bayat pencere kabul (+ `_question_pool_cache` TTL 3600)
- ES kapı reindex'i **bilinçli ertelendi** (28 Tem kararı), sızıntı ayrı kapatıldı

### Alet zinciri tuzakları (bugün 3 kez ısırdı)

- Pinli ruff 0.7.1 ile yerel ruff `assert` biçimlendirmesinde anlaşmıyor → sonsuz
  salınım. Çözüm: mesajı değişkene al, satırı kısalt.
- Bastırma direktifinin metnini **düz yorumda** geçirmek yeter: ruff RUF100 ile
  cümleyi kesti, mypy "geçersiz direktif" dedi. Yorumda direktif adı yazma.
- Pre-commit bir hook'un ortamını kuramazsa **tüm koşumu** düşürür — bandit'in
  çökmesi sır tarayıcısını da devre dışı bırakıyordu.

### Bilinen, kapsam dışı

- Depo geneli bandit taraması yapılmadı; ilk kez dokunulan her dosyada birikmiş
  bulgu çıkabilir.
- GF testlerinin çoğu skip (seed-veri bağımlı), login çalışıyor — görev #11
- Rotasız beat görevleri hiç koşmuyor — #430
- `agents/learning_path_agent.py` import edilemiyor (ölü kod)
- `difficulty_min/max` API parametreleri fiilen yok sayılıyor (işaretlendi, silinmedi)
