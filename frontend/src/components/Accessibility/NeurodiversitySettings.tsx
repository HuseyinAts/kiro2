/**
 * F17: Nörodiversite Desteği Güçlendirme
 *
 * Settings panel covering:
 *   - Font size slider (14–24 px)   → settingsStore.accessibility.fontSize
 *   - Line height selector           → settingsStore.accessibility.lineHeight
 *   - Focus mode toggle              → localStorage via useNeurodiversityPrefs
 *   - Persistent timer bar toggle    → localStorage via useNeurodiversityPrefs
 *   - Breadcrumb navigation toggle   → localStorage via useNeurodiversityPrefs
 *
 * fontSize / lineHeight are stored in the shared Zustand settingsStore so they
 * stay in sync with TypographySettings and useAccessibilityStyles.
 * The three novel prefs (focusMode, persistentTimer, showBreadcrumb) are
 * managed by the useNeurodiversityPrefs hook in hooks/useNeurodiversityPrefs.ts.
 */

import * as React from 'react';
import {
  Box,
  Divider,
  FormControlLabel,
  Paper,
  Slider,
  Stack,
  Switch,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from '@mui/material';
import AccessibilityNewIcon from '@mui/icons-material/AccessibilityNew';
import CenterFocusStrongIcon from '@mui/icons-material/CenterFocusStrong';
import FormatLineSpacingIcon from '@mui/icons-material/FormatLineSpacing';
import NavigationIcon from '@mui/icons-material/Navigation';
import TextFieldsIcon from '@mui/icons-material/TextFields';
import TimerIcon from '@mui/icons-material/Timer';
import { useSettingsStore } from '../../store/settingsStore';
import {
  useNeurodiversityPrefs,
  type NeurodiversityExtPrefs,
} from '../../hooks/useNeurodiversityPrefs';

// ─── Component ───────────────────────────────────────────────────────────────

export const NeurodiversitySettings: React.FC = () => {
  // Font size and line height are owned by the shared store.
  const fontSize = useSettingsStore((s) => s.accessibility.fontSize);
  const lineHeight = useSettingsStore((s) => s.accessibility.lineHeight);
  const setFontSize = useSettingsStore((s) => s.setFontSize);
  const setLineHeight = useSettingsStore((s) => s.setLineHeight);

  // Novel extended prefs are stored in localStorage via the hook above.
  const { prefs, setPrefs } = useNeurodiversityPrefs();

  const updateExt = (partial: Partial<NeurodiversityExtPrefs>) =>
    setPrefs((prev) => ({ ...prev, ...partial }));

  // Apply CSS custom properties for font size and line height so the rest of
  // the app can consume them via var(--kiro2-font-size) / var(--kiro2-line-height).
  React.useEffect(() => {
    document.documentElement.style.setProperty('--kiro2-font-size', `${fontSize}px`);
  }, [fontSize]);

  React.useEffect(() => {
    document.documentElement.style.setProperty('--kiro2-line-height', String(lineHeight));
  }, [lineHeight]);

  // Line height options within the store's allowed range (1.0–2.0).
  const LINE_HEIGHT_OPTIONS: Array<{ value: number; label: string }> = [
    { value: 1.5, label: 'Normal' },
    { value: 1.75, label: 'Geniş' },
    { value: 2.0, label: 'Çok Geniş' },
  ];

  const handleLineHeightChange = (
    _event: React.MouseEvent<HTMLElement>,
    newValue: number | null,
  ) => {
    if (newValue !== null) {
      setLineHeight(newValue);
    }
  };

  const handleFontSizeChange = (_event: Event, newValue: number | number[]) => {
    setFontSize(newValue as number);
  };

  return (
    <Paper
      elevation={0}
      sx={{
        p: 3,
        borderRadius: 2,
        border: '1px solid',
        borderColor: 'divider',
      }}
    >
      <Stack spacing={3}>
        {/* Header */}
        <Stack direction="row" alignItems="center" spacing={1}>
          <AccessibilityNewIcon color="primary" />
          <Typography variant="h6" fontWeight={700}>
            Erişilebilirlik Ayarları
          </Typography>
        </Stack>

        <Divider />

        {/* Font Size */}
        <Box>
          <Stack direction="row" alignItems="center" spacing={1} mb={1}>
            <TextFieldsIcon fontSize="small" />
            <Typography variant="body2" fontWeight={600}>
              Yazı Boyutu: {fontSize}px
            </Typography>
          </Stack>
          <Slider
            value={fontSize}
            onChange={handleFontSizeChange}
            min={14}
            max={24}
            step={1}
            marks={[
              { value: 14, label: '14' },
              { value: 18, label: '18' },
              { value: 24, label: '24' },
            ]}
            aria-label="Yazı boyutu"
            valueLabelDisplay="auto"
          />
        </Box>

        {/* Line Height */}
        <Box>
          <Stack direction="row" alignItems="center" spacing={1} mb={1}>
            <FormatLineSpacingIcon fontSize="small" />
            <Typography variant="body2" fontWeight={600}>
              Satır Aralığı
            </Typography>
          </Stack>
          <ToggleButtonGroup
            value={lineHeight}
            exclusive
            onChange={handleLineHeightChange}
            size="small"
            aria-label="Satır aralığı seçimi"
          >
            {LINE_HEIGHT_OPTIONS.map((opt) => (
              <ToggleButton key={opt.value} value={opt.value} aria-label={opt.label}>
                {opt.label}
              </ToggleButton>
            ))}
          </ToggleButtonGroup>
        </Box>

        <Divider />

        {/* Focus Mode */}
        <FormControlLabel
          control={
            <Switch
              checked={prefs.focusMode}
              onChange={(_e, checked) => updateExt({ focusMode: checked })}
              color="primary"
            />
          }
          label={
            <Stack direction="row" alignItems="center" spacing={1}>
              <CenterFocusStrongIcon fontSize="small" />
              <Box>
                <Typography variant="body2" fontWeight={600}>
                  Odak Modu
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Her ekranda tek soru göster (ADHD dostu)
                </Typography>
              </Box>
            </Stack>
          }
        />

        {/* Persistent Timer */}
        <FormControlLabel
          control={
            <Switch
              checked={prefs.persistentTimer}
              onChange={(_e, checked) => updateExt({ persistentTimer: checked })}
              color="primary"
            />
          }
          label={
            <Stack direction="row" alignItems="center" spacing={1}>
              <TimerIcon fontSize="small" />
              <Box>
                <Typography variant="body2" fontWeight={600}>
                  Sürekli Zamanlayıcı
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Sınav/quiz sırasında zamanlayıcı her zaman görünür
                </Typography>
              </Box>
            </Stack>
          }
        />

        {/* Breadcrumb Navigation */}
        <FormControlLabel
          control={
            <Switch
              checked={prefs.showBreadcrumb}
              onChange={(_e, checked) => updateExt({ showBreadcrumb: checked })}
              color="primary"
            />
          }
          label={
            <Stack direction="row" alignItems="center" spacing={1}>
              <NavigationIcon fontSize="small" />
              <Box>
                <Typography variant="body2" fontWeight={600}>
                  Konum Göstergesi
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  &ldquo;Neredesin?&rdquo; breadcrumb navigasyonu göster
                </Typography>
              </Box>
            </Stack>
          }
        />
      </Stack>
    </Paper>
  );
};

export default NeurodiversitySettings;
