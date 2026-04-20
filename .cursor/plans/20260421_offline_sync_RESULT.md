# Pilot RESULT — api.offline_sync_api

**Tarih:** 2026-04-21  
**Aşama:** B (şema) + D (4 kod borcu belgelendi, ayrı iş)  
**Sonuç:** Kısmi başarı (şema B uyumlu; runtime 4 kod borcu belgelendi)

## ADIM 0 özet

Offline sync router yüklü; `fsrs_cards` / `question_bank` / `student_answers` vb. tablolar DB’de VARCHAR uyumlu. Servis katmanında `student_answers` INSERT yok, `package_id` persist yok, FSRS eşlemesi `front_text.contains` ile kırılgan ve eşleşme olmadan `synced` artabiliyor (detay: `backend/_pilots/20260421_offline_sync_state.md`).

## Smoke test sonuçları

| Endpoint | Status | Süre | Not |
|---|---|---|---|
| GET /api/v1/offline/sync-status | 200 | 22.3 ms | `last_sync_at` null, `pending_results_count=0`, `offline_package_version=1.0` |
| GET /api/v1/offline/sync-package?limit=5 | **500** | ~295–667 ms | `build_sync_package` tek JSON `options` dict bekliyor; ORM’de `option_a`…`option_e` kolonları var, `options` yok → AttributeError, paket üretilemiyor (§11.1 #4). |
| POST /api/v1/offline/sync-results | 200 | 51.3 ms | `synced_count=1`, `failed_count=0`, `next_sync_recommended_at` döndü |

## DB gözlem (fsrs_cards)

Pre-call:  `total=0`, `last_rev` null (admin için `fsrs_cards` satırı yok — beklenen senaryo).

Post-call: `total=0`, `last_rev` null (değişmedi — beklenen).

`matching_cards` (`front_text LIKE '%<question_id>%'`): **0**

**Yorum (plan §2.5 ile hizalı):** Pre == Post, `matching_cards=0`, buna rağmen API `synced_count=1` döndü — bu **§11.1 kod borcu #3’ün canlı kanıtı** (sessiz başarı: FSRS güncellenmedi, metrik yanıltıcı). Admin’de FSRS kartı olmaması **hata değil**; pilot bunu “sessiz başarı kanıtı” olarak kaydeder.

## Bilinen sınırlamalar (kod borcu — ayrı iş, bu pilotta düzeltilmedi)

Aşağıdaki maddeler kod seviyesinde gerçek teknik borçlar (çoğu **`offline_sync_service.py`**). Pilot bunları **düzeltmez**, yalnızca belgeler:

**#1 — `student_answers` persist YOK**
- `offline_sync_api.py` docstring: "student_answers'a kayıt eklenir"
- `offline_sync_service.process_sync_results` gerçeği: `student_answers` tablosuna INSERT yok; yalnızca `fsrs_cards` update
- **Etki:** Öğrencinin offline cevabı cevap tarihçesinde görünmüyor; sadece FSRS zamanlamasına yansıyor
- **Fix niyeti:** Servise `StudentAnswer` INSERT ekle (yeni `exam_session` yaratma veya "virtual offline session" kararı gerekli)

**#2 — `package_id` uçucu (audit açığı)**
- `build_sync_package` `uuid.uuid4()` üretir, yanıtta döner
- Hiçbir tabloya persist edilmez
- `process_sync_results` `package_id`'i parametre alır ama DOĞRULAMAZ — rastgele UUID kabul edilir
- **Etki:** Audit/replay imkânsız; kötüye kullanımda bir saldırgan package üretmeden sync-results POST edebilir
- **Fix niyeti:** `offline_sync_packages` tablosu (package_id, student_id, created_at, consumed_at) ve process içinde doğrulama

**#3 — FSRS eşleme `front_text.contains(question_id)` ile kırılgan**
- `FSRSCard` ile `QuestionBankItem` arasında **doğru bir FK yok**
- Servis `FSRSCard.front_text.contains(question_id)` substring arar
- Eşleşme bulunamazsa bile `synced += 1` (satır ~227) — sessiz başarı
- **Etki:** Servis "başarılı" dese bile FSRS zamanlaması güncellenmeyebilir; metrikler yanıltıcı
- **Fix niyeti:** `FSRSCard.question_id` kolonu + FK ekle; migration yaz; front_text.contains'i FK join'e dönüştür; eşleşmezse `failed += 1` yap

**#4 — sync-package ORM alan uyumsuzluğu**
- `build_sync_package` `QuestionBankItem.options` okuyor (tek `dict` bekleniyor) ama ORM’da alanlar **`option_a` … `option_e`** (`mapped_column`; birleşik `options` attribute yok).
- **Etki:** `GET /api/v1/offline/sync-package` **500** / paket JSON’u üretilemiyor; smoke’ta `package_id` sunucudan alınamadı, dummy UUID kullanıldı.
- **Fix niyeti:** servis kodu düzeltmesi (tek dosya), migration yok — seçeneklerden biri: `options` dict’i `option_a`…`e`’den üret veya sorguda yalnızca ihtiyaç duyulan alanları oku.

## Briefing v13 için öneri notu

P1 teknik borç listesine eklenebilir: offline_sync **§11.1 dört maddesi** (smoke 2026-04-21).

## Sonraki pilot önerisi

`.cursor/plans/20260422_offline_sync_code_fix.md` — kullanıcı tarafından oluşturulacak (kod düzeltme pilotu).  
*(Batch sırasındaki alternatif: `api.pwa_sync_api` — ayrı plan.)*
