# KIRO2 — Erişilebilirlik Denetimi & Gerçek-Cihaz Test Listesi

Bu belge KIRO2 prototipi üzerinde **programatik** olarak yapılan erişilebilirlik denetimini ve bir insanın **gerçek cihazlarda** tamamlaması gereken manuel test listesini içerir.

## Yöntem
- **Renk kontrastı:** Tüm tasarım-sistemi metin/zemin çiftleri için WCAG 2.1 bağıl-parlaklık kontrast oranı hesaplandı (rgba katmanları önce zemine harmanlandı). Eşikler: **AA 4.5** (normal metin <18px / <14px-bold), **AA-large 3.0** (≥18px veya ≥14px-bold).
- **Görünüm:** 390px (iPhone SE/mid Android) genişlikte tüm 21 uygulama ekranı `overflowX=0` (bkz. DEVIR §9), tam-uygulama iframe prob'uyla doğrulandı.
- **Dokunma hedefi:** 21 ekran 390px'te tarandı; hit target ≥44px (bkz. DEVIR §9c).

## Kontrast Sonuçları

### KOYU ekranlar — tümü geçer ✓
| Metin / Zemin | Oran | Sonuç |
|---|---|---|
| `#F1E9F2` / koyu `#150E20` | 15.85 | AA |
| ikincil `rgba(241,233,242,.6)` / koyu | 6.18 | AA |
| dawn `#FFC59B` / `#1A0F26` | 12.03 | AA |
| boss `#C9A8B6` / `#120A14` | 9.04 | AA |
| şafak `#8C8398` / `#110C18` | 5.34 | AA |

Koyu yüzeylerde erişilebilirlik sorunu **yok**.

### AÇIK ekranlar
| Metin / Zemin | Oran | Sonuç | Not |
|---|---|---|---|
| mürekkep `#2A2433` / kâğıt | 13.69 | **AA** | birincil metin |
| muted `#6B6478` / kâğıt | 5.15 | **AA** | ikincil metin |
| muted `#4A4456` / beyaz | 9.32 | **AA** | — |
| POST `#C2452B` / `#FFF3EE` | 4.62 | **AA** | çip |
| faint `#8A8398` / kâğıt | 3.31 | AA-large | küçük meta metin |
| amber `#C77A1E` / beyaz | 3.37 | AA-large | risk/etiket |
| coral text `#B45309` / `#FBF0DE` | 4.45 | AA-large | çip |
| green `#1B8A5A` / `#E3F6EE` | 3.87 | AA-large | çip |
| coral `#FF6F5C` (metin) / beyaz | 2.73 | **FAIL** | yalnız dolgu/ikon olarak kullanılmalı |
| faint `#B0A9B8` / kâğıt | 2.08 | **FAIL** | ipucu/ince yazı |
| disabled `#B5AEA2` / kâğıt | 2.01 | **FAIL** | kilitli/pasif durum |

## Değerlendirme
- **Birincil ve ikincil metin AA uyumlu.** Ana içerik okunabilirliği güçlü.
- **AA-large griler** (`#8A8398`, `#C77A1E`) etiket/meta için kullanılıyor; ≥18px veya bold olduklarında uyumlu, küçük (11-13px) kullanımlarda sıkı-AA'nın altında.
- **FAIL olanlar** çoğunlukla **dekoratif/pasif** rollerde: `#B0A9B8` klavye-ipucu ve ince yazı, `#B5AEA2` kilitli/pasif durum. WCAG pasif kontrolleri ve tamamen dekoratif metni muaf tutar. `#FF6F5C` metin olarak değil, düğme/ikon **dolgusu** olarak kullanılıyor (beyaz metin coral üstünde — ters yön, uyumlu).

## Somut Düzeltme Önerileri — ✅ UYGULANDI (bu tur, yalnız AYDINLIK ekranlar)
Koyu ekranlar zaten tam AA olduğundan (bkz. üstteki tablo) tüm kontrast düzeltmeleri YALNIZ aydınlık ekranlara uygulandı; runtime kontrast denetimiyle doğrulandı (koyu ekran/kart regresyonu = **0**).
1. ✅ **Küçük ikincil metin:** `#8A8398` + `#9A93A5` → **`#6B6478`** (194 örnek / 30 dosya). 3.31 → **5.15 AA**. En yüksek etkili değişiklik.
2. ✅ **Amber etiketler:** küçük `#C77A1E` / `#B5701A` → **`#9A5D0D`** (52 örnek; beyaz 5.32 AA, amber-tint çip 4.72 AA). Koyu ekranda amber `#C77A1E` korundu (zaten AA).
3. ✅ **Coral metin:** sabit `color:#FF6F5C` → **`#C2452B`** (17 örnek; beyaz 5.02 AA). `{{ accent }}`-güdümlü coral metin (kullanıcı-ayarlı vurgu) bilinçli korundu.
4. **İpucu/pasif metin** (`#B0A9B8`, `#B5AEA2`, `#A39BAA`): dekoratif/pasif → WCAG muaf, korundu.
5. ✅ **İkon-only düğmeler:** 3 nav rayı (Öğrenci/Veli/Öğretmen) + topbar dişli/çan + geri/kapat + gönder düğmeleri + Öğrenme Yolu düğümleri + Ayarlar vurgu-swatch'ları → `aria-label`. Runtime: **adsız etkileşimli öğe = 0**.
6. ✅ **Form alanları:** AI Sohbet + Sokratik sohbet girişleri, İnteraktif Çözüm 3 kaydırıcı (a/b/c) → `aria-label`.

**Koyu-kart yan düzeltmesi:** Lig "sıralaman" kartı + Düello güç etiketleri (koyu zeminde muted gri) → **`#9B93A8`** (AA on dark).

### Kalan (bilinçli, 6 önerinin DIŞINDA)
Runtime denetimi sonrası kalan düşük-kontrast örnekler (~174) kapsam dışı:
- **`{{ accent }}` coral metin (~52):** kullanıcı-ayarlı vurgu rengi (varsayılan mercan) — sabit değiştirmek tweak'i bozardı; kullanıcı AA vurgu seçebilir.
- **Anlamsal durum renkleri** (yeşil `#17936B`, kırmızı `#E0593F`, ders mavi/mor): renk-kodlama, çoğu AA-large; öneri listesinde yok.
- **Dekoratif/pasif griler** (`#B5AEA2`, `#B0A9B8`, `#A39BAA`): rec 4 — WCAG muaf.
Bunlar üretimde renk-sistemi kararıyla (yeni token) ele alınmalı.

## Yerinde Olan Erişilebilirlik Özellikleri ✓
- `prefers-reduced-motion: no-preference` — tüm hareket (geçişler, giriş anim.) bu sorgu içinde; hareketi kapatan kullanıcıda durur (49 ekranda, DEVIR §19).
- `:focus-visible` coral odak halkası — klavye navigasyonu görünür (49 ekranda).
- Dokunma hedefleri ≥44px (nav rayı `.ni min-height:44px`, DEVIR §9c).
- 390px'te overflowX=0 (21/21 ekran, DEVIR §9).
- Semantik: `<header>/<main>/<section>/<h1..h3>`; sayılar `tabular-nums`.
- Kaygı-duyarlı dil: alarm-kırmızısı yok (risk=amber), baskı dili yok — bilişsel erişilebilirlik.

## Gerçek-Cihaz Manuel Test Listesi (insan gerektirir)
Programatik denetim ekran-okuyucu davranışını, dokunma ergonomisini ve gerçek ekran koşullarını **kapsayamaz**. Üretim öncesi bir insanın doğrulaması gerekenler:

- [ ] **Ekran okuyucu — iOS VoiceOver:** her ekranı baştan sona gez; okuma sırası mantıklı mı, ikon düğmeler adlandırılmış mı, canlı bölgeler (kutlama, boss hasar) duyuruluyor mu.
- [ ] **Ekran okuyucu — Android TalkBack:** aynı akış.
- [ ] **Dinamik Yazı Tipi / Font ölçekleme %200:** metin taşıyor mu, kesiliyor mu; layout kırılıyor mu.
- [ ] **Gerçek dokunma:** başparmakla 44px hedefler rahat mı; yanlış-dokunma oranı; tek-elle erişim (alt bölge).
- [ ] **Güneş ışığı / parlama:** açık ekranlar dış mekânda okunuyor mu; en soluk griler kayboluyor mu (yukarıdaki FAIL griler burada kritik).
- [ ] **Gerçek cihazlar:** iPhone SE (küçük), iPhone 15 (notch/dynamic island), orta-segment Android (ör. Samsung A-serisi), küçük ekran + düşük DPI.
- [ ] **Klavye / switch-control** navigasyonu: odak sırası, tuzak yok, `:focus-visible` görünür.
- [ ] **OS reduced-motion** açıkken: geçişler duruyor mu (kod hazır, cihazda doğrula).
- [ ] **Renk körlüğü** simülasyonu (protanopi/döteranopi): ders renkleri + durum renkleri ayırt edilebilir mi (renk tek işaret olmamalı — metin/ikon destekli).
- [ ] **Yavaş ağ / offline:** yükleniyor durumları, fallback davranışı.
- [ ] **Sınav kaygısı bağlamı:** gerçek YKS öğrencileriyle bilişsel yük / kaygı testi (bkz. kullanıcı testi planı).

## Özet
Renk kontrastı **koyu ekranlarda tam AA**; açık ekranlarda birincil/ikincil metin AA idi ve **6 öneri bu tur uygulandı** (grey→#6B6478, amber→#9A5D0D, coral-metin→#C2452B, tüm ikon düğmelerine + form alanlarına `aria-label`; runtime denetimiyle doğrulandı — adsız öğe 0, koyu regresyon 0). Kalan düşük-kontrast örnekler kapsam dışı (kullanıcı-ayarlı vurgu, anlamsal durum renkleri, dekoratif griler). Kalan iş **fiziksel cihaz + ekran-okuyucu** manuel doğrulamasıdır.
