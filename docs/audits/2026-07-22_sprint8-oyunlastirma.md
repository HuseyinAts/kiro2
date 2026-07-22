# KIRO2 — Faz 3 · SPRINT8 Oyunlaştırma (Grup 6) — RAPOR

**Tarih:** 2026-07-22
**Branch:** feature/self-evolution-optimization (push YOK — commit'ler local birikir)
**Kapsam:** Grup 6 Oyunlaştırma 4 ekran (Lig · 1v1 Düello · Arkadaş Serisi · Seri Dondurma) → `frontend/src/kiro/`
**Sonuç:** 4/4 ekran ✅ — **Grup 6 TAMAM**. İlerleme **25/42 ekran + 1 composite (QuestionCard)**.

---

## Ekranlar

| Ekran | Tema | Rota | Satır | Kaynak DC |
|---|---|---|---|---|
| Lig | **paper** | `/lig` | 766 | KIRO2 Lig.dc.html |
| 1v1 Düello | **dusk** (arena) | `/duello` | 778 | KIRO2 Duello.dc.html |
| Arkadaş Serisi | **paper** | `/arkadas-serisi` | 404 | KIRO2 Arkadas Serisi.dc.html |
| Seri Dondurma | **paper** | `/seri` | 494 | KIRO2 Seri Dondurma.dc.html |

**Tema DC-kanıtından türetildi** (naif "oyunlaştırma=dusk" tahmini DEĞİL): Lig body `#F7F4EF` (sağ ray koyu kart = izole yüzey, dusk teması değil); Düello arena `radial(#16203B→#0A0E1B)` = Boss gibi oyun-sahnesi (`// kanon-allow: boss-arena, kutlama`); Arkadaş/Seri paper (coral hero = CTA-kartı, seri = çalışma-aracı).

---

## Backend gerçeği (session notlarının düzeltilmesi)

Session notları "sadece `league_api.py` var, düello/streak yeni/mock" varsayıyordu. Keşif (8 ajan) çok daha fazlasını buldu:

- **Lig** → `/api/v1/leagues/{current,history,award-xp}` TAM çalışır (snake_case, `is_self`). Yeni /league YAZILMADI. ✅
- **Düello** → İKİ sistem MEVCUT: gerçek-zamanlı `/api/v1/duel/*` (SSE + ELO + matchmaking: matchmake/current-question/answer/stream/result/rating) **ve** `/api/v1/cozum-duellosu/*` (async + oylama).
- **Arkadaş** → `/api/v1/birlikte-streak/*` var ama **otomatik-eşleşmeli** (arkadaş seçme/davet YOK). İsimli-arkadaş + davet = **friend sistemi backend'de YOK**.
- **Seri Dondurma** → freeze/dondurma mekaniği **hiçbir yerde YOK**. "Sakin mod / sıralamayı gizle" tercihi de YOK.

---

## Kararlar (kullanıcı onayı, 2026-07-22)

1. **1v1 Düello → gerçek `/api/v1/duel/*` SSE+ELO'ya bağlanır** (Faz 3 mock kuralından bilinçli sapma). Ekran `postDuelMatchmake/getDuelCurrentQuestion/postDuelAnswer/getDuelResult/getDuelRating/duelStream` tüketir. **Çift-kollu:** live → gerçek REST + `EventSource` (cookie-auth); mock → deterministik server-sim (jsdom/Storybook için — jsdom'da EventSource yok). Sunucu-otorite mock'ta bile izole (puan/turSonucu/skor sim/sunucuda hesaplanır, ekran yalnız yanıtı render eder).
2. **Seri Dondurma "%48 daha uzun seri" istatistiği ÇIKARILDI** (kaynak doğrulanmamış; 17-19 yaş + KVKK/hukuk riski). Kartın affedicilik gövdesi kaldı.
3. **4 ekran da bu sprint** (tek commit + tek adversarial review; S5-S7 gibi).

---

## Süreç (pipeline)

Keşif workflow (6 ajan) → build workflow (Infra 1 + 4 ekran paralel + Gate 1) → **adversarial review workflow (19 ajan: 4×4-boyut inceleme + bulgu-bazlı skeptik doğrulama)** → fix workflow (4 ekran + gate).

**Altyapı (mock-katmanı, üretime sızmaz — additive):** `api-client.ts` +410 (getLeague/getDuel*/getFriends/getStreak/duelStream/buildMockStreak), `types.ts` +147 (13 tip + DuelTurSonucu), `kiro-data.json` +60 (league/duelOpponent/friends/streak; MockData Pick güncellendi), `mswHandlers.ts` +84 (REST handler; SSE E2E'de gerçek backend). Düello soruları questionBank'ten STRIP'li (doğru şık sızmaz).

---

## Adversarial review — 4 boyut (server-otorite · a11y · kanon-kopya · breakpoint-motion)

19 ajan (4 inceleme + 15 doğrulama). **P0: 0 · major: 2 · minor: 10** doğrulandı; **0 phantom hayatta kaldı** (S197 phantom-eleme dersine uygun her bulgu bağımsız skeptik doğrulamadan geçti).

### 2 major (ikisi de Düello) — DÜZELTİLDİ
- **[server-otorite] `turSonucu` mantık hatası** (`DuelloPage:352`): tur-sonuç bandı stream'den gelen `turSonucu`'ya güveniyordu; mock `duelStream` tur `i` için `(i+1)*900ms` sabit zamanda hesaplıyordu ama `userRounds[i]` yalnız `postDuelAnswer`'da (kullanıcı kilitleyince) set edilir → timer atarken daima `undefined` → band ASLA "Turu kazandın!" ('me') gösteremiyor, noktalar asla yeşil, final overlay "Kazandın!" derken çelişiyordu. **Fix:** `turSonucu` `DuelAnswerResult`'a taşındı (sunucu-hesaplı); `postDuelAnswer` o turun userRound + rakip script'inden hesaplar; `duelStream.onAnswer` yalnız rakip durum-pili (doğru/süre) taşır. Regresyon testi eklendi ('me' yolu doğrulandı).
- **[a11y/kanon] CTA kontrastı** (`DuelloPage:630` + `:744`): parlak coral `#FF6F5C` + beyaz metin ~2.73:1 (AA FAIL). **Fix:** metin → `ARENA.darkInk #0A0E1B` (~6.6:1, dusk-CTA kanonu: parlak coral + koyu mürekkep).

### 10 minor — 9 DÜZELTİLDİ, 1 ERTELENDİ
- Lig: podyum SR-sıra metni (DOM 2-1-3, aria-hidden rozet) → srOnly `{rank}. sıra`; koyu-kart risk rengi `#C77A1E` (~4.46:1) → `#FFB347` (~8:1); tier + `'ndesin` Türkçe gramer bozulması → locative-ek kaldırıldı (`{tier} — kendi ritminde ilerle, sıralama ikincil.`).
- Düello: ölü `finalRef` → `getDuelResult` hata yolunda SSE `onFinished` sonucu fallback olarak bağlandı.
- Arkadaş: tebrik butonu statik aria-label → `{ad} için tebrik gönder`; seri sayısı SR birimi (`gün seri`); dürt/CTA hit-target 34/40px → 44px (şeffaf pad, görsel korundu).
- Seri: `Bugün · bugün` tekrarlı aria-label → düzeltildi; iskelet grid responsive değildi (`300px minmax(0,1fr)` sabit) → `dar ? '1fr' : ...`.
- **ERTELENDİ (#6, `DuelloPage:470`):** VS bandında SEN/orta skor aynı değeri gösteriyor. Sözleşmede tek skor metriği var; DC'nin puan-vs-galibiyet ayrımı Faz 4 backend'e bağlı. Mevcut tutarlı, kırık değil.

---

## Kapı sonuçları (fix sonrası, canlı doğrulandı)

- **kanon-lint: 0 ihlal** (11 uyarı — hepsi pre-existing: kutlama kanon-allow + token `#6B6478`)
- **type-check (tsc --noEmit): 0 hata**
- **vitest src/kiro: 47 dosya / 265 test PASS** (0 fail, 0 skip)
- breakpoint (build-storybook) ve canlı `/duel` SSE E2E: **operatöre bırakıldı** (backend ayakta gerektirir)

---

## ONAY BEKLER (kaygı-duyarlı inferred kopya — DC'de olmayan)

S1-S7 normuyla yazıldı + işaretlendi (ön-blok değil):
- **Lig:** ilk-hafta empty ("Ligin Pazartesi başlıyor — bu hafta odak sende."); error (sakin); zon-status server-güvenli reword ("İlk {n}'desin — üst lige doğru").
- **Düello:** skeleton ("Rakip eşleştiriliyor…"); ErrorState (sakin, "senlik bir şey değil").
- **Arkadaş:** empty (davet); error; **"Arkadaş ekle" davet akışı DC'de YOK** — buton var, akış mock/flag.
- **Seri:** empty (seri=0 "İlk tuğlanı bugün koy…"); error; dondurmaHak=0 durumu.

---

## Faz 4 / operatör backlog

1. **Operatör E2E (sende):** dev stack ayağa (`docker compose up -d` / native) → Düello canlı `/duel/*` SSE + ELO doğrulaması; breakpoint kapısı (`npm run kiro:breakpoints`, ~28 yeni story × 7 = +196 snapshot).
2. **Backend wiring (Faz 4):** Lig `standings` per-oyuncu seviye/trend/zon-eşiği/senVsDun DTO'da YOK (mock zengin, live iskeletsel); "sakin mod / sıralamayı gizle" preference ucu YOK; **freeze mekaniği YOK**; **friend sistemi YOK** (birlikte-streak otomatik-eşleşmeli). Hepsi Faz 3'te mock-katmanı.
3. **KVKK (Arkadaş):** arkadaş günlük-durum + tam XP görünürlüğü → karşılıklı-onay + opt-in gerekir (17-19 yaş, hassas).
4. **#6** VS skor puan/galibiyet ayrımı (contract).
5. **Rota wiring:** ekranlar App router'a bağlanmadı (S1-S7 gibi ayrı backlog; route guard ile birlikte).

---

## Kararlar (gelecek session tekrar tartışmasın)

- **Düello = gerçek `/duel/*` SSE (live) + deterministik mock-sim (test).** Sunucu-otorite mock'ta bile izole.
- **Tema DC-kanıtından:** Lig/Arkadaş/Seri paper, Düello dusk-arena. "Oyunlaştırma=dusk" naif tahmini DC ile çürütüldü.
- **Rota `/arkadas-serisi`** (SideNav preset ile hizalı; SPRINT8_SPEC `/arkadaslar` sapması reddedildi).
- **%48 istatistiği kalıcı çıkarıldı** (doğrulanmamış iddia).
