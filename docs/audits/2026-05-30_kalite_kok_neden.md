# Kalite Neden Hiç Yakalanamadı — Kök Neden Analizi

**Tarih:** 30 Mayıs 2026
**Tetikleyen soru (Hüseyin):** "Bu tip OCR/kalite işlemlerini defalarca yaptım ama gerekli kaliteyi yakalayamadım. Kök sebebini bul."
**Yöntem:** 4 paralel salt-okunur forensics ajanı, 4 ayrı lens (veri-lineage / süreç-rework / ground-truth / strateji-hedef). Kanıtlar `dosya:satır`, git, docs/audits, .claude/rules genesis. ~616K token.

> Dört lens **bağımsız olarak aynı kök nedene yakınsadı.** Bu yakınsama tesadüf değil — yapısal bir gerçeğin dört yüzü.

---

## Tek Cümlelik Kök Neden

**"Kalite" hiçbir zaman öğrenci-deneyimi olarak tanımlanmadı; bunun yerine ölçmesi-kolay otomatik proxy'ler (format-PASS %95, soru-sayısı 45K, cevap-doğruluğu, kaynak-anlaşması) "kalite" yerine kondu. Bu proxy'ler öğrencinin yaşadığı tek katmanı — "soruyu okuyup çözebiliyor mu?" — HİÇ içermedi, ve ground-truth pipeline'ın kendi çıktısıyla dairesel doğrulandı (0/167K insan onayı). Sonuç: 3 ay ve onlarca OCR turu, ölçülmeyen ve kırık bir temelin ÜSTÜNDEKİ katları optimize etti — gerçek kalite yapısal olarak ulaşılamazdı.**

---

## İki Pekiştiren Mekanizma

### 1. Katman-hatası (Maslow tersine çevirme)
Öğrencinin gördüğü tek şey `question_text` (OCR metni). Ama bütün emek bunun ÜSTÜNDEKİ katmanlara gitti:

| Katman | Ne zaman ele alındı | Sonuç |
|--------|---------------------|-------|
| **L0 — Soru okunabilir mi** (figür/metin sadakati) | **30 May, ilk kez, kazara** | Temel katman atlandı |
| L1 — Görselin varlığı (image-match Tier A-H) | Nis-May (S157-158) | %99 coverage — **ama görsel `false &&` ile KAPALI** |
| L2 — Cevap anahtarı doğru mu (S182-198) | 23 May | 2,547 düzeltme — okunamayan soruya |
| L3 — Rationale açıklaması (Phase 7) | 22 May | %26.7 kabul edilemez |

**En keskin kanıt:** Image-match Tier H **49,468 satır** işledi (sonra rollback) — görseli eşleştirmek için onlarca session — ama `ModernOSYMExamInterface.tsx:551` görseli `false &&` ile render etmiyor. *Render edilmeyen bir alana aylarca yazıldı.* `pipeline.py:286` OCR prompt'u figürü açıklamıyor (sadece görünen metni alıyor), yani figür-bağımlı sorular L1'de zaten çözülemez doğuyor.

### 2. Dairesel öz-doğrulama (ground-truth yok)
Dört kalite kapısının da ground-truth'u ya dairesel ya yanlış-katman:

| Kapı | Ground-truth = | Sorun |
|------|----------------|-------|
| `cross_validate_answers.py` | "kaynaklar hangi harfte anlaşıyor" | Kaynaklar ortak OCR-hatasını paylaşırsa anlaşma = **korelasyonlu hata** (A-bias) |
| `validate_sample.py` (13 check) | JSON şema bütünlüğü | "100% PASS" = format temiz, **cevap/okunabilirlik DEĞİL** |
| `curator.py` R4 | kitap-adı dışlama + flag yokluğu | "auto_judged_high" — **hiçbir yargı yok**, sadece dışlama |
| Phase 7 rationale | DB cevabı = aksiyom | DB yanlışsa **CIRCULAR** gerekçe (%55 matematik circular) |

**0/167,559 soru insan tarafından doğrulandı** (`curator_verdict` = 0, bu session'da DB'den teyit edildi). Pipeline kendi biased çıktısının kendisiyle tutarlılığını "kalite" sanıyor.

---

## Neden Sonsuz Çaba Bile Çözmedi (yapısal argüman)

- **Süreç forensiği:** ~149 audit doc / 2 ay (1 doc/10 saat). Döngü *dalga-içi* kapanıyor (21 May Mega %97) ama *dalgalar-arası* kapanmıyor — her mega-audit eski backlog'u devralmak yerine yeni baseline'dan başlıyor. S197: **8 P0'ın %75'i phantom.**
- **`.claude/rules/` = başarısızlık fosil kaydı:** 8 kuralın en az 4'ü aynı sınıftan doğdu — **"doğrulanmamış proxy sinyale gerçekmiş gibi güvenip toplu aksiyon"** (Tier H tek-sinyal, `LEFT(text,200)` truncation %24-vs-%2.15, %67 phantom, A-bias kaynak-biased). Aynı ders 2-3 kez öğrenildi (Health 503: S7/12/19).
- **Vanity-metric:** soru sayısı (45K→%172 EXCEEDED 🟢) gerçek metriği gizledi: **beta-safe = 10,535/167,559 = %6.3**. ~16x uçurum. Bugün bile "high-confidence 25K bulk-promote" cazibesi ~16,900 hatalı soruyu beta'ya sokacaktı (verify-first son anda durdurdu).
- **Garble ölçülemez:** "loylak/bilkidir" gibi anlamlı-ama-yanlış OCR kelimeleri NFC-normal, ASCII, tekrarsız → 13-check'ten PASS alır. Bozulma **semantik**, hiçbir regex/SQL/chi-sq yakalayamaz. Ölçüm aracı yanlış katmana baktığı için gerçek problem görünmez kaldı.

---

## Düzeltici İlke (act-on-this)

1. **Kaliteyi öğrenci-katmanında operasyonel tanımla.** Tek geçerli metrik: *"Temsili bir öğrenci, ekranda GÖRDÜĞÜ haliyle bu soruyu okuyup çözebiliyor mu, VE bağımsız bir çözücü keyed-cevaba ulaşıyor mu?"* — JSON şemasında değil, **render edilen artifact** üzerinde ölç.
2. **Daireselliği insan/bağımsız ground-truth ile kır.** Hiç yapılmayan tek şey: gate'e insan onayı (veya en azından kör-bağımsız çözüm — bu session'da 42-sample ile kanıtlandı). DB-cevabını LLM'e verip "doğrula" demek dairesel; kör çözdürmek değil.
3. **Önce temeli (L0 okunabilirlik) at.** Daha fazla cevap-anahtarı/rationale işi YOK — `gorsel_metin_cozum.md` Faz 0→1→2 sırası tam bu (artık kök-neden ile doğrulandı).
4. **Vanity-metric'i bırak.** Tek sayı: *okunabilir-VE-çözülebilir-VE-doğrulanmış* soru sayısı. Diğer her şey yanıltıcı.

---

## Phantom/Gerçek Dürüstlüğü

- **Gerçek ilerleme:** 21 May Mega %97 follow-through; S194 A-bias root #2 pipeline fix (78/78 test, adversarial verify); cevap-ekseni %96 doğruluk.
- **Phantom/rework:** %75 phantom P0; 8,913-soru d-dataset silme-churn'ü; render edilmeyen görsele yazılan image-match emeği; "temizlenen" 787 sorunun otomatik (manuel değil) geri-promote'u.
- **Bu analizin sınırı:** Kök neden 4-lens yakınsaması + canlı kanıtla güçlü ama bir HİPOTEZ değil teşhis seviyesinde. Doğrulama: düzeltici ilke uygulanınca (render-artifact üzerinde kör-çözüm gate) beta-safe sayısı GERÇEK okunabilirlikle yeniden ölçülmeli.

---

*Oluşturulma: 30 May 2026. 4 forensics ajanı (veri-lineage / süreç / ground-truth / strateji). İlişkili: `2026-05-30_yks_quality_95_roadmap.md`, `docs/brainstorms/2026-05-30_gorsel_metin_cozum.md`, `.claude/rules/audit-methodology.md`.*
