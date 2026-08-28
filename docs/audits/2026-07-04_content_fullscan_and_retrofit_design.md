# Tüm-Havuz İçerik Taraması (#4) + 76-Tablo Retrofit Tasarımı (#3)

*Tarih: 2026-07-04 · Bağlam: satış-hazırlık açık maddeleri #3/#4*

## #4 — Tüm Servis Havuzu Deterministik İçerik Taraması

**Yöntem:** v_safe_for_beta'nın TAMAMI (25.127 soru, örneklem DEĞİL) 3 deterministik sinyalle tarandı:
1. **garble** — char-trigram LM skoru (`garble_char_lm.py`, coherent=true üzerinde eğitildi) ≥ 4.0
2. **figure_orphan** — metin şekil/grafik/tablo/görsele atıf yapıyor AMA `question_image_url` yok
3. **structural** — key A-E değil / şık boş / metin <15 char

Script: `backend/scripts/quality/_content_fullscan/deterministic_scan.py` (reproducible, LLM yok).

### Sonuç: **~%0 yapısal kusur** (11/25.127 = %0.04, hepsi false-positive)

| Kategori | Ham flag | Gerçek kusur |
|---|--:|--:|
| figure_orphan | 10 | **0** (regex Türkçe substring yakaladı) |
| garble | 1 | **0** (borderline OCR notasyonu, okunabilir) |

**11 flag incelendi, hepsi geçerli çıktı** (CLAUDE.md "ucuz filtre yanlış-pozitif" dersi — körü körüne silinmedi):
- figure_orphan'lar: "şekil**lenen**" (shaped), "iki **şekilde**" (in two ways), "çevreci bir **tablo** ortaya koyuyor" (deyim), "sağlıklı bir **şekilde**" — hiçbiri gerçek şekle atıf değil; hepsi edebiyat/paragraf sorusu. Regex kelime-sınırı eksikti (`şekilde/şekillenen/tablo-deyimi`).
- garble (e4d01e92 GEOMETRI, skor 4.04): |AB|→IABI OCR notasyonu, çözülebilir.

### Yorum: içerik riski YAPISAL değil, SEMANTİK
Panelin ~%9.2 kusur tahmini (428 örneklem) **cevap-anahtarı hataları + zayıf çeldirici + TYT/AYT etiket** gibi **semantik** kusurlardan — bunlar deterministik yakalanamaz, **kör-çözüm (blind-solve)** gerektirir. Tüm-havuz semantik doğrulama = 25K soruyu kör-çözmek = ayrı, çok-oturumlu iş (mevcut "pool growth / blind-solve" track'i; her dalga ~1.500-3.000 soru). Bu tek workflow'a sığmaz; deterministik tarama structural-temizliği kanıtladı, semantik doğrulama devam eden ayrı çaba.

**Aksiyon:** Deaktivasyon YOK (11 flag geçerli). figure_orphan regex'e kelime-sınırı guard'ı (gelecekte). Semantik full-scan = blind-solve backlog (Faz 1+).

---

## #3 — 76-Tablo organization_id Retrofit Tasarımı

**Durum:** Faz 0'da org_id yalnız 4 kimlik tablosunda (users + 3 profil). Diğer tenant-owned tablolar org'u `user_id` join'iyle türetiyor. Discovery (canlı şema): **80 aday tablo** (user_id/student_id/teacher_id/parent_id kolonlu).

### Neden hepsi tek seferde YAPILMADI (bilinçli)
Tasarımın #1 riski = **sessiz cross-tenant PII sızıntısı** (kod tabanının is_active-sızıntı geçmişi kanıtlı). 80 tabloya körlemesine FK+backfill = tam da o risk. Ayrıca çoğu tablo org'u user_id join'iyle türetebildiği için **acil değil** — kimlik çekirdeği (Faz 0) load-bearing olanı.

### Sınıflandırma (satır sayısına göre öncelik)
Tenant-owned 80 tablo, dolu olanlar öncelikli. En dolu: image_uploads 70K, chat_sessions 10K, refresh_tokens 4.8K, student_abilities 631, user_theta 103. Çoğu <100 satır.

### Önerilen staged yaklaşım (Faz 1, tur tur — tek seferde DEĞİL)
1. **Katman A (yüksek-PII, öncelikli):** exam_sessions, student_answers/v_response_log, fsrs_*, student_abilities, learning_paths, bkt_states, student_question_flags, kvkk_consents. Her tablo: nullable org_id FK → user_id join backfill → NOT NULL + server_default. Backup + cross-tenant leak testi PER TABLO.
2. **Katman B (analytics/dashboard):** learning_analytics, performance_history, kiro2_learning_events, dashboard tabloları.
3. **Katman C (düşük-hassasiyet/büyük):** image_uploads (70K), chat_sessions (10K), refresh_tokens — org_id ekle ama düşük öncelik (PII değil / kısa-ömürlü).
4. **RLS ikinci savunma:** Katman A tamamlandıktan sonra PostgreSQL Row-Level Security (app-katman filtresi unutulsa bile DB keser).

### Backfill deseni (her tablo için, kanıtlı Faz 0 deseni)
```sql
-- org_id = ilgili user'ın org'u (users.organization_id üzerinden)
UPDATE <tablo> t SET organization_id =
  (SELECT u.organization_id FROM users u WHERE u.id = t.user_id)
WHERE t.organization_id IS NULL;
```

### KISS/YAGNI notu
image_uploads (70K) + chat_sessions (10K) gibi büyük tabloları erken retrofit etmek riskli+düşük-ROI. Katman A (PII) önce; B/C trafik geldikçe. RLS Faz 1 sonu. **Tek seferde 80-tablo migration YASAK** (körlemesine = #1 risk).

---

## Özet — 4 açık madde durumu
- **#1 Durable deploy:** ✅ ÇÖZÜLDÜ — image rebuild + recreate, fresh-image'da login/org/register/reviews hepsi çalışıyor; latent `kullanicilar` register bug'ı bulundu+fix'lendi.
- **#2 GF harness:** ✅ ÇÖZÜLDÜ — in-process→canlı httpx, GF suite 22s'de 30 pass 0 fail; 2 tenancy GF PASS.
- **#3 76-tablo retrofit:** ✅ TASARLANDI — staged Katman A/B/C + RLS planı (uygulama Faz 1, tur tur, tek seferde değil).
- **#4 Tüm-havuz içerik:** ✅ TARANDI — 25.127 deterministik, ~%0 yapısal kusur (11 flag false-positive). Semantik (~%9) = blind-solve backlog.
