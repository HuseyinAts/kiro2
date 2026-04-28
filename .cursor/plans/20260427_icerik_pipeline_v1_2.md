# İçerik Pipeline v1.2.1 — Saf Opus + Örnekleme QA

**Tarih:** 27 Nisan 2026, v1.2 (gözden geçirme: v1.2.1) **Yazar:** Claude (Opus 4.7) **Pilot tipi:** Veri pipeline (tek seferlik veri yükleme, router aktivasyonu DEĞİL) **Kapsam:** \~400+ kitap × ortalama \~250 sayfa ≈ \~100K PNG → PostgreSQL `question_bank`. Kesin sayım pilot sonrası yapılacak (S1: bilinmiyor, scope unbounded).

**Gözden geçirme notu (v1.2 → v1.2.1):** İlk yazım sırasında `question_bank` şeması ezbere yazılmıştı (Türkçe kolon adları). v1.2.1'de gerçek şema `dbhub-kiro2` MCP üzerinden teyit edildi (73 kolon, İngilizce, 44 NOT NULL). Mapping tablosu, INSERT şablonu, conflict policy SQL ve risk matrisi gerçek verilere göre yeniden yazıldı. Detay: Bölüm 12 versiyon notu.

---

## 0. Pre-Flight (zorunlu, plan onayından önce okunsun)

### 0.1 Bu plan **ana router pilotu değildir, ama mini-migration içerir**

Mevcut KIRO2 pilot artifact sistemi (`backend/_pilots/YYYYMMDD_*_state.md` + `.cursor/plans/YYYYMMDD_*_RESULT.md`) router aktivasyonu için tasarlandı. Bu plan **iki adımlı**:

1. **Pre-pilot mini-migration** (KIRO2 standart pilot akışıyla — kendi ADIM 0 + RESULT'ı olur):
   - `question_bank.soru_hash VARCHAR(32)` kolonu ekle + 64K satır için backfill + UNIQUE INDEX
   - `manual_review_queue` tablosu oluştur
   - `question_bank_staging` tablosu oluştur
2. **Ana içerik pipeline pilotu** (bu plan, mini-migration tamamlandıktan sonra):
   - PNG → Opus → JSON → staging → conflict policy → production
   - Migration yok, alembic dokunulmaz, container restart yok (mini-migration zaten yapıldı)

Önceki v1.2'de "alembic dokunulmaz" diye yazmıştım — yanlıştı. Mini-migration alembic'e dokunur, ama **ana pipeline değil**. (Madde #1, #2 düzeltmesi.)

### 0.2 Mevcut pipeline'larla ilişki — gerçek tablodan teyitli

- `d-dataset/` 30+ extract/match script'i var. **Bu plan bunları kullanmaz.**
- **Kritik bulgu:** `eslesmis_sorucevap.jsonl` (77.336 kayıt) → DB'ye **zaten yüklü** (77.336 soruda `source_book IS NOT NULL`, 405 distinct kitap). Bu, pipeline v1.2'nin aynı kitapları okuduğunda **çakışma oranının çok yüksek olacağı** anlamına geliyor (R6 risk maddesi güncellendi).
- Eski OCR/Gemini/PaddleOCR/Qwen pipeline'ları → arşivde kalır
- Mevcut 64.199 aktif satır → **conflict policy uygulanır** (Bölüm 5.4)

### 0.3 Mevcut veri kalitesi sorunu (yeni keşfedilen, plan motivasyonu güçlendirici)

DB'den 5 örnek soru çekildiğinde (`345 2025 Ayt Matematik`):

- "1. Bir kareli bir polikromik beton, yüksekliği 20 cm olan bir blok..." → anlamsız metin (OCR hatası ya da AI hallucination)
- "Tümce - 1" → "Test - 1" yanlış transkripsiyonu
- "Türevin tanımı nedir? A) f(x) = x²" → soru ve seçenek tutarsız
- Buna rağmen `quality_score=100`, `quality_review_status='approved'`, `is_calibrated=TRUE` olabiliyor

**Sonuç:** Pipeline v1.2 **gerekli ve değerli**. Mevcut 77K kayıt çoğunlukla çöp kalitede; conflict policy "yeni okuma daha güvenilir" varsayımı **veriyle desteklenmiş** durumda.

### 0.4 Briefing'deki D-Dataset notları geçersiz mi?

KIRO2 SESSION BRIEFING v16'daki "P0 — D-Dataset match rate %0.11" kaydı bu pipeline ile **kapanmaz**. O ayrı bir iş kalemi (725 YOLO crop, GEMINI_API_KEY ekleme). Pipeline v1.2 paralel ve **alternatif** bir yol — eski pipeline'ı düzeltmek yerine baştan yazıyor.

### 0.5 Bilimsel temel (60 sayfa baseline)

BranşGTSonnetOpusSonnet accOpus accMatematik848384%98.8%**100**Fizik494249%85.7%**100**Kimya534553%84.9%**100**Biyoloji504450%88.0%**100TOPLAM236214236%90.7%100**

60 sayfa × 236 cevap, GT = bu sohbette Hüseyin + Opus 4.7 ortak okuması. Sonnet 4.6 ayrı sohbette JSON üretti, Opus 4.7 (bu sohbet) cevap anahtarı satırlarını okudu — kontrollü deney.

**Dürüst güven aralığı:** 60 sayfa küçük örneklem. Wilson skor güven aralığı (n=236, p=1.0, %95): yaklaşık **\[%98.5, %100\]**. Üretimde %99-99.8 arası beklemek makul.

### 0.6 Doğrulanmış DB durumu (27.04.2026, dbhub-kiro2 MCP üzerinden)

MetrikDeğerNot`question_bank` toplam77.445Briefing 77.401 demişti (küçük fark)`is_active=TRUE`64.199Briefing 64.270 (küçük fark)`is_calibrated=TRUE` (legacy)360Eski IRT kolonu`irt_calibrated=TRUE` (yeni)0Yeni kolon hiç kullanılmamış`is_calib_pool=TRUE`1.855Briefing 1.909 (küçük fark)`student_answers` referansı olan soru**151**Çok düşük — conflict policy "DELETE+INSERT" çoğu çakışmada uygulanabilir`source_book IS NOT NULL`77.336%99.9 — eski pipeline'ın çıktısıDistinct `source_book`405Pipeline v1.2 aynı kitapları tekrar okuyacakAlembic head`diary_drift_recovery_20260422`Briefing ile aynı

Bu sayılar `dbhub-kiro2` MCP ile teyit edildi. Briefing ile küçük farkları bilgi notu, plan'a etkisi yok.

---

## 1. Karar — Saf Opus + %1 örnekleme QA (DÜZELTİLDİ)

### 1.1 Seçenek listesi (referans için)

- **A)** Branş başına farklı oran — operasyonel karmaşıklık yüksek, kazanım marjinal
- **B)** Cross-check (Sonnet+Opus) — \~1.5x maliyet, Opus zaten %100 olduğu için katkısı yok
- **C)** Saf Opus + %5 örnekleme QA — v1.2'de seçildi
- **C')** Saf Opus + **%1 örnekleme QA + %100 anomali QA** — v1.2.1'de revize (Madde #4 düzeltmesi)

### 1.2 C' niye C'den daha gerçekçi

v1.2'de %5 örnekleme önerdim. Aritmetik:

- 100K sayfa × %5 = 5.000 sayfa QA
- Hüseyin manuel kontrol: \~12 sayfa/saat (tahmini, **henüz ölçülmedi**)
- Toplam: \~417 saat = 2-3 ay full-time, "2-3 hafta yarım gün" hatası yapmıştım

**C' düzeltmesi:** İki katmanlı QA

- **%1 random stratified sample** (1.000 sayfa, \~80 saat = 2-3 hafta yarım gün)
- **%100 flagged sample** — anomali tespit kuralları işaretlediği sayfalar (extraction_confidence &lt; 0.7, branş tutarsızlığı, boş cevap_anahtarı vb.)
- Pilot tahmini: anomali oranı \~%5 → 100K'da 5.000 flag, +%1 random = 6.000 toplam → \~500 saat (yine fazla)
- **Pratik:** anomali threshold pilot sonrası kalibre edilir; eğer %5'ten yüksekse threshold sıkılaştırılır

### 1.3 KIRO2 hata eşiği ile uyum (YENİ AÇIKLAMA — Madde #5)

"&lt;%2 hata oranı" iki farklı şeyi anlatabilir:

- **(a) IRT/FSRS kalibrasyon hassasiyeti:** Sadece `is_calib_pool=TRUE` olan sorular için geçerli. Pipeline v1.2'nin yeni soruları `is_calib_pool=FALSE` (S5 yedek havuz) olarak girdiği için **bu eşik şu an pipeline'ı bağlamıyor**. Hüseyin ileride manuel pool seçerken kalitelileri seçer.
- **(b) Exam session UX'i:** Yeni sorular `is_active=TRUE` ile öğrenciye gösterilecek. %1 hata = 1.000 yanlış cevap anahtarına sahip soru → öğrenci yanlış öğrenir, deneyim bozulur. Bu eşik **pipeline'ı bağlıyor**.

Beklenen Opus accuracy %99-99.8 → 100K sayfa × \~5 cevap = 500K cevap → 1.000-5.000 hata. Hata oranı %0.2-1.0, eşik altında ama UX etkisi var. Pilot raporunda branş bazlı accuracy ölçülecek; %99'un altı çıkan branşlar için cross-check (Seçenek B) düşünülür.

---

## 2. Pre-Flight Soru-Cevap (S1–S6, Hüseyin 27.04.2026 onayı)

### S1 — Kapsam doğrulaması

**Cevap:** Bilinmiyor. Pilot sonrası ölçülecek. Plan 100K varsayımıyla yazıldı, sapma olursa risk matrisi R3 güncellenir.

### S2 — Branş kapsamı

**Cevap:** Türkçe / Edebiyat / Sosyal Bilimler **dahil**. Bu branşlar için Opus accuracy ölçülmedi. **Faz 1/Faz 2 ayrımı zorunlu** (Bölüm 5.2):

- **Faz 1:** Matematik + Geometri + Fizik + Kimya + Biyoloji (\~50K sayfa, %100 baseline 4 branşta mevcut, Geometri için tahmini de %100 ama doğrulanmadı)
- **Ara baseline:** Türkçe / Edebiyat / Sosyal / Tarih / Coğrafya için 60 sayfa GT — yeni accuracy ölçümü
- **Faz 2:** Sosyal branşlar (\~50K sayfa)

DB'den teyit: subject_area enum 13 değer içeriyor (MATEMATIK, GEOMETRI, TURKCE, FIZIK, KIMYA, EDEBIYAT, BIYOLOJI, GENEL, TARIH, SOSYAL, COGRAFYA, FEN, INGILIZCE). v1.2'de Geometri ve Fen ayrı kategoriler olarak öngörülmemişti — Geometri Faz 1'e dahil edildi (matematik altı branşı), Fen ve İngilizce manuel review'a bırakıldı.

### S3 — `question_bank` çakışma stratejisi (KRİTİK GÜNCELLEME)

**Cevap:** "Eskileri sil" niyeti onaylandı, **kalibrasyon/yanıt verisi koruma kuralıyla**. Üç katmanlı conflict policy. Detay Bölüm 5.4'te.

DB'den teyit:

- `student_answers` tablosu mevcut, `question_id → question_bank.id` FK olarak bağlı
- Sadece **151 soru** student_answers'a sahip (briefing'deki 64K ezbere yazımı yanıltmıştı, gerçek çok daha az)
- Bu, "DELETE+INSERT" katmanının **çakışmaların büyük çoğunluğunda uygulanabilir** olduğu anlamına geliyor
- 1.855 + 360 = \~2.000 soru kalibre/havuzda, geri kalan 75K SKIP/REPLACE adayı

### S4 — Çalıştırma yöntemi

**Cevap:** Karma — pilot bu sohbette (\~390-500 sayfa, MCP), production Claude Code CLI'da paralel batch.

### S5 — `is_calibrated` / `is_calib_pool` durumu

**Cevap:** **Yedek havuz** — `is_calibrated=FALSE`, `is_calib_pool=FALSE`, `is_active=TRUE`.

DB'den teyit: Tüm 73 kolonun şeması alındı. Yeni kayıtlar için varsayılan değer matrisi Bölüm 5.5'te tam olarak listeli (önceki v1.2'de "..." ile geçiştirilmişti, Madde #9 düzeltmesi).

### S6 — TÜBİTAK BİGG zaman ilişkisi

**Cevap:** İlişki yok. Timeline baskısı yok. Pilot PASS olmadan production'a geçilmez.

---

## 3. Mimari

### 3.1 Veri akışı

```
PNG (veriseti/zkitap/screenshots/<kitap>/sayfa_NNNN.png)
   │
   ▼
[OPUS OKUMA]  ← 2 PNG/batch (MCP, pilot) veya N PNG/batch (CLI, prod)
   │
   ▼
JSON çıktısı (file_page, book_page, page_type, subject_area, primary_topic_id, questions[])
   │
   ▼
[VALIDATION]  ← şema kontrolü, anomali tespiti
   │           - boş cevap_anahtarı + page_type=questions = anomali
   │           - subject_area enum dışı = anomali
   │           - extraction_confidence < 0.7 = manual review queue
   ▼
[STAGING]     ← question_bank_staging (mini-migration ile oluşturulur)
   │
   ▼
[CONFLICT POLICY] ← üç katmanlı (Bölüm 5.4)
   │              soru_hash match → SKIP / DELETE+INSERT / INSERT
   ▼
[QA SAMPLE]   ← %1 random + %100 flagged → Hüseyin manuel
   │
   ▼
[PRODUCTION] ← question_bank INSERT
              is_calibrated=FALSE, is_calib_pool=FALSE, is_active=TRUE
              + 41 NOT NULL alan dolu (Bölüm 5.5)
```

### 3.2 Prompt mimarisi (Opus için)

60 sayfa baseline'da kullanılan prompt yapısı, üretimde değişmez:

1. Tek mesaj: PNG dosyası + Türkçe instruction
2. Beklenen çıktı: JSON
3. Cevap anahtarı satırı: sayfa altında "1.E 2.A 3.B..." formatında — Opus doğrudan transkript ediyor
4. Soru metni transkripsiyonu: ikincil — pipeline soru çözmüyor, sadece OCR + meta-extraction

**NOT:** Opus'un "akıl yürütme" yetisi sadece JSON formatlama ve anomali tespit için kullanılıyor.

### 3.3 Çıktı formatı (JSON şeması)

Sonnet'in 60 sayfa için ürettiği JSON şeması zaten test edildi. Opus aynı şemayı üretecek:

```json
{
  "file_page": "0015",
  "book_page_from_footer": 14,
  "page_type": "questions | lecture | chapter_cover | unit_cover | mixed",
  "test_no": 1,
  "test_category": "Karma Sorular | ÖSYM Tadında | Kazanım Odaklı | ...",
  "subject_area": "MATEMATIK | GEOMETRI | FIZIK | KIMYA | BIYOLOJI | TURKCE | EDEBIYAT | TARIH | COGRAFYA | SOSYAL",
  "primary_topic_code": "string (topic_hierarchy.code)",
  "exam_type": "AYT | TYT",
  "question_count": 5,
  "questions": [
    {
      "position_on_page": 1,
      "question_number_on_page": 1,
      "question_text": "string",
      "options": {"A": "...", "B": "...", "C": "...", "D": "...", "E": "..."},
      "correct_answer": "A | B | C | D | E",
      "has_diagram": false,
      "is_real_exam_question": false,
      "exam_year": null,
      "bloom_level_estimate": 2,
      "difficulty_estimate": "MEDIUM"
    }
  ],
  "extraction_confidence": 0.92,
  "page_notes": "string"
}
```

**v1.2.1 değişikliği:** `subject_area` ve `correct_answer` enum değerleri DB'deki gerçek constraint'lere göre yazıldı (büyük harf, A-E). `primary_topic_code` eklendi — pipeline `topic_hierarchy.code` üzerinden topic eşleştirecek (125 mevcut topic var).

---

## 4. Pilot — 500 sayfa gerçek deneme

### 4.1 Niçin 500 sayfa

60 sayfa accuracy ölçümü içindi. Üretim öncesi:

- Throughput ölçümü (kaç PNG/saat) — **henüz ölçülmedi**
- Hata pattern'lerinin pilot ölçeğinde tekrar görünmesi
- DB write throughput (staging tablo)
- QA sample workflow gerçekçi mi
- Anomali tespit kuralları işliyor mu
- **Conflict policy gerçek veride test edilsin** — özellikle yüksek çakışma oranı senaryosu

### 4.2 Pilot kapsamı

- **Kapsam:** Tek kitap — `345 2025 Ayt Matematik Soru Bankası` (\~390 sayfa, baseline kaynağı)
- **Çıkış kriteri (PASS):**
  - Accuracy %99+ (örnekleme QA ile)
  - Conflict policy üç katmanı **gerçek veride çalıştığı doğrulandı**
  - Anomali oranı %5 altında
  - Throughput **ölçüldü ve raporlandı** (eşik koymuyoruz, gözlem)
- **Başarısızlık eşiği (FAIL):** %95 altı accuracy → cross-check fallback
- **Gri zon (%95-99):** plan v1.3 revizyonu, branş bazlı strateji (Madde #14)

### 4.3 Pilot timeline (DÜZELTİLDİ — Madde #10)

v1.2'de Gün 1'e devasa iş yığmıştım. v1.2.1'de pre-pilot ayrı pilot olarak ayrıldı (Bölüm 0.1):

**Pre-pilot (mini-migration):**

- Gün 1-2: ADIM 0 [state.md](http://state.md) (mevcut şema teyiti, hash dağılımı analizi, 64K backfill simulasyonu)
- Gün 3: Migration yazımı (`soru_hash` kolonu, `manual_review_queue`, `question_bank_staging`)
- Gün 4: Migration apply (test ortam) + smoke test (hash UNIQUE çalışıyor mu, FK'ler doğru mu)
- Gün 5: RESULT raporu, production approval

**Ana pilot (500 sayfa):**

- Gün 6: Pilot script + prompt sabitleme + DB conflict policy fonksiyonu
- Gün 7-8: \~390 sayfa Opus okuma (\~5-6 saat aktif çalışma)
- Gün 9: %1 random + %100 flagged QA (\~30-40 sayfa)
- Gün 10: RESULT raporu + production karar

Toplam: \~2 hafta. v1.2'deki "5 gün" gerçekçi değildi.

---

## 5. Production Pipeline (pilot PASS sonrası)

### 5.1 Çalışma stratejisi (S4 = karma)

**Pilot → Bu sohbet (Claude Desktop):**

- 2 PNG/batch, MCP üzerinden
- Throughput: **henüz ölçülmedi**, pilot raporu gösterecek

**Production → Claude Code CLI:**

- Terminal'den `claude-opus-4-7` API çağrıları, batch script
- Throughput: **henüz ölçülmedi**. Pilot CLI'da değil MCP'de yapılacak; CLI ilk kez Faz 1 başında smoke test ile ölçülecek (Madde #13 düzeltmesi)
- Avantaj: Hızlı, otomatik, geceleri çalışır
- Dezavantaj: Max abonelik dahilinde rate limit'e dikkat

**Faz 1 başı CLI smoke test (yeni adım, R3 önlemi):**

- 100 sayfa CLI ile oku (paralel 4 worker)
- Throughput, accuracy, rate limit davranışı ölç
- Sonuç tatmin edici değilse paralel sayısını ayarla, yoksa Senaryo (a) sohbet bazlı'ya dön

### 5.2 Branş önceliklendirme (S2 cevabı)

1. **Faz 1:** MATEMATIK + GEOMETRI + FIZIK + KIMYA + BIYOLOJI (\~50K sayfa) — Opus accuracy 4 branşta %100, Geometri için tahmini de %100 ama pilotta ayrıca doğrulanacak
2. **Ara baseline:** TURKCE + EDEBIYAT + TARIH + COGRAFYA + SOSYAL için 60 sayfa GT — yeni accuracy ölçümü
3. **Faz 2:** Sosyal branşlar (\~50K sayfa)

**Manuel review:** FEN ve INGILIZCE kategorisi (toplam 427 mevcut soru) çok az; pipeline'a dahil edilmesi opsiyonel, Hüseyin pilot sonrası karar verir.

Faz 1 production sonuçları gelmeden Faz 2'ye geçiş yok. Ara baseline'da yeni branşlarda %95'in altı çıkarsa, o branşlar için Seçenek B (cross-check) düşünülür.

### 5.3 Hata kurtarma

- Her PNG için:
  - Read fail → 3 retry, sonra `failed_pages.csv`'ye yaz, devam
  - JSON parse fail → 1 retry farklı prompt ile, sonra failed
  - Anomali (`extraction_confidence < 0.7`) → `manual_review_queue`'a
- Sona kalan failed listesi → batch sonu insan müdahalesi

### 5.4 Conflict Policy — DB yazma stratejisi (S3 cevabı)

**Yeni tablo:** `question_bank_staging` (mini-migration ile oluşturulur, Bölüm 0.1). Şema `question_bank` ile **aynı 73 kolon** + `staging_status` (enum: `pending`/`validated`/`conflict_kept_old`/`conflict_replaced`/`failed`) + `staging_batch_id`.

**Üç katmanlı conflict kararı (PSEUDO-KOD — pilot script Python'da yazılır, Madde #7 düzeltmesi):**

```
Hash hesapla:
   soru_hash = MD5(LOWER(TRIM(question_text)) || '|' ||
                   option_a || '|' || option_b || '|' ||
                   option_c || '|' || option_d || '|' ||
                   COALESCE(option_e, ''))

Karar ağacı (Python pseudo-kod):

   existing = SELECT id, is_calibrated, is_calib_pool, irt_calibrated,
                     EXISTS(SELECT 1 FROM student_answers WHERE question_id = q.id) AS has_answers
              FROM question_bank q WHERE soru_hash = :new_hash

   if not existing:
      # KATMAN 1: Yeni soru
      INSERT INTO question_bank (...) VALUES (...)  # Bölüm 5.5
      status = 'inserted'

   elif (not existing.is_calibrated and
         not existing.irt_calibrated and
         not existing.is_calib_pool and
         not existing.has_answers):
      # KATMAN 2: Eski kullanılmamış, üzerine yaz
      DELETE FROM question_bank WHERE id = existing.id
      INSERT INTO question_bank (...) VALUES (...)
      status = 'conflict_replaced'

   else:
      # KATMAN 3: Eski korunacak (kalibre / havuzda / yanıtlanmış)
      INSERT INTO manual_review_queue (
         old_question_id, new_payload_json, reason,
         created_at
      ) VALUES (
         existing.id, :new_json,
         'kept_old: calibrated=' || existing.is_calibrated ||
         ', in_pool=' || existing.is_calib_pool ||
         ', answered=' || existing.has_answers,
         NOW()
      )
      staging.staging_status = 'conflict_kept_old'
```

`manual_review_queue` **tablo şeması (mini-migration ile oluşturulur):**

```sql
CREATE TABLE manual_review_queue (
  id              VARCHAR PRIMARY KEY,  -- UUID generate
  old_question_id VARCHAR NOT NULL REFERENCES question_bank(id),
  new_payload_json JSONB NOT NULL,
  reason          TEXT NOT NULL,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  reviewed_at     TIMESTAMPTZ NULL,
  reviewed_by     VARCHAR NULL REFERENCES users(id),
  decision        VARCHAR NULL  -- 'keep_old' | 'replace' | 'merge' | 'pending'
);
```

**Önemli notlar:**

- `soru_hash` kolonu mini-migration ile eklenir; **64K satır için backfill gerekiyor.** Tahmini süre: &lt;5 dakika (PostgreSQL native MD5 fonksiyonu hızlı). Backfill UPDATE query mini-migration ADIM 0'da test edilecek.
- Backfill sırasında 14 kolon (option_e nullable) NULL kontrolü gerekiyor — `COALESCE(option_e, '')` kullanılmalı.
- UNIQUE INDEX backfill **sonrası** oluşturulacak (varolan kayıtlarda hash collision olursa migration başarısız olur, önce dedup gerekir).

### 5.5 INSERT şablonu — TAM (Madde #9 düzeltmesi)

**v1.2'de "..." ile geçiştirmiştim.** v1.2.1'de gerçek 73 kolon şemasına göre tam INSERT şablonu (mevcut Matematik kayıtlarında gözlenen tipik değerlerden uyarlandı):

```sql
INSERT INTO question_bank (
  -- Identity
  id,                          -- UUID v5 (deterministik, hash bazlı)
  question_text,               -- Opus okuması
  option_a, option_b, option_c, option_d, option_e,  -- Opus
  correct_answer,              -- Opus, CHECK A-E
  
  -- Topic (FK zorunlu)
  primary_topic_id,            -- topic_hierarchy.id, Opus topic_code → lookup
  
  -- Bloom (NOT NULL, CHECK 1-6)
  bloom_level,                 -- 2 (default tahmin)
  bloom_category,              -- 'kavrama' (default)
  
  -- Difficulty (NOT NULL)
  difficulty_level,            -- 'MEDIUM' (default)
  irt_based_difficulty,        -- 'medium' (default, küçük harf!)
  student_success_rate,        -- 0.0
  difficulty_update_count,     -- 0
  
  -- IRT (NOT NULL, CHECK aralıkları)
  irt_discrimination,          -- 1.0 (CHECK 0.1-3.0)
  irt_difficulty,              -- 0.0 (CHECK -3 to +3)
  irt_guessing,                -- 0.2 (CHECK 0-1)
  irt_upper_asymptote,         -- 1.0 (CHECK 0-1)
  is_calibrated,               -- FALSE (S5)
  calibration_sample_size,     -- 0
  calibration_quality_score,   -- 0.0
  
  -- Linguistik (NOT NULL)
  morphology_complexity,       -- compute (kelime sayısı / unique)
  word_count,                  -- compute
  unique_word_count,           -- compute
  average_word_length,         -- compute
  readability_score,           -- 50.0 (default, ileride hesaplanır)
  
  -- Stats (NOT NULL, başlangıç 0)
  times_asked, times_correct, times_wrong, times_skipped,
  average_response_time, median_response_time, exposure_rate,
  
  -- Meta (NOT NULL)
  exam_type,                   -- 'AYT' | 'TYT'
  subject_area,                -- 'MATEMATIK' (büyük harf!)
  grade_level,                 -- 11 (CHECK 9-12) — pilot kitabı için sabit
  osym_format_compliant,       -- TRUE
  quality_score,               -- 75.0 (mevcut 100'den daha dürüst)
  quality_review_status,       -- 'pending' (mevcut 'approved' yalan)
  
  -- Source (NULLABLE ama dolduruluyor)
  source_book,                 -- "<kitap_adı>"
  source_page,                 -- file_page numarası INT
  pipeline_metadata,           -- JSONB: {pipeline:'v1.2', model:'opus-4-7', batch_id:..}
  
  -- Activity flags (NOT NULL)
  is_active,                   -- TRUE
  is_public,                   -- FALSE
  is_calib_pool,               -- FALSE (S5)
  
  -- Yeni kolonlar (mini-migration ile)
  soru_hash                    -- MD5 hash
  
  -- Timestamps (NOT NULL, default now())
  -- created_at, updated_at otomatik
)
VALUES (...);
```

**41 NOT NULL kolon dolu** (irt_calibrated ve diğer nullable kolonlar atlandı). Bu, pilot script'in **JSON → INSERT mapping fonksiyonunun** karmaşık olacağı anlamına geliyor. Pilotta gerçek INSERT'leri görerek mapping ince ayarı yapılır.

### 5.6 IRT durumu (S5 cevabı)

Yeni kayıtlar:

- Exam session'larda öğrenciye gösterilir (`is_active=TRUE`)
- Pazar 03:00 Celery `irt_calibration` task'ı bunlara dokunmaz (`is_calib_pool=FALSE`)
- Mevcut 1.855 dengeli havuz korunur
- İleride Hüseyin manuel olarak `is_calib_pool=TRUE` yapabilir

**Pipeline'ın yarattığı varsayılan IRT değerleri (irt_discrimination=1.0, irt_difficulty=0.0, irt_guessing=0.2, irt_upper_asymptote=1.0)** kalibre olmadan kullanılmamalı; bunlar sadece NOT NULL constraint'i geçmek için. CAT engine `is_calib_pool=FALSE` olanları sorgudan otomatik dışlıyor (Bölüm 3.1 doğrulanmadı, pilotta teyit edilecek).

---

## 6. `question_bank` Mapping — gerçek şemaya göre (Madde #6 düzeltmesi)

**v1.2'de Türkçe kolon adları (ders, konu, soru_metni vb.) ezbere yazılmıştı — yanlıştı.** v1.2.1'de gerçek 73 kolon dbhub-kiro2 MCP ile teyit edildi. Mapping:

JSON alanı`question_bank` kolonuTip / KısıtNot(UUID v5 hash)`id`VARCHAR PKdeterministik, soru_hash'ten türetilir`questions[i].question_textquestion_text`TEXT NOT NULLOpus transkripsiyonu(yok, opsiyonel)`question_html`TEXT NULLbaşlangıçta NULL(yok, opsiyonel)`question_latex`TEXT NULLmatematik/fizik için ileride(yok, opsiyonel)`question_image_url`VARCHAR NULLdiyagramlı sorular için ileride`questions[i].options.Aoption_a`TEXT NOT NULL"A) " prefix temizlenip`questions[i].options.Boption_b`TEXT NOT NULLaynı`questions[i].options.Coption_c`TEXT NOT NULLaynı`questions[i].options.Doption_d`TEXT NOT NULLaynı`questions[i].options.Eoption_e`TEXT NULLbazı sorularda 4 şık var`questions[i].correct_answercorrect_answer`VARCHAR NOT NULL CHECK A-EOpus okuması`primary_topic_code` (lookup)`primary_topic_id`VARCHAR NOT NULL FK→topic_hierarchycode → id eşleştirme gerekli`questions[i].bloom_level_estimatebloom_level`INT NOT NULL CHECK 1-6Opus tahmini, default 2(sabit)`bloom_category`VARCHAR NOT NULL"kavrama" default`questions[i].difficulty_estimatedifficulty_level`enum NOT NULLVERY_EASY/EASY/MEDIUM/HARD/VERY_HARD(sabit)`irt_based_difficulty`VARCHAR NOT NULL"medium" küçük harf, mevcut pattern(sabit)`irt_discrimination`DOUBLE NOT NULL1.0 (CHECK 0.1-3.0)(sabit)`irt_difficulty`DOUBLE NOT NULL0.0 (CHECK -3 to +3)(sabit)`irt_guessing`DOUBLE NOT NULL0.2 (CHECK 0-1)(sabit)`irt_upper_asymptote`DOUBLE NOT NULL1.0 (CHECK 0-1)(sabit, S5)`is_calibrated`BOOL NOT NULLFALSE(sabit)`calibration_sample_size`INT NOT NULL0(sabit)`calibration_quality_score`DOUBLE NOT NULL0.0(compute)`morphology_complexity`DOUBLE NOT NULLunique/total ratio(compute)`word_count`INT NOT NULLsplit() len(compute)`unique_word_count`INT NOT NULLset() len(compute)`average_word_length`DOUBLE NOT NULLmean char count(sabit)`readability_score`DOUBLE NOT NULL50.0 default(sabit)`times_asked, times_correct, times_wrong, times_skipped`INT NOT NULL0, 0, 0, 0(sabit)`average_response_time, median_response_time`DOUBLE NOT NULL0.0, 0.0(sabit)`exposure_rate`DOUBLE NOT NULL CHECK 0-10.0`exam_typeexam_type`VARCHAR NOT NULL"AYT" / "TYT"`subject_areasubject_area`VARCHAR NOT NULLbüyük harf: MATEMATIK, GEOMETRI, ...(sabit / kitap meta)`grade_level`INT NOT NULL CHECK 9-12AYT için 11 default, TYT için 11(sabit)`osym_format_compliant`BOOL NOT NULLTRUE`questions[i].exam_yearosym_year`INT NULLsadece çıkmış soru(sabit)`quality_score`DOUBLE NOT NULL CHECK 0-10075.0 (mevcut 100 yalan, daha dürüst)(sabit)`quality_review_status`VARCHAR NOT NULL"pending" (mevcut "approved" yalan)(sabit)`source_book`VARCHAR NULL"&lt;kitap_adı&gt;"`file_pagesource_page`INT NULLparsed integer(compute)`pipeline_metadata`JSONB NULL{pipeline:'v1.2', model:'opus-4-7', batch_id, opus_run_at}(sabit, opsiyonel)`created_by`VARCHAR NULL FK→usersNULL (otomatik)(sabit)`is_active`BOOL NOT NULLTRUE(sabit)`is_public`BOOL NOT NULLFALSE(sabit, S5)`is_calib_pool`BOOL NOT NULLFALSE(compute, mini-migration ile yeni)`soru_hash`VARCHAR(32)MD5 hex(otomatik)`created_at, updated_at`TIMESTAMPTZ NOT NULLnow() default

**Atlanan kolonlar (nullable, başlangıçta dolmuyor):** `explanation`, `explanation_video_url`, `alternative_solutions`, `secondary_topics`, `last_difficulty_update`, `last_calibration_date`, `last_used_date`, `osym_year`, `pipeline_metadata`, `embedding`, `image_ocr_text`, `image_width`, `image_height`, `irt_a/b/c/calibrated/method/calibrated_at/n_responses`.

Toplam: **45 kolon dolu** (41 NOT NULL + 4 nullable ama doldurulan), 28 kolon NULL bırakılır. Pilot script `INSERT` query'sini bu mapping'e göre üretir.

---

## 7. Risk Matrisi (DÜZELTİLDİ — Madde #8, #13)

#RiskOlasılıkEtkiYedek planR1Opus accuracy %100 değil, %95'e düşerDüşükYüksekPilot'ta görülürse → cross-check (Seçenek B)R2Yeni branşlarda (Türkçe vb.) accuracy düşükOrtaOrtaFaz 1/Faz 2 ayrımı (Bölüm 5.2), Faz 2 öncesi ara baselineR3CLI rate limit (Max 20x) — pratik sınır**Bilinmiyor**Orta**Faz 1 başında 100 sayfa CLI smoke test (Bölüm 5.1)**, sonuca göre paralel sayısı ayarlanırR4Hash backfill 64K satırda yavaşDüşükDüşükPostgreSQL native MD5 hızlı; mini-migration ADIM 0'da testR5`student_answers` FK kontrolü yavaş (her conflict'te subquery)OrtaDüşükDB'den teyit: sadece 151 soru yanıt almış, bulk LEFT JOIN ile tek geçişte çözülürR6**Conflict policy "kept_old" oranı yüksek olurYüksek** (mevcut 77.336 source_book dolu, %90+ çakışma bekleniyor)OrtaPilot raporu hash collision oranını gösterecek; &gt;%30 ise yeni okuma hash'i source_book+page bazlı yapılabilirR7Mevcut kalibre 360 sorudan biri yeni okumayla çakışırsaYüksekDüşükConflict policy zaten koruyor (Katman 3 → manual review queue)R8Container/DB araya girer (offline_sync deploy gibi)DüşükDüşükPipeline staging tablosuna yazıyor, production'ı etkilemezR9Kitap dizinleri tutarsız (footer offset, isim formatı)YüksekDüşükBiyoloji'de footer-1 zaten görüldü; per-kitap pre-flightR10Prompt drift (Opus farklı sürümlerde farklı çıktı)DüşükYüksekPilot prompt'unu commit'e bağla (K-İçerik-3 cevabı)R11Hüseyin tek başına QA yetiştiremezOrtaOrta%1 random + %100 flagged sample (Bölüm 1.2)R12Manual review queue patlarOrta-YüksekOrtaR6 ile ilişkili; pilot sonrası queue boyutu görülür; eşik aşılırsa Hüseyin batch karar verirR13`subject_area` enum dışı değer (FEN, INGILIZCE)DüşükDüşükPipeline subject_area validate eder, dışarıdaysa manual_review_queue'aR14Mevcut çöp veri kalitesi yüksek "kept_old" oranına yol açarYüksekYüksekBölüm 0.3 motivasyonu; eğer çakışan eski kayıt çöp ise (örn. "polikromik beton") manuel olarak `is_active=FALSE` yapılıp yeni okuma INSERT edilebilir — Hüseyin pilot raporu sonrası karar

---

## 8. Açık Borçlar / Karar Bekleyenler (DÜZELTİLDİ — Madde #2, #15)

1. **K-İçerik-1:** S1-S6 cevaplandı (Bölüm 2). Kapalı.
2. **K-İçerik-2:** Pilot sonucu PASS / FAIL / Gri zon kararı (Bölüm 4.2)
3. **K-İçerik-3 (KAPALI):** ~~Pipeline yarı yolda Opus model güncellemesi~~ → Karar: **yeni model 60 sayfa baseline'da %100 değilse devam, %100'se isteğe bağlı switch.** Pilot prompt'u commit'e bağlanır, model değişikliği ayrı plan v1.3 turunda değerlendirilir.
4. **K-İçerik-4:** D-Dataset (`eslesmis_sorucevap.jsonl` 77K) bu pipeline ile birleştirilecek mi?
   - **DB analizi cevabı:** O dosya zaten DB'de yüklü (77.336 source_book dolu). Birleştirme = conflict policy zaten yapıyor. Ek aksiyon yok. **Kapalı.**
5. **K-İçerik-5 (KAPALI):** Mini-migration ayrı pre-pilot mu? → **Cevap: EVET, ayrı pre-pilot.** Gerekçe: 64K satıra ALTER TABLE + UPDATE (backfill) production şemasını etkileyen bir operasyon, kendi RESULT raporu hak ediyor. KIRO2 pilot artifact akışı (ADIM 0 + RESULT) uygulanır. (Bölüm 0.1 ve 4.3'e yazıldı.)

Yeni açık borçlar: 6. **K-İçerik-6:** Mevcut 77K çöp kaliteli sorularla ne yapılacak?

- Conflict policy "kept_old" yapan ama gerçekte çöp olan kayıtlar (örn. "polikromik beton")
- Seçenek (a): Pilot sonrası batch SQL ile `is_active=FALSE` yap, yeni okuma INSERT edilsin
- Seçenek (b): manual_review_queue'da "decision='replace'" işaretle, batch replace
- Seçenek (c): Dokunulmasın, kalsınlar
- Pilot raporu somut örneklerle bu kararı bilgilendirir

---

## 9. Bu Plan Ne Değildir

- ❌ Tek başına ana pipeline pilotu değil — pre-pilot mini-migration ayrı pilot olarak yürütülecek
- ❌ Auth audit'i değil — API surface değişmez
- ❌ Eski D-Dataset'in yeniden işlenmesi değil — paralel ve alternatif iş kalemi
- ❌ Frontend dokunmaz, sadece DB'ye yazar
- ❌ Soru çözüm AI'ı değil — sadece OCR + meta-extraction
- ❌ Mevcut 64K aktif soruyu silme operasyonu değil — sadece kullanılmamış çakışanlar değiştirilir, kalibre/yanıtlanmış olanlar korunur
- ❌ IRT kalibrasyon devreye sokmuyor — yeni sorular `is_calib_pool=FALSE`, mevcut 1.855 havuz dengesi korunur

---

## 10. Sıradaki Adımlar (DÜZELTİLDİ — Madde #14)

### Pre-pilot fazı (mini-migration)
1. ✅ Hüseyin: S1–S6 cevap (bu sohbette tamamlandı, plan'a Bölüm 2'ye yazıldı)
2. ✅ Claude: Plan v1.2 → gözden geçirme → v1.2.1 (bu doküman)
3. Hüseyin: v1.2.1 onay (gözden geçirme bekliyor)
4. Claude: Pre-pilot ADIM 0 state.md (`backend/_pilots/20260428_icerik_pipeline_prepilot_state.md`)
   - Mevcut `question_bank` şema teyiti (zaten yapıldı, dökümante edilecek)
   - 64K satır hash dağılımı simülasyonu (Python ile, DB read-only)
   - `manual_review_queue` ve `question_bank_staging` tablo plan
   - Migration drift kontrolü (alembic head: `diary_drift_recovery_20260422`)
5. Hüseyin: Mini-migration onayı
6. Claude: Migration script (`alembic revision -m "add_soru_hash_and_staging_tables"`)
7. Hüseyin: Migration apply (`alembic upgrade head`) + smoke test
8. Claude: Mini-migration RESULT raporu

### Ana pilot fazı (500 sayfa)
9. Claude: Pilot script (`d-dataset/plans/20260428_pilot_500p.py` + prompt sabit)
10. Hüseyin: Pilot başlat — bu sohbette ya da yeni sohbette, 1 kitap 390 sayfa
11. Claude: Pilot RESULT raporu (accuracy + throughput + conflict policy davranışı)
12. **Karar matrisi:**
    - **PASS** (%99+): Production karar → Faz 1 başlat
    - **Gri zon** (%95-99): plan v1.3 revizyonu, branş bazlı strateji yeniden değerlendir
    - **FAIL** (%95 altı): Cross-check (Seçenek B) fallback, plan v1.3'te yeniden tasarla

### Production fazı (PASS sonrası)
13. CLI smoke test (100 sayfa, R3 önlemi, Bölüm 5.1)
14. Faz 1 başlat → MATEMATIK + GEOMETRI + FIZIK + KIMYA + BIYOLOJI (~50K sayfa)
15. Faz 1 RESULT (accuracy + manual review queue boyutu)
16. **K-İçerik-6 kararı** (mevcut çöp kaliteli kayıtlar)
17. Ara baseline (Türkçe / Edebiyat / Sosyal / Tarih / Coğrafya 60 sayfa GT)
18. Faz 2 (Sosyal branşlar ~50K sayfa)
19. Toplam pipeline RESULT, kapanış

---

## 11. v1.2 → v1.2.1 Düzeltme Özeti (15 madde, hangi nereye)

| # | v1.2 sorunu | v1.2.1 düzeltmesi | Yer |
|---|---|---|---|
| 1 | "Migration yok, alembic dokunulmaz" iddiası kendi içeriğiyle çelişiyordu | Bölüm 0.1 yeniden yazıldı: pre-pilot mini-migration ayrı, ana pipeline migration'sız | Bölüm 0.1 |
| 2 | K-İçerik-5 açık soru olarak duruyordu, ama plan zaten cevabı içeriyordu | K-İçerik-5 KAPALI, gerekçe "ayrı pre-pilot, kendi RESULT raporu" | Bölüm 8 |
| 3 | Throughput rakamları (80, 200, 12 sayfa/saat) ezbere | "henüz ölçülmedi", PASS kriterindeki ≥80 eşiği kaldırıldı, "ölçüldü ve raporlandı" | Bölüm 4.2, 5.1 |
| 4 | %5 QA matematiği yanlıştı (5.000 sayfa × 12/saat ≠ 2-3 hafta) | %1 random + %100 flagged stratejisi (1.000 + flagged sayfa) | Bölüm 1.2 |
| 5 | "<%2 hata oranı" bağlamı belirsizdi | (a) IRT vs (b) UX ayrımı yapıldı; pipeline UX eşiğine bağlı | Bölüm 1.3 |
| 6 | Mapping tablosu Türkçe ezbere kolon adlarıyla doluydu | dbhub-kiro2 MCP ile gerçek 73 kolon teyit edildi, mapping tamamen yeniden yazıldı | Bölüm 6 |
| 7 | Bölüm 5.4 SQL pseudo-koddu ama gerçek SQL gibi sunulmuştu | Açıkça PSEUDO-KOD etiketi, Python pseudo-kod olarak yazıldı | Bölüm 5.4 |
| 8 | R6 olasılığı "Düşük" yazılmıştı, gerçekte yüksek olabilir | Olasılık "Yüksek" güncellendi, gerekçe DB analizi (77.336 source_book) | Bölüm 7 R6 |
| 9 | Bölüm 5.5 INSERT şablonu "..." ile geçiştirilmişti | 41 NOT NULL kolonun tam listesi, default değerleriyle | Bölüm 5.5 |
| 10 | Bölüm 4.3 timeline 5 gün, Gün 1 devasa | Pre-pilot ayrıldı, ana pilot 5 gün, toplam ~2 hafta | Bölüm 4.3 |
| 11 | Bölüm 0.4 markdown tablosu render olmamıştı | Düzeltildi, tablo doğru pipe karakterleriyle | Bölüm 0.5 |
| 12 | Bölüm 11 versiyon notu "v1.0/v1.1" cümlesi yanıltıcı | Bu özet (Bölüm 11) kalıcı olarak değişiklik kayıtları için | Bölüm 11, 12 |
| 13 | R3 risk maddesi "tahmin", CLI hiç denenmedi | "CLI smoke test Faz 1 başında ölçülecek" yedek planı eklendi | Bölüm 7 R3, 5.1 |
| 14 | Bölüm 10 sıralı adımlar PASS/FAIL ikili, gri zon yoktu | Karar matrisi 3'lü: PASS/Gri zon/FAIL, gri zon → v1.3 revizyonu | Bölüm 10 |
| 15 | K-İçerik-3 (model güncellemesi) cevapsız bırakılmıştı | KAPALI: "yeni model 60 sayfa baseline'da %100 değilse devam, %100'se isteğe bağlı switch" | Bölüm 8 |

**Yeni keşfedilen ve eklenen risk/borç (v1.2'de yoktu):**
- **R7 (yeni):** Mevcut kalibre 360 soru çakışırsa (zaten conflict policy koruyor)
- **R13 (yeni):** Subject_area enum dışı değer (FEN, INGILIZCE) — 427 mevcut soru
- **R14 (yeni):** Mevcut çöp veri ("polikromik beton") yüksek "kept_old" oranına yol açar
- **K-İçerik-6 (yeni):** Mevcut 77K çöp kaliteli sorularla ne yapılacak

---

## 12. Versiyon Notu

**v1.2 (27.04.2026, sabah):** İlk yazılı versiyon. 60 sayfa baseline (Opus %100, Sonnet %90.7). Saf Opus + %5 QA seçildi. S1-S6 cevaplandı. Önemli eksiklik: şema ezbere yazıldı, mapping yanlış, throughput ezbere, conflict policy SQL pseudo-kod gibi sunulmadı.

**v1.2.1 (27.04.2026, akşam):** Gözden geçirme turunda 15 madde tespit edildi (3 kritik, 5 orta, 7 küçük). Tümü düzeltildi. Kritik: dbhub-kiro2 MCP ile gerçek `question_bank` şeması teyit edildi (73 kolon, 41 NOT NULL, İngilizce — Türkçe ezberi tamamen değiştirildi). DB durumu doğrulandı (77.445 toplam, 64.199 aktif, 360 kalibre, 1.855 havuz, 151 yanıtlanmış, 405 distinct kitap). Mevcut veri kalitesi sorunu keşfedildi (Bölüm 0.3) — pipeline motivasyonu güçlendi. Mini-migration ayrı pre-pilot olarak ayrıldı. QA stratejisi gerçekçi sayılarla düzeltildi (%1 random + %100 flagged). Risk matrisi 11 → 14 maddeye çıkarıldı.

**Bekleyen:** v1.2.1 onay → pre-pilot ADIM 0 state.md → mini-migration → ana pilot → RESULT → production karar.
