/**
 * EBA TV Video Player Bileşeni
 * 
 * TRT EBA TV videolarını oynatmak için özel video player.
 */

import React, { useState, useRef, useEffect } from 'react';
import { Play, Pause, Volume2, VolumeX, Maximize, Settings, SkipBack, SkipForward } from 'lucide-react';

interface EbaTVVideoPlayerProps {
  videoUrl: string;
  title: string;
  duration: number;
  thumbnail?: string;
  subtitles?: boolean;
  onProgress?: (progress: number) => void;
  onComplete?: () => void;
  onTimeUpdate?: (currentTime: number, totalTime: number) => void;
}

interface VideoProgress {
  currentTime: number;
  duration: number;
  buffered: number;
  played: number;
}

export const EbaTVVideoPlayer: React.FC<EbaTVVideoPlayerProps> = ({
  videoUrl,
  title,
  duration,
  thumbnail,
  subtitles = false,
  onProgress,
  onComplete,
  onTimeUpdate
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [volume, setVolume] = useState(1);
  const [progress, setProgress] = useState<VideoProgress>({
    currentTime: 0,
    duration: 0,
    buffered: 0,
    played: 0
  });
  const [showControls, setShowControls] = useState(true);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [playbackRate, setPlaybackRate] = useState(1);
  const [showSettings, setShowSettings] = useState(false);

  // Video kontrolleri
  const togglePlay = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause();
      } else {
        videoRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const toggleMute = () => {
    if (videoRef.current) {
      videoRef.current.muted = !isMuted;
      setIsMuted(!isMuted);
    }
  };

  const handleVolumeChange = (newVolume: number) => {
    if (videoRef.current) {
      videoRef.current.volume = newVolume;
      setVolume(newVolume);
      setIsMuted(newVolume === 0);
    }
  };

  const handleSeek = (seekTime: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = seekTime;
    }
  };

  const skipForward = () => {
    if (videoRef.current) {
      videoRef.current.currentTime = Math.min(
        videoRef.current.currentTime + 10,
        videoRef.current.duration
      );
    }
  };

  const skipBackward = () => {
    if (videoRef.current) {
      videoRef.current.currentTime = Math.max(
        videoRef.current.currentTime - 10,
        0
      );
    }
  };

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      videoRef.current?.requestFullscreen();
      setIsFullscreen(true);
    } else {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  };

  const changePlaybackRate = (rate: number) => {
    if (videoRef.current) {
      videoRef.current.playbackRate = rate;
      setPlaybackRate(rate);
      setShowSettings(false);
    }
  };

  // Video event handlers
  const handleTimeUpdate = () => {
    if (videoRef.current) {
      const currentTime = videoRef.current.currentTime;
      const duration = videoRef.current.duration;
      const buffered = videoRef.current.buffered.length > 0 
        ? videoRef.current.buffered.end(0) 
        : 0;
      const played = (currentTime / duration) * 100;

      const newProgress = {
        currentTime,
        duration,
        buffered,
        played
      };

      setProgress(newProgress);
      
      // Callback'leri çağır
      onProgress?.(played);
      onTimeUpdate?.(currentTime, duration);
    }
  };

  const handleVideoEnd = () => {
    setIsPlaying(false);
    onComplete?.();
  };

  const handleLoadedMetadata = () => {
    if (videoRef.current) {
      setProgress(prev => ({
        ...prev,
        duration: videoRef.current!.duration
      }));
    }
  };

  // Zaman formatı
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Kontrol görünürlüğü
  useEffect(() => {
    let timeout: NodeJS.Timeout;
    
    const resetTimeout = () => {
      clearTimeout(timeout);
      setShowControls(true);
      timeout = setTimeout(() => {
        if (isPlaying) {
          setShowControls(false);
        }
      }, 3000);
    };

    resetTimeout();
    
    return () => clearTimeout(timeout);
  }, [isPlaying]);

  // Klavye kısayolları
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      switch (e.code) {
        case 'Space':
          e.preventDefault();
          togglePlay();
          break;
        case 'ArrowLeft':
          e.preventDefault();
          skipBackward();
          break;
        case 'ArrowRight':
          e.preventDefault();
          skipForward();
          break;
        case 'KeyM':
          e.preventDefault();
          toggleMute();
          break;
        case 'KeyF':
          e.preventDefault();
          toggleFullscreen();
          break;
      }
    };

    document.addEventListener('keydown', handleKeyPress);
    return () => document.removeEventListener('keydown', handleKeyPress);
  }, []);

  return (
    <div className="relative bg-black rounded-lg overflow-hidden group">
      {/* Video Element */}
      <video
        ref={videoRef}
        src={videoUrl}
        poster={thumbnail}
        className="w-full h-auto"
        onTimeUpdate={handleTimeUpdate}
        onEnded={handleVideoEnd}
        onLoadedMetadata={handleLoadedMetadata}
        onMouseMove={() => setShowControls(true)}
        crossOrigin="anonymous"
      >
        {subtitles && (
          <track
            kind="subtitles"
            src={`${videoUrl}.vtt`}
            srcLang="tr"
            label="Türkçe"
            default
          />
        )}
        Tarayıcınız video oynatmayı desteklemiyor.
      </video>

      {/* Video Başlığı */}
      <div className="absolute top-4 left-4 right-4">
        <h3 className="text-white text-lg font-semibold bg-black bg-opacity-50 px-3 py-1 rounded">
          {title}
        </h3>
      </div>

      {/* Video Kontrolleri */}
      <div 
        className={`absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black to-transparent p-4 transition-opacity duration-300 ${
          showControls ? 'opacity-100' : 'opacity-0'
        }`}
      >
        {/* Progress Bar */}
        <div className="mb-4">
          <div className="relative h-2 bg-gray-600 rounded-full cursor-pointer">
            {/* Buffered Progress */}
            <div 
              className="absolute h-full bg-gray-400 rounded-full"
              style={{ width: `${(progress.buffered / progress.duration) * 100}%` }}
            />
            
            {/* Played Progress */}
            <div 
              className="absolute h-full bg-red-500 rounded-full"
              style={{ width: `${progress.played}%` }}
            />
            
            {/* Seek Handle */}
            <div 
              className="absolute w-4 h-4 bg-red-500 rounded-full -mt-1 cursor-pointer"
              style={{ left: `calc(${progress.played}% - 8px)` }}
            />
            
            {/* Clickable Area */}
            <input
              type="range"
              min="0"
              max={progress.duration}
              value={progress.currentTime}
              onChange={(e) => handleSeek(Number(e.target.value))}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            />
          </div>
        </div>

        {/* Control Buttons */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            {/* Play/Pause */}
            <button
              onClick={togglePlay}
              className="text-white hover:text-red-500 transition-colors"
            >
              {isPlaying ? <Pause size={24} /> : <Play size={24} />}
            </button>

            {/* Skip Backward */}
            <button
              onClick={skipBackward}
              className="text-white hover:text-red-500 transition-colors"
            >
              <SkipBack size={20} />
            </button>

            {/* Skip Forward */}
            <button
              onClick={skipForward}
              className="text-white hover:text-red-500 transition-colors"
            >
              <SkipForward size={20} />
            </button>

            {/* Volume */}
            <div className="flex items-center space-x-2">
              <button
                onClick={toggleMute}
                className="text-white hover:text-red-500 transition-colors"
              >
                {isMuted ? <VolumeX size={20} /> : <Volume2 size={20} />}
              </button>
              
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={isMuted ? 0 : volume}
                onChange={(e) => handleVolumeChange(Number(e.target.value))}
                className="w-20 h-1 bg-gray-600 rounded-lg appearance-none cursor-pointer"
              />
            </div>

            {/* Time Display */}
            <div className="text-white text-sm">
              {formatTime(progress.currentTime)} / {formatTime(progress.duration)}
            </div>
          </div>

          <div className="flex items-center space-x-4">
            {/* Settings */}
            <div className="relative">
              <button
                onClick={() => setShowSettings(!showSettings)}
                className="text-white hover:text-red-500 transition-colors"
              >
                <Settings size={20} />
              </button>

              {showSettings && (
                <div className="absolute bottom-8 right-0 bg-black bg-opacity-90 rounded-lg p-3 min-w-32">
                  <div className="text-white text-sm mb-2">Oynatma Hızı</div>
                  {[0.5, 0.75, 1, 1.25, 1.5, 2].map((rate) => (
                    <button
                      key={rate}
                      onClick={() => changePlaybackRate(rate)}
                      className={`block w-full text-left px-2 py-1 text-sm rounded ${
                        playbackRate === rate 
                          ? 'bg-red-500 text-white' 
                          : 'text-gray-300 hover:bg-gray-700'
                      }`}
                    >
                      {rate}x
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Fullscreen */}
            <button
              onClick={toggleFullscreen}
              className="text-white hover:text-red-500 transition-colors"
            >
              <Maximize size={20} />
            </button>
          </div>
        </div>
      </div>

      {/* Loading Overlay */}
      {!progress.duration && (
        <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-50">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-500"></div>
        </div>
      )}
    </div>
  );
};