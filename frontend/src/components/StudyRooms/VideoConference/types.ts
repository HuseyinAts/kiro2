/**
 * VideoConference Types
 *
 * Shared TypeScript interfaces for video conference module.
 * All type definitions are centralized here for consistency.
 */

// ============================================================
// Participant Types
// ============================================================

export type ParticipantRole = 'host' | 'participant';

export interface Participant {
  id: string;
  user_id: string;
  name: string;
  avatar?: string;
  role: ParticipantRole;
  is_muted: boolean;
  is_video_enabled: boolean;
  is_screen_sharing: boolean;
  joined_at: string;
}

// ============================================================
// WebRTC Types
// ============================================================

export interface PeerConnection {
  userId: string;
  connection: RTCPeerConnection;
  stream?: MediaStream;
}

export interface RTCConfig {
  iceServers: RTCIceServer[];
}

// ============================================================
// WebSocket Message Types
// ============================================================

export type WebSocketMessageType =
  | 'user-joined'
  | 'user-left'
  | 'offer'
  | 'answer'
  | 'ice-candidate'
  | 'participants-update'
  | 'audio-toggle'
  | 'video-toggle'
  | 'screen-share-start'
  | 'screen-share-stop';

export interface WebSocketMessage {
  type: WebSocketMessageType;
  userId?: string;
  userName?: string;
  offer?: RTCSessionDescriptionInit;
  answer?: RTCSessionDescriptionInit;
  candidate?: RTCIceCandidateInit;
  participants?: Participant[];
  isMuted?: boolean;
  isVideoEnabled?: boolean;
}

// ============================================================
// Component Props Types
// ============================================================

export interface VideoConferenceProps {
  roomId: string;
  currentUserId: string;
  currentUserName: string;
  onLeave: () => void;
}

export interface VideoGridProps {
  localVideoRef: React.RefObject<HTMLVideoElement>;
  screenShareRef: React.RefObject<HTMLVideoElement>;
  remoteVideosRef: React.MutableRefObject<Map<string, HTMLVideoElement>>;
  participants: Participant[];
  currentUserName: string;
  isVideoEnabled: boolean;
  isMuted: boolean;
  isScreenSharing: boolean;
  screenStream: MediaStream | null;
  pinnedParticipant: string | null;
  onPinParticipant: (userId: string | null) => void;
}

export interface MediaControlsProps {
  isMuted: boolean;
  isVideoEnabled: boolean;
  isScreenSharing: boolean;
  isRecording: boolean;
  participantCount: number;
  onToggleMute: () => void;
  onToggleVideo: () => void;
  onToggleScreenShare: () => void;
  onToggleRecording: () => void;
  onOpenParticipants: () => void;
  onLeave: () => void;
}

export interface ScreenShareProps {
  screenShareRef: React.RefObject<HTMLVideoElement>;
  screenStream: MediaStream | null;
  isScreenSharing: boolean;
}

export interface ParticipantListProps {
  open: boolean;
  onClose: () => void;
  participants: Participant[];
  currentUserName: string;
  isMuted: boolean;
  isVideoEnabled: boolean;
}

// ============================================================
// WebRTC Manager Types
// ============================================================

export interface WebRTCManagerConfig {
  roomId: string;
  currentUserId: string;
  onParticipantsUpdate: (participants: Participant[]) => void;
  onPeerStreamReceived: (userId: string, stream: MediaStream) => void;
  onPeerDisconnected: (userId: string) => void;
}

export interface MediaConstraints {
  video: {
    width: { ideal: number };
    height: { ideal: number };
    facingMode: string;
  };
  audio: {
    echoCancellation: boolean;
    noiseSuppression: boolean;
    autoGainControl: boolean;
  };
}

// ============================================================
// Event Handler Types
// ============================================================

export type UserJoinedHandler = (userId: string, userName: string) => Promise<void>;
export type UserLeftHandler = (userId: string) => void;
export type OfferHandler = (userId: string, offer: RTCSessionDescriptionInit) => Promise<void>;
export type AnswerHandler = (userId: string, answer: RTCSessionDescriptionInit) => Promise<void>;
export type IceCandidateHandler = (userId: string, candidate: RTCIceCandidateInit) => Promise<void>;
