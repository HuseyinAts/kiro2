# Faz 3 · SPRINT7 — Duygusal çekirdek II / Grup 5 BİTER (2026-07-22)

Kapsam: **3 ekran** — Sınav Geri Sayım · Başarımlar · Boss Savaşı. Hepsi **dusk**. **Grup 5 (Hub/duygusal) TAMAM.**
Süreç: keşif workflow (6 ajan) → paylaşılan-infra → build workflow (3 ajan) → gate → adversarial review (4 boyut) → fix → gate.

## DoD sonuçları

| Ekran | rota | tema | axe | breakpoint | kanon | tsc | vitest |
|---|---|---|---|---|---|---|---|
| Sınav Geri Sayım | `/geri-sayim` | dusk | ✅ | ✅ 14/14 (2 varyant story) | ✅ 0 | ✅ 0 | ✅ |
| Başarımlar | `/basarimlar` | dusk | ✅ | ✅ 7/7 | ✅ 0 | ✅ 0 | ✅ |
| Boss Savaşı | `/boss` | dusk (kırmızı arena) | ✅ | ✅ 7/7 | ✅ 0 | ✅ 0 | ✅ |

- **Kapı:** kanon-lint **0 ihlal** (9 uyarı pre-existing) · scoped strict **tsc 0** · vitest **tam kiro 43 dosya / 240 test PASS** · **breakpoint 175/175** (25 story × 7) · axe temiz.

## Paylaşılan infra
- **`lib/gunSayaci.ts` (YENİ):** `gunKalan(yksTarihi, bugun?)` = sınava kalan gün (ceil((yks−bugün)/86400000)) + `haftaKalan` (Math.max(1,…) DC alt-sınır). SPRINT6 açık-nokta-3 çözümü. **YALNIZ Geri Sayım** tüketir (bkz. flag).
- **api-client `postBossSession` + `postBossAnswer` (YENİ):** mock server-sim (`postCatNext` deseni). **Sunucu-otorite:** `correct`/`hasar`/`hp`/`kombo`/`can` = postBossAnswer yanıtından; istemci HESAPLAMAZ. Boss soruları `getQuestionSet` STRIP'li (dogru sızmaz). Boss "9"/maxHP 2000/lives 5/+800 XP = mock sabit → sunucu (açık-nokta 5).
- **Boss KIRMIZI istisnası:** `// kanon-allow: boss-arena, kutlama` — kırmızı aile (#FB7185/#BE123C/#991B1B/#7F1D1D/#641225) inline (token değil). Kullanıcı-hatası TERRACOTTA #E8836B, doğru şık YEŞİL #1FB683. (ONAYLI 2026-07-04.)

## Ekran notları
- **Geri Sayım** (2 varyant): default **Kaygı-nötr (B)** ("Bugüne bak. Gün saymaya gerek yok.", SR'de de sayısız — dürüstlük); `varyant` prop korundu (A story'de). Batım gökyüzü + gunSayaci. Ayarlar toggle + `/me.geriSayimTercihi` → **S8**.
- **Başarımlar**: mor radyal; hero band (seviye/XP/seri-rekor) + hâkimiyet halkaları (96px SVG dasharray 201.06, tierFromPct eşik 40/65/85, dusk tier renkleri, role=img) + seri kilometre taşları (7/14/21/30/50/100) + kademe lejantı. `kazanilan = ders sayısı + açılan taş` (DC birebir 8). kilitliGoster SABİT true.
- **Boss Savaşı** (ağır + kırmızı): kırmızı arena + ejderha SVG + savaş döngüsü (postBossAnswer, HP scaleX) + zafer/yenilgi overlay (ConfettiDawn zaferde) + growth-mindset yenilgi kopyası birebir. HP role=progressbar, TEK aria-live, overlay role=dialog + focus-trap, klavye.

## Adversarial review — 4 bulgu (3 dedup) → 2 fix · 1 ertele
Boss (ağır/P0) sunucu-otorite + kopya + kırmızı-scope + hareket-guard boyutlarında TEMİZ.

| # | ekran | sev | bulgu | karar |
|---|---|---|---|---|
| 1 | GeriSayim | minor | `haftaKalan` DC `Math.max(1,…)` alt-sınırını düşürmüş (sınav günü "0 hafta" vs DC "1") | **FIX** → Math.max(1,…) |
| 2 | Boss | minor | bitiş overlay `aria-modal` ama focus-trap yok (arka plan tabbable) | **FIX** → Tab odak-tuzağı (dialog içinde döner) |
| 3 | Basarimlar | minor | `siralama` prop düşürülmüş (spec §B "kalır") | **ERTELE** — prototip editör-prop'u (görünür kontrol değil); default hâkimiyet-azalan DC-sadık; sort toggle geniş Ayarlar geçişinde (KISS) |

## Build-turu düzeltmeleri (gate)
- Boss HP barı `transition:width` (DC-kopya) → **`transform: scaleX`** (kanon: layout-anim yasak; drain görseli korundu, sol-çapa).
- Başarımlar `kazanilan` = usta+fethedildi (6, hatalı yorum) → **ders sayısı + taş (8, DC birebir)**.

## Resolved kopya/piksel çelişkileri + flag'ler
- **gunSayaci çelişkisi (b-hibrit):** SPEC §A "Bugün hub'ı da aynı util'i kullanır" der ama Bugün'ün "tuğla"sı ÇABA metaforudur ("Bugünün tuğlasını koy" gün-sayacıyla anlamsızlaşır); Geri Sayım "gün/gündoğumu" der, "tuğla" demez. **gunSayaci yalnız Geri Sayım'da; Bugün çaba-tuğlası korundu (migrate EDİLMEDİ).** SPEC §A satır 43 iddiası düzeltilmeli.
- **Boss dusk CTA** = parlak coral/altın + koyu mürekkep (#2A1018/#241329) — AA-güvenli (paper'ın tersi).

## Açık noktalar (Faz 4)
1. Geri Sayım A/B: PostHog deneyi + `/me.geriSayimTercihi` + Ayarlar toggle (S8).
2. ~~Boss kırmızı~~ — ONAYLI (kanon-allow: boss-arena).
3. Boss uçları openapi (`/boss/session` + `/boss/answer`).
4. Başarımlar `kazanilan` sunucudan (`/achievements` özeti) + `siralama` toggle (ertelendi).
5. Boss "9"/maxHP/lives/ödül sunucudan. **+800 XP (Boss arena) vs +120 XP (Kutlama boss) çakışması** → sunucu tek-kaynağa indirmeli.

## Kalibrasyon
| Ekran | tip | birim | not |
|---|---|---|---|
| Geri Sayım | 2-varyant (gunSayaci reuse, dusk kabuk reuse) | ~1.6 | S6 dusk altyapısı reuse |
| Başarımlar | özgün (mastery halka SVG + kilometre taşları) | ~1.9 | dasharray/tierFromPct reuse |
| Boss Savaşı | özgün AĞIR (arena + combat + overlay + server-sim) | ~3.0 | sprintin ağır işi; postBossAnswer + kırmızı + ConfettiDawn |

**İlerleme: 21/42 ekran + 1 composite (QuestionCard). Grup 5 (Hub/duygusal) TAMAM (6/6).**
Sonraki: **Grup 6 Oyunlaştırma (S8)** — Lig · 1v1 Düello · Arkadaş Serisi · Seri Dondurma (lig ucu: önce backend keşfi).
