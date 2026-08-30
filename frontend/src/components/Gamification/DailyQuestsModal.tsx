import React from 'react';
import {
  Dialog, DialogTitle, DialogContent, Typography,
  List, ListItem, LinearProgress, Box, Chip,
} from '@mui/material';

export interface Quest {
  id: number;
  title: string;
  description: string;
  target: number;
  current: number;
  completed: boolean;
  xp_reward: number;
}

interface DailyQuestsModalProps {
  open: boolean;
  onClose: () => void;
  quests: Quest[];
}

export const DailyQuestsModal: React.FC<DailyQuestsModalProps> = ({ open, onClose, quests }) => {
  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle sx={{ fontWeight: 'bold', textAlign: 'center' }}>
        🚀 Günlük Görevler
      </DialogTitle>
      <DialogContent>
        <List>
          {quests.map((quest) => (
            <ListItem key={quest.id} sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', mb: 2, p: 2, border: '1px solid #eee', borderRadius: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', width: '100%', mb: 1 }}>
                <Typography variant="subtitle1" fontWeight="bold">
                  {quest.title} {quest.completed && '✅'}
                </Typography>
                <Chip label={`+${quest.xp_reward} XP`} color="warning" size="small" />
              </Box>

              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                {quest.description}
              </Typography>

              <Box sx={{ width: '100%', display: 'flex', alignItems: 'center', gap: 2 }}>
                <Box sx={{ flexGrow: 1 }}>
                  <LinearProgress
                    variant="determinate"
                    value={Math.min((quest.current / quest.target) * 100, 100)}
                    color={quest.completed ? 'success' : 'primary'}
                    sx={{ height: 8, borderRadius: 4 }}
                  />
                </Box>
                <Typography variant="body2" fontWeight="bold">
                  {quest.current} / {quest.target}
                </Typography>
              </Box>
            </ListItem>
          ))}
        </List>
      </DialogContent>
    </Dialog>
  );
};
