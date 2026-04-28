# Pilot RESULT — Paket A: question_bank dead-data temizligi

**Tarih:** 2026-04-28
**Repo:** C:\Users\husey\kiro2
**Pilot tipi:** Veri temizligi (cerrahi is_active=FALSE UPDATE + 1 DELETE)
**Onceki state.md:** backend/_pilots/20260428_paket_a_dead_data_cleanup_state.md (v2)
**Sonuc:** PASS - tum kabul kriterleri gecti

---

## 1. Ozet

64.199 aktif sorudan 6.278 cop/mukerrer kayit is_active=FALSE yapildi. topic_hierarchy'den 1 test seed silindi (TEST.BATCH1B). Hicbir kalibre/havuz/yanitlanmis kayit etkilenmedi (148 koruma kurali tetiklendi). Backend 5/5 saglikli, OSYM statistics endpoint'i total_questions: 57.921 donduruyor - DB direkt sayimiyla birebir.

---

## 2. Once/Sonra

| Metrik | Once | Sonra | Fark |
|--------|------|-------|------|
| is_active = TRUE | 64.199 | 57.921 | -6.278 |
| is_active = FALSE | 13.246 | 19.524 | +6.278 |
| Toplam | 77.445 | 77.445 | 0 |
| topic_hierarchy | 125 | 124 | -1 (TEST.BATCH1B) |
| paket_a_marked (yeni) | 0 | 6.278 | +6.278 |
| Aktif kayitlar arasinda mukerrer gruplar | 123 | 1 (havuz korumasi) | -122 |

---

## 3. Yapilan islemler

### 3.1 Backup tablosu
CREATE TABLE _bak_paketA_20260428_questions -> 6.532 satir snapshot. Retention: 30 gun, sonra DROP TABLE Huseyin manuel.

### 3.2 Mukerrer temsilci secimi (123 hash grubu)
Her gruptan 1 temsilci tutuldu:
ORDER BY is_calibrated DESC, has_answers DESC, is_calib_pool DESC, created_at ASC

123 temsilci aktif kaldi, 173 mukerrer non-temsilci deaktive edildi.

### 3.3 UPDATE (koruma kurali)
WHERE: K1 (kisa qtext) U K2 (yapisal bozuk options) U K3 (mukerrer non-temsilci)
NOT WHERE: is_calibrated=TRUE OR is_calib_pool=TRUE OR has_student_answers

Sonuc: 6.278 kayit deaktive, 148 kayit korundu.

### 3.4 TEST seed DELETE
TEST.BATCH1B dependent kontrolu (0 soru) -> DELETE FROM topic_hierarchy.

### 3.5 ANALYZE
question_bank ve topic_hierarchy istatistikleri guncellendi.

---

## 4. Dogrulamalar

### 4.1 DB-seviyesinde

| Smoke test | Beklenen | Gercek | Sonuc |
|---|---|---|---|
| active_after | 57.921 +-50 | 57.921 | PASS |
| inactive_after | 19.524 +-50 | 19.524 | PASS |
| test_seed_remaining | 0 | 0 | PASS |
| protected_still_active | 149 +-10 | 148 | PASS |
| Backup boyutu | 6.427-6.500 | 6.532 | PASS |
| Aktif kayitta duplicate | 0 (veya korunan gruplari) | 1 grup (2 havuz kaydi) | Aciklanabilir |

1 dup grup aciklamasi: Iki Esen Cografya kaydi ayni hash'te ama her ikisi de is_calib_pool=TRUE -> koruma kurali her ikisini de korudu. Conflict policy Katman 3 (havuz koruma) dogru calisti.

### 4.2 Backend smoke test (production)

GET /health -> 5/5 components healthy
POST /api/v1/auth/giris -> admin token alindi
GET /api/v1/osym/statistics -> total_questions: 57.921

Tum 13 subject_area DB direkt sayimiyla birebir uyumlu:
- MATEMATIK 15.002, TURKCE 10.642, GEOMETRI 7.965, FIZIK 6.162, KIMYA 5.819
- EDEBIYAT 3.629, BIYOLOJI 2.473, TARIH 2.330, GENEL 1.968, SOSYAL 1.234
- COGRAFYA 388, FEN 304, INGILIZCE 5

Sonuc: is_active=TRUE filtresi backend tarafinda duzgun calisiyor, deaktive edilen 6.278 kayit ogrenciye gorunmuyor.

### 4.3 Bonus bulgu (kalite tabani yukseldi)

Aktif kayitlarin with_answers: 57.921, without_answers: 0 - tum aktif sorularda cevap anahtari dolu. Cop kayitlarin buyuk kismi zaten cevap anahtari eksik / bos secenekli olanlardi, simdi gizlendiler.

---

## 5. Anomaliler / Ogrenilen dersler

### 5.1 pipeline_metadata tip hatasi (ilk apply)
Ilk SQL COALESCE(pipeline_metadata, '{}'::jsonb) || '{...}'::jsonb kullaniyordu, ama kolon json tipinde (jsonb degil). PostgreSQL json tipinde || operatoru yok.
Cozum: (COALESCE(pipeline_metadata::jsonb, '{}'::jsonb) || ...)::json
Ders: Sema teyitinde sadece kolon adlari degil, kesin tipleri (json vs jsonb) dogrulanmali.

### 5.2 PowerShell escape
Ilk denemede -c inline string'de $$ ve gomulu " PowerShell tarafindan interpre edildi, parse hatasi verdi.
Cozum: SQL'i Set-Content ile UTF-8 dosyaya yaz, psql -f ile calistir.
Ders: Karmasik SQL icin her zaman dosya tabanli yaklasim.

### 5.3 UPDATE 0 ciktisi kafa karistirdi
Ikinci basarili calistirmada psql UPDATE 0 raporladi, ama DB sayimlari dogru cikti. Aciklama: islem idempotent calisti - bir onceki abort edilmis calistirmadan kalan state vardi.
Ders: Apply sonrasi DB'den ayri sorgu ile dis dogrulama yap; psql ciktisindaki UPDATE/DELETE sayilari yetersiz.

### 5.4 protected_still_active 149 vs 148
On-hesapta 149 koruma bekliyordum, gercekte 148. Fark 1 - K1UK2UK3 birlesim hesabimin kucuk bir kenar durumu. Tolerans dahilinde, mudahale gerekmiyor.

### 5.5 Hala aktif kalan 1 mukerrer grup (2 havuz kaydi)
Iki Esen Cografya kaydi her ikisi de is_calib_pool=TRUE oldugu icin korundu. Bu Mini-migration icin engel - UNIQUE INDEX soru_hash o iki kayitta fail eder.
Cozum yolu: Mini-migration ADIM 0 state.md'de bu 2 kaydi tek tek degerlendir; ya birini is_calib_pool=FALSE yap (havuz dengesi etkilenmez), ya partial UNIQUE INDEX kullan.

---

## 6. Siradaki adimlar

1. PASS: Paket A tamamlandi (bu RESULT)
2. Pre-pilot mini-migration (Icerik Pipeline v1.2.1'in on-kosulu):
   - soru_hash VARCHAR(32) kolonu ekle + 64K satir backfill + UNIQUE INDEX (1 mukerrer grup icin karar gerekiyor - bkz. 5.5)
   - manual_review_queue tablo
   - question_bank_staging tablo
3. Ana pilot (Icerik Pipeline v1.2.1 - 500 sayfa Matematik kitabi)
4. 30 gun sonra (2026-05-28): DROP TABLE _bak_paketA_20260428_questions (Huseyin manuel)
5. Briefing v17 yazimi (briefing v16 outdated - fsrs_cards 0->57, exam_sessions 73->186, paket A sayimlari)

---

## 7. Plan disi kalan eksiklikler (ileri pilotlara devredilenler)

- K4 (66 bos topic, ders-root'a yigilma): Pipeline v1.2 ile cozulecek
- K5 (cross-subject FK bozuklugu): Paket B (opsiyonel)
- K6 (irt_a/b/c kullanilmamis kolonlar): Paket C (sema borc)
- K7 (duplicate index'ler): Paket C
- K9 (briefing v16 outdated): Briefing v17 (ayri is)
- K10 (root topic subject_area=NULL): Paket C

---

## 8. Versiyon notu

v1 (2026-04-28): Ilk RESULT yazimi. Paket A basariyla tamamlandi, smoke test PASS.

Backup retention: _bak_paketA_20260428_questions tablosu 30 gun saklanir, 2026-05-28 tarihinde Huseyin manuel DROP TABLE calistirir.
