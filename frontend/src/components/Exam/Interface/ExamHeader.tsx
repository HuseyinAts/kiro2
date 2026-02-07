/**
 * Exam Header Component
 *
 * Displays exam title, timer, save status, and control buttons
 * Extracted from OSYMExamInterface.tsx
 */

import {
  ExitToApp,
  Timer,
  CloudDone,
  CloudOff,
  SaveAlt,
  Warning,
} from '@mui/icons-material';
import {
  Box,
  Typography,
  AppBar,
  Toolbar,
  Chip,
  IconButton,
  LinearProgress,
  Tooltip as MuiTooltip,
} from '@mui/material';
import * as React from 'react';

import { formatTime, getTimerColor } from '../../../hooks/useExamTimer';

export interface ExamHeaderProps {
  examTitle: string
  examType: string
  currentQuestionIndex: number
  totalQuestions: number
  remainingTime: number
  totalDuration: number
  saveStatus: 'saved' | 'saving' | 'error' | null
  saveMessage?: string
  isConnected: boolean
  onExit: () => void
}

export const ExamHeader: React.FC<ExamHeaderProps> = ({
  examTitle,
  examType,
  currentQuestionIndex,
  totalQuestions,
  remainingTime,
  totalDuration,
  saveStatus,
  saveMessage,
  isConnected,
  onExit,
}) => {
  const timerColor = getTimerColor(remainingTime, totalDuration);
  const progress = ((currentQuestionIndex + 1) / totalQuestions) * 100;

  return (
    <AppBar position="static" color="default" elevation={2}>
      <Toolbar sx={{ justifyContent: 'space-between', gap: 2 }}>
        {/* Exam Info */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Box>
            <Typography variant="h6" component="div">
              {examTitle}
            </Typography>
            <Typography variant="caption" color="textSecondary">
              {examType} - Soru {currentQuestionIndex + 1} / {totalQuestions}
            </Typography>
          </Box>
        </Box>

        {/* Center: Progress */}
        <Box sx={{ flexGrow: 1, maxWidth: 300 }}>
          <Typography variant="caption" color="textSecondary" align="center" display="block">
            İlerleme: {progress.toFixed(0)}%
          </Typography>
          <LinearProgress
            variant="determinate"
            value={progress}
            color="primary"
            sx={{ height: 8, borderRadius: 4 }}
          />
        </Box>

        {/* Right: Timer, Save Status, Exit */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          {/* Timer */}
          <Chip
            icon={<Timer />}
            label={formatTime(remainingTime)}
            color={timerColor}
            variant="filled"
            sx={{ fontWeight: 'bold', fontSize: '1.1rem' }}
          />

          {/* Save Status */}
          {saveStatus && (
            <MuiTooltip title={saveMessage || ''}>
              <Chip
                icon={
                  saveStatus === 'saved' ? (
                    <CloudDone />
                  ) : saveStatus === 'saving' ? (
                    <SaveAlt />
                  ) : (
                    <CloudOff />
                  )
                }
                label={
                  saveStatus === 'saved'
                    ? 'Kaydedildi'
                    : saveStatus === 'saving'
                    ? 'Kaydediliyor...'
                    : 'Hata'
                }
                color={saveStatus === 'saved' ? 'success' : saveStatus === 'saving' ? 'info' : 'error'}
                size="small"
              />
            </MuiTooltip>
          )}

          {/* Connection Status */}
          {!isConnected && (
            <MuiTooltip title="Bağlantı kesildi">
              <Chip
                icon={<Warning />}
                label="Çevrimdışı"
                color="warning"
                size="small"
                variant="outlined"
              />
            </MuiTooltip>
          )}

          {/* Exit Button */}
          <MuiTooltip title="Sınavdan Çık">
            <IconButton color="error" onClick={onExit} size="large">
              <ExitToApp />
            </IconButton>
          </MuiTooltip>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default ExamHeader;
