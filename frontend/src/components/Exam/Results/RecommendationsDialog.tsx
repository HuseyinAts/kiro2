/**
 * Kişiselleştirilmiş Öneriler Dialog
 * Personalized Recommendations Dialog
 */
import { EmojiObjects, CheckCircle, TrendingUp } from '@mui/icons-material';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
} from '@mui/material';
import * as React from 'react';

export interface RecommendationsDialogProps {
  open: boolean;
  onClose: () => void;
  oneriler?: any[];
  gelisimOnerileri?: any[];
  children?: React.ReactNode;
}

export const RecommendationsDialog: React.FC<RecommendationsDialogProps> = ({
  open,
  onClose,
  oneriler = [],
  gelisimOnerileri = [],
}) => {
  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
    >
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <EmojiObjects sx={{ mr: 1, color: 'warning.main' }} />
          Kişiselleştirilmiş Öneriler
        </Box>
      </DialogTitle>
      <DialogContent>
        <Typography variant="h6" gutterBottom>
          💡 Öğrenme Önerileri
        </Typography>

        {oneriler.length > 0 ? (
          <List>
            {oneriler.map((oneri, index) => (
              <ListItem key={index}>
                <ListItemIcon>
                  <CheckCircle color="primary" />
                </ListItemIcon>
                <ListItemText primary={oneri.oneri || oneri} />
              </ListItem>
            ))}
          </List>
        ) : (
          <Typography variant="body2" color="textSecondary">
            Henüz kişiselleştirilmiş öneri bulunmuyor
          </Typography>
        )}

        <Divider sx={{ my: 2 }} />

        <Typography variant="h6" gutterBottom>
          📈 Gelişim Önerileri
        </Typography>

        {gelisimOnerileri.length > 0 ? (
          <List>
            {gelisimOnerileri.map((oneri, index) => (
              <ListItem key={index}>
                <ListItemIcon>
                  <TrendingUp color="success" />
                </ListItemIcon>
                <ListItemText primary={oneri.oneri || oneri} />
              </ListItem>
            ))}
          </List>
        ) : (
          <Typography variant="body2" color="textSecondary">
            Henüz gelişim önerisi bulunmuyor
          </Typography>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} variant="contained">
          Kapat
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default RecommendationsDialog;
