# Brainstorm: P2 Figür-İzolasyon (884 unsolvable)
Tarih: 2026-06-02 | Domain: content | Perspektifler: Kalite · Hız · Hata Toleransı

> ⛔ **SONUÇ (2026-06-03): Aksiyon-1 ölçümü P2'yi ERTELEDİ.** İzole-edilebilirlik %6 (eşik %20).
> 884'ün ~%90'ı OCR artefaktı (%46 tam-sayfa çok-soru screenshot + %44 figürsüz garble), figür-bağımlı değil.
> Detay + karar: `docs/audits/2026-06-03_p2_figure_isolatability_measurement.md`. Bu brainstorm'un öncülü (tam-blok crop) çürüdü.

## TL;DR
884 figure-dependent sorunun hepsi tam-blok crop (soru+figür+şıklar birlikte) içerdiği için
frontend `false &&` ile gizliyor — gösterse şıklar görsel sızar. Üç perspektif de **partial-yield**'de
hemfikir: 884'ün tamamını izole etmeye çalışmak Tier-H (49K rollback) hatasının tekrarıdır; sadece
**güvenle izole edilebilen yüksek-güven alt-kümeyi** yayınla, gerisini gizli bırak (regresyon yok).
En kritik risk: CSS-clip gibi client-side maskeleme **güvenlik tiyatrosu** (DevTools açan öğrenci şıkları görür) —
sızıntı yalnız **fiziksel crop + sunucu-tarafı gate + insan pixel-onayı** ile kapatılır.

## Top 5 Aksiyon
1. **Ölçüm ÖNCE: 884'ten stratified ~50 sample incele** — kaçında figür gerçekten ayrılabilir (tek-ayrık şekil) vs metne-gömülü, kaçı zaten garbled/okunamaz? — Etki: 5/5 · Zorluk: kolay · Kaynak: Kalite kör-noktası (izole-edilebilirlik oranı hiç ölçülmedi). Bu olmadan körlemesine yatırım = bu session'daki #1 dersinin tekrarı.
2. **Fiziksel üst-bölge crop** (Pillow yatay-projeksiyon ile ilk "A)" bandını bul, üstünü kes; 884×~0.1s ≈ 90 sn batch) — şıkları FİZİKSEL çıkarır, CSS hilesi değil — Etki: 4/5 · Zorluk: orta · Kaynak: Hız yol-2
3. **İki-yönlü leak gate** (negatif doğrulama): izole crop'u DB'nin 5 option metniyle Jaccard kıyasla + lokal OCR ile "A)/B)/C)" harfi ara → sızıntı varsa REDDET, gizli tut — Etki: 5/5 · Zorluk: orta · Kaynak: Hata-Tol #1
4. **Boyut invariant'ı** (sessiz-kayıp dedektörü): izole crop orijinal bbox'ın <%30 (figür kesilmiş) veya >%95 (hiç kırpılmamış) ise otomatik red — Etki: 4/5 · Zorluk: kolay · Kaynak: Hata-Tol #2
5. **`figure_safe=true` flag + per-soru render guard → stratified ≥50 (GEO/FİZİK ağırlıklı) insan pixel-onayı** sonra yayın. ASLA global un-suppress-sonra-filtrele — Etki: 5/5 · Zorluk: kolay · Kaynak: Hata-Tol #3 + Kalite uyarısı

## Konsensüs (2+ perspektif)
- **Partial-yield > tam-kapsama** (3/3): yalnız güvenle-izole-edilebilen alt-kümeyi `figure_safe` yayınla; gerisi bugün zaten gizli, regresyon yok. Kalite "izole-edilebilirlik oranı bilinmiyor" der, Hata-Tol "abstain > yanlış-bağ" der, Hız "subject-filtre hibrit" önerir — aynı sonuç.
- **İnsan pixel-onayı zorunlu, otomatik un-suppress yasak** (Kalite + Hata-Tol): ≥50 sample, <%95 onay → ders bloke.
- **Client-side maskeleme leak çözümü DEĞİL** (Hız explicit + diğerleri ima): DevTools "remove style" şıkları geri getirir. Fiziksel crop veya server-side şart.

## Çatışmalar
| Konu | Taraf A | Taraf B | Önerilen karar |
|---|---|---|---|
| Yöntem ağırlığı | Kalite: YOLO re-train (etki 5/zor, deterministik) | Hız: CSS-clip (kolay/0-maliyet) | **Orta yol: Hız yol-2 fiziksel OCR-satır crop** (90sn, gerçek leak-removal, YOLO-emeği yok) |
| CSS-clip değeri | Hız: 884×0 maliyet | Hız+Hata-Tol: güvenlik tiyatrosu | Self-resolved: clip yalnız kozmetik, asla leak-fix |

## Perspektif Detayları

### Kalite
3 yaklaşım: (1) Lokal layout-detection (PubLayNet/Detectron2) ile figure-class çek — risk: YKS geometri çizimi dağılım-dışı, "text" sanılır. (2) Classical CV bağlı-bileşen + alt A-E bandı kesme — risk: inline/2-sütun yerleşimde band kayar. (3) YOLO'ya `siklar`+`figur` class ekle re-detect — risk: etiketleme emeği + K3 mapping ayrı problem. **Kör nokta:** 884'ün kaçında figür gerçekten ayrılabilir hiç ölçülmedi. **Uyarı:** insan pixel-onayı olmadan un-suppress etme — yanlış-kesilmiş crop'un sızıntısı SESSİZ, kör-solve gate bile yakalamaz (solver metni okur, görseldeki sızan şıkkı değil).

### Hız
3 öneri: (1) Render-side CSS-clip alt %25-30 maskele (884×0 işlem) — risk: sabit %70 değişken şık-konumunda figürü keser/şık sızdırır. (2) OCR-satır-tespitli üst crop (Pillow, GPU'suz, ~90sn batch). (3) Hibrit subject-filtre + clip. **CSS-clip mümkün ama güvenlik tiyatrosu** (DevTools). **Kör nokta:** clip'lenen bölge okunabilir figür mü garbled crop mu — 61K garble ile aynı kök. **Uyarı:** saf CSS-clip'i leak-çözümü sanıp `false &&` açma.

### Hata Toleransı
3 öneri: (1) İki-yönlü leak gate (VLM/Jaccard "şık görünüyor mu"). (2) Pre/post boyut invariant (<%30 / >%95 red). (3) Stratified zorunlu insan spot-check + auto-promote yasağı. **Partial-yield = kesinlikle doğru** (Tier-H tekrarından kaçınır). **Kör nokta:** leak-testinin kendisi garble'a bağımlı — DB option metni garble ise Jaccard sessizce fail, sızan şık tespit edilemez, "temiz" sanılır. **Uyarı:** `false &&`'i alt-küme onaylanmadan global kaldırma — bir deploy penceresinde 884'ün TAMAMI leak'li sızar. Flag-first, sonra koşullu göster.

## Kör Noktalar & Uyarılar (birleşik)
1. **İzole-edilebilirlik oranı ölçülmedi** — kaç soru tek-ayrık-figür vs metne-gömülü? (Kalite)
2. **İzole bölge garbled mı?** — clip/crop okunabilir figür üretiyor mu, yoksa "gizlenmiş çöp" mü? (Hız) — 61K garble kökü
3. **Leak-gate garble'a bağımlı** — DB option garble ise Jaccard leak-match sessizce başarısız; gate PASS ≠ gerçekten temiz (Hata-Tol)
4. **SESSİZ sızıntı** — yanlış-kesilmiş crop'un cevap sızıntısını kör-solve gate yakalayamaz (solver metni okur) (Kalite)

**Birleşik uyarı:** Sıra önemli — önce `figure_safe` flag + per-soru render guard, SONRA koşullu göster. Asla "global un-suppress → sonra filtrele". CSS-clip yalnız kozmetik; gerçek leak-removal fiziksel crop + Jaccard/OCR gate + ≥50 insan pixel-onayı gerektirir.

## Önerilen ilk adım (sentez)
Aksiyon-1 (ölçüm) bir sprint değil, ~1 saatlik keşif: 884'ten stratified 50 sample crop'u görsel incele → izole-edilebilir % + garble % çıkar. Bu sayı ROI'yi belirler: eğer <%20 ayrılabilir veya çoğu garbled ise, P2 tümüyle ertelenir (re-OCR/Gemini'ye bağlanır); >%40 temiz-ayrılabilir ise Aksiyon 2-5 pipeline'ı kurmaya değer.
