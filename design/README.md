# Handoff: KIRO2 — YKS Hazırlık EdTech Uygulaması

## Overview
KIRO2, Türkiye YKS (TYT/AYT) sınavına hazırlanan **17-19 yaş öğrenciler** için bir EdTech mobil/web uygulamasının **frontend tasarım prototipidir**. Tamamen Türkçe. Öğrenme bilimi çekirdeği: **CAT/IRT** (adaptif zorluk, θ kestirimi), **FSRS** (aralıklı tekrar), **BKT** (bilgi takibi), Sokratik AI ve **kaygı-duyarlı** oyunlaştırma. 33 ekran; öğrenci, veli ve öğretmen rollerini kapsar (galeri: KIRO2 Tasarim Sistemi).

Prototip tek bir tutarlı öğrenci hikâyesi etrafında kurulu: **Hüseyin Ateş, 12. Sınıf Sayısal**, hedefi Bilgisayar Mühendisliği (ODTÜ/Bilkent).

## About the Design Files
Bu pakettteki ve projedeki `*.dc.html` dosyaları **HTML ile üretilmiş tasarım referanslarıdır** — hedeflenen görünüm, kopya ve davranışı gösteren prototiplerdir; doğrudan kopyalanacak üretim kodu **değildir**. Görev: bu tasarımları hedef kod tabanının **mevcut ortamında** (React / React Native / Vue / SwiftUI / Kotlin vb.) o ortamın yerleşik desen ve kütüphaneleriyle **yeniden oluşturmak**. Henüz bir ortam yoksa proje için en uygun çerçeveyi seçip tasarımları orada uygulayın.

> **Not:** Prototipler `.dc.html` (Design Component) formatındadır — bir çalışma-zamanı (`support.js`) template'i tarayıcıda React'e derler. Bu çalışma-zamanı bir **prototip aracıdır**, üretime taşınmaz. Siz yalnızca **görünen tasarımı** (layout, renk, tipografi, etkileşim) hedef çerçevede yeniden kurarsınız.

## Fidelity
**Yüksek (hi-fi).** Renkler, tipografi, boşluk ve etkileşimler nihai. UI'ı kod tabanının kütüphaneleriyle **piksel-hassasiyetinde** yeniden oluşturun. Pixel detay için ilgili `.dc.html` dosyasını tarayıcıda açıp inceleyin.

## İki Otoriter Referans (önce bunları okuyun)
1. **`KIRO2 Tasarim Sistemi.dc.html`** — canlı tasarım sistemi: renk, tipografi, boşluk, bileşenler, oyunlaştırma desenleri ve 24 ekranın galerisi. Tasarımın tek görsel kaynağı.
2. **`KIRO2 API Sozlesmesi.dc.html`** — backend REST sözleşmesi (aşağıdaki "Data Architecture"in tam hâli). Her uç + JSON şekli + kullanan ekranlar.

Ayrıca `DEVIR-NOTU.md` (bu pakette) her ekranın veri bağlama durumunu ve bilinçli tasarım kararlarını içerir — **kapsamlı teknik durum belgesi**.

---

## Design System — "Şafak" (Dawn) Kanonu

### KRİTİK kural: Açık vs Koyu
Ekranın ruhu temayı belirler:
- **AÇIK (sıcak kâğıt)** — çalışma / odak / analitik ekranlar. Gerekçe: uzun çözüm oturumunda göz yorgunluğunu azaltır; YKS gerçeği beyaz kâğıt olduğu için sınav koşuluyla eşleşir. Örn. Soru Çözme, Adaptif Test, FSRS Tekrar, Paneller, Öğrenme Yolu, Haftalık Plan, Abonelik, API dokümanı.
- **KOYU (şafak göğü)** — duygusal / hub / dinlenme / kutlama / ritüel ekranlar. Örn. Bugün (ana hub), Mola, Kutlama, Boss Savaşı, Sınava Geri Sayım, Başarımlar.
- Kavramsal köprü: gece (pre-dawn, duygusal) → güneş doğar → **gündüz ışığında (kâğıt) çalışırsın**.

### Renkler (hex)
**Açık yüzeyler**
- Kâğıt zemin: `#F7F4EF` · Kart: `#FFFFFF` · İkincil zemin: `#FBF8F3` / `#FBF7F1`
- Kenarlık: `#ECE6DD` (birincil), `#E2DACE` (koyu), `#F0EAE1` (ince)
- Mürekkep (metin): `#2A2433` · İkincil: `#4A4456` / `#6B6478` · Soluk: `#8A8398` / `#B0A9B8` / `#B5AEA2`

**Koyu yüzeyler**
- Zemin: `#110C18` / `#150E20` / `#170E22` / `#120A14` (boss)
- Şafak gökyüzü gradyanı (kanon): `linear-gradient(176deg, #141029, #241640, #3E1F4E, #6A2B52, #A33C4E, #D35F49, #F2974C, #FFC76F)` ya da radyal alt-ışık: `radial-gradient(130% 100% at 50% 118%, #FFB57E, #FF8A5B, #C24E7E, #5B2F66, #1A0F26)`
- Koyu metin: `#F1E9F2` / `#FBEFE6` / `#ECE4F0` · İkincil: `rgba(241,233,242,0.6)`

**Dawn aksanı (marka ipliği — hem açık hem koyu)**
- Mercan: `#FF6F5C` (birincil) · `#FF8A5B` · Şeftali: `#FFAE86` / `#FFC59B` · Altın: `#FFD98C` / `#FCD34D`

**Ders renkleri** (iki palet — zemine göre)
| Ders | KOYU-parlak (kiro-data) | AÇIK-panel |
|---|---|---|
| Matematik | `#5B8DEF` | `#3B82F6` |
| Fizik | `#A77BFF` (mor — kanon) | `#8B5CF6` |
| Kimya | `#E25A72` | `#E0593F` |
| Biyoloji | `#2DD4A7` | `#1FB683` |
| Türkçe | `#FFB347` | `#F59E0B` |

**Semantik**
- Risk / zayıf konu: **amber** — **asla alarm-kırmızısı değil** (kaygı-duyarlılık). Dolgu/grafik `#C77A1E`; **açık zeminde amber METİN `#9A5D0D`** (sıkı-AA, bkz. ACCESSIBILITY.md).
- Açık zeminde küçük ikincil METİN grisi `#6B6478` (AA); `#8A8398`/`#9A93A5` yalnız koyu zeminde/dekoratif. Sabit coral METİN açıkta `#C2452B`.
- Başarı / tamam: `#1FB683` / `#34D399` · Hâkimiyet tier renkleri: Tanıdık `#9A93A5`, Yetkin `#7FB0FF`, Usta `#FFAE86`, Fethedildi `#FCD34D`.
- **YASAK:** indigo/lacivert (mor/menekşe yalnız Fizik için korunur).

### Tipografi
- **Instrument Serif** — his / mantra / duygusal başlık (italik sık). Örn. hero başlıklar, mantralar.
- **Hanken Grotesk** — işlev + **tüm sayılar** (her zaman `font-variant-numeric: tabular-nums`). Ana UI fontu, ağırlık 400-800.
- **IBM Plex Mono** — kod / API dokümanı.
- Ölçek (uygulama): h1 ~38px/800, h2 22-26px/800, gövde 14-16px, küçük 11-13px. Büyük sayı hero'ları 96-176px (clamp). Slaytlarda min 24px.

### Boşluk · Radius · Gölge · Motion
- Radius: 8-12px (küçük/çip), 14-18px (kart), 20-22px (büyük kart/hero).
- Kart padding ~18-24px; grid/flex `gap` 12-20px.
- Gölge: yumuşak, renkli-düşük-opaklık (örn. `0 20px 50px -24px rgba(42,36,51,0.3)`); koyu ekranlarda dawn-renkli glow.
- **Motion:** sayfalar arası geçişte micro-interaction + `:focus-visible` ring korunur (View Transitions `navigation:auto` kaldırıldı — konsol uyarısı üretiyordu). Giriş animasyonları **transform-only** (opacity:0→1 değil). Tümü `prefers-reduced-motion`'a saygılı. Kaygı-duyarlı: sakin, yavaş, agresif değil.

### İkonlar & Emoji
- **Tüm ikonlar bespoke inline SVG** (stroke-width 1.8-2.2, `stroke-linecap/linejoin: round`). İkon kütüphanesi yok.
- **Emoji YOK.**

---

## Data Architecture (kritik)
Tüm prototip **tek-kaynak** `kiro-data.js` modülünden beslenir (bu pakette dahil). Ekranlar veriyi **senkron** `window.__KIRO`'dan okur (`kiro-seed.js` — `kiro-data.js`'in otomatik-üretilen ikizi; her ekranın <head>'inde support.js'ten önce yüklenir) → ilk render'da gerçek değerler, flaş yok, ekran-içi inline fallback literali yok. Dinamik `import('./kiro-data.js')` yalnız recovery (seed 404). ⚠️ `kiro-data.js` değişince `kiro-seed.js`'i yeniden üret (bkz. DEVIR §22b).

**Üretimde:** `import('./kiro-data.js')` → `KIRO2 API Sozlesmesi.dc.html`'deki REST uçlarına `fetch`. Şekiller birebir aynı; ekranların iç mantığı değişmez. `kiro-data.js` exports → endpoint eşlemesi:

| Export | Endpoint | İçerik |
|---|---|---|
| `persona` | `GET /me` | kimlik, hedef, seri, XP, seviye, yksTarihi |
| `subjects` | `GET /subjects` | 5 ders + hakimiyet/θ/BKT |
| `topics` | `GET /topics` | konu düzeyi hâkimiyet + durum |
| `curriculum` | `GET /curriculum/:ders` | ünite → konu ağacı |
| `atomKirilim` | `GET /topics/:konu/atoms` | konu-altı atom kırılımı |
| `reviewQueue` | `GET /review/due` + `POST /review/:id/grade` | FSRS kuyruğu |
| `questionBank` / `catBankMat` | `POST /questions/:id/answer` · `POST /cat/next` | sorular + θ/BKT/CAT (sunucuda) |
| `lastExam` | `GET /exams/last` | deneme net dökümü |
| `seviyeEsik` / `seviyeBilgi` | `GET /level` | XP eşikleri → seviye |
| — | `GET /streak` · `/achievements` · `/league` | oyunlaştırma |
| `engine` | `GET /engine` | model + banka meta |
| `odevler` | `GET /assignments` · `POST /assignments` (öğretmen) | ödev döngüsü; durum acik/bekliyor/tamam |
| `sinifRoster` | `GET /class/:id/roster` | öğretmen sınıf listesi (θ + risk) |
| `katalogUniteler` | `GET /katalog/:ders/uniteler` | EA/Sözel ünite ağacı |
| — | `POST /auth/*` · `/sync/*` · `/notifications` · `/billing/*` | Giriş/Kurtarma · Çevrimdışı · Bildirim · Ödeme (sözleşme §auth-§fatura) |

Yardımcılar (`kiro-data.js`): `masteryTier(pct)` (Tanıdık<40, Yetkin<65, Usta<85, Fethedildi), `irtProb(θ,a,b)`, `seviyeBilgi(xp)`, `trNum`, `enZayifAtom`. Türkçe sayı: `.toLocaleString('tr-TR')`.

---

## Screens / Views (ekran envanteri)
Her ekran ayrı bir sayfadır; pixel-detay için ilgili `.dc.html`'i açın. Gruplar:

**Duygusal / Hub (KOYU)**
- **Bugün (KIRO Safak)** — sabah ana hub; günün planı, seri, ruh hâli, "Şafağa X tuğla" hero. Türev odak kartı → Soru Çözme.
- **Kutlama** — kaygı-duyarlı kutlama anı (şafak konfeti); 4 tür: günlük/seviye/seri/boss (`?type=`).
- **Mola** — nefes/dinlenme ritüeli.
- **Sınava Geri Sayım** — iki varyant (`varyant` tweak): **Kaygı-nötr (VARSAYILAN)** — geri sayım sayısı yok, "Bugüne bak" + sabit "YKS ufku" çipi + büyüme çipleri; **Geri sayım** — `yksTarihi`'den canlı gün farkı ("gündoğumu").
- **Başarımlar** — trophy room; hâkimiyet tier madalyonları + seri kilometre taşları.
- **Boss Savaşı** — en zayıf konuyu (Türev) "boss"a çeviren savaş; HP/can/kombo; zayıf-nokta = en zayıf atom.

**Çalışma / Odak (AÇIK)**
- **Soru Çözme** — sınav-tarzı soru + adım adım çözüm.
- **Adaptif Test** — CAT/IRT motoru (θ kestirimi, SE yakınsama).
- **FSRS Tekrar** — zamanı gelen kartlar; getirim pratiği.
- **Harmanlanmış Deneme** — interleaving oturumu.
- **Neden Geri Bildirim** — yanlışta "neden"; adım adım muhakeme, atom rozeti.
- **İnteraktif Çözüm** — canlı parabol sandbox.
- **Öğrenme Yolu** — ders → ünite → konu curriculum ağacı (düğüm haritası, boss kontrol noktaları).
- **Bilgi Atomları** — konu → kavram → atom kırılımı; zayıf-konu seçici; en zayıf atomu vurgular.
- **Haftalık Plan** — 7 günlük takvim; reviewQueue (FSRS) + en zayıf konular + hafta sonu deneme.
- **Çalışma Modları** — havuz/mod seçimi.

**AI & Çözüm (AÇIK)**
- **AI Sohbet** — asistan; gerçek zayıf konular paneli.
- **Sokratik AI** — yönlendiren diyalog (cevabı vermez).
- **Çözüm Paylaş** — akran/öğretmen tartışması.

**Paneller & Roller (AÇIK)**
- **Öğrenci Paneli** — pano; hâkimiyet, θ, hedefe mesafe, KPI'lar.
- **Ödevlerim (öğrenci)** ↔ **Ödev Atama (öğretmen)** — ödev döngüsü; θ-tabanlı kişiye özel set; geciken "eksik" değil "bekliyor".
- **Sınav Sonuç** — TYT+AYT ders-ders net dökümü.
- **Veli Paneli** / **Öğretmen Paneli** — rol görünümleri (aynı Hüseyin verisi).
- **Ayarlar & Profil** — hedef, bildirim, görünüm, Premium upsell.
- **Bildirim Merkezi** — gerçek veriden bildirimler + boş durum.

**Oyunlaştırma & Sosyal (karışık)**
- **Lig** (AÇIK) — haftalık sıralama; "sen vs dün" hero birincil; **sıralama kullanıcı tarafından gizlenebilir** ("Sıralamayı gizle" + `siralamaGizli` tweak); `sakinMod`'da düşme bölgesi amber, rekabet kopyaları yumuşak.
- **1v1 Düello** — adil eşleşme.
- **Arkadaş Serisi** (AÇIK) — ortak seri.
- **Seri & Nudge / Seri Dondurma** — seri koruma + affedicilik.

**Onboarding & İş**
- **Giriş & Kayıt** — sekmeli kimlik ekranı; kayıt akışı Onboarding yerleştirmesine bağlanır. **Hesap Kurtarma** — 4 adımlı sakin şifre sıfırlama.
- **Ödeme** — checkout; "bugün ödeme alınmaz" güvencesi; `?rol=veli` destekli. **Çevrimdışı** — "İnternet gitti. Çalışman gitmedi."
- **Onboarding** — yerleştirme (catBankMat placement ladder).
- **İlk Hafta** — 7 günlük momentum yayı (pre-persona kurgu).
- **Abonelik / Paywall** (AÇIK) — Ücretsiz vs Premium; aylık/yıllık; kaygı-duyarlı ("7 gün ücretsiz, iptal et"). `?rol=veli` **veli-yüzü**: siz-dili, kanıt şeridi, "öğrenci fiyat baskısı görmez"; Veli Paneli ROI CTA'sı buraya bağlanır.

**Paylaşılan bileşenler**
- **KIRO Kenar** — sol nav rayı (öğrenci); container-query ile 64px ikon-only'e çöker. Veli/Öğretmen varyantları var.
- **KIRO Mastery Rozet** — hâkimiyet rozeti (badge, pct, trend); `dc-import` ile gömülür.

---

## Interactions & Behavior
- **Navigasyon:** her ekran ayrı sayfa; `<a href>` ile geçiş. Sayfalar arası **View Transitions** (fade+slide). Nav rayı (Kenar) çalışma ekranlarında sabit.
- **Kaygı-duyarlı oyunlaştırma:** kutlamalar ölçülü (dopamin küçük); "sen vs dün" (sıralama-baskısı değil); risk amber (alarm değil); davet dili.
- **Motorlar (sunucuda):** CAT/IRT madde seçimi + θ kestirimi; FSRS kart zamanlaması; BKT hâkimiyet güncelleme. İstemci yalnız sonucu gösterir.
- **Durumlar:** yükleniyor · boş · hata üçlüsü standart — kanonik örnekler + kopya formülleri `KIRO Durumlar.dc.html` spec ekranında (zıplamayan iskelet; yönlendiren boşluk; sakin amber hata + "sorun sende değil" güvencesi). Üretimde Skeleton/EmptyState/ErrorState bileşenlerine gömülür. Etkileşim geri bildirimleri ayrı: doğru/yanlış (Soru/Boss), win/lose overlay (Boss).
- **Responsive:** 390px'te tüm ekranlar overflowX=0. Telefon katmanı `@media(max-width:480px)`; nav 64px ikon-only; hit target ≥44px.
- **Erişilebilirlik:** `prefers-reduced-motion` saygısı; `:focus-visible` coral ring; ≥24px slayt metni.

## State Management
Her ekran yerel state tutar (prototipte React sınıf-bileşeni deseni: `state`, `setState`, `componentDidMount` ile veri yükleme). Örnek durumlar: seçili ders (Öğrenme Yolu), seçili atom-konu (Bilgi Atomları), fatura dönemi (Abonelik), boss savaş durumu (hp/lives/combo/phase), fatura/oynatma toggle'ları. Üretimde bu yerel state korunur; veri katmanı `import` → `fetch`.

## Design Tokens (özet)
Yukarıdaki "Design System" bölümü tam token listesidir. Öne çıkanlar: kâğıt `#F7F4EF`, mürekkep `#2A2433`, kenar `#ECE6DD`, mercan `#FF6F5C`, risk-amber `#C77A1E`, başarı `#1FB683`. Fontlar: Instrument Serif · Hanken Grotesk (tabular sayı) · IBM Plex Mono. İndigo yasak; emoji yok; ikonlar inline SVG.

## Assets
- **Fontlar:** Google Fonts — Instrument Serif, Hanken Grotesk, IBM Plex Mono, (bazı ekranlarda Bricolage Grotesque).
- **İkonlar:** tamamı bespoke inline SVG (harici dosya yok).
- **Görseller:** yer tutucu yok; gerçek ürün materyali (öğrenci fotoğrafı/logo) eklenmedi. `screenshots/flow/*.png` (bu pakette) = 19 ekranın güncel görüntüleri (sunum/demo için).

## Files (bu pakette)
- `README.md` — bu belge (kendine yeterli oryantasyon).
- **Üretim başlangıç dosyaları** (web + mobil ortak çekirdek için):
  - `tokens.ts` — platformdan bağımsız tasarım token'ları (React + React Native ortak tek kaynak).
  - `tokens.css` — aynı token'ların web CSS-değişkeni yansıması (`.k-paper` / `.k-dusk` tema sınıfları).
  - `types.ts` — kiro-data şekillerinin TypeScript tipleri + export→endpoint eşlemesi.
  - `BILESEN_ENVANTER.md` — çekirdek bileşen kütüphanesi haritası: paylaşılan DC'ler + desenden çıkarılacak bileşenler, props imzaları, ekran kullanımı, port sırası.
  - `ui-starter/` — 20 P0 yapı taşının React iskeleti: 15 temel + prototip DC'lerinden çıkarılmış 5 ek bileşen — SideNav (3 rol preset'i + bespoke ikon seti), MasteryBadge, StatusChip, ChatBubble, ConfettiDawn (tokens.ts'tüketir; ⚠️ test edilmemiş başlangıç kodu). Piksel referansı: `KIRO Bilesenler.dc.html`.
  - `api-client.ts` — tipli API client: `mock` (kiro-data.json'ı servisler) ↔ `live` (REST) tek konfigürasyonla; sunucu-otoriter uçlar (cevap doğrulama, CAT, FSRS) notlandı.
  - `openapi.yaml` — API sözleşmesinin makine-okur formu (Faz 4.1 çıktısı): 34 uç, backend contract-test + frontend zod üretimi buradan.
  - `ADR.md` — 7 mimari karar (ADR-000 retrofit dahil; **2026-07-04: hepsi kabul**, ADR-002 = Stripe birincil).
  - `CLAUDE_CODE_TALIMAT.md` — hedef repoda çalışacak geliştirici/Claude Code için giriş noktası ve iş sırası.
  - `kiro-data.json` — kiro-data'nın salt-veri anlık görüntüsü (mock/MSW/json-server için; getter'lar düz sayıya çevrildi).
  - `PORT_DURUM.md` — 42 ekran × 6 DoD işaretlenebilir takip tablosu + kalibrasyon ölçümü (2026-07-05: +3 yeni tasarım; Çözüm Paylaş MVP dışı).
  - `SPRINT1_SPEC.md` — kalibrasyon sprint'i: Button+Card+StatusChip + Giriş + Ödevlerim.
  - `SPRINT2_SPEC.md` — auth hunisi tamamlanması + kabuk: SideNav+MasteryBadge bağlama + Hesap Kurtarma + Onboarding + Öğrenci Paneli.
  - `SPRINT3_SPEC.md` — çekirdek döngü I: Soru Çözme + Neden Geri Bildirim + FSRS Tekrar (kanon düzeltme notlarıyla).
  - `SPRINT4_SPEC.md` — çekirdek döngü II: Adaptif Test + Harmanlanmış Deneme + Sınav Sonuç (IRT sunucuda; net-birincil).
  - `SPRINT5_SPEC.md` — Planlama: Haftalık Plan + Öğrenme Yolu + Bilgi Atomları + Çalışma Modları (⚠ /plan/week ucu sözleşmeye eklenecek).
  - `SPRINT6_SPEC.md` — Duygusal çekirdek I (ilk koyu ekranlar): Bugün/Şafak + Kutlama + Mola (dusk tema kurulumu; ⚠ mood ucu önerisi).
  - `SPRINT7_SPEC.md` — Duygusal çekirdek II (Grup 5 biter): Sınav Geri Sayım (2 varyant) + Başarımlar + Boss Savaşı (kırmızı istisnası ONAYLI; /boss/* uçları önerisi).
  - `SPRINT8_SPEC.md` — Sosyal & Motivasyon (Grup 6): Lig + Düello (⚠ ADR-003 çatışması: asenkron öneri) + Arkadaş Serisi + Seri Dondurma (/league /duel /friends /streak uçları önerisi).
  - `SPRINT9_SPEC.md` — AI & Destek (Grup 7): Sokratik AI + AI Sohbet (/ai/* uçları; kota↔abonelik) + İnteraktif Çözüm + Kaygı Ölçüm (araştırma flag'i; STAI lisansı ön koşul).
  - `SPRINT10_SPEC.md` — Ticari & Hesap (Grup 8): Abonelik (GET /plans) + Ödeme (⚠ Stripe Elements — ham kart formu taşınmaz) + Ayarlar (⚠ tema/vurgu seçici kanon çatışması + port ekleri) + Bildirim Merkezi.
  - `SPRINT11_SPEC.md` — Öğretmen & Veli (Grup 9): Öğretmen Paneli + Veli Paneli (⚠ KVKK veli↔çocuk bağlama akışı eksik) + Ödev Atama (/teacher/* + /parent/* uçları önerisi).
  - `SPRINT12_SPEC.md` — Platform (Grup 10, SON): Çevrimdışı (K1/K2 kapsam kararı) + Alan Kütüphanesi + Çözüm Paylaş (MVP dışı önerisi) + Mobil (referans, port edilmez). **39 üretim ekranının spec'i tamam.**
  - `scripts/kanon-lint.mjs` — CI kanon lint'i (alarm-kırmızısı/indigo/emoji/"eksik" = ihlal).
  - Yığın (ADR-000 kabul): **mevcut `kiro2` reposundaki `frontend/`'e retrofit** (Vite + React 18); Next.js monorepo İPTAL. Mobil (Expo) ihtiyacı doğunca `packages/` çıkarımı değerlendirilir.
- `kiro-data.js` — tek-kaynak veri modeli (üretim API şekillerinin kaynağı).
- `kiro-seed.js` — kiro-data'nın otomatik-üretilen senkron ikizi (`window.__KIRO`; her ekranın <head>'inde). ⚠️ kiro-data değişince yeniden üretilir.
- `CLAUDE.md` — kalıcı tasarım ilkeleri (Şafak kanonu, açık/koyu kuralı).
- `DEVIR-NOTU.md` — kapsamlı teknik durum: her ekranın veri bağlama durumu + bilinçli tasarım kararları (§1-22g).
- `ACCESSIBILITY.md` — sıkı-AA denetimi + açık/koyu kontrast kuralları.
- `KIRO2_DERIN_ANALIZ.md` — kanıt-temelli derin analiz raporu (yol haritasının kaynağı).
- `ROADMAP_DURUM.md` — yol haritasında uygulanan/kalan işler.
- `URETIM_YOL_HARITASI.md` — **üretim frontend'i + backend entegrasyonu için faz faz tam yol haritası** (Faz 0-6, ekran DoD'leri, mock→live geçiş sırası, altın kurallar).
- `USER_TESTING.md` — kaygı ölçüm test planı (pre/post durumluk kaygı).
- `screenshots/flow/` — 19 ekranın güncel PNG görüntüleri.
- Mobil referans: `KIRO2 Mobil.dc.html` (ana projede) — 8 telefon-çerçeveli kritik ekran (390pt, safe-area, ışık/koyu kuralı).

**Tam HTML prototipleri** (tüm `*.dc.html` ekranlar + `support.js` çalışma-zamanı) ana projededir. Piksel-hassas referans için projeyi indirin; iki otoriter spec: `KIRO2 Tasarim Sistemi.dc.html` (tasarım sistemi) ve `KIRO2 API Sozlesmesi.dc.html` (backend sözleşmesi).
