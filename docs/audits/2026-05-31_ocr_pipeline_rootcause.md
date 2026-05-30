# FINAL — Nihai Sıralı Kök-Neden Raporu (KIRO2 İçerik Kalitesi)

**Tarih:** 31 May 2026
**Soru:** Defalarca OCR yapıldı, görseller eklendi, 198 oturum çalışıldı — ama soru-görsel,
soru-cevap ve metin doğruluğu istenen seviyeye NEDEN çıkmadı? (semptom değil **kök neden**)
**Girdi:** 8 eksen bulgusu + sentez + 3 adversarial challenge (determinism / evidence / depth).
**Yöntem:** Her load-bearing iddia canlı `dosya:satır` ile doğrulandı. 3 skeptik tur "şüpheli=çürütüldü"
varsayımıyla TOP 5 kökü çürütmeyi denedi: **5/5 DOĞRULANDI, 0 çürütüldü.** Phantom filtresi uygulandı.

---

## 1. Yönetici Özeti

Kalite hiçbir zaman "yeterince iyi" olmadı çünkü **problem ölçülmedi, ölçülemedi ve aktif olarak
gizlendi.** En derin kök bir teknik bug değil, bir **ölçüm-tasarımı çöküşü**: kalite kapısı
yalnızca FORMAT/dağılım katmanını ölçtü (JSON-şema, chi-square uniformluk), öğrenci-okunabilirliğini
hiç ölçmedi; ve tek "doğruluk referansı" dairesel (`--auto-verify` ile AI kendi cevabını "insan
ground-truth" diye kopyalamış — 600/600 mismatch=0, tek timestamp). Bu iki şey birleşince sistematik
hata (garbled metin, figür-kaybı, A/E-bias) tüm kaynaklarda ortak olduğu için "anlaşma/PASS" göründü.
İçerik tarafında üç bağımsız fiziksel/mimari tavan bunun altında yatıyor: (1) kaynak görüntü 1080p
ekran-yakalama + pipeline'da hiç upscale yok → ~9px/karakter → garbled metin; (2) soru↔crop arasında
ingest-anında deterministik bağ HİÇ kurulmadı → 19+ heuristik matcher + Tier H 49,468-satır rollback;
(3) crop birimi tüm soru bloğu (şıklar dahil) → cevap sızıntısı → frontend `false &&` ile TÜM görseller
kalıcı gizli → on-binlerce satır image-match emeği 0 öğrenci-değeri üretti. Vanity-metrik ("45K→%172
EXCEEDED 🟢", "Quality 100% 🟢") ve audit-as-progress (S197: 8 P0'ın %75'i phantom) bu durumu "başarı"
çerçeveleyip düzeltici baskıyı sildi. Sonuç: gerçek temiz soru ~5,323/167,559 ≈ **%3.2**, raporlanan
"%100 PASS"a karşı 30x uçurum.

---

## 2. TOP Kök-Neden Tablosu (sıralı, adversarial sonrası güven)

| # | Kök-neden | Mekanizma (özet) | Kanıt (dosya:satır / artifact) | Eksen | Şiddet | Güven (adv. sonrası) | Fix-yönü |
|---|---|---|---|---|---|---|---|
| **K1a** | **Kalite gate yanlış katmanı ölçüyor (format, okunabilirlik değil)** | `validate_sample.py` 13-check'in tamamı JSON-şema/kaba OCR-çöp; "loylak/bilkidir" NFC-normal+ASCII+tekrarsız → PASS. Aynı havuz coherence tam-run %60 drop, garbled %63 | `validate_sample.py:75,94,104,117,136,160,200,209,236`; `goldpool_coherence_pilot.md:64-67` | meta/üçü | **P0** | **KESİN** (fonksiyon gövdeleri bizzat doğrulandı) | Gate'i render-artifact üzerinde **kör-bağımsız-çözüm**'e çevir |
| **K1b** | **Ground-truth dairesel — 0 bağımsız insan onayı** | `--auto-verify` PI cevabını "insan cevabı" kopyalıyor; `ground_truth_v1.jsonl` 600 satır TEK timestamp, mismatch=0, dağılım byte-identik, verifier="human" SAHTE etiket; "%100 RELIABLE" tautolojik | `build_ground_truth_sample.py:428-430`; jsonl 600 satır canlı; `ground_truth_analysis.json acc=1.0`; `validate_ground_truth.py gate=FAIL` ama durdurmadı | meta/cevap | **P0** | **KESİN** (canlı veri ile tautoloji ispatlandı) | Gerçek insan-GT (≥300, görsel zorunlu); `--auto-verify` YASAK; tüm GT-bağımlı kalibrasyonu invalide et |
| **K2a** | **Kaynak görüntü 1080p ekran-yakalama (PDF render değil)** | DRM viewer `pyautogui.screenshot()` tam-ekran; A4 1080p'de ~975px (200 DPI'da ~2339px) → ~2.4x çözünürlük kaybı kaynakta, geri kazanılamaz | `auto_screenshot.py:38`, `screenshot.py:30,56`; ölçülen `sayfa_0001.png=(1920,1080)` 3 kitap; `config.yaml:68 max_image_size:1024` | metin/cevap/görsel | **P0** | **YÜKSEK** (R1 ölçümü sentezden miras; mekanizma sağlam) | Yüksek-zoom/yüksek-DPI capture; PDF varsa `pdf2image` 300 DPI |
| **K2b** | **Pipeline'da UPSCALE yok; sadece downscale + 1024 cap** | Tüm resize çağrıları `if max(...) > max_dim:` guard'lı (yalnız küçültme); enlarge dalı yok; median crop **352px → ~9px/karakter** → VLM soft-decode → "loylak" sınıfı | `script_common.py:123-126,631,1021,1113` (hepsi downscale-guard, **bizzat doğrulandı**); `config.yaml:102-103`; upscale grep=0 | metin/cevap | **P0** | **KESİN** (kod path bizzat doğrulandı) | OCR-öncesi 2-3x LANCZOS upscale (min-boyut hedefi); W4r: hatayı %20-40 azaltır |
| **K3** | **Soru↔crop deterministik bağ ingest'te HİÇ kurulmadı** | INSERT'te `question_image_url`/`crop_file` doldurulmuyor; kimlik `uuid5(book\|page\|q_num)`, q_num=Gemini OCR test-no; crop ise YOLO bbox `(y1,x1)` uzamsal sırası — ortak değişmez anahtar yok → 19+ post-hoc heuristik matcher | `backend/scripts/import_d_dataset.py:160-163,223-278,344-360` (**yol düzeltildi**: backend/, d-dataset/ değil); `crop_from_detections.py:266-274`; `pipeline.py:3315` (crop_path VAR, kullanılmıyor) | görsel/cevap/metin | **P0** | **YÜKSEK** (mekanizma; Tier H rollback `6a3fa7fc0` bağımsız teyit) | Crop+OCR+ingest'i tek pipeline'da birleştir; crop_path'i INSERT'te yaz (det. 1:1) |
| **K4a** | **Crop birimi = tüm soru bloğu → cevap sızıntısı deterministik** | YOLO `'soru'` kutusu stem+figure+A-E şıkları içeriyor; "figure-only" sınıf yok; vision-audit ampirik "TÜM url'ler leak içeriyor" | `pipeline.py:164-166,709,714,682-688`; `populate_image_urls_tier_c.py:14-16`; `beta_eligible_filter_v2.py:33-34` | görsel/metin | **P0** | **YÜKSEK** (DÜZELT: YOLO'da 'cevaplar' AYRI sınıf var ama saha-pratiğinde 'soru' bbox şıkları kapsıyor — leak ampirik teyitli) | Temiz figure-crop (soru−cevaplar farkı veya figür-dedektör); yeniden-crop gerek |
| **K4b** | **Frontend `false &&` ölü-devre: TÜM görseller kalıcı gizli** | Leak sızmasın diye render derleme-zamanı `false` ile kapatılmış; leak'siz meşru figürler de gizli → figure-dependent soru görselsiz, çözülemez | `frontend/src/components/Exam/ModernOSYMExamInterface.tsx:551` (**yol düzeltildi**: components/Exam/, pages/ değil); git blame `9094dd50c` 21 May, 10+ gün canlı | görsel (ürün) | **P0** | **KESİN** (satır + git-blame bizzat doğrulandı) | K4a çözülmeden kaldırma YASAK; sıra: temiz crop → suppress kaldır |
| **K5** | **page_inline cevap-OCR düşük-qnum'a çöküyor → A/E bias orada yoğun** | answers_page_inline %53 kaynak; AVG 1.9 cevap/sayfa, qnum≤5 payı %80.2; A+E q1-5'te %54, q6+ %37 (uniform) → bias içerikten değil, grid'i lokal-qnum'a çökertmekten; B yutuluyor (%11.3) | `answers_v8.db` 78,720 satır; `reextract_answer_keys.py:494-521,139-170,404`; bucket tablosu | cevap | **P0** | **YÜKSEK** (R16 üretici-mekanizma bizzat doğrulandı; R12 DB-istatistiği sentezden miras) | quality_check'e A+E>%46 bias-guard; multi-test grid lokal→global qnum mapping |
| **K6** | **Cevap↔soru bağı sayfa-pozisyonuyla (içerik eşleşmesi değil)** | OCR soru_no ile DB qnum **%40.9 sayfa-çiftinde HİÇ örtüşmüyor**; o durumda cevap ordinal pozisyona atanıyor (Tier 1B) → "harf doğru, yanlış soruya yapışmış" | `match_crop_answers.py:20,26,27-29` (header BİZZAT "40.9% ZERO overlap" + "+78.5% improvement" diye övülmüş); `pipeline.py:2902-2924` | cevap/görsel | **P0** | **YÜKSEK** (header bizzat doğrulandı; %40.9 DB re-query gerekiyor) | Pozisyon-eşleşmeyi çift-sinyalle (Jaccard≥0.50) zorla; pozisyon-only → low_confidence/Curator |
| **K7** | **page_inline kaynağı tek-engine (Gemini 2.0 Flash), tek-crop, doğrulamasız** | Konsensüs/2.model/insan yok; sabit `BOTTOM_CROP_RATIO=0.20`; `"NO"/"YOK"` ASCII alt-dizi yanlış-pozitif veri kaybı; gevşek regex `(\d{1,3})\s+([A-E])` | `phase4_page_inline_answers.py:58,63,107,215` (**4/4 bizzat doğrulandı**, "NO" bug dahil) | cevap | **P0** | **KESİN** (verbatim doğrulandı) | Çok-model konsensüs; cevap-anahtarına özel crop kalibrasyonu; "NO" word-boundary'e |
| **K8** | **Çekirdek soru-cevap matching TEK-SİNYAL (q_number); gate yok, YOLO-index fallback** | `(book,page,q_no)` lookup, Jaccard yok; boş/sayısal-olmayan q_no sadece -5/-10 ceza yine match; parse edilemezse YOLO `question_index` fallback → conf≥70 production'a | `pipeline.py:2902-2924,2906-2913,2305-2310,2948-2953`; CLAUDE.md çift-sinyal kuralı sadece image-mapping'e uygulanmış | cevap/metin | **P0** | **YÜKSEK** (kod doğrulandı) | Sayısal-olmayan q_no → match YAPMA (pending); YOLO-index fallback YASAK; çift-sinyal |
| **R6/K9** | **Tek-sinyal eşleşme → Tier H 49,468 satır YANLIŞ (ROLLBACK)** | `q_index_in_page` exact filename match, Jaccard atlandı; 0/1-index kayması yakalanamadı | `tier_h_qip_exact.py:132,27-31`; `rollback_tier_h.sql`; Tier F karşıt key+sim≥0.50→%100(49/49) | görsel | P0 gerçekleşti / P1 tekrar-riski | **KESİN** (rollback gerçek) | `tier_h_*.py` → `_deprecated/` veya `sys.exit(DEPRECATED)`; çift-sinyal CI/lint |
| **K10** | **Crop count ≠ DB count → pozisyonel eşleşme zemini kayıyor** | v15a son-çare matcher NULL satırları bbox Y-sırasına eşliyor; `db_max==disk_max` sadece 3/100 sayfa | `image_match_v15a:97-103`; audit Aşama C 100 sayfa; `v15_page_fallback` tüm-sayfa itirafı | görsel | P1 | YÜKSEK | Sayfa-içi count invariant'ı eşleşme ön-koşulu yap |
| **K11** | **19+ matcher sürümü → izlenemez provenance** | Her başarısızlık yeni sürüm; hangi satır hangi tier/güvenle eşleşti belirsiz; tier_c flag hiç yazılmadı | 19 image_match*.py + tier scriptleri; audit "tier_c_match flag YAZILMAMIŞ" | görsel/meta | P1 | YÜKSEK | Tek kanonik `pipeline_metadata.image_match` şeması; yeni sürüm öncesi %100 provenance |
| **K12** | **Figür-bağımlı sorular havuzdan TUTARSIZ dışlanıyor** | Backend filtresi yalnız GEO/FİZİK + (görsel yok VE metin<500); diğer derslerde figure-dependent metin-only sızıyor; `URL NOT NULL` "OK" sayılıyor ama render edilmiyor | `osym_exam_engine.py:1277-1282`; coherence figure_dependent=1,880; `_select_beta_questions:1166-1205` | görsel/metin | P0 standart / P1 beta-flag | YÜKSEK | Filtreyi subject-bağımsız figure-flag'e çevir |
| **K13** | **OCR prompt figürü tarif etmiyor → figür-bağımlı soru "ölçülemez-doğru" doğuyor** | Prompt sadece metin transkribe; figür içerik üretilmiyor; hiçbir check figür-eksikliğini flag'lemiyor (has_image bile PASS) | `pipeline.py:290 _BASE_OCR_PROMPT`; validate_sample figure-check=0; coherence figure_dependent=1,880 | görsel/metin | P1 | YÜKSEK | Figür-bağımlıyı gate'te ayrı sınıfla; re-OCR'da figür-tarif prompt |
| **K14** | **Bayesian `ai_upgrade` over-weighting — FIX'Lİ; kalıntı tie-break + tek-kaynak anti-bias-bypass** | Eski: ai_upgrade→ai_solved(0.85)→A-reddi. **FIX canlı** (`:114 ai_upgrade:0.65`). KALINTI: tie-break(0.02) orijinal A/E koruyor; ANTI_BIAS_PRIOR sadece 2+ güçlü kaynakta → tek-kaynak page_inline'da KAPALI | `cross_validate_answers.py:114,268-278` (fix canlı); `:93,411-420,542` (kalıntı) | cevap | P1 gelecek / DB kontamine | **KESİN** (fix bizzat doğrulandı — PHANTOM) | Anti-bias'ı tek-kaynakta da uygula; tie-break A/E korumasını kaldır; eski DB Curator'a |
| **K15** | **Kitap-adı join'e Türkçe-locale I→ı + normalizasyon KANONİK DEĞİL** | `normalize_tr` ASCII kitap-adına I→ı: ACIL→acıl, AKTIF→aktıf; 3 script 3 farklı kural (match_simple full / cross_validate NFC-only / create_v8 ham) → sessiz join kaybı | `match_simple_v4.py:27-33,45,59,78`; `cross_validate_answers.py:159-170`; `create_answers_v8.py:134,140,40-41` | cevap/görsel | P1 | YÜKSEK | ASCII-safe `book_key()` (NFC+str.lower, I→ı YOK), 3 script import etsin |
| **K16** | **Funnel'da provenance silme: dedup "son kazanır", sinyal-izi yok** | v2.4→v3.5 elemeleri kaynak-ETİKETİNE göre; satır-bazlı (matched_by/sim/crop_path) iz yok → temizlik "neden bu cevap" türetemiyor | `create_answers_v8.py:131-141,13`; `cross_validate:258-296` | üçü | P1 | YÜKSEK | Satır-bazlı sinyal-izi yaz; dedup'ta güven-tabanlı seçim + çakışma logu |
| **K17** | **Çözünürlük teşhisi VAR ama OCR döngüsüne bağlı DEĞİL (dead code) + eşik yanlış** | `full_image_quality_assessment` `pdf_low_dpi` etiketliyor ama pipeline çağırmıyor; eşik `width<300` (median 352 üstünde) | `script_common.py:1665,1679,1686-1687`; pipeline grep `is_low_resolution`=0 | metin | P1 | YÜKSEK | Teşhisi OCR-öncesi gate yap; eşiği etkin-karakter-genişliği bazlı kalibre |
| **K18** | **Vanity-metrik (soru-sayısı) gerçek metriği aktif gizledi** | "45K→%172 EXCEEDED🟢", "Quality 100%🟢" format/sayı; v_safe_for_beta 23,417→10,535 drift; gerçek temiz ~5,323/167,559=%3.2 | CLAUDE.md status; MEMORY drift; `goldpool_coherence_pilot.md:18` | meta | P1 | YÜKSEK | Tek geçerli sayı: okunabilir∧çözülebilir∧bağımsız-doğrulanmış; ham sayıyı "ham" etiketle |
| **K19** | **Audit/test döngüsü dalga-İÇİ kapanıyor; proxy-artifact gerçek-sinyal sayıldı** | "audit yazıldı + 5/5 consensus" = kapanış; S197 8 P0'ın %75'i phantom; aynı ölçüm hatası 2-3 kez tekrarladı | S197 meta-audit; `.claude/rules/` 4 kural aynı sınıftan; `audit-methodology.md` LEFT(200) %24-vs-%2.15 | meta | P1 | YÜKSEK | Hiçbir kalite-task ≥1 gerçek beta-kullanıcı önüne çıkana dek "tamamlandı" sayılmaz |
| **K20** | **OCR metni depolama anında NFC-normalize edilmiyor** | Çıktı verbatim saklanıyor; NFD/görünmez karakter → Jaccard sim yanlış düşük (çift-sinyal zayıflar) + okunabilirlik düşer | `ocr_crops.py` NFC grep=0; NFC ilk olarak downstream; `parse_question_from_ocr` normalize etmiyor | metin/sim | P2 | YÜKSEK (amplifier) | Yazma öncesi `normalize("NFC")` + zero-width strip; içerik I/O'da `errors="replace"` YASAK |

---

## 3. Kök-Neden Zinciri / Bağımlılık Haritası

```
        ┌──────────────────────── META / ÖLÇÜM (en derin) ─────────────────────────┐
        │ K1a gate format ölçtü (okunabilirlik DEĞİL) + K1b dairesel GT (0 insan onay)│
        │   → K18 vanity-metrik "başarı" çerçeveledi + K19 audit-as-progress          │
        │   = sistematik hata 198 oturum GÖRÜNMEZ kaldı; düzeltici baskı silindi      │
        └────────────────────────────────┬───────────────────────────────────────────┘
                                          │ (her ekseni maskeledi — hiçbiri sinyal üretmedi)
     ┌────────────────────┬───────────────┼────────────────────┬─────────────────────┐
     ▼                    ▼               ▼                    ▼                     ▼
 ┌─────────┐       ┌────────────┐   ┌────────────┐      ┌────────────┐       ┌──────────────┐
 │ METİN    │       │ SORU-GÖRSEL │  │ SORU-CEVAP  │      │ GÖRSEL-ÜRÜN │      │ ENCODING/JOIN │
 │ K2a 1080p│       │ K3 bağ yok  │  │ K7 tek-eng  │      │ K4a crop=blok│     │ K15 I→ı +     │
 │ K2b ups.yok→     │ (uuid5 q_num│  │ K5 qnum çök │      │  →leak      │      │  non-canonical │
 │  garble  │       │  ≠ YOLO idx)│  │  →A/E bias  │      │ K4b false&& │      │  book-key      │
 │ (K17 dead│       │ →K9 TierH   │  │ K6 pozisyon │      │  TÜM gizli  │      │ K16 provenance │
 │  K20 amp)│       │ →K10 sayım  │  │  yanlış soru│      │ K12 filtre  │      │  silme         │
 │          │       │ →K11 19 sür.│  │ K8 tek-sin. │      │  eksik      │      │ K20 NFC yok    │
 └────┬─────┘       └─────┬──────┘  │ K14 Bayesian│      │ K13 figür   │      └──────┬───────┘
      │                   │         │  (fix'li)   │      │  prompt yok │             │
      │                   └─────────┴──────┬──────┴──────────┴──────────────────────┘
      └──────────────────────────────────┬─┘
                                          │
        ORTAK META-KÖK (kısmi): "non-deterministik Gemini/YOLO türevi kimliği
        deterministik anahtar gibi kullan + 2. sinyalle teyit etme"
        → K3, K6, K8, K9 bu sınıf (CLAUDE.md çift-sinyal kuralı sadece image-mapping'e
          uygulanmış; çekirdek match + crop-isim hariç). Determinizm fix'i bunları kapatır.
        → K1a/K1b/K2a/K2b/K4a/K4b/K7 determinizm DIŞI (ölçüm/fizik/ürün/sinyal-çeşitliliği) —
          ayrı müdahale gerektirir.
```

**Adversarial netleştirme (3 challenge ortak sonucu):** Sentez "non-deterministik kimlik" meta-kökünü
abartmıştı. Gerçekte 20 kökün yalnızca ~4'ü (K3, K6, K8, K9) determinizm sınıfında. **En kritik tek
müdahale determinizm DEĞİL, ÖLÇÜM (K1a+K1b)** — çünkü diğer 16 kökün hangisinin gerçek/ne kadar yaygın
olduğu **ancak döngü-dışı kör-çözüm gate ile ölçülebilir.** 31 May coherence pilotu (%60 drop yakaladı,
13,595 popülasyon tam-run) bu aracın çalıştığını zaten kanıtladı.

---

## 4. Semptom Olarak Elenenler (ve neden)

| İddia | Karar | Gerekçe |
|---|---|---|
| **A/E bias** | SEMPTOM | Kökü K5 (page_inline qnum-çökme, %53) + K7 (tek-engine). Bias içerikten değil, OCR'ın grid'i lokal-qnum'a çökertmesinden. K6 biased harfi yanlış soruya yapıştırır. |
| **Tier H 49,468 satır yanlış** | SEMPTOM (K9) | K3 (bağ yok) + K5-görsel-eşdeğeri (3 q-semantiği) tezahürü. Metodolojik ders olarak P1 (script silinmedi, tekrar riski). |
| **Bayesian ai_upgrade bug** | **PHANTOM (fix'li)** | `cross_validate_answers.py:114 ai_upgrade:0.65 # S194 fix` CANLI, 78/78 PASS. Audit doc gövdesi (`:265-266 return "ai_solved"`) STALE. ROOT sayılmadı; sadece tie-break/tek-kaynak kalıntısı (K14) gerçek yapısal risk. |
| **`calibrate_yayinevleri.py` / `finalize_calibration.py`** | **PHANTOM DOSYA** | CLAUDE.local.md + briefing referanslı ama diskte YOK (find ile tarandı). Kalibrasyon ana pipeline'a hiç bağlı değil. |
| **"Tek-OCR-engine" (soru-OCR)** | KISMEN PHANTOM | Soru-OCR'da Gemini Flash→Pro **fallback** VAR. Gerçek kök: garbled-ama-geçerli-JSON için fallback tetikleyici yok (K-katkı). Cevap-OCR'da (page_inline, K7) gerçekten tek-engine — KARIŞTIRILMAMALI. |
| **question_image_url coverage %52 vs %99** | ÖNEMSİZ ÇELİŞKİ | İkisi de "kayıt var" anlamında doğru ama K4a/K4b nedeniyle fonksiyonel coverage ~0 (render KAPALI, leak'li) — öğrenci görmüyor. |
| **NFC `errors="replace"` içerik kaybı** | NOT-PHANTOM-NOT-ROOT | İçerik path'inde DEĞİL, yalnız stdout reconfigure (doğrulandı). Kayıp YOK ama desen riskli (K20 notu). |
| **Çift-sinyal kuralı yok** | YANLIŞ FRAMING | Kural VAR (CLAUDE.md) ama KAPSAM eksik — yalnız image-mapping'e uygulanmış; çekirdek match (K8) + crop-isim (K3) hariç. Gerçek bulgu. |

---

## 5. Öncelikli Aksiyon Sırası (en yüksek ROI önce)

> İlke (3 challenge ortak): **Ölçüm düzelmeden içerik fix'leri kör uçar.** K1a+K1b önce; sonra en
> yüksek öğrenci-değer kaldıracı olan görsel-ürün tavanı (K4) ve garble kaynağı (K2); sonra cevap
> dairesi (K5/K6/K7/K8); en son determinizm/provenance temizliği.

**FAZ 0 — ÖLÇÜM (her şeyin ön-koşulu, P0)**
1. **K1a+K1b:** Render-artifact üzerinde **kör-bağımsız-çözüm gate** kur (LLM'e DB-cevabı VERİLMEDEN
   çözdür, sonra keyed cevapla kıyasla). 31 May pilotu aracı kanıtladı — operasyonalize et.
2. **K1b:** Gerçek insan-GT topla (≥300, görsel zorunlu); `--auto-verify` flag'ini prod'dan kaldır;
   `ground_truth_analysis.json`-bağımlı tüm kalibrasyonu (`tier1=0.85` placeholder dahil) invalide et.
3. **K18+K19:** Dashboard'dan format-PASS/soru-sayısı kaldır veya "ham" etiketle; tek geçerli sayı
   = okunabilir∧çözülebilir∧bağımsız-doğrulanmış. Kalite-task tanımını "≥1 gerçek beta-kullanıcı önüne
   çıktı" kapanışına bağla.

**FAZ 1 — GÖRSEL ÜRÜN TAVANI (on-binlerce satır 0-değer, P0)**
4. **K4a:** Temiz figure-crop üret (YOLO 'soru'−'cevaplar' farkı veya figür-dedektör) — yeniden-crop.
5. **K4b:** K4a bittikten SONRA `false &&` suppress'i kaldır (önce kaldırmak leak'i geri açar — YASAK).
6. **K12+K13:** Figür-bağımlı filtreyi subject-bağımsız figure-flag'e çevir; re-OCR figür-tarif prompt'u.

**FAZ 2 — GARBLE KAYNAĞI (%63 drop, P0)**
7. **K2b:** OCR-öncesi 2-3x LANCZOS upscale (min-boyut hedefi) ekle — en ucuz, en yüksek metin-kazanımı.
8. **K2a:** Yüksek-zoom/yüksek-DPI capture veya `pdf2image` 300 DPI (yeni ingest için).
9. **K17+K20:** Çözünürlük teşhisini OCR-öncesi gate'e bağla (eşik yeniden kalibre); yazma öncesi NFC.

**FAZ 3 — CEVAP DAİRESİ (gold pool %53 kaynağı, P0)**
10. **K7+K5:** Cevap-anahtarına çok-model konsensüs + A+E>%46 bias-guard + multi-test lokal→global qnum.
11. **K8+K6:** Çekirdek matching'e zorunlu çift-sinyal (Jaccard≥0.50); YOLO-index fallback YASAK;
    sayısal-olmayan q_no → pending. CLAUDE.md çift-sinyal kuralını CI/lint ile çekirdek-match'e genişlet.
12. **K14:** Anti-bias'ı tek-kaynak page_inline'da da uygula; tie-break A/E korumasını kaldır; eski
    `ai_upgrade*` DB satırlarını Curator'a düşür (yeni iş yok, backfill).

**FAZ 4 — DETERMİNİZM / PROVENANCE TEMİZLİĞİ (gelecek-koruma, P1)**
13. **K3:** Crop+OCR+ingest'i tek pipeline'da birleştir; crop_path'i INSERT'te yaz (det. 1:1).
14. **K9+K11:** `tier_h_*.py` → `_deprecated/`; tek kanonik `pipeline_metadata.image_match` provenance şeması.
15. **K15+K16:** ASCII-safe `book_key()` (3 script ortak); satır-bazlı sinyal-izi + güven-tabanlı dedup.

---

*Tüm kod iddiaları 31 May 2026 canlı dosyalarda satır-doğrulandı. KESİN-güven kökler bizzat
re-verify edildi (K1a, K1b, K2b, K4b, K7, K14). Phantom'lar (Bayesian fix, kalibrasyon dosyaları)
Bölüm 4'te işaretli. Determinizm meta-kök kapsamı 3 challenge ile ~4 köke daraltıldı.*
