/**
 * Tipografi Ayarları Sayfası
 * Task 76: Tipografi ve Görsel Düzenlemeler Demo
 */

import * as React from 'react';

import { TypographySettings } from '../components/Accessibility';
import '../styles/typography-settings.css';

export const TypographySettingsPage: React.FC = () => {
  return (
    <div className="typography-settings-page">
      <div className="page-container">
        <header className="page-header">
          <h1>Tipografi ve Okuma Ayarları</h1>
          <p className="page-subtitle">
            Okuma deneyiminizi kişiselleştirin. Disleksi ve diğer öğrenme farklılıkları için optimize edilmiş ayarlar.
          </p>
        </header>

        <main className="page-content">
          <TypographySettings />

          <section className="info-section">
            <h2>Disleksi Desteği Hakkında</h2>
            <div className="info-grid">
              <div className="info-card">
                <div className="info-icon">🔤</div>
                <h3>Özel Fontlar</h3>
                <p>
                  OpenDyslexic ve Dyslexie fontları, harflerin birbirine karışmasını önlemek için
                  özel olarak tasarlanmıştır. Her harfin benzersiz bir şekli vardır.
                </p>
              </div>

              <div className="info-card">
                <div className="info-icon">📏</div>
                <h3>Aralık Ayarları</h3>
                <p>
                  Satır, harf ve kelime aralıklarını artırmak, metni daha kolay takip edilebilir
                  hale getirir ve okuma yorgunluğunu azaltır.
                </p>
              </div>

              <div className="info-card">
                <div className="info-icon">🎨</div>
                <h3>Renk Desteği</h3>
                <p>
                  Renkli overlay&apos;ler, beyaz sayfa parlaklığını azaltır ve göz yorgunluğunu önler.
                  Her kişi için farklı renkler daha rahat olabilir.
                </p>
              </div>

              <div className="info-card">
                <div className="info-icon">⚡</div>
                <h3>Anında Uygulama</h3>
                <p>
                  Tüm ayarlar gerçek zamanlı olarak uygulanır ve tarayıcınızda kaydedilir.
                  Bir sonraki ziyaretinizde ayarlarınız hazır olacak.
                </p>
              </div>
            </div>
          </section>

          <section className="tips-section">
            <h2>Kullanım İpuçları</h2>
            <ul className="tips-list">
              <li>
                <strong>Başlangıç için:</strong> &quot;Hafif&quot; preset&apos;i deneyin ve ihtiyacınıza göre ayarlayın.
              </li>
              <li>
                <strong>Font seçimi:</strong> OpenDyslexic veya Dyslexie fontlarını deneyin.
                Hangisi daha rahat geliyorsa onu kullanın.
              </li>
              <li>
                <strong>Font boyutu:</strong> 16-18pt arası çoğu kişi için idealdir.
                Mobil cihazlarda biraz daha büyük tercih edilebilir.
              </li>
              <li>
                <strong>Satır aralığı:</strong> 1.5-1.8x arası okumayı kolaylaştırır.
                Daha geniş aralıklar uzun metinlerde yorgunluğu azaltır.
              </li>
              <li>
                <strong>Harf ve kelime aralığı:</strong> 0.1-0.15em arası disleksi için önerilir.
                Çok fazla artırmak okumayı zorlaştırabilir.
              </li>
              <li>
                <strong>Önizleme:</strong> Her değişiklikten sonra önizleme bölümünü kontrol edin.
                Rahat hissettiğiniz ayarları bulun.
              </li>
            </ul>
          </section>

          <section className="research-section">
            <h2>Bilimsel Araştırmalar</h2>
            <p>
              Disleksi dostu tipografi ayarları, çok sayıda bilimsel çalışma ile desteklenmektedir:
            </p>
            <ul className="research-list">
              <li>
                Geniş harf aralığı, disleksili okuyucuların okuma hızını %20&apos;ye kadar artırabilir
                (Zorzi et al., 2012).
              </li>
              <li>
                Özel tasarlanmış fontlar (OpenDyslexic, Dyslexie), harf karışıklığını azaltır ve
                okuma doğruluğunu artırır (Rello & Baeza-Yates, 2013).
              </li>
              <li>
                Satır aralığının artırılması, göz hareketlerini düzenler ve okuma akıcılığını
                iyileştirir (Schneps et al., 2013).
              </li>
              <li>
                Renkli overlay&apos;ler, görsel stres belirtilerini azaltabilir ve okuma konforunu
                artırabilir (Wilkins, 2003).
              </li>
            </ul>
          </section>
        </main>
      </div>
    </div>
  );
};

export default TypographySettingsPage;
