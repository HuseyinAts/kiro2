/**
 * ErrorTypeSelector — "Neden Yanlış?" hata taksonomisi
 *
 * Yanlış cevaptan sonra gösterilir. Öğrenci hatanın türünü seçer:
 * - Kavram Hatası: Konuyu yanlış anladım
 * - İşlem Hatası: Doğru düşündüm ama hesap/uygulama yanlış
 * - Dikkatsizlik: Biliyordum ama dikkatsiz davrandım
 * - Bilgi Eksikliği: Bu konuyu hiç bilmiyordum
 *
 * Metacognition (d=0.69) — DINA model slip/guess parametreleri
 */

import { useState } from 'react';
import { Box, Typography, Chip } from '@mui/material';
import {
  Psychology,
  BuildCircle,
  VisibilityOff,
  HelpOutline,
} from '@mui/icons-material';
import { motion } from 'framer-motion';

export type ErrorType = 'concept' | 'procedural' | 'careless' | 'knowledge_gap';

interface ErrorTypeOption {
  type: ErrorType;
  label: string;
  description: string;
  icon: React.ReactElement;
  color: string;
}

const ERROR_TYPES: ErrorTypeOption[] = [
  {
    type: 'concept',
    label: 'Kavram Hatası',
    description: 'Konuyu yanlış anladım',
    icon: <Psychology sx={{ fontSize: 18 }} />,
    color: '#8b5cf6',
  },
  {
    type: 'procedural',
    label: 'İşlem Hatası',
    description: 'Doğru düşündüm ama uygulama yanlış',
    icon: <BuildCircle sx={{ fontSize: 18 }} />,
    color: '#f59e0b',
  },
  {
    type: 'careless',
    label: 'Dikkatsizlik',
    description: 'Biliyordum ama dikkat etmedim',
    icon: <VisibilityOff sx={{ fontSize: 18 }} />,
    color: '#6366f1',
  },
  {
    type: 'knowledge_gap',
    label: 'Bilgi Eksikliği',
    description: 'Bu konuyu hiç bilmiyordum',
    icon: <HelpOutline sx={{ fontSize: 18 }} />,
    color: '#ef4444',
  },
];

interface ErrorTypeSelectorProps {
  questionId: string;
  onSelect: (questionId: string, errorType: ErrorType) => void;
  selected?: ErrorType;
}

export function ErrorTypeSelector({ questionId, onSelect, selected }: ErrorTypeSelectorProps) {
  const [localSelected, setLocalSelected] = useState<ErrorType | undefined>(selected);

  const handleSelect = (errorType: ErrorType) => {
    setLocalSelected(errorType);
    onSelect(questionId, errorType);
  };

  return (
    <motion.div
      initial={{ opacity: 0, height: 0 }}
      animate={{ opacity: 1, height: 'auto' }}
      transition={{ duration: 0.3 }}
    >
      <Box sx={{ mt: 1.5 }}>
        <Typography variant="caption" fontWeight={700} color="text.secondary" sx={{ mb: 0.75, display: 'block' }}>
          Neden yanlış?
        </Typography>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.75 }}>
          {ERROR_TYPES.map((opt) => {
            const isSelected = localSelected === opt.type;
            return (
              <Chip
                key={opt.type}
                icon={opt.icon}
                label={opt.label}
                size="small"
                onClick={() => handleSelect(opt.type)}
                sx={{
                  fontWeight: 600,
                  fontSize: 11,
                  cursor: 'pointer',
                  borderWidth: 1.5,
                  borderStyle: 'solid',
                  borderColor: isSelected ? opt.color : 'transparent',
                  backgroundColor: isSelected ? `${opt.color}15` : 'rgba(0,0,0,0.04)',
                  color: isSelected ? opt.color : 'text.secondary',
                  '&:hover': {
                    backgroundColor: `${opt.color}10`,
                  },
                  '& .MuiChip-icon': {
                    color: isSelected ? opt.color : 'inherit',
                  },
                }}
              />
            );
          })}
        </Box>
      </Box>
    </motion.div>
  );
}

export { ERROR_TYPES };
export default ErrorTypeSelector;
