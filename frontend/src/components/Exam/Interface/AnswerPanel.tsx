/**
 * Answer Panel Component
 * Displays answer options (A-E) for OSYM format
 * Extracted from OSYMExamInterface.tsx
 */

import {
  RadioGroup,
  FormControlLabel,
  Radio,
  Paper,
  Typography,
} from '@mui/material';
import { motion } from 'framer-motion';
import * as React from 'react';

import { MathText } from '@/components/ui/MathText';

export interface AnswerOption {
  key: string;
  text: string;
}

export interface AnswerPanelProps {
  options: AnswerOption[];
  selectedAnswer: string | null;
  onAnswerSelect: (answer: string) => void;
  disabled?: boolean;
  showCorrectAnswer?: boolean;
  correctAnswer?: string;
}

export const AnswerPanel: React.FC<AnswerPanelProps> = ({
  options,
  selectedAnswer,
  onAnswerSelect,
  disabled = false,
  showCorrectAnswer = false,
  correctAnswer,
}) => {
  const getOptionStyle = (optionKey: string) => {
    if (!showCorrectAnswer) {return {};}

    if (optionKey === correctAnswer) {
      return { backgroundColor: 'rgba(76, 175, 80, 0.1)', borderColor: 'green' };
    }
    if (optionKey === selectedAnswer && optionKey !== correctAnswer) {
      return { backgroundColor: 'rgba(244, 67, 54, 0.1)', borderColor: 'red' };
    }
    return {};
  };

  return (
    <Paper elevation={1} sx={{ p: 2, borderRadius: 2 }}>
      <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
        Cevap Secenekleri
      </Typography>
      <RadioGroup
        value={selectedAnswer || ''}
        onChange={(e) => onAnswerSelect(e.target.value)}
      >
        {options.map((option, index) => (
          <motion.div
            key={option.key}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1 }}
          >
            <Paper
              variant="outlined"
              sx={{
                mb: 1,
                p: 1,
                borderRadius: 1,
                cursor: disabled ? 'default' : 'pointer',
                ...getOptionStyle(option.key),
                '&:hover': !disabled ? {
                  backgroundColor: 'action.hover',
                } : {},
              }}
            >
              <FormControlLabel
                value={option.key}
                control={<Radio disabled={disabled} />}
                label={
                  <Typography variant="body1" component="div">
                    <strong>{option.key})</strong> <MathText inline>{option.text}</MathText>
                  </Typography>
                }
                sx={{ width: '100%', m: 0 }}
              />
            </Paper>
          </motion.div>
        ))}
      </RadioGroup>
    </Paper>
  );
};

export default AnswerPanel;
