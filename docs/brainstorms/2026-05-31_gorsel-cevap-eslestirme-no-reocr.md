# Brainstorm: Soru↔Görsel↔Cevap Eşleştirmesi — re-OCR'sız, eldeki veriyle TAM-DOĞRU
Tarih: 2026-05-31 | Domain: content | Perspektifler: Kalite · Hız/Kapsama · Hata-toleransı

## TL;DR
Eşleştirme iki ayrı probleme bölünür: **CEVAP-bağı** (kör-konsensüsle ZATEN çözülüyor — re-OCR'sız, dairesel-olmayan) ve **GÖRSEL-bağı** (figür crop'u). Görsel-bağı re-OCR'sız iki eldeki-veri mekanizmasıyla çözülür: (1) **mevcut bbox'lardan figür-only crop türetme** (deterministik geometri, leak'i öldürür) + (2) **leak'i sinyale çevirme** — crop'ta GÖRÜNEN şıkları vision ile DB option metinleriyle eşle. En kritik uyarı (3 perspektif ortak): tek-solver/tek-run `verified_gold`'u kalıcı ground-truth sayma — K1b dairesinin tekrarı; 2. bağımsız sinyale kadar `verified_provisional`.

## Top 5 Aksiyon
1. **Mevcut bbox'lardan figür-only crop türet** — 'soru' bbox − 'cevaplar' bbox farkı → şıksız figür. Leak (K4a) deterministik ölür, sonra `false &&` kaldırılabilir. Etki 4 · Orta · Kaynak: Kalite M2. **Re-OCR yok, yeni detektör yok — duran geometriden türetme.**
2. **Kör-konsensüsü geniş havuza ölçekle, eşik SABİT + garble ön-filtre** — verified core (2,734) → tahmini ~6,800; ama `verified_provisional` damgası. Etki 5 · Düşük · Kaynak: Hız M1 + Hata uyarı.
3. **Çift-sinyal abstain gate (bilmiyorum > yanlış-bağ)** — görsel: bbox-geometri + vision-option-match; cevap: Jaccard≥0.50 + q_no. Tek sinyal → `pending_link`, fallback YASAK. Etki 4 · Düşük · Kaynak: Hata M3 + Kalite M3.
4. **Her bağa provenance satırı** — `pipeline_metadata.link_provenance={signals,confidence,matched_by,run_id,ts}`; dedup "son kazanır" değil "en yüksek güven + çakışma logu". "Neden bu cevap/görsel" türetilebilir. Etki 5 · Orta · Kaynak: Hata M1.
5. **628 dispute'a çok-model konsensüs** — 3/3 DB'ye karşı hemfikir → otomatik düzelt; aksi → Curator. Tek-solver çıktısını ASLA auto-overwrite etme (K23 tekrarı). Etki 4 · Orta · Kaynak: Hız M2 + Kalite uyarı.

## Konsensüs (2+ perspektif)
- **Kör-konsensüs = doğru araç** (3/3): post-hoc heuristik değil, DB-cevabı verilmeden bağımsız içerik-yargısı → "matcher #20" değil. verified_core kanıtladı.
- **Çift-sinyal + abstain**: tek sinyalle (q_no-only / bbox-only / pozisyon) bağ KURMA → `pending`. Hedef daha çok eşleşme değil, **yanlış eşleşmeyi reddetmek** (Tier-H'nin tersi felsefe).
- **Asla auto-overwrite**: `correct_answer`'a dokunma; metadata-only + Curator + backup (K23 tekrarı yasağı).
- **Garble ön-filtre şart**: solver+DB aynı garble'ı aynı yanlış okuyup "sahte-gold" üretebilir → coherence/garble flag olmadan gold sayısı yalan.
- **Provenance + geri-alınabilirlik**: her write non-destructive + run_id + backup.

## Çatışmalar
| Konu | Hız | Kalite/Hata | Önerilen karar |
|---|---|---|---|
| Kapsama vs doğruluk | 13,595'e ölçekle (gold 2,734→~6,800) | coverage baskısı 19 matcher'ı bozdu; eşik SABİT | Doğru aracı (kör-solve) ölçekle AMA conf≥0.7 sabit + garble ön-filtre; gevşetme YOK |
| verified_gold statüsü | hızlı altın havuz | tek run_id = yeni dairesellik (K1b) | `verified_provisional`; 2. bağımsız sinyal (farklı model/insan-GT) ile "gold"a terfi |
| Unsolvable kurtarma | 884'ü retry | sahte-konsensüs riski | Yalnız garble-flag'siz olanları retry; geri kalan demote |

## Kör Noktalar & Uyarılar (birleşik)
- **Figür-bağımlı sorular**: kör-solver figürü göremez (K13 prompt figürü tarif etmiyor) → doğru-bağı haksızca dispute/unsolvable'a atar + Curator kuyruğunu şişirir. Figür-soruları AYRI ele al (vision-solver veya işaretleyip atla).
- **Sahte-gold**: solver+DB ortak garble → yanlış "agree". Coherence ön-filtre zorunlu.
- **Maliyet**: 167K full 3-solver = devasa token. Önce verified çekirdeğe sıkış, ölçeği kademeli aç.
- **YAPMAYIN**: (a) blind≠DB'yi otomatik production'a UPDATE (K23); (b) conf eşiğini 0.7 altına çekme; (c) tek-run gold'u kalıcı GT sayma; (d) figür-soruları görselsiz beta'ya sızdırma.

## Perspektif Detayları (özet)
**Kalite:** M1 3-solver konsensüs (figürlü crop'u solver'a ver), M2 bbox-farkıyla figür-only crop (leak fix), M3 page_inline'ı Jaccard≥0.50 çift-sinyalle yeniden-bağla + A/E bias-guard.
**Hız:** M1 kör-solve'u student_coherent geneline ölçekle (en büyük kapsama kazancı burada, dispute/unsolvable'da değil), M2 dispute+unsolvable konsensüs-retry, M3 figürsüz verified_gold'u salt-metin beta'ya hemen aç.
**Hata-toleransı:** M1 link_provenance imzalı sinyal-izi, M2 yanlış-bağ tespit + tek-tuş rollback (non-destructive+backup), M3 abstain gate (çift-sinyal yoksa pending_link, fallback yasak).

## Birleşik Öneri
**CEVAP ekseni** (re-OCR'sız tam çözülür): kör-konsensüsü ölçekle + provenance + dispute multi-model + metadata-only. Zaten %50 başarıyla çalışıyor.
**GÖRSEL ekseni** (re-OCR'sız kısmen çözülür): (1) bbox-farkı ile figür-only crop türet (leak öl → un-suppress mümkün); (2) crop↔soru bağını **bbox-geometri + vision-option-match (leak-as-signal)** çift-sinyaliyle kur — uyuşmazsa pending. Vision-matching = görseli "okumak" değil, görünen şıkları DB metinleriyle EŞLEMEK (re-OCR sayılmaz).
**Her ikisi:** abstain > yanlış-bağ; figür-bağımlıları ayır; tek-run'ı `provisional` say.
