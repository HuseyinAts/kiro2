import { useCallback } from 'react';

export function useVideoKeyboard(
  togglePlay: () => void,
  toggleFullscreen: () => void,
  toggleMute: () => void,
  skipBackward: () => void,
  skipForward: () => void,
  showControlsTemporarily: () => void,
) {
  const handleKeyDown = useCallback((event: React.KeyboardEvent) => {
    switch (event.key.toLowerCase()) {
      case 'k':
      case ' ':
        event.preventDefault();
        togglePlay();
        showControlsTemporarily();
        break;
      case 'f':
        event.preventDefault();
        toggleFullscreen();
        break;
      case 'm':
        event.preventDefault();
        toggleMute();
        showControlsTemporarily();
        break;
      case 'j':
      case 'arrowleft':
        event.preventDefault();
        skipBackward();
        showControlsTemporarily();
        break;
      case 'l':
      case 'arrowright':
        event.preventDefault();
        skipForward();
        showControlsTemporarily();
        break;
      default:
        break;
    }
  }, [togglePlay, toggleFullscreen, toggleMute, skipBackward, skipForward, showControlsTemporarily]);

  return { handleKeyDown };
}
