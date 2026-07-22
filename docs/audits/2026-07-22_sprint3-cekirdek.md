# Faz 3 · SPRINT3 — QuestionCard composite + Soru Çözme (2026-07-22)

Kapsam: 1 paylaşılan composite (QuestionCard) + 1 ekran (Soru Çözme). Çekirdek-döngü I'in
ilk yarısı. Tema: **paper** (çalışma ekranı — koyu zemin YASAK). Kaynak: SPRINT3_SPEC §A,
`KIRO2 Soru Cozme.dc.html`, kiro-api.js. Süreç: **keşif workflow → build → adversarial review workflow → fix**.

## DoD sonuçları

| Öğe | tema | axe | breakpoint | odak halkası | kanon | tsc | vitest | commit |
|---|---|---|---|---|---|---|---|---|
| QuestionCard (composite) | paper | ✅ | — (padded) | ✅ | ✅ 0 | ✅ 0 | ✅ 9 | `42d555985`+`8c7698c82` |
| Soru Çözme (ekran) | paper | ✅ | ✅ 7/7 | ✅ `:focus-visible` | ✅ 0 | ✅ 0 | ✅ 6 | ↑ |

- **Breakpoint matrisi:** 6 ekran × 7 genişlik = **42/42** (Soru Çözme ilk turda 7/7 temiz).
- **vitest:** SPRINT3 15 test + tam kiro regresyon **157/157**. QuestionCard'ın **ayrı RTL seti** (radiogroup, klavye, review, işaretle, axe).
- **Veri:** `configureKiroApi` mock; `getQuestionSet('mat','Türev')` (STRIP) + `postAnswer` (sunucu grading).

## Mimari kararı — QuestionCard kontrollü/sunum composite
`dogru`/çözüm/neden'i **hesaplamaz**; yalnız `sonuc` (postAnswer→AnswerResult) prop'undan alır.
Ekran (Soru Çözme) API'yi sahiplenir, `result`'ı aşağı geçirir → sunucu-otoriter akış ekranda,
composite saf/test-edilebilir. Neden Geri Bildirim · Adaptif Test · Harmanlanmış Deneme aynı composite'i kullanacak.

## Sunucu-otoriter (kanon) — adversarial review TAM TEMİZ
Review'in 4 kontrolü de canlı kodda geçti (0 bulgu): QuestionCard prop'unda `dogru` yok · ekran
`SoruSetItem` (dogru alanı yok) tutar · getQuestionSet açık Pick ile strip · self-grade yalnız
mock `postAnswer` vekilinde (sözleşme notu), live'da `POST /questions/{id}/answer`.

## Adversarial review çıktısı (workflow: 4 boyut) — 0 blocker · 3 major · 4 minor → HEPSİ giderildi
| # | sev | kusur | fix |
|---|---|---|---|
| 1 | major | Ok tuşları cevabı ANINDA/geri-alınamaz gönderiyordu (klavye tuzağı + ←/→ çakışması) | Ok = yalnız roving odak; gönderim 1-5/A-E · Enter/Space · tık |
| 2 | major | Geri bildirim kopyası DC'den noktalama/büyük harf sapmış | DC-birebir: "Güzel iş. Yine de…" / "Yanlış — hadi nedenini görelim" başlık noktasız |
| 3 | major | Soru Navigatörü 4-satır lejantı (Cevaplanan/Şu anki/İşaretli/Boş) eksik | Lejant eklendi (DC birebir) |
| 4 | minor | Review harf rozetleri beyaz metin AA-altı (2.6:1) | Derin ton (#047857 / coralCtaBg) — iki-katman kanonu tutarlı |
| 5 | minor | Header yükleme anında "0 soru" | "…" placeholder |
| 6 | minor | Geri bildirim aria-live=assertive | polite (sakin ton) |
| 7 | minor | Cevap sonrası odak body'ye düşüyor | odak Çözüm bölümüne taşınıyor |

## Kaygı-tonu & kanon
- Yanlış = sıcak amber Callout "birlikte bakalım" + review satırı terracotta (#FCEDE8/#F0A593);
  **alarm-kırmızısı YOK**. Doğru = ölçülü ("Güzel iş. Yine de mantığı pekiştirelim.").
- Sayaç **pasif**: amber, geri sayar, 0'da durur — kırmızıya dönmez/yanıp sönmez/baskı yok.
- Coral iki-katman: parlak #FF6F5C yalnız kenar/glow; metin-taşıyan dolgu coralCtaBg #C2452B.
- Hareket YOK (transition/animation sıfır) → kanon RM-guard gerekmez; ilerleme şeridi width'i geçişsiz.

## Kopya durumu (ONAY BEKLER — inferred)
Soru Çözme DC **kanon-temiz** → keşifte copyConflicts:[]; görünür kopyanın TAMAMI birebir.
DC'de olmayan, çıkarım yapılan 3 dize onay bekliyor:
1. ErrorState: "Sorular şu an gelmedi." + sakin-amber gövde (DC'de hata kopyası yok).
2. EmptyState: "Bu turu tamamladın." + "Planıma dön" (DC'de boş-set kopyası yok).
3. Pending: "Cevabın değerlendiriliyor…" (POST uçuşta göstergesi — DC'de yok).

## Ertelenenler (kod-yorumlu)
- Cevap POST hatası → yerel kuyruk + `/sync/events` idempotent (şimdilik sessiz revert + tekrar-dokun).
- "Seti Bitir"/"Seti bitir" → Sınav Sonuç ekranı (Sprint 4); şu an no-op.
- Sokratik link `/sokratik` → Sprint 4 proxy.

## Kalibrasyon — çekirdek-döngü composite amortismanı
| Öğe | tip | birim | not |
|---|---|---|---|
| QuestionCard | paylaşılan composite (radiogroup + review + çözüm) | ~1.6 | bir kez; Neden/Adaptif/Deneme'de yeniden kullanılır |
| Soru Çözme | tam ekran (timer + navigatör + klavye + 3 durum) | ~1.8 | ilk turda breakpoint 7/7 temiz |
| Adversarial review + fix | 4-boyut workflow + 3 major | ~0.5 | kalite tamponu |

**Bulgu:** composite yatırımı (~1.6) çekirdek-döngü'nün kalan 5 ekranını ucuzlatır (Neden Geri Bildirim
QuestionCard'ın review state'ini + sağ ray'ı ekler; Adaptif Test/Deneme QuestionCard + postCatNext).
SPRINT1 formülü (composite bir kez → çekirdek-döngü ucuzlar) **doğrulandı**. Kalan 37 ekran ≈ **43–52 birim**
(composite paylaşımı sayesinde S3 sonrası revize aşağı). Adversarial-review adımı yoğun-etkileşim
ekranlarında (klavye/state) **P0 kabul** — 3 major kusuru mekanik kapılar (kanon/tsc/axe-jsdom) yakalayamadı.

## Komutlar
- `npm run build-storybook && node scripts/kiro-breakpoints.mjs` — breakpoint (6 ekran)
- `npx vitest --run src/kiro/ui/QuestionCard.test.tsx src/kiro/screens/SoruCozmePage.test.tsx`
- `node ../design/scripts/kanon-lint.mjs src/kiro`
