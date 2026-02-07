import { useState, useEffect, RefObject } from 'react';

interface UseVideoPlayerOptions {
  autoplay?: boolean;
  initialVolume?: number;
  initialMuted?: boolean;
}

interface VideoPlayerState {
  isPlaying: boolean;
  isMuted: boolean;
  isFullscreen: boolean;
  currentTime: number;
  duration: number;
  volume: number;
  buffered: number;
  isLoading: boolean;
  error: string | null;
}

interface VideoPlayerControls {
  play: () => void;
  pause: () => void;
  togglePlayPause: () => void;
  seek: (time: number) => void;
  setVolume: (volume: number) => void;
  toggleMute: () => void;
  toggleFullscreen: () => void;
  skipForward: (seconds: number) => void;
  skipBackward: (seconds: number) => void;
}

export const useVideoPlayer = (
  videoRef: RefObject<HTMLVideoElement>,
  options: UseVideoPlayerOptions = {},
): [VideoPlayerState, VideoPlayerControls] => {
  const { autoplay = false, initialVolume = 1, initialMuted = false } = options;

  const [state, setState] = useState<VideoPlayerState>({
    isPlaying: autoplay,
    isMuted: initialMuted,
    isFullscreen: false,
    currentTime: 0,
    duration: 0,
    volume: initialVolume,
    buffered: 0,
    isLoading: true,
    error: null,
  });

  // Play video
  const play = () => {
    if (videoRef.current) {
      videoRef.current.play().catch(error => {
        setState(prev => ({ ...prev, error: error.message }));
      });
    }
  };

  // Pause video
  const pause = () => {
    if (videoRef.current) {
      videoRef.current.pause();
    }
  };

  // Toggle play/pause
  const togglePlayPause = () => {
    if (state.isPlaying) {
      pause();
    } else {
      play();
    }
  };

  // Seek to specific time
  const seek = (time: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = Math.max(0, Math.min(time, state.duration));
    }
  };

  // Set volume (0-1)
  const setVolume = (volume: number) => {
    if (videoRef.current) {
      const clampedVolume = Math.max(0, Math.min(1, volume));
      videoRef.current.volume = clampedVolume;
      setState(prev => ({ ...prev, volume: clampedVolume, isMuted: clampedVolume === 0 }));
    }
  };

  // Toggle mute
  const toggleMute = () => {
    if (videoRef.current) {
      const newMuted = !state.isMuted;
      videoRef.current.muted = newMuted;
      setState(prev => ({ ...prev, isMuted: newMuted }));
    }
  };

  // Toggle fullscreen
  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      videoRef.current?.requestFullscreen().catch(error => {
        setState(prev => ({ ...prev, error: `Fullscreen error: ${error.message}` }));
      });
    } else {
      document.exitFullscreen();
    }
  };

  // Skip forward
  const skipForward = (seconds: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = Math.min(
        state.duration,
        videoRef.current.currentTime + seconds,
      );
    }
  };

  // Skip backward
  const skipBackward = (seconds: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = Math.max(0, videoRef.current.currentTime - seconds);
    }
  };

  // Event handlers
  useEffect(() => {
    const video = videoRef.current;
    if (!video) {return;}

    const handlePlay = () => setState(prev => ({ ...prev, isPlaying: true }));
    const handlePause = () => setState(prev => ({ ...prev, isPlaying: false }));
    const handleTimeUpdate = () =>
      setState(prev => ({ ...prev, currentTime: video.currentTime }));
    const handleDurationChange = () =>
      setState(prev => ({ ...prev, duration: video.duration, isLoading: false }));
    const handleVolumeChange = () =>
      setState(prev => ({ ...prev, volume: video.volume, isMuted: video.muted }));
    const handleProgress = () => {
      if (video.buffered.length > 0) {
        const bufferedEnd = video.buffered.end(video.buffered.length - 1);
        const bufferedPercent = (bufferedEnd / video.duration) * 100;
        setState(prev => ({ ...prev, buffered: bufferedPercent }));
      }
    };
    const handleLoadStart = () => setState(prev => ({ ...prev, isLoading: true }));
    const handleLoadedData = () => setState(prev => ({ ...prev, isLoading: false }));
    const handleError = () =>
      setState(prev => ({ ...prev, error: 'Video yüklenirken hata oluştu' }));
    const handleFullscreenChange = () =>
      setState(prev => ({ ...prev, isFullscreen: !!document.fullscreenElement }));

    video.addEventListener('play', handlePlay);
    video.addEventListener('pause', handlePause);
    video.addEventListener('timeupdate', handleTimeUpdate);
    video.addEventListener('durationchange', handleDurationChange);
    video.addEventListener('volumechange', handleVolumeChange);
    video.addEventListener('progress', handleProgress);
    video.addEventListener('loadstart', handleLoadStart);
    video.addEventListener('loadeddata', handleLoadedData);
    video.addEventListener('error', handleError);
    document.addEventListener('fullscreenchange', handleFullscreenChange);

    // Set initial volume and muted state
    video.volume = initialVolume;
    video.muted = initialMuted;

    return () => {
      video.removeEventListener('play', handlePlay);
      video.removeEventListener('pause', handlePause);
      video.removeEventListener('timeupdate', handleTimeUpdate);
      video.removeEventListener('durationchange', handleDurationChange);
      video.removeEventListener('volumechange', handleVolumeChange);
      video.removeEventListener('progress', handleProgress);
      video.removeEventListener('loadstart', handleLoadStart);
      video.removeEventListener('loadeddata', handleLoadedData);
      video.removeEventListener('error', handleError);
      document.removeEventListener('fullscreenchange', handleFullscreenChange);
    };
  }, [videoRef, initialVolume, initialMuted]);

  const controls: VideoPlayerControls = {
    play,
    pause,
    togglePlayPause,
    seek,
    setVolume,
    toggleMute,
    toggleFullscreen,
    skipForward,
    skipBackward,
  };

  return [state, controls];
};

export default useVideoPlayer;
