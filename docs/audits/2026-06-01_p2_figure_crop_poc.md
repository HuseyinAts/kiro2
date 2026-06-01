# P2 PoC — Figür-only Crop Fizibilite (maliyetsiz, re-OCR'sız)

**Tarih:** 2026-06-01
**Amaç:** Brainstorm #1 (`2026-05-31_gorsel-cevap-eslestirme-no-reocr.md`) iddiası:
"'soru' bbox − 'cevaplar' bbox = şıksız figür crop (leak öl, duran geometriden)".
Build'e başlamadan önce **maliyetsiz** doğrula.

## Yöntem
- Veri: `d-dataset/output/all_detections.json` (5 tam-detection kitap) +
  `detections/` (424 kitap, 83,309 per-sayfa JSON).
- Geometri: 719 sayfada soru+cevaplar birlikte; 725 'cevaplar' kutusu için
  soru-içinde-kapsanma oranı hesaplandı.
- Görsel: `345 2025 Tyt Kimya / sayfa_0077.png` üzerine kutular render edildi
  (`_beta_core_tmp/poc_0077_annotated.png`, `poc_0077_soru0.png`).

## Bulgu (öncül ÇÜRÜDÜ)

| Ölçüm | Sonuç | Anlam |
|---|---|---|
| 'cevaplar' kutusu soru-içinde (≥%70) | **3 / 725** | cevaplar şık-bloğu DEĞİL |
| 'cevaplar' ayrık | **694 / 725** | ayrı bir strip |
| 'cevaplar' median yükseklik | **38px** (soru 206px) | küçük başlık/anahtar strip'i |
| Görsel doğrulama (sayfa_0077) | 'soru' kutusu **stem+tablo+A-E şıkları** birlikte; 'cevaplar' = üst başlık strip | **leak soru kutusunun İÇİNDE** |

**Detection classları:** `soru`, `cevaplar`, `sayfa`, `test_no`, `konu`.
**A-E şıkları / figür için AYRI class YOK.**

### Sonuç
1. **"soru − cevaplar" geometrisi figürü izole EDEMEZ** — çıkarılacak şık-bloğu
   hiç tespit edilmemiş. 'cevaplar' = cevap-anahtarı/başlık strip'i.
2. A-E şıkları 'soru' kutusunun *altında* (~%25) → "üst-kısmı-kırp" heuristiği
   *mümkün* ama riskli (şık konumu değişken: 2-sütun, inline, mid-box).
3. **Asıl blocker K3 değişmedi:** mükemmel figür crop bile doğru `question_bank`
   satırına map edilmeli. 'soru' kutuları per-sayfa tespit edilmiş ama DB
   soru-id'sine deterministik bağlı DEĞİL (19 matcher + Tier-H 49K rollback).

## P2 Verdikt: re-OCR'sız + maliyetsiz figür-crop FİZİBL DEĞİL
Gerçekten yapmak için gereken (hepsi maliyet/iş):
- **(a) Layout heuristiği:** soru kutusunun alt A-E bandını OCR satır-tespiti veya
  dikey boşlukla kes → figür üst-bölge. Orta güven, kalibrasyon gerek.
- **(b) Vision çağrısı:** figür bölgesini VLM ile lokalize → maliyet.
- **(c) Re-detection:** YOLO'ya `siklar`/`figur` class ekle + yeniden çalıştır → model işi.
- **HER DURUMDA K3 mapping** ayrıca çözülmeli (figür crop → DB soru-id, çift-sinyal).

**Öneri:** P2'yi (a) heuristik PoC veya (b/c) ister maliyet/iş olarak ayrı sprint'e
ertele. En yüksek kanıtlanmış kaldıraç **P3 (kör-solve ölçekleme)** — zaten %50
başarıyla çalışıyor ve 2. sinyal üreterek `verified_provisional`'ı `verified_gold`'a
terfi ettirir.

## Artifactlar
`backend/scripts/quality/_beta_core_tmp/`: poc_0077_annotated.png, poc_0077_soru0.png (untracked).
