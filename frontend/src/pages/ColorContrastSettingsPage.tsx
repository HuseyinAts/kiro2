/**
 * Renk ve Kontrast Ayarları Sayfası
 * REQ-50.14 - REQ-50.27: Renk ve Kontrast Ayarları
 * 
 * Task 77: Renk ve Kontrast Ayarları Demo Sayfası
 */

import React from 'react';
import { ColorContrastSettings } from '../components/Accessibility';
import '../styles/color-contrast-settings.css';

export const ColorContrastSettingsPage: React.FC = () => {
  return (
    <div className="color-contrast-settings-page">
      <div className="page-container">
        <header className="page-header">
          <h1>Renk ve Kontrast Ayarları</h1>
          <p className="page-subtitle">
            Görsel konforunuzu artırmak için renk overlay, opacity ve kontrast ayarlarını özelleştirin.
            Tüm ayarlar WCAG 2.1 erişilebilirlik standartlarına uygun olarak tasarlanmıştır.
          </p>
        </header>

        <main className="page-content">
          <ColorContrastSettings />
        </main>

        <footer className="page-footer">
          <div className="info-cards">
            <div className="info-card">
              <h3>🎨 Renkli Overlay</h3>
              <p>
                6 farklı renk seçeneği ile ekran üzerine renkli bir filtre uygulayın.
                Mavi, yeşil, sarı, pembe, mor ve gri tonları mevcuttur.
              </p>
            </div>
            <div className="info-card">
              <h3>🔆 Opacity Kontrolü</h3>
              <p>
                %10 ile %90 arası overlay şeffaflığını ayarlayın.
                Gerçek zamanlı önizleme ile değişiklikleri anında görün.
              </p>
            </div>
            <div className="info-card">
              <h3>⚡ Yüksek Kontrast</h3>
              <p>
                Normal, yüksek kontrast, karanlık mod ve özel kontrast seçenekleri.
                Tüm UI elementlerine tutarlı şekilde uygulanır.
              </p>
            </div>
            <div className="info-card">
              <h3>✓ WCAG AAA Uyumlu</h3>
              <p>
                Minimum 7:1 kontrast oranı ile WCAG AAA standardına uyumluluk.
                Otomatik kontrast hesaplayıcı ve düzeltme önerileri.
              </p>
            </div>
          </div>

          <div className="requirements-section">
            <h2>Karşılanan Gereksinimler</h2>
            <ul className="requirements-list">
              <li>
                <strong>REQ-50.14:</strong> 6 farklı renk seçeneği (mavi, yeşil, sarı, pembe, mor, gri)
              </li>
              <li>
                <strong>REQ-50.15:</strong> Seçilen rengi tüm sayfa üzerine uygulama
              </li>
              <li>
                <strong>REQ-50.16:</strong> %10 ile %90 arası opacity kontrolü
              </li>
              <li>
                <strong>REQ-50.17:</strong> Metin okunabilirliğini korumak için otomatik kontrast ayarı
              </li>
              <li>
                <strong>REQ-50.18:</strong> Gerçek zamanlı önizleme
              </li>
              <li>
                <strong>REQ-50.19:</strong> 150ms içinde yumuşak geçiş
              </li>
              <li>
                <strong>REQ-50.20:</strong> Tercihleri localStorage'da kalıcı saklama
              </li>
              <li>
                <strong>REQ-50.21:</strong> Önceden tanımlı yüksek kontrast temaları
              </li>
              <li>
                <strong>REQ-50.22:</strong> Dark mode desteği
              </li>
              <li>
                <strong>REQ-50.23:</strong> Custom contrast ratio hesaplaması
              </li>
              <li>
                <strong>REQ-50.24:</strong> Tüm UI elementlerine tutarlı uygulama
              </li>
              <li>
                <strong>REQ-50.25:</strong> Minimum 7:1 kontrast oranı (WCAG AAA)
              </li>
              <li>
                <strong>REQ-50.26:</strong> Otomatik kontrast hesaplayıcı
              </li>
              <li>
                <strong>REQ-50.27:</strong> Kontrast uyumsuzluğunda otomatik düzeltme önerisi
              </li>
            </ul>
          </div>
        </footer>
      </div>
    </div>
  );
};

export default ColorContrastSettingsPage;
