import { useState, useCallback } from 'react';

export function useVideoFullscreen(containerRef: React.RefObject<HTMLDivElement>, announce: (message: string, priority?: 'assertive' | 'polite') => void) {
  const [isFullscreen, setIsFullscreen] = useState(false);

  const toggleFullscreen = useCallback(() => {
    if (!document.fullscreenElement) {
      containerRef.current?.requestFullscreen();
      setIsFullscreen(true);
      announce('Tam ekran moduna geçildi', 'polite');
    } else {
      document.exitFullscreen();
      setIsFullscreen(false);
      announce('Tam ekran modundan çıkıldı', 'polite');
    }
  }, [containerRef, announce]);

  return { isFullscreen, setIsFullscreen, toggleFullscreen };
}
