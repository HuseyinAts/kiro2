# Faz 3 · SPRINT4 — Adaptif Test + Harmanlanmış Deneme + Sınav Sonuç (2026-07-22)

Kapsam: 3 ekran — çekirdek-döngü II. **Grup 3 (çekirdek döngü) TAMAM (6/6).** Tema: üçü de paper.
Süreç: **keşif workflow → build → adversarial review workflow → fix**.

## DoD sonuçları

| Ekran | tema | axe | breakpoint | kanon | tsc | vitest | commit |
|---|---|---|---|---|---|---|---|
| Adaptif Test | paper | ✅ | ✅ 7/7 | ✅ 0 | ✅ 0 | ✅ 7 | `48f8ca0c6`+`738849cba` |
| Harmanlanmış Deneme | paper | ✅ | ✅ 7/7 | ✅ 0 | ✅ 0 | ✅ 4 | ↑ |
| Sınav Sonuç | paper | ✅ | ✅ 7/7 | ✅ 0 | ✅ 0 | ✅ 3 | ↑ |

- **Breakpoint:** 13 ekran-story × 7 = **91/91**. **vitest:** tam kiro **33/33 dosya** (aşağıdaki flake notu).

## Test-flake kök-neden (çözüldü)
Tam suite bir koşuda "2 failed" verdi ama her dosya tek/küçük-grup **geçiyor**. Kök neden: **flaky axe-timeout**
(jsdom+axe-core CPU-ağır; 33 dosya paralel → çekişme → bazı 20s axe testleri timeout). Neden bulunamadı:
(1) flake non-deterministik (her koşuda yer değiştirir); (2) grep vitest'in `❯`/`×` Unicode + ANSI kodlarını
yakalayamadı → gerçek hata mesajı görülemedi. **Çözüm:** TAP reporter (düz `ok`/`not ok`) + dosya-izolasyon →
**33/33 geçen, 0 not ok** doğrulandı. SPRINT4 değişiklikleri regresyon getirmedi.

## Adaptif Test
- Tam ekran (SideNav yok) + **motor paneli** (θ/yakınsama SVG/SE — ekranın kimliği). Motor **tümüyle sunucu
  değerleriyle çizilir** (postCatNext); istemci IRT/eşik/durdurma HESAPLAMAZ. `kalanTahmini`/`güvenilirlik`
  review sonrası sunucuya taşındı (eşik 0,30 tek kaynak). Doğru/yanlış geri bildirimi **YOK** (yerleştirme, ceza yok).
- 'Emin değilim' = `secim:null`; `maddeId` idempotent; QuestionCard seçenek deseni kopyala-uyarla (yeni composite yok).
- Klavye: 1-5/A-E seç · Boşluk odaklı şıkkı seç · **Enter=Cevapla** (DoD).

## Harmanlanmış Deneme
- Lobi — SideNav(deneme) + rationale + coral oturum kartı + interleaving görsel (**harman/bloklu toggle üretimde kalır**,
  harmanlı başlar) + karşılaştırma kartları (+/−/! tipografik) + oturum bileşimi. `getReviewTopics().slice(0,4)`+`getTopics` join.
  'Denemeyi başlat' → `/cozum/harman-{id}`. Empty: onaylı sakin ton.

## Sınav Sonuç
- **Net-birincil** (net'ler sıralamadan önce DOM'da; sıralama review sonrası 15px+çerçeveli → görsel de-emphasis).
  '**Tahmini sıralama · yalnız yön göstergesi**' BİREBİR. **ConfettiDawn YOK**. Yanlış-stat zemini **#FBE8E2** (#FEF2F2 değil).
  ProgressRing halka (ariaLabel 'Doğru oranı yüzde {n}') + ProgressBar ders barları reuse. AI metni **sunucudan** (istemci şablon doldurmaz).

## Adversarial review — 0 blocker · 2 major · minorlar → giderildi
Kopya boyutu StructuredOutput retry-cap ile düştü → **ayrı odaklı agent ile yeniden koşuldu** (verbatim dökümü yok, yalnız çelişki).
| # | sev | kusur | fix |
|---|---|---|---|
| 1 | major | Harman 'HARMANLANMIŞ' rozeti beyaz metin #FF6F5C (AA-fail) | coralCtaBg #C2452B |
| 2 | major | Sınav Sonuç sıralama net'lerle aynı 27px (net-birincil ihlali) | 15px + çerçeveli kutu |
| 3 | minor | Adaptif kalanTahmini/güvenilirlik istemcide | sunucuya taşındı (CatNextResult) |
| 4 | minor | Adaptif 'Enter=Cevapla' eksik | eklendi + Boşluk-seç + bitiş odak-duyuru |
| 5 | minor | Harman lejantı aria-hidden | okunabilir (aria-hidden yalnız renk kutusu) |
| 6 | minor | SonucPage israf getSubjects | kaldırıldı |

**Sunucu-otoriter boyut TAM TEMİZ** (0 ihlal): Adaptif θ/SE/seviye/durdurma sunucudan, secim:null; Sonuç salt-okur, AI sunucudan.

## Kopya çelişkileri (canon-tiebreaker ile çözüldü)
Hepsi DC-simülasyon→sunucu veya DC-vs-spec→spec/kanon: 'tamamlandı ✓'→SVG; Emin değilim=secim:null; coral iki-katman;
Matematik chip tek-stil; durdurma sunucuda; TYT tag #EEF3F8 (DC parlak-mavi değil); Harman default HARMANLI; getMe adı.
Genuine insan-kararı çelişki YOK.

## Ertelenenler (bilinen desen / DC-sadık)
- Harman TYT/AYT etiketi kaba `ders→tür` (DC-prototip formülü; üretimde sunucu doğru türü verir).
- Sınav Sonuç trend '+8,5 net' + Adaptif kalanTahmini: mock sunucu-sim; canlı openapi alanları Faz 4 (açık noktalar).

## Kalibrasyon
| Ekran | tip | birim | not |
|---|---|---|---|
| Adaptif Test | özgün (motor paneli + yakınsama SVG + CAT döngü) | ~2.6 | QuestionCard seçenek deseni reuse (copy-adapt); motor bespoke |
| Harmanlanmış Deneme | lobi (SideNav reuse) | ~1.6 | ağırlıkla özgün layout, kabuk primitifleri |
| Sınav Sonuç | net-birincil (ProgressRing/ProgressBar reuse) | ~1.9 | ~%70 özgün + %30 atom |

**Grup 3 çekirdek döngü TAMAM.** İlerleme: **11/42 ekran + 1 composite (QuestionCard).**
Sonraki gruplar (Planlama/Hub/Oyunlaştırma/Roller/İş) Panel/SideNav/MasteryBadge/QuestionCard reuse eder → çarpan düşer.
