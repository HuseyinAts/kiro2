# Spec: No-Key Lokal-Model Pool Growth + İnsan Kalibrasyonu
Tarih: 2026-06-03 | Durum: tasarım onaylandı (kullanıcı), spec review bekliyor

## Problem
Servis havuzu kalite-onaylı sorularla sınırlı (`auto_judged_high`/`human_verified`).
98K unverified+pending soru serviste değil. Bunları **güvenilir + ücretsiz + API-key'siz**
verified_provisional havuzuna taşımak gerekiyor. Önceki workflow pilotu yöntemi
doğruladı ama iki duvara çarptı: (1) workflow-subagent 190K token/soru → 98K infaz
edilemez; (2) iki Claude blind ortak-mod A-bias paylaşıyor.

## Çözüm Özeti
**Tek güçlü lokal model (qwen3:14b, Ollama) blind solve + DB-anahtar uyumu +
hedefli insan kalibrasyonu.** API key yok, token maliyeti yok (lokal GPU). qwen3:14b
hem orijinal Claude pipeline'ından hem DB-anahtar kökeninden bağımsız → `qwen==DB`
anlamlı bağımsız korroborasyon. İnsan, gate kalitesini örnekleyerek doğrular (3. sinyal).

## Mimari (üç bağımsız birim)

### 1. Solver — `ollama_blind_solve.py`
- **Ne yapar:** Verilen soru listesini qwen3:14b ile blind çözer (DB cevabı prompt'a GİRMEZ).
- **Nasıl:** backend-context Python + httpx → `http://kiro2-ollama:11434/api/generate`,
  `model=qwen3:14b`, `think:false`, `stream:false`. Tek-satır `ANSWER: <A-E|NONE> |
  SOLVABLE: <yes|no>` parse (regex).
- **Bağımlılık:** kiro2-ollama (çalışıyor, doğrulandı). DB read-only (soru çekme).
- **Throughput:** sıralı/küçük-eşzamanlı (lokal GPU limiti); rate-limit yok (lokal).
- **Çıktı:** `{id, subject, qwen_letter, qwen_conf, solvable}` JSONL.

### 2. Classifier — `classify_local.py` (pilot classifier'dan adapte)
- **Ne yapar:** solver çıktısını DB cevap-anahtarıyla karşılaştırır (run DIŞINDA, blindness korunur).
- **Kategoriler:**
  - `AGREE_PROMOTE`: qwen solvable ∧ qwen_letter == DB → terfi adayı.
  - `DISPUTE`: qwen solvable ∧ qwen_letter ≠ DB → defer (DB-hatası veya qwen-hatası; insan örnekler).
  - `UNSOLVABLE`: qwen solvable=no → defer (figür/garble).
- **Bağımlılık:** answers.json (id→DB cevap), solver çıktısı.

### 3. Apply — `apply_local.py` (pilot apply'dan adapte, KANITLI)
- **Ne yapar:** insan-onaylı AGREE adaylarını verified_provisional flag'ler.
- **Mekanizma:** backup tablo → `pipeline_metadata.verified_provisional='true'` +
  marker `local_solve_run`. **correct_answer + quality_review_status DOKUNULMAZ.**
- Yalnız beta-practice yoluna girer (`osym_exam_engine.py:1289`), ana servis değişmez.

## İnsan Kalibrasyon Gate (3. sinyal)
- **Faz A — Kalibrasyon (bilinen-iyi):** qwen'i 3,206 verified_provisional üzerinde
  çalıştır → `qwen==DB` uyumunu **branş bazında** ölç. Bu, qwen'in YKS doğruluğunun
  zeminidir. Branş uyumu düşükse (örn. matematik Türkçe-STEM zayıflığı) o branş
  auto-promote'tan ÇIKAR — sadece yüksek-kalibre branşlar otomatik terfi.
- **Faz B — Spot-check (gerçek run):** AGREE adaylarından stratified ~30-50 insan onayı
  → gate doğruluğu teyit (hedef ≥%90). + DISPUTE örneklemi (~20) ile gerçek-DB-hata
  oranı tahmini (qwen-hatası mı DB-hatası mı ayrımı).

## Akış (kademeli)
```
Faz A: qwen kalibrasyon (3,206 known-good) → branş-bazlı güven eşiği
  ↓ (eşik tutmazsa DUR/düzelt)
Pilot 500: prep (stratified) → garble ön-eleme → qwen blind solve → classify
  ↓
Faz B: insan spot-check (AGREE ~40 + DISPUTE ~20) → gate ≥%90 mı?
  ↓ (tutarsa)
Apply: pilot AGREE'leri verified_provisional (backup'lı)
  ↓ (gate kanıtlandıysa)
Full 98K: aynı pipeline, yüksek-kalibre branşlar auto-promote, gerisi defer
```

## Başarı Kriterleri
- Faz A: en az birkaç branşta `qwen==DB` known-good uyumu ≥%85 (auto-promote'a uygun).
- Faz B: AGREE spot-check insan-doğruluğu ≥%90.
- Apply: correct_answer 0 değişiklik (doğrulanır), reversible backup.
- Maliyet: $0 (lokal), API key yok.

## Hata Yönetimi
- Ollama erişilemez/timeout → soru `solver_error` işaretlenir, terfi edilmez (fail-safe).
- qwen parse başarısız → `PARSE_FAIL`, terfi edilmez.
- Apply öncesi backup zorunlu; rollback tek UPDATE.

## Test
- Solver: 5 bilinen-cevaplı soruda (örn. 37 üçlü-teyitli) qwen doğruluğu smoke-test.
- Classifier: sentetik {qwen,DB} çiftleriyle kategori birim testi (TDD).
- Apply: pilot 3-5 ID'de backup+flag+correct_answer-değişmedi doğrulaması.

## Kapsam-Dışı (YAGNI)
- Harici API (Gemini/OpenAI), API key.
- İkinci model blind (kullanıcı kararı: tek qwen14 + DB + insan).
- DISPUTE'ların otomatik çözümü (sadece örneklenir).
- Real-time servis entegrasyonu / correct_answer düzeltme.

## Riskler
- **qwen YKS matematik zayıflığı:** Faz A bunu ölçer; zayıfsa o branş auto-promote'tan çıkar.
- **qwen==DB tek-model korroborasyon (pilot'taki çift-blind'den zayıf):** insan kalibrasyonu
  (Faz A+B) telafi eder; ayrıca qwen Claude'dan ve DB-kökeninden bağımsız.
- **Lokal GPU throughput:** 98K yavaş olabilir; kademeli + arka-plan kabul edilir.

## Reuse
`backend/scripts/quality/_pool_growth_pilot/` scaffold: prep_pilot.py (garble+stratify),
classify_results.py, apply_candidates.py — solver workflow→Ollama'ya çevrilir, gerisi adapte.
