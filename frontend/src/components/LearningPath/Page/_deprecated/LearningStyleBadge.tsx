/**
 * Learning Style Badge Component
 *
 * Displays learning style information and preferences
 * Extracted from LearningPathPage.tsx
 */

import { TrendingUp } from '@mui/icons-material';
import { Paper, Box, Typography, Divider, Chip, Alert } from '@mui/material';
import * as React from 'react';

export interface LearningStyleBadgeProps {
  learningStyle: string
}

/**
 * Badge component showing learning style information
 *
 * Displays learning style code and personalized content preferences
 */
export const LearningStyleBadge: React.FC<LearningStyleBadgeProps> = ({
  learningStyle,
}) => {
  return (
    <Paper
      elevation={2}
      sx={{
        p: 3,
        mb: 3,
        background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
        color: 'white',
        borderRadius: 2,
      }}
    >
      <Box className="flex items-center gap-2 mb-2">
        <TrendingUp sx={{ fontSize: 32 }} />
        <Box>
          <Typography variant="h6" fontWeight="bold">
            Öğrenme Stiliniz: {learningStyle}
          </Typography>
          <Typography variant="body2" sx={{ opacity: 0.9 }}>
            {learningStyle.includes('V') && 'Görsel öğrenme odaklı - '}
            {learningStyle.includes('A') && 'İşitsel öğrenme destekli - '}
            Size özel içerik önerileri hazırlanıyor
          </Typography>
        </Box>
      </Box>

      <Divider sx={{ my: 2, borderColor: 'rgba(255,255,255,0.3)' }} />

      <Box className="flex gap-2 flex-wrap">
        <Chip
          label="🎥 Video İçerik +40%"
          size="small"
          sx={{
            backgroundColor: 'rgba(255,255,255,0.3)',
            color: 'white',
            fontWeight: 'bold',
          }}
        />
        <Chip
          label="📊 Görsel Materyaller +30%"
          size="small"
          sx={{
            backgroundColor: 'rgba(255,255,255,0.3)',
            color: 'white',
            fontWeight: 'bold',
          }}
        />
        <Chip
          label="🎮 İnteraktif Alıştırmalar +20%"
          size="small"
          sx={{
            backgroundColor: 'rgba(255,255,255,0.3)',
            color: 'white',
            fontWeight: 'bold',
          }}
        />
        <Chip
          label="📝 Yazılı İçerik +10%"
          size="small"
          sx={{
            backgroundColor: 'rgba(255,255,255,0.3)',
            color: 'white',
            fontWeight: 'bold',
          }}
        />
      </Box>

      <Alert
        severity="info"
        sx={{
          mt: 2,
          backgroundColor: 'rgba(255,255,255,0.2)',
          color: 'white',
          '& .MuiAlert-icon': { color: 'white' },
        }}
      >
        <Typography variant="body2">
          <strong>💡 İpucu:</strong> Görsel öğrenme stilinize uygun videolar ve
          diyagramlar önceliklendirildi. Karmaşık konuları anlamak için görsel
          kaynakları tercih edin!
        </Typography>
      </Alert>
    </Paper>
  );
};

export default LearningStyleBadge;
