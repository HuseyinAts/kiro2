# KIRO2 — Bileşen Envanteri (üretim çekirdek bileşen kütüphanesi için)

Adım 3'ün haritası: prototipte **fiilen paylaşılan** bileşenler + ekranlarda **tekrar eden desenlerden çıkarılacak** bileşenler. Her girişte: önerilen props (TS), kullanıldığı ekranlar, tema varyantı, piksel referansı (en iyi kaynak `.dc.html`). Token'lar `tokens.ts`'ten gelir — bileşen içinde ham hex kullanma.

Öneri: `packages/ui-web` + `packages/ui-native` aynı bileşen adları ve props imzalarıyla; görsel doğrulama `screenshots/flow/` + ilgili `.dc.html` tarayıcıda.

---

## A · Prototipte fiilen paylaşılan bileşenler (dc-import ile gömülü)

### 1. SideNav (prototipte: `KIRO Kenar` · `KIRO Kenar Veli` · `KIRO Kenar Ogretmen`)
Üretimde **tek bileşene birleştir**: `role` prop'u menü setini seçer.
```ts
interface SideNavProps { role: 'ogrenci'|'veli'|'ogretmen'; active: string; accent?: string }
```
- `active` değerleri (öğrenci): `panel · plan · path · practice · review · deneme · ai · assistant · interaktif · league · arkadas · seri`
- Davranış: ≤760px'te 64px ikon-only'e çöker (container-query); alt blokta "KIRO Asistan" CTA + profil.
- Kullanım (öğrenci): Panel, Haftalık Plan, Öğrenme Yolu, Soru ekranları, FSRS, Harmanlanmış, AI Sohbet, Sokratik, Neden, İnteraktif, Lig, Arkadaş Serisi, Seri Dondurma, Ayarlar, Bildirim Merkezi. Veli/Öğretmen: kendi panelleri.
- Piksel referansı: `KIRO Kenar.dc.html` (+ Veli/Ogretmen varyant dosyaları).

### 2. MasteryBadge (prototipte: `KIRO Mastery Rozet`)
```ts
interface MasteryBadgeProps { pct: number; trend?: 'up'|'down'|'flat'; badge?: boolean /* false = galeri/demo modu */ }
```
- Eşikler `masteryTier` ile birebir: <40 Tanıdık · <65 Yetkin · <85 Usta · ≥85 Fethedildi (renkler `tokens.color.mastery`).
- Kullanım: Soru Çözme (konu rozeti), Neden Geri Bildirim, Öğrenme Yolu ("Sıradaki adım"), Bilgi Atomları (satır başına), Birleşik Motor (×2).
- Piksel referansı: `KIRO Mastery Rozet.dc.html` (galeri modu tüm kademeleri gösterir).

---

## B · Desenden çıkarılacak bileşenler — P0 · temel yapı taşları

| Bileşen | Önerilen props | Başlıca ekranlar | Tema | Piksel referansı |
|---|---|---|---|---|
| **Button** | `variant: 'primary'\|'ghost'\|'goldDark'; size: 'md'(40)\|'lg'(48-50); icon?; disabled?` | Tüm ekranlar (primary=coral+gölge, ghost=beyaz+border, goldDark=koyu ekran altın CTA) | ikisi | Abonelik CTA · Lig "XP kazan" · Kutlama CTA |
| **Chip / Pill** | `kind: 'streak'\|'tag'\|'status'; label; icon?; tone` | Seri çipi (alev+sayı): Panel, Lig, Geri Sayım, Veli; TYT/AYT etiketi: Sınav Sonuç, Veli; durum pili: Abonelik "Şu an", anket aşama pili | ikisi | Ogrenci Paneli topbar · Sinav Sonuc satırları |
| **Card** | `padding; radius: 'card'(16-18)\|'lg'(20); variant: 'solid'\|'dashed'(boş durum)\|'dusk'` | Tüm açık ekran gövdeleri; koyu sağ-ray kartları (Lig) | ikisi | Ogrenci Paneli · Lig sağ ray |
| **StatBlock** | `value; label; delta?; tone?` — büyük tabular sayı + alt etiket | KPI satırları: Panel, Veli Paneli, Sınav Sonuç; hero statlar: Geri Sayım çipleri | ikisi | Veli Paneli KPI · Sinav Sonuc hero |
| **ProgressBar** | `pct; color; height: 6-9` | Ders hâkimiyeti: Panel, Veli, Sınav Sonuç; seviye: Lig; günlük: Bugün | ikisi | Sinav Sonuc ders dökümü |
| **ProgressRing** | `pct; size; label; sublabel` | Sınav Sonuç doğru-oranı (148px), Panel günlük hedef (%60) | açık | Sinav Sonuc hero ringi |
| **SegmentedControl** | `options: {key,label,badge?}[]; value; onChange` | Abonelik aylık/yıllık, Kutlama tip önizleme, Kaygı Ölçüm 1-4 ölçeği | ikisi | Abonelik toggle · Kaygi Olcum satırı |
| **Input** | `value; onChange; placeholder; ariaLabel` (44px hedef) | Kaygı Ölçüm katılımcı kodu, Ayarlar formları, AI Sohbet composer | açık | Kaygi Olcum header |
| **Avatar** | `initials; size: 24-70; bg; ring?` | Lig sıralama/podyum, Veli topbar çocuk seçici, Kenar profil | ikisi | Lig podyum |
| **IconBadge** | `icon; tone; size: 32-56; radius` — yumuşak zeminli ikon karesi | Her ekranda (kart başlıkları, özellik satırları) | ikisi | Sunum sahne kartları · Veli ROI |
| **Callout** | `tone: 'success'\|'attention'(amber)\|'dawn'; icon; children` | Veli Paneli uyarılar, Seri Dondurma bilgi kutusu, anket etik şeridi | açık | Veli Paneli "Uyarılar" |
| **Skeleton** | `shape: 'card'\|'row'\|'bar'; lines?` — gerçek düzen geometrisi, 1,6s nabız, reduced-motion'da statik, <400ms'te gösterilmez | Tüm veri ekranları (üretimde) | ikisi | KIRO Durumlar §1 + şafak süpürmesi & 3sn mantra satırı (Durumlar §1, 2026-07-21) |
| **EmptyState** | `icon; serifTitle; body; action?` (dashed kart; "yönlendiren boşluk" kopyası) | Lig sıralama-gizli, Bildirim Merkezi boş, FSRS sıfır kart… (standart) | ikisi | KIRO Durumlar §2 |
| **ErrorState** | `serifTitle; body; onRetry` (amber çerçeve; "sorun sende değil" + güvence zorunlu; kırmızı yasak) | Tüm veri ekranları (üretimde) | ikisi | KIRO Durumlar §3 |
| **ZoneHeader** | `label; tone; icon?` — renkli etiket + ince çizgi | Lig bölge başlıkları; liste ayraçları | açık | Lig "Yükselme bölgesi" |

**A11y taahhütleri (P0'da bileşene göm):** ikon-düğmede zorunlu `aria-label`; tüm sayılar `tabular-nums`; dokunma hedefi ≥44px; açık zeminde küçük metin ≥ `ink.muted` (#6B6478); risk asla kırmızı.

---

## C · Bileşik bileşenler — P1-P2 · çekirdek döngü

| Bileşen | Önerilen props | Ekranlar | Piksel referansı |
|---|---|---|---|
| **TopBar** | `title; children(sağ statlar); sticky+blur` | Tüm açık ekranlar | Lig · Panel topbar |
| **SubjectMasteryRow** | `subject; pct; color` (nokta+ad+%+bar) | Panel, Veli Paneli, Sınav Sonuç | Veli "Ders Bazında" |
| **QuestionCard** | `question; selected?; revealState: 'none'\|'correct'\|'wrong'; onSelect` (A-E şıklar, doğru=yeşil kontur) | Soru Çözme, Adaptif Test, Harmanlanmış, Boss | Soru Cozme |
| **QuestionNavigator** | `total; current; answered[]; marked[]` | Soru Çözme, Harmanlanmış | Soru Cozme sağ panel |
| **TimerChip** | `remaining; tone` (amber zemin; alarm-kırmızısı YOK) | Soru ekranları | Soru Cozme header |
| **SolutionSteps** | `steps[]; neden` (adım adım + "neden" kapanışı) | Neden Geri Bildirim, Soru Çözme çözümü | Neden Geri Bildirim |
| **FlashcardReview** | `card; flipped; onGrade('kolay'\|'iyi'\|'zor')` | FSRS Tekrar | FSRS Tekrar |
| **ReviewQueueRow** | `item: ReviewItem` (stabilite/R% göstergeli) | FSRS Tekrar, Haftalık Plan | FSRS Tekrar kuyruk |
| **WeekBars** | `days: {label,value,highlight?}[]` mini sütun grafiği | Veli Paneli, Haftalık Plan | Veli "Haftalık Aktivite" |
| **CurriculumTree** | `units: CurriculumUnit[]` (done/current/open/locked düğümleri) | Öğrenme Yolu | Ogrenme Yolu |
| **AtomBreakdown** | `kirilim: AtomKirilim; enZayifVurgu` | Bilgi Atomları, Boss zayıf-nokta | Bilgi Atomlari |

## D · Oyunlaştırma & iş — P2-P3

| Bileşen | Props özü | Ekranlar | Referans |
|---|---|---|---|
| **SenVsDunHero** | `delta; pct; bars(dün/bugün)` — gradient şerit, serif mantra | Lig (birincil), Panel özeti | Lig üst şerit |
| **RankingList + RankingRow + Podium** | `rows; zones; you; hideable` (gizlenebilirlik P1 kararı!) | Lig | Lig |
| **TierStepper / MilestoneStepper** | `steps; currentIdx` | Lig lig şeridi · Seri Dondurma kilometre taşları | ilgili ekranlar |
| **StreakCalendar** | `week: {done\|frozen\|today}[]` (dondurma=mavi kare) | Seri Dondurma | Seri Dondurma |
| **NudgeBubble** | `tone: 'insani'\|'agresif-anti-ornek'` (ikincisi yalnız dokümantasyon!) | Seri Dondurma | Seri Dondurma |
| **CelebrationOverlay** | `type: 'gunluk'\|'seviye'\|'seri'\|'boss'; stats` (dusk + şafak konfeti; reduced-motion'da konfeti yok) | Kutlama | Kutlama |
| **CountdownHero** | `varyant: 'sayim'\|'notr'` (A/B — feature flag) | Sınava Geri Sayım | Sinav Geri Sayim |
| **PlanCard + TrustChips** | `plan: 'free'\|'premium'; billing; rol: 'ogrenci'\|'veli'` | Abonelik (+`?rol=veli`), Veli ROI kartı | Abonelik |
| **EvidenceStrip** | `stats: {value,label,tone}[]` | Abonelik veli-yüzü, Veli ROI | Abonelik ?rol=veli |
| **SurveyScale** | `items; value; onChange` (1-4; seçili=mürekkep dolgu) | Kaygı Ölçüm (araştırma aracı — üretim uygulamasına GİRMEZ) | Kaygi Olcum |

**Bileşenleştirme eşiği:** tek ekranda yaşayan sahne-özel yapılar (Boss HUD, İnteraktif parabol sandbox, Onboarding merdiveni, sunum/demo çerçeveleri) bileşen kütüphanesine ALINMAZ — ekran içi kalır (prototipteki "erken bileşenleştirme yapma" kuralının üretim karşılığı).

---

## E · Port sırası (bağımlılık grafiği)

1. **P0** — B tablosundaki 15 yapı taşı (Button → Card → Chip → StatBlock → Progress* → Segmented → Input → Avatar → IconBadge → Callout → Skeleton → EmptyState → ErrorState → ZoneHeader) — durum üçlüsünün kanonik örnekleri: `KIRO Durumlar.dc.html`
2. **P1** — SideNav (3 rolü tek bileşende) + TopBar + MasteryBadge → ilk ekran portu: **Öğrenci Paneli** (en çok bileşeni tüketir, iyi entegrasyon testi)
3. **P2** — çekirdek döngü composites (QuestionCard seti, SolutionSteps, FlashcardReview) → Bugün → Soru Çözme → Neden → FSRS → Kutlama ekranları
4. **P3** — oyunlaştırma/iş composites → kalan ekranlar

Her bileşen bittiğinde: Storybook story (paper+dusk varyantı) + ilgili `.dc.html` ile yan yana piksel karşılaştırma.
