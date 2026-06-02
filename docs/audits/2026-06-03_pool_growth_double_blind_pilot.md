# Pool-Growth Double-Blind Pilot (Top-1 + Top-2)
Tarih: 2026-06-03 | Yöntem: Workflow (rate-limit hardened) | Örnek: 120 stratified

Brainstorm `docs/brainstorms/2026-06-03_kalite-havuzu-buyutme.md` Top-1 (garble
ön-eleme) + Top-2 (çift-bağımsız-kör-solve gate) pilot uygulaması. Amaç: ~98K
unverified+pending sorudan kalite-onaylı havuza **Gemini'siz** terfi adayı tespiti.

## Pipeline (uygulandı)
```
98K unverified+pending → [char-trigram garble LM, 0-token] → readable
  → [2× bağımsız kör-solve, DB cevabı VERİLMEDEN, 4'erli sıralı dalga]
  → sınıflandırma (DB ile karşılaştırma run DIŞINDA — blindness korundu)
```
- Prep: `prep_pilot.py` (garble eğitim 5,513 coherent; stratified 120, seed 42)
- Workflow: `dblind_workflow.mjs` (batch=4, 429-retry)
- Sınıflandırma: `classify_results.py` (apply YOK)

## Sonuçlar (n=120)

| Kategori | n | % | Anlam |
|----------|---|---|-------|
| AGREE_PROMOTE | 37 | 30.8% | b1==b2==DB → güvenli terfi adayı (3'lü teyit) |
| DISPUTE | 41 | 34.2% | b1==b2≠DB → **3. sinyal gerek** (DB hatası DEĞİL kanıtı yok) |
| SPLIT | 30 | 25.0% | b1≠b2 → çözüm belirsiz |
| UNSOLVABLE | 12 | 10.0% | en az bir blind "çözülemez" (figür/garble) |

**Garble ön-eleme (Top-1):** char-garble ≥4.5 = **0/120**. MEMORY doğrulandı:
karakter-seviye garble popülasyonda ~0. Ucuz filtre rastgele unverified örnekte
hiçbir şey elemiyor → asıl iş blind-solve'da (semantik UNSOLVABLE %10 onu yakalıyor).

## Kritik bulgular

### 1. Küçük örnek yanıltıcıydı (ölçek şart)
İlk 24-örnek %54 AGREE verdi; tam 120 **%31**. İlk 24 daha sözel/kolaydı; 120'de
MATEMATIK ağırlığı (49/120) AGREE'yi düşürdü (MAT 14/49 = %29). Audit-methodology
"sample ≠ evren" canlı tekrar.

### 2. DISPUTE %34 ≠ "DB %34 hatalı" — ortak-mod A-bias (brainstorm kör-noktası #2)
İki **aynı-model** (Claude) blind %72 oranında birbiriyle hemfikir (common-mode).
Bu konsensüsün sadece %47'si DB ile eşleşiyor. Ama solver harf dağılımı **D-yanlı,
E-kaçışlı**: blind E=14 vs DB E=28 (yarısı kadar E seçiyor). DB=E FIZIK soruları
(görelilik, çift-yarık) blind D dedi → bunlar **solver hatası, DB hatası değil**.
→ DISPUTE'lar same-model blind ile çözülemez; **farklı-model 3. sinyal zorunlu.**

### 3. Maliyet duvarı — workflow subagent ölçeklenmez
22.8M token / 120 soru = **~190K token/soru** (96K/agent × 2 blind). Full 98K bu
harness'la ≈ **18.6 milyar token — infaz edilemez**. Üretim için workflow-subagent
DEĞİL, **hafif doğrudan-API solver** (minimal prompt, ~1-2K token/çağrı) gerekir.

### 4. Rate-limit (çözüldü)
İlk 120-run 222/240 agent HTTP 429 yedi (pipeline ~16 eşzamanlı). Düzeltme: 4'erli
sıralı dalga + 429-retry → 120/120 temiz (0 rate-limit). L1 "≤6 eşzamanlı" dersi
Workflow harness'ında da geçerli.

## Güvenli çıktı: 37 terfi adayı
b1==b2==DB üçlü-teyitli 37 soru `pool_pilot_candidates.json`. DB cevabı 2 bağımsız
kör-solve ile teyitli — solver bias DB tarafından bağımsız doğrulandığı için iptal
olur. Düşük riskli, reversible. **APPLY YAPILMADI** (insan onayı bekliyor).

## Öneri (sonraki adım)
1. **Hafif solver** (P3 backlog) — workflow değil, doğrudan-API batch; 96K→~1.5K
   token/çağrı. 98K'yı ekonomik işlemenin tek yolu.
2. **Farklı-model 3. sinyal** — DISPUTE+SPLIT (71/120 = %59) için A-bias kırıcı.
   Same-model çift-blind tek başına yetersiz; brainstorm öncülü doğrulandı.
3. **37 adayı uygula** (opsiyonel, düşük değer) — pilot kanıtı için, üçlü-teyitli
   alt küme verified_provisional'a (backup + correct_answer DOKUNMA).

## Reprodüksiyon
`backend/scripts/quality/_pool_growth_pilot/` — prep_pilot.py, generate_workflow.py,
dblind_workflow.mjs, classify_results.py. Run: prep → generate 120 4 → Workflow →
classify. Seed 42, deterministik.
