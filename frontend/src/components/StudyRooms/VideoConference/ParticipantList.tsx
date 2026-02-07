/**
 * ParticipantList Component
 *
 * Dialog showing all participants in the video conference
 * with their audio/video status and role information.
 */

import {
  Videocam as VideocamIcon,
  VideocamOff as VideocamOffIcon,
  Mic as MicIcon,
  MicOff as MicOffIcon,
} from '@mui/icons-material';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  Avatar,
  Box,
  Chip,
} from '@mui/material';
import * as React from 'react';

import type { ParticipantListProps, Participant } from './types';

// ============================================================
// Sub-components
// ============================================================

interface ParticipantStatusProps {
  isMuted: boolean;
  isVideoEnabled: boolean;
  isHost?: boolean;
}

const ParticipantStatus: React.FC<ParticipantStatusProps> = ({
  isMuted,
  isVideoEnabled,
  isHost = false,
}) => (
  <Box component="span" sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
    {isMuted ? (
      <MicOffIcon fontSize="small" color="error" aria-label="Mikrofon kapali" />
    ) : (
      <MicIcon fontSize="small" color="action" aria-label="Mikrofon acik" />
    )}
    {isVideoEnabled ? (
      <VideocamIcon fontSize="small" color="action" aria-label="Kamera acik" />
    ) : (
      <VideocamOffIcon fontSize="small" color="error" aria-label="Kamera kapali" />
    )}
    {isHost && (
      <Chip
        label="Host"
        size="small"
        color="primary"
        sx={{ ml: 1 }}
      />
    )}
  </Box>
);

interface ParticipantItemProps {
  participant: Participant;
}

const ParticipantItem: React.FC<ParticipantItemProps> = ({ participant }) => (
  <ListItem>
    <ListItemAvatar>
      <Avatar src={participant.avatar}>
        {participant.name.charAt(0).toUpperCase()}
      </Avatar>
    </ListItemAvatar>
    <ListItemText
      primary={participant.name}
      secondary={
        <ParticipantStatus
          isMuted={participant.is_muted}
          isVideoEnabled={participant.is_video_enabled}
          isHost={participant.role === 'host'}
        />
      }
    />
  </ListItem>
);

interface CurrentUserItemProps {
  name: string;
  isMuted: boolean;
  isVideoEnabled: boolean;
}

const CurrentUserItem: React.FC<CurrentUserItemProps> = ({
  name,
  isMuted,
  isVideoEnabled,
}) => (
  <ListItem>
    <ListItemAvatar>
      <Avatar sx={{ bgcolor: 'primary.main' }}>
        {name.charAt(0).toUpperCase()}
      </Avatar>
    </ListItemAvatar>
    <ListItemText
      primary={`${name} (Ben)`}
      secondary={
        <ParticipantStatus
          isMuted={isMuted}
          isVideoEnabled={isVideoEnabled}
        />
      }
    />
  </ListItem>
);

// ============================================================
// Main Component
// ============================================================

const ParticipantList: React.FC<ParticipantListProps> = ({
  open,
  onClose,
  participants,
  currentUserName,
  isMuted,
  isVideoEnabled,
}) => {
  const totalCount = participants.length + 1; // +1 for current user

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="sm"
      fullWidth
      aria-labelledby="participants-dialog-title"
    >
      <DialogTitle id="participants-dialog-title">
        Katilimcilar ({totalCount})
      </DialogTitle>
      <DialogContent>
        <List aria-label="Katilimci listesi">
          {/* Current User - Always first */}
          <CurrentUserItem
            name={currentUserName}
            isMuted={isMuted}
            isVideoEnabled={isVideoEnabled}
          />

          {/* Other Participants */}
          {participants.map((participant) => (
            <ParticipantItem
              key={participant.user_id}
              participant={participant}
            />
          ))}
        </List>
      </DialogContent>
    </Dialog>
  );
};

export default ParticipantList;
