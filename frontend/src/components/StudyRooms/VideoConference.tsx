/**
 * VideoConference.tsx - Backward Compatibility Wrapper
 *
 * REFACTORED (2025-01-25):
 * Bu dosya artik sadece geriye uyumluluk icin bir wrapper.
 * Gercek implementasyon ./VideoConference/ dizininde.
 *
 * Yeni yapi:
 * - VideoConference/index.tsx - Barrel export
 * - VideoConference/VideoConference.tsx - Ana orchestrator
 * - VideoConference/VideoGrid.tsx - Video gorunumu
 * - VideoConference/MediaControls.tsx - Ses/video kontrolleri
 * - VideoConference/ScreenShare.tsx - Ekran paylasimi
 * - VideoConference/ParticipantList.tsx - Katilimci listesi
 * - VideoConference/types.ts - Shared type'lar
 * - VideoConference/lib/webrtcManager.ts - WebRTC utility
 *
 * @deprecated Import from './VideoConference' instead
 */

// Re-export everything from the new modular structure
export { default } from './VideoConference/index';
export * from './VideoConference/index';
