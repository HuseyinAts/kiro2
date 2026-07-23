# KIRO2 — Faz 0-1 Kuruluş Durumu (2026-07-22)

**Faz 0 keşif ✅** — 4 hedef canlı kodda doğrulandı (`docs/audits/2026-07-22_faz0-kesif.md`, 8 agent):
- teacher/classes **VAR** (`teacher_classroom.py:98,138`); katılım kodu · code/rotate · `/me/class/join` · sınıf-varsayılanları **YENİ**.
- Lig **VAR** (`league_api.py`, loader:205) → **yeni `/league` YAZMA**; "sakin mod / sıralamayı gizle" ayarı **YENİ**.
- diary mood kayıt ucu + gizlilik guard'ı **VAR** (`diary_api.py:1266`, self-only) → yeniden kurma yok.
- ⚠ Sokratik prompt "evi" = **`enhanced_chat.py`** (SOCRATIC_SYSTEM_PROMPT + teaching_mode), bilge_alp DEĞİL — plan G düzeltmesi.

**Faz 1 kuruluş ✅** — DoD:
- `design/` = handoff kökü (flatten); `node design/scripts/kanon-lint.mjs frontend/src/kiro` çalışır.
- `frontend/src/kiro/{tokens,types,api,ui,screens}/` — tokens.ts/css + types.ts + api-client.ts + kiro-data.json birebir; theme.tsx foundation.
- `configureKiroApi({mode:'mock', mockData})` → `OrnekPage` GERÇEK mock veriyi render eder (RTL testi **PASS**).
- Doğrulama: kanon-lint **0 ihlal** (2 uyarı: tokens `#6B6478` — kaynak dosya paper+dusk ikisini de tanımlar, yanlış-pozitif) · scoped strict `tsc` **0 hata** · vitest **PASS**.
- ADR'ler `docs/adr/README.md` (design tek-dosya formatı). kanon-lint CI'da: `ci.yml` frontend-test adımı + `npm run kanon:lint`.
- Verbatim sapmalar (kayıt): import `./types`→`../types` · 2 doküman-yorumu "eksik" + 1 `⚠️` emoji neutralize · kullanılmayan `Question` import kaldırıldı.
- react-query v5 (ADR-006) **ERTELENDİ** — Faz 1 plain hooks; screen-state gerektiğinde (YAGNI).

---

# KIRO2 — Faz 2 Bileşen Kalite Kapısı (2026-07-22)

**20/20 bileşen ✅** — her biri story + RTL + axe + BackstopJS kapısından geçti.
- Storybook **10.5.3** (Vite 7 builder) + `@storybook/addon-a11y`; `.storybook/` config; `npm run storybook` / `build-storybook`.
- Piksel refleri `frontend/src/kiro/ui/__pixel_refs__/` (7 `.dc.html`; gitignore'lu Deckset'e bağımlı değil).
- Kalibrasyon trio: Button · Card · StatusChip. Kalan 17: **17-agent workflow fan-out** (kanon 0 + strict tsc 0 ilk geçişte).
- **Doğrulama:** vitest **115 test / 21 dosya PASS** · kanon-lint **0 ihlal** · scoped strict tsc **0** · BackstopJS **111 story → 222/222 ≤%1** (LOKAL dev gate: `npm run kiro:visual:ref|test`).
- Skeleton: kiroSweep (2.6s) + 3sn güvence + gün-mantrası (`role=status`) — spec-mandated, story+test dahil.

**A11y bulguları (çözüldü — GİZLENMEDİ):**
- ProgressBar: `role=progressbar` erişilebilir ad yoktu → **`ariaLabel` prop eklendi** (fix).
- ChatBubble(me) · Button primary · SideNav-aktif: beyaz metin coral `#FF6F5C` üzerinde ~2.75:1 < AA idi → **düzeltildi** (yeni token `coralCtaBg = #C2452B`; beyaz metin 5:1, `#C2452B`/`#FFF3EE` 4.69:1 — AA ✓). Bright coral yalnız aksan/glow için kalır.

**Sapmalar → ADR-007** (`docs/adr/README.md`).

---

# KIRO2 — Faz 3 · SPRINT1 Durumu (2026-07-22)

**2/2 ekran ✅** — Giriş & Kayıt · Ödevlerim (rapor: `docs/audits/2026-07-22_sprint1-ekranlar.md`).
- **Tema:** her ikisi **paper** (Giriş "dusk" talimatı → SPEC/DC gereği **paper** onaylandı; route-bazlı, toggle YOK).
- **DoD:** axe temiz · breakpoint **14/14** (390→1440 overflowX=0 + hit≥44 ≤1199, `npm run kiro:breakpoints`) · odak halkası `:focus-visible` · kanon 0 · tsc 0 · vitest **13/13**.
- **Veri:** configureKiroApi mock + MSW handler seti (`kiro/api/mswHandlers.ts`, kiro-api.js'ten türetildi).
- **Coral-CTA:** `coralCtaBg #C2452B` + beyaz (onaylı sapma). **Button md 40→44px** (SPEC A1 + hit≥44).
- **Kopya sapması (ONAY BEKLER):** 2 dize spec'in kendi "absence-dili yok" kuralı gereği nötrlendi — e-posta hint "yarım görünüyor"; liste dipnotu "Geciken ödev kapanmaz — 'bekliyor'".
- **Kalibrasyon:** ekran-port infra (template + MSW kalıbı + `kiro:breakpoints` Playwright denetçisi) tek-seferlik kuruldu; kalan 40 ekran ≈ **44–52 birim** (S2'de yeniden ölç). Detay raporda.

---

# KIRO2 — Faz 3 · SPRINT2 Durumu (2026-07-22)

**3/3 ekran ✅** — Hesap Kurtarma · Onboarding (§C0 ton) · Öğrenci Paneli (rapor: `docs/audits/2026-07-22_sprint2-ekranlar.md`).
- **Tema:** 3'ü de **paper** (route-bazlı, toggle YOK).
- **DoD:** axe temiz · breakpoint **35/35** (5 ekran × 7 genişlik; denetçi index.json'dan otomatik türetir) ·
  odak halkası · kanon 0 · tsc 0 · vitest **15/15** (Panel 5 + Onboarding 5 + Kurtarma 5).
- **§C0 ton adımı:** DC'den birebir çıkarıldı (agir/gelgit/sakin + adaptif yanıt); "Seriyi koru" (TALIMAT v2).
- **Panel duyarlılığı:** kompozit dashboard 10 breakpoint-FAIL → 3 kırılım + topbar-wrap + ders-kompakt ile 0.
- **Kopya sapması (ONAY BEKLER):** Onboarding "Devam et" CTA (DC-çıkarım) · Kurtarma e-posta hint "yarım".
- **Kalibrasyon:** composite ~2.3 birim (2.0 taban + 0.3 duyarlılık); SPRINT1 formülü <%40 sapma → korunur. Detay raporda.

**İlerleme: 5/42 ekran portlu** (Giriş · Ödevlerim · Hesap Kurtarma · Onboarding · Öğrenci Paneli).

---

# KIRO2 — Faz 3 · SPRINT3 Durumu (2026-07-22)

**QuestionCard composite + Soru Çözme ✅** (rapor: `docs/audits/2026-07-22_sprint3-cekirdek.md`).
- **QuestionCard** (ui/, paylaşılan composite): kontrollü/sunum — `dogru`/çözüm/neden'i HESAPLAMAZ,
  `sonuc` (postAnswer→AnswerResult) prop'undan alır. Neden/Adaptif/Deneme'de yeniden kullanılacak.
- **Soru Çözme** (ekran): tam ekran odak (SideNav yok, paper), pasif amber sayaç, tap→postAnswer→review,
  Soru Navigatörü + lejant, ←/→/M klavye, 3 durum.
- **Süreç:** keşif workflow → build → **adversarial review workflow** (4 boyut) → 3 major + 4 minor fix.
  Sunucu-otoriter boyut TAM TEMİZ. **Kapı:** kanon 0 · tsc 0 · vitest 157/157 · breakpoint 42/42.
- **Kopya (ONAY BEKLER):** DC kanon-temiz (görünür kopya birebir); DC'de olmayan 3 inferred dize —
  ErrorState/EmptyState/pending (raporda).
- **Kalibrasyon:** composite ~1.6 + ekran ~1.8; SPRINT1 "composite→çekirdek ucuzlar" formülü doğrulandı.

**İlerleme: 6/42 ekran portlu** (+ 1 paylaşılan composite: QuestionCard).

---

# KIRO2 — Faz 3 · SPRINT3-B Durumu (2026-07-22)

**Neden Geri Bildirim + FSRS Tekrar ✅** — çekirdek-döngü I TAMAM (rapor: `docs/audits/2026-07-22_sprint3b-neden-fsrs.md`).
- **Neden Geri Bildirim**: SideNav(practice) + sonuç bandı + "Neden?" bloğu + sağ ray (FSRS/hâkimiyet/ilgili);
  DC glyph'leri bespoke SVG; içerik tümüyle AnswerResult'tan (genişletildi).
- **FSRS Tekrar**: sayfa (hero + Unutma eğrisi SVG + hafıza gücü + 7-gün) + tekrar-oturumu overlay (focus trap +
  Esc + Boşluk/1-4 klavye + RM-guard ConfettiDawn). Aralıklar sunucudan; postReviewGrade(kartId).
- **Soru Çözme kopya-sync**: ErrorState/kuyruk/EmptyState onaylı kopyaya çekildi; aria-live assertive (SPEC §161).
- **Adversarial review** (4 boyut): 0 blocker · 4 major (FSRS overlay focus-trap/Boşluk/kartId/CTA) · 7 minor → hepsi giderildi.
  Yoğun-etkileşim **P0 doğrulandı** — 4 major yalnız adversarial pass ile yakalandı (mekanik kapılar kaçırdı).
- **Kopya çelişkisi**: FSRS alt başlık DC vs spec §118 → DC (line-5 kuralı). ConfettiDawn `infinite`→sonlu (WCAG 2.2.2).
- **Kapı:** kanon 0 · tsc 0 · vitest 166/166 · breakpoint 70/70 (10 story × 7).

**İlerleme: 8/42 ekran + 1 composite (QuestionCard). Grup 3 çekirdek-döngü I (Soru Çözme·Neden·FSRS) TAMAM.**

---

# KIRO2 — Faz 3 · SPRINT4 Durumu (2026-07-22)

**Adaptif Test + Harmanlanmış Deneme + Sınav Sonuç ✅** — Grup 3 çekirdek döngü TAMAM (rapor: `docs/audits/2026-07-22_sprint4-cekirdek-II.md`).
- **Adaptif Test**: tam ekran + motor paneli (θ/yakınsama/SE, SUNUCU değerleriyle çizilir; istemci IRT hesaplamaz).
  Geri bildirim yok (yerleştirme); 'Emin değilim'=secim:null; QuestionCard seçenek deseni copy-adapt; Enter=Cevapla.
- **Harmanlanmış Deneme**: lobi; harman/bloklu toggle üretimde kalır; getReviewTopics().slice(0,4); →/cozum/harman-{id}.
- **Sınav Sonuç**: net-birincil (sıralama küçük+çerçeveli); 'yalnız yön göstergesi' birebir; ConfettiDawn YOK; #FBE8E2.
- **Adversarial review** (4 boyut, kopya boyutu odaklı re-run): 0 blocker · 2 major (Harman rozet coral, Sonuç sıralama
  de-emphasis) · minorlar → hepsi giderildi. Sunucu-otoriter TAM TEMİZ.
- **Test-flake**: tam-suite flaky axe-timeout (paralel yük) — TAP reporter + izolasyon ile 0 gerçek hata (33/33 dosya).
- **Kapı:** kanon 0 · tsc 0 · vitest 33/33 dosya · breakpoint 91/91 (13 story × 7).

**İlerleme: 11/42 ekran + 1 composite (QuestionCard). Grup 3 (Çekirdek döngü) TAMAM.**

---

# KIRO2 — Faz 3 · SPRINT5 Durumu (2026-07-22)

**4/4 ekran ✅** — Haftalık Plan · Öğrenme Yolu · Bilgi Atomları · Çalışma Modları — **Grup 4 (Planlama) TAMAM** (rapor: `docs/audits/2026-07-22_sprint5-planlama.md`).
- **Tema:** dördü de **paper**. Süreç: keşif workflow (6 ajan) → paylaşılan-infra → build workflow (4 ajan) → gate → adversarial review (4 boyut) → fix.
- **Infra (mock-katmanı, üretime sızmaz):** `getPlanWeek()`/`buildMockPlanWeek()` + `PlanWeek` tipleri (açık-nokta 1) · `Atom.enZayif` + `markEnZayif()` (açık-nokta 2, sunucu-otorite sim) · MSW `/plan/week`·`/curriculum`(+`:ders`)·`/topics/:konu/atoms`. kiro-data.json'a plan İÇERİĞİ eklenmedi.
- **Adversarial review:** 11 bulgu → **8 fix** (h1 italik→düz, gün h1/h2, "Serbest" AA, mod-CTA AA `ctaRenk`, ProgressRing 11px, EmptyState bekleyiş-dili) · 2 red (SideNav 1023=rail kuralı; chip=spec "zayıf konular") · 1 ertele (chip roving-tabindex).
- **Breakpoint bug (2):** HaftalikPlan `minmax(0,1fr)` (min-content blowout); OgrenmeYolu içerik-sarmalayıcı `boxSizing:border-box` (content-box padding taşması — 2 yanlış hipotez sonrası **parent-zincirli Playwright teşhisiyle** bulundu).
- **Kapı:** kanon **0 ihlal** · tsc **0** · vitest **37 dosya / 203 test** · breakpoint **119/119** (17 story × 7) · axe temiz.

**İlerleme: 15/42 ekran + 1 composite (QuestionCard). Grup 4 (Planlama) TAMAM.**
Sonraki: Grup 5 Hub/duygusal — **Bugün/Şafak = İLK dusk ekran** (S6).

---

# KIRO2 — Faz 3 · SPRINT6 Durumu (2026-07-22 · İLK DUSK)

**3/3 ekran ✅** — Bugün/Şafak hub · Kutlama · Mola — **Grup 5 (Hub/duygusal) ilk yarısı TAMAM; İLK KOYU (dusk) EKRANLAR** (rapor: `docs/audits/2026-07-22_sprint6-duygusal-cekirdek-I.md`).
- **Tema:** üçü de **dusk**. Süreç: keşif workflow (6) → paylaşılan-infra → build workflow (3) → gate → adversarial review (4 boyut) → fix.
- **Dusk infra (İLK):** `.k-dusk` shell + `surf('dusk')` ilk ekrana bağlandı; `tokens.ts` dusk ikincil tonları (ink2/iconMuted/faded/body80, §7 kanonu); **`dawnSkyLinear` durak-yüzdeleri düzeltildi** (kanon gradyan, tokens.ts+css); `// kanon-allow: kutlama` (MOTION_KANON §5 dusk motion). DUSK CTA = parlak coral + **koyu mürekkep** (#2A1018 — paper'ın tersi, AA-güvenli). ConfettiDawn reuse.
- **Adversarial review:** 18 bulgu (çoğu dedup) → **tümü fix**. Mola 0; Bugün 1 (gradyan token); **Kutlama 7** (kurucu ajan DC dosyasını bulamadı → eyebrow uppercase, ödül-chip row, yıldız nokta, seviye-recompute, halo/CTA/mantra drift).
- **Test flake:** 2 axe-**timeout** (SPRINT5 ağır paper ekranlar, 40-dosya paralel yük) → 20s→40s bump (ihlal değil).
- **Kapı:** kanon **0 ihlal** · tsc **0** · vitest **40 dosya / 222 test** · breakpoint **147/147** (21 story × 7) · axe temiz.

**İlerleme: 18/42 ekran + 1 composite (QuestionCard). Grup 5 ilk yarısı TAMAM.**
Sonraki: Grup 5 ikinci yarısı (S7) — Geri Sayım · Başarımlar · Boss Savaşı (kırmızı istisnası boss-arena).

---

# KIRO2 — Faz 3 · SPRINT7 Durumu (2026-07-22 · GRUP 5 BİTER)

**3/3 ekran ✅** — Sınav Geri Sayım · Başarımlar · Boss Savaşı — **Grup 5 (Hub/duygusal) TAMAM (6/6)** (rapor: `docs/audits/2026-07-22_sprint7-duygusal-cekirdek-II.md`).
- **Tema:** üçü de **dusk** (Boss = kırmızı arena istisnası). Süreç: keşif workflow (6) → paylaşılan-infra → build workflow (3) → gate → adversarial review (4 boyut) → fix.
- **Infra (YENİ):** `lib/gunSayaci.ts` (`gunKalan`/`haftaKalan`, Math.max(1,…) DC alt-sınırı; YALNIZ Geri Sayım tüketir) · api-client `postBossSession`+`postBossAnswer` (mock server-sim; **sunucu-otorite:** correct/hasar/hp/kombo/can API yanıtından, Boss soruları `getQuestionSet` STRIP'li). **Boss KIRMIZI:** `// kanon-allow: boss-arena, kutlama` (kırmızı aile inline, 2026-07-04 onaylı; kullanıcı-hata TERRACOTTA, doğru şık YEŞİL).
- **Ekranlar:** Geri Sayım 2-varyant (default **kaygı-nötr** "gün saymaya gerek yok") · Başarımlar hâkimiyet halkaları (96px SVG, tierFromPct 40/65/85) + seri kilometre taşları · Boss ağır (arena + ejderha + combat döngüsü + zafer/yenilgi overlay + ConfettiDawn zaferde, HP role=progressbar + focus-trap).
- **Adversarial review:** 4 bulgu (3 dedup) → **2 fix** (GeriSayım haftaKalan Math.max alt-sınırı; Boss overlay Tab focus-trap) · 1 ertele (Başarımlar `siralama` prop = editör-prop, görünür kontrol değil). Boss server-otorite/kopya/kırmızı-scope/hareket-guard **TAM TEMİZ**.
- **Build-turu:** Boss HP `transition:width`→`transform:scaleX` (layout-anim yasak); Başarımlar `kazanilan` = ders + taş (DC birebir 8).
- **Kapı:** kanon **0 ihlal** · tsc **0** · vitest **43 dosya / 240 test PASS** (canlı doğrulandı) · breakpoint **175/175** (25 story × 7) · axe temiz.

**İlerleme: 21/42 ekran + 1 composite (QuestionCard). Grup 5 (Hub/duygusal) TAMAM (6/6).**
Sonraki: **Grup 6 Oyunlaştırma (S8)** — Lig · 1v1 Düello · Arkadaş Serisi · Seri Dondurma (lig ucu: önce backend keşfi).

---

# KIRO2 — Faz 3 · SPRINT8 Durumu (2026-07-22 · GRUP 6 TAMAM)

**4/4 ekran ✅** — Lig · 1v1 Düello · Arkadaş Serisi · Seri Dondurma — **Grup 6 (Oyunlaştırma) TAMAM** (rapor: `docs/audits/2026-07-22_sprint8-oyunlastirma.md`).
- **Tema (DC-kanıtından):** Lig/Arkadaş/Seri **paper**, Düello **dusk-arena** (`// kanon-allow: boss-arena, kutlama`). "Oyunlaştırma=dusk" naif tahmini DC ile çürütüldü.
- **Backend gerçeği:** `/leagues/*`, `/duel/*` (SSE+ELO), `/cozum-duellosu/*`, `/birlikte-streak/*` MEVCUT çıktı (session notları "yok" sanıyordu). "sakin-mod/sıralamayı-gizle", freeze mekaniği, friend sistemi backend'de YOK → Faz 3 mock-katmanı.
- **Kararlar (kullanıcı):** Düello **gerçek `/duel/*` SSE+ELO'ya bağlandı** (çift-kollu: live REST+EventSource / mock server-sim); Seri "%48 istatistiği" **çıkarıldı**; 4 ekran tek sprint.
- **Adversarial review (19 ajan, 4 boyut + bulgu-bazlı skeptik doğrulama):** P0 **0** · major **2** · minor **10** · phantom **0**. 2 major (Düello turSonucu mantık çelişkisi + CTA AA kontrast) + 9 minor **fix**; 1 **ertele** (#6 VS skor puan/galibiyet ayrımı — contract Faz 4).
- **Infra (additive, üretime sızmaz):** api-client +410 · types +147 · kiro-data +60 · msw +84. Düello soruları STRIP'li (doğru sızmaz).
- **Kapı:** kanon **0** · tsc **0** · vitest **47 dosya / 265 test PASS** · axe temiz. breakpoint (build-storybook) + canlı `/duel` SSE E2E → **operatör** (backend ayakta gerektirir).

**İlerleme: 25/42 ekran + 1 composite (QuestionCard). Grup 6 (Oyunlaştırma) TAMAM (4/4).**
Sonraki: **Grup 7 Roller (S9+)** — Veli Paneli · Öğretmen Paneli · Öğrenci Özeti · Veli Bağlama · Ödev Atama · Sınıf Kurulumu.

---

# KIRO2 — Faz 3 · SPRINT9-A Durumu (2026-07-23 · GRUP 7 kısmi 4/6)

**4/6 panel ✅** — Veli Paneli · Öğretmen Paneli · Öğrenci Özeti · Sınıf Kurulumu (rapor: `docs/audits/2026-07-23_sprint9a-roller.md`). Veli Bağlama (KVKK) + Ödev Atama **ayrı tur** (kullanıcı "ağırları ayır").
- **Tema:** 4'ü de **paper** (rol/panel/iş ekranı). Rol/gizlilik: Veli **SİZ-dili** + çocuk **salt-okur** (sohbet/AI/mood gizli); Öğretmen SİZ + roster salt-okur; Öğrenci Özeti salt-okur (tek yazma = ödev-ata link); Sınıf Kurulumu **DC SEN korundu** (DC>spec tiebreaker).
- **Backend gerçeği:** `/api/v1/teacher` + `/api/v1/parent` (email iki-taraf onay) MEVCUT → Faz 4 wiring; katılım-kodu/rotate/join + öğrenci Ödevlerim + zengin-atama alanları **YOK → mock**. Karar (kullanıcı): Veli Bağlama **DC kod-akışı + mock**.
- **Paylaşımlı `ui/WeeklyActivityBars`** (Veli+Öğretmen+ÖğrenciÖzeti; transform:scaleY layout-anim değil, RM-guard, per-bar SR metni).
- **Adversarial review (11 ajan, rol-gizlilik odaklı):** P0 **0** · major **2** · minor **2** · phantom **0** → hepsi fix (VeliPaneli yeşil-token AA `success→successTextOnLight` + rozet; OgrenciOzeti başlık h1→h2→h3; OgretmenPaneli negatif-delta amber).
- **Breakpoint:** SinifKurulumu kök-div `content-box` 12px yatay taşma → **deterministik Playwright teşhisi** (parent-zincir) → `box-sizing:border-box` fix → **0 FAIL / 280**. (Build+adversarial kaçırdı, mekanik kapı yakaladı — SPRINT8 dersi tekrar.)
- **Kapı:** kanon **0** · tsc **0** · vitest **52 dosya / 294 test PASS** · axe temiz · breakpoint **0 / 280**.

**İlerleme: 29/42 ekran + 1 composite (QuestionCard) + `ui/WeeklyActivityBars` (paylaşımlı). Grup 7 kısmi (4/6).**
Sonraki: **Grup 7 kalanı** — Veli Bağlama (KVKK kod-akışı) + Ödev Atama (Ödevlerim döngüsü) ayrı tur.

---

# KIRO2 — Faz 3 · SPRINT9-B Durumu (2026-07-23 · GRUP 7 TAMAM 6/6)

**2/2 ekran ✅** — Veli Bağlama · Ödev Atama — **Grup 7 (Roller) TAMAM (6/6)** (rapor: `docs/audits/2026-07-23_sprint9b-roller-kalan.md`).
- **Veli Bağlama (paper, KVKK):** SideNav YOK merkezi kart-akışı; **iki muhatap/iki dil** — veli **SİZ** 4-adım (Kod→Rıza→Bekle→Tamam) + öğrenci **SEN** 2-durum (Bekliyor→Tamam). Karar: **DC 6-haneli kod-akışı + mock** (IDOR-güvenli; gerçek /parent email-onay Faz 4). İç-içe checkbox-link FIX; consent-gate gerçek disabled; kod/consent/durum **sunucu-otorite** (istemci üretmez).
- **Ödev Atama (paper):** öğretmen "sana" meslektaş dili; konu **radiogroup** + öğrenci **checkbox** + θ **switch**; **θ-set kurulumu sunucuda** (istemci yalnız form gönderir); risk=amber; kaygı-varsayılanları kartı (kanon öğretir); Ödevlerim (SPRINT1) döngü sözleşmesi hizalı + OgrenciOzeti "ödev ata" CTA rotası hizalandı.
- **Infra:** metod-collision (getTopics/postAssignment/SinifOgrenci mevcut) → `getAtamaKonular`/`getAtamaRoster`/`postAtama` + `AtamaOgrenci` (SPRINT4 bozulmadı). Veli Bağlama uçları collision-free.
- **Adversarial review (4 ajan):** P0 **0** · major **0** · minor **2** · phantom **0** → 2 DC-kopya fix (Sınıfın; kaygı-madde kanon-güvenli, DC "eksik" yasağı). **Veli Bağlama tertemiz** (KVKK/server-otorite/checkbox-nesting/SEN-SİZ hepsi geçti).
- **Kapı:** kanon **0** · tsc **0** · vitest **54 dosya / 308 test PASS** · axe temiz · **breakpoint 0 FAIL / 329**.

**İlerleme: 31/42 ekran + 1 composite (QuestionCard) + `ui/WeeklyActivityBars`. Grup 7 (Roller) TAMAM (6/6).**
Sonraki: **Grup 8 İş & dayanıklılık (7)** — Abonelik · Ödeme · Plan Yönetimi · Ayarlar · Bildirim Merkezi · Alan Kütüphanesi · Çevrimdışı.

---

# KIRO2 — Faz 3 · SPRINT10-A Durumu (2026-07-23 · GRUP 8 kısmi 3/7)

**3/3 ekran ✅** — Bildirim Merkezi · Alan Kütüphanesi · Çevrimdışı (rapor: `docs/audits/2026-07-23_sprint10a-is-dayaniklilik.md`; keşif: `2026-07-23_sprint10-grup8-kesif.md`).
- **Tema:** 3'ü de **paper** (DC-kanıtlı, 7/7 Grup 8 paper). Dilimleme: **3 alt-tur** (kullanıcı) — S10-A basit 3 → S10-B billing zinciri → S10-C Ayarlar.
- **Kararlar (kullanıcı, keşif sonrası):** Ödeme/PSP saf-mock · öğrenci fiyat gizli→veli yönlendirme · sakin-mod+sıralamayı-gizle tek `KullaniciAyar`+tam davranış (S10-B/C'de uygulanır).
- **Infra (additive):** types +11 · api-client +6 metod · msw +6 route · kiro-data +3 anahtar. `Alan/AlanKey/DersKatalogEntry/KatalogUnite` REUSE; Plan* çakışması önlendi.
- **Adversarial (22 ajan, 4 boyut):** 12 doğrulandı / 6 phantom. 1 major (Alan `ink.faded2` AA 2.08:1 → `ink.muted`) + minör/nit fix (DC dipnot geri, akordeon DC-sadık sunucu-sayaç, Bildirim `<h1>`, Çevrimdışı 'bugün' sunucu-otorite + getMe tolere + minWidth guard) + test kapsamı.
- **Breakpoint:** ilk tur 5 FAIL (Alan akordeon `minHeight:36<44` hit-target) → `minHeight:44` → 0 FAIL.
- **Kapı:** kanon **0** · tsc **0** · vitest **57 dosya / 340 test PASS** · **breakpoint 0 FAIL / 364** · axe temiz.

**İlerleme: 34/42 ekran + 1 composite (QuestionCard) + `ui/WeeklyActivityBars`. Grup 8 kısmi (3/7).**
Sonraki: **S10-B billing zinciri** (Abonelik · Ödeme · Plan Yönetimi) → S10-C Ayarlar.

---

# KIRO2 — Faz 3 · SPRINT10-B Durumu (2026-07-23 · GRUP 8 billing zinciri, 6/7)

**3/3 ekran ✅** — Abonelik · Ödeme(+3DS mock) · Plan Yönetimi + paylaşılan VeliYonlendirmeKarti (rapor: `docs/audits/2026-07-23_sprint10b-billing.md`).
- **Tema:** 3'ü de **paper**. Kullanıcı kararları uygulandı: PSP saf-mock (3DS timer-sim, kart PCI UI-only) · öğrenci fiyat gizli→VeliYonlendirmeKarti (Abonelik+Plan+Ödeme guard) · `AbonelikPlan`/`AbonelikYonetim` ayrı ad · fiyat `veliDashboard.premium`+`roi` hizalı.
- **Infra (additive):** types +11 · api-client +8 metod · msw +8 route · kiro-data +2 anahtar + `screens/billing/VeliYonlendirmeKarti.tsx` (KVKK).
- **Ödeme composite:** 3-fazlı state machine (form→3ds→tamam); banka-decline amber; spinner RM-guard + bespoke stepper (role=list/aria-current).
- **Adversarial (23 ajan, 4 boyut):** 16 doğrulandı / 13 unique / 3 phantom. major (Abonelik `ink.faded2` AA→muted; Ödeme kart-input odak WCAG 2.4.7 + decline role=alert 4.1.3) + nit (CTA veli-kopya, öğrenci guard/MarkaBar KVKK, geri-aç sunucu-otorite refetch). Phantom: getAbonelik öğrenci-payload strip + 3DS re-poll = Faz 4.
- **Kapı:** kanon **0** · tsc **0** · vitest **61 dosya / 383 test PASS** · **breakpoint 0 FAIL / 455** · axe temiz.

**İlerleme: 37/42 ekran + QuestionCard + WeeklyActivityBars + VeliYonlendirmeKarti. Grup 8 kısmi (6/7).**
Sonraki: **S10-C Ayarlar** (composite + yeni `ui/Switch`; KullaniciAyar tek-kaynak + tam davranış) → Grup 8 TAMAM.

---

# KIRO2 — Faz 3 Ekran Port Takibi (43 ekran × 6 DoD — 42 port + 1 MVP-dışı bekleme)

2026-07-22: +1 Sınıf Kurulumu (S11). Tasarım Dili (public sayfa) ve E-posta & Bildirim (kopya sistemi spec'i) PORT EDİLMEZ — referans yüzeyleri.
2026-07-05: +3 yeni tasarım eklendi (Veli Bağlama · Öğrenci Özeti · Plan Yönetimi); 3DS bekleme
durumu Ödeme ekranının parçasıdır (ayrı satır değil). Çözüm Paylaş MVP DIŞI işaretlendi.

Sütunlar (URETIM_YOL_HARITASI Faz 3 DoD'si):
**PX** prototiple yan yana piksel karşılaştırma · **DUR** Skeleton/Empty/Error üç durum bağlı ·
**390** 390px'te overflow-x=0 + hit ≥44pt + safe-area · **KOPYA** kaygı-duyarlı kopya birebir ·
**A11Y** klavye + aria-label + axe temiz · **TEMA** ekran-türü teması doğru (çalışma=açık · duygusal=koyu)

İşaretleme: `☐` → `☑`. Her PR bu dosyayı günceller; grup bitince gruba tarih yaz.

## 1 · Auth & ilk temas (4)
| Ekran | Kaynak DC | PX | DUR | 390 | KOPYA | A11Y | TEMA |
|---|---|---|---|---|---|---|---|
| Giriş & Kayıt | KIRO2 Giris.dc.html | ☑ | ☑ | ☑ | ☑ | ☑ | ☑ |
| Hesap Kurtarma (3 adım) | KIRO2 Hesap Kurtarma.dc.html | ☑ | ☑ | ☑ | ☑ | ☑ | ☑ |
| Onboarding (misafir yerleştirme) | KIRO2 Onboarding.dc.html | ☑ | ☑ | ☑ | ☑ | ☑ | ☑ |
| İlk Hafta | KIRO Ilk Hafta.dc.html | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |

+ route guard + rol yönlendirmesi (öğrenci/veli/öğretmen): ☐

## 2 · SideNav + Öğrenci Paneli (1)
| Ekran | Kaynak DC | PX | DUR | 390 | KOPYA | A11Y | TEMA |
|---|---|---|---|---|---|---|---|
| Öğrenci Paneli (Rahat/Kompakt) | KIRO2 Ogrenci Paneli.dc.html | ☑ | ☑ | ☑ | ☑ | ☑ | ☑ |

## 3 · Çekirdek döngü (6) — ✅ TAMAM (2026-07-22, SPRINT3+3B+4)
| Ekran | Kaynak DC | PX | DUR | 390 | KOPYA | A11Y | TEMA |
|---|---|---|---|---|---|---|---|
| Soru Çözme | KIRO2 Soru Cozme.dc.html | ☑ | ☑ | ☑ | ☑ | ☑ | ☑ |
| Neden Geri Bildirim | KIRO2 Neden Geri Bildirim.dc.html | ☑ | ☑ | ☑ | ☑ | ☑ | ☑ |
| FSRS Tekrar | KIRO2 FSRS Tekrar.dc.html | ☑ | ☑ | ☑ | ☑ | ☑ | ☑ |
| Adaptif Test | KIRO2 Adaptif Test.dc.html | ☑ | ☑ | ☑ | ☑ | ☑ | ☑ |
| Harmanlanmış Deneme | KIRO2 Harmanlanmis Deneme.dc.html | ☑ | ☑ | ☑ | ☑ | ☑ | ☑ |
| Sınav Sonuç (net-birincil) | KIRO2 Sinav Sonuc.dc.html | ☑ | ☑ | ☑ | ☑ | ☑ | ☑ |

## 4 · Planlama (4) — ✅ TAMAM (2026-07-22, SPRINT5)
| Ekran | Kaynak DC | PX | DUR | 390 | KOPYA | A11Y | TEMA |
|---|---|---|---|---|---|---|---|
| Haftalık Plan | KIRO2 Haftalik Plan.dc.html | ☑ | ☑ | ☑ | ☑ | ☑ | ☑ |
| Öğrenme Yolu | KIRO2 Ogrenme Yolu.dc.html | ☑ | ☑ | ☑ | ☑ | ☑ | ☑ |
| Bilgi Atomları | KIRO Bilgi Atomlari.dc.html | ☑ | ☑ | ☑ | ☑ | ☑ | ☑ |
| Çalışma Modları | KIRO Calisma Modlari.dc.html | ☑ | ☑ | ☑ | ☑ | ☑ | ☑ |

## 5 · Hub / duygusal — KOYU (6) — ilk yarı ✅ TAMAM (2026-07-22, SPRINT6 · İLK DUSK)
| Ekran | Kaynak DC | PX | DUR | 390 | KOPYA | A11Y | TEMA |
|---|---|---|---|---|---|---|---|
| Bugün (hub) | KIRO Safak.dc.html | ☑ | ☑ | ☑ | ☑ | ☑ | ☑ |
| Kutlama | KIRO2 Kutlama.dc.html | ☑ | ☑ | ☑ | ☑ | ☑ | ☑ |
| Mola | KIRO2 Mola.dc.html | ☑ | ☑ | ☑ | ☑ | ☑ | ☑ |
| Geri Sayım (kaygı-nötr varsayılan) | KIRO2 Sinav Geri Sayim.dc.html | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| Başarımlar | KIRO2 Basarimlar.dc.html | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| Boss Savaşı | KIRO2 Boss Savasi.dc.html | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |

## 6 · Oyunlaştırma (4) — ✅ TAMAM (2026-07-22, SPRINT8)
| Ekran | Kaynak DC | PX | DUR | 390 | KOPYA | A11Y | TEMA |
|---|---|---|---|---|---|---|---|
| Lig (siralamaGizli + gizle düğmesi) | KIRO2 Lig.dc.html | ☑ | ☑ | ☑ | ☑ | ☑ | ☑ |
| 1v1 Düello | KIRO2 Duello.dc.html | ☑ | ☑ | ☑ | ☑ | ☑ | ☑ |
| Arkadaş Serisi | KIRO2 Arkadas Serisi.dc.html | ☑ | ☑ | ☑ | ☑ | ☑ | ☑ |
| Seri Dondurma | KIRO2 Seri Dondurma.dc.html | ☑ | ☑ | ☑ | ☑ | ☑ | ☑ |

## 7 · Roller (6) — ✅ TAMAM (SPRINT9-A + SPRINT9-B, 2026-07-23)
| Ekran | Kaynak DC | PX | DUR | 390 | KOPYA | A11Y | TEMA |
|---|---|---|---|---|---|---|---|
| Veli Paneli (SİZ-dili) | KIRO2 Veli Paneli.dc.html | ☑ | ☑ | ☑ | ☑ | ☑ | ☑ |
| Öğretmen Paneli | KIRO2 Ogretmen Paneli.dc.html | ☑ | ☑ | ☑ | ☑ | ☑ | ☑ |
| Öğrenci Özeti (öğretmen, salt-okur) | KIRO2 Ogretmen Ogrenci Ozet.dc.html | ☑ | ☑ | ☑ | ☑ | ☑ | ☑ |
| Veli Bağlama (KVKK, iki taraf) | KIRO2 Veli Baglama.dc.html | ☑ | ☑ | ☑ | ☑ | ☑ | ☑ |
| Ödev Atama | KIRO2 Odev Atama.dc.html | ☑ | ☑ | ☑ | ☑ | ☑ | ☑ |
| Sınıf Kurulumu ("İlk sınıfını kur") | KIRO2 Sinif Kurulum.dc.html | ☑ | ☑ | ☑ | ☑ | ☑ | ☑ |
| Ödevlerim | KIRO2 Odevlerim.dc.html | ☑ | ☑ | ☑ | ☑ | ☑ | ☑ |

Ödev Atama ↔ Ödevlerim tek döngü olarak test edildi: ☐

## 8 · İş & dayanıklılık (7) — kısmi 6/7 (SPRINT10-A+B, 2026-07-23)
| Ekran | Kaynak DC | PX | DUR | 390 | KOPYA | A11Y | TEMA |
|---|---|---|---|---|---|---|---|
| Abonelik (?rol=veli) | KIRO2 Abonelik.dc.html | ☑ | ☑ | ☑ | ☑ | ☑ | ☑ |
| Ödeme (+3DS bekleme durumu) | KIRO2 Odeme.dc.html | ☑ | ☑ | ☑ | ☑ | ☑ | ☑ |
| Plan Yönetimi (premium) | KIRO2 Plan Yonetimi.dc.html | ☑ | ☑ | ☑ | ☑ | ☑ | ☑ |
| Ayarlar | KIRO2 Ayarlar.dc.html | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| Bildirim Merkezi | KIRO2 Bildirim Merkezi.dc.html | ☑ | ☑ | ☑ | ☑ | ☑ | ☑ |
| Alan Kütüphanesi (ünite drill) | KIRO2 Alan Kutuphanesi.dc.html | ☑ | ☑ | ☑ | ☑ | ☑ | ☑ |
| Çevrimdışı | KIRO2 Cevrimdisi.dc.html | ☑ | ☑ | ☑ | ☑ | ☑ | ☑ |

## 9 · AI & çözüm (4)
| Ekran | Kaynak DC | PX | DUR | 390 | KOPYA | A11Y | TEMA |
|---|---|---|---|---|---|---|---|
| AI Sohbet | KIRO2 AI Sohbet.dc.html | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| Sokratik AI (mock → Faz 4 proxy) | KIRO2 Sokratik AI.dc.html | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| İnteraktif Çözüm | KIRO2 Interaktif Cozum.dc.html | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| Çözüm Paylaş — **MVP DIŞI** (karar 2026-07-04; pilot kararı gelirse açılır) | KIRO Cozum Paylas.dc.html | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |

---
**Kapsam dışı (2):** Kaygı Ölçüm · Moderatör Kılavuzu — araştırma saha paketi, üretime port edilmez.

**Kalibrasyon (S1+S2 ölçüldü):** infra bir-seferlik kuruldu (template + MSW + `kiro:breakpoints` denetçisi).
Ekran-başı marjinal iş (birim = form-ağırlıklı Giriş referansı):
- Form/wizard (Giriş ~1.0, Hesap Kurtarma ~1.2) · Layout+veri (Ödevlerim ~1.3) · 3-durum+mock (Onboarding ~1.5)
- **Composite dashboard (Öğrenci Paneli ~2.3)** = ~2.0 taban + ~0.3 breakpoint-remediation (yoğun-grid ilk turda geçmez).
- **Revize tahmin:** kalan 39 ekran ≈ **46–55 birim** (composite-yoğun S3–S5 üst-sınır; basit paneller ~0.7).
  Paylaşılan composite'ler (QuestionCard seti, TopBar) bir kez yapılınca çekirdek-döngü ekranları ucuzlar.
