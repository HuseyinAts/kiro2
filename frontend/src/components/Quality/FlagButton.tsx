/**
 * FlagButton — Faz 7.2 student feedback
 *
 * Beta öğrencisinin soru hatasını raporlaması için küçük IconButton + Dialog.
 * Backend: POST /api/v1/quality/feedback/flag
 */

import { ReportProblemOutlined } from '@mui/icons-material';
import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  FormControlLabel,
  IconButton,
  Radio,
  RadioGroup,
  Snackbar,
  TextField,
  Tooltip,
  Alert,
} from '@mui/material';
import { useState } from 'react';

import { feedbackService, type FlagType } from '../../services/feedbackService';
import { extractErrorDetail } from '../../utils/extractErrorDetail';

interface FlagButtonProps {
  questionId: string;
  size?: 'small' | 'medium';
}

const FLAG_OPTIONS: { value: FlagType; label: string }[] = [
  { value: 'wrong_answer', label: 'Cevap yanlış' },
  { value: 'wrong_topic', label: 'Konu yanlış (örn. matematik sorusu fizik olarak işaretlenmiş)' },
  { value: 'solution_visible', label: 'Çözüm/cevap görselde görünüyor' },
  { value: 'incomplete_text', label: 'Metin eksik veya bozuk' },
  { value: 'circular', label: 'Soru kendini cevaplıyor (dairesel)' },
  { value: 'figure_needed', label: 'Şekil/görsel gerekiyor ama yok' },
  { value: 'other', label: 'Diğer' },
];

export const FlagButton: React.FC<FlagButtonProps> = ({ questionId, size = 'small' }) => {
  const [open, setOpen] = useState(false);
  const [flagType, setFlagType] = useState<FlagType | ''>('');
  const [note, setNote] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [toast, setToast] = useState<{ open: boolean; severity: 'success' | 'error'; message: string }>({
    open: false,
    severity: 'success',
    message: '',
  });

  const handleClose = () => {
    if (submitting) return;
    setOpen(false);
    // Form state reset on close (not on submit success, so user sees "submitted" state briefly)
    setTimeout(() => {
      setFlagType('');
      setNote('');
    }, 300);
  };

  const handleSubmit = async () => {
    if (!flagType) return;
    setSubmitting(true);
    try {
      await feedbackService.submitFlag({
        question_id: questionId,
        flag_type: flagType,
        note: note.trim() || undefined,
      });
      setToast({ open: true, severity: 'success', message: 'Bildirimin alındı, teşekkürler!' });
      setOpen(false);
      setTimeout(() => {
        setFlagType('');
        setNote('');
      }, 300);
    } catch (err) {
      const msg = extractErrorDetail(err, 'Bildirim gönderilemedi');
      setToast({ open: true, severity: 'error', message: msg });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      <Tooltip title="Bu soruda hata var">
        <IconButton
          size={size}
          onClick={() => setOpen(true)}
          aria-label="Soru hatası bildir"
          sx={{ color: 'text.secondary', '&:hover': { color: 'warning.main' } }}
        >
          <ReportProblemOutlined fontSize={size === 'small' ? 'small' : 'medium'} />
        </IconButton>
      </Tooltip>

      <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
        <DialogTitle>Soru hatası bildir</DialogTitle>
        <DialogContent>
          <FormControl component="fieldset" sx={{ mt: 1, width: '100%' }}>
            <RadioGroup value={flagType} onChange={(e) => setFlagType(e.target.value as FlagType)}>
              {FLAG_OPTIONS.map((opt) => (
                <FormControlLabel
                  key={opt.value}
                  value={opt.value}
                  control={<Radio />}
                  label={opt.label}
                  sx={{ mb: 0.5 }}
                />
              ))}
            </RadioGroup>
          </FormControl>
          <TextField
            label="Açıklama (opsiyonel)"
            multiline
            rows={3}
            fullWidth
            value={note}
            onChange={(e) => setNote(e.target.value)}
            inputProps={{ maxLength: 2000 }}
            helperText={`${note.length}/2000`}
            sx={{ mt: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose} disabled={submitting}>
            İptal
          </Button>
          <Button
            onClick={handleSubmit}
            variant="contained"
            color="warning"
            disabled={!flagType || submitting}
          >
            {submitting ? 'Gönderiliyor…' : 'Bildir'}
          </Button>
        </DialogActions>
      </Dialog>

      <Snackbar
        open={toast.open}
        autoHideDuration={4000}
        onClose={() => setToast((t) => ({ ...t, open: false }))}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert
          onClose={() => setToast((t) => ({ ...t, open: false }))}
          severity={toast.severity}
          variant="filled"
          sx={{ width: '100%' }}
        >
          {toast.message}
        </Alert>
      </Snackbar>
    </>
  );
};
