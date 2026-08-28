# Figür-Eksik Soru Audit — "figür-bağımlı ama görsel yok" (2026-06-24)

## Soru
Tüm DB'de figür-bağımlı sorularda figür eksik kaç tane var, kök nedeni ne, çöz.

## Ölçüm (canlı DB, question_bank)
- Toplam satır **187.835**, aktif **110.896**.
- `question_image_url` DOLU: **181.652 (%96.7)** — görsel kapsama yüksek (CLAUDE.md'deki
  "%75.7" notu bayat).
- **Görselsiz: 6.183** — ama aktif yalnız **252** (%96'sı, 5.931 inaktif).

### "Figür-bağımlı + görselsiz" — detektör tuzağı
| Sinyal | Toplam | Aktif |
|---|---|---|
| metin-regex (şekil/grafik/...) + görselsiz | ~1.824 | ~12 |
| **SIKI** regex (şekildeki/şekil-I/grafik/devre/şema/koordinat/yandaki) | — | 1 |
| **`has_diagram=true` (güvenilir flag) + görselsiz** | **4** | **2** |

Naive regex **yanlış-pozitif** üretiyor: `şekil` → `şekilde`(tarz), edebiyat/paragraf
soruları. Tek "sıkı" aktif eşleşme (c635ea39) bile klasik edebiyat sorusuydu (figür
gerektirmez). **Gerçek figür-kırığı servis sette = 2 soru** (has_diagram güvenilir sinyaliyle).

## KÖK NEDEN (iki katman)
1. **Çıkarılmış-nesil artığı (asıl):** görselsizlerin %93'ü `rematch`, %73'ü `db_v7`
   neslinden. v3.5+ temizliğinde bu güvenilmez nesiller **bilerek production'dan çıkarıldı**
   (CLAUDE.md: "db_v7=0, rematch=0"). Crop'ları işlenmişti (3.989'unda boyut/OCR var) ama
   `question_image_url` mapping **yalnız kabul edilen sete** uygulandığı için bunlara
   bağlanmadı. → Görsel-eksikliği **servis kalitesi sorunu değil**, %96 inaktif temizlik artığı.
2. **Detektör yanlış-pozitifi:** "figür-bağımlı" tespiti metin-regex'le aşırı sayıyor
   (`şekilde`=tarz, paragraf soruları). Güvenilir `has_diagram` flag'i gerçek sayıyı veriyor.

## ÇÖZÜM (uygulandı, reversible)
Servis setindeki **2 gerçek-kırık** figür-bağımlı görselsiz soru (AYT Edebiyat, crop/OCR/boyut
yok = kurtarılamaz):
- `f3fa05a9` "Numaralanmış eserlerden hangisi... eşleştirilemez?" (eser-listesi görseli yok)
- `c8c7c72d` "Yukarıdaki dönemlerin karşılaştırılması..." (dönem-tablosu görseli yok)

→ `gate2c_demoted` (reason `figdep_no_image_broken`). v_safe-dışı doğrulandı.
`correct_answer`/`is_active` dokunulmadı. Geri-alma: `DELETE FROM gate2c_demoted WHERE
reason='figdep_no_image_broken'`.

## Aksiyon gerektirmeyenler
- **6.181 görselsiz** (geri kalan): %96 inaktif çıkarılmış-nesil → servis dışı zaten.
- **32 aktif "kurtarılabilir crop"**: hep Türkçe/Edebiyat **paragraf** soruları — kaynak
  paragraf görsel-crop'tu ama metin `question_text`'te tam var → **kırık değil**. URL re-map
  nice-to-have; ama crop dosya-adı metadata'da yok (`crop_file=null`) → disk-eşleme (çift-sinyal,
  pipeline-fix kuralı) gerektiren ayrı host-script işi, kör-mapping YAPILMAZ.

## Ders (audit-methodology'e uyumlu)
Kategori-sayısı (figür-eksik) ölçülmeden "çok var" sanılırdı; metin-regex detektörü
doğrulamayı geçmedi (yanlış-pozitif). Güvenilir flag + örnek-doğrulama ile gerçek sayı
(binlerce değil **2**) ortaya çıktı. Bkz `.claude/rules/audit-methodology.md` (Metrik
Doğrulama Gate, Ucuz Filtre Tuzağı).

---

# EK: Frontend — "görseller hiç görünüyor mu?" (2026-06-24, ikinci soru)

## Bulgu: görseller frontend'de KASITLI KAPALI
- Aktif sınav sayfası `pages/ExamPage.tsx` → **`ModernOSYMExamInterface`** kullanıyor.
- `ModernOSYMExamInterface.tsx:566`: görsel render `{false && cq.question_image_url && (...)}`
  ile **hard-disable** (Bug #11 defensive suppress, 18 May 2026).
- Gerekçe (kod yorumu): "Vision audit ortaya koydu ki tüm question_image_url'ler **solution
  leak** içeriyor (image içinde A) B) C) D) E) görünüyor)".
- Legacy `OSYMExamInterface.tsx:779` görseli render EDER (suppress yok) ama **aktif değil**.
- → **Hiçbir soru görseli öğrenciye görünmüyor** (figür-bağımlı dahil).

## Görsel kanıt (crop'u açtım)
`Apotemi_2024_Ayt_Kimya..._p0061_q01.png`: figür (cam-kap gaz düzeneği) crop'ta VAR, ama
**5 şık + doğru cevap (C) yuvarlak içine alınmış** halde görünüyor → crop kaynak kitabın
işaretli-cevap halinden alınmış. Göstermek = cevap sızdırmak. **Suppress haklı; "sadece aç"
çözüm değil.**

## Crop tipleri (disk, 528.586 PNG)
- `_PAGE.png` 29.411 → **tüm sayfa** (çoklu soru + cevaplar = ağır leak).
- `_qNN.png` 396.992 → soru-bazlı ama yine şık+işaretli-cevap içeriyor.

## Servis-etkisi (v_safe, görseller kapalı)
- `has_diagram=true`: 197. AMA örnekleme ~yarısının **yanlış-pozitif** olduğunu gösterdi
  (metinden çözülen matematik/geometri: "iki koşucu 360m parkur", "(x-2)²(x²-5x)<0",
  koordinat geometri — figür süs). 'grafik' bile çoğu fonksiyon-verilmiş matematik.
- Gerçek-kırık (veri salt figürde: "grafikte verilmiştir", "şekilde", "yukarıdaki sistem")
  alt-küme daha küçük → **temiz SQL-pattern YOK, soru-bazlı yargı şart** (blanket-demote
  yarısını boşuna siler).

## KÖK NEDEN (zincir)
1. Crop generation soru bloğunu (metin+şık+işaretli-cevap) kırpıyor → **cevap sızıntısı**.
2. Tek görsel kaynağı bu olduğundan figürü göstermek = cevabı göstermek.
3. Frontend defansif `false &&` ile TÜM görselleri kapatıyor.
4. Sonuç: figür-zorunlu sorular figürsüz servis ediliyor → cevaplanamaz (ama figür-süs olanlar
   metinden çözülüyor, sorun değil).

## ÇÖZÜM (adım adım)
**Asıl fix (host/GPU, Vision — yapılmadı):**
1. Figür-zorunlu sorular için kaynak crop'tan **yalnız figür bölgesini** yeniden kırp
   (şık/metin/işaretli-cevap HARİÇ) — Vision bbox tespiti.
2. `question_image_url`'i figür-only crop ile değiştir.
3. `ModernOSYMExamInterface.tsx`'teki `false &&` suppress'ini kaldır.
4. Pilot 30-50 crop pixel-doğrula (leak=0) → ölçekle.

**Interim (DB, soru-bazlı yargı gerektirir — opsiyonel):** görseller kapalıyken figür-ZORUNLU
servis sorularını Opus-yargısıyla tespit edip `gate2c_demoted`'a al (reversible). has_diagram
veya 'grafik' blanket DEĞİL (yarısı yanlış-pozitif). Pool-growth'taki Opus-çöz desenine benzer.

## Not
Bu, pool-growth'ta figür-bağımlı soruları neden ATLADIĞIMIN de kök sebebi: o sorular metinden
çözülemez VE figürleri zaten frontend'de görünmüyor.

---

## RE-CROP PILOT (2026-06-24, "a" seçeneği)
Yaklaşım: leak = alttaki şık bloğu (A)..E)+işaretli cevap). Öğrenci şıkları DB'den alır →
görselden şık-bloğunu ATIP üstünü (figür+kök) tutmak leak'i giderir.

**Araçlar (workspace):** PIL 12.2, OpenCV 4.13, Tesseract+pytesseract, numpy; host crops yazılabilir.
Disk'te 528.586 crop (29.411 `_PAGE` tüm-sayfa + 396.992 `_qNN`). Script:
`d-dataset/scripts/recrop_figure_only.py`.

**OCR otomasyonu YETERSİZ (kanıtlandı):** crop'lar düşük-çözünürlüklü + matematik ağır →
Tesseract "A)" şık-işaretlerini "5M" gibi okuyor (upscale 3× + psm 6/11/4 denendi, 0 tespit).
→ Şık-bloğu y'sini OCR ile güvenilir bulamıyoruz. Orijinal yorumdaki "**Vision re-crop**" tam
bu yüzden: OCR değil, **görü/layout-modeli** gerekiyor.

**Kavram kanıtı (Opus-görü ile kesim):** Apotemi Kimya crop'u figür-only yapıldı — cam-kap
düzeneği (figür) korundu, **5 şık + yuvarlaklı C cevabı kesildi (leak=0)**. Çıktı:
`d-dataset/output/crops_figonly/pilot/`. → Ürün doğru; tek eksik **ölçekli kesim-tespiti**.

## End-to-end fix (3 parça, durum)
1. **Re-crop** (figür-only): kesim-tespiti ölçekte ya host/GPU **layout-modeli** ile ya da
   Opus-görü-döngüsü (batch-batch, yavaş) ile. OCR ELENDİ.
2. **`question_image_url`** → figür-only yola güncelle (DB, ben — reversible).
3. **Frontend suppress kaldır**: `ModernOSYMExamInterface.tsx` `false &&` → `true &&` /
   koşulu sadeleştir + **rebuild/redeploy (host)**. ⚠️ Crop'lar düzelmeden AÇMA (leak geri gelir).

**Karar:** ölçekli kesim için (a) host layout-modeli pipeline, veya (b) Opus-görü-döngüsü
batch'leri (figür-zorunlu v_safe ~100-300 soru; pool-growth deseni, yavaş). Frontend redeploy
her halükârda host'ta gerekli.

---

## PIPELINE HAZIR (seçenek A — layout-model, 2026-06-24)
Ölçekli kesim için OCR (eleme: "A)" okunamıyor) ve OpenCV çizgi-heuristiği (eleme: şıkları
içine alıyor, leak riski) yerine **doclayout-yolo 'figure' sınıfı** (semantik figür ayırma).

**Teslim edilen (kod hazır, test edildi):**
- `d-dataset/scripts/recrop_pipeline.py` — layout-model figür-only crop + `_map.tsv`. I/O
  stub-modda doğrulandı (3/3 OK, `crops/_figonly/<rel>` + map). Yalnız figure/table/formula
  kutuları; şık/metin ASLA. NO_FIGURE → görsel üretilmez.
- `recrop_01_export_input.sql` — input (351 q-level figür-olası v_safe sorusu).
- `recrop_02_apply_urls.sql` — url apply, **reversible** (`figonly_url_backup`).
- `RECROP_README.md` — host/GPU adımları (export→model→pilot-40→doğrula→tam→url-apply→redeploy).
- **Frontend GÜVENLİ açıldı**: `ModernOSYMExamInterface.tsx` `false &&` → `showImg`
  (`url.includes('/_figonly/')`). Şimdi davranış değişmez (figonly url yok); pipeline+url-apply
  sonrası **otomatik** yalnız de-leak figürler görünür, eski leaky crop'lar gizli kalır.

**Scope:** v1 = 351 q-level. PAGE-crop (14.022, tüm-sayfa) v2 (soru+figür lokalizasyonu gerekir).

**Host'ta kalan (sende):** pip install doclayout-yolo + ağırlık → pipeline çalıştır (GPU) →
pilot-40 pixel-doğrula → url-apply → frontend rebuild/redeploy → sınavda doğrula.

### Kapsam + beta-güvenlik (24 Haz, full run sonrası)
Full run: 109 q-crop → **65 figonly** apply (0 mojibake, reversible, v_safe'te). Kapsam ölçümü
(v_safe figür-zorunlu = `has_diagram=true`, 197 soru):
- **64 düzeldi** (figonly) + 7 q-crop düzelmemiş (kolay, geniş input ile re-crop).
- **126 PAGE-crop** (tüm-sayfa): figonly üretilemez (sayfada soru+figür lokalizasyonu = v2).
- Bunların ~%40'ı gerçekten figür-zorunlu (kırık), ~%60'ı metinden çözülebilir (has_diagram
  false-pozitif: cebir, verili-değerli geometri, kavram, bilinen-molekül). Blanket-demote YOK.
- **Beta-güvenlik:** verisi/cevabı SADECE figürde olan **12 yüksek-kesinlik kırık** demote
  edildi (`gate2c_demoted` reason `figdep_pagecrop_databound`): örüntü/şema/dalga-modeli görseli,
  "görselleri verilen canlı", tablo-boşluğu, grafikte-veri, grafik-şık, periyodik-boyalı-sütun.
  Cevaplanabilir geometri KORUNDU.

**Backlog (v2):** 126 PAGE-crop'un kalan figür-zorunluları + 7 q-crop → PAGE'den figür
çıkarma (layout-model full-page + soru lokalizasyonu). Demote edilen 12 reversible — v2 sonrası
un-demote. **Sıradaki host adımı: `docker compose up -d --build frontend` → 65 figonly canlıya.**

### Pilot run + bug fix (host GPU, 24 Haz)
- doclayout-yolo kuruldu, ağırlık indi, pilot-40 çalıştı.
- **BUG (yakalandı, fix'lendi):** `KEEP_CLASSES`'a `isolate_formula` koymak LEAK üretti — şıklar
  formül (M=2.M) olduğundan figür+formül birleşimi tüm soruyu kapsadı (Apotemi'de şıklar
  görünüyordu). Fix: **`KEEP_CLASSES = {"figure"}`** (formül/tablo dışla).
- **Doğrulama GEÇTİ:** fix sonrası pilot-40 → OK=23/NO_FIGURE=17; 4 örnek (conf 0.44–0.96)
  pixel-doğrulandı, hepsi figür-tam + şık/cevap YOK.
- **psql `\copy` UTF8 fix:** export+apply SQL'lerine `ENCODING 'UTF8'` (Türkçe url bozulması).
- **İlk yanlış apply geri alındı:** stub `_map.tsv` 3 url'i değiştirmişti → MCP ile orijinale
  restore + `figonly_url_backup` truncate. DB temiz (0 figonly url).
