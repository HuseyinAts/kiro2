/**
 * Exam Navigation Component
 * Question navigation grid and controls
 * Extracted from OSYMExamInterface.tsx
 */

import {
  NavigateBefore,
  NavigateNext,
  Flag,
  FlagOutlined,
} from '@mui/icons-material';
import {
  Box,
  Button,
  IconButton,
  Tooltip,
  Grid,
  Paper,
  Typography,
} from '@mui/material';
import * as React from 'react';

export interface QuestionStatus {
  answered: boolean;
  flagged: boolean;
}

export interface ExamNavigationProps {
  currentQuestion: number;
  totalQuestions: number;
  questionStatuses: QuestionStatus[];
  onQuestionSelect: (index: number) => void;
  onPrevious: () => void;
  onNext: () => void;
  onToggleFlag: () => void;
  isFlagged: boolean;
}

export const ExamNavigation: React.FC<ExamNavigationProps> = ({
  currentQuestion,
  totalQuestions,
  questionStatuses,
  onQuestionSelect,
  onPrevious,
  onNext,
  onToggleFlag,
  isFlagged,
}) => {
  const getButtonColor = (index: number): 'primary' | 'success' | 'warning' | 'inherit' => {
    if (index === currentQuestion) {return 'primary';}
    const status = questionStatuses[index];
    if (status?.flagged) {return 'warning';}
    if (status?.answered) {return 'success';}
    return 'inherit';
  };

  return (
    <Paper elevation={1} sx={{ p: 2, borderRadius: 2 }}>
      {/* Navigation Controls */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
        <Button
          variant="outlined"
          startIcon={<NavigateBefore />}
          onClick={onPrevious}
          disabled={currentQuestion === 0}
        >
          Onceki
        </Button>

        <Tooltip title={isFlagged ? 'Isaretlemeyi Kaldir' : 'Isaretl'}>
          <IconButton onClick={onToggleFlag} color={isFlagged ? 'warning' : 'default'}>
            {isFlagged ? <Flag /> : <FlagOutlined />}
          </IconButton>
        </Tooltip>

        <Button
          variant="outlined"
          endIcon={<NavigateNext />}
          onClick={onNext}
          disabled={currentQuestion === totalQuestions - 1}
        >
          Sonraki
        </Button>
      </Box>

      {/* Question Grid */}
      <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
        Soru Haritasi
      </Typography>
      <Grid container spacing={0.5}>
        {Array.from({ length: totalQuestions }, (_, i) => (
          <Grid item key={i}>
            <Button
              size="small"
              variant={i === currentQuestion ? 'contained' : 'outlined'}
              color={getButtonColor(i)}
              onClick={() => onQuestionSelect(i)}
              sx={{
                minWidth: 36,
                height: 36,
                fontSize: '0.75rem',
              }}
            >
              {i + 1}
            </Button>
          </Grid>
        ))}
      </Grid>

      {/* Legend */}
      <Box sx={{ display: 'flex', gap: 2, mt: 2, fontSize: '0.75rem' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <Box sx={{ width: 12, height: 12, bgcolor: 'success.main', borderRadius: 0.5 }} />
          <span>Cevaplandi</span>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <Box sx={{ width: 12, height: 12, bgcolor: 'warning.main', borderRadius: 0.5 }} />
          <span>Isaretlendi</span>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <Box sx={{ width: 12, height: 12, bgcolor: 'grey.300', borderRadius: 0.5 }} />
          <span>Bos</span>
        </Box>
      </Box>
    </Paper>
  );
};

export default ExamNavigation;
