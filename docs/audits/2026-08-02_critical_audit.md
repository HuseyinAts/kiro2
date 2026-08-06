# KIRO2 7-Lens Kritik Sistem Analizi (02 Ağustos 2026)

Bu rapor, kullanıcıdan gelen geri bildirimler ve sistemin derinlemesine taranması sonucu ortaya çıkan bulgularla oluşturulmuştur. Modelin 7 farklı lens (optik) kullanarak tespit ettiği mimari, kullanıcı deneyimi, güvenlik ve performans zafiyetleri aşağıda listelenmiştir.

## 1. UI/UX (Kullanıcı Arayüzü ve Deneyimi) Lens
* **AI Öğretmen Asistanı Görsel Eksikliği (KRİTİK):** Kullanıcının haklı isyanı; `AISohbetPage.tsx` içerisinde mesajlaşma girdisi olarak sadece bir `<textarea>` kullanılmış. YKS (özellikle Geometri ve karmaşık Matematik) bağlamında öğrencilerin çözemedikleri soruların fotoğraflarını çekip atabilmeleri (OCR / Görüntü İşleme) şarttır. Dosya yükleme butonu `<input type="file">` arayüzde tamamen unutulmuş.
* **Öğrenme Yolunda Kötü Soru Gösterimleri ve Kırık Link:** `OgrenmeYoluPage.tsx` dosyasında sıradaki konuya (soru çözmeye) geçiş için React Router'ın `navigate` fonksiyonu veya `<Link>` komponenti yerine `<a href="/soru-cozme">` kullanılmış. Bu, SPA (Single Page Application) yapısını bozar ve tüm React state'ini (ve hafızasını) sıfırlayarak hard-reload yapar. Ayrıca `App.tsx` içerisinde `/soru-cozme` rotası tanımlı bile değil! Kullanıcı konuya başla dediğinde 404 hatasına düşüyor.

## 2. Backend & API (Sunucu ve Uç Noktalar) Lens
* **Haftalık Plan 404 Hatası:** Frontend'de `App.tsx`'te günlük plan (`/daily-plan`) mevcut ancak kullanıcının belirttiği haftalık plan özelliğinin rotası ve görünümü (View) tamamen kayıp. Eğer kullanıcılar dashboard veya eski bir e-posta bildiriminden haftalık plana gitmeye çalışırlarsa sistem doğrudan 404 dönmektedir. Haftalık hedefler ile günlük hedefler (Daily Quests) birbirine karıştırılmış.
* **Eksik API Hata Yönetimi:** Öğrenme yolunda veri çekerken API fail olursa sadece jenerik bir "Bağlantı soluklandı" mesajı veriliyor, arkasındaki HTTP 500 veya 401 hatası analiz edilip (Örn: Token expires) yönlendirme yapılmıyor.

## 3. Data & State (Veri Yönetimi) Lens
* **LaTeX Rendering Parsing Zafiyeti (Adaptif Test & Geometri):** Kullanıcının verdiği örnek: `$A(1, 2)$ noktası $(x-4)^2 + (y+2)^2 = r^2$`. `MathText.tsx` içerisindeki `autoWrapBareLatex` fonksiyonu metin içerisinde `$` karakteri bulduğunda tüm metni wrap etmeyi bırakıyor ve doğrudan `react-markdown` ile parse etmeye çalışıyor. Ancak ardışık formüller içeren metinlerde veya `$` etiketleri arasında Türkçe/alfanümerik text bulunduğunda (Örn: `... noktası ...`), `remark-math` parse ağacını kırarak formülü düz yazı (plain-text) gibi render ediyor ve `katex` sınıfları devreye girmiyor.
* **İzolasyon Sorunu:** `App.tsx` ve Sayfa komponentleri arası prop geçişleri yerine sürekli hook-based global state (`useAuthStore`) çağırımları bileşenlerin tekrar kullanılabilirliğini düşürmüş.

## 4. Security (Güvenlik) Lens
* **Sohbet XSS Riski:** `AISohbetPage.tsx`'te kullanıcı input'u `ReactMarkdown` ile render edilirken (LLM çıktısı dahil), `DOMPurify` gibi bir sanitasyon aracı kullanılmamış. Kötü niyetli bir prompt enjeksiyonu LLM'in zararlı bir `<script>` veya XSS payload'u dönmesine sebep olabilir, bu da doğrudan tarayıcıda çalışır.
* **State Üzerinden Veri Sızıntısı:** Redux/Zustand devtools kapatılmamışsa, öğrenci paneli üzerinden (API'den dönen ve UI'da kullanılmayan) ham JWT token'ları, gizli admin ID'leri client belleğine sızdırılıyor olabilir.

## 5. Performance (Performans) Lens
* **Math/KaTeX Bundle Bloat:** `katex`, `rehype-katex` ve `remark-math` kütüphaneleri `MathText.tsx`'te doğrudan import edilmiş. Soru çözülmeyen, LaTeX içermeyen sayfalarda bile bu devasa bağımlılıklar ana JS bundle'ına dahil ediliyor. Lazy loading kullanılmamış.
* **Gereksiz Yeniden Çizim (Re-render):** `OgrenmeYoluPage` içindeki dikey patika, ders (Matematik, Fizik vb.) değiştirildiğinde tüm API'leri eşzamanlı tekrar çağırıp ekranı kitliyor. Lokal cache (`react-query`'nin `staleTime` konfigürasyonları) tam olarak entegre edilmemiş.

## 6. Pedagogy (Pedagojik Yaklaşım) Lens
* **Matematik ve Geometride Görsel Yokluğu:** Adaptif testte sadece text üzerinden denklem sorulması YKS sisteminin gerçekçi doğasına (ÖSYM'nin görsel ve paragraf ağırlıklı yeni nesil soruları) tamamen terstir. Sistemin en büyük pedagojik eksiği budur.
* **Niceliksel Zehirlenme:** Dashboard üzerindeki "Alev (Seri)", "Kupa" ve "XP" öğeleri o kadar baskın ki, öğrenci konu eksiğini kapatmaktan ziyade sistemi "grind" etmeye (boş soru çözerek puan kasmaya) yönlendiriliyor.

## 7. Infrastructure & Code Quality (Altyapı ve Kod Kalitesi) Lens
* **Geçersiz HTML DOM Yuvalaması:** `MathText.tsx`'te `inline` özelliği `false` olduğunda `div` basıyor ama ReactMarkdown içindeki `p` etiketlerine müdahale şekli nedeniyle, eğer dışarıdan bir `p` etiketine sarılırsa "p inside p" (Geçersiz HTML) hatası üretme potansiyeli var.
* **Klasör ve Rota Dağınıklığı:** `pages`, `kiro/screens`, `kiro/routes` gibi birden fazla dizin yapısı birbiriyle karışmış. Hangi rotanın App-router'da hangisinin bağımsız çalıştırılabilir test bileşeni olduğu belirsizleşmiş. (Örn: `App.tsx`'te `/parent-new` yazıyor ama `ModernParentDashboard` componentini çağırıyor).

### SONUÇ VE AKSİYON PLANI
Kullanıcı tarafından bildirilen (Görsel yükleme, 404 Haftalık plan, Kötü soru gösterimi, LaTeX hatası) sorunlar tamamen doğrulanmıştır. Bunlar basit "bug"lar değil, UI mimarisinde ve routing katmanında alınmış yanlış mühendislik kararlarının doğrudan sonuçlarıdır. Hızlı düzeltmeler için:
1. `App.tsx`'e `/soru-cozme` ve `/weekly-plan` rotaları eklenmeli.
2. `AISohbetPage.tsx`'e `<input type="file" />` entegre edilerek Image OCR backend endpoint'ine bağlanmalı.
3. `MathText.tsx` regex ve parse mimarisi, cümlenin ortasındaki `$ ... $` syntax'ini bozmayacak şekilde (escaped delimiter ile) yeniden yazılmalı.
