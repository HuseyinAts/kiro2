/**
 * Exam Results Header Component
 *
 * Displays exam title, score badge, and action buttons
 */

import {
  Analytics,
  PictureAsPdf,
  EmojiObjects,
  Refresh,
} from '@mui/icons-material';
import {
  Paper,
  Typography,
  Box,
  Button,
  Chip,
  CircularProgress,
  Tooltip as MuiTooltip,
} from '@mui/material';
import * as React from 'react';

import { examService } from '../../../services/examService';
import { getSuccessLevel } from '../../../utils/examResultsHelpers';

export interface ExamResultsHeaderProps {
  sinavTipi: string
  hamPuan: number
  pdfGenerating: boolean
  onGeneratePDF: () => void
  onShowRecommendations: () => void
  onRetake?: () => void
}

export const ExamResultsHeader: React.FC<ExamResultsHeaderProps> = ({
  sinavTipi,
  hamPuan,
  pdfGenerating,
  onGeneratePDF,
  onShowRecommendations,
  onRetake,
}) => {
  const successInfo = getSuccessLevel(hamPuan);

  return (
    <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          mb: 2,
          flexWrap: 'wrap',
          gap: 2,
        }}
      >
        {/* Title */}
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Analytics sx={{ fontSize: 40, color: 'primary.main', mr: 2 }} />
          <Box>
            <Typography variant="h4">Gelişmiş Sınav Analizi</Typography>
            <Typography variant="h6" color="textSecondary">
              {examService.getExamTypeDescription(sinavTipi as any)}
            </Typography>
          </Box>
        </Box>

        {/* Action Buttons */}
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
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

      {/* Success Badge */}
      <Chip
        label={successInfo.level}
        color={successInfo.color}
        size="medium"
        icon={successInfo.icon as any}
        sx={{ fontSize: '1rem', px: 2 }}
      />
    </Paper>
  );
};

export default ExamResultsHeader;
