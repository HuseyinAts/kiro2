# Kalite Kök Neden — DERİN KATMAN (v2, ilk analizi derinleştirir)

**Tarih:** 30 Mayıs 2026
**Yöntem:** 4 paralel derin forensics ajanı (platform-geneli desen / yukarı-akış+imkânsızlık / **adversarial karşı-teşhis** / gerçeklik-teması). Önceki `2026-05-30_kalite_kok_neden.md`'yi **çürütmedi, derinleştirdi** — onun "proxy/dairesel/Maslow-tersine" bulguları MEKANİZMA; bu doc GENERATOR + KİLİT'i buluyor.

> İlk analiz: "yanlış katman ölçüldü." Bu doğru ama **semptom katmanı.** Daha derin: *neden* yanlış katman ölçüldü, ve *neden* hiçbir cila yakınsamadı.

---

## En Derin Kök Neden (tek paragraf)

**Platform, dış-gerçeğe hiç dokunmamış tam-kurulu bir KAPALI-DEVRE SİMÜLASYON: sentetik yanıtlar → bootstrap IRT prior → makine-judge kalite → makine-konsensüs curator; hiçbir halka gerçek öğrenciye bağlı değil. "Kalite"yi *launch-öncesi mükemmelleştirilebilir bir özellik* sanmak temel hata — çünkü kalite yapısal olarak *launch-sonrası ortaya çıkan* bir özellik (her metrik gerçek-öğrenci-temasını gerektiriyor). İki iç içe generator bu kapalı-döngüyü yarattı: (1) operasyonel "iyi soru" tanımı / golden eval-set HİÇ olmadı → ölçecek referans yokken ölçmesi-kolay proxy boşluğu doldurdu; (2) tertemiz küçük çekirdek (50-100 soru) kurulmadan 167K'ya ölçeklendi → doğrulama imkânsız hacme çıktı. Sonuç: yakınsama kriteri (gerçek-öğrenci-sinyali) döngünün DIŞINDA kaldığı için sonsuz cila bile kaliteyi yakalayamaz.**

---

## 1. Hard DB Kanıtı — hiçbir şey gerçeğe dokunmadı (en sağlam bulgu)

| Gerçeklik sinyali | Var mı? | Canlı DB kanıtı (5434) |
|---|---|---|
| Gerçek öğrenci yanıtı | **HAYIR** | `irt_n_responses>0` = **0** (187,834 sorunun tamamı). `kiro2_learning_events`=254 (hepsi test@/beta01@). **`..._synthetic`=117,179** (`generate_synthetic_responses.py`) |
| İnsan-etiketli golden set | **HAYIR** | `curator_verdict`=**0** (Curator UI S178'de yapıldı, tek insan oyu girilmedi). Tüm status makine-yargısı |
| Gerçek retention/davranış | **HAYIR** | `fsrs_reviews`=0, `fsrs_study_sessions`=0, `fsrs_cards`=100 (seed) |
| Beta kullanıcı | **HAYIR** | `users`=75-100, **%100 test/seed**, organik kayıt 0 |
| IRT kalibrasyon | **HAYIR** | 167,559/167,559 `irt_method='bootstrap_difficulty_prior'` — kod itiraf ediyor: "yanıt yok, kalibrasyon matematiksel imkânsız" |

Bu narrative değil, sayı. **Kapalı simülasyon tezi en sağlam-kanıtlı bulgu.**

## 2. Platform-geneli hastalık (8/8 sütun, içeriğe özgü DEĞİL)

Aynı "proxy gerçeğin yerine geçti + ground-truth döngüsü hiç kapanmadı" patolojisi her sütunda:

| Sütun | Proxy | Gerçek olması gereken | Kanıt |
|---|---|---|---|
| IRT zorluk | öğretmen-etiketi `difficulty_level` | yanıt-kalibre `b` | 167K bootstrap, 0 response |
| CAT seçimi | proxy-`b` üzerinden Fisher-optimal | gerçek bilgi | `irt_engine.py:265` |
| **`is_calibrated` sinyali** | bootstrap'ı "kalibre" raporluyor | response-türevli ise TRUE | `irt_engine.py:66` **YANLIŞ-POZİTİF** |
| Quest/dungeon | client self-report +1 | server-doğrulanmış eylem | `daily_quest_api.py:219` |
| Analytics | 17/20 flag mock | DB-türevli | `mock_endpoint_flags.json` |
| İçerik | format-PASS / cevap-doğru | öğrenci-okunabilir + insan-onay | `cross_validate:125 "placeholder until human GT"` |

**Mimari doğruyu BİLİYOR** (is_calibrated kolonu, server-validation docstring, _real impl'ler var) ama **gerçek-veri yolu her yerde boş.** Refleks: boşluğu görünür bırakmak yerine proxy ile maskelemek. (`is_calibrated=TRUE` yanlış-pozitifi bu refleksin en saf kanıtı.)

## 3. Yukarı-akış: kaynak Gün-1'de yapısal yetersizdi, yanlış teşhis edildi

- Kaynak = 1080p taranmış-kitap screenshot. Etkin karakter genişliği: uzun paragraf 70-85 char/satır → **8-10px** (Session 87 eşiği: <7px sistematik hata, ≥12px hedef). Uzun-metin + figür-bağımlı sorular **L0'da çözülemez doğuyor.**
- **Gün-1 ölçüldü** (`25_KITAP_ANALIZ_RAPORU.md`, 1 Oca: %15.7 halüsinasyon, Paragraf %24, Türkçe %26) ama **"yayınevi-seçimiyle çözülür içerik sorunu"** sanıldı → "%96 kullanılabilir" denip ölçeklemeye geçildi. Gerçekte yapısal (fizik): hangi yayınevi olursa olsun uzun-metin char-width aynı düşük.
- Nüans: matematik/geometri (kısa metin, %9 halüs) sınırda-yeterli; sorun homojen değil. **Temiz 15-25K mat/geo çekirdeği bu kaynakla mümkündü; 167K tüm-konu sınav-derecesi değildi.**

## 4. İmkânsızlık üçgeni (aritmetik)

167K kapsam × sınav-derecesi kalite × manuel doğrulama (~%35dk/8 soru):
- 167,559 ÷ 8 × 35dk = **~12,218 saat ≈ 6.1 insan-yılı**. Sadece beta-safe 10,535 için bile **~768 saat ≈ 4.6 ay tam-zaman.**
- Üç kısıt aynı anda **imkânsız.** Gerçekleşen sonuç bunu kanıtlıyor: kapsam %172 AŞILDI ✅ (otomasyonla ucuz köşe), doğrulama **0/167K** (insan-bütçesi köşesi sıfıra çekildi), kalite otomatik proxy ile taklit edildi. Proje farkında olmadan **"yüksek kapsam + sahte kalite + sıfır doğrulama"** köşesine itildi — tercih değil, matematik.

## 5. Adversarial dürüstlük (teşhis kendi phantom-filtresinden geçti)

Karşı-teşhis ajanı kanıt-gücü sıralaması:
1. **Golden eval-set / kalite-tanımı yokluğu** — EN DERİN (proxy'nin generatorü)
2. **Premature scaling** (temiz çekirdek yok) — Maslow-tersine'yi açıklar
3. İlk analizin proxy/dairesel tezi — MEKANİZMA (orta derinlik)
4. Vanity-metric kültürü (🟢 EXCEEDED) — pekiştirici
5. "0 insan GT / yanlış katman / Maslow-tersine" — SEMPTOM

Uyarılar: (a) İlk analizin en keskin kanıtı (Tier H görsel→`false&&` boşa-emek) **leak premise spot-check'siz** — kendi CLAUDE.md kuralından muaf değil. (b) Kaynak-yetersizlik %15.7 sadece 25-kitap örneklemi, evren doğrulanmadı. (c) Bu teşhisin doğrulaması = düzeltici sıralamayı UYGULAYIP gerçek-sinyalle test etmek.

---

## Düzeltici İlke — SIRALAMA İNVERSİYONU

**"Mükemmelleştir-sonra-launch" → "minimal-okunabilir-çekirdek → kontrollü-beta → gerçekle-kalibre-et".**

1. **Pre-beta'da SADECE okunabilirlik (bounded, sonsuz cila DEĞİL):** launch-eşiği alt-kümesini (~10.5K veya daha küçük temiz çekirdek) öğrenci-okunabilir + **kör-bağımsız-çözüm-doğrulanmış** yap (brainstorm Faz 0-2: best_text + blind-solve gate). Bu KÜÇÜK, sınırlı bir iş — 167K'yı mükemmelleştirmek DEĞİL.
2. **Kontrollü beta aç:** gold pool zaten "launch-eşiği" kalitede (mükemmel değil, başlamak için yeterli). Küçük gerçek kullanıcı grubu.
3. **Gerçeklik kalibre etsin:** ilk ~30 yanıt/soru → gerçek IRT kalibrasyon; yanlış-anahtar sinyali (öğrenciler mis-keyed soruda sistematik "doğruyu seçtim yanlış sayıldı"); gerçek retention. **Tek yapısal kilit açıcı bu.**
4. **Proxy-chasing'i durdur:** yakınsama kriteri döngünün dışında — daha fazla audit/cila onu içeri getirmez, beta getirir.

**Reframe (önemli):** 198 session "yanlış iş" değildi — **doğru iş, yanlış sırada ve gerçek yerine proxy'ye karşı ölçülerek** yapıldı. Eksik olan emek değil, gerçeklik-teması.

---

*İlişkili: `2026-05-30_kalite_kok_neden.md` (mekanizma katmanı), `2026-05-30_yks_quality_95_roadmap.md`, `docs/brainstorms/2026-05-30_gorsel_metin_cozum.md` (Faz 0-2 = pre-beta okunabilirlik). Sonraki: düzeltici sıralamanın 1. adımı (minimal okunabilir çekirdek) + leak premise Faz-0 doğrulaması.*
