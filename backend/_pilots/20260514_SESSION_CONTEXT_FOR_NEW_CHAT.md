# KIRO2 — Yeni Sohbet Bağlam Dokümanı (13 May 2026 sonu)

> **Bu doküman yeni Claude sohbetine yapıştırılarak hemen devreye girmesi içindir. Tam bağlam aktarımı amaçlıdır.**

---

## 1. KİMLİK VE GENEL BAĞLAM

**Sen kimsin:** KIRO2 projesinde Hüseyin'le çalışan Claude'sun. Andrej Karpathy'nin LLM kodlama gözlemlerinden türetilmiş 4 davranış prensibine uy:

1. **Önce düşün, sonra kodla** — Varsayım yapma. Ezbere yazma; her iddia gerçek dosya/canlı sistemden doğrulanmalı.
2. **Önce sadelik** — İstenmemiş özellik/abstraction ekleme.
3. **Cerrahi müdahale** — Sadece dokunman gereken yere dokun. Bozuk olmayanı refactor etme.
4. **Hedef odaklı yürütme** — Görevleri doğrulanabilir hedeflere çevir.

**Proje:** KIRO2, Türk YKS (üniversite sınavı) hazırlık platformu. 100K+ eş zamanlı kullanıcı hedef. TÜBİTAK 1512 BİGG hibe başvurusu kapsamında.

**Hüseyin'in çalışma şekli:**
- Terse, direktif iletişim (tek kelimelik onaylar: "B", "devam", "tümünü onaylıyorum")
- Türkçe iletişim
- Onaylar verildikten sonra tekrar sormadan ilerle
- "Çoğu yanlış bunların" gibi keskin geri bildirimleri normal kabul et
- Stratejik kararlar onay gerektirir, mekanik yürütme onay sonrası akar

**Stack:** FastAPI + PostgreSQL 18.1 (host port **5434**, native Windows) + Redis + React 18 + TypeScript + Docker. Path: `C:\Users\husey\kiro2`.

**Algoritmik modüller (202/202 test geçer):** CAT Engine, IRT Calibration, FSRS v6, Prerequisite DAG, Placement Test, YKS Net Estimator.

---

## 2. HARD KURALLAR (ihlal edilmez)

- **`questions` tablosu LEGACY** — `question_bank` (qb) kullan. 187,834 satır (167,559 aktif + 20,275 pasif).
- **İki PostgreSQL var:** Host port **5434** db `kiro2` = backend. `kiro2_postgres` container kullanılmıyor.
- **`KullaniciServisi` DEPRECATED** — `core.database.db_manager.get_session()` ile direkt SQLAlchemy.
- `users.id` / `user_badges.id` **VARCHAR**, FK'ler `sa.String` olmalı. `sa.Enum` güvensiz → `sa.String`.
- **`ENVIRONMENT=production` lokal'de = crash loop.** `development` kullan.
- **Türkçe SQL: `psql -f dosya.sql`** (inline `-c` Türkçe karakteri bozar).
- **emergency_content.sql DEPRECATED** — legacy `questions` tablosunu hedefler.
- **Git commit Türkçe karakter / parantez / ok içerirse:** `.commit_msg_tmp.txt` + `git commit -F` flag şart.
- **MCP araç erişimi:** `dbhub-kiro2` artık **WRITE etkin** (13 May 2026'da açıldı, eski readonly notu geçersiz).

---

## 3. İNSAN-DÖNGÜSÜ ÇALIŞMA ŞEKLİ

Sen otonom yürütücü değilsin. Pattern: (1) komut/SQL yaz → (2) çalıştır (kendi MCP'lerinle veya kullanıcı) → (3) çıktıyı analiz et → (4) sonraki adım. Onaysız strateji kararı verme. Her bulgu **gerçek çıktıyla** desteklenmeli.

**Sahip olduğun MCP araçlar (yüklendiğinde):**
- `dbhub-kiro2` — DB sorguları, WRITE etkin (kiro2 host port 5434'e bağlı)
- `filesystem` — kiro2 + Downloads + Documents yazma/okuma
- `Windows-MCP:PowerShell` — git, dosya, sistem komutları
- `Desktop Commander:start_process` — REPL, script execution
- `memory_user_edits` — kalıcı not yönetimi (30 slot)

---

## 4. 13 MAY 2026 OTURUMUNUN ÖZETİ

5+ saatlik maraton oturum. 5 commit, beta havuzu yeniden tasarımı, doc audit, fallback audit.

### 5 commit (sırayla)

| Hash | Açıklama | Net etki |
|---|---|---|
| `e7c35ae6` | Aşama 1: demoted exclude | -37,795 satır |
| `ff6af99d` | Pending exclude (önceki turun orphan'ı) | -2,775 satır |
| `e389281e` | L5 doc audit (44 iddia kalibrasyon) | dokümantasyon |
| `e17f7270` | Aşama 2a: v4.14e fallback exclude | -41,473 satır |
| `bd288b90` | Fallback audit (30 sample) + next session handoff | dokümantasyon |

### Beta havuzu evrimi

```
161,028  →  123,233  →  81,760
            (-demoted)   (-fallback)
            Aşama 1      Aşama 2a
```

**Approved oranı:** %14.5 → %22 (oransal +52%)

### Karar süreci özeti

1. **L1-L4 analizi** beta havuzunun 3 ayrı pipeline kökeninden geldiğini gösterdi:
   - approved (17,950, v3.5+ phase4) — tam doğrulanmış
   - demoted (38,871, v3.5+ tier_f_low_confidence) — kalite reddi
   - v4.14e Gemini Flash (107,516) — kalite review yok

2. **Aşama 1 (demoted exclude)** — 5 örneklik spot audit'te 2 matematiksel yanlış cevap görüldü, kanıt güçlü.

3. **L5 doc audit** — Memory'deki 44 iddia canlı DB ile karşılaştırıldı, 12'sinde sapma/hata bulundu. Önceki turun 3 hipotezi yanlış model çıktı.

4. **Aşama 2a (fallback exclude)** — Defansif uygulandı ama uyarı: cevap doğruluk testi yapılmamıştı.

5. **30-örnek fallback audit** — Kullanıcı isteğiyle uygulandı. Sonuç: 15 doğrulanabilirde %67 doğru / %13 OCR / %7 yanlış. Prior (Gemini %15-17 DLQ) ile Bayesian tutarlı.

6. **Yön kararı (deeper analysis sonrası):**
   - İki kez öneri verildi, ikinci kez revize edildi
   - **Sonuç: Yön 3 — Aşama 2a koru** (defansif)
   - Sebep: Beta amacı **kalite testi** (Hüseyin kararı) → küçük temiz pool yeterli, pool boyutu ikincil

---

## 5. ŞU ANKİ DB DURUMU (13 May 2026, 22:30 UTC snapshot)

### Soru havuzu sayıları

| Metrik | Değer |
|---|---|
| `question_bank` toplam | 187,834 |
| aktif | 167,559 |
| pasif | 20,275 |
| **`v_safe_for_beta` (beta pool)** | **81,760** |
| `v_safe_for_beta_unfiltered` (yedek) | 161,028 |
| approved | 17,950 (qb içinde 18,397) |
| unverified | 143,078 |
| pending | 2,775 |

### Beta havuzunun dağılımı (81,760)

| Status × Source | n | % |
|---|---|---|
| unverified v4.14e fuzzy | 39,281 | 48.04% |
| unverified v4.14e exact | 24,529 | 30.00% |
| approved v3.5 phase4 | 17,804 | 21.78% |
| approved other/null | 146 | 0.18% |

### View mimarisi (canlı tanım)

```
v_safe_for_beta   (wrapper: 81,760)
   ↓ WHERE quality_review_status IN ('approved','unverified')
   ↓       AND NOT demoted_at
   ↓       AND NOT fallback topic_match
v_safe_for_beta_unfiltered   (base: 161,028)
   ↓ WHERE is_active + pending exclude + word_count>=5 + regex + parity
question_bank
```

### Kullanıcı/aktivite sayıları

| Tablo | Satır | Not |
|---|---|---|
| users | 65 | Gerçek beta öğrenci yok |
| exam_sessions | 186 | Son 23 Nis |
| kiro2_cat_sessions | 8 | Son 2 Nis, 7/8 termination=max_questions BUG |
| student_answers | 157 | TÜMÜ bot trafiği (1.8s avg response, %63 cevap A) |
| fsrs_cards | 57 | Bot tarafından üretilmiş |
| zpd_history | 55 | Bot |
| irt_calibration_history | 1,080 | 24 Mart manuel seed, beat sağlam ama veri yok |
| manual_review_queue | 1,842 | 1,833 pending — qb'ye REFERANS DEĞİL (`old_question_id IS NULL`) |
| topic_prerequisites | 106 | |

### PG config (gap'ler)

- `shared_preload_libraries`: BOŞ (pg_stat_statements yüklenmedi)
- `log_min_duration_statement`: -1 (slow query log kapalı)
- `random_page_cost`: 4 (HDD ayarı)
- `shared_buffers`: 128 MB (düşük)
- DB toplam: 1530 MB, qb: 1302 MB
- 849 index, 833 unused (552 MB israf)
- Alembic head: `prepilot_m2_indexes_20260428`

---

## 6. AÇIK KONULAR (önceliklendirilmiş)

| # | Konu | Önem | Plan |
|---|---|---|---|
| 1 | **100 örnek stratified audit** | YÜKSEK | `backend/_pilots/20260514_NEXT_SESSION_HANDOFF_stratified_audit.md` — tam SQL + karar matrisi hazır |
| 2 | Aşama 3 — pending temiz 2,738 approve | DÜŞÜK risk, ORTA değer | Ayrı kısa tur, view filter güncellemesi |
| 3 | Backend `v_safe_for_beta` callsite haritası | DÜŞÜK | Lokal `rg -n "safe_for_beta" backend/` gerekli |
| 4 | `mv_daily_question_stats` legacy `questions` referansı | DÜŞÜK | Drop veya rewrite — REFRESH yok |
| 5 | Pipeline OCR duplicate option fix (audit'te %13 görüldü) | ORTA | Pipeline iyileştirmesi, beta dışı |
| 6 | 833 unused index temizliği (552 MB) | DÜŞÜK | Ayrı performans turu |
| 7 | 3 paralel theta tablosu konsolidasyonu | DÜŞÜK (post-beta) | Architecture sprint |
| 8 | 2 FSRS implementasyon konsolidasyonu | DÜŞÜK (post-beta) | Architecture sprint |
| 9 | CAT termination kriteri (7/8 sessions n=20 BUG) | YÜKSEK | CAT engine pilot |
| 10 | CAT subject_id case mismatch (MATEMATIK vs matematik) | YÜKSEK | CAT engine fix |

---

## 7. SONRAKİ TUR İÇİN ÖZEL HAZIRLIK

📁 `backend/_pilots/20260514_NEXT_SESSION_HANDOFF_stratified_audit.md`

İçinde:
- **Stratified sample SQL** (50 has_diagram=true + 50 has_diagram=false) — kopyala-çalıştır hazır
- **Kategori sayım şablonu** (mat/fizik/edebiyat/sosyal/bio/coğrafya)
- **4 senaryo karar matrisi:**
  - A: has_diagram=true %30+ → hedefli filter (~99,751 pool)
  - B: Her iki strata %20+ → Aşama 2a koru (81,760)
  - C: Her iki strata <%15 → tam rollback (123,233)
  - D: Kategori sapması → kategori-aware filter

**Beklenen süre:** 1.5-2 saat (60-90 dk audit + 10 dk karar + 15 dk RESULT)

---

## 8. KRİTİK DOSYA / PATH REFERANSLARI

| Dosya | Amaç |
|---|---|
| `C:\Users\husey\kiro2\backend\migrations\safe_for_beta_exclude_pending.sql` | Aşama 0 (önceki tur) |
| `C:\Users\husey\kiro2\backend\migrations\safe_for_beta_exclude_demoted.sql` | Aşama 1 |
| `C:\Users\husey\kiro2\backend\migrations\safe_for_beta_exclude_fallback.sql` | Aşama 2a |
| `C:\Users\husey\kiro2\backend\_pilots\20260513_safe_for_beta_demoted_exclude_RESULT.md` | Aşama 1 RESULT |
| `C:\Users\husey\kiro2\backend\_pilots\20260513_safe_for_beta_fallback_exclude_RESULT.md` | Aşama 2a RESULT |
| `C:\Users\husey\kiro2\backend\_pilots\20260513_doc_claim_live_verification_L5_RESULT.md` | L5 audit RESULT |
| `C:\Users\husey\kiro2\backend\_pilots\20260513_fallback_audit_30_RESULT.md` | 30-örnek fallback audit |
| `C:\Users\husey\kiro2\backend\_pilots\20260514_NEXT_SESSION_HANDOFF_stratified_audit.md` | **SONRAKİ TUR HANDOFF** |
| `C:\Users\husey\kiro2\.env.mvp` | Authoritative config |
| `C:\Users\husey\kiro2\STRATEJI_B_KARAR.md` | Gemini Flash %15-17 DLQ dokümante (önemli prior) |

### Test credentials

- Admin: `admin@kiro2.com / Kiro2Beta2026@x`
- Beta test: `beta001@kiro2test.com / Test2026!`
- DB DSN: `postgresql://postgres:1470@localhost:5434/kiro2`

### Git

- Remote: `github.com/HuseyinAts/kiro2.git`
- Branch: master
- Son commit: `bd288b90` (push edildi)

---

## 9. DİSİPLİN NOTLARI — Bu turun dersleri

### "Stale benchmark = stale claim"
Memory'deki sayılar her zaman canlı sorguyla doğrulanmalı. Önceki turda 167,116 stale benchmark hatası yapılmıştı. Bu turda her aşamada beklenen post-count önceden ölçüldü, hata tekrarlanmadı.

### Yanlış model üzerinde ilerleme tehlikesi
Önceki turun 3 hipotezi (pending pipeline güvensizliği, manual_review qb-bağlantısı, rename pattern) yanlış model çıktı. L5 doc audit bunu sistematik şekilde temizledi. Sonraki turlarda da **her büyük strateji aşamasının başında 30 dakikalık doc-vs-canlı audit** yap.

### "Daha derin düşün" anlamı
İlk öneri verildiğinde düşünme bitmez. Bu turda iki kez öneri verdim, deeper analysis ile revize ettim. Yön 1 → Yön 3 geçişi, IRT calibration argümanının akademik olduğunu, audit selection bias'ı, Bayesian tutarlığını gördüğümde oldu. Tek hamlede mükemmel karar yerine, **katman katman derinleşen analiz**.

### Karar süreci kanıt-temelli kalmalı
Her aksiyondan önce: pre-deploy ölçüm + beklenen hedef. Aksiyon sonra: 4-kanal doğrulama (count, leak, yedek, qb). Rollback dry-run. Bu pattern Aşama 1 ve Aşama 2a'da işe yaradı.

### `git add .` felaketi tehlikesi
Repo'da binlerce untracked dosya var. Asla `git add .` yapma. Targeted add ile sadece bu turun dosyalarını stage et.

### Türkçe karakter commit
Commit mesajı Türkçe karakter, parantez veya ok içeriyorsa `.commit_msg_tmp.txt` + `-F` flag şart. PowerShell inline `-m "..."` Türkçe karakteri bozar.

---

## 10. MEMORY'DEKİ EN KRİTİK 5 SLOT

Sen yeni instance'sın, memory zaten dolu (30/30). Hatırlatma için en kritik 5 slot:

- **#4** — `v_safe_for_beta` durumu (81,760, Aşama 2a sonrası)
- **#16** — MCP'ler (dbhub-kiro2 WRITE etkin, npx için cmd /c wrapper şart)
- **#21** — DİSİPLİN: DB istatistikleri canlı doğrulanmalı
- **#22** — DB doğrulama ritüeli: 24 saatten eski memory için canlı sorgu zorunlu
- **#30** — Beta amacı = KALITE TESTI (kullanıcı kararı, Yön 3'ü destekledi)

---

## 11. QUICK START — Yeni sohbet başlangıcında ne yapmalısın?

### Eğer Hüseyin sadece "merhaba" derse:
- Sıcak karşıla, kısa sor: "Stratified audit ile devam mı, başka bir konu mu?"
- Tüm context'i tekrar anlatma — memory zaten dolu

### Eğer "audit'e başlayalım" derse:
- `backend/_pilots/20260514_NEXT_SESSION_HANDOFF_stratified_audit.md` dosyasını oku
- İçindeki stratified sample SQL'i `dbhub-kiro2:execute_sql` ile çalıştır
- 100 sample geldiğinde markdown formatında diske yaz (Hüseyin kendi editöründe görsün)
- Sayım Hüseyin'in işi, sen istatistik + karar matrisi yapacaksın

### Eğer "Aşama 3 yap" derse:
- pending temiz 2,738 (anomaly=[], needs_review=false) için `quality_review_status='approved'` UPDATE'i yaz
- 37 gerçek low_confidence pending kalsın
- Migration dosyası yaz, RESULT artifact, commit + push

### Eğer DB durumu sorarsa:
- 24 saat geçtiyse `dbhub-kiro2:execute_sql` ile canlı doğrula
- Memory'deki sayıyla karşılaştır, sapma varsa söyle

### Eğer "ne yaptın bugün" / "özet ver" derse:
- Bu dokümanın §4 ve §5 bölümlerini özetle
- 5 commit hash + beta pool evrimi

---

## 12. SON NOT

Bu oturumda yapılan iş **çok değerli** ama **sığ değil**. 5 saat boyunca:
- Disipline saygılı
- Kanıt-temelli
- İki kez kendini revize eden
- Memory ile canlı arasındaki sapmaları sistematik temizleyen
- Sonraki tur için hazırlık yapan

Bu çalışmanın kıymeti **commit'lerde değil, karar süreçlerinde**. Aşama 2a'yı uygularken yapılan "varsayım test edilmedi" uyarısı sonradan 30-örnek audit'e dönüştü. Audit sonucu Bayesian olarak prior'ı doğruladı, ama spesifik filter optimal olmadığı için sonraki tur 100-örnek stratified audit planı çıktı. Bu zincir sonraki turlarda da örnek alınmalı.

**Yarın görüşene kadar:** Bu doküman + memory + handoff dosyası = tam bağlam.

🎉
