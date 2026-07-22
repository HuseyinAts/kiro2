# KIRO2 — Yeni Sohbet Devir Notu (güncel: 2026-07-21)

> **Yeni sohbete başlarken:** "design_handoff_kiro2/YENI_SOHBET_DEVIR.md dosyasını oku ve kaldığımız
> yerden devam et" demek yeterli. Projedeki en güncel durumun tek otoriter özeti budur.
> Çelişki durumunda öncelik: bu dosyanın KARARLAR bölümü > sprint spec'leri > prototip DC'leri.

---

## 1. Proje nedir, nerede duruyoruz
**KIRO2**: 17-19 yaş YKS öğrencisi için kaygı-duyarlı EdTech uygulaması. Bu proje ürünün
**frontend tasarım kaynağıdır**: ~45 ürün prototipi (`.dc.html`, kök dizinde) + `design_handoff_kiro2/`
devir paketi. Kod bu projede YAZILMAZ — `HuseyinAts/kiro2` GitHub reposunda (private, default branch
**master**) Claude Code ile yazılacak; bu proje spec + piksel referansı olarak kalır.

**Mevcut durum (2026-07-05):**
- 12 sprint spec'i yazıldı → **42 üretim ekranının TAMAMININ port spec'i hazır** (SPRINT1-12_SPEC.md;
  PORT_DURUM tablosu 2026-07-05'te 42'ye güncellendi, Çözüm Paylaş MVP-dışı işaretli).
- ADR'lerin hepsi kabul, openapi sözleşmesi sprint bulgularıyla topluca güncellendi.
- Bekleyen kullanıcı onayları tek turda kapatıldı (aşağıda KARARLAR).
- Kalan açık işlerden **veli↔çocuk KVKK bağlama akışı** (`KIRO2 Veli Baglama.dc.html`),
  **3DS bekleme durumu** (`KIRO2 Odeme.dc.html` içine, §6b), **öğretmenin öğrenci-özet sayfası**
  (`KIRO2 Ogretmen Ogrenci Ozet.dc.html`, §6c) ve **premium plan-yönetimi**
  (`KIRO2 Plan Yonetimi.dc.html`, §6d) tasarlandı (2026-07-05).
- **Tasarım kuyruğu boşaldı** — kalan açık işler tasarım dışı (hukuk/lisans/istatistik/kapsam kararı, §7).

## 2. Repo keşif bulgusu + ADR'ler (hepsi KABUL, 2026-07-04)
Repoda olgun `frontend/` var: Vite + React 18 + TS + Vitest + Playwright + MSW + axe + BackstopJS +
PWA/workbox; MUI + lucide-react + emotion kullanıyor (kanonla çelişir → kademeli sökülecek). Backend aynı repoda.
- **ADR-000:** mevcut repoya retrofit; Next.js monorepo İPTAL (en kritik karar).
- **ADR-001:** kendi JWT'miz (`/auth/*`).
- **ADR-002:** **Stripe birincil, iyzico yedek** (kullanıcı revizyonu — öneri iyzico'ydu, reddedildi).
- **ADR-003:** gerçek zamanlı yok; 15 sn polling. (Düello bu yüzden ASENKRON — bkz. KARARLAR.)
- **ADR-004:** push (FCM/APNs) web fazında ertelenir.
- **ADR-005:** Sentry + opt-in PostHog EU (KVKK).
- **ADR-006:** TanStack Query v5 + Zustand (repo react-query v3 → v5 upgrade).

## 3. design_handoff_kiro2/ paketi — içindekiler
| Dosya | Ne işe yarar |
|---|---|
| `README.md` | Kendine yeterli oryantasyon (paket + prototipler + yığın) |
| `URETIM_YOL_HARITASI.md` | 6 fazlı üretim planı |
| `CLAUDE_CODE_TALIMAT.md` | Repoda çalışacak Claude Code'un giriş noktası: `frontend/src/kiro/{tokens,types,api,ui,screens}` yerleşimi, yasak bağımlılıklar (MUI, lucide, emotion, react-hot-toast), tema kuralı, sprint sırası, tuzaklar |
| `ADR.md` | 7 karar — hepsi kabul |
| `openapi.yaml` | ~50 ucun makine-okur sözleşmesi; kanon şemaya gömülü (motorlar sunucuda, `dogru` yalnız answer yanıtında, "eksik" yok, billing veli yüzü). 2026-07-04 toplu güncelleme + 2026-07-05 /parent/link uçları İŞLENDİ |
| `PORT_DURUM.md` | 39 ekran × 6 DoD takip tablosu + kalibrasyon ölçümü (Claude Code dolduracak) |
| `SPRINT1..12_SPEC.md` | Ekran-ekran port spec'leri (aşağıda §4 özet) + her birinde "Erişilebilirlik satırları" bölümü (B10, 2026-07-21) |
| `BREAKPOINT_SPEC.md` | 4 bant (≤480 · 481-767 · 768-1199 tablet · ≥1200) yerleşim kuralları + prototip .r* sınıf haritası + QA matrisi (B8, 2026-07-21) |
| `scripts/kanon-lint.mjs` | CI lint: alarm-kırmızısı/indigo hex + emoji + "eksik" = ihlal (exit 1); koyu ekranda #6B6478 = uyarı; **`// kanon-allow: boss-arena`** dosya istisnası (onaylı). **2026-07-21 motion/ikon kuralları:** guard'sız hareket · `transition:all` · layout animasyonu · stok ikon/UI kitaplığı importu = ihlal; 600ms+ süre = uyarı (`kanon-allow: kutlama` istisnası) |
| `ui-starter/` (20 bileşen) | Prototiplerden çıkarılmış başlangıç kodu — Button, Card, StatusChip, SideNav (3 rol preset'i), MasteryBadge (eşikler 40/65/85), ChatBubble, ConfettiDawn (+useReducedMotion) vb. TEST EDİLMEMİŞ — Faz 2 kalite kapısından geçecek |

## 4. Sprint spec'leri — grup haritası + her birinin kritik notu
Format hepsi aynı: birebir kopya tabloları, durum makineleri, ⚠ kanon düzeltmeleri (prototip
hataları — porta taşınmaz), veri bağlama, DoD notları, ölçüm (süre → PORT_DURUM kalibrasyonu).
1. **S1 · Kalibrasyon:** Button+Card+StatusChip + Giriş & Kayıt + Ödevlerim. Ders renkleri açık palet: mat #3B82F6 fiz #8B5CF6 kim #E0593F biy #1FB683 tur #F59E0B.
2. **S2 · Auth+kabuk:** Hesap Kurtarma (3 adım) + Onboarding (misafir yerleştirme — sorular üretimde /cat/next'ten, θ kayıtta taşınır) + Öğrenci Paneli.
3. **S3 · Çekirdek döngü I:** Soru Çözme (odak modu, localStorage kalıcılık) + Neden Geri Bildirim (#991B1B/#FEE2E2 → terracotta) + FSRS Tekrar (4 derece; aralık etiketleri sunucudan).
4. **S4 · Çekirdek döngü II:** Adaptif Test (TÜM IRT sunucuda; "Emin değilim" = secim:null) + Harmanlanmış Deneme (harmanlı/bloklu pedagojik toggle üretimde KALIR) + Sınav Sonuç (net-birincil; "yalnız yön göstergesi" etiketi asla kalkmaz).
5. **S5 · Planlama:** Haftalık Plan (/plan/week eklendi) + Öğrenme Yolu + Bilgi Atomları + Çalışma Modları (Eşleştirme+Hız UI'ları yok — açık).
6. **S6 · Duygusal çekirdek I (İLK KOYU):** Bugün/Şafak hub (kanon gökyüzü gradyanı birebir; koyu-parlak ders paleti AYRI: mat #5B8DEF fiz #A77BFF kim #E25A72 biy #2DD4A7 tur #FFB347) + Kutlama (4 tür kopya tablosu) + Mola (16s kutu-nefesi; hata kutusu asla).
7. **S7 · Duygusal çekirdek II:** Sınav Geri Sayım (2 varyant) + Başarımlar + Boss Savaşı (kırmızı istisnası ONAYLI; HP/kombo sunucuda).
8. **S8 · Sosyal:** Lig (sakinMod + sıralama gizleme = ürün kimliği) + Düello (ASENKRON) + Arkadaş Serisi + Seri Dondurma (AGRESİF nudge anti-örnek — taşınmaz).
9. **S9 · AI & Destek:** Sokratik AI (mod sabit; merdiven tespiti sunucuda) + AI Sohbet + İnteraktif Çözüm + Kaygı Ölçüm (ARAŞTIRMA aracı — feature-flag; STAI lisansı ön koşul).
10. **S10 · Ticari & Hesap:** Abonelik (fiyat/kota GET /billing/plans'ten) + Ödeme (**ham kart formu taşınmaz → Stripe Elements + appearance eşlemesi**; başarı CTA → Bugün/Veli Paneli) + Ayarlar (tema+vurgu seçici KALDIRILDI; PORT EKLERİ: sakin mod, sıralama gizle, geri sayım tercihi, yoğunluk) + Bildirim Merkezi.
11. **S11 · Öğretmen & Veli:** Öğretmen Paneli ("Ödev oluştur" link düzeltmesi; dikkat kartları amber) + Veli Paneli + Ödev Atama (kişiye özel θ zorluk varsayılan AÇIK; kaygı-duyarlı varsayılanlar kutusu birebir).
12. **S12 · Platform (SON):** Çevrimdışı (K1/K2) + Alan Kütüphanesi + Çözüm Paylaş (MVP DIŞI) + Mobil (PORT EDİLMEZ — 390px QA referansı).

## 5. ✅ KARARLAR (kullanıcı onaylı — spec'lerdeki "karar bekliyor" notlarını geçersiz kılar)
**2026-07-04 (ilk tur):** ADR'ler kabul (002 Stripe'a revize) · Boss kırmızıları `kanon-allow: boss-arena` ile istisna.
**2026-07-04 (ikinci tur — 8 karar):**
1. **Kopyalar HEPSİ KABUL** — "Seriyi koru" (S2) · FSRS boş durumu "Bugün tekrar yok — eğrin sağlıklı." (S3) · AI ErrorState "Koç şu an toparlanıyor…" (S9) · ödeme reddi kopyası (S10) · tüm boş-durum kopyaları (S8/S11).
2. **Düello ASENKRON** (ADR-003 uyumlu; rakip kendi hızında, sonuç poll ile). Güçler (50:50, Süre Dondur) MVP'de YOK.
3. **Ayarlar: tema seçici + vurgu rengi seçici İKİSİ DE KALDIRILDI** (yerine bilgi satırı).
4. **Geri Sayım: varsayılan kaygı-nötr** + Ayarlar tercihi + PostHog ölçümü.
5. **Mood: POST /me/mood KABUL** (veliye asla gösterilmez).
6. **Vision/fotoğraf MVP'de gizli**, Faz 4.5'te /ai/vision ile açılır.
7. **Çevrimdışı K1/K2** (K1 MVP = bant + cevap kuyruğu + FSRS önbelleği; tam sayfa + paketler K2).
8. **Çözüm Paylaş MVP DIŞI** — girecekse öğretmen-onaylı pilot.
9. Delege küçük kararlar: 7 gün tekrar yükü → /review/due'ya projeksiyon alanı · harman bileşimi SUNUCUDA · AI analiz metni /exams/{id} yanıtında hazır · Kutlama CTA'ları şimdilik hepsi Bugün'e · Alan Kütüphanesi konu satırı → Bilgi Atomları · interaktif içerik uç olarak kalır.
**2026-07-21 (Şafak craft):** koyu-parlak Kimya **#FF6B6B → #E25A72** (kızıl-gül) — marka corali #FF6F5C ile uzaktan çakışıyordu (SAFAK_CRAFT_LISTESI A1, KULLANICI ONAYLI). Senkron: kiro-data/seed (kök+handoff) + kiro-data.json + tokens.ts/css + README palet tablosu + DEVIR-NOTU + SPRINT6_SPEC + Safak Mimari DC + Mobil DC.
**2026-07-21 (Onboarding ton kopyaları — KULLANICI ONAYLI):** Adım 1 kaygı-tonu metinlerinin tamamı kabul: soru ("Sınavı düşününce şu an neredesin?") · 3 seçenek (Kaygı ağır basıyor / Değişken — güne göre / Genelde sakinim) · 3 serif yanıt · 3 payoff satırı · kilit satırı ("veline ya da öğretmenine gösterilmez"). Kanon gereği artık BİREBİR taşınır (değişiklik = yeni onay).
**2026-07-21 (P2 kararları — KULLANICI: "Decide for me" → önerilen uygulandı):** ① **Ses/haptik (B4):** web MVP TAMAMEN SESSİZ (kütüphane/sınıf bağlamı — beklenmedik ses = utanç/kaygı); haptik MOBİL (Expo) fazında yalnız 2 anda (kutlama girişi tek yumuşak vuruş + FSRS derece seçimi hafif tık; Ayarlar'dan kapatılabilir, varsayılan açık); ses MVP'ye girmez — mobil fazı sonunda kullanıcı testiyle yeniden değerlendirilir. ② **E-posta/bildirim kapsamı (B9):** veli haftalık özeti + bildirim KOPYA SİSTEMİ (`KIRO2 Eposta Bildirim.dc.html`); kurallar: günde ≤ 1 push · sessiz 21:00–09:00 · sınav haftası otomatik sessiz · seri KAYBI BİLDİRİLMEZ · "eksik"/ünlem/sayac-baskısı yasak · formul = gerçek durum + küçük yapılabilir adım; veli e-postasında sıralama/kıyas yok + gizlilik satırı zorunlu + veri yoksa gönderilmez.
**2026-07-21 (S11 kapsam — "devam" → önerilen uygulandı):** Öğretmen "İlk sınıfını kur" akışı MVP'ye GİRER — minimal kod-temelli kurulum (`KIRO2 Sinif Kurulum.dc.html`): 3 adım (ad + düzey/alan segmentleri → süresiz 6 haneli katılım kodu + kopyala/paylaş + kaygı-duyarlı sınıf varsayılanları kartı → hazır; boş liste "başlangıçtır" kopyası). Öğrenci ucu: Ayarlar → Sınıfa katıl. openapi: `POST /teacher/classes` + `POST /me/class/join` (+kod rotate notu). §7 madde 4 kapandı.
**2026-07-21 (Şafak craft kapanış — tümü KULLANICI ONAYLI):** tuğla tanımı = ~15 dk'lık günlük plan bloğu (hero+progress aynı birim; sıfır-durum "Bugünün tuğlaları yerinde.") · mantra havuzu 5 cümle, gün-seed'li rotasyon ("Sınav bir günü ölçer…" / "Küçük adım, her gün." / "Dünkü senden bir adım önde." / "Acele etme; istikrar yetenektir." / "Bu yol tuğla tuğla örülür.") · hub'a ilişkililik satırı "Elif de bugün çalıştı" (baskısız: sayı/CTA/kıyas yok; üretimde arkadaş akışından) · SAFAK_CRAFT_LISTESI.md KAPANDI (tüm A-F uygulandı; denetim listesi dosyada).

## 6. 2026-07-05'te yapılan: Veli Bağlama tasarımı
`KIRO2 Veli Baglama.dc.html` (yeni DC — S11'in en kritik açık işi):
- **Veli akışı 4 adım:** 6 haneli kod (çocuğun cihazında Ayarlar → Veli bağlantısı; 10 dk geçerli)
  → KVKK açık rıza + yan yana "Görürsünüz / Asla görmezsiniz" listeleri → "Şimdi söz {çocuk}'te"
  bekleme (çocuk onayı) → tamam. Haftalık e-posta özeti isteğe bağlı checkbox, varsayılan KAPALI.
- **Öğrenci onay ekranı** (`taraf=ogrenci` prop'u): aynı şeffaflık listeleri çocuk perspektifiyle;
  "Şimdi değil" = bildirimsiz ret. İlkeler: çift taraflı onay · sohbet/mood/cevap detayı/arkadaş
  etkileşimi VELİYE KAPALI · rıza tek dokunuşla geri çekilir.
- Tweaks: `taraf` (veli/ogrenci) + `baslangicAdimi` (kod/riza/bekle/tamam) ile tüm durumlar gezilir.
- openapi'ye eklendi: `POST /parent/link {kod}` · `POST /parent/link/consent` (+DELETE = rıza geri
  çekme, tek adım) · `POST /me/parent-link/approve`.
- **Bekleyen:** KVKK Aydınlatma Metni'nin hukuk incelemesi (metin placeholder link).

## 6b. 2026-07-05'te yapılan: 3DS bekleme durumu (S10)
`KIRO2 Odeme.dc.html` içine yeni **faz=3ds** eklendi (yeni DC değil — spec "Ödeme'ye eklenecek" diyordu):
- **Akış:** form → (CTA) → 3ds bekleme → onay ise başarı / ret ise form + amber kutuda onaylı
  ret kopyası ("Kart bu sefer onaylanmadı — bankan engellemiş olabilir; başka kartla dene ya da bize yaz.").
- **Kart içeriği:** dawn-aksan spinner halkası + kalkan ikonu · "Bankan doğrulama istiyor."
  (Instrument italic) · açıklama: bildirim/SMS onayı, "onay gelince burası kendiliğinden ilerler" ·
  3 adımlı ilerleme: Kart bilgisi alındı ✓ (yeşil) → Banka onayı ● (aksan) → Deneme başlar (soluk) ·
  not pili "Genelde bir dakikadan kısa sürer — bu sayfa açık kalsın." · 5 sn sonra fallback:
  "Bildirim gelmedi mi?" → "Doğrulama penceresini yeniden aç" / "Farklı kartla dene" · kilit satırı
  "Doğrulama bankanın kendi güvenli sayfasında (3-D Secure) yapılır; şifren bize ulaşmaz."
- Spinner `prefers-reduced-motion` guard'lı; zamanlayıcılar (5 sn fallback / 12 sn sonuç)
  prototip SİMÜLASYONUdur — üretimde Stripe challenge dönüşü beklenir, ek uç yok.
- Tweaks: `baslangicFazi` (form/3ds/tamam) + `bankaSonucu` (onay/ret) ile tüm durumlar gezilir.
- openapi: `/billing/trial` yanıtı `{ durum: aktif | dogrulama_gerekli, clientSecret?, … }` oldu.
- SPRINT10_SPEC §3DS bloğu ve açık-nokta listesi güncellendi.

## 6c. 2026-07-05'te yapılan: Öğretmenin öğrenci-özet sayfası (S11)
`KIRO2 Ogretmen Ogrenci Ozet.dc.html` — yeni DC; rota `/ogretmen/ogrenci/:id`, SALT-OKUR.
- **Yapı:** SideNav (öğretmen, active=students) · topbar ("← Panel" + "Salt-okur görünüm" pili) ·
  kimlik bandı + tek CTA "Bu öğrenciye ödev ata" · durum kartı (risk = amber + "öğrenciye bayrak
  gösterilmez" satırı / sağlıklı = yeşil sakin) · KPI ×4 (TYT net+trend · hâkimiyet % · seri ·
  ödev tamam/toplam + "bekliyor") · ders hâkimiyeti (AÇIK palet) · "Desteğe hazır konular" amber
  chip'leri · atanan ödevler (Tamam/Bekliyor/Açık) · son deneme (TYT/AYT etiket standardı +
  "yalnız yön göstergesi" dipnotu) · haftalık aktivite (pasif #FFD3C4) · **öğrenci gizliliği
  kutusu** (sohbet+duygu inmez · tekil cevap yok · risk yalnız yetişkine — kanonu öğreten yüzey).
- Tweaks: `ogrenci` (saglikli=Hüseyin / riskli=Emre Şahin, 9 gün girişsiz) + accent; `?ogrenci=riskli` URL'den de.
- Öğretmen Paneli linkleri güncellendi: tablo satırları → bu DC, dikkat kartları → `?ogrenci=riskli`
  (artık Öğrenci Paneli'ne sızmıyor — spec'teki AÇIK NOKTA kapandı).
- openapi: `GET /teacher/student/{id}/summary` eklendi (gizlilik notuyla). SPRINT11_SPEC'e A2 bölümü eklendi.

## 6d. 2026-07-05'te yapılan: Premium plan-yönetimi (S10)
`KIRO2 Plan Yonetimi.dc.html` — yeni DC; `/premium` rotası plan=premium ise bunu render eder
(Abonelik satış sayfası dokunulmadı). Tek sütun max 680px, paper.
- **Bloklar:** durum pili (Aktif yeşil · Deneme/İptal amber — iptal bile alarm değil) · serif
  "Planını yönet." · plan kartı (fiyat + yenileme satırı "e-postayla hatırlatırız; sessizce ücret
  alınmaz" + Visa •••• 4242 + "Kartı değiştir") · fatura geçmişi (Ödendi chip + Makbuz linki;
  deneme boş durumu: "Henüz fatura yok — deneme sürüyor, bugün ödeme alınmadı.") · **iptal TEK
  adım** (onay diyaloğu yok → amber bilgi bandı + "Geri aç" — geri-al modeli; deneme iptali:
  "hiç ücret alınmaz").
- Tweaks: `durum` (aktif/deneme/iptal) · `fatura` (yillik/aylik) · `rol` (veli/ogrenci) — URL
  paramlarıyla da.
- openapi: `GET /billing/subscription` + `POST /billing/subscription/reactivate` eklendi;
  DELETE açıklaması "erişim dönem sonuna kadar açık" oldu. SPRINT10_SPEC'e A2 bölümü eklendi.

## 7. ⏳ KALAN AÇIK İŞLER (öncelik sırasıyla — hiçbiri tasarım işi değil)
1. KVKK Aydınlatma Metni hukuk incelemesi (§6).
2. STAI ölçek lisansı + etik kurul + araştırma verisi backend'i (S9 — flag ön koşulu).
3. "%48 daha uzun seri" istatistiğinin kaynağı (S8 — doğrulanana dek yayın kopyasından çıkar).

## 8. Kanon (her işte geçerli — kök CLAUDE.md'den; kanon-lint CI'da zorlar)
- **Tema ekran TÜRÜdür:** çalışma/odak/analitik = paper (açık, #F7F4EF sıcak kâğıt, mürekkep #2A2433)
  · duygusal/hub/kutlama = dusk (koyu şafak). Asla karışmaz, asla kullanıcı toggle'ı değil.
- Sıkı-AA yalnız açık zeminde: küçük gri #6B6478 · amber metin #9A5D0D · coral metin #C2452B.
  Koyu ekranda #6B6478 KULLANILMAZ (dusk ikincil: #B6A6C4 vb.).
- Risk = sıcak amber, alarm-kırmızısı YOK (tek istisna: boss arena, dosya-kapsamlı allow) ·
  indigo YOK · emoji YOK (bespoke SVG) · tüm sayılar tabular-nums · geciken ödev = "bekliyor",
  "eksik" hiçbir katmanda yok · serif (Instrument) his/mantra, Hanken Grotesk işlev · kopyalar
  prototipten BİREBİR (değişiklik = kullanıcı onayı) · sıralama-baskısı yerine "sen vs dün".
- **Motorlar (θ/IRT/FSRS/BKT) SUNUCUDA** — istemci simülasyonları prototip aracıdır, taşınmaz;
  `dogru` yalnız answer yanıtıyla iner.
- Animasyonlar `prefers-reduced-motion` guard'lı; konfeti = ConfettiDawn bileşeni.

## 9. Otoriter referanslar (bu projede)
`KIRO2 Tasarim Sistemi.dc.html` (görsel) · `KIRO2 API Sozlesmesi.dc.html` (veri — openapi.yaml
makine-okur eşi) · `KIRO Bilesenler.dc.html` (P0 piksel) · `KIRO Durumlar.dc.html` (skeleton/boş/
hata standardı) · `KIRO Safak Mimari.dc.html` (şafak dili kanonu) · **kanon üçlüsü (P0, 2026-07-21):** `KIRO Motion Kanonu.dc.html` (hareket dili) · `KIRO Illustrasyon Sistemi.dc.html` (spot gramer) · `KIRO Veri-Viz.dc.html` (grafik grameri) · kök `CLAUDE.md` (kanon) ·
`design_handoff_kiro2/` (devir paketi) · `screenshots/flow/` 19 PNG (görsel regresyon).
Prototip DC'leri kök dizinde `KIRO2 <Ekran>.dc.html` (bazıları `KIRO <Ad>.dc.html`) adlarıyla.

## 10. Sıradaki adımlar
**Bu projede (tasarım): P0 TAMAMLANDI (2026-07-21, TASARIM_DENETIM.md §E).**
1. ✅ `KIRO Motion Kanonu.dc.html` (P0-1) — süre skalası (anlık 90 · hızlı 160 · standart 240 · sahne 400 · kutlama 640ms) · easing ailesi (doğuş cubic-bezier(0.2,0,0,1) varsayılan · veda 0.4,0,1,1 · geçiş 0.45,0,0.15,1 · kutlama-spring) · stagger 48ms (max 6 öğe; yön hep aşağıdan yukarı 10-14px) · şafak imza geçişi (alt kenardan doğan ışık süpürmesi — dekoratif, rota başına bir kez) · mikro-etkileşim = ışık/renk (hover kalkışı anti-örnek olarak gösteriliyor) · spring YALNIZ dusk kutlamada · reduced-motion (CSS no-preference bloğu + WAAPI matchMedia guard + döngüler durur). Canlı WAAPI demoları (süpürme/stagger/spring) + RM simülasyon toggle'ı. ⚠ Giriş animasyonunun baz durumu opacity:1 kalır (capture kuralı) — WAAPI/fill:backwards ile geçici uygulanır.
2. ✅ `KIRO Illustrasyon Sistemi.dc.html` (P0-2) — spot illüstrasyon grameri.
3. ✅ `KIRO Veri-Viz.dc.html` (P0-3) — eksen dili, dolgu/çizgi, boş-veri hali, anotasyon (paper + dusk; "sen vs dün", amber risk, pasta yasak).
4. ✅ kanon-lint'e motion/ikon kuralları eklendi: guard'sız hareket (dosyada animation/transition/WAAPI var ama prefers-reduced-motion yok) = İHLAL · `transition:all` = İHLAL · layout animasyonu (width/height/top/left/margin/padding) = İHLAL · 600ms+ süre = UYARI (`kanon-allow: kutlama` dosya istisnası) · stok ikon/UI kitaplığı importu (lucide-react, react-icons, @mui, @emotion, @heroicons, font-awesome, react-hot-toast) = İHLAL.
Üç kanon DC galeriye eklendi (Tasarım Sistemi · Araştırma & Sistem № 34-36).
**Sıradaki: P1** — 42 ekrana TASARIM_DENETIM.md §D craft pass'ı (sprint sırasıyla; ekran başına imza anı + hiyerarşi düzeltmesi) · yaşayan gökyüzü · skeleton kişiliği · onboarding ark · breakpoint spec · erişilebilirlik satırları.
**P1 craft pass ilerleme (2026-07-21):** ✅ S1 — `KIRO2 Giris` (zemin soğuk gri #F1F2F6 → sıcak kâğıt #F7F4EF; imza anı: kart üstünde şafak-ufku spot illüstrasyonu "giriş = gün başlıyor"; #9A93A5 küçük metin → #6B6478; serif h1 31px + negatif letter-spacing) · `KIRO2 Odevlerim` (imza anı + hiyerarşi: header köşesindeki özet metrik → hero sayı "~N dk / bugün kalan · N açık ödev" + mini ufuk motifi; jenerik boş-durum ikonu → şafak-ufku spot illüstrasyonu). İkisinde de indigo-yakını accent seçeneği #3B6FD4 → altın #E8A33D (tweaks). Kopyalar DEĞİŞMEDİ (yalnız hero'daki "bugün kalan" etiketi yeni — faktüel). ✅ S2 — `KIRO2 Hesap Kurtarma` (Giriş aile dili: sıcak kâğıt zemin + şafak-ufku illüstrasyonu; adım-eyebrow + küçük griler #6B6478; şifre-göster butonuna aria-label; karşılanmamış şifre kuralı metni #6B6478) · `KIRO2 Onboarding` (KANON İHLALLERİ temizlendi: CTA hover **indigo #4338CA** → brightness; confetti soğuk mavi/pembe/mor → dawn paleti; seviye rampası kırmızılı #FCA5A5 → şeftali #FFC59B; şık hover #FAFBFF → #FFF8F2; paper'da overshoot'lu kpop spring → doğuş easing'i, Motion Kanonu §04; connector #E2E5EB → #ECE6DD) · `KIRO2 Ogrenci Paneli` (imza anı: selamlama Instrument Serif italik; soğuk slate #334155 → #4A4456; onaylı kopya "Streak'i koru" → **"Seriyi koru"** (KARARLAR #1); KPI/yoğunluk/mobil kancalarına DOKUNULMADI — `[style*='font-size: 30px']` seçicisi korunur). Onboarding+Hesap Kurtarma+Panel'de accent seçeneği de #E8A33D'ye çekildi. **Flow görselleri tazelendi:** giris/odevlerim/hesap-kurtarma/panel PNG (22f reçetesi) + handoff kopyaları. ✅ S3 — `KIRO2 Soru Cozme` (konu çipi #EAF0FC/#3B6FD4 → mat ders paleti #EFF6FF/#3B82F6; "Bu soruyu atla" #A39BAA → #6B6478; basma tepkisi translateY → scale 0.985; **varsayılan accent #3B6FD4 → coral**) · `KIRO2 Neden Geri Bildirim` (S3 spec düzeltmesi UYGULANDI: alarm-kırmızısı ailesi #FEF2F2/#FECACA/#FCA5A5/#991B1B/#FEE2E2 → terracotta #FCEDE8/#F0A593/#9A3520/#FBE3DA — banner + yanlış şık + "neden yanlış" bloğu; bir indigo hover #4338CA daha → brightness) · `KIRO2 FSRS Tekrar` (confetti → dawn paleti; DONE overlay kpop overshoot → doğuş; #334155 → #4A4456; "kırmızılar bugün tekrar istiyor" → '"Bugün" etiketliler tekrar istiyor' — kanonda kırmızı yok). soru-cozme/neden/tekrar PNG'leri de tazelendi. ✅ S4 — `KIRO2 Adaptif Test` (yalnız yüzey, CAT motoru DOKUNULMADI: soğuk hover'lar #F3F5F8/#F6F7F9 → #F2EEE7; ders çipi #2563EB → #3B82F6; #334155 → #4A4456; "Zayıf" rozet zemini rose rgba(244,63,94) → terracotta rgba(224,89,63)) · `KIRO2 Harmanlanmis Deneme` (`mode` tweak'i state'e bağlı değildi — düzeltildi `_mode()`; HARMANLANMIŞ kartının silik beyazımsı kenarı → #F2CFC2) · `KIRO2 Sinav Sonuc` (Yanlış KPI zemini alarm-ailesi #FEF2F2 → #FCEDE8; Boş KPI soğuk #F1F4F7 → #F2EEE7; TYT etiketi soğuk slate #EEF3F8/#5A6B82 → ders mavisi #EFF6FF/#3B82F6; amber metrik #B45309 → sıkı-AA #9A5D0D; net-birincil hiyerarşi zaten §22g'den doğru). Üçünde accent seçenekleri coral/şeftali/altın'a çekildi. S4 ekranlarının flow PNG'si yok → görsel tazeleme gerekmedi. ✅ S5 — `KIRO2 Haftalik Plan` (**sol-kenar-aksan kalıbı kaldırıldı** — AI-slop/§D; yerine tag satırında renkli nokta; BUGÜN kart vurgusu statik Pzt'ye çakılıydı, canlı `buHafta` bugün'üne bağlandı — badge/vurgu artık aynı günü gösterir; haftalik-plan.png tazelendi) · `KIRO2 Ogrenme Yolu` (ünite banner rengi #3B6FD4 → #3B82F6; FETHEDİLDİ etiketi #B45309 → #9A5D0D; **kbounce/kring/kfloat için eksik reduced-motion guard'ı eklendi** — SPRINT5 spec'in "porta eklenir" notu prototipte de kapandı) · `KIRO Bilgi Atomlari` (pulseA'ya aynı reduce guard'ı) · `KIRO Calisma Modlari` (Test modu #3B6FD4 → #3B82F6). Haftalık Plan + Öğrenme Yolu accent seçenekleri dawn üçlüsüne. Sıradaki: S6 — İLK KOYU grup (Bugün/Şafak · Kutlama · Mola); koyu ekranlarda sıkı-AA düzeltmesi YAPILMAZ kuralına dikkat.
✅ S6+S7 (KOYU grup — renk kanonu zaten temizdi, grep denetimi: #6B6478/indigo/soğuk sızıntı YOK; iş = eksik reduced-motion guard'ları): `KIRO Safak` + `KIRO2 Kutlama` + `KIRO2 Sinav Geri Sayim` + `KIRO2 Basarimlar` + `KIRO2 Boss Savasi` → blanket `@media (reduce) { * { animation:none } }` eklendi (döngüler durur — Motion Kanonu §05). **`KIRO2 Mola` HEDEFLİ guard:** nefes-küpü metin sıralaması (c1-c4 opacity crossfade) İÇERİKTİR — reduce'ta kalır; yalnız twinkle/drift/breatheOrb/breatheRing `[style*=ad]` seçicisiyle durdu (blanket olsaydı 4 nefes metni üst üste binerdi). Boss confetti soğuk mavi/pembe/mor → dawn paleti. Görsel değişiklik yok → bugun/kutlama/geri-sayim/basarimlar/boss PNG'leri GEÇERLİ kaldı. ✅ S8: `KIRO2 Lig` (non-sakin geri sayım kutusu alarm-kırmızısı #FEF2F2/#FBD5D5 → terracotta #FCEDE8/#F0A593; demote çizgisi aynı; risk etiketi koyu kartta #FB7185 → #FFB347; SEN satırı soğuk #F5F6FF → #FFF3EE; podyum gümüş #E2E8F0 → #EAE3D9; ölü kfPulse keyframe silindi; **Instrument Serif kullanılıyordu ama yüklenmiyordu → font linke eklendi**) · `KIRO2 Duello` (kfRing gül-kırmızısı → terracotta rgba(232,131,107); rakip avatar + kayıp ikonu #7F1D1D → #9A3520; #FB7185 ailesi → #E8836B; berabere kutusu soğuk slate → beyaz-alfa; konfeti soğuk mavi/pembe/mor → dawn paleti; blanket reduce guard eklendi; **KARARLAR #2 uygulandı: MVP-dışı Güçler çipleri (50:50, Süre Dondur) kaldırıldı** → yerine asenkron-karar satırı "Rakip kendi hızında çözer — puanlar tur sonunda karşılaştırılır."; kpop spring dusk-kutlama istisnası olarak KALDI) · `KIRO2 Arkadas Serisi` (**KANON İHLALİ: "Arkadaş ekle" hover indigo #4338CA → brightness**; görev etiketi menekşe #F5F3FF → #FFF3EE; ⏳ emoji → saat SVG; transition:all ×4 → spesifik; boş kfloat span'ı silindi; kpop ölü keyframe silindi + reduce guard; çalıştı-chip #15803D/#DCFCE7 → standart #17936B/#D1FAE5; imza anı: alt bilgi kutusu Instrument Serif italik mantra) · `KIRO2 Seri Dondurma` (soğuk connector #E2E5EB → #ECE6DD, kesikli #D9DEE6 → #DED6C8; ölü glyph kodu temizlendi; imza anı: "Kötü bir gün, ayların emeğini silmesin." serif italik; buz-mavisi dondurma semantiği BİLİNÇLİ korundu — buz = soğuk; AGRESİF nudge anti-örneği alarm-kırmızısı + emojisiyle BİLİNÇLİ kaldı, taşınmaz). 4 ekranda accent seçenekleri [coral, altın #E8A33D, teal] olarak tekilleştirildi. lig.png tazelendi (+handoff kopyası); duello/arkadas/seri-dondurma flow PNG'si yok. ✅ S9 (Kaygı Ölçüm araştırma yüzeyi — grep temiz, dokunulmadı): `KIRO2 Sokratik AI` (**İNDİGO ×3 temizlendi:** mod pili metni + gönder butonu hover'ı + 'yönlendiren soru' tagFg'leri #4338CA → #C2452B/brightness; 'Çözümü göster' border/hover #F1D5D5/#FEF2F2 → terracotta #F0A593/#FCEDE8; kopya onarımı: 'Selam Hüseyin Doğrudan' → 'Selam Hüseyin! Doğrudan' — emoji sökümünden kalan kayıp noktalama) · `KIRO2 AI Sohbet` (kart hover'ları soğuk #D7DCE3/#FCFCFD → #E0D8CC/#FBF9F4 ×4; fotoğraf butonu hover #EAEEF2 → #ECE6DD; 'dünkü yanlışlar' chip #FEF2F2 → #FCEDE8; fiz-moru #F5F3FF/#8B5CF6 kartı ders-rengi çifti olarak KORUNDU) · `KIRO2 Interaktif Cozum` (**İNDİGO ×2:** slider thumb gölgesi rgba(79,70,229) → rgba(224,89,63) + 'Kontrol et' hover → brightness; eksenler #E2E5EB → #D9D2C6, svg zemini #FAFBFC → #FBF9F6, track #ECE6DD; tepe chip #FEF2F2 → #FCEDE8; KEŞFET kutusu menekşe (#F5F3FF/#DDD6FE/#4C1D95) → altın-dawn (#FBF0DE/#F2D9AC/#4A4456); **ders-rengi düzeltmesi: 'AYT MATEMATİK' eyebrow fiz-moru #8B5CF6 → mat #3B82F6**). Üçünde de accent seçenekleri [coral, altın, teal]. ✅ S10 (Abonelik grep temiz — dokunulmadı): `KIRO2 Odeme` (S1'deki aynı hata: zemin soğuk gri #F1F2F6 → sıcak kâğıt #F7F4EF, radial uç dahil; küçük griler #9A93A5 ×3 → #6B6478; accent seçeneğinde indigo-yakını #3B6FD4 → [coral, altın, teal]; odeme.png tazelendi +handoff) · `KIRO2 Ayarlar` (**KARARLAR #3 UYGULANDI: tema seg-control + vurgu-rengi swatch'ları KALDIRILDI → bilgi satirlari** — tema: güneş ikonlu "Otomatik — ekran türüne göre" pili; vurgu: coral nokta + "Şafak mercanı", desc "Marka şafak tonu — uygulamanın kimliği."; themeBtns/accentSw logic'te atıl ama zararsız kaldı; transition:all da bununla gitti) · `KIRO2 Bildirim Merkezi` (timestamp #A39BAA → #6B6478; fiz-moru kategori çifti #F5F3FF/#8B5CF6 ders-rengi olarak KORUNDU). Sıradaki: S11 (Öğretmen Paneli · Veli Paneli · Ödev Atama · Veli Baglama · Ogretmen Ogrenci Ozet · Plan Yonetimi — son dördü yeni/temiz olabilir, grep'le doğrula) sonra S12 (Çevrimdışı · Alan Kütüphanesi; Mobil referans, Çözüm Paylaş MVP-dışı) + kanon-lint kapanış taraması. ✅ S11 (Plan Yonetimi grep temiz — dokunulmadı; Veli Paneli yalnız accent-seçenek düzeltmesi): `KIRO2 Ogretmen Paneli` (**ilk dikkat kartı alarm-kırmızısıydı** #FEF2F2/#FBD5D5/#C2452B → amber ailesi #FFFBEB/#FDE9B8/#B45309 — spec "dikkat kartları amber", 3 kart artık tutarlı; hiyerarşi sırayla) · `KIRO2 Odev Atama` ('Gelişiyor' çipi soğuk #3B5FA8/#EAF0FC → mat çifti #3B82F6/#EFF6FF — S3 Soru Çözme ile aynı; odev-atama.png tazelendi +handoff) · `KIRO2 Veli Baglama` (#9A93A5 ×7 → #6B6478) · `KIRO2 Ogretmen Ogrenci Ozet` (#9A93A5 ×2 → #6B6478). **Paylaşılan kenar çubuğu düzeltmesi (3 dosya):** `KIRO Kenar` + `KIRO Kenar Ogretmen` + `KIRO Kenar Veli` — dar (64px) durumda .nprofile yatay padding'i 34px avatarı kırpıyordu → @container kuralına padding-left/right:0 eklendi (validator bulgusu, Ödev Atama'da yakalandı). Sıradaki: S12 (Çevrimdışı · Alan Kütüphanesi) + kanon-lint kapanış taraması. ✅ S12: `KIRO2 Cevrimdisi` (#9A93A5 ×4 → #6B6478; mat paket tinti #EAF0FC → #EFF6FF; accent seçeneğinde #3B6FD4 → [coral, altın, teal]; #B0A9B8 yalnız opacity:0.62 'bekleyen' satırlarında — devre-dışı durum, WCAG muaf, BİLİNÇLİ kaldı) · `KIRO2 Alan Kutuphanesi` (tintOf mat girdisi #EAF0FC → #EFF6FF — tek dokunuş).
**✅ KAPANIŞ TARAMASI (2026-07-21, tüm proje grep):** üretim DC'lerinde 4 kalıntı bulundu ve kapatıldı — `KIRO2 Giris` **body** zemini hâlâ #F1F2F6'ydı (S1'de wrapper düzelmiş, body kaçmış) → #F7F4EF · `KIRO2 Kutlama` + `KIRO Safak` transition:all → spesifik · `KIRO2 Cevrimdisi` accent seçeneği (yukarıda). Kalan eşleşmeler BİLİNÇLİ/kapsam-dışı: Boss Savaşı (kanon-allow: boss-arena) · Seri Dondurma AGRESİF anti-örnek · KIRO Birlesik Motor + Moderator Kilavuzu + Sunum-standalone (dokümantasyon/araştırma yüzeyleri, §11) · spec .md'lerdeki hex referansları (doküman). **P1 craft pass'ın ekran turu S1-S12 TAMAM (42/42).** P1'den kalan açık kalemler: yaşayan gökyüzü · skeleton kişiliği · onboarding arkı · breakpoint spec · erişilebilirlik satırları (TASARIM_DENETIM §D'nin ekran-ötesi maddeleri).
**✅ Yaşayan gökyüzü (2026-07-21, TASARIM_DENETIM #7):** `KIRO Safak.dc.html` gökyüzü artık iki sürücüyle yaşıyor — (1) **saat fazı** (gerçek saat): gece 23-05 koyulaştıran tint + 10 ek yıldız · alacakaranlık 05-08/18-23 baz gökyüzü + 4 yıldız · gündüz 08-18 hafif menekşe tint + ek yıldız yok; (2) **ufuk ışığı = sınava kalan gün** (persona.yksTarihi'nden): güneş sarmalı translateY (uzak = ufkun altında, yaklaştıkça doğar) + ufukta güçlenen sıcak bant. **Sayı gösterilmez** — KARARLAR #4 kaygı-nötr varsayılımla uyum; yakınlık yalnız ışıkla anlatılır. Akış-güvenli uygulama: baz gradyan + 6 yıldız inline kalır (anında boyanır), modülasyon `{{ }}` ek-stil delikleriyle biner (çözülmeden önce görünmez). **Yan-bug düzeltmesi:** sunPulse keyframe'i inline translateX(-50%)'i eziyordu → glow çemberi 260px sağa kaymış haldeydi; sarmal yapıyla (left:-260px çocuklar) kökten çözüldü. Tweaks: `gokyuzu` (otomatik/gece/alacakaranlik/gunduz) + `ufukIsigi` (otomatik/uzak/yaklasiyor/cok-yakin). bugun.png tazelendi (+handoff). Not: blanket reduce-guard tüm gökyüzü animasyonlarını zaten durduruyor; tint/konum statik olduğu için reduce'ta da yaşıyor (hareketsiz).
**⏳ Şafak craft listesi (2026-07-21):** uzman analiz turlarının tüm bulguları `design_handoff_kiro2/SAFAK_CRAFT_LISTESI.md`'de tek listede toplandı (A renk · B kompozisyon · C hareket · D sahne · E durum/veri · F kopya-onaylı) + uygulama sonrası denetim kontrol listesi. UYGULANMADI — kullanıcı onayı/seçimi bekliyor; F1-F3 ayrıca kopya onayı ister. Her yeni ekran: yeni DC (`KIRO2 <Ad>.dc.html`), kanona uygun, bitince
openapi + bu dosya güncellenir.
**✅ P1 KAPANIŞI (2026-07-21 — kalan 4 kalem):** ① **Skeleton kişiliği** — Durumlar'daki şafak süpürmesi + 3sn güvence/mantra standardı `ui-starter/Skeleton.tsx`'e taşındı (kiroSweep overlay yalnız card; `slowAfterMs=3000` "Biraz uzun sürdü, getiriyoruz…" + gün-seed'li ONAYLI 5'li mantra havuzu — Şafak ile birebir; RM'de nabız+süpürme statik). ② **Onboarding arkı (B6)** — `KIRO2 Onboarding` yeni Adım 1 "Hoş geldin": tek soruluk kaygı-tonu (Kaygı ağır basıyor / Değişken — güne göre / Genelde sakinim; bespoke ikon + radiogroup; seçimde kişisel serif yanıt + "Seviyeni ölçelim →"; "Bu soruyu geç" ile atlanabilir; kilit satırı "veline ya da öğretmenine gösterilmez" — KARARLAR #5 gizliliği) + payoff'ta ton-uyumlu tek serif satır; yerleştirme motoru DOKUNULMADI; tweaks `baslangicAdimi` (ton/olcum); openapi `/auth/register.misafirYerlestirme`'ye `kaygiTonu` (agir/gelgit/sakin, nullable) eklendi. ✅ TON KOPYALARI KULLANICI ONAYLI (KARARLAR). ③ **`BREAKPOINT_SPEC.md` (B8)** — 4 bant + tablet 768–1199 desen tablosu + prototip `.r*` haritası + QA matrisi (390/768/834/1024/1194/1280/1440); 768–1023 rail kuralı üretim işi olarak işaretli. ④ **Erişilebilirlik satırları (B10)** — 12 sprint spec'ine ekran-özel "Erişilebilirlik satırları (yatay DoD)" bölümü (odak halkası kanonu · klavye/odak yönetimi · aria-live bölgeleri · tek-delik aria-label gotcha'sı; timer'da sürekli duyuru YOK — kaygı). **TASARIM_DENETIM P1 TAMAM** — sırada P2: design-language sayfası · e-posta/bildirim yüzeyi · ses/haptik kararı.
**✅ P2-1 Design-language sayfası (2026-07-21):** `KIRO Tasarim Dili.dc.html` (galeri №37, Araştırma & Sistem) — public anlatı sayfası (Awwwards/It's Nice That yüzü): dusk hero (yıldız + ufuk glow, RM guard'lı, opacity-giriş YOK) → paper gövde; 6 bölüm: 01 Metafor (dusk/paper yan yana mini mock + "tema = ekran türü") · 02 Dil ("Tipik EdTech vs Şafak" 3 önce/sonra çifti — onaylı kopyalardan: bekliyor/henüz/geri-sayımsız) · 03 Renk (dawn aksanı + iki ders paleti + tek-gradyan-gökyüzü kuralı) · 04 Tipografi (serif his / grotesk sayı, tabular) · 05 Hareket (süre skalası çipleri + kanon üçlüsü linkleri) · 06 Kanıt (iki ürün iddiası + kanon-lint satırı). Template-only DC, K gerektirmez. Kalan P2: e-posta/bildirim yüzeyi · ses/haptik kararı (kullanıcıya soruldu).
**✅ P2-2 + P2-3 (2026-07-21):** `KIRO2 Eposta Bildirim.dc.html` (galeri №38) — A) veli haftalık özet e-postası 600px piksel+kopya referansı (dusk başlık + SİZ-dili + 3 stat (6,5 sa · seri 12 · 120,25 net) + amber Kimya içgörüsü + tek CTA + gizlilik satırı "ruh hâli/sohbet asla paylaşılmaz" + opt-out; kötü-hafta formülü baskısız); B) bildirim kopya sistemi (5 zorunlu kural + formül + 6 türlük birebir kopya tablosu — push mock'u dahil); C) ses/haptik kararı ekranda dokümante. KARARLAR'a işlendi. **TASARIM_DENETIM P2 TAMAM** — denetim listesi (P0+P1+P2) kapandı.
**✅ S11 son açık iş (2026-07-21):** `KIRO2 Sinif Kurulum.dc.html` (galeri №39, öğretmen ailesi — Hesap Kurtarma/Veli Bağlama görsel dili): 3 adımlı state-machine (`baslangicAdim` tweak ile gezilir); kod kartı kesikli dashed + 38px tabular kod; alt kilit satırı 'sohbet/mood/tekil cevap öğretmene açılmaz'. **Giriş noktaları:** Öğretmen Paneli topbar'ına kesikli '+' (Yeni sınıf, aria-label'lı) eklendi; ayrıca 'Ödev oluştur' CTA'sının yanlış `Soru Cozme` hedefi `KIRO2 Odev Atama.dc.html`'e DÜZELTİLDİ (S11 spec'teki bilinen link hatası — prototipte de kapandı). openapi öğretmen bölümü genişledi. ⚠ GOTCHA GÜNCELLEMESİ (verifier kanıtlı): `background-color:{{ }}` longhand deliği STATE-güdümlü post-mount güncellemede de reapply edilmiyor (eski support.js) — seçim dolgusu için güvenli desen: statik `background:#fff` + `box-shadow:inset 0 0 0 999px {{ zemin }}` (Sınıf Kurulumu 6 segment + Onboarding 3 ton radio'suna uygulandı).
**✅ Görsel + demo eşitleme (2026-07-22):** `screenshots/flow/` +3 PNG (§22f reçetesi): `sinif-kurulum` · `tasarim-dili` · `eposta-bildirim` — toplam 22 görsel, handoff kopyalandı. **Canlı Demo 15→16 sahne:** Ödev Atama'dan önce 'Sınıf Kurulumu' sahnesi (öğretmen halkasının başı: kur → ata → öğrenci ucu); banner metinleri (Demo + galeri) '16 sahne'. Sunum 12 slaytta kaldı (bilinçli — sahne eklenmedi).
**✅ Sunum güncellendi + yeniden export (2026-07-22):** Slayt 11 'Günün ötesi' roller kolonu artık öğretmen halkasını tam anlatıyor — görseller sinif-kurulum + odev-atama, kopya 'Öğretmen sınıfını kodla kurar, θ'ya göre ödev atar…', stat kartı '32→43 ekran · 3 rol'; konuşmacı notu eşitlendi. Üç türev de (ana + -print + -standalone) senkron (standalone'da img path'leri mevcutsa swap, kopya her hâlükârda). PPTX yeniden üretildi: `export/KIRO2 Sunum.pptx` (12 slayt + notlar, doğrulama bayrağı 0, screenshots modu).
**✅ Backend entegrasyon katmanı — prototip tarafı TAM (2026-07-22):** `kiro-api.js` (kök + handoff kopyası) — openapi.yaml sözleşmesinin ÇALIŞAN mock uygulaması: 25+ uç (me/subjects/topics/curriculum/atoms · review/due+grade · questions/answer · cat/next · exams/last · streak/checkin · level · mood · assignments+progress · teacher/classes GET/POST · me/class/join · notifications · billing/plans · auth/login), gerçek async gecikme (120-350ms), hata zarfı `{error:{code,message}}` (kaygı-duyarlı mesajlar), sunucu-otoriter kanon (dogru/çözüm YALNIZ answer yanıtında; cat/next 'dogru'suz; sınıf varsayılanlarını sunucu yazar), mutasyonlar `localStorage['kiro2-api-state']` (sıfırlama fonksiyonu var). **`KIRO2 API Konsol.dc.html` (galeri №40):** her ucu tıkla-çağır konsolu — istek satırı + gövde, durum kodu, ms, pretty JSON (koyu mono pane), hata örnekleri dahil (yanlış kod → 404, tanımsız uç → sözleşme mesajı). MİMARİ KARARI KORUNDU: ekranlar senkron seed'de kalır (akış hızı, §22b); üretim geçişi = bu katmanın imzasıyla fetch (api-client.ts) — ekran değişmez. Repo-tarafı entegrasyon Claude Code işi: URETIM_YOL_HARITASI Faz 4 + openapi + api-client + bu referans mock.
**✅ Gerçek-repo entegrasyon planı (2026-07-22):** GitHub keşfi yapıldı (`HuseyinAts/kiro2@master`: FastAPI `/api/v1/*` + Vite/React/TS frontend) → `ENTEGRASYON_PLANI.md` yazıldı — dosya-dosya eşleme (design uç ↔ gerçek backend dosyası ↔ gerçek frontend service/page ↔ prototip DC). Kritik keşifler: auth httpOnly-COOKIE (Bearer değil → openapi revize edilecek) · FSRS/CAT/placement/learning-path/teacher-classroom/osym-exam uçları REPODA ZATEN VAR (motorlar sunucuda ✓) · hata biçimi FastAPI detail (zarf zorlanmaz; kaygı-duyarlı mesajlar errorMessages.ts'e) · snake_case (sınırda mapper) · MUI/lucide Modern* sayfalar rota rota sökülür (ADR-000). Eklenecek YENİ uçlar §J'de kısa liste (kaygi_tonu, parent/link, fsrs grade, katilim_kodu, assignments/me, student summary, billing doldurma). Yürütme sırası S0-S12, DoD = PORT_DURUM + kanon-lint + API Konsolu smoke seti.
**✅ CLAUDE_CODE_TALIMAT v2 (2026-07-22):** baştan sona yeniden yazıldı — ENTEGRASYON_PLANI otoriter-plan bağlantısı (çelişkide o kazanır) · 43 ekran/22 PNG/PORT_DURUM güncel sayıları · ADR-001 cookie revizyon notu · S11 kapsamına Sınıf Kurulumu · sprint spec a11y bölümleri DoD olarak · kiro-api.js Faz 4 davranış referansı · BREAKPOINT_SPEC QA matrisi · yeni tuzaklar (inset box-shadow deseni taşınmaz, kaygiTonu/mood gizliliği, sayısız geri sayım varsayılanı, seed yalnız prototip) · 6 maddelik ekran DoD bölümü.
**Repoda (Claude Code):** zip'i `design/` olarak koy (kullanıcı yapacak) → Sprint 1
(SPRINT1_SPEC.md, süre ölçümü → PORT_DURUM kalibrasyonu) → Sprint 2-12 sırayla.
**Süreç kuralı:** her sprint spec'i işlenirken bu dosyanın KARARLAR bölümü spec'in "karar
bekliyor / öneri" notlarını geçersiz kılar; yeni karar gerektiğinde kullanıcıya sorulur,
"Decide for me" gelirse önerilen seçenek uygulanır ve buraya işlenir.

## 11. Bilinen sınırlamalar
- ui-starter bileşenleri test edilmemiş başlangıç kodu (Faz 2 kalite kapısı).
- Kapsam dışı yüzeyler: Kaygı Ölçüm + Moderatör Kılavuzu (araştırma), Canlı Demo/Sunum/Araştırma
  DC'leri (dokümantasyon), Mobil DC (referans), Çözüm Paylaş (ertelendi).
- Mobil (Expo) ertelendi; push ADR-004 ile web fazında yok.
- Bu projedeki `support.js` eski sürüm — mevcut DC'ler ona göre yazıldı, YÜKSELTME (bilinçli).
