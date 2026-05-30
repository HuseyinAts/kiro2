# Kalite Kök Neden — EN DERİN KATMAN (v3, insan + işbirliği + ilk-ilkeler)

**Tarih:** 30 Mayıs 2026
**Yöntem:** 3. tur, 4 paralel forensics ajanı — teknik analizin ULAŞAMADIĞI katman: insan-karar-psikolojisi / insan+AI-işbirliği / ilk-ilkeler öğrenci-değeri / kaldıraç-noktası. Önceki iki doc'u (mekanizma + yapı) İNSAN katmanıyla tamamlar.

> Bu doc bir karar veriyor: **analizin dibi burası.** v1 "yanlış katman ölçüldü" (mekanizma), v2 "kapalı-simülasyon, sıralama-imkânsızlığı" (yapı), v3 "**neden** — yargıdan kaçınma" (insan). Bundan derini analiz değil, **eylem.**

---

## ⚠️ Önce: bu turun yakaladığı phantom (dürüstlük)

Önceki doc'lar "platform gerçeğe hiç dokunmadı / beta hiç açılmadı" dedi. **Git bunu çürütüyor:**
- `2026-05-17` `feat(faz-7-1): Manual Beta launch — 10 user + invite template + tracking SQL`
- `2026-05-19` `fix(beta-feedback): beta01 15 flag resolve` (gerçek kullanıcı 15 flag attı; exam-create HTTP 500 bu sayede yakalandı)

Yani gerçeklik-teması **bir kez oldu** — ve ardından sistem genişlemek yerine **refleksif olarak temizliğe geri çekildi** (13 günlük post-beta pencerede ~60 commit'in hiçbiri gerçek-yanıt işlemiyor; hepsi audit/cila). Bu, "0 reality contact" iddiasını yumuşatır ama asıl tezi **güçlendirir:** beta açıldı, ilk 15 gerçek-flag geldi, ve tepki "ürünü büyüt" değil "havuzu daha çok temizle" oldu. İlk yargı sinyali kaçışı tetikledi. *(Bu phantom, kök-neden doc'ları için de %30-70 phantom kuralının geçerli olduğunun kanıtı.)*

---

## En Derin Kök Neden (insan katmanı)

**198 session'lık mükemmeliyet, "yaptığım şey gerçekten iyi mi?" sorusunu sonsuza dek erteleyen çok zarif bir savunmaydı.** Ürün simülasyonda kaldığı sürece "harika olabilir" ihtimali canlı kalır; gerçek öğrenciye değdiği an o ihtimal ölçülebilir bir gerçeğe (belki "vasat") çöker. Cila, cesaret yokluğu değil — sevilen işin yargılanmasına hazır olmamanın **en üretken görünen biçimi.** Yapısal nedenler (proxy-metrik, kapalı-simülasyon, golden-set yok) bu duygusal motorun *mekanizmalarıydı*; motorun kendisi: **konforlu-belirsizliği rahatsız-yargıya çevirmekten kaçınma.**

---

## Üç pekiştiren katman (kanıtlı)

### 1. İnsan: kutlanan vs ertelenen
Sayıya dönüşen her şey kutlanıp kapatıldı (`%172 EXCEEDED 🟢`, `100% PASS`, `99.95% gold pool`); yargıya açık olan her şey "P0" rozetiyle devredildi (beta launch ~3 ay, 100+ session "Next Priority #1" kaldı). **Beta'nın sonu yok ve kontrol öğrencide; audit'in sonu var ve kontrol sende.** Sistem hep ilkini erteledi. Hatta kutlanan sayıların önemli kısmı stale/yanlıştı (`v_safe_for_beta 23,417→10,535`, `IRT %100→347 kalibre`, `coverage 53%→16.6%`) — kaçış o kadar güçlü ki sığınılan metrik bile çoğu zaman hayaliydi.

### 2. İnsan+AI: döngü deseni büyüttü
~335 simülasyon-içi artifact (202 `_pilots/` + 53 audit + 63 meta-dosya), 53 audit'in %60'ı başka audit'e atıf — kapalı alıntı ağı. AI, inandırıcı proxy-artifact (audit, geçen test, "5/5 consensus") üretmekte friksiyonsuz; ama gerçek öğrenci **getiremez.** Böylece kapanış-sinyali yanlış katmandan geldi: bir task "tamamlandı" sayıldı çünkü *artifact üretildi + simülasyon-içi doğrulandı*, *bir insan davranışı değiştiği için* değil. **AI'nın erişemediği şey (gerçek öğrenci), gerekli-olmayan gibi davranıldı.** *(Bu session dahil: "gerçeğe dokun" denildi, daha çok analiz üretildi — döngü bir kez daha tekrarladı.)*

### 3. İlk-ilkeler: enerji ölçülebilir-olana aktı, kritik-olana değil
Öğrenci-değerinin gerçek %20'si — **dönüş-alışkanlığı (habit loop) + ilk-gün onboarding + ~3K temiz soru + doğru rationale** — büyük ölçüde ihmal edildi:
- **Retention push** (Duolingo'nun 1 numaralı silahı) 198 session boyunca `logger.debug` + `users[:10]` idi; **ilk kez bugün canlıya alındı** (P0.1, `8d2568a69`).
- **Onboarding sayfası:** ~60 frontend sayfası var (BossFight, TokenOptimizationDashboard, RBACTestPage dahil) — `onboard/welcome/intro` **sıfır.**
- **Rationale:** en kritik öğrenme kaldıracı, **%26.7 kabul-edilemez** bırakıldı.
- **Cevap-anahtarı:** %96→%99 son hassasiyetine 100+ task; ama A-bias root #1 hâlâ açık (sistematik hata) — enerji marjinal-hassasiyete gitti, kritik-hataya değil.

"Lambanın altında anahtar arama": kalite, *ölçülebilir + AI-otomatik* olduğu için içerik-doğruluğunda arandı; oysa belirleyici olan *ölçmesi zor ama yokluğu öldürücü* habit-loop ve ilk-gün deneyimiydi.

---

## Kaldıraç: çaba en altta, kaldıraç en üstte

Meadows hiyerarşisi: 198 session'ın tamamı en düşük basamaklarda (12-parametre: cevap-anahtarı, soru-sayısı, IRT-değeri) döndü. Gerçek kaldıraç en üstte boş duruyor:
- **8. Geri-besleme döngüsü** (gerçek-öğrenci sinyali) = `irt_n_responses=0`, `curator_verdict=0` — **boş.**
- **1. Paradigma** ("mükemmelleştir-sonra-launch" → "launch-sonra-öğren") = **hiç sorgulanmadı.**

En keskin kanıt: parametre basamağında 49,468 satır image-match (Tier H) — ama o görseller `false &&` ile render bile edilmiyor. *Kalite-tanımı (üst basamak) kurulmadığı için, render edilmeyen alana aylarca parametre yazıldı.*

---

## TEK Kaldıraç-Act (bu hafta, teknik bariyer YOK)

> **~500 tertemiz-okunabilir-VE-kör-çözüm-doğrulanmış soruyla, 10-20 gerçek YKS öğrencisine 1 haftalık kapalı beta. Tek metrik: öğrenci render edilen soruyu okuyup çözdü mü + cevap anahtarı tuttu mu.**

- Çekirdek zaten var (TARIH %93, SOSYAL %90, kısa-metin dersler hazır; mat/geo %9 halüs sınırda-yeterli). 500 temiz soru bir günde süzülür — 167K mükemmelleştirilmesi GEREKMİYOR.
- Tek yeni iş: bu 500'ün **render-artifact üzerinde kör-bağımsız-çözüm gate'i** (DB-cevabı verip "doğrula" demek dairesel; kör çözdürmek değil — 42-sample ile kanıtlandı). Bounded.
- İlk ~30 yanıt/soru → gerçek IRT, mis-keyed sinyali, gerçek D1 dönüş. **Tek yapısal kilit açıcı.**

**Engelleyen gerçek (teknik değil) bariyer:** Docker hazır, E2E 7/7, golden flow yeşil. Bariyer davranışsal: (1) yargıdan kaçınma, (2) `%172 EXCEEDED` vanity-story'sini "500 ile başlıyoruz" itirafıyla değiştirme zorluğu, (3) "yeterince iyi" kırılganlığının "biz mükemmelleştiriyoruz" konforuna tercihi.

---

## Reframe (suçlama değil, ayna)

198 session **emek israfı değildi** — doğru iş, **yanlış sırada** ve **gerçek yerine proxy'ye karşı ölçülerek** yapıldı. Kova doğruydu, öncelik tersine dönmüştü. Eksik olan emek değil — **gerçeklik-teması ve onu göze almak.**

İşbirliği-kuralı (bundan sonra): *Hiçbir kalite-task'ı "tamamlandı" sayılamaz, çıktısı en az 1 gerçek beta-kullanıcısının önüne çıkana kadar. "Audit/test/consensus geçti" kapanış değil, ön-koşuldur. Her oturum, ürettiği artifact'i değil, kullanıcıya gösterilen delta'yı raporlar; delta 0 ise "ilerleme yok".*

---

*İlişkili: `kalite_kok_neden.md` (mekanizma), `kalite_kok_neden_DERIN.md` (yapı), bu (insan). Sonraki adım: ANALİZ DEĞİL — 500 temiz soru çekirdeği + kör-çözüm gate + 20 gerçek öğrenci.*
