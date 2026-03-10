/**
 * MasteryBadge - BKT Mastery Göstergesi
 *
 * Öğrencinin belirli bir konudaki hakimiyet seviyesini gösterir.
 * Puan/rozet yerine yetkinlik odaklı feedback (SDT competence r=.41).
 * Veri kaynağı: adaptive_test_engine.py → knowledge_probability
 */

import { Box, Typography, CircularProgress } from '@mui/material';

interface MasteryBadgeProps {
  /** 0-1 arası mastery oranı */
  mastery: number;
  /** Compact mod (sadece yüzde göster) */
  compact?: boolean;
}

const getMasteryColor = (mastery: number): string => {
  if (mastery >= 0.8) return '#4CAF50';
  if (mastery >= 0.5) return '#FF9800';
  return '#F44336';
};

const getMasteryLabel = (mastery: number): string => {
  if (mastery >= 0.8) return 'Güçlü';
  if (mastery >= 0.5) return 'Gelişiyor';
  return 'Başlangıç';
};

export function MasteryBadge({ mastery, compact = false }: MasteryBadgeProps) {
  const pct = Math.round(mastery * 100);
  const color = getMasteryColor(mastery);

  if (compact) {
    return (
      <Typography
        variant="caption"
        fontWeight={600}
        sx={{ color }}
      >
        %{pct}
      </Typography>
    );
  }

  return (
    <Box sx={{ display: 'inline-flex', alignItems: 'center', gap: 1 }}>
      <Box sx={{ position: 'relative', display: 'inline-flex' }}>
        <CircularProgress
          variant="determinate"
          value={pct}
          size={36}
          thickness={4}
          sx={{ color, '& .MuiCircularProgress-circle': { strokeLinecap: 'round' } }}
        />
        <Box
          sx={{
            position: 'absolute',
            inset: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Typography variant="caption" fontWeight={700} sx={{ fontSize: '0.6rem' }}>
            {pct}
          </Typography>
        </Box>
      </Box>
      <Box>
        <Typography variant="caption" fontWeight={600} sx={{ color, lineHeight: 1.2, display: 'block' }}>
          {getMasteryLabel(mastery)}
        </Typography>
        <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.65rem', lineHeight: 1 }}>
          hakimiyet
        </Typography>
      </Box>
    </Box>
  );
}

export default MasteryBadge;
