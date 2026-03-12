/**
 * MnemonicHint — F19: Hafıza İpucu Gösterimi
 *
 * Shows LLM-generated Turkish mnemonic hints for questions.
 * Displayed in quiz explanation/result views.
 */
import { useState, useCallback } from 'react';
import {
  Box,
  Typography,
  IconButton,
  Collapse,
  Chip,
  CircularProgress,
  Paper,
} from '@mui/material';
import {
  Lightbulb as LightbulbIcon,
  ExpandMore as ExpandIcon,
  ExpandLess as CollapseIcon,
} from '@mui/icons-material';

interface MnemonicHintProps {
  questionId: string;
  /** Pre-loaded mnemonic text (from question data) */
  hint?: string;
  compact?: boolean;
}

export function MnemonicHint({ questionId, hint: initialHint, compact = false }: MnemonicHintProps) {
  const [expanded, setExpanded] = useState(false);
  const [hint, setHint] = useState(initialHint || '');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);

  const fetchHint = useCallback(async () => {
    if (hint || loading) return;
    setLoading(true);
    setError(false);
    try {
      const res = await fetch(`/api/v1/mnemonics/${questionId}`, {
        credentials: 'include',
      });
      if (res.ok) {
        const data = await res.json();
        setHint(data.mnemonic_hint || '');
      } else if (res.status === 404) {
        // No hint exists — try to generate one
        const genRes = await fetch(`/api/v1/mnemonics/${questionId}/generate`, {
          method: 'POST',
          credentials: 'include',
        });
        if (genRes.ok) {
          const data = await genRes.json();
          setHint(data.mnemonic_hint || '');
        }
      }
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  }, [questionId, hint, loading]);

  const handleToggle = useCallback(() => {
    if (!expanded && !hint && !loading) {
      fetchHint();
    }
    setExpanded(prev => !prev);
  }, [expanded, hint, loading, fetchHint]);

  if (compact) {
    return (
      <Chip
        icon={<LightbulbIcon />}
        label={loading ? 'Yükleniyor...' : 'Hafıza İpucu'}
        size="small"
        variant="outlined"
        color="warning"
        onClick={handleToggle}
        sx={{ cursor: 'pointer' }}
      />
    );
  }

  return (
    <Paper variant="outlined" sx={{ mt: 1, borderColor: 'warning.light', borderRadius: 2 }}>
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          px: 1.5,
          py: 0.75,
          cursor: 'pointer',
          '&:hover': { bgcolor: 'action.hover' },
        }}
        onClick={handleToggle}
      >
        <LightbulbIcon sx={{ fontSize: 18, color: 'warning.main', mr: 1 }} />
        <Typography variant="body2" fontWeight={600} color="warning.dark" sx={{ flex: 1 }}>
          Hafıza İpucu
        </Typography>
        {loading ? (
          <CircularProgress size={16} />
        ) : (
          <IconButton size="small">
            {expanded ? <CollapseIcon /> : <ExpandIcon />}
          </IconButton>
        )}
      </Box>
      <Collapse in={expanded}>
        <Box sx={{ px: 1.5, pb: 1.5 }}>
          {hint ? (
            <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>
              {hint}
            </Typography>
          ) : error ? (
            <Typography variant="body2" color="text.secondary">
              İpucu yüklenemedi.
            </Typography>
          ) : (
            <Typography variant="body2" color="text.secondary">
              Yükleniyor...
            </Typography>
          )}
        </Box>
      </Collapse>
    </Paper>
  );
}
