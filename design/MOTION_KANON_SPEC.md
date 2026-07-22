# KIRO Motion Kanonu — Yapım Spec'i (DC yazılmadan önceki plan)

> Hedef dosya: `KIRO Motion Kanonu.dc.html` (kök dizin, otoriter referanslara katılır).
> Format: `KIRO Safak Mimari.dc.html` gibi kanon-dokümanı DC — paper zemin, bölüm bölüm,
> her kuralın YANINDA canlı demo (renderVals içinde createElement ile animasyonlu örnekler,
> template'te hole ile — animasyon state'i re-render'da yaşasın).

## 1. Süre skalası (token)
- `an` 120ms — hover/renk tepkisi, chip durum değişimi
- `adim` 200ms — kart giriş, buton basma, toggle
- `gecis` 320ms — ekran içi bölüm değişimi, akordeon
- `sahne` 600ms — ekran geçişi, faz değişimi (form→3ds gibi)
- `tören` 1200ms+ — kutlama/boss/güneş doğuşu (yalnız duygusal anlar)

## 2. Easing skalası
- `cikis` cubic-bezier(0.16, 1, 0.3, 1) — giren her şey (hızlı başla, yumuşak dur)
- `giris` cubic-bezier(0.7, 0, 0.84, 0) — çıkan/kapanan
- `nefes` ease-in-out sinüs — Mola nefes kutusu, gök nabzı (4s döngü)
- `spring` (JS, ~%8 overshoot) — YALNIZ kutlama + streak sayaç zıplaması. Çalışma ekranlarında spring YASAK (kaygı: zıplayan UI = oyunlaştırma sinyali).

## 3. Stagger kuralı
- Liste/kart girişleri: 48ms aralık, maks 8 öğe (sonrası aynı anda), yukarıdan aşağı.
- Y-ofset 8px + opacity 0→1; scale KULLANILMAZ (paper ekranlarda büyüme yok).

## 4. Şafak imza geçişi (ürün kimliği)
- Ekranlar arası: alt kenardan 120% genişlikte dawn-gradyan ışık süpürmesi (mercan→şeftali→şeffaf),
  600ms `cikis`, içerik 80ms gecikmeyle stagger başlar. Yalnız dusk↔paper geçişlerinde tam sahne;
  paper→paper'da minimal (yalnız stagger).
- Güneş doğuşu töreni: boss zaferi + büyük kutlamada ufuk çizgisi + yükselen disk, 1600ms.

## 5. Ekran-türü kuralları
- **Paper (çalışma):** yalnız `an/adim/gecis`, opacity+translate, spring yok, tören yok.
- **Dusk (duygusal):** `sahne/tören` serbest, gök nabzı, ConfettiDawn buradan tetiklenir.

## 6. Reduced-motion
- Tüm token'lar `prefers-reduced-motion: reduce` altında: süreler 0, stagger 0, nefes kutusu
  animasyonsuz sayaçlı, konfeti statik final karesi. Her demoda guard gösterilir.

## 7. DC yapısı (bölümler)
1. Başlık + ilke ("Hareket ödül değil, yön duygusudur — kaygıyı azaltır, artırmaz.")
2. Süre + easing tablosu (canlı eğri çizimleri + tekrar-oynat butonlu top demoları)
3. Stagger demo (kart listesi, tekrar butonu)
4. Şafak imza geçişi demo (mini ekran mockup'ı üstünde)
5. Paper vs Dusk yasak/serbest matrisi
6. Reduced-motion bölümü
7. Uygulama notu: CSS değişken adları (`--k-motion-an` vb. ÜRETİM için; prototipte inline)

## 8. Bitince
- kanon-lint'e kural önerisi: çalışma-ekranı DC'lerinde `spring`/`bounce`/`elastic` anahtar
  kelimesi = uyarı.
- YENI_SOHBET_DEVIR.md §6e + otoriter referans listesine ekle; TASARIM_DENETIM.md B1 işaretle.
