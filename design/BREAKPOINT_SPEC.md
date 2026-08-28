# KIRO2 — Breakpoint & Ara-Genişlik Spec'i (TASARIM_DENETIM B8)

> 2026-07-21. Tablet (768–1199) dahil dört bandın yerleşim kuralları.
> **Kanon:** breakpoint ekran TÜRÜNÜ (paper/dusk temasını) asla değiştirmez — yalnız yoğunluk ve yerleşim değişir.

## 1 · Bantlar

| Bant | Aralık | Kaynak | Durum |
|---|---|---|---|
| Masaüstü | ≥1200px | referans tasarım (DC'ler olduğu gibi) | ✅ prototipte |
| Tablet | 768–1199px | BU SPEC §3 — öğretmen/veli birincil cihazı | 🔶 kurallar burada; prototip ≤760'ta çöker (bilinçli fark, §3 not) |
| Dar tablet / büyük telefon | 481–767px | mevcut kolon çökertmeleri (760/800/820 MQ'ları) | ✅ prototipte |
| Telefon | ≤480px | `.r*` mobil pass (DEVIR-NOTU §9–9c) — QA referansı **390px** | ✅ prototipte, 21/21 overflowX=0 |

## 2 · Prototipteki mekanik (envanter — porta birebir taşınır)

- Her DC kendi helmet `<style>`'ında media query taşır; global stylesheet yok (DC kuralı).
- Sınıf haritası: `.rnav` (sol nav 250→64px ikon rayı, ≤760) · `.rpadx`/`.rpadp` (yatay gutter 30→16–20) · `.rhead` (topbar wrap) · `.rkpi4` (KPI 4→2→1) · `.rtwo` (2 kolon→1) · `.rstack` · `.rdense` (dikey yoğunluk) · `.rh1` (38→~30px başlık) · `.rstud`/`.rstudhide` (öğretmen tablosu 4→3 kolon) · `.rhiderail` (sağ ray ≤760 gizli) · `.rbody`/`.rnavq` (soru + navigatör dikey stack) · `.rsec` (telefonda gizlenen ikincil öğe).
- `KIRO Kenar*` kendi container-query'siyle çöker (`@container max-width:150px` → `.ni { min-height:44px }`).
- Dokunma hedefi ≥44px (tap-target denetimi DEVIR-NOTU §9c); kısa metin linkleri bilinçli istisna.
- ⚠ Runtime gotcha: statik inline değer eşleyen seçicilerde `[style*='font-size: 30px']` (colon+BOŞLUK) yazımı — runtime stili boşluklu serialize eder.

## 3 · Tablet bandı kuralları (768–1199) — üretim

| Desen | 1024–1199 | 768–1023 |
|---|---|---|
| Sol nav | tam genişlik (250px) | 64px ikon rayı (tooltip'li; `aria-label` korunur) |
| İçerik gutter | 26–30px | 20–24px |
| KPI ızgarası | sığıyorsa 4'lü, değilse 2×2 | 2×2 |
| İki-kolon bölümler (`.rtwo` deseni) | korunur | ≥900 korunur, <900 tek kolon |
| Öğretmen tabloları | 4 kolon | ≥900 4 kolon; <900 'Son aktivite' gizlenir (`.rstudhide` deseni) |
| Soru + navigatör | yan yana | <1024 dikey stack (dokunmatik erişim) |
| Tip ölçeği | masaüstü değerleri — küçültme YOK (tablet okuma mesafesi yakın) | aynı |
| Dokunma hedefi | ≥44px (≤1199 tamamı dokunmatik varsayılır) | ≥44px |
| Modal/overlay | max-width sabit (560–680px), kenar boşluğu ≥24px | tam genişlik − 32px |

**Not:** prototip nav'ı ≤760'ta çöker; 768–1023 rail kuralı ÜRETİM işidir. Prototipe taşımak istenirse mevcut `.rnav` MQ'sunu 1023'e genişletmek yeterli (ekran başına tek satır) — bilinçli beklemede: prototip masaüstü sunum aracı olarak kullanılıyor.

## 4 · QA matrisi (görsel regresyon + overflow)

Genişlikler: **390** (telefon QA) · **768** (iPad dikey) · **834** (iPad Air) · **1024** (iPad yatay — rail/tam-nav sınırı) · **1194** (iPad Pro yatay) · **1280** · **1440**.
DoD her bantta: `overflowX=0` · hit ≥44 (≤1199) · odak halkası her iki zeminde görünür · tema DEĞİŞMEZ.

## 5 · Üretim eşlemesi

- `tokens.ts`'e sabit: `breakpoint = { phone: 480, narrow: 767, tablet: 1199 }` (CSS'te ham MQ; JS'te `matchMedia`).
- PORT_DURUM DoD "≤480 responsive" satırı bu spec'le genişler: "≤480 **ve** 768/1024 bantlarında overflowX=0 + hit ≥44".
- Mobil (Expo) fazında bu bantlar geçerli değil — RN kendi yerleşimi (`KIRO2 Mobil.dc.html` 390pt referans).
