/**
 * Okuma Yardımcıları Bileşeni
 * REQ-50.28 - REQ-50.42: Okuma Yardımcıları
 *
 * Task 78: Okuma Yardımcıları
 * - 78.1: Okuma cetveli (reading ruler)
 * - 78.2: Odak modu (focus mode)
 * - 78.3: Kelime vurgulama
 * - 78.4: Hece ayırma
 */

import * as React from 'react';
import {  useState  } from 'react';

import { useReadingHelpers } from '../../hooks/useReadingHelpers';
import './ReadingHelpers.css';

interface ReadingHelpersProps {
  className?: string;
}

export const ReadingHelpers: React.FC<ReadingHelpersProps> = ({ className = '' }) => {
  const {
    settings,
    isLoading,
    updateSetting,
    resetSettings,
    applyPreset,
  } = useReadingHelpers();

  const [showPreview, setShowPreview] = useState(true);

  if (isLoading) {
    return (
      <div className={`reading-helpers ${className}`}>
        <div className="loading-spinner">Ayarlar yükleniyor...</div>
      </div>
    );
  }

  const previewText = `
    Türkiye Üniversite Sınavları Hazırlık Platformu'na hoş geldiniz! 
    Bu platform, YKS (TYT/AYT/YDT) sınavlarına hazırlanan öğrenciler için 
    AI destekli, kişiselleştirilmiş bir eğitim sistemidir. Platform, ÖSYM ve 
    MEB müfredatına tam uyumlu içerikler sunarak öğrencilerin bireysel öğrenme 
    hızlarına göre kişiselleştirilmiş eğitim yolları oluşturur.
  `;

  return (
    <div className={`reading-helpers ${className}`}>
      <div className="settings-header">
        <h2>Okuma Yardımcıları</h2>
        <p className="settings-description">
          Okuma deneyiminizi geliştirmek için çeşitli yardımcı araçları etkinleştirin.
        </p>
      </div>

      {/* Hızlı Preset Seçenekleri */}
      <div className="preset-section">
        <h3>Hızlı Ayarlar</h3>
        <div className="preset-buttons">
          <button
            onClick={() => applyPreset('basic')}
            className="preset-button"
            aria-label="Temel okuma yardımcılarını uygula"
          >
            <span className="preset-icon">📖</span>
            <span className="preset-label">Temel</span>
            <span className="preset-description">Okuma cetveli + vurgulama</span>
          </button>
          <button
            onClick={() => applyPreset('focus')}
            className="preset-button"
            aria-label="Odak modunu uygula"
          >
            <span className="preset-icon">🎯</span>
            <span className="preset-label">Odak</span>
            <span className="preset-description">Dikkat dağınıklığını azalt</span>
          </button>
          <button
            onClick={() => applyPreset('advanced')}
            className="preset-button"
            aria-label="Gelişmiş okuma yardımcılarını uygula"
          >
            <span className="preset-icon">⚡</span>
            <span className="preset-label">Gelişmiş</span>
            <span className="preset-description">Tüm özellikler aktif</span>
          </button>
        </div>
      </div>

      {/* Okuma Cetveli - Task 78.1 (REQ-50.28 - REQ-50.31) */}
      <div className="setting-group">
        <div className="setting-header">
          <label htmlFor="reading-ruler-toggle" className="setting-label">
            <span className="label-text">Okuma Cetveli</span>
            <span className="label-badge">
              {settings.readingRuler.enabled && '✓ Aktif'}
            </span>
          </label>
          <div className="toggle-switch">
            <input
              type="checkbox"
              id="reading-ruler-toggle"
              checked={settings.readingRuler.enabled}
              onChange={(e) => updateSetting('readingRuler', { ...settings.readingRuler, enabled: e.target.checked })}
              className="toggle-input"
              aria-describedby="reading-ruler-description"
            />
            <label htmlFor="reading-ruler-toggle" className="toggle-label" aria-label="Toggle reading ruler">
              <span className="toggle-slider" aria-hidden="true"></span>
            </label>
          </div>
        </div>
        <p id="reading-ruler-description" className="setting-description">
          Okuduğunuz satırı vurgulamak için yatay bir cetvel görüntüler.
        </p>

        {settings.readingRuler.enabled && (
          <div className="sub-settings">
            {/* Cetvel Yüksekliği */}
            <div className="sub-setting">
              <label htmlFor="ruler-height" className="sub-setting-label">
                <span>Cetvel Yüksekliği</span>
                <span className="label-value">{settings.readingRuler.height}px</span>
              </label>
              <input
                id="ruler-height"
                type="range"
                min="30"
                max="100"
                step="5"
                value={settings.readingRuler.height}
                onChange={(e) => updateSetting('readingRuler', { ...settings.readingRuler, height: parseInt(e.target.value) })}
                className="slider"
                aria-valuemin={30}
                aria-valuemax={100}
                aria-valuenow={settings.readingRuler.height}
                aria-valuetext={`${settings.readingRuler.height} piksel`}
              />
              <div className="slider-labels">
                <span>30px</span>
                <span>65px</span>
                <span>100px</span>
              </div>
            </div>

            {/* İmleci Takip Et */}
            <div className="sub-setting">
              <label htmlFor="follow-cursor-checkbox" className="checkbox-label">
                <input
                  id="follow-cursor-checkbox"
                  type="checkbox"
                  checked={settings.readingRuler.followCursor}
                  onChange={(e) => updateSetting('readingRuler', { ...settings.readingRuler, followCursor: e.target.checked })}
                  className="checkbox-input"
                />
                <span>İmleci Takip Et</span>
              </label>
              <p className="sub-setting-description">
                Cetvel, fare imlecini otomatik olarak takip eder.
              </p>
            </div>

            {/* Cetvel Rengi */}
            <div className="sub-setting">
              <label htmlFor="ruler-color" className="sub-setting-label">
                <span>Cetvel Rengi</span>
              </label>
              <div className="color-picker-group">
                <input
                  id="ruler-color"
                  type="color"
                  value={settings.readingRuler.color}
                  onChange={(e) => updateSetting('readingRuler', { ...settings.readingRuler, color: e.target.value })}
                  className="color-picker"
                  aria-label="Cetvel rengini seç"
                />
                <span className="color-value">{settings.readingRuler.color}</span>
              </div>
            </div>

            {/* Cetvel Şeffaflığı */}
            <div className="sub-setting">
              <label htmlFor="ruler-opacity" className="sub-setting-label">
                <span>Şeffaflık</span>
                <span className="label-value">{Math.round(settings.readingRuler.opacity * 100)}%</span>
              </label>
              <input
                id="ruler-opacity"
                type="range"
                min="0.1"
                max="0.9"
                step="0.1"
                value={settings.readingRuler.opacity}
                onChange={(e) => updateSetting('readingRuler', { ...settings.readingRuler, opacity: parseFloat(e.target.value) })}
                className="slider"
                aria-valuemin={10}
                aria-valuemax={90}
                aria-valuenow={Math.round(settings.readingRuler.opacity * 100)}
                aria-valuetext={`${Math.round(settings.readingRuler.opacity * 100)} yüzde`}
              />
              <div className="slider-labels">
                <span>%10</span>
                <span>%50</span>
                <span>%90</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Odak Modu - Task 78.2 (REQ-50.32 - REQ-50.35) */}
      <div className="setting-group">
        <div className="setting-header">
          <label htmlFor="focus-mode-toggle" className="setting-label">
            <span className="label-text">Odak Modu</span>
            <span className="label-badge">
              {settings.focusMode.enabled && '✓ Aktif'}
            </span>
          </label>
          <div className="toggle-switch">
            <input
              type="checkbox"
              id="focus-mode-toggle"
              checked={settings.focusMode.enabled}
              onChange={(e) => updateSetting('focusMode', { ...settings.focusMode, enabled: e.target.checked })}
              className="toggle-input"
              aria-describedby="focus-mode-description"
            />
            <label htmlFor="focus-mode-toggle" className="toggle-label" aria-label="Toggle focus mode">
              <span className="toggle-slider" aria-hidden="true"></span>
            </label>
          </div>
        </div>
        <p id="focus-mode-description" className="setting-description">
          Çevredeki metni karartarak mevcut satır/paragrafı vurgular.
        </p>

        {settings.focusMode.enabled && (
          <div className="sub-settings">
            {/* Odak Alanı */}
            <div className="sub-setting">
              <div className="sub-setting-label">
                <span>Odak Alanı</span>
              </div>
              <div id="focus-area-group" className="toggle-group" role="group" aria-label="Odak alanı seçimi">
                <button
                  onClick={() => updateSetting('focusMode', { ...settings.focusMode, focusArea: 'line' })}
                  className={`toggle-button ${settings.focusMode.focusArea === 'line' ? 'active' : ''}`}
                  aria-pressed={settings.focusMode.focusArea === 'line'}
                >
                  Satır
                </button>
                <button
                  onClick={() => updateSetting('focusMode', { ...settings.focusMode, focusArea: 'paragraph' })}
                  className={`toggle-button ${settings.focusMode.focusArea === 'paragraph' ? 'active' : ''}`}
                  aria-pressed={settings.focusMode.focusArea === 'paragraph'}
                >
                  Paragraf
                </button>
                <button
                  onClick={() => updateSetting('focusMode', { ...settings.focusMode, focusArea: 'sentence' })}
                  className={`toggle-button ${settings.focusMode.focusArea === 'sentence' ? 'active' : ''}`}
                  aria-pressed={settings.focusMode.focusArea === 'sentence'}
                >
                  Cümle
                </button>
              </div>
            </div>

            {/* Karartma Yoğunluğu */}
            <div className="sub-setting">
              <label htmlFor="dim-intensity" className="sub-setting-label">
                <span>Karartma Yoğunluğu</span>
                <span className="label-value">{Math.round(settings.focusMode.dimIntensity * 100)}%</span>
              </label>
              <input
                id="dim-intensity"
                type="range"
                min="0.1"
                max="0.9"
                step="0.1"
                value={settings.focusMode.dimIntensity}
                onChange={(e) => updateSetting('focusMode', { ...settings.focusMode, dimIntensity: parseFloat(e.target.value) })}
                className="slider"
                aria-valuemin={10}
                aria-valuemax={90}
                aria-valuenow={Math.round(settings.focusMode.dimIntensity * 100)}
                aria-valuetext={`${Math.round(settings.focusMode.dimIntensity * 100)} yüzde`}
              />
              <div className="slider-labels">
                <span>%10</span>
                <span>%50</span>
                <span>%90</span>
              </div>
            </div>

            {/* Vurgulama Rengi */}
            <div className="sub-setting">
              <label htmlFor="highlight-color" className="sub-setting-label">
                <span>Vurgulama Rengi</span>
              </label>
              <div className="color-picker-group">
                <input
                  id="highlight-color"
                  type="color"
                  value={settings.focusMode.highlightColor}
                  onChange={(e) => updateSetting('focusMode', { ...settings.focusMode, highlightColor: e.target.value })}
                  className="color-picker"
                  aria-label="Vurgulama rengini seç"
                />
                <span className="color-value">{settings.focusMode.highlightColor}</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Kelime Vurgulama - Task 78.3 (REQ-50.36 - REQ-50.39) */}
      <div className="setting-group">
        <div className="setting-header">
          <label htmlFor="word-highlight-toggle" className="setting-label">
            <span className="label-text">Kelime Vurgulama</span>
            <span className="label-badge">
              {settings.wordHighlight.enabled && '✓ Aktif'}
            </span>
          </label>
          <div className="toggle-switch">
            <input
              type="checkbox"
              id="word-highlight-toggle"
              checked={settings.wordHighlight.enabled}
              onChange={(e) => updateSetting('wordHighlight', { ...settings.wordHighlight, enabled: e.target.checked })}
              className="toggle-input"
              aria-describedby="word-highlight-description"
            />
            <label htmlFor="word-highlight-toggle" className="toggle-label" aria-label="Toggle word highlight">
              <span className="toggle-slider" aria-hidden="true"></span>
            </label>
          </div>
        </div>
        <p id="word-highlight-description" className="setting-description">
          Kelimelerin üzerine geldiğinizde veya tıkladığınızda vurgular.
        </p>

        {settings.wordHighlight.enabled && (
          <div className="sub-settings">
            {/* Vurgulama Modu */}
            <div className="sub-setting">
              <div className="sub-setting-label">
                <span>Vurgulama Modu</span>
              </div>
              <div id="highlight-mode-group" className="toggle-group" role="group" aria-label="Vurgulama modu seçimi">
                <button
                  onClick={() => updateSetting('wordHighlight', { ...settings.wordHighlight, mode: 'hover' })}
                  className={`toggle-button ${settings.wordHighlight.mode === 'hover' ? 'active' : ''}`}
                  aria-pressed={settings.wordHighlight.mode === 'hover'}
                >
                  Üzerine Gelme
                </button>
                <button
                  onClick={() => updateSetting('wordHighlight', { ...settings.wordHighlight, mode: 'click' })}
                  className={`toggle-button ${settings.wordHighlight.mode === 'click' ? 'active' : ''}`}
                  aria-pressed={settings.wordHighlight.mode === 'click'}
                >
                  Tıklama
                </button>
                <button
                  onClick={() => updateSetting('wordHighlight', { ...settings.wordHighlight, mode: 'both' })}
                  className={`toggle-button ${settings.wordHighlight.mode === 'both' ? 'active' : ''}`}
                  aria-pressed={settings.wordHighlight.mode === 'both'}
                >
                  Her İkisi
                </button>
              </div>
            </div>

            {/* Çoklu Renk Vurgulama */}
            <div className="sub-setting">
              <label htmlFor="multi-color-checkbox" className="checkbox-label">
                <input
                  id="multi-color-checkbox"
                  type="checkbox"
                  checked={settings.wordHighlight.multiColor}
                  onChange={(e) => updateSetting('wordHighlight', { ...settings.wordHighlight, multiColor: e.target.checked })}
                  className="checkbox-input"
                />
                <span>Çoklu Renk Vurgulama</span>
              </label>
              <p className="sub-setting-description">
                Farklı kelimeleri farklı renklerle vurgulayın.
              </p>
            </div>

            {/* Vurgulama Renkleri */}
            <div className="sub-setting">
              <div className="sub-setting-label">
                <span>Vurgulama Renkleri</span>
              </div>
              <div id="highlight-colors-palette" className="color-palette" role="group" aria-label="Vurgulama renkleri">
                {settings.wordHighlight.colors.map((color, index) => (
                  <div key={index} className="color-palette-item">
                    <input
                      id={`highlight-color-${index}`}
                      type="color"
                      value={color}
                      onChange={(e) => {
                        const newColors = [...settings.wordHighlight.colors];
                        newColors[index] = e.target.value;
                        updateSetting('wordHighlight', { ...settings.wordHighlight, colors: newColors });
                      }}
                      className="color-picker-small"
                      aria-label={`Vurgulama rengi ${index + 1}`}
                    />
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Hece Ayırma - Task 78.4 (REQ-50.40 - REQ-50.42) */}
      <div className="setting-group">
        <div className="setting-header">
          <label htmlFor="syllable-breaks-toggle" className="setting-label">
            <span className="label-text">Hece Ayırma</span>
            <span className="label-badge">
              {settings.syllableBreaks.enabled && '✓ Aktif'}
            </span>
          </label>
          <div className="toggle-switch">
            <input
              type="checkbox"
              id="syllable-breaks-toggle"
              checked={settings.syllableBreaks.enabled}
              onChange={(e) => updateSetting('syllableBreaks', { ...settings.syllableBreaks, enabled: e.target.checked })}
              className="toggle-input"
              aria-describedby="syllable-breaks-description"
            />
            <label htmlFor="syllable-breaks-toggle" className="toggle-label" aria-label="Toggle syllable breaks">
              <span className="toggle-slider" aria-hidden="true"></span>
            </label>
          </div>
        </div>
        <p id="syllable-breaks-description" className="setting-description">
          Kelimeleri hecelerine ayırarak görüntüler (Türkçe hece kurallarına göre).
        </p>

        {settings.syllableBreaks.enabled && (
          <div className="sub-settings">
            {/* Ayırıcı Stil */}
            <div className="sub-setting">
              <div className="sub-setting-label">
                <span>Ayırıcı Stil</span>
              </div>
              <div id="separator-style-group" className="toggle-group" role="group" aria-label="Ayırıcı stil seçimi">
                <button
                  onClick={() => updateSetting('syllableBreaks', { ...settings.syllableBreaks, separator: 'dot' })}
                  className={`toggle-button ${settings.syllableBreaks.separator === 'dot' ? 'active' : ''}`}
                  aria-pressed={settings.syllableBreaks.separator === 'dot'}
                >
                  Nokta (·)
                </button>
                <button
                  onClick={() => updateSetting('syllableBreaks', { ...settings.syllableBreaks, separator: 'dash' })}
                  className={`toggle-button ${settings.syllableBreaks.separator === 'dash' ? 'active' : ''}`}
                  aria-pressed={settings.syllableBreaks.separator === 'dash'}
                >
                  Tire (-)
                </button>
                <button
                  onClick={() => updateSetting('syllableBreaks', { ...settings.syllableBreaks, separator: 'space' })}
                  className={`toggle-button ${settings.syllableBreaks.separator === 'space' ? 'active' : ''}`}
                  aria-pressed={settings.syllableBreaks.separator === 'space'}
                >
                  Boşluk ( )
                </button>
              </div>
            </div>

            {/* Görsel İşaretleyici */}
            <div className="sub-setting">
              <label htmlFor="visual-marker-checkbox" className="checkbox-label">
                <input
                  id="visual-marker-checkbox"
                  type="checkbox"
                  checked={settings.syllableBreaks.visualMarker}
                  onChange={(e) => updateSetting('syllableBreaks', { ...settings.syllableBreaks, visualMarker: e.target.checked })}
                  className="checkbox-input"
                />
                <span>Görsel İşaretleyici</span>
              </label>
              <p className="sub-setting-description">
                Hece sınırlarını renkli çizgilerle işaretle.
              </p>
            </div>

            {/* İşaretleyici Rengi */}
            {settings.syllableBreaks.visualMarker && (
              <div className="sub-setting">
                <label htmlFor="marker-color" className="sub-setting-label">
                  <span>İşaretleyici Rengi</span>
                </label>
                <div className="color-picker-group">
                  <input
                    id="marker-color"
                    type="color"
                    value={settings.syllableBreaks.markerColor}
                    onChange={(e) => updateSetting('syllableBreaks', { ...settings.syllableBreaks, markerColor: e.target.value })}
                    className="color-picker"
                    aria-label="İşaretleyici rengini seç"
                  />
                  <span className="color-value">{settings.syllableBreaks.markerColor}</span>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Önizleme */}
      <div className="preview-section">
        <div className="preview-header">
          <h3>Önizleme</h3>
          <button
            onClick={() => setShowPreview(!showPreview)}
            className="preview-toggle"
            aria-expanded={showPreview}
            aria-controls="reading-helpers-preview"
          >
            {showPreview ? 'Gizle' : 'Göster'}
          </button>
        </div>
        {showPreview && (
          <div
            id="reading-helpers-preview"
            className="preview-content"
            data-reading-ruler={settings.readingRuler.enabled}
            data-focus-mode={settings.focusMode.enabled}
            data-word-highlight={settings.wordHighlight.enabled}
            data-syllable-breaks={settings.syllableBreaks.enabled}
          >
            <p>{previewText}</p>
            <p>
              <strong>Örnek kelimeler:</strong> öğrenci, kişiselleştirilmiş, hazırlanan, platform
            </p>
          </div>
        )}
      </div>

      {/* Sıfırlama Butonu */}
      <div className="settings-footer">
        <button
          onClick={resetSettings}
          className="reset-button"
          aria-label="Tüm okuma yardımcı ayarlarını sıfırla"
        >
          <span aria-hidden="true">↺</span>
          Ayarları Sıfırla
        </button>
      </div>
    </div>
  );
};

export default ReadingHelpers;
