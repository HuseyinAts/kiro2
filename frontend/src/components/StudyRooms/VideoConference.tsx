/**
 * Task 109.5: Video Conference Client
 *
 * WebRTC-based video conferencing with screen sharing.
 * Supports multiple participants, audio/video controls, and screen sharing.
 */

import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import {
  Box,
  Paper,
  IconButton,
  Typography,
  Avatar,
  Tooltip,
  Grid,
  Badge,
  Dialog,
  DialogTitle,
  DialogContent,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  Chip,
  Button,
} from '@mui/material';
import {
  Videocam as VideocamIcon,
  VideocamOff as VideocamOffIcon,
  Mic as MicIcon,
  MicOff as MicOffIcon,
  ScreenShare as ScreenShareIcon,
  StopScreenShare as StopScreenShareIcon,
  CallEnd as CallEndIcon,
  PeopleAlt as PeopleAltIcon,
  Settings as SettingsIcon,
  MoreVert as MoreVertIcon,
  PushPin as PushPinIcon,
  FiberManualRecord as RecordIcon,
} from '@mui/icons-material';

// ============================================================
// Types
// ============================================================

interface Participant {
  id: string;
  user_id: string;
  name: string;
  avatar?: string;
  role: 'host' | 'participant';
  is_muted: boolean;
  is_video_enabled: boolean;
  is_screen_sharing: boolean;
  joined_at: string;
}

interface VideoConferenceProps {
  roomId: string;
  currentUserId: string;
  currentUserName: string;
  onLeave: () => void;
}

interface PeerConnection {
  userId: string;
  connection: RTCPeerConnection;
  stream?: MediaStream;
}

// ============================================================
// Component
// ============================================================

const VideoConference: React.FC<VideoConferenceProps> = ({
  roomId,
  currentUserId,
  currentUserName,
  onLeave,
}) => {
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

  const localVideoRef = useRef<HTMLVideoElement>(null);
  const screenShareRef = useRef<HTMLVideoElement>(null);
  const remoteVideosRef = useRef<Map<string, HTMLVideoElement>>(new Map());

  // WebRTC Configuration
  const rtcConfig: RTCConfiguration = {
    iceServers: [
      { urls: 'stun:stun.l.google.com:19302' },
      { urls: 'stun:stun1.l.google.com:19302' },
    ],
  };

  useEffect(() => {
    initializeMedia();
    connectWebSocket();

    return () => {
      cleanup();
    };
  }, []);

  const initializeMedia = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 1280 },
          height: { ideal: 720 },
          facingMode: 'user',
        },
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });

      setLocalStream(stream);

      if (localVideoRef.current) {
        localVideoRef.current.srcObject = stream;
      }

      // Notify server that we joined
      await axios.post(`/api/study-rooms/${roomId}/video/join`, {
        user_id: currentUserId,
        name: currentUserName,
      });
    } catch (error) {
      console.error('Error accessing media devices:', error);
      alert('Kamera veya mikrofona erişim sağlanamadı. Lütfen izinleri kontrol edin.');
    }
  };

  const connectWebSocket = () => {
    const wsUrl = `ws://localhost:8000/ws/study-rooms/${roomId}/video`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('WebSocket connected for video conference');
      setWsConnection(ws);
    };

    ws.onmessage = async (event) => {
      const message = JSON.parse(event.data);

      switch (message.type) {
        case 'user-joined':
          await handleUserJoined(message.userId, message.userName);
          break;
        case 'user-left':
          handleUserLeft(message.userId);
          break;
        case 'offer':
          await handleOffer(message.userId, message.offer);
          break;
        case 'answer':
          await handleAnswer(message.userId, message.answer);
          break;
        case 'ice-candidate':
          await handleIceCandidate(message.userId, message.candidate);
          break;
        case 'participants-update':
          setParticipants(message.participants);
          break;
        default:
          console.log('Unknown message type:', message.type);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
    };
  };

  const handleUserJoined = async (userId: string, userName: string) => {
    if (userId === currentUserId) return;

    // Create peer connection for new user
    const peerConnection = new RTCPeerConnection(rtcConfig);

    // Add local stream tracks to peer connection
    if (localStream) {
      localStream.getTracks().forEach((track) => {
        peerConnection.addTrack(track, localStream);
      });
    }

    // Handle incoming stream
    peerConnection.ontrack = (event) => {
      const remoteVideo = remoteVideosRef.current.get(userId);
      if (remoteVideo) {
        remoteVideo.srcObject = event.streams[0];
      }
    };

    // Handle ICE candidates
    peerConnection.onicecandidate = (event) => {
      if (event.candidate && wsConnection) {
        wsConnection.send(
          JSON.stringify({
            type: 'ice-candidate',
            userId: userId,
            candidate: event.candidate,
          })
        );
      }
    };

    // Create and send offer
    const offer = await peerConnection.createOffer();
    await peerConnection.setLocalDescription(offer);

    if (wsConnection) {
      wsConnection.send(
        JSON.stringify({
          type: 'offer',
          userId: userId,
          offer: offer,
        })
      );
    }

    // Store peer connection
    setPeerConnections((prev) => {
      const newMap = new Map(prev);
      newMap.set(userId, { userId, connection: peerConnection });
      return newMap;
    });
  };

  const handleUserLeft = (userId: string) => {
    // Close peer connection
    const pc = peerConnections.get(userId);
    if (pc) {
      pc.connection.close();
      setPeerConnections((prev) => {
        const newMap = new Map(prev);
        newMap.delete(userId);
        return newMap;
      });
    }

    // Remove from participants
    setParticipants((prev) => prev.filter((p) => p.user_id !== userId));
  };

  const handleOffer = async (userId: string, offer: RTCSessionDescriptionInit) => {
    const peerConnection = new RTCPeerConnection(rtcConfig);

    // Add local stream
    if (localStream) {
      localStream.getTracks().forEach((track) => {
        peerConnection.addTrack(track, localStream);
      });
    }

    // Handle incoming stream
    peerConnection.ontrack = (event) => {
      const remoteVideo = remoteVideosRef.current.get(userId);
      if (remoteVideo) {
        remoteVideo.srcObject = event.streams[0];
      }
    };

    // Handle ICE candidates
    peerConnection.onicecandidate = (event) => {
      if (event.candidate && wsConnection) {
        wsConnection.send(
          JSON.stringify({
            type: 'ice-candidate',
            userId: userId,
            candidate: event.candidate,
          })
        );
      }
    };

    // Set remote description and create answer
    await peerConnection.setRemoteDescription(new RTCSessionDescription(offer));
    const answer = await peerConnection.createAnswer();
    await peerConnection.setLocalDescription(answer);

    // Send answer
    if (wsConnection) {
      wsConnection.send(
        JSON.stringify({
          type: 'answer',
          userId: userId,
          answer: answer,
        })
      );
    }

    // Store peer connection
    setPeerConnections((prev) => {
      const newMap = new Map(prev);
      newMap.set(userId, { userId, connection: peerConnection });
      return newMap;
    });
  };

  const handleAnswer = async (userId: string, answer: RTCSessionDescriptionInit) => {
    const pc = peerConnections.get(userId);
    if (pc) {
      await pc.connection.setRemoteDescription(new RTCSessionDescription(answer));
    }
  };

  const handleIceCandidate = async (userId: string, candidate: RTCIceCandidateInit) => {
    const pc = peerConnections.get(userId);
    if (pc) {
      await pc.connection.addIceCandidate(new RTCIceCandidate(candidate));
    }
  };

  const toggleMute = () => {
    if (localStream) {
      localStream.getAudioTracks().forEach((track) => {
        track.enabled = !track.enabled;
      });
      setIsMuted(!isMuted);

      // Notify other participants
      if (wsConnection) {
        wsConnection.send(
          JSON.stringify({
            type: 'audio-toggle',
            isMuted: !isMuted,
          })
        );
      }
    }
  };

  const toggleVideo = () => {
    if (localStream) {
      localStream.getVideoTracks().forEach((track) => {
        track.enabled = !track.enabled;
      });
      setIsVideoEnabled(!isVideoEnabled);

      // Notify other participants
      if (wsConnection) {
        wsConnection.send(
          JSON.stringify({
            type: 'video-toggle',
            isVideoEnabled: !isVideoEnabled,
          })
        );
      }
    }
  };

  const startScreenShare = async () => {
    try {
      const stream = await navigator.mediaDevices.getDisplayMedia({
        video: {
          cursor: 'always',
        },
        audio: false,
      });

      setScreenStream(stream);
      setIsScreenSharing(true);

      if (screenShareRef.current) {
        screenShareRef.current.srcObject = stream;
      }

      // Replace video track in all peer connections
      const videoTrack = stream.getVideoTracks()[0];
      peerConnections.forEach((pc) => {
        const sender = pc.connection.getSenders().find((s) => s.track?.kind === 'video');
        if (sender) {
          sender.replaceTrack(videoTrack);
        }
      });

      // Handle screen share stop
      videoTrack.onended = () => {
        stopScreenShare();
      };

      // Notify other participants
      if (wsConnection) {
        wsConnection.send(
          JSON.stringify({
            type: 'screen-share-start',
          })
        );
      }
    } catch (error) {
      console.error('Error starting screen share:', error);
    }
  };

  const stopScreenShare = () => {
    if (screenStream) {
      screenStream.getTracks().forEach((track) => track.stop());
      setScreenStream(null);
      setIsScreenSharing(false);

      // Restore camera video in all peer connections
      if (localStream) {
        const videoTrack = localStream.getVideoTracks()[0];
        peerConnections.forEach((pc) => {
          const sender = pc.connection.getSenders().find((s) => s.track?.kind === 'video');
          if (sender) {
            sender.replaceTrack(videoTrack);
          }
        });
      }

      // Notify other participants
      if (wsConnection) {
        wsConnection.send(
          JSON.stringify({
            type: 'screen-share-stop',
          })
        );
      }
    }
  };

  const toggleRecording = async () => {
    if (!isRecording) {
      try {
        await axios.post(`/api/study-rooms/${roomId}/video/start-recording`);
        setIsRecording(true);
      } catch (error) {
        console.error('Error starting recording:', error);
      }
    } else {
      try {
        await axios.post(`/api/study-rooms/${roomId}/video/stop-recording`);
        setIsRecording(false);
      } catch (error) {
        console.error('Error stopping recording:', error);
      }
    }
  };

  const handleLeave = async () => {
    try {
      await axios.post(`/api/study-rooms/${roomId}/video/leave`);
      cleanup();
      onLeave();
    } catch (error) {
      console.error('Error leaving conference:', error);
    }
  };

  const cleanup = () => {
    // Stop local stream
    if (localStream) {
      localStream.getTracks().forEach((track) => track.stop());
    }

    // Stop screen share
    if (screenStream) {
      screenStream.getTracks().forEach((track) => track.stop());
    }

    // Close all peer connections
    peerConnections.forEach((pc) => {
      pc.connection.close();
    });

    // Close WebSocket
    if (wsConnection) {
      wsConnection.close();
    }
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%', bgcolor: 'background.default' }}>
      {/* Video Grid */}
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
                  label="Ekran Paylaşımı"
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
                height: isScreenSharing ? 200 : 400,
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
                <Avatar
                  sx={{
                    position: 'absolute',
                    top: '50%',
                    left: '50%',
                    transform: 'translate(-50%, -50%)',
                    width: 80,
                    height: 80,
                    bgcolor: 'primary.main',
                    fontSize: 32,
                  }}
                >
                  {currentUserName.charAt(0).toUpperCase()}
                </Avatar>
              )}
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
                  label={currentUserName + ' (Ben)'}
                  size="small"
                  sx={{ bgcolor: 'rgba(0,0,0,0.6)', color: 'white' }}
                />
                {isMuted && <MicOffIcon sx={{ color: 'error.main' }} />}
              </Box>
            </Paper>
          </Grid>

          {/* Remote Videos */}
          {participants.map((participant) => (
            <Grid item xs={12} md={pinnedParticipant === participant.user_id ? 9 : 6} key={participant.user_id}>
              <Paper
                sx={{
                  position: 'relative',
                  height: isScreenSharing ? 200 : 400,
                  bgcolor: 'black',
                  overflow: 'hidden',
                }}
              >
                <video
                  ref={(el) => {
                    if (el) remoteVideosRef.current.set(participant.user_id, el);
                  }}
                  autoPlay
                  playsInline
                  style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                />
                {!participant.is_video_enabled && (
                  <Avatar
                    src={participant.avatar}
                    sx={{
                      position: 'absolute',
                      top: '50%',
                      left: '50%',
                      transform: 'translate(-50%, -50%)',
                      width: 80,
                      height: 80,
                      bgcolor: 'secondary.main',
                      fontSize: 32,
                    }}
                  >
                    {participant.name.charAt(0).toUpperCase()}
                  </Avatar>
                )}
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
                    label={participant.name}
                    size="small"
                    sx={{ bgcolor: 'rgba(0,0,0,0.6)', color: 'white' }}
                  />
                  {participant.is_muted && <MicOffIcon sx={{ color: 'error.main' }} />}
                  {participant.is_screen_sharing && <ScreenShareIcon sx={{ color: 'primary.main' }} />}
                </Box>
                <IconButton
                  size="small"
                  onClick={() => setPinnedParticipant(pinnedParticipant === participant.user_id ? null : participant.user_id)}
                  sx={{ position: 'absolute', top: 8, right: 8, color: 'white', bgcolor: 'rgba(0,0,0,0.4)' }}
                >
                  <PushPinIcon fontSize="small" />
                </IconButton>
              </Paper>
            </Grid>
          ))}
        </Grid>
      </Box>

      {/* Controls */}
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
      >
        <Tooltip title={isMuted ? 'Mikrofonu Aç' : 'Mikrofonu Kapat'}>
          <IconButton
            onClick={toggleMute}
            sx={{
              bgcolor: isMuted ? 'error.main' : 'action.hover',
              color: isMuted ? 'white' : 'text.primary',
              '&:hover': { bgcolor: isMuted ? 'error.dark' : 'action.selected' },
            }}
          >
            {isMuted ? <MicOffIcon /> : <MicIcon />}
          </IconButton>
        </Tooltip>

        <Tooltip title={isVideoEnabled ? 'Kamerayı Kapat' : 'Kamerayı Aç'}>
          <IconButton
            onClick={toggleVideo}
            sx={{
              bgcolor: !isVideoEnabled ? 'error.main' : 'action.hover',
              color: !isVideoEnabled ? 'white' : 'text.primary',
              '&:hover': { bgcolor: !isVideoEnabled ? 'error.dark' : 'action.selected' },
            }}
          >
            {isVideoEnabled ? <VideocamIcon /> : <VideocamOffIcon />}
          </IconButton>
        </Tooltip>

        <Tooltip title={isScreenSharing ? 'Ekran Paylaşımını Durdur' : 'Ekran Paylaş'}>
          <IconButton
            onClick={isScreenSharing ? stopScreenShare : startScreenShare}
            sx={{
              bgcolor: isScreenSharing ? 'primary.main' : 'action.hover',
              color: isScreenSharing ? 'white' : 'text.primary',
            }}
          >
            {isScreenSharing ? <StopScreenShareIcon /> : <ScreenShareIcon />}
          </IconButton>
        </Tooltip>

        <Tooltip title={isRecording ? 'Kaydı Durdur' : 'Kayıt Başlat'}>
          <IconButton
            onClick={toggleRecording}
            sx={{
              bgcolor: isRecording ? 'error.main' : 'action.hover',
              color: isRecording ? 'white' : 'text.primary',
            }}
          >
            <RecordIcon />
          </IconButton>
        </Tooltip>

        <Tooltip title="Katılımcılar">
          <Badge badgeContent={participants.length + 1} color="primary">
            <IconButton onClick={() => setParticipantsDialogOpen(true)}>
              <PeopleAltIcon />
            </IconButton>
          </Badge>
        </Tooltip>

        <Box sx={{ flex: 1 }} />

        <Tooltip title="Aramayı Bitir">
          <IconButton
            onClick={handleLeave}
            sx={{
              bgcolor: 'error.main',
              color: 'white',
              '&:hover': { bgcolor: 'error.dark' },
            }}
          >
            <CallEndIcon />
          </IconButton>
        </Tooltip>
      </Paper>

      {/* Participants Dialog */}
      <Dialog
        open={participantsDialogOpen}
        onClose={() => setParticipantsDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          Katılımcılar ({participants.length + 1})
        </DialogTitle>
        <DialogContent>
          <List>
            {/* Current User */}
            <ListItem>
              <ListItemAvatar>
                <Avatar>{currentUserName.charAt(0).toUpperCase()}</Avatar>
              </ListItemAvatar>
              <ListItemText
                primary={`${currentUserName} (Ben)`}
                secondary={
                  <Box component="span" sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                    {isMuted ? <MicOffIcon fontSize="small" /> : <MicIcon fontSize="small" />}
                    {isVideoEnabled ? <VideocamIcon fontSize="small" /> : <VideocamOffIcon fontSize="small" />}
                  </Box>
                }
              />
            </ListItem>

            {/* Other Participants */}
            {participants.map((participant) => (
              <ListItem key={participant.user_id}>
                <ListItemAvatar>
                  <Avatar src={participant.avatar}>
                    {participant.name.charAt(0).toUpperCase()}
                  </Avatar>
                </ListItemAvatar>
                <ListItemText
                  primary={participant.name}
                  secondary={
                    <Box component="span" sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                      {participant.is_muted ? <MicOffIcon fontSize="small" /> : <MicIcon fontSize="small" />}
                      {participant.is_video_enabled ? (
                        <VideocamIcon fontSize="small" />
                      ) : (
                        <VideocamOffIcon fontSize="small" />
                      )}
                      {participant.role === 'host' && (
                        <Chip label="Host" size="small" color="primary" />
                      )}
                    </Box>
                  }
                />
              </ListItem>
            ))}
          </List>
        </DialogContent>
      </Dialog>
    </Box>
  );
};

export default VideoConference;
