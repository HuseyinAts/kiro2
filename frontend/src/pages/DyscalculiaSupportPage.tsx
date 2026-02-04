/**
 * Dyscalculia Support Demo Page
 * 
 * Diskalkuli desteği için görsel matematik temsilleri demo sayfası.
 * Tüm 4 component'i tek bir sayfada gösterir.
 */

import React, { useState } from 'react';
import {
  NumberBlocks,
  FractionBars,
  GeometricShapes3D,
  GraphPlotter
} from '../components/Accessibility/Dyscalculia';
import './DyscalculiaSupportPage.css';

type ActiveTab = 'numbers' | 'fractions' | 'shapes' | 'graphs';

const DyscalculiaSupportPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<ActiveTab>('numbers');

  return (
    <div className="dyscalculia-support-page">
      <header className="page-header">
        <h1>Diskalkuli Desteği - Görsel Matematik Temsilleri</h1>
        <p className="page-description">
          Matematik öğrenme güçlüğü yaşayan öğrenciler için özel olarak tasarlanmış
          interaktif görsel araçlar. Soyut matematiksel kavramları somut hale getirerek
          öğrenmeyi kolaylaştırır.
        </p>
      </header>

      <nav className="tab-navigation">
        <button
          className={`tab-btn ${activeTab === 'numbers' ? 'active' : ''}`}
          onClick={() => setActiveTab('numbers')}
        >
          <span className="tab-icon">🔢</span>
          <span className="tab-label">Sayı Blokları</span>
        </button>
        <button
          className={`tab-btn ${activeTab === 'fractions' ? 'active' : ''}`}
          onClick={() => setActiveTab('fractions')}
        >
          <span className="tab-icon">📊</span>
          <span className="tab-label">Kesir Çubukları</span>
        </button>
        <button
          className={`tab-btn ${activeTab === 'shapes' ? 'active' : ''}`}
          onClick={() => setActiveTab('shapes')}
        >
          <span className="tab-icon">🎲</span>
          <span className="tab-label">3D Şekiller</span>
        </button>
        <button
          className={`tab-btn ${activeTab === 'graphs' ? 'active' : ''}`}
          onClick={() => setActiveTab('graphs')}
        >
          <span className="tab-icon">📈</span>
          <span className="tab-label">Grafik Çizim</span>
        </button>
      </nav>

      <main className="page-content">
        {activeTab === 'numbers' && (
          <section className="tool-section">
            <div className="section-intro">
              <h2>Sayı Blokları (Base-10 Sistemi)</h2>
              <p>
                Basamak değerini ve sayı kavramını görsel olarak anlamak için Base-10 blok sistemi.
                Binler, yüzler, onlar ve birler basamaklarını farklı renk ve boyutlarda gösterir.
              </p>
              <div className="features-list">
                <span className="feature-badge">✓ İnteraktif Manipülasyon</span>
                <span className="feature-badge">✓ Drag & Drop</span>
                <span className="feature-badge">✓ Toplama/Çıkarma Animasyonları</span>
                <span className="feature-badge">✓ Renkli Kodlama</span>
              </div>
            </div>
            <NumberBlocks 
              initialValue={1234}
              showAnimation={true}
            />
          </section>
        )}

        {activeTab === 'fractions' && (
          <section className="tool-section">
            <div className="section-intro">
              <h2>Kesir Çubukları</h2>
              <p>
                Kesirleri görselleştirmek, denk kesirleri bulmak ve kesir işlemlerini anlamak için
                interaktif kesir çubukları. Her kesir parçası renkli olarak gösterilir.
              </p>
              <div className="features-list">
                <span className="feature-badge">✓ Denk Kesir Görselleştirme</span>
                <span className="feature-badge">✓ Kesir Karşılaştırma</span>
                <span className="feature-badge">✓ Kesir İşlemleri</span>
                <span className="feature-badge">✓ Gerçek Zamanlı Değer Gösterimi</span>
              </div>
            </div>
            <FractionBars 
              showEquivalent={true}
              showComparison={true}
            />
          </section>
        )}

        {activeTab === 'shapes' && (
          <section className="tool-section">
            <div className="section-intro">
              <h2>3D Geometrik Şekiller</h2>
              <p>
                Küp, küre, silindir, koni ve piramit gibi 3D şekilleri görselleştirin.
                360 derece döndürme, hacim ve yüzey alanı hesaplamaları ile öğrenin.
              </p>
              <div className="features-list">
                <span className="feature-badge">✓ 360° Rotasyon</span>
                <span className="feature-badge">✓ Hacim Hesaplama</span>
                <span className="feature-badge">✓ Yüzey Alanı</span>
                <span className="feature-badge">✓ Şekil Açılımı (Net)</span>
              </div>
            </div>
            <GeometricShapes3D 
              showMeasurements={true}
              showNet={true}
            />
          </section>
        )}

        {activeTab === 'graphs' && (
          <section className="tool-section">
            <div className="section-intro">
              <h2>Grafik Çizim Aracı</h2>
              <p>
                Matematiksel fonksiyonları görselleştirin. Doğrusal, karesel, trigonometrik ve
                üstel fonksiyonları interaktif koordinat sisteminde çizin.
              </p>
              <div className="features-list">
                <span className="feature-badge">✓ Gerçek Zamanlı Çizim</span>
                <span className="feature-badge">✓ Zoom & Pan</span>
                <span className="feature-badge">✓ Nokta Seçimi</span>
                <span className="feature-badge">✓ Renkli Eksenler</span>
              </div>
            </div>
            <GraphPlotter 
              initialFunction="x^2"
              showMeasurements={true}
            />
          </section>
        )}
      </main>

      <footer className="page-footer">
        <div className="footer-content">
          <h3>Diskalkuli Hakkında</h3>
          <p>
            Diskalkuli, sayıları anlama ve matematiksel işlemleri yapma konusunda yaşanan
            öğrenme güçlüğüdür. Bu araçlar, soyut matematiksel kavramları somut görsel
            temsillerle sunarak öğrenmeyi kolaylaştırır ve matematik kaygısını azaltır.
          </p>
          <div className="support-info">
            <p><strong>Gereksinimler:</strong> REQ-51.1 - REQ-51.20</p>
            <p><strong>WCAG Uyumluluğu:</strong> Level AA</p>
            <p><strong>Tarayıcı Desteği:</strong> Chrome, Firefox, Safari, Edge</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default DyscalculiaSupportPage;
