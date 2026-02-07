/**
 * WebRTC Manager
 *
 * Handles WebRTC connection management, peer connections,
 * ICE candidate exchange, and media stream handling.
 */

import type {
  PeerConnection,
  RTCConfig,
  MediaConstraints,
  WebSocketMessage,
} from '../types';
import { config } from '@/config';

// ============================================================
// Default Configuration
// ============================================================

export const DEFAULT_RTC_CONFIG: RTCConfig = {
  iceServers: [
    { urls: 'stun:stun.l.google.com:19302' },
    { urls: 'stun:stun1.l.google.com:19302' },
  ],
};

export const DEFAULT_MEDIA_CONSTRAINTS: MediaConstraints = {
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
};

// ============================================================
// Media Stream Functions
// ============================================================

/**
 * Initialize local media stream (camera + microphone)
 */
export async function initializeLocalStream(
  constraints: MediaConstraints = DEFAULT_MEDIA_CONSTRAINTS,
): Promise<MediaStream> {
  try {
    const stream = await navigator.mediaDevices.getUserMedia(constraints);
    return stream;
  } catch (error) {
    console.error('Error accessing media devices:', error);
    throw new Error('Kamera veya mikrofona erisim saglanamadi. Lutfen izinleri kontrol edin.');
  }
}

/**
 * Start screen sharing
 */
export async function startScreenCapture(): Promise<MediaStream> {
  try {
    const stream = await navigator.mediaDevices.getDisplayMedia({
      video: {
        cursor: 'always',
      } as MediaTrackConstraints,
      audio: false,
    });
    return stream;
  } catch (error) {
    console.error('Error starting screen share:', error);
    throw new Error('Ekran paylasimi baslatilamadi.');
  }
}

/**
 * Stop all tracks in a media stream
 */
export function stopMediaStream(stream: MediaStream | null): void {
  if (stream) {
    stream.getTracks().forEach((track) => track.stop());
  }
}

/**
 * Toggle audio tracks in a stream
 */
export function toggleAudioTracks(stream: MediaStream, enabled: boolean): void {
  stream.getAudioTracks().forEach((track) => {
    track.enabled = enabled;
  });
}

/**
 * Toggle video tracks in a stream
 */
export function toggleVideoTracks(stream: MediaStream, enabled: boolean): void {
  stream.getVideoTracks().forEach((track) => {
    track.enabled = enabled;
  });
}

// ============================================================
// Peer Connection Functions
// ============================================================

/**
 * Create a new RTCPeerConnection with the given configuration
 */
export function createPeerConnection(
  config: RTCConfiguration = DEFAULT_RTC_CONFIG,
): RTCPeerConnection {
  return new RTCPeerConnection(config);
}

/**
 * Add local stream tracks to a peer connection
 */
export function addStreamToPeerConnection(
  peerConnection: RTCPeerConnection,
  stream: MediaStream,
): void {
  stream.getTracks().forEach((track) => {
    peerConnection.addTrack(track, stream);
  });
}

/**
 * Replace video track in all peer connections (for screen sharing)
 */
export function replaceVideoTrack(
  peerConnections: Map<string, PeerConnection>,
  newTrack: MediaStreamTrack,
): void {
  peerConnections.forEach((pc) => {
    const sender = pc.connection.getSenders().find((s) => s.track?.kind === 'video');
    if (sender) {
      sender.replaceTrack(newTrack);
    }
  });
}

/**
 * Close a peer connection and clean up
 */
export function closePeerConnection(peerConnection: RTCPeerConnection): void {
  peerConnection.close();
}

/**
 * Close all peer connections
 */
export function closeAllPeerConnections(
  peerConnections: Map<string, PeerConnection>,
): void {
  peerConnections.forEach((pc) => {
    pc.connection.close();
  });
}

// ============================================================
// Signaling Functions
// ============================================================

/**
 * Create and return an SDP offer
 */
export async function createOffer(
  peerConnection: RTCPeerConnection,
): Promise<RTCSessionDescriptionInit> {
  const offer = await peerConnection.createOffer();
  await peerConnection.setLocalDescription(offer);
  return offer;
}

/**
 * Create and return an SDP answer
 */
export async function createAnswer(
  peerConnection: RTCPeerConnection,
  offer: RTCSessionDescriptionInit,
): Promise<RTCSessionDescriptionInit> {
  await peerConnection.setRemoteDescription(new RTCSessionDescription(offer));
  const answer = await peerConnection.createAnswer();
  await peerConnection.setLocalDescription(answer);
  return answer;
}

/**
 * Set remote description (answer) on peer connection
 */
export async function setRemoteAnswer(
  peerConnection: RTCPeerConnection,
  answer: RTCSessionDescriptionInit,
): Promise<void> {
  await peerConnection.setRemoteDescription(new RTCSessionDescription(answer));
}

/**
 * Add ICE candidate to peer connection
 */
export async function addIceCandidate(
  peerConnection: RTCPeerConnection,
  candidate: RTCIceCandidateInit,
): Promise<void> {
  await peerConnection.addIceCandidate(new RTCIceCandidate(candidate));
}

// ============================================================
// WebSocket Message Helpers
// ============================================================

/**
 * Create a WebSocket message object
 */
export function createWSMessage(
  type: WebSocketMessage['type'],
  payload: Partial<WebSocketMessage> = {},
): string {
  return JSON.stringify({ type, ...payload });
}

/**
 * Parse incoming WebSocket message
 */
export function parseWSMessage(data: string): WebSocketMessage {
  return JSON.parse(data);
}

// ============================================================
// Connection Setup Helpers
// ============================================================

/**
 * Setup peer connection with all necessary event handlers
 */
export function setupPeerConnection(
  config: RTCConfiguration,
  localStream: MediaStream | null,
  onTrack: (event: RTCTrackEvent) => void,
  onIceCandidate: (event: RTCPeerConnectionIceEvent) => void,
): RTCPeerConnection {
  const peerConnection = createPeerConnection(config);

  // Add local stream tracks
  if (localStream) {
    addStreamToPeerConnection(peerConnection, localStream);
  }

  // Setup event handlers
  peerConnection.ontrack = onTrack;
  peerConnection.onicecandidate = onIceCandidate;

  return peerConnection;
}

/**
 * Get WebSocket URL for video conference
 */
export function getWebSocketUrl(roomId: string, baseUrl?: string): string {
  const wsUrl = baseUrl ?? config.api.wsURL;
  return `${wsUrl}/ws/study-rooms/${roomId}/video`;
}
