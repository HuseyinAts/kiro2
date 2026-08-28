import { useState, useCallback } from 'react';

export function useVideoCaptions(videoRef: React.RefObject<HTMLVideoElement>, announce: (message: string, priority?: 'assertive' | 'polite') => void) {
  const [activeTrack, setActiveTrack] = useState<string | null>(null);
  const [showCaptions, setShowCaptions] = useState(false);
  const [showTranscript, setShowTranscript] = useState(false);
  const [transcript, setTranscript] = useState<string>('');

  const toggleCaptions = useCallback(() => {
    const newShowCaptions = !showCaptions;
    setShowCaptions(newShowCaptions);

    if (videoRef.current) {
      const textTracks = videoRef.current.textTracks;
      for (let i = 0; i < textTracks.length; i++) {
        textTracks[i].mode = newShowCaptions && textTracks[i].id === activeTrack ? 'showing' : 'hidden';
      }
      announce(newShowCaptions ? 'Altyazılar açıldı' : 'Altyazılar kapatıldı', 'polite');
    }
  }, [showCaptions, activeTrack, videoRef, announce]);

  const selectTrack = useCallback((trackId: string) => {
    setActiveTrack(trackId);
    if (videoRef.current && showCaptions) {
      const textTracks = videoRef.current.textTracks;
      for (let i = 0; i < textTracks.length; i++) {
        textTracks[i].mode = textTracks[i].id === trackId ? 'showing' : 'hidden';
      }
      announce('Altyazı dili değiştirildi', 'polite');
    }
  }, [showCaptions, videoRef, announce]);

  return {
    activeTrack, setActiveTrack,
    showCaptions, setShowCaptions,
    showTranscript, setShowTranscript,
    transcript, setTranscript,
    toggleCaptions, selectTrack
  };
}
