/**
 * QuestionCard — CAT ve Placement için ortak soru kartı
 */
import { useState, useEffect, useRef } from 'react';
import {
  Box, Typography, Button, LinearProgress,
  Chip, Paper, Stack,
} from '@mui/material';
import { CheckCircle, Cancel } from '@mui/icons-material';

interface QuestionCardProps {
  stem: string;
  options: Record<string, string>;
  onAnswer: (key: string, ms: number) => void;
  disabled?: boolean;
  feedback?: { selected: string; is_correct: boolean; correct_option: string | null } | null;
  questionNumber?: number;
  totalQuestions?: number;
  theta?: number;
  phase?: string;
}

export function QuestionCard({
  stem, options, onAnswer, disabled = false,
  feedback, questionNumber, totalQuestions, theta, phase,
}: QuestionCardProps) {
  const [selected, setSelected] = useState<string | null>(null);
  const startTime = useRef(Date.now());

  useEffect(() => {
    setSelected(null);
    startTime.current = Date.now();
  }, [stem]);

  const handleSelect = (key: string) => {
    if (disabled || selected) return;
    setSelected(key);
    onAnswer(key, Date.now() - startTime.current);
  };

  const getColor = (key: string): 'default' | 'success' | 'error' | 'primary' => {
    if (!feedback) return selected === key ? 'primary' : 'default';
    if (key === feedback.correct_option) return 'success';
    if (key === feedback.selected && !feedback.is_correct) return 'error';
    return 'default';
  };

  const progress = totalQuestions && questionNumber ? (questionNumber / totalQuestions) * 100 : 0;

  return (
    <Paper elevation={3} sx={{ p: 3, borderRadius: 3, maxWidth: 720, mx: 'auto' }}>
      {questionNumber && (
        <Box mb={2}>
          <Stack direction="row" justifyContent="space-between" alignItems="center" mb={1}>
            <Typography variant="caption" color="text.secondary">
              Soru {questionNumber}{totalQuestions ? ` / ~${totalQuestions}` : ''}
            </Typography>
            <Stack direction="row" spacing={1}>
              {theta !== undefined && (
                <Chip size="small" label={`θ = ${theta.toFixed(2)}`} variant="outlined" />
              )}
              {phase && (
                <Chip size="small"
                  label={phase === 'warm_up' ? '🔥 Isınma' : '🎯 Ana Test'}
                  color={phase === 'warm_up' ? 'default' : 'primary'}
                  variant="outlined"
                />
              )}
            </Stack>
          </Stack>
          {totalQuestions && (
            <LinearProgress variant="determinate" value={progress} sx={{ borderRadius: 1, height: 6 }} />
          )}
        </Box>
      )}

      <Typography variant="body1" fontWeight={500} mb={3} sx={{ lineHeight: 1.8 }}>
        {stem}
      </Typography>

      <Stack spacing={1.5}>
        {Object.entries(options).map(([key, text]) => {
          const color = getColor(key);
          const isSelected = selected === key || feedback?.selected === key;
          return (
            <Button
              key={key}
              variant={isSelected ? 'contained' : 'outlined'}
              color={color as any}
              onClick={() => handleSelect(key)}
              disabled={disabled || !!selected}
              fullWidth
              sx={{
                justifyContent: 'flex-start',
                textAlign: 'left',
                py: 1.2, px: 2,
                borderRadius: 2,
                textTransform: 'none',
                fontWeight: isSelected ? 600 : 400,
              }}
              startIcon={
                feedback
                  ? key === feedback.correct_option ? <CheckCircle />
                    : key === feedback.selected && !feedback.is_correct ? <Cancel />
                    : null
                  : null
              }
            >
              <Typography variant="body2" fontWeight="inherit">
                <strong>{key})</strong>&nbsp;{text}
              </Typography>
            </Button>
          );
        })}
      </Stack>

      {feedback && (
        <Box mt={2} p={1.5} borderRadius={2}
          sx={{ bgcolor: feedback.is_correct ? 'success.50' : 'error.50',
                border: 1, borderColor: feedback.is_correct ? 'success.light' : 'error.light' }}>
          <Typography variant="body2" fontWeight={600}
            color={feedback.is_correct ? 'success.dark' : 'error.dark'}>
            {feedback.is_correct
              ? '✅ Doğru!'
              : `❌ Yanlış. Doğru cevap: ${feedback.correct_option}`}
          </Typography>
        </Box>
      )}
    </Paper>
  );
}
