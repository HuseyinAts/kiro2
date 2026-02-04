/**
 * Task 96: Sensory Load Reduction - Duyusal Yük Azaltma
 * OSB desteği için duyusal yük kontrol paneli
 *
 * Combines all Task 96 sub-tasks:
 * - 96.1: Minimal Animation (Reduce motion)
 * - 96.2: Silent Mode (Mute all sounds)
 * - 96.3: Plain Backgrounds (Solid colors, no patterns)
 * - 96.4: Clean Design (Minimal clutter, white space)
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import './SensoryControl.css';

export interface SensorySettings {
  // Task 96.1: Minimal Animation
  reduceMotion: boolean;
  disableAnimations: boolean;
  subtleTransitions: boolean;

  // Task 96.2: Silent Mode
  muteAllSounds: boolean;
  noBackgroundMusic: boolean;
  noNotificationSounds: boolean;

  // Task 96.3: Plain Backgrounds
  plainBackgrounds: boolean;
  noPatterns: boolean;
  solidColors: boolean;

  // Task 96.4: Clean Design
  minimalClutter: boolean;
  extraWhitespace: boolean;
  clearHierarchy: boolean;
  largeSpacing: boolean;
}

const DEFAULT_SENSORY_SETTINGS: SensorySettings = {
  reduceMotion: true,
  disableAnimations: false,
  subtleTransitions: true,
  muteAllSounds: false,
  noBackgroundMusic: true,
  noNotificationSounds: false,
  plainBackgrounds: true,
  noPatterns: true,
  solidColors: true,
  minimalClutter: true,
  extraWhitespace: true,
  clearHierarchy: true,
  largeSpacing: false
};

interface SensoryContextValue {
  settings: SensorySettings;
  updateSettings: (updates: Partial<SensorySettings>) => void;
  resetSettings: () => void;
  applyPreset: (preset: 'minimal' | 'comfortable' | 'standard') => void;
}

const SensoryContext = createContext<SensoryContextValue>({
  settings: DEFAULT_SENSORY_SETTINGS,
  updateSettings: () => {},
  resetSettings: () => {},
  applyPreset: () => {}
});

export const useSensorySettings = () => useContext(SensoryContext);

interface SensoryProviderProps {
  children: ReactNode;
  initialSettings?: Partial<SensorySettings>;
}

export const SensoryProvider: React.FC<SensoryProviderProps> = ({
  children,
  initialSettings = {}
}) => {
  const [settings, setSettings] = useState<SensorySettings>({
    ...DEFAULT_SENSORY_SETTINGS,
    ...initialSettings
  });

  useEffect(() => {
    // Apply CSS classes based on settings
    const root = document.documentElement;

    // Task 96.1: Animation control
    root.classList.toggle('reduce-motion', settings.reduceMotion);
    root.classList.toggle('no-animations', settings.disableAnimations);
    root.classList.toggle('subtle-transitions', settings.subtleTransitions);

    // Task 96.2: Sound control
    root.classList.toggle('mute-all', settings.muteAllSounds);

    // Task 96.3: Background control
    root.classList.toggle('plain-backgrounds', settings.plainBackgrounds);
    root.classList.toggle('no-patterns', settings.noPatterns);
    root.classList.toggle('solid-colors', settings.solidColors);

    // Task 96.4: Design control
    root.classList.toggle('minimal-clutter', settings.minimalClutter);
    root.classList.toggle('extra-whitespace', settings.extraWhitespace);
    root.classList.toggle('clear-hierarchy', settings.clearHierarchy);
    root.classList.toggle('large-spacing', settings.largeSpacing);
  }, [settings]);

  const updateSettings = (updates: Partial<SensorySettings>) => {
    setSettings(prev => ({ ...prev, ...updates }));
  };

  const resetSettings = () => {
    setSettings(DEFAULT_SENSORY_SETTINGS);
  };

  const applyPreset = (preset: 'minimal' | 'comfortable' | 'standard') => {
    const presets: Record<string, SensorySettings> = {
      minimal: {
        reduceMotion: true,
        disableAnimations: true,
        subtleTransitions: false,
        muteAllSounds: true,
        noBackgroundMusic: true,
        noNotificationSounds: true,
        plainBackgrounds: true,
        noPatterns: true,
        solidColors: true,
        minimalClutter: true,
        extraWhitespace: true,
        clearHierarchy: true,
        largeSpacing: true
      },
      comfortable: DEFAULT_SENSORY_SETTINGS,
      standard: {
        reduceMotion: false,
        disableAnimations: false,
        subtleTransitions: false,
        muteAllSounds: false,
        noBackgroundMusic: false,
        noNotificationSounds: false,
        plainBackgrounds: false,
        noPatterns: false,
        solidColors: false,
        minimalClutter: false,
        extraWhitespace: false,
        clearHierarchy: false,
        largeSpacing: false
      }
    };
    setSettings(presets[preset]);
  };

  return (
    <SensoryContext.Provider value={{ settings, updateSettings, resetSettings, applyPreset }}>
      {children}
    </SensoryContext.Provider>
  );
};

interface SensoryControlPanelProps {
  onClose?: () => void;
  showPresets?: boolean;
}

export const SensoryControlPanel: React.FC<SensoryControlPanelProps> = ({
  onClose,
  showPresets = true
}) => {
  const { settings, updateSettings, resetSettings, applyPreset } = useSensorySettings();

  return (
    <div className="sensory-control-panel">
      <div className="panel-header">
        <h2 className="panel-title">🎛️ Duyusal Ayarlar</h2>
        {onClose && (
          <button onClick={onClose} className="close-button" aria-label="Kapat">
            ✕
          </button>
        )}
      </div>

      {showPresets && (
        <div className="presets-section">
          <h3 className="section-title">Hızlı Ayarlar</h3>
          <div className="preset-buttons">
            <button onClick={() => applyPreset('minimal')} className="preset-btn preset-minimal">
              🔇 Minimal (En Az Uyarıcı)
            </button>
            <button onClick={() => applyPreset('comfortable')} className="preset-btn preset-comfortable">
              😌 Rahat (Önerilen)
            </button>
            <button onClick={() => applyPreset('standard')} className="preset-btn preset-standard">
              🎨 Standart (Normal)
            </button>
          </div>
        </div>
      )}

      {/* Task 96.1: Animation Settings */}
      <div className="settings-section">
        <h3 className="section-title">📐 Animasyon Ayarları</h3>
        <label className="setting-item">
          <input
            type="checkbox"
            checked={settings.reduceMotion}
            onChange={(e) => updateSettings({ reduceMotion: e.target.checked })}
          />
          <span className="setting-label">Hareketi Azalt</span>
          <span className="setting-description">Animasyonları yavaşlatır</span>
        </label>
        <label className="setting-item">
          <input
            type="checkbox"
            checked={settings.disableAnimations}
            onChange={(e) => updateSettings({ disableAnimations: e.target.checked })}
          />
          <span className="setting-label">Animasyonları Kapat</span>
          <span className="setting-description">Tüm animasyonları devre dışı bırakır</span>
        </label>
        <label className="setting-item">
          <input
            type="checkbox"
            checked={settings.subtleTransitions}
            onChange={(e) => updateSettings({ subtleTransitions: e.target.checked })}
          />
          <span className="setting-label">İnce Geçişler</span>
          <span className="setting-description">Hafif geçiş efektleri kullanır</span>
        </label>
      </div>

      {/* Task 96.2: Sound Settings */}
      <div className="settings-section">
        <h3 className="section-title">🔇 Ses Ayarları</h3>
        <label className="setting-item">
          <input
            type="checkbox"
            checked={settings.muteAllSounds}
            onChange={(e) => updateSettings({ muteAllSounds: e.target.checked })}
          />
          <span className="setting-label">Tüm Sesleri Kapat</span>
          <span className="setting-description">Hiç ses çıkmaz</span>
        </label>
        <label className="setting-item">
          <input
            type="checkbox"
            checked={settings.noBackgroundMusic}
            onChange={(e) => updateSettings({ noBackgroundMusic: e.target.checked })}
          />
          <span className="setting-label">Arka Plan Müziği Yok</span>
          <span className="setting-description">Sessiz çalışma ortamı</span>
        </label>
        <label className="setting-item">
          <input
            type="checkbox"
            checked={settings.noNotificationSounds}
            onChange={(e) => updateSettings({ noNotificationSounds: e.target.checked })}
          />
          <span className="setting-label">Bildirim Sesi Yok</span>
          <span className="setting-description">Sessiz bildirimler</span>
        </label>
      </div>

      {/* Task 96.3: Background Settings */}
      <div className="settings-section">
        <h3 className="section-title">🎨 Arka Plan Ayarları</h3>
        <label className="setting-item">
          <input
            type="checkbox"
            checked={settings.plainBackgrounds}
            onChange={(e) => updateSettings({ plainBackgrounds: e.target.checked })}
          />
          <span className="setting-label">Sade Arka Planlar</span>
          <span className="setting-description">Karmaşık arka plan yok</span>
        </label>
        <label className="setting-item">
          <input
            type="checkbox"
            checked={settings.noPatterns}
            onChange={(e) => updateSettings({ noPatterns: e.target.checked })}
          />
          <span className="setting-label">Desen Yok</span>
          <span className="setting-description">Dikkat dağıtıcı desen yok</span>
        </label>
        <label className="setting-item">
          <input
            type="checkbox"
            checked={settings.solidColors}
            onChange={(e) => updateSettings({ solidColors: e.target.checked })}
          />
          <span className="setting-label">Düz Renkler</span>
          <span className="setting-description">Gradient yok, düz renkler</span>
        </label>
      </div>

      {/* Task 96.4: Design Settings */}
      <div className="settings-section">
        <h3 className="section-title">✨ Tasarım Ayarları</h3>
        <label className="setting-item">
          <input
            type="checkbox"
            checked={settings.minimalClutter}
            onChange={(e) => updateSettings({ minimalClutter: e.target.checked })}
          />
          <span className="setting-label">Minimum Karmaşıklık</span>
          <span className="setting-description">Gereksiz elementler gizlenir</span>
        </label>
        <label className="setting-item">
          <input
            type="checkbox"
            checked={settings.extraWhitespace}
            onChange={(e) => updateSettings({ extraWhitespace: e.target.checked })}
          />
          <span className="setting-label">Ekstra Boşluk</span>
          <span className="setting-description">Daha fazla beyaz alan</span>
        </label>
        <label className="setting-item">
          <input
            type="checkbox"
            checked={settings.clearHierarchy}
            onChange={(e) => updateSettings({ clearHierarchy: e.target.checked })}
          />
          <span className="setting-label">Net Hiyerarşi</span>
          <span className="setting-description">Belirgin başlıklar ve bölümler</span>
        </label>
        <label className="setting-item">
          <input
            type="checkbox"
            checked={settings.largeSpacing}
            onChange={(e) => updateSettings({ largeSpacing: e.target.checked })}
          />
          <span className="setting-label">Geniş Aralıklar</span>
          <span className="setting-description">Elementler arası daha fazla boşluk</span>
        </label>
      </div>

      <div className="panel-footer">
        <button onClick={resetSettings} className="reset-button">
          🔄 Varsayılana Dön
        </button>
      </div>
    </div>
  );
};

export default SensoryProvider;
