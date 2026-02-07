/**
 * VideoConference Module - Barrel Export
 *
 * Re-exports all video conference components and utilities.
 * Import from this index for clean module access.
 */

// Main orchestrator component
export { default } from './VideoConference';
export { default as VideoConference } from './VideoConference';

// Sub-components
export { default as VideoGrid } from './VideoGrid';
export { default as MediaControls } from './MediaControls';
export { default as ParticipantList } from './ParticipantList';
export {
  default as ScreenShare,
  RemoteScreenShareIndicator,
  ScreenSharePreview,
} from './ScreenShare';

// Types
export type {
  // Participant types
  Participant,
  ParticipantRole,
  // WebRTC types
  PeerConnection,
  RTCConfig,
  // WebSocket types
  WebSocketMessage,
  WebSocketMessageType,
  // Component props
  VideoConferenceProps,
  VideoGridProps,
  MediaControlsProps,
  ScreenShareProps,
  ParticipantListProps,
  // WebRTC manager types
  WebRTCManagerConfig,
  MediaConstraints,
  // Event handler types
  UserJoinedHandler,
  UserLeftHandler,
  OfferHandler,
  AnswerHandler,
  IceCandidateHandler,
} from './types';

// WebRTC utilities
export {
  DEFAULT_RTC_CONFIG,
  DEFAULT_MEDIA_CONSTRAINTS,
  initializeLocalStream,
  startScreenCapture,
  stopMediaStream,
  toggleAudioTracks,
  toggleVideoTracks,
  createPeerConnection,
  addStreamToPeerConnection,
  replaceVideoTrack,
  closePeerConnection,
  closeAllPeerConnections,
  createOffer,
  createAnswer,
  setRemoteAnswer,
  addIceCandidate,
  createWSMessage,
  parseWSMessage,
  setupPeerConnection,
  getWebSocketUrl,
} from './lib/webrtcManager';
