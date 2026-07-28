## Session Handoff — 2026-07-28 02:30
**Branch:** feature/self-evolution-optimization
**Son commit:** `b65195065` docs(rules): "severity de bir ölçümdür" — kural yazılıydı, yine ihlal edildi
**Uncommitted:** temiz (0 dosya) · **Push: tamam, 0 bekleyen commit**

### Yapilanlar

- **#7 kalite kapısı canlıya alındı** (`bb57a6676`, `c6725435b`)
  `backend/alembic/versions/20260727_mv_safe_for_beta.py` uygulandı → mv 25.127 = view.
  `backend/tests/e2e/test_quality_gate_leak.py:42` xfail(strict) XPASS verince kaldırıldı.
  Mutasyon: `core/quality_gate.py:69` no-op → PF 20/20, CAT 13/30 sızıntı. Rebuild sonrası
  kapı çağrı yeri container'da 2→16; celery `refresh_safe_pool` → `{'refreshed':True,'rows':25127}`.
- **ES cevap sızıntısı kapatıldı** (`f605f1e93`) — `api/elasticsearch.py:153` her öğrenciye
  `correct_answer`+`explanation` veriyordu (64.270/64.270). `services/elasticsearch_service.py`
  `STUDENT_SAFE_QUESTION_FIELDS` beyaz listesi + `core/elasticsearch_client.py` `source_includes`.
  `explanation` arama alanından da çıkarıldı (ayrı oracle: "Doğru cevap: E" → 4/10 E).
- **ÖSYM uçları auth'suz cevap veriyordu** (`84efb746f`) — `api/osym_inspired_routes.py:104`
  token'sız 200 + `correct_answer`. `_STAFF_ONLY` eklendi; auth-yok/öğrenci 403, öğretmen/admin 200.
- **Sınıf bekçisi** (`fbb8c30e6`) — `backend/scripts/audit_unauthenticated_get.py` +
  `tests/e2e/test_no_unauthenticated_answer_leak.py`. Canlı: 647 GET → 465 korunuyor, 89 açık, **0 hassas**.
- **4 bozuk hook onarıldı** — `ac3bec8b8` bandit kurulamıyordu (hiç commit geçmiyordu),
  `012a377d7` pre-push ölü + yanlış config + `default_stages`, `546c05894` reward-hacking cp1254 çöküşü.
  Yeni: `backend/hooks/push_secret_guard.py` (push aralığında sır taraması, commit-commit).
- **Anahtar envanteri** (`78a2271db`) — `backend/scripts/secret_inventory.py --check-live`: **14/14 ÖLÜ**.
- **Ders kalıcılaştırıldı** (`b65195065`) — `.claude/rules/audit-methodology.md` "Severity de bir
  ölçümdür" + frontmatter; `.claude/rules/verification.md` checklist maddesi.

### Fail Eden Testler
YOK — `tests/e2e`: **42 passed / 151 skipped / 1 xfailed / 0 failed** (39.5 s, gerçek DSN).
xfailed = `test_es_answer_leak.py::test_es_search_respects_quality_gate` (bilinçli, aşağıda).

### Engelleyiciler
YOK.

### Sonraki Adimlar (maks 5)
1. **#433 ES index'ini `v_safe_for_beta`'dan yeniden kur.** Örneklem: ES dokümanlarının %93.6'sı
   kapı dışı, %41'i `is_active=false`. `test_es_answer_leak.py` içinde xfail(strict) mühürlü —
   reindex yapılınca XPASS verip paketi kırmızıya döndürecek, marker kaldırılmalı.
2. **#436 faturalama penceresi** — anahtarlar ölü ama bir dönem canlı+public'ti; kötüye kullanım
   kontrolü konsol işi (Google Cloud Billing / OpenAI usage). İlk sızma 13 May 2026.
3. **Kapı 1 / #8** şifre kurtarma uçtan uca (~8h) · **#9-10** roster yazma uçları (~22h).
4. P2 bilgi sızıntıları: `/api/v1/ocr/health` iç Python hata metni, `/api/v1/monitoring/quality/health`
   iç metrik — ikisi de auth'suz.
5. #430 rotasız celery beat görevleri hiç koşmuyor.

### Kararlar (gelecek session tekrar tartismasin)
- **Havuz yetersizse boş dön** + "henüz doğrulanmış soru yok" — gevşetme/komşu-konu YOK.
- **ES kapı reindex'i bilinçli ertelendi** (28 Tem, kullanıcı kararı); sızıntı ayrı kapatıldı.
- **pre-push'tan `pytest -x backend/tests/` kaldırıldı**: 16.743 test + `-x`, bilinen tek bir
  pre-existing fail her push'u bloke ederdi → bekçi kesin bypass edilirdi. Tam paket CI'ın işi.
- **Beyaz liste, kara liste değil**: index'e sonradan eklenen alan kara listede otomatik sızar.
- **Alet zinciri tuzağı (4 kez ısırdı)**: bastırma direktifinin adını düz YORUM metninde geçirme —
  ruff/mypy onu gerçek direktif sanıp cümleyi kesiyor. Ayrıca `# nosec` ÖNCE ve kimliksiz olmalı.
