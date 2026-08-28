# KIRO2 — Sprint 7 Port Spec'i: Duygusal çekirdek II (Grup 5 biter)

Kapsam: **3 ekran** (Sınav Geri Sayım · Başarımlar · Boss Savaşı) — hepsi DUSK.
Piksel referansı her zaman kaynak DC'dir.

Önkoşul: Sprint 6 DoD tamam (dusk teması kurulu; ConfettiDawn gerçek ekranda çalışıyor).

---

## A · Ekran: Sınav Geri Sayım (`KIRO2 Sinav Geri Sayim.dc.html`)

**Tema:** DUSK — ama Bugün'den FARKLI gökyüzü: ufuk-batımı radyali
(135% 108% at 50% 122%: #FFB07A→#FF7E6B 10%→#C2506F 30%→#5B2F66 58%→#1A0F26) + güneş glow'u
(sunGlow 6s) + 5 yıldız (tw). **Rota:** `/geri-sayim`. Bugün hub'ındaki "Sınava sayım" pilinden gelinir.

### ⚠ İKİ VARYANT — ürün kararı gerektirir (bu ekranın kalbi)
Prototipte `varyant` prop'u: **"Geri sayım"** (geleneksel: dev gün sayısı) vs **"Kaygı-nötr"**
(VARSAYILAN: sayı yok, "Bugüne bak. Gün saymaya gerek yok.").
- Üretim önerisi: **kullanıcı tercihi değil, A/B deneyi** (ADR-005 PostHog; opt-in analitik).
  Kaygı-duyarlı kanona göre varsayılan **kaygı-nötr**; geri sayım isteyen Ayarlar'dan açar
  (tercih `/me` profiline yazılır — openapi'ye alan: `geriSayimTercihi`).
- Karar gelene dek: kaygı-nötr varsayılan, Ayarlar toggle'ı Sprint 8'de bağlanır.

### Varyant A · Geri sayım — BİREBİR
- Eyebrow "YKS · {tarih}" · dev sayı (clamp 100-176px, tabular, text-shadow) ·
  serif italik "{birim} kaldı" (birim: "gündoğumu" | "gün" — şiirsel varsayılan gündoğumu).
- Gövde: "Sınav senin şafağın. Her {birim} bir tuğla — acelesi yok, sen vs dün."
- 3 cam chip: hafta · günlük seri · dk/gün.

### Varyant B · Kaygı-nötr — BİREBİR
- Eyebrow "BUGÜN · {uzun tarih}" · serif başlık "Bugüne bak.<br>Gün saymaya gerek yok."
- Gövde: "Sınav uzak bir tehdit değil — ufuktaki sabit bir gün. Sen bugüne odaklan; yarıştığın tek kişi dünkü sen."
- "YKS ufku · {tarih}" pili (sayaç değil, sabit ufuk) · 3 chip: seri · en uzun seri · dk · günlük ritim.

### Ortak bloklar
- **Hedef kartı:** "{hedefBolum}" + "{hedefUni} · ilk {hedefSira}". Alt satır varyanta göre:
  A: "Son denemede {guncelSira}. sıradaydın — her tuğla seni yaklaştırıyor." ·
  B: "Acele yok — istikrar sıralamadan güçlü. Her gün bir adım yeter." (sıralama sayısı B'de HİÇ geçmez — bilinçli).
- Mantra (serif italik, 3 seçenek prototipte) + CTA "Bugünün tuğlasını koy" → Soru Çözme.

### Veri bağlama + tuğla senkronu
- `/me` persona: yksTarihi, seri, seriRekor, hedef üçlüsü, gunlukHedefDk.
- **Sprint 6 açık noktası #3 BURADA ÇÖZÜLÜR:** "Şafağa {n} tuğla" = `ceil((yksTarihi − bugün) / 86400000)`
  — tek kaynak `/me.yksTarihi`; Bugün hub'ı ve bu ekran aynı util'i kullanır (`src/kiro/lib/gunSayaci.ts`).
- Sayı biçimi: sıralamalar tr-TR binlik ("18.000").

### DoD notları
- sunGlow/tw → reduced-motion guard. Dev sayı `aria-live` DEĞİL (her gün değişir, oturumda değişmez).
- 390px: `.rpadc` 20px padding; chip'ler sarar; dev sayı clamp zaten akışkan.

---

## B · Ekran: Başarımlar (`KIRO2 Basarimlar.dc.html`)

**Tema:** DUSK (mor radyal: #3E2554→#271A3C 40%→#150E20). **Layout:** tek sütun max 900px,
geri oku → Panel. **Rota:** `/basarimlar`.

### Bloklar — BİREBİR
1. **Hero bandı** (amber cam): 66px seviye karesi (gradyan #FFB570→#FF6F91, taç rozeti) +
   "SEVİYE {n}" + "{xp} XP toplandı" (tr-TR binlik) · sağda seri/rekor ikilisi (dikey ayraçlı).
2. **Hâkimiyet Rozetleri** ("her ders bir kademede"): ders başına 96px SVG halkası
   (dasharray 201.06, ders renginde + glow drop-shadow) + %n merkez + kademe chip'i.
   **Kademe renkleri (dusk):** Tanıdık #9A93A5 · Yetkin #7FB0FF · Usta #FFAE86 · Fethedildi #FCD34D.
   Eşikler MasteryBadge ile AYNI (40/65/85) — ama bu ekran MasteryBadge BİLEŞENİNİ KULLANMAZ
   (o açık-tema; burada dusk halka çizimi). Eşik sabitleri ortak modülden (`masteryTier`).
3. **Seri Kilometre Taşları:** aktif seri barı ("rekora {n} gün") + 7/14/21/30/50/100 karoları —
   kazanılan: alev SVG + coral gradyan karo; kilitli: kilit SVG + kesikli kenar. "açıldı/kilitli" etiketi.
4. **Kademe lejantı:** 4 kademe + aralıkları (0–40 · 40–65 · 65–85 · 85–100).

### Props → üretim
- `siralama` (hakimiyet|ad) → kalır: küçük yerel sıralama kontrolü (görsel toggle; localStorage).
- `kilitliGoster` → kalır ama varsayılan true; Ayarlar'a bağlamaya gerek yok (yerinde toggle da olmaz —
  sadeleştir: ÜRETİMDE SABİT true, prop iptal. Kilitli taşları saklamak motivasyon hilesi olur — gösterilir).
- Başlıktaki "{kazanilan} rozet kazanıldı · yolun kanıtı" — kazanilan İSTEMCİDE toplanıyor (tier sayısı +
  açılan taş) → üretimde sunucudan (`/achievements` özet alanı; openapi'ye eklenecek — açık nokta).

### Veri bağlama
- `/me` (seviye, xp, seri, rekor) · `/subjects` (hâkimiyet) · kilometre taşları: seriRekor'dan türetilir.
- Üç durum: Skeleton (halka iskeletleri) · ErrorState (sakin amber, dusk üstünde) · yeni kullanıcı:
  halkalar %0 + "İlk rozetin ilk çalışmayla gelir" tonu (kopya onaya sunulur — prototipte yok).

### DoD notları
- Halkalara `role="img"` + `aria-label="{ders} yüzde {n}, {kademe}"`; karo durumu metinle var ("açıldı/kilitli").
- shimmer animasyonu kullanılmıyorsa taşınmaz; scrollbar stili `.scan` → global koyu scrollbar token'ı.
- 390px: `.rpadb` 20px; rozet grid'i sarar (126px sabit genişlik korunur).

---

## C · Ekran: Boss Savaşı (`KIRO2 Boss Savasi.dc.html`)

**Tema:** DUSK — en koyu kırmızı arena (radyal #3A0E1E→#160A18 45%→#120A14). **Layout:** SideNav YOK,
58px bar (X → Öğrenme Yolu · "ZORLU" rozeti · faz noktaları 1/3). **Rota:** `/boss/:konuId`.
Öğrenme Yolu'ndaki boss düğümünden gelinir.

### ⚠ KANON KARARI — ejderha kırmızıları (KABUL EDİLDİ)
Bu ekran bilinçli olarak kırmızı ailesi kullanır (#FB7185 #BE123C #991B1B #7F1D1D): ejderha =
kurgusal düşman kimliği, alarm-semantiği DEĞİL. Kutlama'daki mor istisnasına paralel.
**Karar:** kanon-lint'e dosya-kapsamlı istisna (`// kanon-allow: boss-arena`) — yalnız
`BossSavasi.tsx` içinde kırmızı ailesi serbest; kullanıcı-hatası geri bildirimi orada bile
terracotta kalır (seçili yanlış = #E8836B — prototipte zaten öyle). **ONAYLANDI (2026-07-04).**

### Arena — BİREBİR
- 142px ejderha SVG (döndürülmüş kare katmanlar + radyal çekirdek + kızgın kaş/ağız) + aura
  (kfAura 2.4s) + yüzme (kfBoss 3s) + isabet sarsıntısı (kfHit 0.35s — yalnız doğru cevapta).
- "{konu} Ejderhası" + "Konu Canavarı · {konu}" + zayıf nokta pili: "Zayıf noktası: **{atom}**".
- **BOSS CAN** barı: 2.000 → 0, gradyan #BE123C→#FB7185 + glow, 0.4s geçiş.
- Durum şeridi: CANLARIN (5 kalp, dolu #E8836B / boş kontur) · KOMBO ×{n} (altın) ·
  saldırı gücü {n} (coral şimşek).
- Sağ üstteki "9" karesi: prototipte SABİT — boss seviyesidir; üretimde `bossSeviye` verisinden (açık nokta).

### Savaş döngüsü — BİREBİR
- "SALDIRI SORUSU · {n}" + "Doğru cevap = ~{hasar} hasar" · 2×2 seçenek grid'i.
- Doğru: hasar = 280 + (kombo−1)×70; kombo +1; HP düşer; geri bildirim "{hasar} hasar verdin!
  Kombo ×{n} — vur vur!" (yeşil) + seçenekte "−{hasar}" şimşeği.
- Yanlış: 1 kalp gider, kombo 1'e döner; "Iskaladın — 1 can kaybettin. Kombo sıfırlandı."
- Buton: "Saldır!" (seçimsiz %50 soluk) → reveal'da "Sonraki saldırı".
- Ödül şeridi: "Ejderhayı yenersen: +800 XP · Efsanevi rozet · Konu fethi".

### Bitiş overlay'i — BİREBİR
- **Zafer:** kupa rozeti (altın gradyan, kpop) + "Ejderhayı yendin!" + "{konu} konusunu fethettin —
  lig sıran ve XP'n yükseldi." + ödül chip'leri + altın CTA "Zaferi kutla" → Kutlama?type=boss +
  "Yeniden savaş" / "Öğrenme Yolu".
- **Yenilgi:** kalkan rozeti + "Henüz değil" + "Bu tur ejderha güçlüydü — birkaç tekrar, sonra
  yeniden deneriz. Kaybeden yok; sadece 'henüz' olan var." (growth-mindset kopyası — ASLA değiştirme) +
  "Hazırlan, geri dön" (birincil) / "Öğrenme Yolu".
- Zaferde konfeti: inline 90-parça burst → **ConfettiDawn** (reduced-motion'da yok).

### ⚠ Kanon düzeltmeleri (porta taşınmaz)
- Zafer chip'indeki "✓ Konu fethi" metin glyph'i → bespoke SVG tik.
- kfBoss/kfAura/kfHit/kpop → reduced-motion guard (sarsıntı da dahil — vestibüler).

### Veri bağlama (Faz 4) — ⚠ uç eksik
- **openapi'de boss ucu YOK.** Öneri: `POST /boss/session {konuId}` → {bossAd, seviye, maxHP,
  zayifAtom, ilkSoru} · `POST /boss/answer {secim}` → {dogru, hasar, kalanHP, kombo, can,
  sonrakiSoru | sonuc}. Kanon gereği `dogru` + hasar SUNUCUDAN — istemci HP/kombo hesabı yapmaz
  (prototipteki bank + _atk simülasyondur, taşınmaz). XP/rozet yazımı sunucuda.
- Boss teması: en zayıf mat konusu + o konunun en zayıf atomu (prototip formülü) — üretimde
  sunucu seçer, yanıtta gelir.
- Üç durum: Skeleton ("Ejderha uyanıyor…" tonu) · ErrorState (oturum düşerse ilerleme sunucuda —
  kaldığı sorudan devam) · çevrimdışı: boss OYNANMAZ (canlı oturum; girişte uyarı).

### DoD notları
- Kalp/kombo/HP değişimleri `aria-live="polite"` tek satır özet ("Can 4, kombo 2").
- Klavye: 1-4/A-D seçim, Enter saldır.
- 390px: `.rwrap` sarar; seçenek grid'i 1 sütuna düşer (prototipte 2×2 sabit — media query PORT'ta eklenir, kanon-lint değil ürün kararı; not düş).

---

## Sprint 7 açık noktaları
1. Geri Sayım varyantı: A/B deneyi mi kullanıcı tercihi mi? (öneri: varsayılan kaygı-nötr + Ayarlar tercihi + PostHog ölçümü)
2. ~~Boss kırmızı istisnası~~ — **ONAYLANDI (2026-07-04)**: `kanon-allow: boss-arena` mekanizması lint'e eklendi.
3. Boss uçları openapi'ye eklenecek (`/boss/session` + `/boss/answer`) — Faz 4 sözleşme işi.
4. Başarımlar "kazanılan rozet" sayısı sunucudan (`/achievements` özeti) — openapi eki.
5. Boss "9" seviye karesi + "+800 XP" sabitleri veriye bağlanır.

## Ölçüm
Ekran-başı süreyi PORT_DURUM.md'ye yaz. **Grup 5 bitti** → PORT_DURUM'da Grup 5'e tarih at.

---

## Erişilebilirlik satırları (yatay DoD — TASARIM_DENETIM B10, 2026-07-21)

Kanon (her ekranda): odak halkası iki temada da `2px rgba(255,111,92,0.7)` + `outline-offset:2px` (global `:focus-visible`) · görünür etiketi olmayan her etkileşimliye `aria-label` (interpolasyon YOK — tek delik/tek string, runtime gotcha) · tüm hareket `prefers-reduced-motion` guard'lı · dokunmatik bantlarda hit ≥44px.

- Geri Sayım kaygı-nötr varyant: SR çıktısı da SAYISIZ — görselle aynı bilgi (dürüstlük).
- Başarımlar: kilitli rozet `aria-disabled` + "kilitli" metni; tier renk+etiket birlikte.
- Boss: HP çubukları `role="progressbar"` + `aria-valuenow`; combat akışı TEK `aria-live="polite"` bölge (her vuruş assertive DEĞİL); sonuç overlay'inde odak yönetimi.
