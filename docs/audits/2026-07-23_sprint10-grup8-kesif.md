# KIRO2 — Faz 3 · SPRINT10 (Grup 8 · İş & Dayanıklılık) KEŞİF Sentezi

**2026-07-23** · 7 ekran (Abonelik · Ödeme · Plan Yönetimi · Ayarlar · Bildirim Merkezi · Alan Kütüphanesi · Çevrimdışı).
Girdi: 11-ajan keşif workflow (2 backend salt-okur + 1 infra çakışma + 7 DC kanon çıkarımı → sentez). **Kalibrasyon: ~12.3 birim** + tek-seferlik paylaşılan infra. **Build ÖNCESİ — kararlar bekliyor (bkz. §6).**

---

## 1. Özet

- **Tema tekdüzeliği: 7/7 PAPER, DC-KANITLI.** Her DC kökü `body{background:#F7F4EF}` + `color:#2A2433`; hiçbir ekranda dusk shell yok. SPRINT8'in "kategori-tahmini çürüdü" dersinin **ters teyidi** — "iş ekranı=paper" bu kez DC ile örtüşür ama karar yine kanıttan türedi. Tek nüans: **Ayarlar abonelik-banner'ı** paper içinde gömülü dusk aksan kartı (`#2A2433→#3A3145`), ekran teması değil → ikincil metni `tokens.dusk.ink2`.
- **Backend spektrumu geniş:** Çevrimdışı = en sağlam (tüm `/offline`+`/sync`+`/push` gerçek). Ödeme + Plan Yönetimi = **tam mock** (PSP/checkout/3DS/self-serve grep=0). Abonelik + Ayarlar + Bildirim = kısmi/karışık.
- **Sistemik kanon riski P0:** tüm DC'ler `accent=#FF6F5C` (parlak coral) CTA/logo/metin → **7/7 ekranda AA FAIL**; port genelinde `coralCtaBg #C2452B` + açık-zemin coral METİN `#C2452B` map zorunlu.

**Build ekseni:** paylaşılan infra → 3 basit standalone (Bildirim · Alan Kütüphanesi · Çevrimdışı) → billing zinciri (Abonelik → Ödeme → Plan) → composite Ayarlar.

---

## 2. Backend Gerçeği (mock-vs-gerçek)

| Ekran | Durum | Gerçek Uç | Mock Gereken | Faz 4 Not |
|---|---|---|---|---|
| **Abonelik** | KISMİ | `GET /api/v1/billing/me` (`billing_api.py:46`, is_premium + billing_subscriptions) | fiyat/plan katalog, self-serve başlat | Public `GET /billing/plans` YOK (Plan modeli var `billing.py:37`) |
| **Ödeme** | YOK (tam mock) | — (iyzico/PayTR/Stripe=0; 3ds/threeds=0) | checkout · 3DS init+callback · tokenizasyon · taksit · fatura profili | PSP entegrasyonu; Invoice "kart YOK — YAGNI" |
| **Plan Yönetimi** | YOK (tam mock) | `GET /billing/me` (kısmi durum) | iptal · geri-aç · upgrade/downgrade · B2C fatura geçmişi | `billing_subscriptions` raw SQL (ORM+write-path YOK) |
| **Ayarlar** | KISMİ | `GET/PUT /api/v1/osb/settings`+reset/preset (erişilebilirlik) | **calm-mode + hideRanking (Faz0: YOK)** · bildirim-tercih · genel per-user prefs | `email_notifications` kolonu var, API YOK; `/preferences` eksik |
| **Bildirim** | KARIŞIK | öğrenci `GET /student-dashboard/bildirimler` GERÇEK (GET-only) · veli `/parent/notifications`+`/veli/bildirimler` GERÇEK (TR/EN dup) | mark-read · mark-all · clear · unread-count · birleşik `/notifications` | **öğretmen `/ogretmen/bildirim*` = MOCK** (in-memory dict, restart'ta uçar) |
| **Alan Kütüphanesi** | PARÇALI | `/dag/topics` (topic_hierarchy) · `/learning-path/{status,weekly}` · `/konular` · EBA/ÖSYM taksonomi — hepsi GERÇEK | kanonik browse composite; ünite-seviye gruplama | **`/curriculum/*` = MEB UYUMLULUK, kütüphane DEĞİL (isim tuzağı)**; getCurriculum path drift DOĞRULA |
| **Çevrimdışı** | GERÇEK (en sağlam) | `/offline/{sync-package,sync-results,sync-status,health}`+`/sync/*`+`/push/*` | — (kritik eksik YOK) | bağlantı durumu = navigator.onLine; render saf-frontend |

**Sonuç:** Ödeme+Plan Faz 3'te izole mock-katman (uydurma-trend YOK, sunucu-otorite şeklini modelleyen). Çevrimdışı Faz 4'te gerçek uçlara doğrudan wire edilebilir.

---

## 3. Infra & Çakışma

api-client.ts (1369 satır, 58 export): hedeflenen 8 Grup-8 metod adının **hiçbiri mevcut değil** — doğrudan çakışma YOK. 4 reuse/collision riski:

- **YÜKSEK — Plan ad çakışması:** `PlanWeek`/`PlanBlok`/`PlanGun`/`getPlanWeek()`/`buildMockPlanWeek()` ZATEN VAR = **çalışma (ders) planı**. Grup 8 abonelik "Plan" → `AbonelikPlan`/`AbonelikYonetim`/`Subscription` ayrı ad ZORUNLU.
- **ORTA — Alan Kütüphanesi reuse:** `Alan`/`AlanKey`/`DersKatalogEntry`/`KatalogKonular`/`KatalogUnite(ler)` tipleri + `dersKatalog`/`alanlar`/`katalogKonular`/`katalogUniteler` mock anahtarları ZATEN VAR (yalnız `getKatalogKonular()` getter). **Yeni tip TANIMLAMA — REUSE.**
- **ORTA — Abonelik/fiyat:** `VeliDashboard.premium{fiyatAy,indirimYuzde,maddeler}`+`roi{...}` ZATEN modelliyor. `AbonelikData` bununla HİZALA — ikinci fiyat modeli üretme.
- **DÜŞÜK — StatusChip/OdevDurum:** iki ayrı `OdevDurum` var; Ayarlar/Bildirim durum-chip'i StatusChip reuse, üçüncü tanımlama.

**Kurallar:** MockData genişletme İKİ yerde (`KiroData` interface + `MockData=Pick<>` union); MSW çift-kayıt yapma (teacher/* zaten var); yeni tipler `../api` re-export bloğuyla açılır.

---

## 4. Build Sırası + Paylaşılan Infra

**0. PAYLAŞILAN INFRA (önce, tek commit, additive/çakışma-güvenli):**
- **Tipler:** `PlanTier`·`FaturaDonem`·`AbonelikPlan`·`AbonelikData` / `OdemeFaz`·`OdemeOzeti`·`KartFormState`(UI-only)·`ThreeDSDurum` / `AbonelikYonetim`·`OdemeYontem`·`Fatura`·`FaturaGecmisi` / `KullaniciAyar`·`BildirimTercih`·`AboneOzet`·`ProfilOzet` / `BildirimTon`·`Bildirim`·`BildirimGrup`·`BildirimYanit` / `ConnectivityState`·`CachedPack`·`SyncQueueItem`·`SyncStatus` / `AlanKutuphaneData`. **REUSE:** `Alan`/`AlanKey`/`DersKatalogEntry`/`KatalogUnite(ler)`/`CurriculumDers`/`OdevDurum`.
- **API (18 yeni):** getAbonelik · getOdemeOzeti · postOdemeDeneme · getOdeme3dsSonuc · getAbonelikYonetim · postAbonelikIptal · postAbonelikGeriAc · getFaturaMakbuz · getKullaniciAyar · updateKullaniciAyar · getBildirimler · markBildirimOkundu · markTumBildirimOkundu · clearBildirimler · getAlanKutuphane · getCevrimdisiPaketler · getSenkronDurum · logout. **REUSE:** getEngine · getVeliDashboard · getKatalogKonular · getCurriculum · getMe.
- **MSW:** billing/abonelik · abonelik/ozet · odeme/deneme-baslat · odeme/3ds/:id · abonelik/yonetim · abonelik/iptal · abonelik/geri-ac · abonelik/fatura/:id/makbuz · ayarlar(GET+PUT) · notifications(+:id/read,read-all,clear) · alan-kutuphane · offline/packs · offline/sync-status.
- **kiro-data anahtarları (İKİ yerde):** abonelik · abonelikYonetim · kullaniciAyar · bildirimler · alanKutuphane · cevrimdisi.
- **UI bileşeni:** `ui/Switch` (Toggle) — DC elle çiziyor, ui/'da YOK; `role=switch`+`aria-checked`+Space/Enter; track ON=coral fill / OFF=`#DDD6CC`. (Ayarlar 7 toggle + reuse.)

**Ekran sırası:** 1) Bildirim Merkezi (~1.7, liste+grup, infra doğrular) → 2) Alan Kütüphanesi (~1.7, tip-reuse) → 3) Çevrimdışı (~1.7, durum makinesi) → 4) Abonelik (~1.7, billing kök) → 5) Ödeme (~1.9, composite 3-fazlı 3DS state machine) → 6) Plan Yönetimi (~1.7, varyant matrisi) → 7) Ayarlar (~1.9, composite + yeni Switch, en son).

---

## 5. Riskler

- **P0 coral-CTA AA (7/7 sistemik)** → `coralCtaBg #C2452B`+beyaz; açık-zemin coral METİN `#C2452B`. DC literal `#FF6F5C`'i bağlama.
- **P1 ham `#6B6478` FALSE-POSITIVE (7/7 paper)** → PAPER `ink.muted` (meşru AA muted), dusk ihlali DEĞİL; kanon-lint uyarısı kabul edilebilir (Faz1/2 kaydı). İSTİSNA: Ayarlar banner ikincil metni `tokens.dusk.ink2`.
- **P1 `/\beksik\b/` absence-dili** (Abonelik/Ödeme/Bildirim/Plan): "eksik ödeme/bilgi/kart" → kanon-lint HATA → "bekliyor"/davetkâr reword. DC mevcut kopyası temiz; CIKARIM (Skeleton/Empty/Error) kopyasına 'eksik' sokma (KOPYA gate).
- **P1 'Senin alanın' rozet + profil-hero gradient AA:** alan-renk/gradient üstünde beyaz metin AA riski → koyu-token/ink metin (bkz. karar).
- **Plan ad çakışması (YÜKSEK):** `AbonelikPlan`/`AbonelikYonetim` ayrı ad.
- **MockData çift-güncelleme** (tsc hatası), **MSW çift-kayıt**, **getCurriculum path drift** (Faz4 doğrula), **Switch önkoşul**, **alarm-red cazibesi** (iptal/decline→amber), **box-sizing:border-box kök dahil** (SPRINT8 dersi), **HAS_MOTION guard** (3DS spinner + view-transition).

**Çelişkiler:** Plan Yönetimi iç-çelişki (veli "öğrenci fiyat görmez" vs öğrenci-varyant fiyat gösterir — KVKK); Bildirim zayıf-konu coral(DC) vs amber(kanon → amber, kanon>DC); Alan örnek-soru mock(8 seed) vs live(77K) davranış farkı; `/curriculum/*` isim tuzağı; DC tasarımcı-meta-notu (Çevrimdışı satır 110) porta kopya DEĞİL.

---

## 6. Açık Kararlar (build ÖNCESİ — kullanıcıya soruldu)

Öneri-öncelikli, 11 deduped. Kritik 5 `AskUserQuestion` ile sorulacak; kalanlar öneri-varsayılanla ilerler:

1. **Ödeme/PSP scope** — öneri: Faz3 saf-mock (izole timer sim), PSP Faz4 (TR: iyzico/PayTR eğilim).
2. **Öğrenci fiyat görünürlüğü / KVKK** — DC iç-çelişki; öneri: öğrenci salt-görünüm, fiyat gizli/link-only, satın-alma yalnız veli (çözülmeden portlanmaz).
3. **Sakin-mod ↔ Sıralamayı-gizle** — öneri: tek `KullaniciAyar` kaynağı (hideRanking+calmMode), Faz3 localStorage mock persist; davranış sözleşmesi: hideRanking→Lig gizle, calmMode→reduced-motion+dürtme-sustur.
4. **Billing akış zinciri + route guard** — öneri: premium→Plan Yönetimi, değil→Abonelik→Ödeme(?rol&?fatura)→Plan; `GET /billing/me` sunucu-otorite.
5. **Sprint dilimleme** — 7 ekran + 2 composite + billing zinciri → tek tur vs 2-3 alt-sprint (Grup 7 "ağırları ayır" ile bölündü).
6. Çevrimdışı SW kapsamı — öneri: saf-istemci navigator.onLine + mock manifest.
7. Bildirim zayıf-konu ton — öneri: amber (kanon>DC, otomatik).
8. Öğrenci SideNav erişimi — öneri: TopBar avatar→Ayarlar, çan+unread rozet→Bildirim.
9. Alan API şekli — öneri: composite `getAlanKutuphane()` (sayaç sunucu-otorite).
10. Composite bileşen (PlanCard/TrustChips) — öneri: screen-local, 3. kullanımda çıkar (YAGNI).
11. İptal onay-adımı — öneri: tek onay-adımı (yanlış-tık koruması).

---

*Kaynak: keşif workflow `wf_a52b9c17-4dd` (11 ajan, 0 hata, 1.56M token). Build kararlar onaylandıktan sonra başlar.*
