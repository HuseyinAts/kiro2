# Faz 3 · SPRINT3-B — Neden Geri Bildirim + FSRS Tekrar (2026-07-22)

Kapsam: 2 ekran (çekirdek-döngü I'in ikinci yarısı) + Soru Çözme durum-kopya senkronu.
Kaynak: SPRINT3_SPEC §B/§C, ilgili DC'ler. Tema: ikisi de **paper**. Süreç: **keşif workflow →
build → adversarial review workflow → fix**.

## DoD sonuçları

| Ekran | tema | axe | breakpoint | kanon | tsc | vitest | commit |
|---|---|---|---|---|---|---|---|
| Neden Geri Bildirim | paper | ✅ | ✅ 14/14 (2 story) | ✅ 0 | ✅ 0 | ✅ 4 | `7c82330f2` |
| FSRS Tekrar (sayfa+overlay) | paper | ✅ | ✅ 14/14 (2 story) | ✅ 0 | ✅ 0 | ✅ 6 | `2bcf1387c` |
| Soru Çözme kopya-sync | paper | ✅ | — | ✅ 0 | ✅ 0 | ✅ | `a59e3de95` |
| Review remediation | — | — | — | ✅ 0 | ✅ 0 | ✅ | `408e2bf7c` |

- **Breakpoint:** `kiro:breakpoints` → 10 ekran-story × 7 = **70/70** (Neden Yanlis/Dogru + FSRS Sayfa/Oturum dahil).
- **vitest:** tam kiro **166/166**. FSRS'nin overlay klavye/resume testleri (Boşluk=göster, 1-4=derece, "Tekrara devam et") ayrı.

## Soru Çözme durum-kopyaları (onaylı, spec-sync)
- ErrorState: "Sorular şu an gelmedi — senlik bir şey değil." + "Yeniden dene".
- Cevap-POST kuyruğu: "Cevabın güvende — bağlantı gelince gönderilir." (yeni onaylı).
- EmptyState: "Bu turu tamamladın." + "Panele dön". Pending: "Cevabın değerlendiriliyor…".
- QuestionCard geri bildirim aria-live **assertive** (SPEC §161 — önceki review-fix polite'ı geri alındı; spec authoritatif).

## Neden Geri Bildirim
- SideNav(practice) + orta sütun (sonuç bandı + soru özeti + "Neden?" bloğu) + sağ ray (Hafıza motoru/FSRS coral
  gradyan + Kavram hâkimiyeti MasteryBadge trend-down + İlgili kavramlar). ≤1100px sağ ray gizli (§B onaylı).
- **Glyph→SVG (kanon):** DC'deki tik/çarpı text-glyph'leri bespoke SVG'ye çevrildi.
- İçerik TÜMÜYLE `AnswerResult`'tan (salt-okur). `AnswerResult` genişletildi: fsrsNextDays/mastery/relatedConcepts/nedenYanlis (sunucudan).

## FSRS Tekrar
- Sayfa: header + hero (coral gradyan {n} kart + Unutma eğrisi SVG) + 3 stat + hafıza gücü (vade chip + güç barı) + 7-gün yükü.
- **Overlay (modal):** SORU → "Cevabı göster" → CEVAP + 4 derece; focus trap + Esc + aria-modal + scroll kilidi;
  klavye **Boşluk=göster · 1-4=derece** (aria-keyshortcuts); bitişte ConfettiDawn (RM-guard'lı).
- **Sunucu-otoriter:** aralık önizlemeleri `getReviewSession.previews` (istemci FSRS hesaplamaz); `postReviewGrade(kartId)`.

## Adversarial review — 0 blocker · 4 major · 7 minor → HEPSİ giderildi
Yoğun-etkileşim P0 kuralı **doğrulandı**: 4 major'ı mekanik kapılar (kanon/tsc/axe-jsdom/breakpoint) yakalayamadı.
| # | sev | kusur | fix |
|---|---|---|---|
| 1 | major | Focus trap geçişlerde sızıyor (odak body'ye → Esc/1-4 ölü) | Her geçişte overlay-içi birincil aksiyona programatik odak (data-oto-odak) |
| 2 | major | "Boşluk=göster" yok + açılış odağı yıkıcı Kapat'ta | Boşluk dalı + ilk odak "Cevabı göster" (native + aria-keyshortcuts) |
| 3 | major | Derece konu ile anahtarlı (aynı konu çok kart çakışır) | ReviewCard.id + postReviewGrade(kartId) → /review/{kartId}/grade |
| 4 | major | Hero CTA "Tekrara devam et" varyantı eksik | tekrarlanmis izleme + koşullu etiket + devam davranışı |
| 5 | minor | Coral gradyan küçük beyaz metin AA-altı | Gradyan koyulaştırıldı #C2452B→#E0593F, opacity kaldırıldı |
| 6 | minor | ConfettiDawn `infinite` (WCAG 2.2.2) | Sonlu (1 forwards) + 5sn'de self-clear |
| 7 | minor | h1 yok / seviye atlama | h1 (Neden/FSRS başlık) + Neden "Neden?" h2; FSRS Empty gövde onaylı; stat mock işaretli |

## Kopya çelişkisi (canon-tiebreaker ile çözüldü)
- FSRS hafıza-gücü alt başlığı: DC `"Bugün" etiketliler tekrar istiyor.` vs SPRINT3_SPEC §118 `kırmızılar…`.
  Spec'in kendi line-5 kuralı ("Piksel referansı her zaman DC") → **DC seçildi**. Renk-tek-sinyal olmadığı için a11y de daha iyi.
- Diğerleri kanonla: derece aralıkları sunucudan (sabit değil); glyph→SVG; empty onaylı.

## Ertelenenler (kod-yorumlu / bilinen desen)
- 7-gün yükü: API yok (açık nokta #1) → mock. Tutma%/haftalık: API alanı yok → mock işaretli.
- Modül-yükleme `configureKiroApi` — TÜM kiro ekranlarının ortak mock-demo deseni (provider'a taşıma ayrı refactor).
- Bitiş "Serin {seri+1}. güne" — DC-sadık optimistik; üretimde oturum-tamamlanma yanıtından.
- Grade-interval mock previews — sunucu FSRS projeksiyonunu simüle eder (client hesaplamaz).

## Kalibrasyon
| Ekran | tip | birim | not |
|---|---|---|---|
| Neden Geri Bildirim | bespoke (3 imza blok + sağ ray) | ~2.0 | QuestionCard review'i reuse ETMİYOR (monolitik) — 3 blok net-new |
| FSRS Tekrar | en karmaşık: sayfa + overlay + eğri SVG + focus trap + confetti | ~2.6 | + review remediation ~0.5 (4 major) |

**Bulgu:** çekirdek-döngü'nün 2. yarısı composite-amortisman görmedi (Neden bespoke, FSRS özgün overlay) —
SPRINT1 formülünün "composite paylaşımı" avantajı bu iki ekranda düşük. Adversarial-review yoğun-etkileşim
ekranlarında **kesin P0** (focus-trap/klavye kusurları yalnız adversarial pass ile yakalandı). Kalan 34 ekran ≈
**42–52 birim** (rol panelleri Panel'i reuse eder → ucuz; Sınav/Ödeme akışları yeni).

**İlerleme: 8/42 ekran + 1 paylaşılan composite (QuestionCard). SPRINT3 (çekirdek-döngü I) TAMAM.**
