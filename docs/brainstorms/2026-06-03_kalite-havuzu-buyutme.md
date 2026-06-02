# Brainstorm: Kalite havuzunu büyütme (98K unverified+pending → onaylı, Gemini'siz)
Tarih: 2026-06-03 | Domain: content | Perspektifler: Kalite · Hız · Hata toleransı

> Bağlam: Bugün `soru_bankasi_service` is_active-only sızıntısı kapatıldı (lesson #31).
> Servis havuzu ~110K aktif → **~12.3K kalite-onaylı** (TYT 8,719 + AYT 3,618). 98K
> unverified+pending artık servis EDİLMİYOR. Soru: bunları **Gemini'siz** (API bloke)
> onaylı havuza nasıl DOĞRU + GÜVENLİ + EKONOMİK taşırız?

## TL;DR
Önce char-trigram garble LM ile (0-token, deterministik) 98K'nın okunabilir alt-kümesini ayır; sadece onu **çift-bağımsız-kör-solve AND-gate**'inden geçir (iki blind `==DB` → `verified_provisional`, asla tek-run). En kritik risk üç boyutlu: (1) iki aynı-model solver'ın korele A-bias'ı "anlaşma" sanılır → gerçek bağımsızlık için farklı-model 3. sinyal şart; (2) DB rollback'i mümkün ama beta öğrencisinin gördüğü kötü soru **kalıcı itibar hasarı** — bu yüzden provisional havuz 2. sinyal teyidi olmadan canlı öğrenci servisine girmemeli; (3) unverified'i ne toplu terfi ne toplu reddet — "incelenmemiş ≠ çöp/onaylı" (garble efsanesi tekrarı).

## Top 5 Aksiyon
1. **Char-trigram garble LM ön-eleme (Türkçe-char guard'lı)** — yüksek-surprisal kuyruğu kör-solve'a SOKMA; ~427M→~310M token tasarruf + dairesel-garble tuzağını engelle. Etki: 5/5 · Zorluk: kolay · Kaynak: Kalite+Hız (konsensüs)
2. **Çift-bağımsız-kör-solve AND-gate** — iki blind `==DB` → `verified_provisional` terfi; tek-run ASLA (A-bias canlı, tek-blind anlaşması yalnız %59.6). Etki: 5/5 · Zorluk: orta · Kaynak: Kalite+Hata (konsensüs)
3. **Reversible apply disiplini** — backup tablo + `correct_answer` DOKUNMA + `verified_provisional` flag (gold değil) + servis sorgusunun status-filtreli olduğunu doğrula (lesson #31, bugün kapatıldı). Etki: 5/5 · Zorluk: kolay · Kaynak: Hata
4. **Subject-relabel'i (2-sinyal) kör-solve ÖNCESİ yap** — yanlış subject etiketi konu-stratify ve "true_subject" yargısını bozar (K21). Etki: 3/5 · Zorluk: orta · Kaynak: Kalite
5. **≤6 sıralı dalga + düz-JSON parse + AGREE-first / DISAGREE-defer** — 16+ eşzamanlı = net throughput SIFIR (529 rate-limit); DISAGREE 2. sinyalini sona at (~140M token erteler). Etki: 4/5 · Zorluk: kolay · Kaynak: Hız

## Konsensüs (2+ perspektif)
- **Garble LM ucuz ön-filtre, pahalı LLM-solve'dan ÖNCE** (Kalite#1, Hız#1). Deterministik, 0 token, doğrulanmış detektör (`garble_char_lm.py`).
- **Çift-bağımsız sinyal terfi gate'i; tek-run kalıcı GT değil** (Kalite#2, Hata#1). L1/L1d deseni zaten kanıtlı.
- **correct_answer'a dokunma + backup + reversible metadata flag + verified_provisional** (Kalite#2, Hata#3).
- **unverified'i toplu terfi DE toplu reddet DE etme** — üç uyarının ortak noktası; "incelenmemiş ≠ çöp/onaylı", silmek/terfi varsayımdır (audit-methodology, garble efsanesi).
- **A-bias ortak-mod riski**: iki aynı-model solver korele yanılabilir → farklı-model 3. sinyal (Kalite kör nokta, Hata risk#1).

## Çatışmalar
| Konu | Taraf A (Hız) | Taraf B (Kalite+Hata) | Önerilen karar |
|------|---------------|----------------------|----------------|
| AGREE terfi için kaç sinyal? | Tek-blind AGREE'leri HEMEN terfi et, DISAGREE 2. sinyalini ertele (~140M token tasarruf) | Terfi = 2-bağımsız-blind AND; tek-sinyal A-bias'lı yanlış-pozitif | **B kazanır (doğruluk)** ama A'nın kademelendirmesi uzlaştırılır: sinyal-1 tüm okunabilir kümeye → sinyal-2 yalnız AGREE alt-kümesini TEYİT için (garble ön-filtre zaten en kötüyü attığı için ucuz); DISAGREE dispute-çözümü ayrı kuyruğa ertelenir |
| Geri-alınabilirlik yeterli güvence mi? | (örtük) backup + provisional = güvenli | DB rollback öğrencinin gördüğünü geri ALMAZ — itibar hasarı kalıcı | **B**: provisional havuz 2. sinyal teyidi olmadan canlı öğrenci servisine girMEMELİ; beta-gated path'te tut |

## Perspektif Detayları

### Kalite (yargı doğruluğu)
1. Garble ön-eleme → kör-solve sıralaması (4/kolay) — yüksek-surprisal kuyruğu solve'a sokma; dairesel "garble metin kendini cevaplıyor" tuzağı (verified_core re-curate %42 kör nokta). Risk: LM eşiği geçerli Türkçe STEM'i yanlış-pozitif eler → Türkçe-char guard zorunlu.
2. İki-bağımsız-kör-solve konsensüs gate (5/orta) — AGREE→provisional, DISAGREE→2.sinyal, tek-run ASLA. Risk: ortak-mod hatası → farklı-model 3.sinyal gerek.
3. Subject-relabel kör-solve ÖNCESİ (3/orta) — yanlış etiket stratify+true_subject yargısını bozar. Risk: relabel tek-keyword olursa yeni hata enjekte.
- **Kör nokta:** DISAGREE havuzu A-bias'ı — DB anahtarı A/E'ye çöküyor; 2-sinyal "DB yanlış" derse gerçek hata olabilir (143 REAL_ERROR böyle yakalandı), hızcı bunu "solver hatası" sayıp atar.
- **Uyarı:** unverified'i char-LM/format-PASS ile toplu REDDETME — "incelenmemiş ≠ çöp" (61K garble hiç ölçülmemişti). Flag'le, silme.

### Hız (throughput/maliyet)
- **Birim ekonomi:** verified_core = 24M token / 5,513 = ~4,355 token/soru → 98K × 4,355 ≈ **~427M token** (~18× verified_core); 2. sinyal 2-3×.
1. Char-LM ön-eleme → sadece okunabilir alt-küme solve'a (5/kolay); ~427M→~310M token. Risk: eşik geçerli STEM keser.
2. ≤6 eşzamanlı sıralı dalga + düz-JSON parse sabit protokol (4/kolay); 16+ = 529 rate-limit. Risk: burst'te yine patlar.
3. Tek-sinyal AGREE terfi + DISAGREE'yi ertele (4/orta); ~140M token erteler. Risk: tek-sinyal A-bias yanlış terfi.
- **Kör nokta:** char-LM geçen ama semantik-dairesel/figür-bağımlı sorular temiz geçip solve token yakar, sonra UNSOLVABLE'a düşer — optimizasyon bu israfı gizler.
- **Uyarı:** maliyet için eşzamanlılığı 6'nın üstüne ÇIKARMA — net throughput SIFIRA iner (ters teper).

### Hata toleransı (risk/geri-alınabilirlik)
- **Asimetri:** tek-blind anlaşma %59.6 (dar marj); DISAGREE'lerin %43'ü solver hatası; gerçek temiz ~%3.2.
1. Çift-blind AND-gate (5/kolay) — motor mevcut. Risk: korele A-bias "anlaşma" sanılır.
2. Asimetrik eşik + Türkçe-char guard + kademeli 500'lük batch + parti-başı spot-check (4/orta); terfi conf≥0.7+AND, RED tek-sinyal yeter. Risk: yüksek eşik havuzu küçük tutar (kabul edilebilir).
3. Reversible terfi: backup + verified_provisional + is_active/correct_answer DOKUNMA (5/kolay). Risk: lesson #31 — servis status-filtreli mi önce doğrula.
- **Kör nokta:** geri-alınabilirlik DB'de VAR, kullanıcı algısında YOK — beta öğrenci kötü soruyu gördüyse itibar hasarı kalıcı.
- **Uyarı:** unverified'e toplu kör-TERFİ uygulama — yargılanmadı, %24 UNSOLVABLE/garble içeriyor; sadece çift-sinyal-geçen terfi edilir.

## Kör Noktalar & Uyarılar (birleşik)
**Kör noktalar:**
- A-bias ortak-mod: iki aynı-model solver korele yanılır → farklı-model 3. sinyal gerçek bağımsızlık için.
- Semantik-dairesel/figür-bağımlı sorular char-LM'i temiz geçer, solve token yakar, UNSOLVABLE'a düşer.
- DB geri-alınabilirliği ≠ kullanıcı-algısı geri-alınabilirliği; beta öğrenciye giden kötü soru kalıcı itibar.

**Uyarılar (YAPMAYIN):**
- unverified'i toplu REDDETME (char-LM/format proxy ile) — "incelenmemiş ≠ çöp".
- unverified'e toplu kör-TERFİ — sadece çift-sinyal-geçen terfi.
- Eşzamanlılığı 6 dalganın üstüne çıkarma — net throughput sıfırlanır.

## Önerilen pipeline (sentez)
```
98K unverified+pending
  └─[0-token] char-trigram garble LM skor + Türkçe-char guard
        ├─ yüksek-surprisal kuyruk → re-OCR backlog (Gemini-bloke, ertelenir), TERFİ ETME
        └─ okunabilir alt-küme
              └─[2-sinyal] subject-relabel (yanlış etiket düzelt)
                    └─[blind solve #1, ≤6 dalga, düz-JSON]
                          ├─ AGREE(==DB) → [blind #2 farklı-model TEYİT] → verified_provisional (backup+flag, correct_answer DOKUNMA)
                          └─ DISAGREE → ayrı dispute kuyruğu (sona ertele; 143 REAL_ERROR deseni)
  verified_provisional → 2-sinyal teyit OLMADAN canlı öğrenci servisine girmez (beta-gated)
```
**Not:** Bu pipeline'ın 3. adımı (terfi → servis) ancak bugün kapatılan lesson #31 sızıntısı sayesinde güvenli — servis sorgusu artık status-filtreli.
