/**
 * Renk ve Kontrast Ayarları Bileşeni
 * REQ-50.14 - REQ-50.27: Renk ve Kontrast Ayarları
 * 
 * Task 77: Renk ve Kontrast Ayarları
 * - 77.1: Renkli overlay (6 renk: mavi, yeşil, sarı, pembe, mor, gri)
 * - 77.2: Opacity ayarlama (%10-%90)
 * - 77.3: Yüksek kontrast modları
 * - 77.4: WCAG AAA uyumu (7:1 kontrast oranı)
 */

import React, { useState } from 'react';
import { useColorContrastSettings } from '../../hooks/useColorContrastSettings';
import './ColorContrastSettings.css';

interface ColorContrastSettingsProps {
  className?: string;
}

export const ColorContrastSettings: React.FC<ColorContrastSettingsProps> = ({ className = '' }) => {
  const {
    settings,
    isLoading,
    updateSetting,
    resetSettings,
    applyPreset,
    increaseOpacity,
    decreaseOpacity,
    calculateContrastRatio,
    isWCAGAAACompliant,
  } = useColorContrastSettings();

  const [showPreview, setShowPreview] = useState(true);

  if (isLoading) {
    return (
      <div className={`color-contrast-settings ${className}`}>
        <div className="loading-spinner">Ayarlar yükleniyor...</div>
      </div>
    );
  }

  // Renk seçenekleri - REQ-50.14
  const colorOptions = [
    { value: 'none', label: 'Yok', color: 'transparent', description: 'Overlay kapalı' },
    { value: 'blue', label: 'Mavi', color: 'rgb(173, 216, 230)', description: 'Sakinleştirici mavi ton' },
    { value: 'green', label: 'Yeşil', color: 'rgb(144, 238, 144)', description: 'Göz dostu yeşil' },
    { value: 'yellow', label: 'Sarı', color: 'rgb(255, 255, 224)', description: 'Sıcak sarı ton' },
    { value: 'pink', label: 'Pembe', color: 'rgb(255, 192, 203)', description: 'Yumuşak pembe' },
    { value: 'purple', label: 'Mor', color: 'rgb(221, 160, 221)', description: 'Rahatlatıcı mor' },
    { value: 'gray', label: 'Gri', color: 'rgb(211, 211, 211)', description: 'Nötr gri ton' },
  ];

  // Kontrast modu seçenekleri - REQ-50.21
  const contrastModes = [
    { value: 'normal', label: 'Normal', description: 'Standart kontrast' },
    { value: 'high', label: 'Yüksek Kontrast', description: 'Gelişmiş okunabilirlik' },
    { value: 'dark', label: 'Karanlık Mod', description: 'Göz yorgunluğunu azaltır' },
    { value: 'custom', label: 'Özel', description: 'Manuel kontrast ayarı' },
  ];

  const previewText = `
    Türkiye Üniversite Sınavları Hazırlık Platformu'na hoş geldiniz! 
    Bu platform, YKS (TYT/AYT/YDT) sınavlarına hazırlanan öğrenciler için 
    AI destekli, kişiselleştirilmiş bir eğitim sistemidir.
  `;

  // Kontrast oranını hesapla - REQ-50.26
  const contrastRatio = calculateContrastRatio();
  const isAAA = isWCAGAAACompliant();

  return (
    <div className={`color-contrast-settings ${className}`}>
      <div className="settings-header">
        <h2>Renk ve Kontrast Ayarları</h2>
        <p className="settings-description">
          Görsel konforunuzu artırmak için renk overlay ve kontrast ayarlarını özelleştirin.
        </p>
      </div>

      {/* Hızlı Preset Seçenekleri */}
      <div className="preset-section">
        <h3>Hızlı Ayarlar</h3>
        <div className="preset-buttons">
          <button
            onClick={() => applyPreset('reading')}
            className="preset-button"
            aria-label="Okuma modu uygula"
          >
            <span className="preset-icon">📖</span>
            <span className="preset-label">Okuma</span>
            <span className="preset-description">Uzun süreli okuma için</span>
          </button>
          <button
            onClick={() => applyPreset('exam')}
            className="preset-button"
            aria-label="Sınav modu uygula"
          >
            <span className="preset-icon">✏️</span>
            <span className="preset-label">Sınav</span>
            <span className="preset-description">Sınav odağı için</span>
          </button>
          <button
            onClick={() => applyPreset('night')}
            className="preset-button"
            aria-label="Gece modu uygula"
          >
            <span className="preset-icon">🌙</span>
            <span className="preset-label">Gece</span>
            <span className="preset-description">Gece çalışması için</span>
          </button>
        </div>
      </div>

      {/* Renkli Overlay - Task 77.1 (REQ-50.14, REQ-50.15) */}
      <div className="setting-group">
        <label className="setting-label">
          <span className="label-text">Renkli Overlay</span>
          <span className="label-badge">
            {settings.colorOverlay !== 'none' && '✓ Aktif'}
          </span>
        </label>
        <p className="setting-description">
          Ekran üzerine renkli bir filtre uygulayarak okuma konforunu artırın.
        </p>
        <div className="color-grid">
          {colorOptions.map((option) => (
            <button
              key={option.value}
              onClick={() => updateSetting('colorOverlay', option.value as any)}
              className={`color-option ${settings.colorOverlay === option.value ? 'active' : ''}`}
              aria-label={`${option.label} overlay seç`}
              aria-pressed={settings.colorOverlay === option.value}
              title={option.description}
            >
              <div
                className="color-swatch"
                style={{
                  backgroundColor: option.color,
                  border: option.value === 'none' ? '2px dashed #ccc' : 'none',
                }}
              >
                {option.value === 'none' && <span style={{ fontSize: '24px' }}>∅</span>}
              </div>
              <span className="color-label">{option.label}</span>
              {settings.colorOverlay === option.value && (
                <span className="check-icon" aria-hidden="true">✓</span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Opacity Ayarlama - Task 77.2 (REQ-50.16, REQ-50.18, REQ-50.19, REQ-50.20) */}
      {settings.colorOverlay !== 'none' && (
        <div className="setting-group">
          <label htmlFor="overlay-opacity" className="setting-label">
            <span className="label-text">Overlay Şeffaflığı</span>
            <span className="label-value">{Math.round(settings.overlayOpacity * 100)}%</span>
          </label>
          <div className="slider-controls">
            <button
              onClick={decreaseOpacity}
              disabled={settings.overlayOpacity <= 0.1}
              className="slider-button"
              aria-label="Şeffaflığı azalt"
            >
              <span aria-hidden="true">−</span>
            </button>
            <input
              id="overlay-opacity"
              type="range"
              min="0.1"
              max="0.9"
              step="0.1"
              value={settings.overlayOpacity}
              onChange={(e) => updateSetting('overlayOpacity', parseFloat(e.target.value))}
              className="slider"
              aria-valuemin={10}
              aria-valuemax={90}
              aria-valuenow={Math.round(settings.overlayOpacity * 100)}
              aria-valuetext={`${Math.round(settings.overlayOpacity * 100)} yüzde`}
            />
            <button
              onClick={increaseOpacity}
              disabled={settings.overlayOpacity >= 0.9}
              className="slider-button"
              aria-label="Şeffaflığı artır"
            >
              <span aria-hidden="true">+</span>
            </button>
          </div>
          <div className="slider-labels">
            <span>%10</span>
            <span>%50</span>
            <span>%90</span>
          </div>
          <p className="setting-description">
            Overlay'in yoğunluğunu ayarlayın. Düşük değerler daha hafif, yüksek değerler daha belirgin filtre sağlar.
            {settings.overlayOpacity > 0.7 && (
              <>
                <br />
                <strong style={{ color: '#e67e22' }}>
                  ⚠️ Yüksek opacity metin okunabilirliğini etkileyebilir
                </strong>
              </>
            )}
          </p>
        </div>
      )}

      {/* Kontrast Modu - Task 77.3 (REQ-50.21, REQ-50.22, REQ-50.23, REQ-50.24) */}
      <div className="setting-group">
        <label className="setting-label">
          <span className="label-text">Kontrast Modu</span>
        </label>
        <div className="contrast-modes">
          {contrastModes.map((mode) => (
            <button
              key={mode.value}
              onClick={() => updateSetting('contrastMode', mode.value as any)}
              className={`contrast-mode-button ${settings.contrastMode === mode.value ? 'active' : ''}`}
              aria-label={`${mode.label} modunu seç`}
              aria-pressed={settings.contrastMode === mode.value}
            >
              <span className="mode-label">{mode.label}</span>
              <span className="mode-description">{mode.description}</span>
              {settings.contrastMode === mode.value && (
                <span className="check-icon" aria-hidden="true">✓</span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Özel Kontrast Oranı - Task 77.3 (REQ-50.23) */}
      {settings.contrastMode === 'custom' && (
        <div className="setting-group">
          <label htmlFor="contrast-ratio" className="setting-label">
            <span className="label-text">Kontrast Oranı</span>
            <span className="label-value">{settings.customContrastRatio.toFixed(1)}:1</span>
          </label>
          <input
            id="contrast-ratio"
            type="range"
            min="1"
            max="21"
            step="0.5"
            value={settings.customContrastRatio}
            onChange={(e) => updateSetting('customContrastRatio', parseFloat(e.target.value))}
            className="slider"
            aria-valuemin={1}
            aria-valuemax={21}
            aria-valuenow={settings.customContrastRatio}
            aria-valuetext={`${settings.customContrastRatio.toFixed(1)} bire bir`}
          />
          <div className="slider-labels">
            <span>1:1</span>
            <span>7:1 (AAA)</span>
            <span>21:1</span>
          </div>
        </div>
      )}

      {/* WCAG AAA Uyumluluk - Task 77.4 (REQ-50.25, REQ-50.26, REQ-50.27) */}
      <div className="setting-group">
        <div className="wcag-compliance">
          <h3>WCAG Uyumluluk Durumu</h3>
          <div className="compliance-status">
            <div className={`status-badge ${isAAA ? 'compliant' : 'non-compliant'}`}>
              <span className="status-icon">{isAAA ? '✓' : '⚠️'}</span>
              <span className="status-text">
                {isAAA ? 'WCAG AAA Uyumlu' : 'WCAG AAA Uyumsuz'}
              </span>
            </div>
            <div className="contrast-info">
              <p>
                <strong>Mevcut Kontrast Oranı:</strong> {contrastRatio.toFixed(2)}:1
              </p>
              <p>
                <strong>WCAG AAA Minimum:</strong> 7:1
              </p>
              {!isAAA && (
                <p className="warning-text">
                  ⚠️ Kontrast oranı WCAG AAA standardını karşılamıyor. 
                  Daha iyi okunabilirlik için kontrast ayarlarını artırın.
                </p>
              )}
            </div>
          </div>
          
          {/* Otomatik Düzeltme Önerisi - REQ-50.27 */}
          {!isAAA && (
            <div className="auto-fix-section">
              <p className="auto-fix-description">
                Kontrast oranını otomatik olarak WCAG AAA standardına uygun hale getirebiliriz.
              </p>
              <button
                onClick={() => updateSetting('customContrastRatio', 7.0)}
                className="auto-fix-button"
                aria-label="Kontrast oranını otomatik düzelt"
              >
                <span aria-hidden="true">🔧</span>
                Otomatik Düzelt (7:1)
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Metin Rengi Ayarı */}
      <div className="setting-group">
        <label htmlFor="text-color" className="setting-label">
          <span className="label-text">Metin Rengi</span>
        </label>
        <div className="color-picker-group">
          <input
            id="text-color"
            type="color"
            value={settings.textColor}
            onChange={(e) => updateSetting('textColor', e.target.value)}
            className="color-picker"
            aria-label="Metin rengini seç"
          />
          <span className="color-value">{settings.textColor}</span>
        </div>
      </div>

      {/* Arka Plan Rengi Ayarı */}
      <div className="setting-group">
        <label htmlFor="background-color" className="setting-label">
          <span className="label-text">Arka Plan Rengi</span>
        </label>
        <div className="color-picker-group">
          <input
            id="background-color"
            type="color"
            value={settings.backgroundColor}
            onChange={(e) => updateSetting('backgroundColor', e.target.value)}
            className="color-picker"
            aria-label="Arka plan rengini seç"
          />
          <span className="color-value">{settings.backgroundColor}</span>
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
            aria-controls="color-contrast-preview"
          >
            {showPreview ? 'Gizle' : 'Göster'}
          </button>
        </div>
        {showPreview && (
          <div
            id="color-contrast-preview"
            className="preview-content"
            style={{
              color: settings.textColor,
              backgroundColor: settings.backgroundColor,
              position: 'relative',
            }}
          >
            {/* Overlay preview */}
            {settings.colorOverlay !== 'none' && (
              <div
                className="preview-overlay"
                style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  right: 0,
                  bottom: 0,
                  backgroundColor: colorOptions.find(c => c.value === settings.colorOverlay)?.color,
                  opacity: settings.overlayOpacity,
                  pointerEvents: 'none',
                }}
              />
            )}
            <div style={{ position: 'relative', zIndex: 1, padding: '20px' }}>
              <p>{previewText}</p>
              <p>
                <strong>Kalın metin örneği:</strong> Bu metin kalın yazılmıştır.
              </p>
              <p>
                <em>İtalik metin örneği:</em> Bu metin italik yazılmıştır.
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Sıfırlama Butonu */}
      <div className="settings-footer">
        <button
          onClick={resetSettings}
          className="reset-button"
          aria-label="Tüm renk ve kontrast ayarlarını sıfırla"
        >
          <span aria-hidden="true">↺</span>
          Ayarları Sıfırla
        </button>
      </div>
    </div>
  );
};

export default ColorContrastSettings;
