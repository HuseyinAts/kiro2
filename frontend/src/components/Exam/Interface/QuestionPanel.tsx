/**
 * Question Panel Component
 * Displays question content with proper formatting
 * Extracted from OSYMExamInterface.tsx
 */

import { Box, Typography, Paper, Chip } from '@mui/material';
import { motion } from 'framer-motion';
import * as React from 'react';

export interface QuestionPanelProps {
  questionNumber: number;
  totalQuestions: number;
  questionText: string;
  category?: string;
  difficulty?: string;
  isFlagged?: boolean;
}

export const QuestionPanel: React.FC<QuestionPanelProps> = ({
  questionNumber,
  totalQuestions,
  questionText,
  category,
  difficulty,
  isFlagged = false,
}) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <Paper
        elevation={2}
        sx={{
          p: 3,
          mb: 2,
          borderRadius: 2,
          border: isFlagged ? '2px solid orange' : 'none',
        }}
      >
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
          <Typography variant="h6" component="h2">
            Soru {questionNumber} / {totalQuestions}
          </Typography>
          <Box sx={{ display: 'flex', gap: 1 }}>
            {category && <Chip label={category} size="small" color="primary" variant="outlined" />}
            {difficulty && <Chip label={difficulty} size="small" color="secondary" variant="outlined" />}
          </Box>
        </Box>
        <Typography
          variant="body1"
          sx={{
            whiteSpace: 'pre-wrap',
            lineHeight: 1.8,
            fontSize: '1.1rem',
          }}
        >
          {questionText}
        </Typography>
      </Paper>
    </motion.div>
  );
};

export default QuestionPanel;
