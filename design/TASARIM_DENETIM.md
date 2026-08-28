# KIRO2 Frontend — Tam Tasarım Denetimi (2026-07-05)

> Amaç: 42 ekranın tamamına adım adım bakış — eksikler, iyileştirmeler ve dünyanın
> ilk-3 EdTech tasarımına girmek için yol. Son bölüm: "yapay zeka yapmış" izlenimini
> silen craft kuralları. Öncelik: P0 (kimliği belirler) → P1 → P2.

---

## A. GÜÇLÜ TEMEL (korunacak — bunlar zaten ilk-3 malzemesi)
- Kavramsal omurga benzersiz: **şafak metaforu** (gece=duygu, gündüz kâğıdı=çalışma). Duolingo'nun baykuşu neyse KIRO'nun şafağı o olabilir — ama henüz yeterince İŞLENMİYOR (bkz. C1).
- Kaygı-duyarlı dil sistemi ("bekliyor", amber-risk, "sen vs dün") = ürün kimliği, rakipsiz.
- Tema-ekran-türü kuralı (paper/dusk) disiplinli; kanon-lint ile CI'da zorlanıyor.
- Tipografi ikiliği (Instrument serif = his, Hanken = işlev) doğru kurulmuş.

## B. EKSİKLER — sistem düzeyi (ekran değil, dil eksik)
1. **Motion kanonu YOK.** Tek kural `prefers-reduced-motion`. Süre/easing/stagger skalası,
   ekran-geçiş imzası, "şafak" temalı bir imza geçişi (ör. alt kenardan doğan ışık süpürmesi)
   tanımsız. Duolingo'yu Duolingo yapan %50 motion'dır. → **P0, yeni DC: `KIRO Motion Kanonu`.**
2. **İllüstrasyon sistemi YOK.** Boş durumlar/kutlamalar/onboarding placeholder. Bespoke SVG ikon
   var ama SAHNE dili yok (spot illüstrasyon grameri: şafak paleti, tek ışık kaynağı, grenli doku).
   → **P0.** AI-görünümünün 1 numaralı nedeni jenerik boşluklar.
3. **Veri-viz kanonu YOK.** Sınav Sonuç, Panel, Öğrenci Özeti, Veli Paneli hepsi grafik çiziyor
   ama ortak gramer (eksen dili, dolgu/çizgi kuralı, boş-veri hali, anotasyon stili) tanımsız →
   ekranlar arası tutarsızlık riski. → **P0, `KIRO Veri-Viz` DC.**
4. **Ses/haptik yok** (web fazında ses küçük ama kutlama/streak için ayırt edici). → P2, karar iste.
5. **Skeleton/yükleme kişiliksiz.** `KIRO Durumlar` standardı var ama nötr; şafak diline bağlanmalı
   (ör. skeleton shimmer'ı dawn-aksan, yüklemede mantra satırı). → P1.
6. **Onboarding duygusal ark zayıf.** Misafir yerleştirme işlevsel; ilk 60 saniyede "bu uygulama
   beni anlıyor" anı yok (tek soruluk kaygı-tonu seçimi + kişisel karşılama). → P1, kapsam kararı.
7. **Hub statik.** Bugün ekranı gökyüzü gradyanı sabit; saat/mevsim/ilerlemeye göre yaşayan gökyüzü
   (yıldız yoğunluğu, ufuk ışığı sınava kalan günle bağlanır) = imza fırsatı. → P1.
8. **Tablet/ara-genişlik hikâyesi yok.** Mobil ertelendi ama 768-1200px tanımsız; öğretmenler
   tablet kullanır. → P1 (en az breakpoint kuralları spec'e).
9. **Bildirim/e-posta yüzeyi tasarımsız.** Veli haftalık özeti e-postası (opt-in var, tasarım yok),
   bildirim kopya sistemi dağınık. → P2.
10. **Erişilebilirlik AA'da kalıyor.** Odak halkası stili, klavye gezinme sırası, canlı-bölge
    duyuruları (doğru/yanlış geri bildirimi) spec'lerde tek tek yok. → P1, yatay madde her sprint'e.

## C. İLK-3 EDTECH İÇİN 5 HAMLE (sıralı)
1. **Şafağı KARAKTERLEŞTİR (maskotsuz).** Güneş/ufuk motifi yaşayan bir varlık gibi davranmalı:
   seri büyüdükçe ufuk aydınlanır, boss yenilince güneş doğar, mola ekranında nefesle gök nabzı.
   Tek tutarlı görsel varlık = akılda kalıcılık. (Maskot ÖNERMİYORUM — 17-19 yaşa çocuksu kaçar;
   soyut-ama-canlı motif daha olgun.)
2. **Motion + illüstrasyon + veri-viz kanonları** (B1-B3) — dil tamamlanmadan craft pass anlamsız.
3. **Ekran-ekran craft pass** (D bölümü kontrol listesiyle, sprint sırasıyla 42 ekran).
4. **İmza etkileşimler:** cevap-gönder mikro-animasyonu (kalem izi?), FSRS derece seçiminde
   dokunsal eğri, kutlamada ConfettiDawn'ın ötesinde tür-bazlı sahneler. Ödül kazandıran şey budur.
5. **Public design-language sayfası** (Awwwards/It's Nice That görünürlüğü) — ilk-3 algısı
   yarısı üründür, yarısı anlatıdır. → P2.

## D. "AI YAPMIŞ" İZLENİMİNİ SİLEN CRAFT KURALLARI (her ekrana uygulanacak kontrol listesi)
AI-görünümünün imzaları ve panzehirleri:
1. **Simetrik 4'lü KPI ızgarası her yerde** → panzehir: hiyerarşi. Bir metrik BÜYÜK (hero sayı,
   serif), kalanlar ikincil satır. Ekran başına tek odak.
2. **Her kart aynı boy/radius/padding** → panzehir: boyut ritmi (1 geniş + 2 dar), tek radius
   skalası ama bilinçli kırılma anları.
3. **Jenerik boş durum (ikon+iki satır ortalanmış)** → panzehir: B2 illüstrasyon sistemi + yerinde
   yazılmış kopya (zaten kanonda: kopyalar birebir, sesli).
4. **Mükemmel yuvarlak sahte veri** (%75, 4.5, 1200) → panzehir: pürüzlü gerçek veri (%67,3 ·
   seri 23 · 14/17). Prototiplerde tarama yapılmalı.
5. **Optik düzeltme yokluğu** → panzehir: büyük serif başlıklarda negatif letter-spacing + optik
   sol hizalama (tırnak/madde asma), ikonlarda optik merkez, sayı/etiket baseline hizası.
6. **Tekdüze dikey ritim** → panzehir: bölümler arası nefes farklı (sıkı grup + cömert ayrım),
   asimetrik marj (içerik sütunu hafif sola, sağda hava).
7. **Gradyan + glow enflasyonu** → dusk ekranlarında gradyan TEK ve kanonik (gökyüzü); kart
   içlerinde düz yüzey + ince doku (paper'da hafif gren).
8. **Hareket yokluğu ya da hepsi fade** → panzehir: B1 motion kanonu; giriş stagger 40-60ms,
   spring yalnız kutlamada, hover'da 1px kalkış değil ışık/renk tepkisi.
9. **Emoji/stok ikon** → zaten yasak; ikon grameri tek stroke ağırlığı + köşe dili dokümante edilmeli.
10. **Her ekran aynı şablon** → panzehir: ekran başına BİR imza anı (Bugün=gökyüzü, Sonuç=hero net,
    FSRS=eğri, Mola=nefes kutusu…). Spec'lere "imza anı" satırı eklensin.

## E. UYGULAMA PLANI (öneri — kullanıcı onayı bekliyor)
- **P0 (3 iş):** `KIRO Motion Kanonu.dc.html` · `KIRO Illustrasyon Sistemi.dc.html` ·
  `KIRO Veri-Viz.dc.html` → sonra kanon-lint'e motion/illüstrasyon kuralları.
- **P1:** 42 ekrana D-listesi craft pass (sprint sırasıyla, ölçülebilir: ekran başına imza anı +
  hiyerarşi düzeltmesi) · yaşayan gökyüzü · skeleton kişiliği · onboarding ark · breakpoint spec ·
  erişilebilirlik satırları.
- **P2:** design-language sayfası · e-posta/bildirim yüzeyi · ses/haptik kararı.
- Her iş bitince: openapi (gerekirse) + YENI_SOHBET_DEVIR.md güncellenir; kopya değişiklikleri
  kanon gereği kullanıcı onayına gider.
