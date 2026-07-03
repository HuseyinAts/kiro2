# İçerik Kalitesi Uzman Paneli — Servis Edilen Havuz (v_safe_for_beta)

*Tarih: 2026-07-03 · Yöntem: 12 branş disiplin uzmanı + adversaryal doğrulama + ÖSYM komisyon sentezi (24 agent, 2.9M token) · Örneklem: branş-başına ≤40 stratified, tam metin, md5(id) deterministik*

## Methodology
- Kaynak: `v_safe_for_beta` (CANLI servis havuzu, evren 25.165 → apply sonrası 25.152)
- Örneklem: 428 soru, branş başına ≤40 (FEN=2, GENEL=26 evrenin tamamı)
- Export: `backend/scripts/quality/_content_panel/export_served_stratified.py` (truncate YOK)
- Her uzman 8 boyut puanladı + kör-çözüm ile anahtar kontrolü; ağır flag'ler bağımsız 2. uzmanla refute-testinden geçti
- **Altyapı notu:** Panel öncesi kritik bulgu — üretim DB (PG18) kapalıydı, boş docker pg15 5434'ü kapmıştı; PG18 restart edilip veri (question_bank=187.835) geri getirildi.

## Branş Karnesi

| Branş | Evren | Verdict | Kötü% | Boyut ort | Not |
|---|--:|---|--:|--:|---|
| GENEL | 26 | HAZIR_DEGIL | 62.0 | 59 | F |
| TURKCE | 2142 | KOSULLU | 20.0 | 79 | D |
| GEOMETRI | 1373 | KOSULLU | 18.0 | 78 | D+ |
| FEN | 2 | KOSULLU | 15.0 | 73 | C |
| TARIH | 1596 | KOSULLU | 10.0 | 84 | C+ |
| FIZIK | 2389 | KOSULLU | 8.0 | 86 | C+ |
| MATEMATIK | 10672 | KOSULLU | 7.5 | 88 | B- |
| KIMYA | 3677 | KOSULLU | 7.5 | 84 | B- |
| BIYOLOJI | 1610 | KOSULLU | 7.0 | 86 | B |
| SOSYAL | 155 | KOSULLU | 7.0 | 86 | B |
| COGRAFYA | 379 | KOSULLU | 5.0 | 87 | B+ |
| EDEBIYAT | 1144 | SATISA_HAZIR | 4.8 | 88 | A- |

**ÖSYM komisyon genel yargı:** KOSULLU — servis kalite ~%90.8. Ağırlıklı kusur ~%9.2 (ÖSYM/ticari eşik: 0 anahtar hatası + <%1-2).

## Sistemik Kök Sorunlar
1. OCR/garble bozulması branşları kesen 1 numaralı kusur: özellikle Türkçe (OCR bütünlük 58), Tarih (72), Geometri (78) — kayıp özneler, hecelenme kırılmaları, ham unicode/LaTeX, düzleşmiş tablolar; okunabilirliği ve bazen çözülebilirliği bozuyor.
2. Cevap-anahtarı hataları (wrong_answer / no_correct): en tehlikeli sınıf çünkü öğrenciye doğrudan yanlış cevap öğretir — Geometri (CRITICAL çözülemez), Biyoloji (CRITICAL basınç-akış), Türkçe (noktalı-virgül), Kimya (N2), Fizik (kaldırma), Coğrafya (GYK), Genel (algoritma).
3. Tek-doğru-cevap ihlali (multiple_correct/ambiguous): Matematik, Fizik, Sosyal, Coğrafya ve Genel'de birden çok savunulabilir doğru — madde geçersizliği.
4. Seviye/müfredat etiketleme kayması (TYT↔AYT): Matematik ve Kimya'da sistematik; içerik geçerli olsa da adaptif servis yanlış seviyeye içerik dağıtıyor — ölçme geçerliği riski.
5. Müfredat-dışı ve önemsiz-trivia + yanlış kitap eşleşmesi: Genel havuzunda kodlama/Python/micro:bit trivia yanlış ders kitaplarına eşlenmiş; ilkokul seviyesi maddeler AYT etiketli.
6. Biçim/görsel işaret kaybı: altı-çizili ibarelerin işaretlenmemesi, kayıp soru kökleri, seçenek-şık sayısı uyuşmazlıkları (6 dize/5 şık), tekrarlı harf ön-ekleri.
7. Zayıf/absürt çeldirici: Genel (çeldirici 48) ve Fen (58) başta olmak üzere ayırt edici olmayan, elenebilir seçenekler.

## ÖSYM Komisyon Notu
Bir ÖSYM soru hazırlama komisyonu bu havuzu MEVCUT haliyle bir yayınevi soru bankası olarak ONAYLAMAZDI. Boyut-ağırlıklı kusur oranı ~%9.2; ÖSYM/ticari standart sıfır cevap-anahtarı hatası ve <%1-2 toplam kusur bekler. Haladyna madde-yazım ilkeleri açısından çok sayıda ihlal doğrulandı: (1) 'Tek doğru/en iyi cevap' ilkesi ihlali — multiple_correct ve no_correct vakaları (Matematik t²-t-1, Fizik kütle-hacim, Sosyal zekât, Geometri çözülemez dönme, Biyoloji basınç-akış); bunlar en ağır ihlaldir çünkü öğrenciye YANLIŞ ya da savunulamaz cevap servis edilir. (2) Dilbilgisel tutarlılık ve netlik ilkesi — çift-olumsuz köklerin ('bahsetmemesi beklenemez', 'yetersiz eğitim almaması'), devrik/eksik cümlelerin yaygınlığı. (3) 'Tüm/hiçbiri' ve önemsiz-trivia yasağı — GENEL branşında müfredat-dışı kodlama trivia'sı ve dairesel/totolojik maddeler. (4) Çeldirici mantıklılığı — özellikle GENEL ve FEN'de absürt, elenebilir çeldiriciler. (5) Görsel/biçim bütünlüğü — altı-çizili ibarelerin kaybı, düzleşmiş tablo-eşleştirme soruları, kayıp soru kökleri (Türkçe/Tarih). Ek olarak, cevap doğru olsa bile TYT/AYT seviye etiketlemesi sistematik hatalı (Matematik integral/türev, Kimya Kçç/kuantum) — adaptif motor TYT öğrencisine AYT içeriği verebilir; bu bir geçerlik (validity) sorunudur. Görsel bağımlılık boyutu (92-98) tek tutarlı güçlü alan.

## Alınan Aksiyon (bu oturum)
- **P0 uygulandı:** 13 doğrulanmış cevap-anahtarı/geçersizlik hatası (wrong_answer 7 + multiple_correct 5 + no_correct 1) →  +  + marker . Backup:  (reversible).  dokunulmadı.
- Deaktive ID listesi: 
- Re-curate kuyruğu (23, SİLİNMEDİ):  — garble/belirsiz/etiket, onarılabilir içerik.

## Backlog (öncelikli remediasyon)
- **P0-a (karar bekliyor):** GENEL (n=26, %62 kötü, kodlama-trivia yanlış-eşleşme) + FEN (n=2) branşlarını v_safe'ten tümüyle çıkar.
- **P1:** TURKCE (OCR 58, %20) + GEOMETRI (%18) hedefli re-OCR/re-curate — genel kusurun orantısız payı bu iki branşta.
- **P2:** TYT/AYT seviye etiket denetimi (MATEMATIK integral/türev, KIMYA Kçç/kuantum) — içerik silinmez, exam_type yeniden sınıflandırılır (adaptif motor geçerliği).
- **P3:** Tüm havuzda char-trigram LM + Türkçe-karakter guard ile garble yeniden ölçümü (tek-pass ucuz filtreden kaçın — 743 yanlış-pozitif dersi).
- **Ölçek notu:** Bu audit 428-soru ÖRNEKLEM. ~%9.2 kusur → tüm havuza yansırsa ~2.300 sorun; tam-havuz remediasyon için panel dalga-dalga tekrarlanmalı.

## Öneri (ÖSYM komisyon)
Önceliklendirilmiş remediasyon: (P0-a) GENEL branşını (26 soru, %62 hata, kodlama-trivia yanlış-eşleşme) tümüyle v_safe'ten çıkar; FEN'i (n=2) servisten kaldır — ikisi de anında, düşük maliyet. (P0-b) Tüm branşlardaki doğrulanmış wrong_answer/no_correct/multiple_correct flag'li maddeleri (bu raporda ~18 kesinleşmiş CRITICAL/MAJOR) is_active=false yap — anahtar hatası servis sızıntısı en yüksek itibar/öğrenme riski; backup+reversible. (P1) Türkçe ve Geometri'yi (OCR 58/78, %20/%18 hata) hedefli re-OCR/re-curate kuyruğuna al — bu iki branş genel kusurun orantısız payını taşıyor; garbled_text + kayıp soru-kökü + kayıp altı-çizili işaret onarılmadan bu branşlar satılamaz. (P2) TYT/AYT seviye etiketleme denetimi: Matematik (integral/türev/karmaşık sayı) ve Kimya (Kçç/kuantum/elektroliz) için exam_type alanını müfredat kazanımına göre yeniden sınıflandır — içerik silinmez, yalnız yeniden etiketlenir; adaptif motor geçerliği için kritik. (P3) Genel garble taraması: char-trigram LM + Türkçe-karakter guard ile (audit-methodology.md'deki doğrulanmış yöntem) tüm havuzda okunabilirlik yeniden ölçülmeli — tek-pass ucuz filtreden kaçın (743 yanlış-pozitif dersi). Hedef: P0+P1 sonrası ağırlıklı kusuru <%3'e, cevap-anahtarı hatasını 0'a indirmeden 'SATISA_HAZIR' ilan etme.
---

## Satış-Hazırlık Turu (aynı oturum, deploy + GF)

### Düzeltilenler (canlı doğrulandı)
- **P0 DB (kritik):** `postgresql-x64-18` STOPPED → boş docker pg15 5434'ü kapmıştı → platform hiç soru servis etmiyordu. Fix: docker pg15 durdur + admin `Start-Service postgresql-x64-18` → question_bank=187.835 geri geldi, backend reconnect.
- **P1 Redis/celery:** `kiro2-redis` container çalışmıyordu (`turkiye_sinav_redis_dev` 6379'u işgal). Fix: eski redis durdur → `docker compose up -d redis` → backend/celery restart. **celery-worker + celery-beat artık healthy** (önce unhealthy), gaierror kayboldu.
- **P1 içerik:** v_safe GENEL(n=25)+FEN → is_active=false (backup `question_bank_content_panel_genelfen_backup_20260703`). v_safe 25.152 → 25.127.

### Golden Flow canlı doğrulama (161 endpoint curl sweep, harness yerine)
- Dağılım: 200×1, 401×56 (auth), 404×11 (unseeded), 405×92 (POST endpoint GET-probe), **500×1**.
- **Tek gerçek crash:** `GET /api/v1/reviews/` → 500, kök `relation "student_reviews" does not exist`. Üniversite-değerlendirme alt-sistemi (universities/departments/professors/courses/dormitories + student_reviews) tabloları hiç yaratılmamış (şema drift, GF106 sınıfı). İkincil sosyal özellik → 503-shim veya tam alt-sistem migration gerek.
- **GF pytest harness bug (ürün değil):** host'tan `Duplicated timeseries CollectorRegistry: database_query_duration_seconds` (query_monitor_config.py:24 bare Histogram, conftest çift-import). Fix önerisi: metrik yaratımını idempotent guard'la (try/except → REGISTRY'den mevcut collector).

### Kalan backlog (sonraki oturum, workflow-shaped)
- **P1:** student_reviews alt-sistemi 503-shim veya migration; GF prometheus harness idempotent guard.
- **P2 içerik (workflow):** TYT/AYT etiket denetimi (MATEMATIK integral/türev, KIMYA Kçç/kuantum) + tam-havuz garble taraması (char-trigram LM). TURKCE/GEOMETRI re-OCR kuyruğu (23 re-curate ID hazır).
- **P2 B2B (design workflow):** okul SSO/MEB, multi-tenant, SOC2/VERBİS — büyük ölçüde eksik, go-to-market blocker.

### P2 TYT/AYT relabel (UYGULANDI, Workflow wf_83250ded)
- 898 aday (TYT etiketli + AYT-keyword) → 30 YKS müfredat uzmanı sınıflandırdı → **748 yüksek-güven AYT (≥0.8) + gerçek-aday** relabel edildi (MATEMATIK 484, KIMYA 264).
- 67 keyword-false-positive doğru şekilde TYT'de bırakıldı (agent katmanının değeri); 5 halüsinasyon id guard'la atıldı.
- exam_type='AYT' (içerik/cevap dokunulmadı). v_safe exam_type 22918/2209 → 22170/2957. Backup `question_bank_tytayt_relabel_backup_20260703` (reversible). Scriptler: `_content_panel/{export_served_stratified→tytayt/, apply_tytayt_relabel.py}`.
- **Kalan:** tam-havuz garble taraması (`garble_char_lm.py` char-trigram LM, input-TSV kur → skorla → eşik-üstü LLM-verify → re-OCR worklist). Deterministik, worklist üretir (anlık fix değil).

### P2 garble taraması (ÖLÇÜLDÜ, char-trigram LM — aksiyon YOK)
- `garble_char_lm.py` tüm is_active (110.858) üzerinde: her iki doğrulama geçti (temiz medyan 2.58 vs sentetik-bozuk 4.26, +1.59 ayrım). Eşik≥4.0: **41 aday** (temiz false-pozitif 0), ≥4.5: 7, ≥5.0: 1.
- **Servis edilen (v_safe) ≥4.0 = yalnız 1** (4.04 borderline, |AB|→IABI OCR notasyonu, okunabilir/çözülebilir → deaktive EDİLMEDİ, false-pozitif olurdu).
- **Sonuç:** servis havuzunda karakter-garble ≈ 0. Panelin "garble #1 sistemik" izlenimi karakter-seviyesinde YANLIŞ — gerçek sorun **semantik/format okunabilirliği** (kayıp özne/düzleşmiş tablo/LaTeX), re-OCR işi, ucuz char-filtre değil. "Garble efsanesi" dersinin (3 Haz) tekrar doğrulanması.
- Yüksek-skorlular: yabancı-dil karışmış sorular + kitap-başlığı metadata satırları (aktif havuzda, servis-dışı çoğu) — ayrı temizlik konusu (P3).

## Bu oturum net sonuç
Satış-hazırlık: P0 DB + P1 Redis/celery düzeltildi (stack healthy), 1 GF-500 (student_reviews, ikincil) kaldı. İçerik: panel KOŞULLU %90.8; uygulanan reversible fix'ler → 13 anahtar-hatası + 25 GENEL/FEN deaktive + 748 TYT→AYT relabel. Garble: servis havuzu temiz. Kalan büyük iş: B2B katmanı (design workflow) + student_reviews/GF-harness + TURKCE/GEOMETRI re-OCR.
