/**
 * VideoGrid Component
 *
 * Renders the video grid layout including local video,
 * remote participant videos, and screen share view.
 */

import {
  MicOff as MicOffIcon,
  ScreenShare as ScreenShareIcon,
  PushPin as PushPinIcon,
} from '@mui/icons-material';
import { Box, Paper, Avatar, Chip, IconButton, Grid } from '@mui/material';
import * as React from 'react';

import type { VideoGridProps } from './types';

// ============================================================
// Sub-components
// ============================================================

interface VideoOverlayProps {
  name: string;
  isSelf?: boolean;
  isMuted: boolean;
  isScreenSharing?: boolean;
}

const VideoOverlay: React.FC<VideoOverlayProps> = ({
  name,
  isSelf = false,
  isMuted,
  isScreenSharing = false,
}) => (
  <Box
    sx={{
      position: 'absolute',
      bottom: 8,
      left: 8,
      display: 'flex',
      alignItems: 'center',
      gap: 1,
    }}
  >
    <Chip
      label={isSelf ? `${name} (Ben)` : name}
      size="small"
      sx={{ bgcolor: 'rgba(0,0,0,0.6)', color: 'white' }}
    />
    {isMuted && <MicOffIcon sx={{ color: 'error.main' }} />}
    {isScreenSharing && <ScreenShareIcon sx={{ color: 'primary.main' }} />}
  </Box>
);

interface VideoAvatarProps {
  name: string;
  avatar?: string;
  isPrimary?: boolean;
}

const VideoAvatar: React.FC<VideoAvatarProps> = ({
  name,
  avatar,
  isPrimary = true,
}) => (
  <Avatar
    src={avatar}
    sx={{
      position: 'absolute',
      top: '50%',
      left: '50%',
      transform: 'translate(-50%, -50%)',
      width: 80,
      height: 80,
      bgcolor: isPrimary ? 'primary.main' : 'secondary.main',
      fontSize: 32,
    }}
  >
    {name.charAt(0).toUpperCase()}
  </Avatar>
);

// ============================================================
// Main Component
// ============================================================

const VideoGrid: React.FC<VideoGridProps> = ({
  localVideoRef,
  screenShareRef,
  remoteVideosRef,
  participants,
  currentUserName,
  isVideoEnabled,
  isMuted,
  isScreenSharing,
  screenStream,
  pinnedParticipant,
  onPinParticipant,
}) => {
  const videoHeight = isScreenSharing ? 200 : 400;

  return (
    <Box sx={{ flex: 1, p: 2, position: 'relative', overflow: 'hidden' }}>
      <Grid container spacing={2} sx={{ height: '100%' }}>
        {/* Screen Share (Full Width when active) */}
        {isScreenSharing && screenStream && (
          <Grid item xs={12}>
            <Paper sx={{ position: 'relative', height: '100%', bgcolor: 'black' }}>
              <video
                ref={screenShareRef}
                autoPlay
                playsInline
                style={{ width: '100%', height: '100%', objectFit: 'contain' }}
              />
              <Chip
                label="Ekran Paylasimi"
                color="primary"
                sx={{ position: 'absolute', top: 8, left: 8 }}
              />
            </Paper>
          </Grid>
        )}

        {/* Local Video */}
        <Grid item xs={12} md={pinnedParticipant ? 3 : 6}>
          <Paper
            sx={{
              position: 'relative',
              height: videoHeight,
              bgcolor: 'black',
              overflow: 'hidden',
            }}
          >
            <video
              ref={localVideoRef}
              autoPlay
              muted
              playsInline
              style={{
                width: '100%',
                height: '100%',
                objectFit: 'cover',
                transform: 'scaleX(-1)', // Mirror local video
              }}
            />
            {!isVideoEnabled && (
              <VideoAvatar name={currentUserName} isPrimary />
            )}
            <VideoOverlay
              name={currentUserName}
              isSelf
              isMuted={isMuted}
            />
          </Paper>
        </Grid>

        {/* Remote Videos */}
        {participants.map((participant) => (
          <Grid
            item
            xs={12}
            md={pinnedParticipant === participant.user_id ? 9 : 6}
            key={participant.user_id}
          >
            <Paper
              sx={{
                position: 'relative',
                height: videoHeight,
                bgcolor: 'black',
                overflow: 'hidden',
              }}
            >
              <video
                ref={(el) => {
                  if (el) {remoteVideosRef.current.set(participant.user_id, el);}
                }}
                autoPlay
                playsInline
                style={{ width: '100%', height: '100%', objectFit: 'cover' }}
              />
              {!participant.is_video_enabled && (
                <VideoAvatar
                  name={participant.name}
                  avatar={participant.avatar}
                  isPrimary={false}
                />
              )}
              <VideoOverlay
                name={participant.name}
                isMuted={participant.is_muted}
                isScreenSharing={participant.is_screen_sharing}
              />
              <IconButton
                size="small"
                onClick={() =>
                  onPinParticipant(
                    pinnedParticipant === participant.user_id ? null : participant.user_id,
                  )
                }
                sx={{
                  position: 'absolute',
                  top: 8,
                  right: 8,
                  color: 'white',
                  bgcolor: 'rgba(0,0,0,0.4)',
                }}
                aria-label={
                  pinnedParticipant === participant.user_id
                    ? 'Sabitlemeyi kaldir'
                    : 'Sabitle'
                }
              >
                <PushPinIcon fontSize="small" />
              </IconButton>
            </Paper>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
};

export default VideoGrid;
