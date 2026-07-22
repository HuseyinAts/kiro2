# Faz 3 · SPRINT5 — Planlama (Grup 4) (2026-07-22)

Kapsam: **4 ekran** — Haftalık Plan · Öğrenme Yolu (ağır) · Bilgi Atomları · Çalışma Modları. Tema: dördü de **paper**.
Süreç: **keşif workflow (6 ajan) → paylaşılan-infra edit → build workflow (4 ajan) → gate → adversarial review workflow (4 boyut) → fix → gate**.
Bu grupla Soru Çözme'ye giden TÜM giriş kapıları bağlandı (plan bloğu · patika düğümü · atom CTA · mod kartı).

## DoD sonuçları

| Ekran | rota | tema | axe | breakpoint | kanon | tsc | vitest |
|---|---|---|---|---|---|---|---|
| Haftalık Plan | `/plan` | paper | ✅ | ✅ 7/7 | ✅ 0 | ✅ 0 | ✅ |
| Öğrenme Yolu | `/yol` | paper | ✅ | ✅ 7/7 | ✅ 0 | ✅ 0 | ✅ |
| Bilgi Atomları | `/atomlar?konu=` | paper | ✅ | ✅ 7/7 | ✅ 0 | ✅ 0 | ✅ |
| Çalışma Modları | `/modlar` | paper | ✅ | ✅ 7/7 | ✅ 0 | ✅ 0 | ✅ |

- **Kapı:** kanon-lint **0 ihlal** (9 uyarı — hepsi kabul: patika hareket-süreleri 0.7s+ "hareket duygusu" + pre-existing `#6B6478` FP) · scoped strict **tsc 0** · vitest **tam kiro 37 dosya / 203 test PASS** · **breakpoint 119/119** (17 ekran-story × 7 genişlik).

## Paylaşılan infra eklemeleri (mock-katmanı; üretime sızmaz)
- **`types.ts`**: `Atom.enZayif?: boolean` (SPRINT5 açık-nokta 2) + `PlanWeek`/`PlanGun`/`PlanBlok`/`PlanBlokTur` (açık-nokta 1).
- **`api-client.ts`**: `getPlanWeek()` + `buildMockPlanWeek()` (reviewQueue-due + zayıf topics + sabit Deneme/Analiz/Mola iskeleti; DC ile birebir hafta 29 Haz–5 Tem) + `markEnZayif()` (getTopicAtoms mock dalında min-hâkimiyet atomu işaretler — **istemci min-hesabı YOK**, sunucu-otorite simülasyonu).
- **`mswHandlers.ts`**: `*/plan/week` · `*/curriculum` · `*/curriculum/:ders` · `*/topics/:konu/atoms` (live/E2E pariteği; enZayif marking live yolda da uygulanır).
- kiro-data.json'a **plan içeriği EKLENMEDİ** — kompozisyon yalnız mock katmanında.

## Ekran notları
- **Haftalık Plan**: SideNav(plan) + 66px header + 7/4/1-sütun hafta grid'i. Blok kartları gerçek `<a href={hedefRota}>` (spec §A DoD). Blok göstergesi 7×7 nokta + tag rengi (DC otoritesi; "sol 3px bar" DEĞİL). Boş gün "Serbest" doldurulmaz. 5 blok türü + renk/meta birebir. Header coral-metin + BUGÜN rozeti `#C2452B` (AA).
- **Öğrenme Yolu** (kimlik ekranı): gamified dikey patika — ünite bandı gradyanları (darken formülü DC'den), 72px düğüm zikzak (offsets [0,±40,±52], 390px'te ±28'e daralır), 4 durum (button + aria-label; kilitli aria-disabled), kbounce/kring/kfloat (`useReducedMotion` guard'lı — kanon-lint MOTION_GUARD şartı), checkpoint 86px (altın/terracotta/gri), sağ ray 3 kart (ProgressRing 100px×11, MasteryBadge, lejant). **Düğüm durumları sunucudan** (curriculum.durum); istemci "tamamlandı" işaretlemez.
- **Bilgi Atomları**: SideNav-siz makale (max 820), kicker/başlık/giriş/içgörü-kutusu BİREBİR, `?konu=` URL state, chip radiogroup+aria-checked, zayıf atom **`enZayif` SUNUCUDAN** okunur, pulseA guard'lı.
- **Çalışma Modları**: SideNav-siz (max 880), 2×2 mod grid, kicker/havuz-kartı/alt-not BİREBİR, poolCards/poolTier `getTopics`+`getReviewDue`'den. 4 mod → /tekrar · /soru-cozme · /tekrar (Eşleştirme en-yakın) · /duello (Hız ileri-ref S8).

## Adversarial review — 11 bulgu (1 major + 10 minor) → 8 fix · 2 red · 1 ertelendi

| # | ekran | sev | bulgu | karar |
|---|---|---|---|---|
| 1 | CalismaModlari | **major** | h1 "Çalışma Modları" `serifText` (italik) — DC düz (upright); kardeş BilgiAtomlari düz | **FIX** → `fontFamily: font.serif` (italik kaldır) |
| 2 | HaftalikPlan | minor | sayfa başlığı `<div>` + gün başlığı `<span>` — spec §A DoD "gün başlıkları `<h2>`" | **FIX** → `<h1>`/`<h2>` (görsel stil korundu) |
| 3 | HaftalikPlan | minor | EmptyState "Planın henüz kurulmadı." absence-dili | **FIX** → "Planın seni bekliyor." (bekleyiş çerçevesi) |
| 4 | HaftalikPlan | minor | "Serbest" `#B5AEA2` ~2:1 (token guidance metin için yasak) | **FIX** → `ink.muted #6B6478` (AA) |
| 5 | CalismaModlari | minor | mod kartı CTA metni canlı ders rengiyle <4.5:1 (Eşleştirme yeşili en kötü) | **FIX** → per-mod AA `ctaRenk` (ikon canlı kalır): #C2452B/#1D4ED8/#047857/#9A5D0D |
| 6 | OgrenmeYolu | minor | ProgressRing 100px strokeWidth atlanmış (8px) — DC 11px | **FIX** → `strokeWidth={11}` |
| 7 | BilgiAtomlari | minor | radiogroup roving-tabindex yok (spec min "radiogroup+aria-checked" KARŞILANDI) | **ERTELE** — SegmentedControl bileşeni doğru ev; spec-met |
| 8 | HaftalikPlan/OgrenmeYolu | minor | SideNav ≤1023px daralır, DC ≤760px | **RED** — BREAKPOINT_SPEC §3 rail kuralı (768-1023); tüm ported kiro ekranlarında tutarlı sistem kararı |
| 9 | BilgiAtomlari | minor | chip'ler `topics(zayif/gelisiyor)` — DC `atomKirilim` konuları | **RED** — spec §C "zayıf konular"; mock'ta 9 zayıf konunun hepsi kırılımlı → EmptyState düşüşü yok; guard mevcut |

**Not:** DC-pixel review ajanı overflow yakalamadı (ajanlar tarayıcı koşmaz) — 2 overflow bug'ı breakpoint denetçisi yakaladı (aşağıda).

## Breakpoint overflow bug'ları (2) — kök-neden + fix
1. **HaftalikPlan @1194 +7px**: `gridTemplateColumns` bare `1fr` (= `minmax(auto,1fr)`) min-content blowout. **Fix**: `minmax(0, 1fr)` (7/4/1 sütun).
2. **OgrenmeYolu @768–1440 +32px** (390 geçti — ofset-korelasyonu yanıltıcı): 2 yanlış hipotez (patika/maskot `overflowX:clip`, sonra ders-özet `marginLeft:auto`) sonrası **parent-zincirli Playwright teşhisi gerçek kaynağı buldu**: içerik-sarmalayıcı `width:100% + padding` ama **`box-sizing` yok → content-box**, padding'i 100%'ün ÜSTÜNE ekliyor (28-32px taşma). Kardeş ekranlar (CalismaModlari:123, SoruCozme) `boxSizing:'border-box'` set ediyor; OgrenmeYolu sarmalayıcısı atlamış. **Fix**: `boxSizing:'border-box'` (tek satır). Yan iyileştirmeler korundu (ders-özet `marginLeft:auto` = PanelPage deseni; grid `minmax(0,1fr)`); yanlış patika-clip geri alındı.

> Ders: ofset-korelasyonu + "sabit 32px" iki kez yanlış yere işaret etti — geometrik akıl-yürütme değil, **parent-zincirli ÖLÇÜM** gerçek kaynağı tek atışta verdi. `box-sizing:border-box`, padded + `width:100%`/`maxWidth` container'larda ZORUNLU desen (kanon adayı).

## Kopya çelişkileri (tiebreaker: SPRINT5_SPEC satır 5 "DC=piksel otoritesi" + Faz2 AA kanonu)
- Ünite-1 rengi #3B82F6 (DC) · Test kartı #3B82F6 (DC) — spec #3B6FD4 değil.
- Coral CTA dolgu+beyaz metin = #C2452B (AA); açık zeminde coral METİN = #C2452B; parlak #FF6F5C yalnız metinsiz dekorasyon (ring/balon kenarı/maskot gradyanı/yıldız-ikon).
- Öğrenme Yolu düğüm = `<button>`+aria-label (spec a11y > DC `<a>`).
- Terracotta chip #E0593F+beyaz (~3.9:1) = bilinçli ders-rengi istisnası (DC birebir).

## Ertelenenler / bilinen
- BilgiAtomlari chip roving-tabindex (bulgu 7) — spec-met; SegmentedControl'e taşınabilir.
- İleri-ref rotalar (hedef ekranlar henüz portlu değil): `/mola` (S6) · `/boss` (S7) · `/duello` (S8) — gerçek href (SideNav'da kanon rota); hedefler portlanınca canlı.
- `/deneme`, `/sinav-sonuc`, `/soru-cozme`, `/tekrar` — portlu; app-shell router bağlanınca canlı.

## Kalibrasyon
| Ekran | tip | birim | not |
|---|---|---|---|
| Haftalık Plan | SideNav+grid+3durum (getPlanWeek yeni) | ~1.6 | Odevlerim/Panel reuse; yeni mock uç +0.3 |
| Öğrenme Yolu | özgün (gamified patika + animasyon + 3 rail kart) | ~3.0 | sprintin ağır işi; SVG ikon + darken + zikzak bespoke |
| Bilgi Atomları | makale (SideNav-siz, kopya-ağır) | ~1.4 | Callout/MasteryBadge reuse |
| Çalışma Modları | makale (2×2 grid, hafif) | ~1.1 | en hafif; tierFromPct reuse |

**İlerleme: 15/42 ekran + 1 composite (QuestionCard). Grup 4 (Planlama) TAMAM.**
Sonraki: Grup 5 Hub/duygusal (Bugün=**İLK dusk ekran**) · Kutlama · Mola · Geri Sayım · Başarımlar · Boss.
