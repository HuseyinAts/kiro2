# Faz 3 · SPRINT2 — Hesap Kurtarma · Onboarding · Öğrenci Paneli (2026-07-22)

Kapsam: 3 ekran + SideNav/MasteryBadge wiring. Kaynak: SPRINT2_SPEC §B/§C/§C0/§D,
BREAKPOINT_SPEC §4, kiro-api.js, ilgili `.dc.html`'ler. Tema: 3'ü de **paper** (route-bazlı, toggle YOK).

## DoD sonuçları

| Ekran | tema | axe | breakpoint (390→1440) | odak halkası | kanon | tsc | vitest | commit |
|---|---|---|---|---|---|---|---|---|
| Hesap Kurtarma (4 adım) | paper | ✅ | ✅ 7/7 | ✅ `:focus-visible` | ✅ 0 | ✅ 0 | ✅ | `fcb189230` |
| Onboarding (misafir + §C0 ton) | paper | ✅ | ✅ 7/7 | ✅ | ✅ 0 | ✅ 0 | ✅ | `ba809ce35` |
| Öğrenci Paneli (composite) | paper | ✅ | ✅ 7/7 | ✅ | ✅ 0 | ✅ 0 | ✅ | `d2c974649` |

- **Breakpoint matrisi:** `npm run kiro:breakpoints` → 5 ekran × 7 genişlik = **35/35 PASS**
  (overflowX=0 + hit≥44 ≤1199). Denetçi artık ekran story'lerini `storybook-static/index.json`'dan
  türetir (`Kiro/Ekran/*`) — yeni ekran otomatik kapıya girer.
- **vitest:** SPRINT2 3 ekran = **15 test PASS** (Panel 5 + Onboarding 5 + Kurtarma 5). RTL + jest-axe her ekranda.
- **Veri:** `configureKiroApi` mock; Panel getMe+getSubjects+getLastExam bağlı, Onboarding calib
  `catBankMat` merdiveni (dogru yerel — motor SUNUCUDA, live'da `/cat/next`).

## §C0 ton adımı (Onboarding — yeni)
SPRINT2_SPEC güncellemesiyle eklendi. Kopya **DC'den birebir çıkarıldı** (repo spec'inde yoktu):
- 3 seçenek: `agir` "Kaygı ağır basıyor" · `gelgit` "Değişken — güne göre" · `sakin` "Genelde sakinim".
- Her seçime kaygı-duyarlı adaptif yanıt (`role=status`, aria-live). radiogroup + klavye.
- "Seriyi koru" (anglicism değil) TALIMAT v2 kararı — Panel günlük görevlerinde kullanıldı.

## Öğrenci Paneli — duyarlılık mühendisliği (SPRINT1'de olmayan yük)
Panel ilk breakpoint turunda **10 FAIL** verdi (kompozit dashboard); giderildi:
- 3 kırılım: SideNav çökme ≤1023 · içerik-stack (hero/KPI/two-col) ≤1100 · kompakt ≤560.
- Topbar narrow-wrap (search kendi satırına) + `⌘K`/birim etiketleri (gün/XP) kompaktta gizli.
- Ders satırı kompakt yoğunlaştırma (θ + trailing % gizli, minWidth küçültme) + container padding daralt.
- search `<input>` `minWidth:0` (intrinsic ~170px flex-shrink'i bloke ediyordu) · "Tümü →" hit≥44.
- Onboarding "Bu soruyu geç" linkBtn 17→44px (hit hedefi).

## Kopya sapmaları (ONAY BEKLER)
1. **Onboarding "Devam et" CTA** — ton adımı buton etiketi **DC'den çıkarılamadı** (çıkarım). Diğer §C0 kopya birebir.
2. **Hesap Kurtarma e-posta hint'i** — SPRINT1 ile aynı absence-dili nötrleme deseni ("yarım görünüyor").

## Diğer sapmalar
- **coral-CTA:** onaylı — dolgu `coralCtaBg #C2452B` + beyaz; parlak `#FF6F5C` yalnız aksan/glow (ADR-007).
- **Panel KPI/haftalık:** §D statik değerler (mock persona'da bu alanlar yok) — açıkça §D-mock işaretli.
- **Panel `gün önce`** son sınav: `Date.now()` — story sabit tarih değil, göreli. jsdom testte tolere.
- Backstop bitmaps gitignore → ekran story'leri için yerel re-baseline gerekir (`npm run kiro:visual:ref`).

## Kalibrasyon — SPRINT1 formülü doğrulaması
SPRINT1 tahmini: 40 ekran ≈ **44–52 birim**; composite döngü ekranları ~1.5–2.0, basit paneller ~0.7.

SPRINT2 ölçülen (infra sonrası marjinal):
| Ekran | tip | birim | not |
|---|---|---|---|
| Hesap Kurtarma | 4-adım wizard + canlı doğrulama | ~1.2 | form state-machine; SPRINT1 Giriş'e yakın |
| Onboarding | 3-durum + calib mock + §C0 | ~1.5 | §C0 DC-çıkarım + stepper bespoke |
| Öğrenci Paneli | composite dashboard (7 blok) | ~2.3 | **~2.0 taban + ~0.3 duyarlılık-remediation** |

**Bulgu:** composite dashboard (~2.0) SPRINT1 üst-sınır tahminini **doğruladı**; sapma <%40 → formül korunur.
**Yeni sinyal:** yoğun-grid dashboard'lar (Panel, Öğretmen/Veli Paneli, Lig) breakpoint'i ilk turda
GEÇMEZ — SPRINT1 iki ekranı geçmişti. Bu sınıfa **+0.3 duyarlılık-remediation tamponu** eklenmeli.
Revize: kalan 39 ekran ≈ **46–55 birim** (composite-yoğun S3–S5'te üst-sınır). Basit paneller (Ayarlar,
Bildirim) hâlâ ~0.7. Envanter §E bağımlılık grafiği: QuestionCard seti bir kez yapılınca çekirdek-döngü ucuzlar.

## Komutlar
- `npm run build-storybook && node scripts/kiro-breakpoints.mjs` — breakpoint matrisi (5 ekran, otomatik türetme)
- `npx vitest --run src/kiro/screens/` — ekran RTL+axe
- `node ../design/scripts/kanon-lint.mjs src/kiro` — kanon
