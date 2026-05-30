# Kök-Neden Sentezi — KIRO2 İçerik Kalitesi (31 May 2026)

**Problem (kullanıcı):** Defalarca OCR yapıldı, görseller var; ama soru-görsel, soru-cevap
ve metin doğruluğu istenen seviyeye çıkmadı. Neden? (semptom değil **kök neden**)

**Yöntem:** 8 eksen bulgusu + brifing birleştirildi. Her satır `dosya:satır` veya gerçek
DB/artifact sayısıyla destekli. Phantom filtresi uygulandı (fix'lenmiş şeyler ROOT'tan ayrıldı).

---

## BÖLÜM 1 — Birleşik Kök-Neden Tablosu (sıralı, eksen-bazlı kümelenmiş)

| # | Kök-neden | Mekanizma (özet) | KANIT | Etkilenen eksen | Şiddet | ROOT/SYMPTOM | Bağlantılar |
|---|---|---|---|---|---|---|---|
| **R1** | **Kaynak görüntü 1080p ekran-görüntüsü (PDF render değil)** | DRM viewer `pyautogui.screenshot()` tam-ekran; A4 sayfa 1080p'de ~975px (200 DPI render'da ~2339px) → ~2.4x çözünürlük kaybı kaynakta, geri kazanılamaz | `auto_screenshot.py:38`, `screenshot.py:30,56`; ölçülen `sayfa_0001.png=(1920,1080)` 3 kitap; `config.yaml:68 max_image_size:1024` | metin (1°), cevap, görsel | **P0** | **ROOT** | → R2 (upscale yok telafi etmiyor) → R3 (teşhis route'lanmıyor) → R12 (garble PASS geçiyor) |
| **R2** | **Pipeline'da UPSCALE yok; sadece downscale + 1024px cap** | YOLO crop'u VLM'e büyütülmeden gidiyor; median crop **352px → ~9px/karakter**; düşük-res'te VLM soft-decode → "loylak/bilkidir" sınıfı | `script_common.py:123-126` (sadece `>` küçültme); `pipeline.py:745-746,1176-1184`; `config.yaml:102-103`; ölçülen crop 333/352/884px; upscale grep=0 | metin (1°), cevap | **P0** | **ROOT** | R1'i kısmen telafi edebilirdi, etmiyor; W4r notu: upscale hatayı %20-40 azaltıyor |
| **R3** | **Çözünürlük teşhisi VAR ama OCR döngüsüne bağlı DEĞİL (dead code) + eşik yanlış** | `full_image_quality_assessment` `pdf_low_dpi` etiketliyor ama pipeline çağırmıyor; eşik `width<300` (median 352 üstünde → bağlansa bile yakalamaz) | `script_common.py:1665,1679,1686-1687`; pipeline grep `is_low_resolution`/`pdf_low_dpi`=0 | metin | P1 | ROOT (operasyonel) | R1/R2'yi yakalayıp route edebilecek gate kapalı |
| **R4** | **Soru↔crop deterministik bağ ingest-anında HİÇ kurulmadı** | INSERT'te `question_image_url`/`crop_file` doldurulmuyor; satır kimliği `uuid5(book\|page\|q_num)`, q_num=Gemini OCR test-no; crop ise YOLO bbox `(y1,x1)` uzamsal sırası — ortak değişmez anahtar yok → 19+ post-hoc matcher heuristik | `import_d_dataset.py:160-163,223-278,344-360` (img kolon yok); `crop_from_detections.py:266-274`; `pipeline.py:3298,3308,3311,3315` (crop_path VAR ama kullanılmıyor) | görsel (1°), cevap, metin | **P0** | **ROOT** | Tüm görsel eşleşme kök-nedenlerinin (R5,R6,R7,R8) altı |
| **R5** | **Üç `q` semantiği tek isme yığılmış** | `question_number` (OCR test-no) ≠ crop `q_index` (YOLO uzamsal) ≠ `q_index_in_page` (Gemini-assigned, 0/1-index belirsiz) — matcher'lar eş sanıyor | `image_match_metadata_v1.py:122-148,168-195`; audit `min(qip)`: min=0 %92.9; `tier_h_v2` offset histogram +1/0/-1 değişken | görsel (1°) | **P0** | ROOT (R4 tezahürü, bağımsız kimlik-tasarım hatası) | R6 (Tier H) bunun sonucu |
| **R6** | **Tek-sinyal eşleşme (text doğrulama yok) → Tier H 49,468 satır YANLIŞ** | `q_index_in_page` exact filename match, Jaccard ikinci sinyal atlandı; 0/1-index kayması yakalanamadı → ROLLBACK | `tier_h_qip_exact.py:132,27-31`; audit: Tier H "Sinyal2=YOK → %25"; karşıt: Tier F key+sim≥0.50 → %100 (49/49) | görsel | P0 (gerçekleşti) / P1 (tekrar riski; script silinmedi) | SYMPTOM (R4+R5) + metodolojik ders | CLAUDE.md "ÇİFT SİNYAL" kuralı buradan doğdu |
| **R7** | **Crop count ≠ DB count (Gemini sayım ≠ YOLO sayım) → pozisyonel eşleşme zemini kayıyor** | v15a son-çare matcher NULL satırları bbox'a Y-sırasıyla eşliyor; ama `db_max==disk_max` sadece **3/100 sayfa**, disk_more 95/100 | `image_match_v15a:97-103`; audit Aşama C 100 sayfa invariant; `v15_page_fallback` tüm-sayfa screenshot itirafı | görsel | P1 | SYMPTOM (R4) + OCR sayım kalitesi | R4'ün pozisyonel telafisini de çürütüyor |
| **R8** | **19+ matcher sürümü (v1→v15a, Tier A→H) → izlenemez provenance** | Her başarısızlık yeni sürüm doğurdu; hangi satır hangi tier/güvenle eşleşti belirsiz; tier_c flag hiç yazılmadı, tier_h flag rollback'te tutarsız | 19 image_match*.py + tier scriptleri (ls doğrulandı); audit "tier_c_match flag YAZILMAMIŞ"; `tier_h_qip_exact.py:181-201` | görsel + meta | P1 | SYMPTOM (süreç) | Gelecek temizliği bloke ediyor |
| **R9** | **Crop birimi = "tüm soru bloğu" → cevap-sızıntısı deterministik** | YOLO `'soru'` kutusu stem+figure+**A-E şıkları** içeriyor; "figure-only" sınıf yok → her `question_image_url` cevap sızdırıyor | `pipeline.py:164-166,709,714,682-688`; `populate_image_urls_tier_c.py:14-16`; `beta_eligible_filter_v2.py:33-34` | görsel (1°), metin | **P0** | **ROOT** | → R10 (frontend suppress) → R11 (filtre eksik) |
| **R10** | **Frontend `false &&` ölü-devre: TÜM görseller kalıcı gizli** | Leak sızmasın diye render derleme-zamanı `false` ile kapatılmış; leak'siz meşru figürler de gizleniyor → figure-dependent soru görselsiz, çözülemez | `ModernOSYMExamInterface.tsx:551 {false && ...}`; git blame `9094dd50c9` (21 May), hâlâ canlı (10 gün+) | görsel | **P0** (ürün) | SYMPTOM (R9) bağımsız ürün-kök | R9 çözülmeden kaldırılamaz |
| **R11** | **Figür-bağımlı sorular havuzdan TUTARSIZ dışlanıyor** | Backend filtresi yalnız GEO/FİZİK + (görsel yok VE metin<500); diğer derslerde figure-dependent metin-only sızıyor; `URL NOT NULL` "OK" sayılıyor ama URL render edilmiyor | `osym_exam_engine.py:1277-1282`; coherence pilot drop figure_dependent=1,880; `_select_beta_questions:1166-1205` flag'e bakıyor | görsel + metin | P0 (standart havuz) / P1 (beta-flag) | ROOT (filtre tasarım eksiği) | R9/R10'u kötüleştiriyor |
| **R12** | **page_inline cevap-OCR çıkarımı düşük-qnum'a çöküyor → A/E bias orada yoğun** | answers_page_inline %53 kaynak; AVG 1.9 cevap/sayfa, **qnum≤5 payı %80.2**; A+E q1-5'te %54, q6+ %37(uniform) → bias içerikten değil, grid'i lokal-qnum'a çökertmekten; B yutuluyor (%11.3) | `answers_v8.db` 78,720 satır canlı; `reextract_answer_keys.py:494-521,139-170,404`; bucket tablosu | cevap (1°) | **P0** | **ROOT** | A-bias semptomunun üreticisi; R13 bunu yanlış soruya yapıştırıyor |
| **R13** | **Cevap↔soru bağı "sayfa pozisyonu" ile (içerik eşleşmesi değil)** | OCR soru_no ile DB qnum **%40.9 sayfa-çiftinde HİÇ örtüşmüyor**; bu durumda cevap ordinal pozisyona atanıyor → "harf doğru, yanlış soruya yapışmış" | `match_crop_answers.py:20,26,27-29`; çekirdek match `pipeline.py:2902-2924` tek-sinyal q_no; fallback `2906-2913` YOLO index | cevap (1°), görsel | **P0** | **ROOT** | R4/R5/R6 ile aynı sınıf; R12 biased harfi yanlış soruya bağlar |
| **R14** | **Çekirdek soru-cevap matching TEK-SİNYAL (q_number); gate yok, YOLO-index fallback** | `(book,page,q_no)` lookup, Jaccard yok; boş/sayısal-olmayan q_no sadece -5/-10 ceza, yine de match; q_no parse edilemezse YOLO `question_index` fallback → conf≥70 ile production'a | `pipeline.py:2902-2924,2906-2913,2305-2310,2948-2953`; CLAUDE.md çift-sinyal kuralı sadece image-mapping'e uygulanmış | cevap (1°), metin | **P0** | **ROOT** | R12'yi besler; R4 ile aynı temel hata (non-det. Gemini/YOLO kimliği → det. anahtar) |
| **R15** | **"İnsan ground-truth" aslında AI auto-verify (görsel gösterilmeden PI kopyalanıyor)** | `--auto-verify` PI cevabını insan cevabı olarak kopyalar; ground_truth_v1.jsonl 600/600 AYNI saniye timestamp, mismatch=0, dağılım byte-identik; "%100 RELIABLE" tautolojik | `build_ground_truth_sample.py:428-430`; `ground_truth_v1.jsonl` 600 satır; `ground_truth_analysis.json acc=1.0`; `validate_ground_truth.py` gate=FAIL ama durdurmadı | cevap (1°), tüm ölçüm | **P0** | **ROOT** | Dairesel zincirin en altı; R12/R13/R14 hatalarını hiç yakalamadı |
| **R16** | **page_inline kaynağı tek-engine (Gemini 2.0 Flash), tek-crop alt-%20, doğrulamasız** | Konsensüs/2. model/insan yok; sabit `BOTTOM_CROP_RATIO=0.20` (kitap-kalibrasyonsuz); `"NO"/"YOK"` ASCII alt-dizi yanlış-pozitif veri kaybı; gevşek regex `(\d{1,3})\s+([A-E])` | `phase4_page_inline_answers.py:58,63,215,107,123` | cevap (1°) | **P0** | **ROOT** | R12'nin altyapısı; tek-engine = R14 ile aynı tek-sinyal felsefesi |
| **R17** | **Bayesian `ai_upgrade` over-weighting (S194 bug) — FIX'Lİ ama kalıntı yapısal** | Eski: `ai_upgrade`→`ai_solved`(0.85) tier → A-reddi. **FIX uygulandı** (`:114 ai_upgrade:0.65`). KALINTI: tie-break (0.02) orijinal A/E'yi koruyor; ANTI_BIAS_PRIOR sadece 2+ güçlü kaynakta → tek-kaynak page_inline'da KAPALI | `cross_validate_answers.py:114,268-278` (fix canlı); `:93,411-420,542` (kalıntı) | cevap | P1 (gelecek) / DB kontamine | SYMPTOM (bug kapandı) + yapısal kalıntı ROOT | Audit doc gövdesi STALE; eski DB temizliği Curator'da |
| **R18** | **Kitap-adı eşleştirmeye Türkçe-locale `I→ı` uygulanıyor + normalizasyon KANONİK DEĞİL** | `normalize_tr` ASCII kitap-adına I→ı: ACIL→acıl, AKTIF→aktıf; 3 script 3 farklı kural (match_simple full / cross_validate NFC-only / create_v8 ham) → sessiz join kaybı | `match_simple_v4.py:27-33,45,59,78`; `cross_validate_answers.py:159-170`; `create_answers_v8.py:134,140,40-41` (nfc tanımlı, uygulanmıyor) | cevap (book+page join), görsel | P1 | ROOT (yanlış kural seçimi + kanoniklik boşluğu) | R13/R14 join'lerinin determinizmini ek bozuyor |
| **R19** | **OCR metni depolama anında NFC-normalize edilmiyor** | Çıktı verbatim saklanıyor; NFD/görünmez karakter → Jaccard sim yanlış düşük (çift-sinyal zayıflar) + okunabilirlik düşer | `ocr_crops.py` NFC grep=0; NFC ilk olarak downstream (`cross_validate:161`, `match_simple:31`); `parse_question_from_ocr` normalize etmiyor | metin, görsel-sim, cevap-sim | P2 | SYMPTOM-AMPLIFIER (asıl garble R1/R2) | ÇİFT-SİNYAL Hard Rule'u zayıflatıyor |
| **R20** | **Funnel'da provenance silme: dedup "son kazanır", sinyal-izi yok** | v2.4→v3.5 elemeleri kaynak-ETİKETİNE göre; satır-bazlı (matched_by/sim/crop_path) iz yok → temizlik "neden bu cevap" türetemiyor; çakışan test_no sessiz eziliyor | `create_answers_v8.py:131-141,13`; `cross_validate:258-296` source-string parse | üçü de | P1 | ROOT (temizlik yanlış sinyale güveniyor) | R8 (görsel provenance) ile aynı sınıf |
| **R21** | **Kalite gate'i FORMAT/yapı katmanını ölçüyor, öğrenci-okunabilirliğini DEĞİL** | `validate_sample.py` 13-check tamamı JSON-şema/kaba OCR-çöp; "loylak" NFC-normal+ASCII+tekrarsız → PASS; aynı havuz coherence tam-run %60 drop, garbled %63 | `validate_sample.py:75,94,104,117,136,160,200,209,236`; `goldpool_coherence_pilot.md:64-67` | metin (1°), görsel+cevap dolaylı | **P0** | **ROOT** | R15/R22 ile birleşince sistematik hata "PASS" görünüyor |
| **R22** | **Kabul kapısı chi-square uniformluğunu "doğruluk" sanıyor (Goodhart)** | `chi_sq<9.49 → PASS(uniform)`; ANTI_BIAS_PRIOR dağılımı yapay düzleştirip PASS gösterebilir; YKS dağılımı zaten uniform değil → yapısal yanlış katman | `cross_validate_answers.py:368-384,711-712`; `:125 tier1:0.85 (placeholder until human GT)` | ölçüm/meta (cevap maskeliyor) | P1 | ROOT (yanlış metrik) | R15 dairesellikle aynı kök |
| **R23** | **OCR prompt figürü tarif etmiyor → figür-bağımlı soru "ölçülemez-doğru" doğuyor** | Prompt sadece metin transkribe; figür/grafik içerik üretilmiyor; downstream hiçbir check figür-eksikliğini flag'lemiyor (has_image bile PASS) | `pipeline.py:290 _BASE_OCR_PROMPT`; validate_sample figure/image check=0; coherence figure_dependent=1,880 | görsel+metin | P1 | ROOT (modalite kaybı) / ölçümde semptom | R11 (filtre) ile birleşince çözülemez soru sızıyor |
| **R24** | **Vanity-metrik (soru-sayısı) gerçek metriği aktif gizledi** | "45K→%172 EXCEEDED 🟢", "Quality 100% 🟢" format/sayı; v_safe_for_beta 23,417→10,535 drift (raporlanan değer bile hayali); gerçek temiz ~5,323/167,559 = %3.2 | CLAUDE.md status; MEMORY drift; `goldpool_coherence_pilot.md:18` | üçü de (meta) | P1 | PEKİŞTİRİCİ (R21/R22 sonucunu "başarı" çerçeveledi) | Düzeltici baskıyı yok etti |
| **R25** | **Audit/test döngüsü dalga-İÇİ kapanıyor, proxy-artifact gerçek-sinyal sayıldı** | "audit yazıldı + 5/5 consensus" = kapanış; S197 meta-audit 8 P0'ın %75'i phantom; aynı ÖLÇÜM hatası (tek-sinyal/truncation) 2-3 kez tekrarladı | S197 meta-audit; `.claude/rules/` 4 kural aynı sınıftan; `audit-methodology.md` LEFT(200) %24-vs-%2.15 | üçü de (meta) | P1 | PEKİŞTİRİCİ/süreç | R15 dairesellikle aynı kök (döngü-dışı referans yok) |

---

## BÖLÜM 2 — EN ÜST 5 KÖK-NEDEN (semptomlar elendi)

Bu beş kök-neden zincirin **tabanında**; çözülmezse üst-katman fix'ler (Tier matcher'ları,
Curator, anti-bias) marjinal kalır. Her biri birden çok ekseni aynı anda tavanlıyor.

### KÖK #1 — Kaynak çözünürlük tavanı + telafi yokluğu (R1 + R2)
**Birleşik:** Girdi 1080p screen-capture (R1) + pipeline upscale yapmıyor, 1024 cap (R2).
Median crop ~9px/karakter → VLM soft-decode → **garbled metnin (%63 drop) doğrudan kökü.**
Metin-eksenindeki başka her şey (NFC, validate) bu olmadan boşa. **Tek en yüksek kaldıraç:**
yüksek-zoom/yüksek-DPI capture + OCR-öncesi 2-3x upscale. Kanıt: ölçülen crop 352px,
upscale grep=0, W4r notu upscale hatayı %20-40 azaltıyor.

### KÖK #2 — Soru↔crop deterministik bağ ingest'te kurulmadı (R4 + R5)
Crop+OCR+ingest ayrı pipeline'lar; ortak değişmez anahtar yok; `crop_path` ingest'te VAR
ama kullanılmıyor (`pipeline.py:3315`). 19+ matcher + Tier H 49,468-satır rollback bunun
geri-mühendislik telafisi. **Görsel-eşleşme ekseninin tamamının kökü.** Fix: crop üretirken
aynı bbox'tan OCR + crop_file'ı INSERT'te yaz (deterministik 1:1); geriye dönük `*_meta.json`
tek otorite + çift-sinyal raptetme.

### KÖK #3 — Cevap kaynağı tek-engine + pozisyon-eşleşme + dairesel GT (R12 + R13 + R15 + R16)
A/E bias bir semptom; kökü: page_inline tek-engine Gemini-Flash, doğrulamasız (R16) →
düşük-qnum'a çöküyor, A/E orada yoğun (R12) → biased harf %40.9 ZERO-overlap sayfalarda
ordinal pozisyonla yanlış soruya yapışıyor (R13) → ve **hiçbir noktada gerçek-dünya doğru
cevabıyla temas yok** çünkü "insan GT" auto-verify kopyası (R15). Cevap-ekseni dairesel
kapalı. Fix: çok-model konsensüs cevap-OCR + çift-sinyal (içerik) eşleşme + GERÇEK insan-GT
(>=300, `--auto-verify` YASAK).

### KÖK #4 — Crop birimi cevap sızdırıyor → görsel ürün-katmanında ölü (R9 + R10 + R11)
YOLO `'soru'` crop'u şıkları içerir (R9, deterministik) → leak refleksiyle frontend `false &&`
TÜM görseli gizler (R10) → figure-dependent soru görselsiz, tutarsız filtreyle havuzda kalır
(R11). Sonuç: sorular %100 görsel-türevli ama görsel KAPALI → **içerik ne kadar iyileşse de
görsel-bağımlı sınıfta kalite tavanı = görselsiz-çözülebilen kısım.** On-binlerce satır
image-match emeği 0 öğrenci-değeri üretti. Fix sıralaması: önce temiz figure-crop (R9),
sonra suppress kaldır (R10), filtreyi subject-bağımsız figure-flag'e çevir (R11).

### KÖK #5 — Kalite hiç öğrenci-katmanında + döngü-dışı referansla tanımlanmadı (R21 + R22 + R15)
Gate format/dağılım ölçtü (R21+R22), referans dairesel (R15) → sistematik hata (garble,
figür-kaybı, A-bias) tüm kaynaklar paylaştığı için "anlaşma/PASS" göründü. **198 oturum
boyunca problemin görünmez kalmasının yapısal sebebi.** Vanity-metrik (R24) + audit-as-progress
(R25) bunu "başarı" çerçeveleyip düzeltici baskıyı sildi. Fix: gate'i render-artifact üzerinde
**kör-bağımsız-çözüm**'e çevir (DB-cevabı verilmeden çözdür, sonra keyed cevapla kıyasla) —
31 May coherence pilotu bu aracı zaten kanıtladı (%60 drop yakaladı).

---

## BÖLÜM 3 — Master Bağlantı Haritası (kökler birbirini nasıl besliyor)

```
                    ┌─────────────────────── META / ÖLÇÜM ───────────────────────┐
                    │ KÖK#5: gate format+dağılım ölçtü (R21,R22) + dairesel GT (R15)│
                    │ → R24 vanity-metrik "başarı" + R25 audit-as-progress         │
                    │ = sistematik hata 198 oturum GÖRÜNMEZ kaldı                  │
                    └──────────────────────────┬──────────────────────────────────┘
                                                │ (her şeyi maskeledi)
        ┌───────────────────────┬──────────────┼───────────────────────┐
        ▼                       ▼              ▼                        ▼
 ┌─────────────┐        ┌──────────────┐ ┌──────────────┐      ┌──────────────┐
 │ METİN        │        │ SORU-GÖRSEL  │ │ SORU-CEVAP   │      │ GÖRSEL-ÜRÜN  │
 │ KÖK#1        │        │ KÖK#2        │ │ KÖK#3        │      │ KÖK#4        │
 │ R1 1080p ───→│        │ R4 bağ yok ─→│ │ R16 tek-eng ─│      │ R9 crop=blok │
 │ R2 upscale yok        │ R5 3×q sem.  │ │ R12 qnum çök │      │   →leak      │
 │ →garble (R3 │        │ →R6 TierH    │ │ →A/E bias    │      │ →R10 false&& │
 │  dead, R19  │        │ →R7 sayım    │ │ →R13 pozisyon│      │   gizli      │
 │  amplify)   │        │ →R8 19 sürüm │ │   yanlış soru│      │ →R11 filtre  │
 └─────┬───────┘        └──────┬───────┘ │ →R14 tek-sin │      │   eksik      │
       │                       │         │ →R17 Bayesian│      └──────┬───────┘
       │ R18 I→ı + non-canonical book-key│   (fix'li)   │             │
       │ R20 provenance silme ───────────┴──────┬───────┘             │
       └────────────────────────────────────────┴─────────────────────┘
                          ORTAK META-KÖK: "non-deterministic Gemini/YOLO türevi kimliği
                          deterministik anahtar gibi kullan + 2. sinyalle teyit etme"
                          (R4, R5, R6, R13, R14 hepsi bu sınıf; CLAUDE.md çift-sinyal kuralı
                          sadece image-mapping'e uygulanmış, çekirdek match + crop-isim hariç)
```

**En kritik tek müdahale:** ÖLÇÜM KÖKÜ (KÖK#5) — çünkü R1-R20'nin hangisinin gerçek/ne kadar
yaygın olduğunu **ancak döngü-dışı kör-çözüm gate ölçebilir.** Pilot zaten kanıtladı. Ölçüm
düzelmeden içerik fix'leri yine kör uçar.

**İçerik tarafında en yüksek kaldıraç sırası:** KÖK#1 (garble kaynağı, %63 drop) → KÖK#4
(görsel ürün-tavanı, on-binlerce satır 0-değer) → KÖK#3 (cevap dairesel) → KÖK#2 (eşleşme bağı).

---

## BÖLÜM 4 — Çakışan / Çelişen / Phantom Bulgular (dürüstlük)

| Konu | Çakışma/Çelişki | Çözüm |
|---|---|---|
| **"Tek-OCR-engine"** | OCR eksen-1: framing kısmen PHANTOM — Gemini Flash→Pro **fallback** var. Cevap eksen-2: page_inline gerçekten tek-engine (Flash). | İki AYRI pipeline: SORU-OCR'da fallback var (R5'te K5: gerçek kök doğrulama-tetikleyici yok); CEVAP-OCR'da (page_inline) gerçekten tek-engine (R16). İkisi karıştırılmamalı. |
| **A/E bias mekanizması** | Eksen-5 (abias): asıl kök **R12 page_inline qnum-çökmesi (%53)**, Bayesian %14. Eksen-6 (groundtruth): R16 tek-engine. | UYUMLU, tamamlayıcı: R16 (kaynak tek-engine) → R12 (qnum çökme + A/E orada yoğun). Bayesian (R17) zincirin ORTASI, fix'li. |
| **Bayesian ai_upgrade bug** | Audit doc gövdesi `:265-266 return "ai_solved"` STALE; kod `:114 ai_upgrade:0.65` FIX'Lİ (S194, 78/78 PASS). | PHANTOM (fix'lenmiş). ROOT olarak SAYILMADI; R17 kalıntı (tie-break + tek-kaynak anti-bias-bypass) gerçek yapısal risk. |
| **calibrate_yayinevleri.py / finalize_calibration.py** | CLAUDE.local.md + briefing referanslı; **diskte YOK** (find ile tarandı). | PHANTOM dosya iddiası. Sadece `kitap_crop_coords.json` + `crop_preprocessor.py` var; kalibrasyon ana pipeline'a (R4 alanı) hiç bağlı değil (doğrulandı). |
| **question_image_url coverage** | Brifing %52-99 çelişik kayıt. | İkisi de "kayıt var" anlamında doğru; ama R9/R10 nedeniyle coverage RAKAMI önemsiz — görsel render KAPALI, leak'li → fonksiyonel coverage ~0 (öğrenci görmüyor). |
| **Tier H scripti** | Rollback edildi ama `tier_h_qip_exact.py` + `tier_h_v2` diskte DURUYOR. | Phantom DEĞİL — tekrar-çağrılma riski P1; `_deprecated/`'a taşı veya `sys.exit(DEPRECATED)` ekle. |
| **NFC `errors="replace"`** | İçerik kaybı şüphesi. | İçerik path'inde DEĞİL, yalnız stdout reconfigure (doğrulandı). Şimdilik kayıp YOK ama desen riskli (R19 notu). |
| **Çift-sinyal kuralı kapsamı** | CLAUDE.md "ÇİFT SİNYAL ZORUNLU" var → ama eksen-3+7: yalnız image-mapping'e uygulanmış; çekirdek soru-cevap match (R14) ve crop-isimlendirme (R4) hariç. | Kural VAR ama kapsam EKSİK — gerçek bulgu, phantom değil. CI/lint ile çekirdek match'e genişlet. |

---

## BÖLÜM 5 — Şiddet Dağılımı

- **P0 (12):** R1, R2, R4, R5, R6, R9, R10, R11, R12, R13, R14, R15, R16, R21 — kök/ürün-tavanı.
- **P1 (8):** R3, R7, R8, R17, R18, R20, R22, R23, R24, R25 — operasyonel/yapısal-kalıntı/meta.
- **P2 (2):** R19 (amplifier), regex-pattern (eksen-5 KÖK3, düşük blast-radius).

*Tüm kod iddiaları 31 May 2026 canlı dosyalarda satır-doğrulandı. Phantom'lar BÖLÜM 4'te işaretli.*
