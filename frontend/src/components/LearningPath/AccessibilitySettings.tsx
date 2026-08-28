/**
 * AccessibilitySettings — Erişilebilirlik ayarları paneli
 *
 * Font boyutu, animasyon, yüksek kontrast toggle'ları.
 * Ayarlar localStorage'da persist edilir ve document.body'e CSS class eklenir.
 *
 * WCAG 2.2 + DevQube nörodiversite 7 prensibi
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import {
  Box,
  Typography,
  Slider,
  Switch,
  IconButton,
  Popover,
} from '@mui/material';
import { Settings, TextFields, Animation, Contrast } from '@mui/icons-material';
import { osbService } from '../../services/osbService';

const STORAGE_KEY = 'kiro2_accessibility';

interface A11ySettings {
  fontSize: 'small' | 'medium' | 'large' | 'extra-large';
  reducedMotion: boolean;
  highContrast: boolean;
}

const DEFAULTS: A11ySettings = {
  fontSize: 'medium',
  reducedMotion: false,
  highContrast: false,
};

const FONT_SIZES = ['small', 'medium', 'large', 'extra-large'] as const;
const FONT_LABELS: Record<string, string> = {
  small: '14px',
  medium: '16px',
  large: '18px',
  'extra-large': '20px',
};

function loadSettings(): A11ySettings {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {return { ...DEFAULTS, ...JSON.parse(raw) };}
  } catch { /* ignore */ }
  return DEFAULTS;
}

function applyToDOM(settings: A11ySettings) {
  const body = document.body;

  // Font size classes
  FONT_SIZES.forEach(s => body.classList.remove(`font-${s}`));
  body.classList.add(`font-${settings.fontSize}`);

  // Reduced motion
  body.classList.toggle('reduced-motion', settings.reducedMotion);

  // High contrast
  body.classList.toggle('high-contrast', settings.highContrast);
}

// #415-D: Bu panelin OSB-eşleşen toggle'larını backend'e yaz. Dokunulmamış 14
// OSB alanını korumak için fetch-merge-put yapılır. Fire-and-forget; çevrimdışı
// için hata yutulur (localStorage yerel kopyayı zaten saklıyor).
async function syncOSBToBackend(settings: A11ySettings): Promise<void> {
  try {
    const current = await osbService.getSettings();
    await osbService.updateSettings({
      ...current,
      reducedMotion: settings.reducedMotion,
      highContrastMode: settings.highContrast,
    });
  } catch {
    /* offline: localStorage cache stands */
  }
}

export function AccessibilitySettings() {
  const [settings, setSettings] = useState<A11ySettings>(loadSettings);
  const [anchorEl, setAnchorEl] = useState<HTMLButtonElement | null>(null);
  // #415-D: mount çalıştırmasında backend'e yazmamak için (yükleme sırasında
  // sunucu durumunu ezmeyi önler) — yalnız kullanıcı değişikliklerinde push.
  const didMountRef = useRef(false);

  // Apply on mount and when settings change
  useEffect(() => {
    applyToDOM(settings);
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
    } catch { /* ignore */ }

    // #415-D: kullanıcı değişikliklerini backend OSB ayarlarına yaz (mount hariç).
    if (didMountRef.current) {
      void syncOSBToBackend(settings);
    } else {
      didMountRef.current = true;
    }
  }, [settings]);

  // Apply on initial mount (for page reloads)
  useEffect(() => {
    applyToDOM(loadSettings());
  }, []);

  const update = useCallback((partial: Partial<A11ySettings>) => {
    setSettings(prev => ({ ...prev, ...partial }));
  }, []);

  const fontIndex = FONT_SIZES.indexOf(settings.fontSize);

  return (
    <>
      <IconButton
        onClick={(e) => setAnchorEl(e.currentTarget)}
        size="small"
        aria-label="Erişilebilirlik ayarları"
        sx={{
          color: 'text.secondary',
          '&:hover': { color: 'primary.main' },
        }}
      >
        <Settings sx={{ fontSize: 20 }} />
      </IconButton>

      <Popover
        open={Boolean(anchorEl)}
        anchorEl={anchorEl}
        onClose={() => setAnchorEl(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
        transformOrigin={{ vertical: 'top', horizontal: 'right' }}
        slotProps={{
          paper: {
            sx: { p: 2.5, width: 280, borderRadius: 3 },
          },
        }}
      >
        <Typography variant="subtitle2" fontWeight={700} sx={{ mb: 2 }}>
          Erişilebilirlik
        </Typography>

        {/* Font Size */}
        <Box sx={{ mb: 2.5 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 1 }}>
            <TextFields sx={{ fontSize: 18, color: 'text.secondary' }} />
            <Typography variant="caption" fontWeight={600}>
              Yazı Boyutu: {FONT_LABELS[settings.fontSize]}
            </Typography>
          </Box>
          <Slider
            value={fontIndex}
            min={0}
            max={3}
            step={1}
            marks={FONT_SIZES.map((s, i) => ({ value: i, label: FONT_LABELS[s] }))}
            onChange={(_, v) => update({ fontSize: FONT_SIZES[v as number] })}
            sx={{ mx: 1 }}
            aria-label="Yazı boyutu"
          />
        </Box>

        {/* Reduced Motion */}
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1.5 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <Animation sx={{ fontSize: 18, color: 'text.secondary' }} />
            <Typography variant="caption" fontWeight={600}>
              Animasyonları Azalt
            </Typography>
          </Box>
          <Switch
            size="small"
            checked={settings.reducedMotion}
            onChange={(_, v) => update({ reducedMotion: v })}
            aria-label="Animasyonları azalt"
          />
        </Box>

        {/* High Contrast */}
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <Contrast sx={{ fontSize: 18, color: 'text.secondary' }} />
            <Typography variant="caption" fontWeight={600}>
              Yüksek Kontrast
            </Typography>
          </Box>
          <Switch
            size="small"
            checked={settings.highContrast}
            onChange={(_, v) => update({ highContrast: v })}
            aria-label="Yüksek kontrast modu"
          />
        </Box>
      </Popover>
    </>
  );
}

export default AccessibilitySettings;
