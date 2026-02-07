/**
 * Results Header Component
 * Header section with title, PDF export, recommendations and retake button
 */
import {
  Analytics,
  PictureAsPdf,
  EmojiObjects,
  Refresh,
  Star,
  TrendingUp,
  TrendingDown,
  Assessment,
} from '@mui/icons-material';
import {
  Paper,
  Box,
  Typography,
  Button,
  Chip,
  CircularProgress,
  Tooltip as MuiTooltip,
} from '@mui/material';
import * as React from 'react';

import { examService } from '../../../services/examService';

interface ResultsHeaderProps {
  sinavTipi: string;
  hamPuan: number;
  onGeneratePDF: () => void;
  onShowRecommendations: () => void;
  onRetake?: () => void;
  pdfGenerating: boolean;
}

export const ResultsHeader: React.FC<ResultsHeaderProps> = ({
  sinavTipi,
  hamPuan,
  onGeneratePDF,
  onShowRecommendations,
  onRetake,
  pdfGenerating,
}) => {
  const getSuccessLevel = (puan: number): { level: string; color: string; icon: React.ReactNode } => {
    if (puan >= 80) {
      return { level: 'Mükemmel', color: 'success', icon: <Star /> };
    } else if (puan >= 70) {
      return { level: 'İyi', color: 'info', icon: <TrendingUp /> };
    } else if (puan >= 60) {
      return { level: 'Orta', color: 'warning', icon: <Assessment /> };
    } else {
      return { level: 'Geliştirilmeli', color: 'error', icon: <TrendingDown /> };
    }
  };

  const successInfo = getSuccessLevel(hamPuan);

  return (
    <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Analytics sx={{ fontSize: 40, color: 'primary.main', mr: 2 }} />
          <Box>
            <Typography variant="h4">
              Gelişmiş Sınav Analizi
            </Typography>
            <Typography variant="h6" color="textSecondary">
              {examService.getExamTypeDescription(sinavTipi as any)}
            </Typography>
          </Box>
        </Box>

        <Box sx={{ display: 'flex', gap: 2 }}>
          <MuiTooltip title="PDF Rapor İndir">
            <Button
              variant="contained"
              startIcon={pdfGenerating ? <CircularProgress size={20} /> : <PictureAsPdf />}
              onClick={onGeneratePDF}
              disabled={pdfGenerating}
              color="error"
            >
              {pdfGenerating ? 'Oluşturuluyor...' : 'PDF İndir'}
            </Button>
          </MuiTooltip>

          <MuiTooltip title="Kişiselleştirilmiş Öneriler">
            <Button
              variant="outlined"
              startIcon={<EmojiObjects />}
              onClick={onShowRecommendations}
            >
              Öneriler
            </Button>
          </MuiTooltip>

          {onRetake && (
            <Button
              variant="contained"
              color="secondary"
              startIcon={<Refresh />}
              onClick={onRetake}
            >
              Tekrar Çöz
            </Button>
          )}
        </Box>
      </Box>

      <Chip
        label={successInfo.level}
        color={successInfo.color as any}
        size="medium"
        sx={{ fontSize: '1rem', px: 2 }}
      />
    </Paper>
  );
};

export default ResultsHeader;
