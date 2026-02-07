/**
 * ScreenShare Component
 *
 * Handles screen sharing display and controls.
 * Shows the shared screen content in the video grid.
 */

import { Paper, Chip, Box } from '@mui/material';
import * as React from 'react';

import type { ScreenShareProps } from './types';

// ============================================================
// Main Component
// ============================================================

const ScreenShare: React.FC<ScreenShareProps> = ({
  screenShareRef,
  screenStream,
  isScreenSharing,
}) => {
  if (!isScreenSharing || !screenStream) {
    return null;
  }

  return (
    <Paper
      sx={{
        position: 'relative',
        width: '100%',
        height: '100%',
        bgcolor: 'black',
        minHeight: 300,
      }}
      role="region"
      aria-label="Ekran paylasimi gorunumu"
    >
      <video
        ref={screenShareRef}
        autoPlay
        playsInline
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'contain',
        }}
        aria-label="Paylasilan ekran"
      />
      <Box
        sx={{
          position: 'absolute',
          top: 8,
          left: 8,
          zIndex: 1,
        }}
      >
        <Chip
          label="Ekran Paylasimi"
          color="primary"
          size="small"
        />
      </Box>
    </Paper>
  );
};

// ============================================================
// Screen Share Indicator (for remote participants)
// ============================================================

interface RemoteScreenShareIndicatorProps {
  participantName: string;
}

export const RemoteScreenShareIndicator: React.FC<RemoteScreenShareIndicatorProps> = ({
  participantName,
}) => (
  <Chip
    label={`${participantName} ekranini paylasiyor`}
    color="primary"
    size="small"
    sx={{
      position: 'absolute',
      top: 8,
      left: 8,
      zIndex: 1,
    }}
  />
);

// ============================================================
// Screen Share Preview (Local preview before sharing)
// ============================================================

interface ScreenSharePreviewProps {
  stream: MediaStream | null;
  onStopPreview: () => void;
}

export const ScreenSharePreview: React.FC<ScreenSharePreviewProps> = ({
  stream,
  onStopPreview,
}) => {
  const videoRef = React.useRef<HTMLVideoElement>(null);

  React.useEffect(() => {
    if (videoRef.current && stream) {
      videoRef.current.srcObject = stream;
    }
  }, [stream]);

  if (!stream) {
    return null;
  }

  return (
    <Box
      sx={{
        position: 'fixed',
        bottom: 100,
        right: 16,
        width: 200,
        height: 150,
        bgcolor: 'black',
        borderRadius: 1,
        overflow: 'hidden',
        boxShadow: 3,
        zIndex: 1000,
      }}
    >
      <video
        ref={videoRef}
        autoPlay
        muted
        playsInline
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'contain',
        }}
      />
      <Chip
        label="Onizleme"
        size="small"
        sx={{
          position: 'absolute',
          top: 4,
          left: 4,
          fontSize: '0.7rem',
        }}
        onClick={onStopPreview}
        onDelete={onStopPreview}
      />
    </Box>
  );
};

export default ScreenShare;
