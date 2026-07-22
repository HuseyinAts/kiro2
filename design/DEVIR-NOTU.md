# KIRO2 — Devir Notu: Tek Kaynak Veri Bağlama Katmanı (Şafak Kanonu) — TAM DURUM

> Yeni sohbete yapıştır. Amaç: sonraki oturumun bağlamı, yapılan her şeyi ve bundan sonra ne yapacağını anlaması.

## 0) Proje özeti (değişmez bağlam)
KIRO2 = Türkiye YKS (TYT/AYT) hazırlığı EdTech ürününün frontend prototipi, tamamen Türkçe. Kullanıcı: 17-19 yaş sınav öğrencisi. Persona: **Hüseyin Ateş, 12. Sınıf Sayısal.** Öğrenme bilimi: CAT/IRT adaptif zorluk, FSRS aralıklı tekrar, BKT, harmanlama, getirim pratiği, Sokratik AI + kaygı-duyarlı insani oyunlaştırma. Her ekran bir Design Component (`Ad.dc.html`). Kalıcı ilkeler → `CLAUDE.md`; tasarım kanonu → `KIRO Safak Mimari.dc.html`.

**IŞIK/KOYU KURALI (KRİTİK):** Çalışma/odak/analitik ekranlar **AÇIK** (sıcak kâğıt `#F7F4EF` / mürekkep `#2A2433` / kart `#FFFFFF` / kenar `#ECE6DD`). Duygusal/hub/kutlama/battle ekranlar **KOYU** (`#110C18` / şafak göğü / boss arena). İndigo **YASAK**. Emoji yok (bespoke SVG). Risk = amber, alarm-kırmızısı yok. Mor/menekşe (Fizik) kanon gereği korunur — indigo değil.

## 1) Tek kaynak veri modülü — `kiro-data.js`
Projedeki tüm "gerçek" içeriğin tek kaynağı. ES module export'ları:

- **persona** — Hüseyin: seri 12 (rekor 21), xp 2450, seviye 7, bas `HA`, sinif `12. Sınıf · Sayısal`, hedefBolum `Bilgisayar Mühendisliği`, hedefUni `ODTÜ / Bilkent`, hedefSiralama 15000, guncelSiralama 27400, yksTarihi 2027-06-20.
- **subjects / subjectMap** — 5 Sayısal ders. key/ad/renk/glow/tur/hakimiyet/theta/bkt. Hâkimiyet: Mat 78, Fiz 64, Kim 52, Biy 71, Tür 83. (renk = **KOYU-ekran** parlak tonları: Mat `#5B8DEF`, Fiz `#A77BFF`, Kim `#E25A72`, Biy `#2DD4A7`, Tür `#FFB347`.)
- **topics** — 18 konu düzeyi hâkimiyet + durum (zayif/gelisiyor/iyi/guclu). Zayıflar: Türev 48, Gazlar 46, Elektrik 50, Kimyasal Tepkimeler 50.
- **questionBank** — 18 tam YKS sorusu: soru + secenekler + dogru(index) + cozum[adımlar] + neden + IRT b/a + sure. 5 dersi kapsar.
- **flashcards** — FSRS getirim kartları (front/back).
- **catBankMat** — CAT/IRT + hızlı-oyun havuzu (TYT Mat, geniş b yayılımı). Çoğu 4 şıklı; Diziler 5 şıklı.
- **reviewQueue** — bugün bekleyen FSRS tekrarları. `dueIn:0` olanlar (3 konu): Türev, Limit ve Süreklilik, Kimyasal Tepkimeler; +Elektrik(dueIn1), Genetik(dueIn2). Her biri kart sayısı taşır.
- **lastExam** — `KIRO Genel Deneme #7` (2026-06-29, TYT+AYT Sayısal). Getter'lı **tytNet=83,0 / aytNet=37,25 / toplam=120,25 / doğru oranı %66 / tahminiSiralama 27400**. TYT ve AYT ders ders soru/dogru/yanlis/bos/net.
- **engine** — Qwen3-8B, 77.000+ soru, CAT/IRT+FSRS+BKT, 4 rol.
- Yardımcılar: `masteryTier(pct)` (0-40 Tanıdık / 40-65 Yetkin / 65-85 Usta / 85-100 Fethedildi), `irtProb(θ,a,b)`, `seciliSet`, `konularByDers`, `trNum`.

## 2) Bağlama deseni (§2) — yeni ekran bağlarken AYNEN uygula
Veri **SENKRON** `window.__KIRO`'dan gelir (`kiro-seed.js` — <head>'de klasik script, support.js'ten ÖNCE çalışır → ilk render'dan önce hazırdır). Böylece **K-null fallback literal'lerine GEREK YOK**; fallback = tek satır guard. DC template'inde import yasak; recovery için (seed 404) logic'te dinamik import:

```js
class Component extends DCLogic {
  state = { K: null };                         // varsa mevcut state'e K: null EKLE
  async componentDidMount() {                  // yalnız RECOVERY: seed yoksa async yükle
    if (!this.state.K) { try { const K = await import('./kiro-data.js'); this.setState({ K }); } catch (e) { console.error('KIRO2 veri yüklenemedi:', e); } }
  }
  renderVals() {
    const K = this.state.K || window.__KIRO;   // SENKRON: seed ilk render'da hazır
    if (!K) return {};                         // seed yoksa boş (recovery devreye girer)
    // ...K'yı DOĞRUDAN kullan — INLINE FALLBACK LİTERALİ YAZMA...
    return { /* ...hepsi... */ };
  }
}
```

**KRİTİK — kiro-seed.js (tek kaynak, OTOMATİK ÜRETİLİR — fallback borcu §22b'de sıfırlandı):**
- `kiro-seed.js` = `kiro-data.js`'in senkron ikizi (`export`→global; `window.__KIRO`, getter'lar + fonksiyonlar dahil). Her veri-ekranının <head>'inde `<script src="./kiro-seed.js">` support.js'ten ÖNCE.
- **kiro-data.js DEĞİŞTİĞİNDE kiro-seed.js'i YENİDEN ÜRET** (run_script: kiro-data oku → `export ` sil → IIFE'ye sar → `window.__KIRO = {…}`). Tek eşitleme noktası; artık inline-literal drift'i YOK.
- Yeni ekran: (1) <head>'e seed script'i ekle, (2) `const K = this.state.K || window.__KIRO; if (!K) return {};`, (3) K'yı doğrudan kullan — literal fallback YAZMA. (İstisna: motor/loading iskeleti — FSRS '…', Öğrenme Yolu DATA, Boss teması — bilinçli authored skeleton olarak korunur; sadece K'yı senkron yap.)
- Türkçe sayı: `.toLocaleString('tr-TR')` ya da net için `fmtNet(n)` deseni:
  ```js
  fmtNet(n){ const r=Math.round(n*100)/100;
    const s=(Number.isInteger(r)||Math.round(r*10)/10===r)?r.toFixed(1):r.toFixed(2);
    return s.replace('.', ','); }   // 33→"33,0", 14.25→"14,25", 120.25→"120,25"
  ```
- **AÇIK panellerde ders rengi:** kiro-data.renk KOYU-ekran için parlak. Açık panelde daha koyu "panel paleti" kullan (color sabit — veri değil):
  `panelColor = { mat:'#3B82F6', fiz:'#8B5CF6', kim:'#E0593F', biy:'#1FB683', tur:'#F59E0B' }`
  KOYU ekranlarda (Şafak/Boss/Düello) doğrudan `s.renk`/`s.glow` kullan.
- Per-item değişen CSS string'ini style hole ile geçir (mevcut desen): `style="{{ s.tagStyle }}"`. Statik/tema değeri için style hole **KULLANMA** (paint'i geciktirir).
- **Motor mantığına DOKUNMA** — sadece veri kaynağını dışarı al (Adaptif Test / Düello deseni).

## 3) Bu oturumlarda bağlanan ekranlar (hepsi §2 + K-null fallback)
**Önceki oturum (devralındı):** Soru Çözme, FSRS Tekrar, Öğrenci Paneli, Adaptif Test (CAT motoru korundu, veri catBankMat'ten). Mastery Rozet badge-yükseklik hatası düzeltildi.

**Bu oturumlarda tamamlanan (§6'nın TAMAMI):**
- **KIRO Safak (Bugün, KOYU korundu)** — dersler `K.subjects` (5 Sayısal), seri persona, tekrar kartı reviewQueue(dueIn0 sayısı + ilk konu). Ruh-hâli/mantra authored (etkileşim, veri değil).
- **KIRO2 Sinav Sonuc** — TAM lastExam: 8 satır TYT+AYT ders-ders net dökümü (TYT/AYT etiketli), doğru oranı %66, TYT net 83,0 / toplam 120,25, sıralama 27.400, D131·Y43·B26; zayıf konular topics'ten; AI en güçlü/zayıf ders subjects'ten.
- **KIRO2 Ogrenme Yolu** — üst çubuk persona(seri/xp/seviye), hâkimiyet halkası + "sıradaki adım" = o dersin EN ZAYIF topics konusu (rozet o konunun hâkimiyeti). Curriculum journey + boss kontrol noktaları AUTHORED (kiro-data'da ünite granülerliği yok — bilinçli korundu).
- **KIRO2 Neden Geri Bildirim** — soru+5 şık+doğru/seçilen questionBank'ten (mat-turev-2, çarpım kuralı); "Neden?" = neden + numaralı cozum adımları; kavram rozeti topics'ten (Türev 48); üst çubuk seri/XP persona (24→12, 3.480→2.450 düzeltildi).
- **KIRO2 Sokratik AI** — üzerinde çalışılan soru catBankMat(Diziler), seri/XP persona. Sokratik diyalog senaryosu (SOC/DIR) AUTHORED (öğretim içeriği) — korundu.
- **KIRO2 Veli Paneli** — kimlik/hedef/seri persona (**"Hedef: Tıp" → "Bilgisayar Müh." DÜZELTİLDİ**), ders özeti subjects, Son Sınavlar + "Son deneme neti" lastExam (deneme %66/120,3; Mat AYT 17,0/%50; Türkçe TYT 33,0/%85), Kimya uyarısı subjectMap; haftalık saat grafikle tutarlı (6,5).
- **KIRO2 Ogretmen Paneli** — takip edilen öğrenci Hüseyin Ateş sınıf listesine gerçek verisiyle eklendi (TYT net 83,0 · hâkimiyet %70 = subjects ort.). Sınıf arkadaşları/ortalama/konu hâkimiyeti/dikkat listesi sınıf-düzeyi olduğu için AUTHORED.
- **KIRO2 Harmanlanmis Deneme** — oturum bileşimi + soru sırası reviewQueue'dan (Türev/Limit/Kimyasal Tepkimeler/Elektrik), durum etiketleri topics'ten; soru/konu/süre bileşimden türetildi.
- **KIRO2 Lig** — Hüseyin satırı + üst çubuk persona (**seviye 12→7 DÜZELTİLDİ**; XP 2.450 zaten tutarlıydı). NPC rakipler authored.
- **KIRO2 Duello** — düellocu kimliği persona (Seviye 7; **meLvl fallback 12→7 flaş düzeltildi; rakip Mert K. sabit 'Seviye 13' → `oppLvl = meLvl` eşleşmeli adil 1v1**), soru havuzu catBankMat (kolay 4-şıklı set, b≤0.6). Gerçek-zamanlı süre/skor/rakip motoru DOKUNULMADI.

**Devir turu — bu oturumda bağlanan (§6 aday listesi + inceleme grubu):**
- **KIRO2 Onboarding** — yerleştirme soruları artık `catBankMat`'ten (Adaptif Test'le aynı TYT-Mat placement ladder: İşlem Önceliği→Denklem→Üslü→Yüzde→Logaritma→İkinci Derece, kolay→zor); payoff "odak konu" = gerçek en zayıf mat konusu (Türev). Adaptif akış motoru DOKUNULMADI, sadece soru kaynağı `componentDidMount`'ta dışarı alındı.
- **KIRO2 Mola (KOYU korundu)** — "2 sa 15 dk" → `persona.bugunCozulenDk` (**30 dk**, Şafak ile tutarlı; `fmtDk` helper). Nefes/mantra/ruh-hâli authored kaldı (ışık kuralı: KOYU dinlenme ekranı).
- **KIRO2 Seri Dondurma** — hero seri **24→12** (persona.seri), en uzun **31→21** (persona.seriRekor), CTA **25→13** (seri+1); kilometre taşları seri/seriRekor'dan türetildi (7 · 12 şu an · 21 rekor · 30 hedef; "kaldı" = target−seri). Agresif nudge anti-örneğindeki **24 → seri** (12) bağlandı. Hafta grid + dondurma hakkı (2) authored.
- **KIRO2 Arkadas Serisi (AÇIK panel)** — ortak-seri kartı avatar `persona.bas` + seri `persona.seri` (12; ortak seri = min(sen,Elif) mantığıyla tutarlı). NPC arkadaşlar / co-op görev / sıralama §5 gereği authored.
- **KIRO2 AI Sohbet (AÇIK asistan)** — karşılama adı `persona.adKisa`; "zayıf konuların" paneli = gerçek en zayıf 3 mat konusu (Türev 48 · Limit 55 · İntegral 62, `topics`'ten asc), eski uydurma Çarpanlara/Köklü/Oran **KALDIRILDI**. reply()+_topicOf()'a Limit & İntegral dalları eklendi — İntegral eşleşmesi Türkçe-İ `toLowerCase` tuzağı için `'ntegral'` ile yapıldı.
- **KIRO Cozum Paylas (AÇIK)** — paylaşan kimliği `persona.bas` + `persona.ad`'dan türetildi ("Hüseyin A." = ad + soyad-baş-harfi). Akran/öğretmen tartışması (NPC) authored.
- **KIRO Calisma Modlari (AÇIK)** — havuz rozeti `Yetkin %47` → Türev gerçek mastery **%48** (`masteryTier(48).label`). Havuz kart sayısı **24 → gerçek** (`reviewQueue` Türev `kart:6`); mod sayıları `poolCards`'tan türetildi (6 kart · 6 soru · 3 çift · 60 sn). Havuz adı + '60 sn' hız kutusu authored.

## 4) Bilinçli dokunulmayanlar (motor/sandbox — kendi ayarlı içeriği korunur)
- **KIRO2 Adaptif Test** — CAT/IRT motoru (θ kestirimi, SE yakınsama, madde seçimi). Veri catBankMat'ten; motor mantığı korunur.
- **KIRO2 Interaktif Cozum** — canlı parabol sandbox'ı (y=ax²+bx+c slider). Persona/soru verisi yüzeyi yok; bir motor gibi bırakıldı.
- **KIRO2 Boss Savasi** — savaş motoru + KOYU kutlama zemini (kanon-doğru). Zaten Hüseyin'in en zayıf konusu Türev temalı. 4-şıklı hızlı combat bankası, questionBank'in 5-şıklı Türev sorularına uymadığı için korundu.
- **KIRO Ilk Hafta** — ilk-hafta momentum kurgu ekranı (3/7 gün, gün-0→7 yay). Kavramsal olarak **pre-persona**; persona.seri=12 ile çelişir → bilinçli authored (Onboarding first-week planı gibi). "30 dk Türev" / "İlk Yetkin rozeti" zaten gerçek konu/eşikle hizalı.
- **KIRO Bilgi Atomlari** — konu-altı "atom" granülerliği (Türev → Zincir kuralı → İç-fonksiyon türevi; atomlar 84/38/71/66). `topics` konu düzeyinde durur, atom düzeyi yok → bilinçli authored. Mastery Rozet `dc-import` zaten kullanıyor.

## 5) Önemli tutarlılık kararları (gerekçeleriyle)
- Hüseyin'in seviyesi HER YERDE **7** (persona.seviye). Lig/Düello'daki eski 12/13 → 7'ye çekildi. (Düello'da kalan meLvl **fallback=12** ve rakip **Seviye 13** bu turda düzeltildi → fallback 7, rakip `oppLvl=meLvl` eşleşmeli.) XP her yerde **2.450**. Seri **12**.
- Hedef = **Bilgisayar Mühendisliği** (persona) — Veli'deki yanlış "Tıp" düzeltildi.
- lastExam tek deneme: toplam net **120,25**, **%66**. Panel/Veli/Sınav Sonuç hepsi bununla tutarlı.
- "47 tuğla" (Şafak hero) ve mola/mantra/ruh-hâli gibi ŞİİRSEL/etkileşimli metinler veri değil — bilinçli authored bırakıldı (uydurma binding = data slop'tan kaçınıldı).
- Curriculum ünite yapıları (Öğrenme Yolu), NPC'ler (Lig/Öğretmen/Düello rakibi), sınıf aggregate'leri kiro-data'da olmadığı için authored — bunları modüle zorlamak tasarımı bozardı.
- **Devir turu düzeltmeleri:** Mola "2sa15dk"→30 dk (bugunCozulenDk); Seri Dondurma 24→12 / 31→21 / 25→13; Çalışma Modları %47→%48 (Türev) + **havuz kart sayısı 24→gerçek** (reviewQueue Türev kart:6 → 6 kart/6 soru/3 çift/60 sn); AI Sohbet uydurma zayıf-konular → gerçek Türev/Limit/İntegral.
- **Onboarding & İlk Hafta = kavramsal "gün 0" akışı:** persona geçmişi (seri 12) zorlanmadı — yerleştirme/first-week kurgusu korundu. Onboarding'de yalnız soru kaynağı (catBankMat) + payoff odak-konu bağlandı; İlk Hafta tamamen authored bırakıldı.

## 6) Sırada ne var
**§6 aday listesinin TAMAMI tamamlandı** (devir turu): Onboarding, Mola, Seri Dondurma, Arkadas Serisi, AI Sohbet, Cozum Paylas, Calisma Modlari bağlandı; Ilk Hafta + Bilgi Atomlari gözden geçirildi → veri yüzeyi olmadığı (pre-persona kurgu / atom-altı granülerlik) için bilinçli authored (§4).

**Single-source'a bağlanacak ekran KALMADI.** Kalan işler yalnız isteğe bağlı:
- Mobil incelik / responsive cila — **BAŞLANDI (§9):** Şafak + Soru Çözme + Öğrenci Paneli mobil pass yapıldı. Kalan sidebar ekranları aynı sistemle sürdürülebilir.
- Gerçek API entegrasyonu (`kiro-data.js` → backend).
- kiro-data granülerliğini artırma (atom/ünite düzeyi) — İSTENİRSE İlk Hafta / Bilgi Atomları / Öğrenme Yolu curriculum'u da veri-güdümlü hale gelebilir.
- Kullanıcı testi.
- Ürün genişletme — yeni ekranlar (Ayarlar / Bildirim Merkezi / Kutlama) + motion + çekirdek-döngü bağlantısı: **BAŞLANDI, bkz. §10.**

**DOKUNMA:** KIRO Safak Mimari (kanon), KIRO Safak Renk (renk kanonu), `Kenar*` (paylaşılan nav), Birlesik Motor / OS Ogrenme Motoru (motor dokümanları), `*Arastirma/*Analiz/*Rapor/*Promptu` (doküman DC'leri — veri binding gerektirmez).

## 7) Çalışma kuralları (değişmez)
Türkçe arayüz+kopya. Şafak kanonu (`CLAUDE.md` + `KIRO Safak Mimari`). Çalışma=**AÇIK**, duygusal/kutlama=**KOYU**. İndigo YASAK; emoji yok (bespoke SVG); risk=amber. Motorlara dokunmadan reskin/veri-bağlama. Mastery rozeti `dc-import` ile. Yeni ekran bağlarken §2 desenini + K-null fallback (gerçek değerlerle) uygula. Küçük değişiklikte sadece isteneni değiştir. Değişiklikleri `dc_write` / `dc_html_str_replace` / `dc_js_str_replace` ile yap.

## 8) Durum
Çekirdek döngü + panel/rol + oyunlaştırma + onboarding/mola/sosyal/asistan + inceleme grubu — **20+ ekran** tek kaynağa bağlı; tek tutarlı Hüseyin hikâyesi öğrenci/veli/öğretmen/asistan görünümlerinde geçerli. Konsol temiz, tüm ekranlar hatasız yükleniyor. Motorlar (Adaptif Test / İnteraktif / Boss) + kavram/kurgu ekranları (İlk Hafta / Bilgi Atomları) tasarım gereği kendi içeriğini koruyor.

## 9) Mobil / responsive pass (Şafak sistemi)
**Sistem:** telefon katmanı `@media (max-width:480px)` (+ mevcut 760/800/820 kolon-çökertme). Gutter → 18px; dev başlıklar 38→~30px; body ≥13px. Sidebar ekranlarda nav rail 64px ikon-only (KIRO Kenar kendi container-query'siyle çöküyor — DOKUNMA). Hit target ≥44px. **390px'te overflowX=0 şart.** Renk/tema/veri binding'e dokunma; tüm kurallar media-query içinde → masaüstü değişmez.
**Yöntem (önemli):** html-to-image iframe içini yakalayamaz → `Mobil Önizleme.html` (390px iframe harness) + programatik prob: `eval_js` ile iframe'e gir, `overflowX` ölç, `getBoundingClientRect().right > innerWidth` olan **breakout eleman**ı bul, computed style doğrula. Kanıt böyle toplanır (screenshot değil).
**Yapıldı:** Şafak (KOYU; `.rpad` gutter 18px + hero h1 `.rh1` 30px), Soru Çözme (`.rbody` dikey stack + `.rnavq` navigatör tam-genişlik altta + `.rhead`/`.rqcard` padding; önceden hiç MQ yoktu), Öğrenci Paneli (hero CTA'ları `.rherobtns` dikey stack; θ badge + Mastery Rozet telefonda gizli `.rsec`; KPI 1-col mevcut 440'tan). Üçü de overflowX=0, konsol temiz.
**Sırada:** overflow açısından ekran KALMADI — **21/21 uygulama ekranı 390px'te overflowX=0** (tam-uygulama iframe prob'uyla doğrulandı). Bu turda düzeltilenler: rol panelleri (Veli/Öğretmen/Sınav Sonuç → `.rkpi4` KPI 2/1-col, `.rtwo` alt bölüm 1-col, `.rhead` başlık wrap), Adaptif Test (`.rbody`/`.rnavq` yan-panel stack), Sokratik AI + Neden (üst bar wrap + sağ ray ≤760 gizli `.rhiderail`), Öğrenme Yolu (üst bar wrap), Düello (VS bandı avatar 48/`.rvsdots` + güç satırı wrap), Boss (durum çubuğu wrap). Zaten temizdi: Lig, Seri Dondurma, Arkadaş Serisi, Harmanlanmış Deneme, FSRS Tekrar, AI Sohbet, Çalışma Modları, İnteraktif Çözüm, Çözüm Paylaş, İlk Hafta, Bilgi Atomları, Mola. Opsiyonel kalan: gerçek-cihaz testi.

**9b — Dikey yoğunluk + tipografi + tablo (≤480, bu tur):** 4 panel main'ine `.rdense` → ana blok gap'i (22/20/18)→16, `.rtwo`/`.rstack` kolon gap'leri→16; KPI **30px sayıları→26px**. Veli/Öğretmen/Sınav main'lerine ayrıca `.rpadx` eklendi (mobil yatay gutter 30/26→16). **Öğretmen öğrenci-tablosu telefonda 4→3 kolon** (`.rstud` = 1.7/0.8/1.4fr; 'Son aktivite' kolonu `.rstudhide` ile gizli). Hepsi overflowX=0.
⚠️ **GOTCHA:** DC runtime React inline stillerini `font-size: 30px` (colon+BOŞLUK) diye yeniden serialize eder → attribute seçici `[style*='font-size: 30px']` (BOŞLUKLU) olmalı; boşluksuz eşleşmez. Statik değer eşleşmesi gereken her `[style*=...]` seçicide bunu hatırla.

**9c — Dokunma hedefi (tap-target) denetimi (bu tur):** 21 ekran 390px'te tarandı; tek sistemik sorun daralmış nav rayıydı (28-35×36, <44). `KIRO Kenar*` DOKUNMA olsa da mobil kullanılabilirlik için container-query'ye (`@container max-width:150px`) **`.ni{min-height:44px}`** + ana Kenar'da **`.kn` yatay padding 14→8** eklendi → öğrenci rayı **40×44**, Veli/Öğretmen **35×44**. Bilinçli/minimal/yalnız daralmış durumda; masaüstü + geniş nav DEĞİŞMEDİ. Kalan <44 kontroller (38-40px ikon butonları; 'Tümü/Yolu gör/Atla' metin linkleri) tasarım gereği kabul edilebilir bırakıldı (metin linkini 44px yapmak yanlış olurdu).

## 10) Ürün genişletme: yeni ekranlar + motion (bu tur)
**Yeni ekranlar** (§2 + K-null fallback + baştan mobil-hazır `.rnav/.rpadx/.rhead/.rtwo/.rdense` sınıfları; hepsi overflowX=0):
- **KIRO2 Ayarlar** (AÇIK, sidebar) — profil (persona), hedef kartı + YKS geri sayım (`yksTarihi` gün farkı, fallback 353), günlük-hedef stepper (`gunlukHedefDk` ±15), çalışan bildirim toggle'ları (state), tema segmenti (authored "çalışma hep aydınlık" notu = ışık/koyu kanonu), vurgu-rengi seçici (state.accent → nav'a canlı geçer). Prop `accent` (color tweak).
- **KIRO2 Bildirim Merkezi** (AÇIK, sidebar) — bildirimler gerçek veriden: reviewQueue dueIn0 (N konu·~dk), lastExam (ad/net `_fmtNet`/oran/sıralama), persona (seri/rekorKalan), topics (Türev zayıf); akran/rozet NPC authored. Okundu-state + "tümünü okundu" + **Temizle → boş-durum** ("Her şey sakin · sıfır bildirim", `isEmpty`/`hasGroups`).
- **KIRO2 Kutlama** (KOYU — kutlama kanonu) — şafak konfeti + parıltı/pulse motion, 4 tür tür-değiştiriciyle: günlük (`bugunCozulenDk`) · seviye (`seviye`/`xp`) · seri (`seri`/rekorKalan) · boss (en zayıf mat konu = Türev). Prop `celebration` + **URL `?type=`** deep-link (`_urlType` = URLSearchParams class-field → ilk render'da hazır). CTA → Şafak.

**Giriş noktaları:** Öğrenci Paneli üst çubuğu → dişli `KIRO2 Ayarlar`, çan `KIRO2 Bildirim Merkezi`. FSRS Tekrar "Bugünün tekrarı tamam" → **"Günü kutla"** birincil CTA = `KIRO2 Kutlama.dc.html?type=gunluk`. **Boss zaferi → Kutlama BAĞLANDI:** Boss Savaşı win overlay'ine `won`-koşullu `sc-if` içinde **"Zaferi kutla"** altın birincil CTA = `KIRO2 Kutlama.dc.html?type=boss` (yıldız ikon, gold gradient dark-ink). Win'de "Yeniden savaş" ikincile indirildi (`retryBg/retryFg/retryBorder` won-koşullu subtle outline); lose'da crimson birincil kaldı. `?type=boss` Kutlama'da `_urlType` ile çözülüyor. **Kutlama giriş durumu — 4/4 BAĞLI:** `gunluk`←FSRS ✓ · `boss`←Boss Savaşı ✓ · **`seviye`←Lig ✓** · **`seri`←Seri Dondurma ✓**. **seviye:** `kiro-data.js`'e `seviyeEsik` + `seviyeBilgi(xp)` eklendi (kümülatif XP eşikleri; 2450→sev 7, sev 8 eşiği 2680). Lig'de "XP kazan" simülasyonu meRow.xp'yi canlı seviyeye çeviriyor (`meRow.lvl`=liveLevel → üst bar + ranking canlı); eşik aşılınca (`leveledUp`) altın level-up kartı + "Seviyeyi kutla" → `Kutlama.dc.html?type=seviye&xp={meXp}`; aşılmadan sonraki-seviye ilerleme çubuğu (`notLeveled`, fallback %61,7 · 230 XP). ~3 tık level 8. **seri:** Seri Dondurma hero'suna kontekstüel "Seriyi kutla" → `?type=seri&seri={seri}` (mevcut streak'i kutlar — yeni-milestone event'i yok, hero'daki gerçek başarıya bağlı). **Kutlama** `?xp=`/`?seri=` okuyor (`_urlXp`/`_urlSeri` class-field); seviye kartı `seviyeBilgi(urlXp)` ile canlı seviye+XP, seri kartı geçirilen streak. **Yan düzeltme:** Lig me-satırı `lvl` fallback'i `12→7` (§5; üst bar düzeltilmişti, ranking satırı fallback'i atlanmıştı → K yüklenene dek "Seviye 12" flaşı vardı, giderildi).

⚠️ **GOTCHA-1 (KRİTİK):** `dc_write`'ta `<helmet>` bloğunun **`</helmet>` kapanışı ŞART**. Atlarsan içerik `<div>`'i açık helmet'e yutulur → `#dc-root` boş, tamamen boş render (konsol TEMİZ, sinsi). Yeni DC'de ilk kontrol bu.
⚠️ **GOTCHA-2 (motion/capture):** Giriş animasyonunu **opacity:0→1 YAPMA** — html-to-image (doğrulayıcı + PPTX export) animasyonu 0% frame'de yakalar → içerik BOŞ görünür (gerçek tarayıcıda sorunsuz). Çözüm: keyframe **transform-only** (translateY/scale), base opacity:1 kalsın (Kutlama `cup`/`cpop` böyle). Sürekli-döngü dekoratif (konfeti/pulse) sorun değil.

## 11) Canlı Demo — tıklanabilir uçtan-uca tur (bu tur)
**`KIRO2 Canli Demo.dc.html`** (AÇIK konsol) — paydaş demosu için rehberli lineer tur. Sol ajanda 8 sahne (her sahnede aydınlık/koyu ritmi etiketli), sağ sahne gerçek ekranı gösterir — **varsayılan statik yüksek-çözünürlük görüntü** (`screenshots/flow/<slug>.png`, faux-browser strip'li çerçeve) + **"Canlı etkileşim"** düğmesiyle üzerine binen `<iframe>` (gerçek tıklanabilir ekran; sahne değişince statik'e döner); alt kontrol Geri/Sonraki + **klavye ← →**, üst-sağ "Yeni sekmede aç", sol-altta ilerleme çubuğu (`01/08`). Sahne sırası (grounded narration = authored, §5): Bugün(`KIRO Safak`) → Soru Çözme → Neden Geri Bildirim → FSRS Tekrar → Kutlama(`?type=gunluk`) → Lig → Boss Savaşı → Öğrenci Paneli. **Hiçbir ekran dosyasına dokunulmadı** — ekranlar iframe'de olduğu gibi, tam etkileşimli kullanılır. Tweak prop'ları: `accent` (coral/teal/gold — indigo/mor yok), `autoplay` + `dwell` (kiosk için otomatik ilerleme; 500ms tick + elapsed akümülatörü, canlı dwell değişimine saygılı). **Giriş noktası:** `KIRO2 Tasarim Sistemi` başında koyu "Canlı Demo · Paydaş Turu" banner'ı → `KIRO2 Canli Demo.dc.html`.
⚠️ **NOT-1:** Dosya adı ASCII ("Canli", Türkçe "ı" değil) — proje dosya-adı kuralı (Cozme/Ogrenci gibi). href/iframe src'de boşluk sorunsuz.
⚠️ **NOT-2 (ÇÖZÜLDÜ):** html-to-image `<iframe>` içeriğini yakalayamaz (capture'da boş beyaz kutu; iframe'i `background:transparent` yapmak da işe yaramaz — html-to-image iframe kutusunu beyaz çizip arkadaki katmanı örter). Ayrıca `dc-import` inline gömme de elenir: runtime'da `dc-import name` **derleme-anında bir kez** okunur (dinamik `{{ }}` değil) ve çocuk DC helmet `body{}` kuralları global sızar (koyu ekranlar konsolu karartır). Çözüm: **varsayılan görünüm gerçek ekranların statik `<img>` görüntüsü** (html-to-image `<img>`'i yakalar) → capture/PDF/PPTX artık gerçek ekranı gösterir; canlı etkileşim `goLive`/`goStatic` state'iyle isteğe bağlı iframe. Görüntüler `screenshots/flow/*.png` — her ekran `show_html`+`save_screenshot` (hq PNG) ile kendisinden üretildi; **ekran tasarımı değişirse o görüntüyü yeniden üret.**

## 12) Paydaş sunumu — slayt destesi (bu tur)
**`KIRO2 Sunum.dc.html`** — 11 slayt, `deck-stage.js` (`x-import component-from-global-scope="deck-stage"`, 1920×1080). Şafak kanonu: kapak (01) + kapanış (11) KOYU şafak göğü gradyan; 8 sahne slaytı (03-10) AÇIK kâğıt. Her sahne slaytı = **gerçek ekran görüntüsü** (faux-browser çerçeve, `screenshots/flow/<slug>.png`) solda + sağda kicker (moment: SABAH/İLK SORU…) · serif başlık (özellik adı) · anlatım · pedagoji çıkarımı (CAT/IRT · FSRS · BKT · kaygı-duyarlı…). Slayt 02 = 8-sahne şerit genel bakışı + aydınlık/koyu ritim göstergesi. **Statik markup** (deck skill: doğrudan düzenlenebilir, loop yok); logic yok. Tip ölçeği helmet `:root --type-*` (≥19px, projeksiyon uyumlu). Görseller §11'deki `screenshots/flow/*.png` ile paylaşılır — **ekran değişirse yeniden üret.**
**Çıkış yolları:** PDF → `open_for_print` (deck-stage tek-sayfa-per-slayt basar) veya "Save as PDF" skill. PPTX → `gen_pptx` (width 1920, height 1080, `resetTransformSelector:"deck-stage"`; editable veya screenshots modu). Kanon: emoji yok, indigo yok, takeaway-box/accent-border yok.

## 13) Curriculum veri katmanı — data-driven (bu tur)
`kiro-data.js`'e eklendi (default export'a dahil): **`curriculum`** (5 ders → ünite → konu ağacı; her ünite `{no, ad, durum: done/current/open/locked, progress "2/4", konular:[{ad,durum}]}`, ders başına `est · done · total · next{q,min}`) + **`atomKirilim`** (konu→kavram→atomlar; şu an `mat/Türev/Zincir kuralı` 84·38·71·66) + **`enZayifAtom(kirilim)`** helper (min hâkimiyet).
**Bağlanan 3 ekran** (§2 deseni + K-null fallback; inline authored içerik fallback olarak KORUNDU → stream flaşı yok):
- **Öğrenme Yolu**: inline `DATA` artık yalnız K-null fallback; K yüklenince `K.curriculum[key]` üniteleri sürer (barW `progress`'ten türetilir, `nextQ/nextMin` curriculum'dan). Ders switch de curriculum'dan (Fizik/Kimya/… doğrulandı). Overall hâkimiyet = `subjects.hakimiyet` (mevcut davranış), sıradaki adım = en zayıf `K.topics` konusu.
- **Bilgi Atomları**: atomlar + breadcrumb (konu/kavram/en-zayıf-atom) + kavram başlığı + insight + CTA hepsi `K.atomKirilim`'den; en zayıf atom `enZayifAtom` (İç-fonksiyon türevi %38). componentDidMount + K yüklemesi eklendi (önce yoktu).
- **İlk Hafta**: odak konu ("Türev" = en zayıf mat) + tier ("Yetkin" = `masteryTier(48)`) K'den bağlandı; **7-gün momentum yayı authored kaldı** (§4 — pre-persona kurgu, `persona.seri=12` ile çelişir, bilinçli).
Konsol temiz; Öğrenme Yolu 17 düğüm + ders-switch curriculum'dan, atom kırılımı + İlk Hafta bağları eval ile doğrulandı. §4/§6'daki "İlk Hafta / Bilgi Atomları authored" notu bu turda güncellendi (artık veri-güdümlü).

**Ek — atom katmanı genişletildi (bu tur):** `atomKirilim` 1→**4 zayıf konu** (Türev/Zincir kuralı · Gazlar/Gaz yasaları · Elektrik/Ohm yasası ve devreler · Kimyasal Tepkimeler/Denkleştirme & stokiyometri; her biri 4 atom, biri belirgin en zayıf). **Bilgi Atomları'na zayıf-konu chip seçici** eklendi (`state.sel`, default Türev, `pick()`); breadcrumb/kavram-başlığı/atomlar/insight/CTA hepsi seçili kırılımdan sürer, en zayıf atom `enZayifAtom` (min hâkimiyet) ile vurgulanır. İnsight suffix-güvenli ("Sorun {konu} değil"). Eval + görsel doğrulandı.

## 14) Sınava Geri Sayım ekranı (bu tur — §10 aday listesinden)
`KIRO2 Sinav Geri Sayim.dc.html` (**KOYU şafak** — duygusal/ritüel kanonu, çalışma değil; ışık/koyu kuralı). Metafor: **sınav = şafak**, kalan gün = "gündoğumu" (Şafak hero "tuğla" dilini sürdürür). Canlı gün farkı `persona.yksTarihi`'den (`Math.ceil((yksTarihi−Date.now())/86.4M)`, fallback 353). **Kaygı-duyarlı:** alarm/baskı yok; büyük sayı yönetilebilir parçalara bölünür (hafta ~51 · seri 12 · günde 45 dk cam çipler). Hedef kartı persona (Bilgisayar Müh · ODTÜ/Bilkent · ilk 15.000 · son deneme 27.400). Instrument Serif mantra + CTA → Soru Çözme. **Tweak prop:** `accent` (dawn coral/amber/pembe — indigo yok) · `birim` (gündoğumu/gün) · `mantra` (enum). §2 K-null fallback (persona ile birebir). **Giriş noktaları:** Şafak/Bugün üst-bar "Sınava sayım" cam chip + Tasarım Sistemi galerisi (Öğrenci grubu · 09). GOTCHA-2 uyumlu (giriş opacity animasyonu yok; yalnız dekoratif sun-glow/twinkle döngüsü).

## 15) Boss Savaşı → curriculum bağı (bu tur — §3 aday'dan)
`KIRO2 Boss Savasi.dc.html` **veri yüzeyi** bağlandı (savaş motoru §4 DOKUNULMADI): boss teması = **en zayıf mat konu** (`K.topics` → Türev); boss'un **"zayıf noktası" = o konunun en zayıf atomu** (`atomKirilim` + `enZayifAtom` → İç-fonksiyon türevi) yeni bir kırmızı rozetle arena'da gösteriliyor. Boss adı ("{konu} Ejderhası"), alt-başlık ("Konu Canavarı · {konu}") ve zafer metni konudan türetiliyor. `componentDidMount` + K yüklemesi + K-null fallback (Türev / İç-fonksiyon türevi) eklendi. **Korunanlar:** 4-şıklı combat bankası, HP/can/kombo/faz motoru, win→`Kutlama?type=boss` CTA. §4'teki "Boss authored" notu bu turda güncellendi (tema+zayıf-nokta artık veri-güdümlü; combat mekaniği hâlâ kendi ayarlı).

## 16) Haftalık Plan ekranı (Faz 2 · madde 4)
`KIRO2 Haftalik Plan.dc.html` (**AÇIK**, sidebar) — 7-günlük çalışma takvimi (Pzt–Paz, Pzt=bugün). Bloklar veriden türetilir: **çalışma** = en zayıf konular (`topics`, ders rengi açık-panel paletinden mat#3B82F6/fiz#8B5CF6/kim#E0593F/biy#1FB683/tur#F59E0B), **FSRS tekrar** = `reviewQueue` gün bazında (`dueIn`→gün: dueIn0 3 konu/15 kart→Pzt, dueIn1 Elektrik→Sal, dueIn2 Genetik→Çar), **deneme** = Harmanlanmış Deneme (hafta sonu), + analiz + mola. Günlük/haftalık dk toplamı türetilir (~6,8 sa), günlük hedef `persona.gunlukHedefDk`. Her blok ilgili ekrana link. **Tweak:** accent · `denemeGunu` (Cmt/Paz) · `molaGoster`. **Haftalık yerleşim authored** (kiro-data'da takvim yok — §5), içerik veri-güdümlü. K-null fallback (topics/reviewQueue birebir). **Giriş:** Kenar nav "Haftalık Plan" (Çalışma bölümü; enum'a `plan` + ids'e 'plan' eklendi) + Tasarım Sistemi galerisi (Öğrenci · 10).

## 17) Başarımlar / rozet galerisi (Faz 2 · madde 5)
`KIRO2 Basarimlar.dc.html` (**KOYU** — kutlama/tutundurma kanonu, oyun-başarım trophy room; earned parlar, locked soluk). Veri: **hâkimiyet tier rozetleri** = `masteryTier(subjects.hakimiyet)` (5 ders madalyonu, `subject.renk` halka + tier pill — Türkçe 83/Mat 78/Biy 71 Usta, Fiz 64/Kim 52 Yetkin); **seri kilometre taşları** = `persona.seriRekor` (7·14·21 açık, 30·50·100 kilitli), aktif progress = seri/rekor (rekora kalan gün). Hero: Seviye 7 + 2.450 XP + seri 12/rekor 21 + kazanılan rozet sayısı. Tier legend (Tanıdık/Yetkin/Usta/Fethedildi eşikleri). **Tweak:** accent · `siralama` (hakimiyet/ad) · `kilitliGoster`. K-null fallback (subjects/persona birebir). **Giriş:** Kenar nav "Başarımlar" (Yarışma&Seri; ids'e 'basarim') + Tasarım Sistemi (Oyunlaştırma · 18). GOTCHA-2 uyumlu (giriş opacity animasyonu yok).

## 18) Abonelik / paywall (Faz 2 · madde 6)
`KIRO2 Abonelik.dc.html` (**AÇIK** — güven/şeffaf fiyatlandırma; kaygı-duyarlı, FOMO/baskı yok). Aylık/Yıllık segment (state.billing; **yıllık ₺124/ay = ₺1.490 · −%38**, aylık ₺199). Ücretsiz vs Premium iki kart; Premium özellikleri ürün motorlarına dayalı (CAT/IRT · FSRS · BKT), `engine.bankSize` (77.000+) + `engine.motorlar` trust chip'leri. "**{denemeGunu} gün ücretsiz dene, istediğin zaman iptal**" çerçevesi. Fiyatlar authored (TL; kiro-data'da fiyat yok). **Tweak:** accent · `varsayilanFatura` (yillik/aylik) · `denemeGunu` (int 0-14). K-null fallback (engine birebir). **Giriş:** Ayarlar'da profil altı koyu "Premium" upsell kartı. ⚠️ CTA placeholder (gerçek ödeme akışı yok → şimdilik Kutlama'ya). Tasarım Sistemi galerisine bilinçli EKLENMEDİ (iş yüzeyi, ürün-ekran değil).

## 19) Ekranlar arası geçiş + micro-interaction (Faz 2 · madde 7)
Tüm **49 `.dc.html`** ekranın helmet `<style>`'ına ortak blok enjekte edildi (`* { box-sizing }` anchor'ı sonrası, `run_script` ile idempotent; `-print`/`-standalone` hariç). İçerik: **View Transitions API** — `@view-transition { navigation: auto; }` (çapraz-belge sayfa geçişi) + `kv-out`/`kv-in` fade+slide keyframe'leri `::view-transition-old/new(root)`'ta. **Micro-interaction:** `a, button, [role=button]` global smooth `transition` (var olan hover/active'leri yumuşatır; inline transition'lar override → çakışma yok). **Erişilebilirlik:** tüm hareket `@media (prefers-reduced-motion: no-preference)` içinde; `:focus-visible` coral ring. **Capture-güvenli:** view-transition pseudo'ları geçici snapshot, gerçek DOM opacity:1 (GOTCHA-2 tetiklenmez). Chromium'da çalışır (preview doğruladı: hasVT + startViewTransition API + keyframe parse); desteklemeyen tarayıcıda sorunsuz anlık-nav'a düşer. **Yeni ekran eklerken:** aynı bloğu helmet style'a koy (ya da script'i tekrar çalıştır — idempotent).

## 20) API Sözleşmesi — geliştirici teslimi (Faz 3 · madde 1)
`KIRO2 API Sozlesmesi.dc.html` (**AÇIK** docs; sticky sidebar + endpoint kartları, IBM Plex Mono koyu kod blokları). `kiro-data.js` export'larının üretim REST karşılığı: base `api.kiro2.app/v1`, Bearer JWT, hata zarfı `{error:{code,message}}`, cursor sayfalama, roller. **Uçlar:** `/me` (persona) · `/subjects` · `/topics` · `/curriculum/:ders` · `/topics/:konu/atoms` · `/review/due` + `POST /review/:id/grade` (FSRS) · `POST /questions/:id/answer` + `POST /cat/next` (θ/BKT **sunucuda**) · `/exams/last` · `/streak/checkin` · `/level` (seviyeEsik) · `/achievements` (tier+milestone) · `/engine`. Her kart "kullanan ekranlar"ı listeler; JSON şekilleri mock ile **birebir**. **Statik** doküman (logic yok → doğrudan düzenlenebilir + yazdırılabilir). Kilit not: gerçek geçişte tek iş = `import('./kiro-data.js')` yerine bu uçlara `fetch`; şekiller aynı olduğundan **ekranlar dokunulmadan** çalışır. ⚠️ JSON kod bloklarında `{{`/`}}` bitişikliğinden kaçın (DC hole parser) — nesneleri boşluk/newline ile ayır.

---

## 22) Kanıt-temelli iyileştirmeler + EA/Sözel kapsam (son tur)
Derin analiz (`KIRO2_DERIN_ANALIZ.md`) yol haritasının uygulanan maddeleri:
- **P1.4 Gerçek AI:** AI Sohbet + Sokratik AI artık `window.claude.complete` çağırıyor (kaygı-duyarlı Sokratik sistem-prompt, en zayıf `topics`'e dayalı, "yazıyor…" + scripted fallback). Sokratik hibrit (açılış scripted, sonrası canlı).
- **P1.5 Boss yumuşatma:** yenilgi "Ejderha seni yendi" → "Henüz değil · kaybeden yok"; retry "Hazırlan, geri dön".
- **P1.6 Paywall:** ücretsiz katmana FSRS tadımlığı (5 kart) + hâkimiyet takibi.
- **P0.1 Tek "bugün":** `kiro-data`'ya `bugunBilgi()`+`buHafta()`; Panel + Haftalık Plan canlı referanstan.
- **P0.2 Sunum:** Canlı Demo 8→12 sahne (Geri Sayım/Plan/Başarımlar/Abonelik).
- **VT fix:** `@view-transition{navigation:auto}` 50 dosyadan kaldırıldı ("skipped transition" konsol hatası); micro-interaction + focus + reduced-motion korundu.
- **Veli satın-alma yüzeyi:** Veli Paneli'ne ROI bandı (gerçek metrik +8,5/%86/seri + dershane-karşıtı konumlama + koyu Premium CTA → Abonelik; FOMO'suz).
- **EA/Sözel (§21):** `dersKatalog`+`alanlar` + `KIRO2 Alan Kutuphanesi.dc.html` (üç alan kartı + katalog derinliği; persona ekranları dokunulmadı).
Kalan P2/P3 (kaygı testi çalıştırma · gerçek backend/IRT · cihaz testi) → `design_handoff_kiro2/ROADMAP_DURUM.md`. **Fallback borcu → §22b'de KAPANDI.**

---

## 22b) Fallback borcu sıfırlandı — senkron seed (bu tur)
**Sorun:** Her veri-ekranı `renderVals`'ta kiro-data değerlerini inline literal olarak kopyalıyordu (K-null fallback) → çift kaynak, drift riski, ekran başına onlarca satır.
**Çözüm:** `kiro-seed.js` — `kiro-data.js`'in senkron ikizi (OTOMATİK üretilir; `export`→IIFE→`window.__KIRO`, getter+fonksiyon dahil). 32 veri-ekranının <head>'ine `<script src="./kiro-seed.js">` support.js'ten ÖNCE eklendi → K ilk render'dan önce senkron hazır. Mekanizma: klasik <head> script'i DC boot'tan (React async yüklenir) önce çalışır; runtime <head>'i parse etmez, dokunmaz.
**Yeni desen (§2 güncellendi):** `const K = this.state.K || window.__KIRO; if (!K) return {};` → K'yı doğrudan kullan. `componentDidMount` import'u yalnız RECOVERY (seed 404).
**Kapsam:** 23 ekran tam de-fallback (inline literaller silindi, `if(!K) return {}` guard). 7 motor/iskele ekranı (FSRS loading, Öğrenme Yolu DATA, Boss teması, AI Sohbet + Sokratik robustluk, Onboarding + Düello bank) K senkron yapıldı — bilinçli authored iskeletleri korundu (naive değer-kopyası değil); Onboarding yerleştirme bankası + Düello persona senkron, flaş bitti. **Adaptif Test + Soru Çözme dokunulmadı** (legit loading iskeleti + motor; değer-kopyası yok) — yalnız <head>'lerine seed eklendi.
**Doğrulama:** 32 ekran iframe-harness ile tarandı → hepsinde `.sc-logic-error`=0, çözülmemiş hole=0, `window.__KIRO` mevcut, render dolu.
⚠️ **kiro-data.js değişince kiro-seed.js'i YENİDEN ÜRET** (tek eşitleme noktası; kiro-data.js başında da not var).

## 22c) Sıkı-AA erişilebilirlik pass (bu tur)
`ACCESSIBILITY.md`'deki 6 öneri uygulandı — **YALNIZ aydınlık ekranlarda** (koyu ekranlar zaten AA; `#6B6478` koyuda AA'yı bozar). Runtime iframe-harness kontrast+ad denetimiyle doğrulandı.
- **Kontrast:** küçük gri `#8A8398`/`#9A93A5`→`#6B6478` (194); amber `#C77A1E`/`#B5701A` metin→`#9A5D0D` (52, inline+JS); sabit coral `color:#FF6F5C`→`#C2452B` (17). Koyu-kart yan-düzeltmesi: Lig sıralama kartı + Düello güç etiketleri→`#9B93A8`.
- **Ad:** 3 nav rayı + topbar dişli/çan + geri/kapat + gönder + Öğrenme Yolu düğümleri + Ayarlar swatch'ları → `aria-label`; sohbet girişleri + İnteraktif kaydırıcılar → `aria-label`. Runtime: adsız etkileşimli öğe **0**, koyu regresyon **0**.
- **Bilinçli korundu:** `{{ accent }}`-güdümlü coral metin (kullanıcı-ayarlı vurgu), anlamsal durum renkleri (yeşil/kırmızı/ders), dekoratif/pasif griler (rec 4, WCAG muaf).
⚠️ **Kural:** kontrast düzeltmeleri koyu ekranlarda YAPILMAZ (`#8A8398` koyuda 5.3=AA; `#6B6478` koyuda 3.3=FAIL). Yeni aydınlık ekranda küçük ikincil metin için doğrudan `#6B6478`, küçük amber için `#9A5D0D`, sabit coral metin için `#C2452B` kullan.

## 22d) Sınava Geri Sayım — kaygı-nötr A/B varyantı (bu tur)
`KIRO2 Sinav Geri Sayim.dc.html`'e `varyant` tweak'i (A/B) eklendi; KOYU şafak kanonu korundu. **A · "Geri sayım"** = mevcut dev geri-sayım sayısı (`{{ gun }}` + "{{ birim }} kaldı"). **B · "Kaygı-nötr" (VARSAYILAN)** = geri-sayım sayısı YOK; hero serif teyit ("Bugüne bak. Gün saymaya gerek yok."), sınav günü sayaç değil **sabit "ufuk"** çipi (YKS ufku · {{ tarih }}), chip'ler "kalan" yerine **büyüme** çerçevesi (günlük seri · en uzun seri · günlük ritim), hedef alt-satırı sıralama-baskısız, present-odaklı eyebrow (BUGÜN · {{ bugunUzun }}, `bugunBilgi()`). Gerekçe: geri-sayım/deadline durumluk kaygıyı artırır; süreç + kontrol-edilebilir eylem odağı azaltır (CLAUDE.md "sen vs dün"). §2 K-null (persona/seri/seriRekor). GOTCHA-2 uyumlu (giriş opacity animasyonu yok), koyu-ekran kontrastı korundu. **A/B:** `varyant` tweak'ini çevir — her iki kol eval ile doğrulandı (logic-error 0, çözülmemiş hole 0). `birim`/`mantra` A'ya özel; varsayılanı A'ya çevirmek için `varyant` default'unu "Geri sayım" yap.

## 22e) Curriculum atom/ünite katmanı derinleştirildi (bu tur)
- **atomKirilim 4 → 9 konu:** aktif öğrenme bölgesindeki (zayıf+gelişiyor) tüm mat/fiz/kim konuları artık atom kırılımına sahip — Türev · Limit ve Süreklilik · İntegral · Kuvvet ve Hareket · Elektrik · Mol Kavramı · Gazlar · Asit-Baz · Kimyasal Tepkimeler (her biri kavram + 4 atom; hâkimiyet konu ortalamasıyla tutarlı, en zayıf atom belirgin). konu adları `topics` ile birebir. Yeni helper `atomlarByKonu(konu)` + default export.
- **Bilgi Atomları:** chip'ler artık 9 konuyu kapsıyor ("Zayıf konu" → "Odak konu"); konu→kavram→atom + en zayıf atom `enZayifAtom`.
- **Öğrenme Yolu:** authored `DATA` iskeleti (~4,3KB / 30+ satır) TAMAMEN kaldırıldı → ünite ağacı yalnız `K.curriculum`, ders sekmeleri `K.subjects.map(ad)`, sıradaki adım en zayıf `topics` konusu. Artık tam veri-güdümlü (dead fallback yok).
- **İlk Hafta:** gün-3 odak artık odak konunun EN ZAYIF ATOMUNU referans veriyor (`atomlarByKonu`+`enZayifAtom`); 7-gün arc yapısı korundu (pre-persona kurgu, §4).
- **Atom bağı (Öğrenme Yolu → Bilgi Atomları):** "Sıradaki adım" kartı, konunun atom kırılımı varsa "Atomlara in · en zayıf: {atom}" ikincil linkiyle `KIRO Bilgi Atomlari.dc.html?konu={konu}`'ya drill eder; Bilgi Atomları `?konu=` URL param'ını okuyup önseçer (`_urlKonu`). Not: yol düğümleri foundational curriculum konuları (atom yok) → drill topic düzeyindeki kartta doğru yerde.
- kiro-data.js değişti → **kiro-seed.js yeniden üretildi.** 3 ekran eval ile doğrulandı (logic-error 0, hole 0, 5 ders sekmesi, 9 konu chip).

## 22f) Demo/sunum görselleri tazelendi (bu tur)
`screenshots/flow/*.png` 12 görselin tümü yeniden yakalandı (924×540, hq PNG) — §22c a11y renkleri + §22d A/B varyantı eskitmişti. Yakalama reçetesi: show_html → save_screenshot `hq:true`, step-code ile scrollbar gizleme (`*{scrollbar-width:none} *::-webkit-scrollbar{display:none}` + html/body `overflow:hidden`) — aksi hâlde kaydırma çubukları görüntüye giriyor. Geri Sayım görseli artık **varsayılan kaygı-nötr (B)** görünümü gösteriyor; Canlı Demo'nun geri-sayim sahne metni buna göre güncellendi. Tüketiciler değişmedi: `KIRO2 Canli Demo` (12 sahne) + `KIRO2 Sunum` / `Sunum-standalone` (aynı dosya yolları).

## 22g) Kaygı çerçevesi yayıldı — Lig kıyası kapatılabilir + Sınav Sonuç hiyerarşisi (bu tur)
- **Lig — rekabet opsiyonel (P1 kalanı):** yeni `siralamaGizli` tweak + bant üzerinde kullanıcıya açık **"Sıralamayı gizle/göster"** düğmesi (state `rankHidden`, tweak = başlangıç değeri). Gizliyken podyum+liste yerine sakin boş-durum kartı ("Sıralama gizli — odak sende." + "XP'n, serin ve terfi hakkın aynen işliyor"); sağ raydaki koyu "Bu haftaki sıran #N" kartı "Bu haftaki emeğin" (XP + sen-vs-dün delta) kartına dönüşür. Ayrıca `sakinMod`'da: düşme bölgesi başlığı/ok/sıra-numarası kırmızı→**amber** (#9A5D0D, "Alt bölge · son 5"), CTA "XP kazan, sırada yüksel"→"XP kazan", toNextText "N. sıraya yüksel"→"Bir üst sıra X XP uzakta — acele yok." (sakinMod=false eski rekabetçi hâli aynen verir → A/B). ROADMAP'teki "ürün onayı" çekincesi korundu: varsayılan görünür, gizleme kullanıcı tercihi.
- **Sınav Sonuç:** hero istatistik sırası sıralama-birincil → **net-birincil** (TYT neti · Toplam net · Tahmini sıralama en sona) + etiket "yalnız yön göstergesi" eki. Sayı dürüstçe duruyor, hiyerarşi baskıyı kaldırıyor.
- `lig.png` yeniden yakalandı (22f reçetesi). Seri Dondurma zaten kaygı-duyarlı (affedicilik + anti-örnek nudge) — dokunulmadı.
- **Handoff paketi tazelendi (bu tur):** `design_handoff_kiro2/` içindeki tüm kopyalar (DEVIR/ACCESSIBILITY/CLAUDE/DERIN_ANALIZ/USER_TESTING/kiro-data) kökten eşitlendi; **kiro-seed.js** ve **screenshots/flow/ (12 PNG)** pakete eklendi; README güncellendi (seed dosya listesi, sıkı-AA token notları, navigation:auto kaldırıldı notu, Geri Sayım/Lig ekran özetleri, 12 görsel).

## 22h) Deste export + veli satın-alma yüzeyi (bu tur)
- **Export:** `KIRO2 Sunum` → **PPTX** üretildi (gen_pptx screenshots modu, 1920×1080, `resetTransformSelector:"deck-stage"`, 11 slayt + konuşmacı notları, doğrulama bayrağı 0) ve **PDF** yazdırma sekmesi açıldı (deck-stage slayt-başına-sayfa basar).
- **Veli-yüzü paywall (P2):** `KIRO2 Abonelik.dc.html` artık `?rol=veli` okuyor (+`rol` tweak). Veli modunda: hero "Hüseyin için tam erişim" + **siz-dili**, hero altı **kanıt şeridi** (Veli Paneli ROI rakamlarıyla aynı: +8,5 net · %86 uyum · seri) + dershane maliyet çapası, premList veli-öncelikli ("Haftalık veli raporu" ilk), CTA "Hüseyin için 7 gün ücretsiz başlat", alt not "Fiyat ve satın alma yalnız veli hesabında — öğrenci fiyat baskısı görmez" (kaygı-duyarlı ilke), geri-link Veli Paneli'ne. Veli Paneli ROI CTA'sı `?rol=veli`'ye bağlandı.
- **Kanon temizliği:** Veli Paneli'ndeki menekşe rozet-uyarı kartı (#F5F3FF/#5B21B6 — indigo yasağı ihlali) şafak tonuna çekildi (#FFF3EE + #C2452B).

## 22i) Kaygı ölçümü prototipe bağlandı — USER_TESTING pre/post anketi (bu tur)
**`KIRO2 Kaygi Olcum.dc.html`** (AÇIK kâğıt — form=nötr iş yüzeyi) — USER_TESTING §3/§7'deki STAI-S kısa form (6 madde: sakin/gergin/üzgün/rahat/memnun/endişeli; 1-4 Hiç→Çok fazla; pozitifler ters kodlanır, skor ×20/6 → 20-80). `?asama=pre|post` (+`asama` tweak) = 2 mini ekran. Kaygı-duyarlı kararlar: **skor katılımcıya gösterilmez** (etik §6) — yalnız "Moderatör görünümü" toggle'ında pre/post/Δ + §5 kriter kartı ("post ≤ pre": karşılandı=yeşil / karşılanmadı=amber "P0 incele", asla alarm-kırmızısı); üst şeritte "Test edilen sensin değil, ürün" + durma hakkı; pre-submit sonrası "Tura başla" → Canlı Demo. Kalıcılık: `localStorage['kiro2-kaygi-anket']` = {code, pre:{answers,score,ts}, post:{…}}; moderatör görünümünde "Sonraki katılımcı — yanıtları sıfırla" (yalnız bu anahtarı siler). Katılımcı kodu alanı başlıkta. **Canlı Demo** sol rayına "Test günü · Anket ön/son" linkleri eklendi; USER_TESTING §8 güncellendi. Seed'e bağlı DEĞİL (persona verisi kullanmaz — gerçek katılımcı). ⚠️ dipnotta: üretim öncesi ölçek lisansı + etik kurul.
⚠️ **GOTCHA (runtime, genel):** mount-sonrası güncellenen düğmelerde (a) bütün-string stil deliği `style="{{ x }}"` ve (b) `background:{{ x }}` KISALTMASI yeniden uygulanmaz — **`background-color:{{ x }}` longhand** + özellik-başına delik kullan (color/border/cursor/box-shadow sorunsuz); (c) interpolasyonlu aria-label (`aria-label="{{ a }} — {{ b }}"`) hiç render olmaz — tek delik `aria-label="{{ o.aria }}"` (JS'te birleştir).

## 22j) Üretim başlangıç dosyaları — web+mobil ortak çekirdek (bu tur)
Karar: üretim **her iki platform** — monorepo önerisi `apps/web` (Next.js) + `apps/mobile` (Expo RN), `packages/tokens · types · api-client` ortak. Handoff paketine eklendi:
- **`tokens.ts`** — platformdan bağımsız token'lar: paper/dusk yüzeyleri, dawn aksanı, sıkı-AA metin karşılıkları (#9A5D0D amber-metin, #C2452B coral-metin, #6B6478 gri), ders renkleri İKİ palet (koyu-parlak + açık-panel + EA/Sözel katalog), mastery tier, radius/gölge/motion/44px hit. Kanon kuralları dosya başında.
- **`tokens.css`** — web yansıması: `:root` sabitleri + `.k-paper`/`.k-dusk` tema sınıfları (tema = ekran türü, kullanıcı toggle'ı değil), `.k-num` tabular, odak halkası, reduced-motion tabanı.
- **`types.ts`** — kiro-data'nın tam TypeScript tipleri (Persona/Subject/Topic/Curriculum/AtomKirilim/ReviewItem/LastExam/Question/CAT/SeviyeBilgi/yardımcı imzalar) + export→endpoint eşlemesi. ⚠️ `Question.dogru`/çözümler üretimde istemciye gönderilmez notu tiplerde.
README "Files" bölümü güncellendi. Sonraki üretim adımları kullanıcıya adım-adım listelendi (0-8): iskelet → token → çekirdek bileşen → mock'lu veri katmanı → ekran portu (çekirdek döngü önce) → motor/AI → kalite kapıları → flag'li yayın.
- **`BILESEN_ENVANTER.md` (adım 3 haritası):** A) fiilen paylaşılan DC'ler — SideNav (Kenar ×3 → üretimde tek bileşen, `role` prop) + MasteryBadge (pct/trend/badge; eşikler masteryTier ile birebir; dc-import kullanım haritası grep'le doğrulandı); B) 13 P0 yapı taşı; C-D) çekirdek döngü + oyunlaştırma composites (props imzaları + piksel referans dosyaları); E) port sırası (P0→SideNav+Panel→çekirdek döngü→kalanlar). Bileşenleştirme eşiği: tek-ekran yapılar (Boss HUD, sandbox) kütüphaneye alınmaz. SurveyScale üretim uygulamasına girmez (araştırma aracı).

- **`api-client.ts` + `kiro-data.json` (adım 4):** tipli client — `configureKiroApi({mode:'mock'|'live'})`; mock kiro-data.json'ı servisler (json run_script'le kiro-data.js'ten üretildi, getter'lar düz sayı: tytNet=83, aytNet=37.25), live REST tabanına gider (Bearer token + KiroApiError). Sunucu-otoriter uçlar: `postAnswer` (dogru/çözüm yalnız yanıttan sonra iner), `postCatNext` (mock'ta `dogru` alanı sıyrılır), `postReviewGrade`. `seviyeBilgiFrom` kiro-data ile birebir. ⚠️ kiro-data.js değişince kiro-data.json'ı da yeniden üret (seed gibi ikinci eşitleme noktası).

## 22k) Durum deseni standardı — yükleniyor · boş · hata (bu tur)
**`KIRO Durumlar.dc.html`** (AÇIK spec ekranı) — P3 "sistematik durum yönetimi"nin tasarım standardı; canlı örnekler açık+koyu çift olarak. Üç ilke: (1) **zıplamayan iskelet** — gerçek düzen geometrisi, 1,6s nabız (`kSkel` opacity; reduced-motion'da statik), <400ms'te gösterilmez, spinner yok; (2) **yönlendiren boşluk** — kesikli kart + serif tek cümle (boşluk çoğu zaman İYİ haber: "Bugün tekrar yok.") + tek CTA; eksiklik dili yasak; (3) **sakin hata** — amber çerçeve (açıkta #F2D9AC/#9A5D0D, koyuda #FFB570), kopya formülü zorunlu: ne oldu · "sorun sende değil" · "çalışman güvende" · tek kurtarma eylemi; kırmızı/hata kodu/jargon yasak. Kopya formülleri tablosu ekranda. Envanter güncellendi: B tablosu 13→15 (Skeleton + ErrorState eklendi; EmptyState referansı Durumlar'a taşındı). Not: prototipte veri senkron seed'den geldiği için yükleniyor pratikte görünmez — standart üretimin ağ gerçekliği için.

## 22l) EA/Sözel çekirdek kapsam + Alan Kütüphanesi derinliği (bu tur)
P2 "Kapsam: EA/Sözel"in inşa-edilebilir çekirdeği:
- **`katalogKonular`** (kiro-data.js): edb 14 · tar 13 · cog 12 · fel 8 · din 6 = 53 konu, **persona-BAĞIMSIZ** envanter (hakimiyet yok — Hüseyin bu dersleri çalışmıyor; dürüstlük korundu). Sayımlar `dersKatalog.konuSayisi` ile script-doğrulamalı birebir.
- **questionBank 18→26:** +8 çözümlü EA/Sözel sorusu (edb: Gazel/Divan + Halit Ziya/Servet-i Fünun · tar: Sened-i İttifak + TBMM 23 Nisan 1920 · cog: Doğu Anadolu karasallık + nüfus piramidi tabanı · fel: rasyonalizm + tümdengelim). Şekil birebir aynı (b/a/sure/cozum/neden).
- **Alan Kütüphanesi:** katalog kartlarında "N konunun tamamını gör" açılır listesi (numaralı 53 konu) + "N örnek soru çözümüyle havuzda" rozeti; açıkken örnek chip'leri gizlenir. Dipnot güncellendi.
- **Eşitleme:** kiro-seed.js + kiro-data.json + handoff kiro-data.js YENİDEN üretildi (tek script; sayım+soru doğrulamalı). types.ts: `Question.ders: KatalogKey`, `KatalogKonular` tipi; api-client: MockData pick + `getKatalogKonular(ders)` (`GET /katalog/:ders/konular`).
- ⚠️ Kalan (üretim işi, ROADMAP'te): EA/Sözel için curriculum ağacı + tam soru havuzu + EA/Sözel persona — ürün kapsamı kararı.
⚠️ **GOTCHA (str_replace):** kiro-data.js'te satır sonunu yutan no-op edit `export const alanlar`'ı yorum satırına gömdü → seed üretimi "Unexpected token ':'" ile kırıldı; blok-blok parse ile bulundu. Ders: anchor amaçlı kendine-eşit edit YAPMA.

## 22m) Kanon eşitleme (bu tur)
Tasarım Sistemi galerisi: "Araştırma & Sistem" 3→5 kart (**Kaygı Ölçümü** + **Durum Deseni** eklendi), Canlı Demo banner metni "8 sahne"→"12 sahne". `DEVIR-Baslangic.md` (yeni-sohbet devam notu) §22f-22m özetiyle YENİDEN yazıldı — üç-ikiz eşitleme kuralı (seed+json+handoff kopyası) ve runtime gotcha'ları şablona işlendi.

## 22n) P0 Bileşen Sayfası + ui-starter iskeletleri (bu tur)
Adım 3'ün araç-içi tamamlaması, iki parça:
- **`KIRO Bilesenler.dc.html`** (AÇIK spec, template-only DC) — 15 P0 yapı taşının tek-sayfa piksel referansı: her kartta numara + props imzası (mono) + varyant/durum örnekleri (primary/ghost/goldDark+disabled Button; streak/tag/status Chip; solid/dashed/dusk Card; ring/bar; 2'li+4'lü Segmented; Avatar ring'li; IconBadge 3 ton; Callout 3 ton; ZoneHeader amber-demote; Skeleton/Empty/Error mini + "tam standart → KIRO Durumlar" linki). Galeriye eklenmedi (spec — Durumlar gibi ayrı yaşar; istenirse eklenir).
- **`design_handoff_kiro2/ui-starter/`** — 18 dosya: theme.tsx (KiroThemeProvider — tema ekran TÜRÜ; surf() yüzey çözücü; numText tabular) + 15 bileşen .tsx + index.ts + README. Hepsi `../tokens` tüketir, ham hex yok; a11y kuralları gömülü (Input.ariaLabel zorunlu, scale radiogroup, ProgressBar role, 44px hit). ⚠️ README'de açık: **test edilmemiş başlangıç kodu** — derleme ortamı yok, hedef repoda tip/ince ayar yapılır. Skeleton delayMs=400 varsayılanı Durumlar standardıyla birebir.

## 22o) Hızlı dokunuş turu: galeri + kanon denetimi + yoğunluk tweak'i (bu tur)
- **Galeri:** `KIRO Bilesenler.dc.html` Tasarım Sistemi galerisine eklendi — "Araştırma & Sistem" 5→6 kart, №25 "Bileşen Spec'leri". §22n'deki "galeriye eklenmedi" borcu kapandı.
- **Kanon denetimi (temiz):** proje genelinde alarm-kırmızısı (#EF4444/#DC2626/#F87171) ve indigo taraması → tek eşleşme Derin Araştırma Promptu'ndaki macOS terminal-nokta mock'u (semantik değil, bırakıldı). Koyu ekranlarda #6B6478 sızıntısı yok.
- **Yoğunluk tweak'i:** `KIRO2 Ogrenci Paneli` yeni prop `yogunluk` (enum Rahat/Kompakt, Görünüm bölümü). Uygulama: helmet'e `.yogun-kompakt` kuralları (main padding/gap 26/22→16/14, rkpi gap+kart padding sıkışır); main'in class'ı JS'te tek delik (`{{ anaSinif }}` — interpolasyon gotcha'sından kaçınmak için bütün string JS'te birleşir). kiro-data DEĞİŞMEDİ → üç-ikiz gerekmedi.

## 22p) Orta paket: 4 yeni ekran + EA/Sözel ünite ağacı + sınıf roster'ı (bu tur)
- **kiro-data.js +2 export → üç-ikiz yeniden üretildi** (tek script, doğrulamalı; 28 export): ① `katalogUniteler` — edb 5 / tar 4 / cog 4 ünite; konular `katalogKonular` ile birebir (script sayım+üyelik doğruluyor) ② `sinifRoster` — 12-A, 8 öğrenci (θ / hakimiyet / amber risk metni / sonAktif). ⚠️ Seed-üretim GOTCHA: kiro-data'da `export default` satırı VAR — regex yalnız `export const/function` soyarsa IIFE "Unexpected token 'default'" ile kırılır; default satırını komple sil (reçeteye eklendi).
- **KIRO2 Hesap Kurtarma** (galeri №26, AÇIK): 4 adımlı state-machine (e-posta→kod→yeni şifre→hazır); kaygı-nötr kopya ("Şifre unutmak da çalışmanın bir parçası", başarıda "Serin ve ilerlemen aynen yerinde"), amber nazik hatalar, canlı şifre-kural checklist'i. Tweak: `baslangicAdim`. K gerektirmez (seed yok — Durumlar gibi).
- **KIRO2 Cevrimdisi** (№27, AÇIK): Durumlar standardının çevrimdışı uygulaması — sakin amber durum bandı (alarm yok), hero "İnternet gitti. Çalışman gitmedi.", cihazda-hazır paketler K'dan türetilir (zayıf konu paketi + FSRS due kart toplamı + son deneme AYT yanlışları), eşitleme kuyruğu + "bağlantı bekliyor" (dimmed). Tweak: `durum` enum 3 hâl (bant per-property delik + `background-color` longhand — gotcha #1 uygulandı).
- **KIRO2 Odev Atama** (№28, AÇIK, öğretmen · Kenar Ogretmen `active="assignments"`): 3 bölümlü form (konu radio — zayıf önde etiketli; soru sayısı + teslim segmented; `sinifRoster` checkbox listesi risk-amber satırlı) + yapışkan özet + **"kişiye özel zorluk (θ tabanlı)" switch (varsayılan açık)** + kaygı-duyarlı varsayılanlar kartı (sıralama yayınlanmaz · geciken "bekliyor" dili · risk bayrağı öğrenciye gösterilmez).
- **KIRO2 Moderator Kilavuzu** (№29, AÇIK, saha paketi): 60 dk oturum akışı 6 faz (dk + görev + birebir akran-dili script'i italik serif blokta), 3 kritik ilke (test edilen sensin / skor paylaşılmaz / durdurma hakkı), oturum-öncesi kontrol listesi, veri&etik kartı (anonim kod, localStorage sıfırlama, STAI-S lisans + etik onay uyarısı araç-dışı işaretli), pre/post/Canlı Demo hızlı linkleri.
- **Alan Kütüphanesi:** drill artık `katalogUniteler` varsa ünite başlıklı gruplu (amber uppercase başlık, numaralar kesintisiz devam); ağaçsız dersler (fel/din) eski düz liste. Template nested sc-for'a çevrildi.
- **Galeri:** Öğrenci akışı 13 · Paydaş 3 · Araştırma & Sistem 7 (yeni kartlar №26-29; numaralar stabil kimliktir, grup-içi pozisyon değil).

## 22q) №26-29 flow görselleri (bu tur)
`screenshots/flow/` +4 PNG (924×540 hq, §22f reçetesi): `hesap-kurtarma.png` (adım 1/3) · `cevrimdisi.png` (çevrimdışı hâl, amber bant + paketler) · `odev-atama.png` (konu seçimi, zayıf-önde) · `moderator-kilavuzu.png` (ilkeler + oturum akışı başı). Toplam 16 görsel; handoff `design_handoff_kiro2/screenshots/flow/` eşitlendi. Deste/demo bu 4'ü referans almıyor — değişiklik yok.

## 22r) fel/din ünite ağacı (bu tur)
`katalogUniteler` +2 ders: **fel** 4 ünite (Felsefeyi Tanıma · Bilgi & Varlık · Değer Felsefesi · Toplum & Mantık) · **din** 3 ünite (İnanç & İbadet · Ahlak & Yaşam · Peygamber & İslam Düşüncesi). Konular `katalogKonular` ile birebir (script doğruladı: 5 ders ✓). Üç-ikiz yeniden üretildi (28 export, seed eval ✓, json 18 anahtar). Alan Kütüphanesi drill'i değişiklik gerektirmedi — ağaç varsa gruplama otomatik; artık 5 dersin tümü ünite başlıklı. §7'deki "fel/din ünite ağacı" borcu kapandı.

## 22s) Backend-öncesi boşluklar kapandı: Giriş · Ödevlerim · Ödeme + sözleşme genişledi (bu tur)
Kanıtlı denetim bulguları (giriş ekranı yok · öğrenci ödev ucu yok · Abonelik CTA'sı Kutlama'ya gidiyor · sözleşmede auth/assignments/sync/notifications/league/duel/billing yok) kapatıldı:
- **KIRO2 Giris** (№30, AÇIK, Hesap Kurtarma görsel dili): Giriş/Kayıt sekmeli kart; kaygı-duyarlı hint'ler; başarıda giriş→Panel, kayıt→Onboarding ("Seviyeni ölçelim"). `mod` tweak. Bağlantılar düzeltildi: Hesap Kurtarma "Girişe dön"→Giris; Onboarding'e "Hesabın var mı? Giriş yap" + "sonra kaydet" linki.
- **KIRO2 Odevlerim** (№31, AÇIK, Kenar `active="odev"`): `kiro-data.js` yeni export **`odevler`** (3 ödev; Mehmet Öztürk, mat; durum acik/bekliyor/tamam) → **üç-ikiz yeniden üretildi** (29 export, seed eval ✓). Kart: ders-renkli ikon, durum çipi (bekliyor=amber "eksik değil" notu), ilerleme barı, "Sorular seviyene göre seçildi" rozeti. `bos` tweak boş durumu gösterir. **KIRO Kenar'a "Ödevlerim" nav öğesi eklendi** (id `odev`, Plan'dan sonra).
- **KIRO2 Odeme** (№32, AÇIK): checkout — kart formu (maskeli girişler), özet (7 gün ücretsiz, ilk ödeme tarihi canlı), "Bugün ödeme alınmaz" + "sessizce ücret alınmaz" güvencesi; `?rol=veli&fatura=` destekli; başarı ekranı → Kutlama. **Abonelik CTA artık `{{ odemeHref }}`** (rol+fatura parametreli) — Kutlama'ya kısa devre kapandı.
- **API Sözleşmesi +6 bölüm:** Kimlik & Hesap (`/auth/register·login·recover×3·refresh`) · Ödevler (`GET/POST /assignments`, `/assignments/:id/progress`; "bekliyor" sözleşmeye yazıldı) · Bildirimler (`/notifications`) · Çevrimdışı Senkron (`/sync/packages`, `/sync/events` idempotent) · Fatura (`/billing/trial·plans·subscription`) · Oyunlaştırma'ya `/league` + `/duel/match`. Yan nav 6 yeni bağlantı.
- **types.ts + api-client.ts eşitlendi:** `Odev/OdevDurum · KatalogUnite(ler) · SinifOgrenci · AuthTokens/Login/RegisterRequest` tipleri (§22p'de eksik kalan katalogUniteler/sinifRoster tipleri de eklendi); `MockData` +3 anahtar; client'a `login/register/recover · getAssignments/postAssignment/postAssignmentProgress · getClassRoster` (mock↔live).
- **Galeri:** Öğrenci akışı 13→16 (№30-32).
⚠️ Kalan (bilinçli): №30-32 flow görselleri gerekirse §22f reçetesiyle; sunum hâlâ §22g-öncesi içerikte.

## 22t) Flow görselleri №26-32 tamam + sunum güncellendi ve yeniden export (bu tur)
- `screenshots/flow/` +3 PNG: `giris` · `odevlerim` · `odeme` (924×540 hq, §22f reçetesi) — toplam 19 görsel; handoff eşitlendi.
- **Sunum 11→12 slayt:** Panel'den sonra yeni **"Günün ötesi"** slaytı (AÇIK) — 3 kolon: Roller döngüyü kapatır (odev-atama+odevlerim) · Akış dayanıklı (cevrimdisi+giris) · Ölçüme & üretime hazır (moderator-kilavuzu + 32 ekran·3 rol·15 P0·29 export stat kartı). Konuşmacı notu hem `data-speaker-notes`'a hem `#speaker-notes` JSON dizisine (indeks 10) eklendi.
- **Export tazelendi:** `export/KIRO2 Sunum.pptx` (gen_pptx screenshots modu, 12 slayt + notlar, doğrulama bayrağı 0) + PDF `open_for_print` ile. ⚠️ Eski türevler (`Sunum-print*.dc.html`, `Sunum-standalone.dc.html`) hâlâ 11 slayt — gerekirse yeniden üretilir; ana deste otoriter.

## 22u) Sunum türevleri senkron + Mobil Uyarlama spec ekranı (bu tur)
- **Türev senkronu:** `Sunum-print` + `Sunum-standalone` x-import bloğu ve speaker-notes JSON'u ana desteden splice edildi → ikisi de 12 slayt (`-print-zic132` geçici artifact, dokunulmadı).
- **KIRO2 Mobil** (№33, galeri "Araştırma & Sistem" 7→8): `ios-frame.jsx` (starter) ile 4 telefon ekranı, 390pt, hit ≥44pt, veri seed'den: **Bugün** (koyu şafak hub: tarih `bugunBilgi`, seri, 3 görevlik plan, tab bar) · **Soru Çözme** (kâğıt; `questionBank[0]`, seçili şık, 4/10 bar) · **FSRS Tekrar** (due kuyruk, hatirlanabilirlik %, amber<82) · **Ödevlerim** (odevler kompakt kart). Işık/koyu kuralı ve iki ders paleti (koyu-parlak/açık-doygun) korunur. §7'deki "mobil uyarlamalar" borcunun ilk somut teslimi — istenirse ekran seti genişletilir.
- **Genişletme (aynı tur):** +4 telefon → 8: **Kutlama** (koyu şafak, konfeti noktaları, dk+seri stat, "Yarın görüşürüz") · **Lig** ("sen vs dün" +XP hero birincil, "Sıralamayı gizle" görünür, sen-satırı coral vurgulu) · **Sokratik AI** (yönlendiren diyalog balonları + hızlı yanıt çipleri) · **Çevrimdışı** (amber bant, 3 indirilen paket). Safe-area düzeltmesi: içerik üst 64-66px / alt ≥34px; Bugün tab bar bottom 22px (verifier bulgusu).

## 22v) Dokümantasyon eşitleme + kanon denetimi (bu tur)
- **Kanon denetimi (temiz):** alarm-kırmızısı/indigo taraması → tek eşleşme yine Derin Araştırma Promptu'ndaki terminal-nokta mock'u (bilinen istisna); Mobil'de #6B6478 yalnız açık zeminlerde, koyu telefonlar rgba beyaz griler.
- **Handoff README:** 33 ekran; export→endpoint tablosuna odevler/sinifRoster/katalogUniteler + auth/sync/notifications/billing satırları; ekran envanterine Giriş&Kayıt · Hesap Kurtarma · Ödeme · Çevrimdışı · Ödevlerim↔Ödev Atama; flow görselleri 19; Mobil referans notu.
- **ROADMAP_DURUM:** "Backend-öncesi boşluklar ✅ (§22s)" + "Mobil uyarlama ✅ ilk teslim (§22u)" maddeleri; sunum 12 slayt notu.

## 22w) Canlı Demo 12→15 sahne (bu tur)
Paydaş turuna 3 sahne eklendi (mevcut flow PNG'leri + canlı geçiş aynen çalışır): **Ödev Atama** (öğretmen yüzü, θ-tabanlı set) · **Ödevlerim** (öğrenci ucu, "bekliyor" dili) · **Çevrimdışı**. Banner metinleri (Demo + galeri) "15 sahne".
⚠️ **GOTCHA (runtime, yeni):** `<img src="{{ x }}">` deliği parse anında ham `{{ }}` URL'siyle bir istek atıyor (konsol resource_error) — sc-if sarmak yetmiyor. Çözüm: img'i JS'te `React.createElement` ile kur, tek delikle (`{{ shotEl }}`) yerleştir (Canlı Demo'da uygulandı).

## 22x) Üretim yol haritası belgesi (bu tur)
`design_handoff_kiro2/URETIM_YOL_HARITASI.md` — backend entegrasyonu dahil faz faz plan: Faz 0 kuruluş+ADR kararları · Faz 1 tokens/types/api-client paketleri · Faz 2 P0 bileşenler (test+Storybook+piksel diff) · Faz 3 ekranların mock-modda port sırası + ekran başına DoD · Faz 4 backend (OpenAPI'leştirme, uç-uç mock→live flag, sunucu-otoriter motorlar, auth+misafir migrasyonu, AI proxy, çevrimdışı senkron, ödeme, ödev döngüsü) · Faz 5 kalite (E2E senaryoları, a11y, kanon lint'i) · Faz 6 yayın+STAI-S saha ölçümü. README dosya listesine eklendi.
**Revizyon (kanıt-temelli):** varsayımsal hafta tahminleri kaldırıldı; yerine sayılarak alınan kapsam dökümü (41 ekran + 4 paylaşılan DC · 15 bileşen · 26+8 uç · 29 veri anahtarı · 246 DoD kontrolü · 19 PNG · 5 E2E) + kalibrasyon yöntemi (ilk sprintte 3 bileşen + 2 ekran ölç → çarp → her sprint güncelle).

--- 

**İlk istek örneği:** "KIRO2 Şafak kanonunda devam. Single-source bağlama tamamlandı (§3) + fallback borcu senkron seed'le kapatıldı (§22b). [X ekranında Y değişikliği] — küçük dokunuş: yalnız isteneni değiştir, §2 desenini koru (`const K = this.state.K || window.__KIRO; if(!K) return {}` — inline literal YAZMA), kanona ve motorlara dokunma, ışık/koyu kuralına uy. **kiro-data.js'e veri eklersen kiro-seed.js'i yeniden üret.**" — kiro-data.js tek kaynak.
