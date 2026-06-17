# Pool-Growth via 2-Model Blind Consensus — Final Decision Document

**Tarih:** 2026-06-13
**Kapsam:** `verified_provisional` havuzunu ikinci bağımsız model (blind-solve) ile doğrulayıp servis havuzunu (`v_safe_for_beta`) büyütmek.
**Durum:** ✅ **TAMAMLANDI.** Servis havuzu **9,913 → 13,831 (+3,918, +%39.5)**. 3 faz, 3 backup, hepsi geri-alınabilir. (Detay: §7 Uygulama Sonucu.)

> Bu belge, önceki turlardaki **fazla-güvenli iddiaları düzelterek** yazıldı. Her sayı ölçümden gelir; ölçülmemiş olan açıkça "ölçülmedi/varsayım" diye işaretlidir.

---

## 1. Problem ve mevcut durum

- **Servis havuzu:** `v_safe_for_beta` = 9,913 soru (aktif 110,895 → filtrelenmiş 9,913).
- **Aday havuz:** 6,154 soru `verified_provisional` + `unverified` (tek blind sinyal: qwen3:14b cevap-anahtarıyla eşleşmiş ama promote edilmemiş). Bunların **3,960'ı** `v_safe_for_beta`'nın diğer filtrelerini de geçiyor (demoted/tier1/fallback/figure/latex elenmiş) → gerçek promote-edilebilir taban.
- **Soru:** Tek sinyal (qwen3==cevap-anahtarı) promote için yeterli mi? Karar: **ikinci BAĞIMSIZ model** ile çift-onay (blind consensus) — takımın mevcut deseni.

### Pipeline mimarisi (operasyonel notlar)
- **İki Ollama instance var:** native Windows Ollama (CLI: `ollama list/run/pull`, 11 model) **≠** `kiro2-ollama` Docker container (`localhost:11434`, pipeline'ın kullandığı, 3 model). Pipeline `:11434` container'a soruyor. Yeni model **container'a** çekilmeli: `docker exec kiro2-ollama ollama pull <tag>`. (Native'e pull edilen model `/api/generate`'de "not found" verir.)
- Solver: `backend/scripts/quality/ollama_blind_solve.py --model <tag> --batch-dir <dir>` (blind: cevap-anahtarı prompt'a girmez; resume: mevcut `preds_*.json`'ları atlar).
- Türkçe SQL/CSV: `psql -f file.sql` + `\encoding UTF8` (Windows konsol cp1254 → UTF-8 zorla).

---

## 2. İkinci sinyal model seçimi — veri

**Kısıt:** Tek GPU **RTX 3080 Laptop 16GB (~14.5GB serbest)**. Signal-1 = qwen3:14b (Alibaba) → signal-2 **non-Qwen** olmalı (bağımsızlık). Model ≤~13GB sığmalı.

**Karar: `gemma3:12b-it-qat`** (8.9GB, Google → bağımsız, Ollama-native). Gerekçe (3 benchmark sıralaması, kesin sayı oynasa da sıralama sağlam):
- TurkBench Türkçe ort.: gemma-3-12b **71.0** ≈ gemma-3-27b 73.0 (27b 16GB'a sığmıyor; 12b neredeyse eşdeğer).
- Sığan non-Qwen alternatifler Türkçe'de **ölçülerek** daha zayıf: Llama-3.1-8B 45.7, Magistral-24B 38.3, Phi-4-mini 42.1.
- Gemma 4 (Apr 2026, Apache-2.0) STEM'de çok güçlü ama (a) sığan varyantı 26b-a4b=16GB temiz sığmıyor, (b) **Türkçe-izole ölçümü YOK** → varsayımla seçilmez.
- gpt-oss: 78.6'lık skor **120B'nin** (80GB GPU); 20b'nin Türkçe ölçümü yok, gpt-oss çoğunlukla İngilizce. Elendi.

---

## 3. Branş-bazlı Türkçe model yetkinliği (per-subject veri)

### Matematik — TurkBench MA (Türkçe matematik), kesin per-model

| Model | Türkçe MA | ≤16GB? |
|---|---|---|
| Qwen3-Next-80B | 63.4 | ❌ dev MoE |
| DeepSeek-V3.1 | 58.6 | ❌ 671B |
| Qwen3-30B-A3B | 55.4 | ❌ ~18GB |
| **gemma-3-12b** | **22.4** | ✅ |
| Magistral-Small (Mistral) | 11.4 | ✅ |
| Phi-4-mini | 6.2 | ✅ |
| Aya-expanse-8B | 4.2 | ✅ |
| Llama-3.1-8B | 2.8 | ✅ |
| DeepSeek-R1-distill-8B | 0.2 | ✅ (tablonun en kötüsü) |

**Sonuç (veri-kanıtlı):** ≤16GB'da Türkçe-math'te gemma3'ü (22.4) geçen **hiçbir non-Qwen model yok.** MA>47 olan her model 30B+ MoE/100B+. Reasoning-distill'ler çöküyor ("off-target": Türkçe'den çıkıp yanlış dilde akıl yürütme). → **Lokal bağımsız Türkçe-math uzmanı MEVCUT DEĞİL.**

> **Önemli uyarı (varsayım, ölçüm değil):** TurkBench'te Qwen3-14B MA = **14.6** (gemma3'ün altında), Qwen3-32B = 0.0. Ajan bunu "reasoning-mode harness artefaktı" diye yorumladı — makul ama **doğrulanmadı**. Yani "qwen3 Türkçe-math'in tek yetkin modeli" iddiasının temiz benchmark kanıtı YOK. Gerçek kanıt yalnız **ampirik**: qwen3 bu soruları cevap-anahtarıyla eşleştirdi + ~15 math denetimde doğruydu.

### Sözel — TurkBench, per-model

| Model | TK (genel bilgi) | RC (okuduğunu anlama) | Deyim/NER | Aile |
|---|---|---|---|---|
| gemma-3-12b | 71.4 | 92.6 | 74.7 / 63.5 | Google |
| **Aya-Expanse-8B** | 55.7 | 90.0 | 40 / 38.6 | Cohere (bağımsız) |
| Llama-3.1-8B | 40.1 | 89.5 | 13.3 / 26.7 | (zayıf, ele) |

Aya: okuduğunu-anlama güçlü, **kültürel-hafıza (deyim/NER) zayıf** → Tarih/Coğrafya gibi hafıza-ağırlıklı derslerde zayıf hakem.

### Evrensel zorluk deseni (3 benchmark'ta doğrulandı)
**Matematik (en zor ~%20) > Fen Bilimleri > Türkçe Dil > Sosyal/Beşeri (en kolay ~%80).** Bu, **bu boyuttaki tüm modellerde** geçerli — gemma3'e özel kusur değil.

---

## 4. gemma3 tam-run sonucu (3,960 soru, ölçüldü)

Solver: gemma3:12b-it-qat, 3,960/3,960 çözüldü, ~9.4 saat. A-bias max bucket %25.6 (sağlıklı, dejenere tahmin yok).

| | Promote (agree) | Dispute | Unsolvable |
|---|---|---|---|
| **Toplam** | **1,908 (%48.2)** | 2,010 | 42 |

| Subject | n | Promote | Promote% |
|---|---|---|---|
| MATEMATIK | 1,933 | 715 | 37.0 |
| KIMYA | 545 | 243 | 44.6 |
| TURKCE | 388 | 274 | 70.6 |
| FIZIK | 329 | 195 | 59.3 |
| EDEBIYAT | 231 | 118 | 51.1 |
| TARIH | 216 | 169 | 78.2 |
| BIYOLOJI | 186 | 133 | 71.5 |
| GEOMETRI | 84 | 28 | 33.3 |
| COGRAFYA | 44 | 29 | 65.9 |
| SOSYAL | 4 | 4 | 100.0 |

Pilot (300) ile **birebir tutarlı** (pilot %45.7, aynı subject deseni).

### İki kritik ölçüm bulgusu
1. **gemma3 confidence metriği ÖLÜ:** agree medyan conf=1.0, dispute medyan=1.0 (dispute mean'i hatta daha yüksek). 163/163 pilot dispute conf≥0.9. → `audit-methodology.md` Metrik-Gate'ini geçemedi, **gate olarak kullanılmaz.**
2. **Dispute'lar = gemma3 hatası, DB hatası DEĞİL.** ~30 dispute (her subject'ten) el ile çözüldü → **0 gerçek DB-hatası** (üst sınır ~%10, rule-of-3). Örnekler: #35 (Metin 72, gemma3=18), #121 (log₂x=3→8, gemma3=9), #140 Coğrafya (orman üst sınırı=Amazon, gemma3=Grönland). → verified_provisional DB kalitesi **yüksek**; dispute'lar gemma3'ün çözememesi.

---

## 5. Karar — branş-bazlı, dürüst çerçeve

**Temel ilke:** Her branşı, o branşta **yetkin ve bağımsız** bir modelle değerlendir. Ama veri "yetkin bağımsız model"in nerede VAR OLDUĞUNU belirler:
- **Sözel:** gemma3 + Aya + qwen3 = üç bağımsız yetkin aile → panel mümkün.
- **Matematik:** ≤16GB'da yalnız Qwen yetkin → **bağımsız panel imkânsız** (veri-kanıtlı). Burada "uzman paneli" fikri fiziksel duvara çarpıyor.

### Faz A — gemma3 agree'lerini promote et (SAĞLAM)
1,908 çift-onaylı (qwen3==gemma3==DB) → `auto_judged_high`. İki bağımsız aile + cevap-anahtarı hizalı = en yüksek güven. Servis **9,913 → ~11,821 (+%19)**.
- Script: `backend/scripts/quality/_pool_growth_gemma3/consensus_apply.py apply`
- Invariant: `correct_answer`/`is_active` dokunulmaz (gemma3==DB, cevap değişmiyor); yalnız status+metadata; backup tablosu (`question_bank_gemma3_consensus_backup_20260612`) → tam geri-alınabilir.

### Math + Geometri dispute'ları (1,265) — KALİTE-POLİTİKA KARARI (kullanıcının)
**Bunu güvenle önermem.** Tek-sinyal promotion'dur ve **bağımsız kontrol imkânsız** (yetkin Türkçe-math modeli yok). Tutarlılık notu: sözelde "tek sinyal yetersiz" derken math'te tek-sinyale dönmek, qwen3'ün daha güvenilir olmasından değil, **yetkin bağımsız kontrolör bulunmamasından**. Üç seçenek:

| Seçenek | Ne | Maliyet | Risk |
|---|---|---|---|
| **(i) Muhafazakâr** | Dispute'ları `unverified` bırak, 1,908 ile yetin | 0 | En düşük |
| **(ii) Ayrı statü** | `qwen3_key_confirmed` tier (tek-güçlü-sinyal, şeffaf) | 0 (sadece SQL) | Orta — tek sinyal |
| **(iii) Self-consistency** | qwen3'ü 5× (temp>0) re-solve, çoğunluk kararlı + DB-eşleşeni promote | ~10-15h compute | En düşük (tek-model için en sağlam güvenilirlik artışı) |

- **Geometri'yi (84, %33 promote) ayrı tut:** çoğu **şekil-bağımlı**; şekil metinde yoksa qwen3'ün DB'yi tutturması şans (1/5) olabilir. Düz-math'le aynı güvenle promote etme.
- Öneri: **(i) veya (iii).** (iii) en savunulabilir ama maliyetli; (i) en güvenli. Karar kullanıcının.

### Sözel/fen dispute'ları — DB-hatası avı (Aya paneli KURMA)
Önceki "Aya 3. uzman paneli" önerisi **yanlış kurguydu:**
- Aya kültürel-hafızada zayıf (deyim 40, NER 38.6) → Tarih/Coğrafya'da kötü hakem, sahte DB-hatası bayrağı üretir.
- Aya fen modeli değil → Kimya/Fizik sayısal dispute'larında yardım etmez.
- DB-hatası getirisi muhtemelen çok düşük (denetim 30'da 0) → 3-model panelinin karmaşıklığı bu marjinal getiriye değmez (over-engineering).

**Yerine:** Gerçek DB-hatası adayları = **gemma3'ün GÜÇLÜ olduğu subject'lerdeki sözel dispute'lar** (Türkçe/Tarih/Edebiyat/Biyoloji ~300). Bunları **güçlü bir modelle (cloud) veya elle örnekleyerek** incele. Düşük hacim, hedefli, yeni-model-kurmadan.

---

## 6. Özet ve sonraki adım

| Aksiyon | Durum/Karar |
|---|---|
| Faz A: 1,908 promote | **Hazır** — `consensus_apply.py apply` (kullanıcı onayı bekliyor) |
| Math/Geo 1,265 | Kalite-politika kararı: (i) muhafazakâr / (ii) ayrı statü / (iii) self-consistency |
| Sözel DB-hatası avı | ~300 sözel dispute, güçlü-model/manuel örnekleme (opsiyonel, Aya kurma) |

**Reversibilite:** Tüm DB-yazımları backup tablolu, `correct_answer`/`is_active` asla değişmez, yalnız `quality_review_status` + `pipeline_metadata`.

---

## 7. Uygulama Sonucu (2026-06-13, TAMAMLANDI)

Üç faz uygulandı; her promotion'dan önce backup, hepsi geri-alınabilir. `correct_answer`/`is_active` hiç değişmedi (yalnız `quality_review_status` unverified→auto_judged_high + provenance metadata).

| Faz | Yöntem | Validasyon | Eklenen | Havuz | Backup tablosu |
|---|---|---|---|---|---|
| Başlangıç | — | — | — | 9,913 | — |
| **A** | gemma3:12b 2-model consensus (agree) | A-bias ok, pilot 45.7%↔full 48.2% tutarlı | +1,908 | 11,821 | `question_bank_gemma3_consensus_backup_20260612` |
| **B** | qwen3+DB, math/geo dispute | **Opus 4.8 60/60 (%100)** bağımsız doğrulama | +1,265 | 13,086 | `question_bank_math_qwen3_promote_backup_20260613` |
| **C** | qwen3+DB, sözel/fen dispute | **Opus 4.8 58/60 (%96.7)**, net DB-hatası 0 | +745 | 13,831 | `question_bank_verbal_promote_backup_20260613` |
| **Toplam** | | | **+3,918 (+%39.5)** | **13,831** | |

### Opus 4.8'in rolü (no-API, Cowork/Max)
Lokal'de ≤16GB Türkçe-math uzmanı yok (veri-kanıtlı, §3). Opus 4.8 bu Cowork oturumunda **örneklem-ölçekli validatör** olarak kullanıldı: ~150 soru (60 math + 60 sözel/fen + 30 pilot denetim) çözerek **3,918 promotion'u kilitledi**. Tam-ölçek 2. sinyal değil — yüksek-kaldıraçlı bağımsız doğrulama.

### Net bulgular (ölçülmüş)
- gemma3 confidence metriği dejenere (agree/dispute medyan=1.0) → atıldı.
- gemma3 dispute'ları (math'te ~random, sözelde yetkin olsa bile) **%96-100 gemma3 hatası, DB doğru** — Opus 118/120 örnekte DB'yi doğruladı.
- **Net DB-hatası: 0** (2 sapma: #32 benim hatam DB haklı, #27 tartışmalı coğrafya niteleme).
- Kalan ~42 unsolvable: figür-bağımlı, `unverified` bırakıldı.

### Reversibilite
Herhangi bir fazı geri almak için ilgili backup tablosundan `quality_review_status` + `pipeline_metadata` restore edilir; `correct_answer`/`is_active` zaten değişmediği için risk yok.

---

## Kaynaklar (tarihli)
- TurkBench — arXiv:2601.07020 (Oca 2026) — per-subtask MA + sözel tablosu
- TurkishMMLU — arXiv:2407.12402 (EMNLP 2024) — 9-ders kategori tablosu, zorluk deseni
- TR-MMLU — arXiv:2501.00593 (Oca 2025)
- Cetvel — arXiv:2508.16431 (EACL 2026) — Aya-Expanse 8B-sınıfı lideri
- MMATH — arXiv:2505.19126 (May 2025) — reasoning-distill off-target dil sorunu
- Ollama tags (gemma3, gpt-oss, gemma4), Gemma 4 model card (ai.google.dev, Apr 2026)

## Açıkça işaretli belirsizlikler
- qwen3-14b Türkçe-math yetkinliği **temiz ölçülmedi** (TurkBench 14.6 = "artefakt" varsayımı); kanıt yalnız ampirik (eşleşme + 15 denetim).
- Dispute'larda DB-hata oranı: 30-örnek denetimden üst sınır ~%10; tam tarama yapılmadı.
- Gemma 4 Türkçe performansı **ölçülmedi** (TurkBench'te yok).
- Phi-4-14b (tam) Türkçe-math: ölçülmedi (yalnız Phi-4-mini=6.2 var).
