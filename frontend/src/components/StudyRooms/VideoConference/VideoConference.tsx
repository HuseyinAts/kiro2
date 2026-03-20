/**
 * VideoConference Orchestrator Component
 *
 * Main orchestrator for the video conference module.
 * Manages WebRTC connections, WebSocket signaling, and coordinates sub-components.
 */

import { Box } from '@mui/material';
import axios from 'axios';
import * as React from 'react';
import {  useState, useEffect, useRef, useCallback  } from 'react';

// Components
import {
  DEFAULT_RTC_CONFIG,
  initializeLocalStream,
  startScreenCapture,
  stopMediaStream,
  toggleAudioTracks,
  toggleVideoTracks,
  setupPeerConnection,
  replaceVideoTrack,
  closeAllPeerConnections,
  createOffer,
  createAnswer,
  setRemoteAnswer,
  addIceCandidate,
  createWSMessage,
  parseWSMessage,
  getWebSocketUrl,
} from './lib/webrtcManager';
import MediaControls from './MediaControls';
import ParticipantList from './ParticipantList';

// Types
import type {
  VideoConferenceProps,
  Participant,
  PeerConnection,
  WebSocketMessage,
} from './types';
import VideoGrid from './VideoGrid';

// WebRTC utilities

// ============================================================
// Main Component
// ============================================================

const VideoConference: React.FC<VideoConferenceProps> = ({
  roomId,
  currentUserId,
  currentUserName,
  onLeave,
}) => {
  // State
  const [participants, setParticipants] = useState<Participant[]>([]);
  const [localStream, setLocalStream] = useState<MediaStream | null>(null);
  const [screenStream, setScreenStream] = useState<MediaStream | null>(null);
  const [peerConnections, setPeerConnections] = useState<Map<string, PeerConnection>>(new Map());
  const [isMuted, setIsMuted] = useState(false);
  const [isVideoEnabled, setIsVideoEnabled] = useState(true);
  const [isScreenSharing, setIsScreenSharing] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [participantsDialogOpen, setParticipantsDialogOpen] = useState(false);
  const [pinnedParticipant, setPinnedParticipant] = useState<string | null>(null);
  const [wsConnection, setWsConnection] = useState<WebSocket | null>(null);

  // Refs
  const localVideoRef = useRef<HTMLVideoElement>(null);
  const screenShareRef = useRef<HTMLVideoElement>(null);
  const remoteVideosRef = useRef<Map<string, HTMLVideoElement>>(new Map());

  // ============================================================
  // WebSocket Message Handlers
  // ============================================================

  const handleUserJoined = useCallback(async (userId: string, ws: WebSocket) => {
    if (userId === currentUserId || !localStream) {return;}

    const peerConnection = setupPeerConnection(
      DEFAULT_RTC_CONFIG,
      localStream,
      (event) => {
        const remoteVideo = remoteVideosRef.current.get(userId);
        if (remoteVideo) {
          remoteVideo.srcObject = event.streams[0];
        }
      },
      (event) => {
        if (event.candidate) {
          ws.send(createWSMessage('ice-candidate', { userId, candidate: event.candidate }));
        }
      },
    );

    const offer = await createOffer(peerConnection);
    ws.send(createWSMessage('offer', { userId, offer }));

    setPeerConnections((prev) => {
      const newMap = new Map(prev);
      newMap.set(userId, { userId, connection: peerConnection });
      return newMap;
    });
  }, [currentUserId, localStream]);

  const handleUserLeft = useCallback((userId: string) => {
    setPeerConnections((prev) => {
      const pc = prev.get(userId);
      if (pc) {
        pc.connection.close();
      }
      const newMap = new Map(prev);
      newMap.delete(userId);
      return newMap;
    });
    setParticipants((prev) => prev.filter((p) => p.user_id !== userId));
  }, []);

  const handleOffer = useCallback(async (
    userId: string,
    offer: RTCSessionDescriptionInit,
    ws: WebSocket,
  ) => {
    if (!localStream) {return;}

    const peerConnection = setupPeerConnection(
      DEFAULT_RTC_CONFIG,
      localStream,
      (event) => {
        const remoteVideo = remoteVideosRef.current.get(userId);
        if (remoteVideo) {
          remoteVideo.srcObject = event.streams[0];
        }
      },
      (event) => {
        if (event.candidate) {
          ws.send(createWSMessage('ice-candidate', { userId, candidate: event.candidate }));
        }
      },
    );

    const answer = await createAnswer(peerConnection, offer);
    ws.send(createWSMessage('answer', { userId, answer }));

    setPeerConnections((prev) => {
      const newMap = new Map(prev);
      newMap.set(userId, { userId, connection: peerConnection });
      return newMap;
    });
  }, [localStream]);

  const handleAnswer = useCallback(async (userId: string, answer: RTCSessionDescriptionInit) => {
    const pc = peerConnections.get(userId);
    if (pc) {
      await setRemoteAnswer(pc.connection, answer);
    }
  }, [peerConnections]);

  const handleIceCandidateMessage = useCallback(async (
    userId: string,
    candidate: RTCIceCandidateInit,
  ) => {
    const pc = peerConnections.get(userId);
    if (pc) {
      await addIceCandidate(pc.connection, candidate);
    }
  }, [peerConnections]);

  // ============================================================
  // Initialization
  // ============================================================

  useEffect(() => {
    let mounted = true;
    let ws: WebSocket | null = null;

    const initialize = async () => {
      try {
        // Initialize media
        const stream = await initializeLocalStream();
        if (!mounted) {
          stopMediaStream(stream);
          return;
        }

        setLocalStream(stream);
        if (localVideoRef.current) {
          localVideoRef.current.srcObject = stream;
        }

        // Notify server
        await axios.post(`/api/v1/study-rooms/${roomId}/video/join`, {
          user_id: currentUserId,
          name: currentUserName,
        });

        // Connect WebSocket
        ws = new WebSocket(getWebSocketUrl(roomId));

        ws.onopen = () => {
          if (mounted) {
            setWsConnection(ws);
          }
        };

        ws.onmessage = async (event) => {
          if (!mounted || !ws) {return;}
          const message: WebSocketMessage = parseWSMessage(event.data);

          switch (message.type) {
            case 'user-joined':
              if (message.userId) {
                await handleUserJoined(message.userId, ws);
              }
              break;
            case 'user-left':
              if (message.userId) {
                handleUserLeft(message.userId);
              }
              break;
            case 'offer':
              if (message.userId && message.offer) {
                await handleOffer(message.userId, message.offer, ws);
              }
              break;
            case 'answer':
              if (message.userId && message.answer) {
                await handleAnswer(message.userId, message.answer);
              }
              break;
            case 'ice-candidate':
              if (message.userId && message.candidate) {
                await handleIceCandidateMessage(message.userId, message.candidate);
              }
              break;
            case 'participants-update':
              if (message.participants) {
                setParticipants(message.participants);
              }
              break;
          }
        };

        ws.onerror = (error) => {
          console.error('WebSocket error:', error);
        };
      } catch (error) {
        console.error('Error initializing video conference:', error);
      }
    };

    initialize();

    return () => {
      mounted = false;
      if (ws) {
        ws.close();
      }
    };
  }, [roomId, currentUserId, currentUserName]);

  // ============================================================
  // Media Control Handlers
  // ============================================================

  const handleToggleMute = useCallback(() => {
    if (localStream) {
      toggleAudioTracks(localStream, isMuted);
      setIsMuted(!isMuted);

      if (wsConnection) {
        wsConnection.send(createWSMessage('audio-toggle', { isMuted: !isMuted }));
      }
    }
  }, [localStream, isMuted, wsConnection]);

  const handleToggleVideo = useCallback(() => {
    if (localStream) {
      toggleVideoTracks(localStream, !isVideoEnabled);
      setIsVideoEnabled(!isVideoEnabled);

      if (wsConnection) {
        wsConnection.send(createWSMessage('video-toggle', { isVideoEnabled: !isVideoEnabled }));
      }
    }
  }, [localStream, isVideoEnabled, wsConnection]);

  const handleToggleScreenShare = useCallback(async () => {
    if (isScreenSharing) {
      // Stop screen share
      stopMediaStream(screenStream);
      setScreenStream(null);
      setIsScreenSharing(false);

      // Restore camera
      if (localStream) {
        const videoTrack = localStream.getVideoTracks()[0];
        replaceVideoTrack(peerConnections, videoTrack);
      }

      if (wsConnection) {
        wsConnection.send(createWSMessage('screen-share-stop', {}));
      }
    } else {
      try {
        const stream = await startScreenCapture();
        setScreenStream(stream);
        setIsScreenSharing(true);

        if (screenShareRef.current) {
          screenShareRef.current.srcObject = stream;
        }

        // Replace video track
        const videoTrack = stream.getVideoTracks()[0];
        replaceVideoTrack(peerConnections, videoTrack);

        // Handle stop
        videoTrack.onended = () => {
          handleToggleScreenShare();
        };

        if (wsConnection) {
          wsConnection.send(createWSMessage('screen-share-start', {}));
        }
      } catch (error) {
        console.error('Error starting screen share:', error);
      }
    }
  }, [isScreenSharing, screenStream, localStream, peerConnections, wsConnection]);

  const handleToggleRecording = useCallback(async () => {
    try {
      if (!isRecording) {
        await axios.post(`/api/v1/study-rooms/${roomId}/video/start-recording`);
        setIsRecording(true);
      } else {
        await axios.post(`/api/v1/study-rooms/${roomId}/video/stop-recording`);
        setIsRecording(false);
      }
    } catch (error) {
      console.error('Error toggling recording:', error);
    }
  }, [roomId, isRecording]);

  const handleLeave = useCallback(async () => {
    try {
      await axios.post(`/api/v1/study-rooms/${roomId}/video/leave`);
    } catch (error) {
      console.error('Error leaving conference:', error);
    }

    // Cleanup
    stopMediaStream(localStream);
    stopMediaStream(screenStream);
    closeAllPeerConnections(peerConnections);
    wsConnection?.close();

    onLeave();
  }, [roomId, localStream, screenStream, peerConnections, wsConnection, onLeave]);

  // ============================================================
  // Render
  // ============================================================

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        bgcolor: 'background.default',
      }}
      role="main"
      aria-label="Video konferans"
    >
      <VideoGrid
        localVideoRef={localVideoRef}
        screenShareRef={screenShareRef}
        remoteVideosRef={remoteVideosRef}
        participants={participants}
        currentUserName={currentUserName}
        isVideoEnabled={isVideoEnabled}
        isMuted={isMuted}
        isScreenSharing={isScreenSharing}
        screenStream={screenStream}
        pinnedParticipant={pinnedParticipant}
        onPinParticipant={setPinnedParticipant}
      />

      <MediaControls
        isMuted={isMuted}
        isVideoEnabled={isVideoEnabled}
        isScreenSharing={isScreenSharing}
        isRecording={isRecording}
        participantCount={participants.length + 1}
        onToggleMute={handleToggleMute}
        onToggleVideo={handleToggleVideo}
        onToggleScreenShare={handleToggleScreenShare}
        onToggleRecording={handleToggleRecording}
        onOpenParticipants={() => setParticipantsDialogOpen(true)}
        onLeave={handleLeave}
      />

      <ParticipantList
        open={participantsDialogOpen}
        onClose={() => setParticipantsDialogOpen(false)}
        participants={participants}
        currentUserName={currentUserName}
        isMuted={isMuted}
        isVideoEnabled={isVideoEnabled}
      />
    </Box>
  );
};

export default VideoConference;
