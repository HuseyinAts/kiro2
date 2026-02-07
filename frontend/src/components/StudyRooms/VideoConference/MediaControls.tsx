/**
 * MediaControls Component
 *
 * Audio/video control buttons for the video conference.
 * Includes mute, camera toggle, screen share, recording, and leave controls.
 */

import {
  Videocam as VideocamIcon,
  VideocamOff as VideocamOffIcon,
  Mic as MicIcon,
  MicOff as MicOffIcon,
  ScreenShare as ScreenShareIcon,
  StopScreenShare as StopScreenShareIcon,
  CallEnd as CallEndIcon,
  PeopleAlt as PeopleAltIcon,
  FiberManualRecord as RecordIcon,
} from '@mui/icons-material';
import { Paper, IconButton, Tooltip, Badge, Box } from '@mui/material';
import type { FC, ReactNode } from 'react';

import type { MediaControlsProps } from './types';

// ============================================================
// Sub-components
// ============================================================

interface ControlButtonProps {
  tooltip: string;
  onClick: () => void;
  isActive?: boolean;
  isDestructive?: boolean;
  children: ReactNode;
  'aria-label'?: string;
}

const ControlButton: FC<ControlButtonProps> = ({
  tooltip,
  onClick,
  isActive = false,
  isDestructive = false,
  children,
  'aria-label': ariaLabel,
}) => {
  const getButtonStyles = () => {
    if (isDestructive) {
      return {
        bgcolor: 'error.main',
        color: 'white',
        '&:hover': { bgcolor: 'error.dark' },
      };
    }
    if (isActive) {
      return {
        bgcolor: 'primary.main',
        color: 'white',
        '&:hover': { bgcolor: 'primary.dark' },
      };
    }
    return {
      bgcolor: 'action.hover',
      color: 'text.primary',
      '&:hover': { bgcolor: 'action.selected' },
    };
  };

  return (
    <Tooltip title={tooltip}>
      <IconButton
        onClick={onClick}
        sx={getButtonStyles()}
        aria-label={ariaLabel || tooltip}
      >
        {children}
      </IconButton>
    </Tooltip>
  );
};

interface ToggleButtonProps {
  tooltip: { on: string; off: string };
  isOn: boolean;
  onToggle: () => void;
  iconOn: ReactNode;
  iconOff: ReactNode;
  invertColors?: boolean;
}

const ToggleButton: FC<ToggleButtonProps> = ({
  tooltip,
  isOn,
  onToggle,
  iconOn,
  iconOff,
  invertColors = false,
}) => {
  const isError = invertColors ? !isOn : isOn;

  return (
    <Tooltip title={isOn ? tooltip.on : tooltip.off}>
      <IconButton
        onClick={onToggle}
        sx={{
          bgcolor: isError ? 'error.main' : 'action.hover',
          color: isError ? 'white' : 'text.primary',
          '&:hover': { bgcolor: isError ? 'error.dark' : 'action.selected' },
        }}
        aria-label={isOn ? tooltip.on : tooltip.off}
      >
        {isOn ? iconOff : iconOn}
      </IconButton>
    </Tooltip>
  );
};

// ============================================================
// Main Component
// ============================================================

const MediaControls: FC<MediaControlsProps> = ({
  isMuted,
  isVideoEnabled,
  isScreenSharing,
  isRecording,
  participantCount,
  onToggleMute,
  onToggleVideo,
  onToggleScreenShare,
  onToggleRecording,
  onOpenParticipants,
  onLeave,
}) => {
  return (
    <Paper
      sx={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        gap: 2,
        p: 2,
        borderTop: 1,
        borderColor: 'divider',
      }}
      role="toolbar"
      aria-label="Video konferans kontrolleri"
    >
      {/* Microphone Toggle */}
      <ToggleButton
        tooltip={{ on: 'Mikrofonu Kapat', off: 'Mikrofonu Aç' }}
        isOn={!isMuted}
        onToggle={onToggleMute}
        iconOn={<MicIcon />}
        iconOff={<MicOffIcon />}
        invertColors
      />

      {/* Camera Toggle */}
      <ToggleButton
        tooltip={{ on: 'Kamerayı Kapat', off: 'Kamerayı Aç' }}
        isOn={isVideoEnabled}
        onToggle={onToggleVideo}
        iconOn={<VideocamIcon />}
        iconOff={<VideocamOffIcon />}
      />

      {/* Screen Share Toggle */}
      <ControlButton
        tooltip={isScreenSharing ? 'Ekran Paylaşımını Durdur' : 'Ekran Paylaş'}
        onClick={onToggleScreenShare}
        isActive={isScreenSharing}
      >
        {isScreenSharing ? <StopScreenShareIcon /> : <ScreenShareIcon />}
      </ControlButton>

      {/* Recording Toggle */}
      <ControlButton
        tooltip={isRecording ? 'Kaydı Durdur' : 'Kayıt Başlat'}
        onClick={onToggleRecording}
        isActive={isRecording}
        isDestructive={isRecording}
      >
        <RecordIcon />
      </ControlButton>

      {/* Participants Button */}
      <Tooltip title="Katılımcılar">
        <Badge badgeContent={participantCount} color="primary">
          <IconButton
            onClick={onOpenParticipants}
            aria-label={`Katılımcılar (${participantCount} kişi)`}
          >
            <PeopleAltIcon />
          </IconButton>
        </Badge>
      </Tooltip>

      {/* Spacer */}
      <Box sx={{ flex: 1 }} />

      {/* Leave Button */}
      <ControlButton
        tooltip="Aramayı Bitir"
        onClick={onLeave}
        isDestructive
      >
        <CallEndIcon />
      </ControlButton>
    </Paper>
  );
};

export default MediaControls;
