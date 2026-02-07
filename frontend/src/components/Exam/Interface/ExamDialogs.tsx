/**
 * Exam Dialogs Component
 * Confirmation and exit dialogs
 * Extracted from OSYMExamInterface.tsx
 */

import {
  Warning,
  CheckCircle,
  Cancel,
} from '@mui/icons-material';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
} from '@mui/material';
import * as React from 'react';

export interface ExamSubmitDialogProps {
  open: boolean;
  onClose: () => void;
  onConfirm: () => void;
  answeredCount: number;
  unansweredCount: number;
  flaggedCount: number;
}

export const ExamSubmitDialog: React.FC<ExamSubmitDialogProps> = ({
  open,
  onClose,
  onConfirm,
  answeredCount,
  unansweredCount,
  flaggedCount,
}) => {
  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Warning color="warning" />
          Sinavi Bitir
        </Box>
      </DialogTitle>
      <DialogContent>
        <Typography variant="body1" sx={{ mb: 2 }}>
          Sinavi bitirmek istediginizden emin misiniz?
        </Typography>
        <List>
          <ListItem>
            <ListItemIcon>
              <CheckCircle color="success" />
            </ListItemIcon>
            <ListItemText primary={'Cevaplanan: ' + answeredCount + ' soru'} />
          </ListItem>
          {unansweredCount > 0 && (
            <ListItem>
              <ListItemIcon>
                <Cancel color="error" />
              </ListItemIcon>
              <ListItemText primary={'Bos: ' + unansweredCount + ' soru'} />
            </ListItem>
          )}
          {flaggedCount > 0 && (
            <ListItem>
              <ListItemIcon>
                <Warning color="warning" />
              </ListItemIcon>
              <ListItemText primary={'Isaretlenen: ' + flaggedCount + ' soru'} />
            </ListItem>
          )}
        </List>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} color="inherit">
          Iptal
        </Button>
        <Button onClick={onConfirm} variant="contained" color="primary">
          Sinavi Bitir
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export interface ExamExitDialogProps {
  open: boolean;
  onClose: () => void;
  onConfirm: () => void;
}

export const ExamExitDialog: React.FC<ExamExitDialogProps> = ({
  open,
  onClose,
  onConfirm,
}) => {
  return (
    <Dialog open={open} onClose={onClose}>
      <DialogTitle>Sinavdan Cik</DialogTitle>
      <DialogContent>
        <Typography>
          Sinavdan cikmak istediginizden emin misiniz?
          Cevaplarıniz kaydedilecektir.
        </Typography>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Iptal</Button>
        <Button onClick={onConfirm} color="error">
          Cik
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ExamSubmitDialog;
