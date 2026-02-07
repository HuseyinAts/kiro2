/**
 * Tipografi Ayarları Bileşeni
 * REQ-50.1 - REQ-50.13: Tipografi ve Görsel Düzenlemeler
 *
 * Task 76: Tipografi ve Görsel Düzenlemeler
 * - 76.1: OpenDyslexic/Dyslexie font entegrasyonu
 * - 76.2: Font boyutu ayarlama (12-24pt)
 * - 76.3: Satır aralığı ayarlama (1.0x-3.0x)
 * - 76.4: Kelime/harf aralığı ayarlama
 */

import * as React from 'react';
import {  useState  } from 'react';

import { useDyslexiaSettings } from '../../hooks/useDyslexiaSettings';

interface TypographySettingsProps {
  className?: string;
}

export const TypographySettings: React.FC<TypographySettingsProps> = ({ className = '' }) => {
  const {
    settings,
    isLoading,
    fontsLoaded,
    updateSetting,
    resetSettings,
    applyPreset,
    increaseFontSize,
    decreaseFontSize,
    increaseLineHeight,
    decreaseLineHeight,
    increaseLetterSpacing,
    decreaseLetterSpacing,
    increaseWordSpacing,
    decreaseWordSpacing,
  } = useDyslexiaSettings();

  const [showPreview, setShowPreview] = useState(true);

  if (isLoading) {
    return (
      <div className={`typography-settings ${className}`}>
        <div className="loading-spinner">Ayarlar yükleniyor...</div>
      </div>
    );
  }

  const previewText = `
    Türkiye Üniversite Sınavları Hazırlık Platformu'na hoş geldiniz! 
    Bu platform, YKS (TYT/AYT/YDT) sınavlarına hazırlanan öğrenciler için 
    AI destekli, kişiselleştirilmiş bir eğitim sistemidir.
  `;

  return (
    <div className={`typography-settings ${className}`}>
      <div className="settings-header">
        <h2>Tipografi Ayarları</h2>
        <p className="settings-description">
          Okuma deneyiminizi kişiselleştirin. Tüm değişiklikler anında uygulanır.
        </p>
      </div>

      {/* Hızlı Preset Seçenekleri */}
      <div className="preset-section">
        <h3>Hızlı Ayarlar</h3>
        <div className="preset-buttons">
          <button
            onClick={() => applyPreset('mild')}
            className="preset-button"
            aria-label="Hafif disleksi desteği uygula"
          >
            <span className="preset-icon">📖</span>
            <span className="preset-label">Hafif</span>
            <span className="preset-description">Temel okuma desteği</span>
          </button>
          <button
            onClick={() => applyPreset('moderate')}
            className="preset-button"
            aria-label="Orta seviye disleksi desteği uygula"
          >
            <span className="preset-icon">📚</span>
            <span className="preset-label">Orta</span>
            <span className="preset-description">Gelişmiş okuma desteği</span>
          </button>
          <button
            onClick={() => applyPreset('severe')}
            className="preset-button"
            aria-label="Yoğun disleksi desteği uygula"
          >
            <span className="preset-icon">🎯</span>
            <span className="preset-label">Yoğun</span>
            <span className="preset-description">Maksimum okuma desteği</span>
          </button>
        </div>
      </div>

      {/* Font Ailesi Seçimi - Task 76.1 */}
      <div className="setting-group">
        <label htmlFor="font-family" className="setting-label">
          <span className="label-text">Font Ailesi</span>
          <span className="label-badge">
            {!fontsLoaded && '⏳ Fontlar yükleniyor...'}
            {fontsLoaded && '✓ Hazır'}
          </span>
        </label>
        <select
          id="font-family"
          value={settings.fontFamily}
          onChange={(e) => updateSetting('fontFamily', e.target.value as any)}
          className="setting-select"
          aria-describedby="font-family-description"
        >
          <option value="default">Varsayılan (System Font)</option>
          <option value="arial">Arial</option>
          <option value="verdana">Verdana</option>
          <option value="opendyslexic">OpenDyslexic (Disleksi Dostu)</option>
          <option value="dyslexie">Dyslexie (Disleksi Dostu)</option>
          <option value="comic-sans">Comic Sans MS</option>
        </select>
        <p id="font-family-description" className="setting-description">
          OpenDyslexic ve Dyslexie fontları disleksi için özel olarak tasarlanmıştır.
        </p>
      </div>

      {/* Font Boyutu - Task 76.2 */}
      <div className="setting-group">
        <label htmlFor="font-size" className="setting-label">
          <span className="label-text">Font Boyutu</span>
          <span className="label-value">{settings.fontSize}pt</span>
        </label>
        <div className="slider-controls">
          <button
            onClick={decreaseFontSize}
            disabled={settings.fontSize <= 12}
            className="slider-button"
            aria-label="Font boyutunu azalt"
          >
            <span aria-hidden="true">−</span>
          </button>
          <input
            id="font-size"
            type="range"
            min="12"
            max="24"
            step="1"
            value={settings.fontSize}
            onChange={(e) => updateSetting('fontSize', parseInt(e.target.value))}
            className="slider"
            aria-valuemin={12}
            aria-valuemax={24}
            aria-valuenow={settings.fontSize}
            aria-valuetext={`${settings.fontSize} punto`}
          />
          <button
            onClick={increaseFontSize}
            disabled={settings.fontSize >= 24}
            className="slider-button"
            aria-label="Font boyutunu artır"
          >
            <span aria-hidden="true">+</span>
          </button>
        </div>
        <div className="slider-labels">
          <span>12pt</span>
          <span>18pt</span>
          <span>24pt</span>
        </div>
        <p className="setting-description">
          Önerilen: 16-18pt arası. Mobil cihazlarda minimum 14pt uygulanır.
        </p>
      </div>

      {/* Satır Aralığı - Task 76.3 */}
      <div className="setting-group">
        <label htmlFor="line-height" className="setting-label">
          <span className="label-text">Satır Aralığı</span>
          <span className="label-value">{settings.lineHeight.toFixed(1)}x</span>
        </label>
        <div className="slider-controls">
          <button
            onClick={decreaseLineHeight}
            disabled={settings.lineHeight <= 1.0}
            className="slider-button"
            aria-label="Satır aralığını azalt"
          >
            <span aria-hidden="true">−</span>
          </button>
          <input
            id="line-height"
            type="range"
            min="1.0"
            max="3.0"
            step="0.1"
            value={settings.lineHeight}
            onChange={(e) => updateSetting('lineHeight', parseFloat(e.target.value))}
            className="slider"
            aria-valuemin={1.0}
            aria-valuemax={3.0}
            aria-valuenow={settings.lineHeight}
            aria-valuetext={`${settings.lineHeight.toFixed(1)} kat`}
          />
          <button
            onClick={increaseLineHeight}
            disabled={settings.lineHeight >= 3.0}
            className="slider-button"
            aria-label="Satır aralığını artır"
          >
            <span aria-hidden="true">+</span>
          </button>
        </div>
        <div className="slider-labels">
          <span>1.0x</span>
          <span>2.0x</span>
          <span>3.0x</span>
        </div>
        <p className="setting-description">
          Önerilen: 1.5-1.8x arası. Daha geniş satır aralığı okumayı kolaylaştırır.
          {settings.lineHeight >= 1.5 && (
            <>
              <br />
              <strong style={{ color: '#27ae60' }}>
                ✓ Optimal okuma genişliği aktif (max 75 karakter)
              </strong>
            </>
          )}
        </p>
        <p className="setting-description" style={{ marginTop: '8px', fontSize: '0.8rem', color: '#666' }}>
          <strong>Otomatik ayar:</strong> Paragraf aralığı {(settings.lineHeight * 1.5).toFixed(2)}em olarak ayarlandı (satır aralığı × 1.5)
        </p>
      </div>

      {/* Harf Aralığı - Task 76.4 */}
      <div className="setting-group">
        <label htmlFor="letter-spacing" className="setting-label">
          <span className="label-text">Harf Aralığı</span>
          <span className="label-value">{settings.letterSpacing.toFixed(2)}em</span>
        </label>
        <div className="slider-controls">
          <button
            onClick={decreaseLetterSpacing}
            disabled={settings.letterSpacing <= 0}
            className="slider-button"
            aria-label="Harf aralığını azalt"
          >
            <span aria-hidden="true">−</span>
          </button>
          <input
            id="letter-spacing"
            type="range"
            min="0"
            max="0.5"
            step="0.05"
            value={settings.letterSpacing}
            onChange={(e) => updateSetting('letterSpacing', parseFloat(e.target.value))}
            className="slider"
            aria-valuemin={0}
            aria-valuemax={0.5}
            aria-valuenow={settings.letterSpacing}
            aria-valuetext={`${settings.letterSpacing.toFixed(2)} em`}
          />
          <button
            onClick={increaseLetterSpacing}
            disabled={settings.letterSpacing >= 0.5}
            className="slider-button"
            aria-label="Harf aralığını artır"
          >
            <span aria-hidden="true">+</span>
          </button>
        </div>
        <div className="slider-labels">
          <span>0em</span>
          <span>0.25em</span>
          <span>0.5em</span>
        </div>
        <p className="setting-description">
          Harfler arası boşluk. Disleksi için 0.1-0.15em önerilir.
        </p>
      </div>

      {/* Kelime Aralığı - Task 76.4 */}
      <div className="setting-group">
        <label htmlFor="word-spacing" className="setting-label">
          <span className="label-text">Kelime Aralığı</span>
          <span className="label-value">{settings.wordSpacing.toFixed(2)}em</span>
        </label>
        <div className="slider-controls">
          <button
            onClick={decreaseWordSpacing}
            disabled={settings.wordSpacing <= 0}
            className="slider-button"
            aria-label="Kelime aralığını azalt"
          >
            <span aria-hidden="true">−</span>
          </button>
          <input
            id="word-spacing"
            type="range"
            min="0"
            max="0.5"
            step="0.05"
            value={settings.wordSpacing}
            onChange={(e) => updateSetting('wordSpacing', parseFloat(e.target.value))}
            className="slider"
            aria-valuemin={0}
            aria-valuemax={0.5}
            aria-valuenow={settings.wordSpacing}
            aria-valuetext={`${settings.wordSpacing.toFixed(2)} em`}
          />
          <button
            onClick={increaseWordSpacing}
            disabled={settings.wordSpacing >= 0.5}
            className="slider-button"
            aria-label="Kelime aralığını artır"
          >
            <span aria-hidden="true">+</span>
          </button>
        </div>
        <div className="slider-labels">
          <span>0em</span>
          <span>0.25em</span>
          <span>0.5em</span>
        </div>
        <p className="setting-description">
          Kelimeler arası boşluk. Disleksi için 0.1-0.15em önerilir.
        </p>
      </div>

      {/* Paragraf Aralığı */}
      <div className="setting-group">
        <label htmlFor="paragraph-spacing" className="setting-label">
          <span className="label-text">Paragraf Aralığı</span>
          <span className="label-value">{settings.paragraphSpacing.toFixed(1)}em</span>
        </label>
        <input
          id="paragraph-spacing"
          type="range"
          min="0"
          max="3"
          step="0.5"
          value={settings.paragraphSpacing}
          onChange={(e) => updateSetting('paragraphSpacing', parseFloat(e.target.value))}
          className="slider"
          aria-valuemin={0}
          aria-valuemax={3}
          aria-valuenow={settings.paragraphSpacing}
          aria-valuetext={`${settings.paragraphSpacing.toFixed(1)} em`}
        />
        <div className="slider-labels">
          <span>0em</span>
          <span>1.5em</span>
          <span>3em</span>
        </div>
      </div>

      {/* Font Kalınlığı */}
      <div className="setting-group">
        <label htmlFor="font-weight" className="setting-label">
          <span className="label-text">Font Kalınlığı</span>
        </label>
        <div className="toggle-group">
          <button
            onClick={() => updateSetting('fontWeight', 'normal')}
            className={`toggle-button ${settings.fontWeight === 'normal' ? 'active' : ''}`}
            aria-pressed={settings.fontWeight === 'normal'}
          >
            Normal
          </button>
          <button
            onClick={() => updateSetting('fontWeight', 'bold')}
            className={`toggle-button ${settings.fontWeight === 'bold' ? 'active' : ''}`}
            aria-pressed={settings.fontWeight === 'bold'}
          >
            Kalın
          </button>
        </div>
      </div>

      {/* Önizleme */}
      <div className="preview-section">
        <div className="preview-header">
          <h3>Önizleme</h3>
          <button
            onClick={() => setShowPreview(!showPreview)}
            className="preview-toggle"
            aria-expanded={showPreview}
            aria-controls="typography-preview"
          >
            {showPreview ? 'Gizle' : 'Göster'}
          </button>
        </div>
        {showPreview && (
          <div
            id="typography-preview"
            className="preview-content"
            style={{
              fontFamily: 'var(--font-family)',
              fontSize: `${settings.fontSize}px`,
              fontWeight: settings.fontWeight,
              lineHeight: settings.lineHeight,
              letterSpacing: `${settings.letterSpacing}em`,
              wordSpacing: `${settings.wordSpacing}em`,
            }}
          >
            <p style={{ marginBottom: `${settings.paragraphSpacing}em` }}>
              {previewText}
            </p>
            <p style={{ marginBottom: `${settings.paragraphSpacing}em` }}>
              <strong>Kalın metin örneği:</strong> Bu metin kalın yazılmıştır.
            </p>
            <p>
              <em>İtalik metin örneği:</em> Bu metin italik yazılmıştır.
            </p>
          </div>
        )}
      </div>

      {/* Sıfırlama Butonu */}
      <div className="settings-footer">
        <button
          onClick={resetSettings}
          className="reset-button"
          aria-label="Tüm tipografi ayarlarını sıfırla"
        >
          <span aria-hidden="true">↺</span>
          Ayarları Sıfırla
        </button>
      </div>
    </div>
  );
};

export default TypographySettings;
