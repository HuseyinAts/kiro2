/**
 * F16: Animasyon / Dikkat Dağıtıcı Kontrolü
 *
 * Reads/writes the "reduce motion" preference via the shared Zustand
 * settingsStore (accessibility.reduceMotion).  The store already seeds
 * from OS prefers-reduced-motion on first run (see settingsStore.initialize).
 *
 * Side-effect (delegated to useReducedMotion hook):
 *   document.documentElement.classList toggle 'reduced-motion'
 *   → accessibility.css disables all CSS transitions/animations.
 */

import * as React from 'react';
import {
  Box,
  Switch,
  Typography,
  FormControlLabel,
  Paper,
  Stack,
} from '@mui/material';
import AnimationOutlinedIcon from '@mui/icons-material/AnimationOutlined';
import { useSettingsStore } from '../../store/settingsStore';

export const AnimationControl: React.FC = () => {
  const reduceMotion = useSettingsStore((s) => s.accessibility.reduceMotion);
  const toggleReduceMotion = useSettingsStore((s) => s.toggleReduceMotion);

  // CSS class side-effect: mirrors what useReducedMotion hook does,
  // kept here so the component is self-contained when mounted standalone.
  React.useEffect(() => {
    const root = document.documentElement;
    if (reduceMotion) {
      root.classList.add('reduced-motion');
    } else {
      root.classList.remove('reduced-motion');
    }
  }, [reduceMotion]);

  const handleChange = (_event: React.ChangeEvent<HTMLInputElement>, checked: boolean) => {
    // Only dispatch when the value actually changes to avoid extra renders.
    if (checked !== reduceMotion) {
      toggleReduceMotion();
    }
  };

  return (
    <Paper
      elevation={0}
      sx={{
        p: 2,
        borderRadius: 2,
        border: '1px solid',
        borderColor: 'divider',
      }}
    >
      <Stack direction="row" alignItems="center" spacing={2}>
        <AnimationOutlinedIcon color="primary" />
        <Box flex={1}>
          <FormControlLabel
            control={
              <Switch
                checked={reduceMotion}
                onChange={handleChange}
                color="primary"
                inputProps={{ 'aria-label': 'Animasyonları azalt' }}
              />
            }
            label={
              <Box>
                <Typography variant="body1" fontWeight={600}>
                  Animasyonları Azalt
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Geçiş efektlerini ve hareketli öğeleri devre dışı bırakır
                </Typography>
              </Box>
            }
          />
        </Box>
      </Stack>
    </Paper>
  );
};

export default AnimationControl;
