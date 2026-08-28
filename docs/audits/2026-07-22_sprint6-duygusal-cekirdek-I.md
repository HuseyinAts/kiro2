# Faz 3 · SPRINT6 — Duygusal çekirdek I / İLK DUSK (2026-07-22)

Kapsam: **3 ekran** — Bugün/Şafak hub · Kutlama · Mola. **İLK KOYU (dusk) EKRANLAR** — Grup 5'in ilk yarısı.
Süreç: **keşif workflow (6 ajan) → paylaşılan-infra → build workflow (3 ajan) → gate → adversarial review (4 boyut) → fix → gate**.
Tema: üçü de **dusk** (koyu şafak) — çalışma ekranları paper, duygusal/hub/ritüel ekranlar dusk (kanon).

## DoD sonuçları

| Ekran | rota | tema | axe | breakpoint | kanon | tsc | vitest |
|---|---|---|---|---|---|---|---|
| Bugün / Şafak | `/bugun` | dusk | ✅ | ✅ 7/7 | ✅ 0 | ✅ 0 | ✅ |
| Kutlama | `/kutlama?type=` | dusk | ✅ | ✅ 14/14 (2 story) | ✅ 0 | ✅ 0 | ✅ |
| Mola | `/mola` | dusk | ✅ | ✅ 7/7 | ✅ 0 | ✅ 0 | ✅ |

- **Kapı:** kanon-lint **0 ihlal** (9 uyarı, hepsi pre-existing; 3 dusk ekran `// kanon-allow: kutlama` ile 0 uyarı üretti) · scoped strict **tsc 0** · vitest **tam kiro 40 dosya / 222 test PASS** · **breakpoint 147/147** (21 story × 7).

## Dusk tema kuruluşu (İLK) — paylaşılan infra
- **`.k-dusk` shell deseni** ilk kez gerçek ekrana bağlandı: `<KiroThemeProvider theme="dusk"><div className="k-dusk" style={{ background: color.dusk.bg, color: color.dusk.text }}>` + `surf('dusk')`.
- **`tokens.ts` dusk ikincil metin tonları eklendi** (§7 kanonu, reused S6+S7): `ink2 #B6A6C4` · `iconMuted #9B8FB5` · `faded #8C8398` · `body80 rgba(236,228,240,0.8)`. Dusk'ta `#6B6478` YASAK.
- **`color.gradient.dawnSkyLinear` durak-yüzdeleri düzeltildi** (adversarial bulgu): duraksız string CSS'te eşit dağılıyordu → DC kanon durakları (0/17/33/51/66/80/92/100) eklendi (tokens.ts + tokens.css). Spec §12 "birebir, yaklaşıklaştırma yok".
- **`// kanon-allow: kutlama`** ilk-satır: dusk duygusal ekranlarda 600ms+ ambient/tören hareketi MEŞRU (MOTION_KANON §5); LONG_DURATION uyarısını bastırır → yeni 3 dosya 0 uyarı.
- **DUSK coral/AA (paper'ın tersi):** dusk CTA = parlak coral/gradyan DOLGU + **KOYU MÜREKKEP** metin (#2A1018/#241329) — AA-güvenli; koyu zeminde sıkı-AA uygulanmaz (TALIMAT §2). ConfettiDawn reuse (kendi reduced-motion guard'ı).

## Ekran notları
- **Bugün** (İLK dusk, ağır): kanon gökyüzü gradyanı (8 durak) + 6 yıldız twinkle + güneş sunPulse + 2-katman silüet; görev kartı (getPlanWeek bugün ilk blok, kGlowB kenar-glow) + ders kartları (subject.dark palet) + FSRS + SEN-vs-DÜN + **mood radiogroup+aria-checked+aria-live** (localStorage gün-anahtarlı, 5 mesaj birebir) + mantra. Dinamik-gökyüzü faz mantığı SADELEŞTİRİLDİ (KISS — güneş %67 sabit, 6 statik yıldız).
- **Kutlama**: tören sahnesi, 4 tür (gunluk/seviye/seri/boss) URL-param'dan; ConfettiDawn reuse (gerçek başarıda); boss mor (kanon-allow); role=status + başlığa programatik focus; CTA'lar → Bugün.
- **Mola**: en koyu zemin #0F0B16; nefes orbu 16s 4-faz (breatheOrb/breatheRing/c1-c4); reduced-motion → orb sabit + statik cue liste; 4 dinlenme-önerisi (tıklanmaz); yalnız getMe; hata kutusu ASLA.

## Adversarial review — 18 bulgu (çoğu dedup) → tümü FIX
Mola **0 bulgu** (DC'sini okudu, temiz). Bugün **1** (paylaşılan gradyan token). Kutlama **7** — kurucu ajan DC dosyasını bulamadı (cwd/path), sözleşmeden yazdı → piksel-drift kümesi:

| # | ekran | sev | bulgu | fix |
|---|---|---|---|---|
| 1 | Bugün+ | major | `dawnSkyLinear` durak-yüzdeleri yok (eşit dağılım) | DC durakları (0/17/…/100) tokens.ts+css |
| 2 | Kutlama | major | Eyebrow textTransform yok → title-case | Türkçe-doğru ön-uppercase ("SEVİYE ATLADIN" vb.) |
| 3 | Kutlama | major | Ödül chip'i SÜTUN (DC YATAY) + punto/radius drift | row, gap 10, 22px, radius 14, etiket 12.5px/0.7α |
| 4 | Kutlama | major | Dekoratif yıldızlar altın-SVG-glif (DC küçük beyaz nokta) | 4 küçük daire nokta (#fff/#FFE8C9, üst bölge); kctwinkle opacity-only |
| 5 | Kutlama | major | Seviye no her zaman persona'dan (DC urlXp'den türetir) | `seviyeBilgiFrom(seviyeEsik, urlXp)` |
| 6 | Kutlama | minor | Rozet halo/glow drift (inset/opacity/scale/boxShadow) | DC değerleri (inset -30, cglow 0.85→1/1.07) |
| 7 | Kutlama | minor | CTA glow yok + padding/margin drift | boxShadow + padding 30 + marginTop 30 |
| 8 | Kutlama | minor | Mantra 20px + tırnaksız | 18px + kıvrık tırnak “…” |

> **Ders:** build ajanına DC'yi mutlak yol + Glob ile buldur; cwd belirsizliğinde ajan "sözleşmeden yaz" moduna düşüyor → tek ekranda piksel-drift kümesi. Adversarial review (DC'yi Glob'la bulan) tümünü yakaladı.

## Test flake (çözüldü)
Tam suite 2 axe-**timeout** (ihlal DEĞİL) — SPRINT5 ağır paper ekranlar (OgrenmeYolu patika + HaftalikPlan 7-sütun). 40 dosya paralel yük + jsdom+axe CPU-ağır → 20s yetmedi. **Fix:** bu 2 ekranın axe testi timeout'u 20s→40s (izolasyonda geçiyorlardı; ihlal yok). SPRINT4 flake dersinin tekrarı.

## Resolved kopya/piksel çelişkileri (SPEC satır 5 "DC=piksel otoritesi")
- Bugün "{n} tuğla" = plan-blok kalanı (DC formülü kalanT), sınava-kalan-gün DEĞİL (spec §A metni ≠ DC; DC kazanır; Sprint7 açık-nokta 3).
- Eyebrow "BUGÜNKİ İLK TUĞLA" (DC; spec "BUGÜNKÜ"). Görev kartı animasyonu kGlowB (DC; spec "floatUp" prototipte yok).
- SEN-vs-DÜN = DC-statik "+15 dk" — "dün" verisi backend'de yok, uydurma YAPILMADI (Faz4 açık-nokta).

## Açık noktalar (Faz 4)
- `POST /me/mood` ucu yok → mood YEREL localStorage (§açık-nokta 1).
- SEN-vs-DÜN "dün dk" alanı yok → statik (uydurma trend gösterilmedi).
- "Şafağa {n} tuğla" birim tanımı (tuğla vs sınava-gün) Sprint7'de netleşecek (açık-nokta 3).
- Bugün dinamik-gökyüzü faz/skyTint/horizonGlow/sunShift (DC'nin saat+sınava-gün mantığı) portlanmadı (KISS; spec hero tanımında yok).

## Kalibrasyon
| Ekran | tip | birim | not |
|---|---|---|---|
| **Dusk tema kuruluşu (İLK)** | infra (shell + tokens dusk tonları + gradyan durak + kanon-allow) | ~0.8 | bir-seferlik; sonraki dusk ekranlar (S7) bunu reuse eder |
| Bugün / Şafak | özgün (gökyüzü hero + 8 blok + mood a11y) | ~2.8 | sprintin ağır işi; ambient SVG + mood localStorage bespoke |
| Kutlama | tören (ConfettiDawn reuse + 4 tür) | ~1.7 | ConfettiDawn reuse; 4-tür + pixel-fix turu |
| Mola | ritüel (nefes orbu 16s + reduce cue) | ~1.4 | orb keyframe + reduced-motion cue bespoke |

**İlerleme: 18/42 ekran + 1 composite (QuestionCard). Grup 5 (Hub/duygusal) ilk yarısı TAMAM — İLK DUSK kuruldu.**
Sonraki: Grup 5 ikinci yarısı (S7) — Geri Sayım · Başarımlar · Boss Savaşı (kırmızı istisnası boss-arena).
