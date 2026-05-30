# Session — Kalite Kök-Neden Kazısı + Beta Clean Core (30 May 2026)

> Bu oturum Opus 4.8 harness demosu olarak başladı, **KIRO2'nin "kalite neden hiç yakalanamadı" kök-neden kazısına** ve somut bir **beta-ready 386-soru çekirdeği** üretimine dönüştü. Kapsamlı handoff — bir sonraki oturum buradan devam edebilir.

---

## 🎯 BU OTURUMUN MERKEZİ BULGUSU (en önemli)

**Kalite 198 session'a rağmen yakalanamadı çünkü "kalite" hiç öğrenci-deneyimi olarak tanımlanmadı; ölçmesi-kolay PROXY'ler (validate %95 PASS = sadece JSON format, soru-sayısı 45K vanity, cevap-doğruluğu) yerine kondu — hiçbiri öğrencinin yaşadığı tek katmanı (soruyu okuyup çözebiliyor mu?) ölçmedi. Ground-truth dairesel (0/167K insan onayı). En derin motor: yargıdan kaçınma — simülasyonda "harika olabilir" yaşar, gerçek öğrencide "vasat" olabilir.**

3 katmanlı doc (oku):
- `docs/audits/2026-05-30_kalite_kok_neden.md` (mekanizma: proxy + dairesel)
- `docs/audits/2026-05-30_kalite_kok_neden_DERIN.md` (yapı: kapalı-simülasyon, sıralama-imkânsızlığı, imkânsızlık üçgeni)
- `docs/audits/2026-05-30_kalite_kok_neden_EN_DERIN.md` (insan: yargıdan kaçınma, insan+AI amplifikasyon)

**AMPİRİK KANIT:** Kör 3-solver gate ile havuzun **~%80'i okunamaz** çıktı (pilot %28→val %14→full run %30 temiz verim). Format-validation "100% PASS" diyordu. Garble semantik (SQL/regex göremez).

---

## ✅ ÜRETİLEN SOMUT ARTIFACT: Beta Clean Core (386 soru)

`docs/audits/2026-05-30_beta_clean_core.md` — DB'de canlı, beta'ya hazır.
- **386 çift-doğrulanmış** soru: hem okunabilir (3 bağımsız kör-solver çözdü) hem cevap-onaylı (consensus==DB).
- DB flag: `pipeline_metadata.beta_clean_verified=true` (metadata-only; cevap/status DEĞİŞMEDİ).
- Sorgu: `SELECT * FROM question_bank WHERE pipeline_metadata::jsonb->>'beta_clean_verified'='true'`
- Backup: `question_bank_beta_core_backup_20260530` (500 satır, rollback hazır).
- Subject: MAT 156, GEO 78, FIZ 51, KIM 26, TUR 21, GENEL 16, BIY 13, EDE 11, TAR 10, SOS 3, COG 1.
- **114 disputed** (`pipeline_metadata.beta_answer_disputed=true`, +consensus_answer/db_answer): consensus≠DB. 20'si DB=A→A-bias DB hatası (gerçek). Curator review bekliyor.
- consensus-vs-DB sadece %77 uyum → "okunabilir" ≠ "cevap-doğru" (ayrı katmanlar).

Gate = kök-neden reçetesi: render `question_text` üzerinde KÖR çözüm (DB cevabı gösterilmez → dairesellik yok).

---

## 📦 BU OTURUMUN COMMIT'LERİ (master, push DURUMU aşağıda)
- `6862bef8a` (önceki) beta pool pilot
- `6a98e81d3` (önceki, oturum-öncesi) IRT cold-start bootstrap
- `246085612` fix: ralph-loop stale state sil + .local.md gitignore (jq hatası kök-çözüm)
- `6fe910f28` docs: YKS ürün-kalite %95 yol haritası (4 eksen workflow, skor 63/100)
- `8d2568a69` fix(retention): streak push canlıya (P0.1, TDD 5/5, celery beat + include + gerçek INSERT)
- `ec691a224` docs: kalite kök-neden 3-katman + görsel-metin brainstorm + P0.2 recon
- `721eeddd9` docs: beta clean core 386

## 🔧 STATE
- Branch **master**, son commit `721eeddd9`. **PUSH EDİLMEDİ** (tüm oturum commit'leri lokal).
- PG 5434 OK. Backend/Frontend muhtemelen DOWN (oturum boyunca DB-direkt çalışıldı).
- Git temiz değil: `_beta_core_tmp/`, `_beta_pool_tmp/`, `_p0_2_tmp/` working data (untracked, commit edilmedi — kasıtlı).

## ⚙️ ÖNEMLİ TEKNİK NOTLAR / GOTCHA
- **Workflow schema+dosya-okuma KIRILIR:** `agent({schema})` + Read + 50-cevap → StructuredOutput çağrılmıyor, batch'ler düşer. **Çözüm: schema YOK, düz JSON metni döndür + JS'te parse.** (1. run 87/500 düştü, fixed run 500 başardı.)
- **529/rate-limit:** 210 eşzamanlı ajan tetikledi. Sunucu-taraflı, geçici. Çözüm: dalga küçült (waveSize=3 → 9 eşzamanlı), bekle, retry'lama.
- `question_bank.id` VARCHAR (UUID değil) — `::uuid` cast kırar. `id = ANY(%s)` ile liste sorgula.
- `pipeline_metadata` tipi `json` (jsonb değil) → `(COALESCE(pm::jsonb,'{}')||%s::jsonb)::json` ile yaz.
- psql Windows: `PGPASSWORD=postgres "/c/Program Files/PostgreSQL/18/bin/psql.exe" -p 5434 -U postgres -d kiro2`
- Python stdout: `≥` cp1254'te crash → `sys.stdout.reconfigure(encoding="utf-8",errors="replace")`

## ⏳ BEKLEYENLER / SONRAKİ ADIMLAR
1. **TEK ACT — beta'yı 386 ile aç** (10-20 gerçek öğrenci, 1 hafta). Gerçek-yanıt → IRT kalibrasyon + cevap-anahtarı gerçek-doğrulama kilidi açılır. Hiçbir audit bunu ikame edemez. **EN ÖNEMLİ.**
2. Tüm oturum commit'lerini **push et** (`721eeddd9`'a kadar).
3. **114 disputed'ı Curator'da çöz** — 20 A-bias DB hatası düzelt, gerisi consensus-hatası mı ayır.
4. Çekirdeği büyüt (gerekirse): fixed workflow hazır — `scriptPath: .../beta-clean-core-500-wf_fca581e6-b49.js`, kalan 67 batch / havuz. ~%30 verimle daha çok temiz.
5. (Uzun yol) Garbage'ı kurtar: Vision re-gen (brainstorm `docs/brainstorms/2026-05-30_gorsel_metin_cozum.md` Faz 3) — crop'tan temiz metin üret. GEMINI_API_KEY rotate bekliyor (AUP P0).
6. Önceki bekleyenler (hâlâ geçerli): rationale %26.7 circular pass, beta-sonrası IRT EM→CAT döngüsü.

## 🔑 KRİTİK KÖK SORUN (referans, gelecek işler için)
Tüm soru havuzu **%100 görsel-türevli**; görseller frontend'de KAPALI (`ModernOSYMExamInterface.tsx:551` `false &&`, "Bug #11" cevap-leak — premise SPOT-CHECK'siz, doğrulanmamış olabilir). Öğrenci sadece OCR `question_text` görür, o da sık bozuk. cat_session.py:247/283 exclusion-regex sadece "şekil/grafik" KELİMESİ geçeni eler, bozuk LaTeX'i yakalayamaz. → görsel-türevli + görsel-kapalı + bozuk-metin = beta-core gate'inin var olma sebebi.

## 📂 ANAHTAR DOSYALAR
- Beta core: `backend/scripts/quality/_beta_core_tmp/{clean_final.json, apply_beta_core.py, batches/}`
- Gate workflow: `~/.claude/projects/.../workflows/scripts/beta-clean-core-500-wf_fca581e6-b49.js`
- P0.2 recon: `backend/scripts/quality/p0_2_abias_recon.sql`
- MEMORY güncellendi: `project_kalite-kok-neden.md` + beta-clean-core satırı.

## 🎭 META-DERS (bu oturum dahil)
"Cilayı bırak, gerçeğe dokun" reçetesi — ama oturum 4 tur "daha derin analiz" üretti; AI-işbirliği ajanı bunu yüzümüze tuttu: AI sınırsız proxy-artifact üretir, gerçek öğrenci getiremez. **Kural: kalite-task çıktısı gerçek kullanıcıya gösterilene kadar "tamamlandı" değildir.** 386 core bunun ilk adımı — şimdi #1 (beta aç) yapılmalı, daha fazla analiz değil.
