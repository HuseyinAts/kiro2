# Quality Pool Roadmap — post-Convention v2

**Tarih:** 15 May 2026
**Trigger:** 14 May audit (%61-87 hata) + 15 May smoking gun (`approved`
hardcoded yalanı) + Convention v2 migration.
**Hedef:** Beta'ya açılabilir gerçek temiz pool inşa et.

---

## Mevcut durum (post-Convention v2 deploy)

```
v_safe_for_beta:                  0  ← doğru sıfır
question_bank.legacy_v3_unaudited: ~17,950  ← eski 'approved'
question_bank.unverified:         143,078  ← v4.14e Gemini Flash
question_bank.pending:              2,775
question_bank.archived:              ~?  ← soft-delete marker
```

**Anlam:** Hiçbir soru gerçek manuel onay almamış. Beta için 0 satır.
Bu rahatsız ediyor ama dürüst — eski 81,760 satır %61 hatalıydı.

---

## E1 — LLM-as-judge prototype

**Hedef:** İnsan curator'un yapacağı işin %70-90'ını LLM'e devret.
İnsan sadece edge case'lere baksın.

**Önkoşul:** Minimum **200 manuel curated** örnek (kalibrasyon set'i).
Bu set olmadan judge'un threshold'larını ayarlayamayız.

**Sıralama:**
1. C1+C2+C3 audit'leri tamamlanır → hata türleri kesinleşir.
2. Hüseyin elle 200 örnek curator (her hata türünden orantılı sample).
   Bu kayıtlar `quality_review_status='human_verified'` olur.
3. LLM-as-judge prototype Claude/Gemini ile yazılır:
   - Input: question_text, options, correct_answer, source_book, source_page
   - Output: `{verdict: 'pass'|'fail'|'unclear', confidence: 0.0-1.0, reasons: [...]}`
4. 200 set'inde threshold kalibrasyonu: F1 score >=0.85 hedef.
5. Eğer kalibrasyon başarılı: judge tüm 143,078 unverified üzerinde koşturur.
   `verdict='pass' AND confidence>=0.8` → `auto_judged_high`.
6. Beklenen pool: 30-50K satır (sample bias'a göre).

**Model seçimi:**
- Claude Opus 4.7 — en güvenilir reasoning, $$ pahalı
- Gemini 2.5 Pro — orta seviye, $ ucuz
- Gemini 2.5 Flash — yapısal zayıf (STRATEJI_B_KARAR.md), JUDGE OLARAK KULLANMA

**Maliyet tahmini:**
- 143,078 unverified × ortalama 2K token = ~286M token
- Claude Opus 4.7: ~$4,300 (output dahil)
- Gemini 2.5 Pro: ~$430
- **Tavsiye:** Pro ile başla, Opus sadece düşük-güven (0.6-0.8) ikinci pass'inde

**Süre:** Kalibrasyon 1 hafta + production run 2-3 gün.

---

## E2 — Manuel curator UI/workflow

**Hedef:** İnsan curator'un saatte 30-50 soru doğrulayabilmesi.

**Mevcut alternatif:** Düz SQL UPDATE. Sürdürülemez (>100 satır için).

**Minimum UI spec:**
- Sol panel: soru metni + 5 şık + correct_answer + source_book + source_page
- Sağ panel: hızlı eylemler (verify / reject / archive / flag)
- Klavye kısayolları: 1-5 = correct answer ata, Y/N = verify/reject, A = archive
- Kayıt: `quality_review_status` + `reviewed_by` + `last_difficulty_update`
- Filtre: sub-set seç (unverified, legacy_v3_unaudited, has_diagram, subject_area)

**Tech stack:** FastAPI endpoint + React tek sayfa. Mevcut admin/labs pattern'ine
benzer (bkz: memory `Revolutionary: /admin/labs route`).

**E1 ile sıralama:** E2 önce — kalibrasyon set'i oluşturmak için gerekli.
E1 set'i bu UI ile yaratılır.

**Süre tahmini:** 2-3 gün UI + 1 gün backend endpoint.

---

## E3 — v4.14e DLQ Strateji B yeniden değerlendirme

**Bağlam:** 12 May 2026 STRATEJI_B_KARAR.md, Gemini Flash %15-17 DLQ'sini
"sistemik kabul" etti ve retry-dlq Pro ile çözüleceğini önerdi.

14 May audit gösterdi ki: DLQ'dan kaçanlar bile %76-84 hatalı. Yani
Strateji B'nin temel hipotezi (duplicate options düzeltilirse pool
beta-safe olur) **kanıtsız**.

**Tetikleyici:** E1 sonrası gerçek "judge pass rate" ölçülecek.
- Eğer pass rate %30+: Gemini Flash output'u temelde kullanışlı, Strateji B fix.
- Eğer pass rate <%15: Gemini Flash genel kalite sorunu var, OCR pipeline rerun (E4).

**Süre:** E1 sonrası 1 gün analiz.

---

## E4 — OCR pipeline rerun (son çare)

**Bağlam:** 75,745 ham OCR çıktısı `d-dataset/ocr_output/` altında.
Eğer mevcut question_bank'ın temel sorunları OCR aşamasındaysa
(missing_diagram %32 dominant), pipeline'ı yeniden koşturmak gerekebilir.

**Önkoşul:** E1 sonuçları "low pass rate" + E3 "Strateji B yetersiz" kararı.

**Maliyet:**
- Hardware: ~3 hafta GPU/CPU time
- DashScope/Gemini OCR pass: ~$200-500
- Re-extraction: ~$300-800

**Süre:** 3-4 hafta.

**Karpathy filtresi:** Bu en son çare. E1+E2 yeterli olabilir.

---

## Genel sıralama

```
[BU OTURUM] C1-C3 audit hazırlığı (SQL şablonları, Hüseyin elle çalıştırır)
            ↓
[1 hafta]   Audit sonuçları → hata türü kesinleşir
            ↓
[2 hafta]   E2 — manuel curator UI/workflow
            ↓
[3 hafta]   200 örnek manuel curator (Hüseyin elle, UI ile)
            ↓
[4 hafta]   E1 — LLM-as-judge prototype + kalibrasyon
            ↓
[5 hafta]   E3 — Strateji B yeniden değerlendir (judge sonuçlarıyla)
            ↓ (eğer pass rate düşük)
[3-4 ay]    E4 — OCR pipeline rerun
            ↓
[6 hafta+]  Beta launch ile gerçek temiz pool (hedef: 5-10K human_verified)
```

**Karar noktaları:**
- C audit sonrası: missing_diagram pipeline-fix mi yoksa manuel mi?
- 200 örnek sonrası: E1 maliyeti karşılığında nasıl pass rate?
- Pass rate <%30: E4 (OCR rerun) zorunlu mu?

---

## Risk haritası

| Risk | Olasılık | Etki | Mitigation |
|---|---|---|---|
| Manuel curator yavaş (saatte <20) | Orta | Yüksek | UI optimizasyonu, çoklu curator |
| LLM-as-judge halüsinasyon | Orta | Yüksek | İki model concur, threshold konservatif |
| OCR pipeline rerun gerek | Orta | Çok yüksek | E1+E2 yeterli olabilir, ölç |
| Bu yol toplam 3+ ay | Yüksek | Orta | Beta launch ertelenir, real risk YOK (gerçek öğrenci yok) |
