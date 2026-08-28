import os

content = """/**
 * WCAG 2.1 Level AA Uyumlu Video Player
 * Türkçe altyazı desteği ve klavye kısayolları.
 *
 * Refactored to AUGUST 2026 ULTRA standards.
 * Tech debt cleared by utilizing specialized hooks.
 */

import {
  PlayArrow,
  Pause,
  VolumeUp,
  VolumeOff,
  Fullscreen,
  FullscreenExit,
  Settings,
  Subtitles,
  SubtitlesOff,
  Replay10,
  Forward10,
} from '@mui/icons-material';
import {
  Box,
  IconButton,
  Slider,
  Typography,
  Tooltip,
  Menu,
  MenuItem,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Chip,
  useTheme,
} from '@mui/material';
import * as React from 'react';
import { useState, useRef, useEffect, useCallback } from 'react';

import { useAccessibilitySettings } from '../../hooks/useAccessibilitySettings';
import { useScreenReader } from '../../hooks/useScreenReader';

import { useVideoControls } from '../../hooks/video/useVideoControls';
import { useVideoCaptions } from '../../hooks/video/useVideoCaptions';
import { useVideoFullscreen } from '../../hooks/video/useVideoFullscreen';
import { useVideoKeyboard } from '../../hooks/video/useVideoKeyboard';

export interface VideoTrack {
  id: string;
  label: string;
  language: string;
  src: string;
  kind: 'subtitles' | 'captions' | 'descriptions';
  default?: boolean;
}

interface AccessibleVideoPlayerProps {
  src: string;
  title: string;
  description?: string;
  poster?: string;
  tracks?: VideoTrack[];
  autoPlay?: boolean;
  muted?: boolean;
  loop?: boolean;
  controls?: boolean;
  width?: string | number;
  height?: string | number;
  onPlay?: () => void;
  onPause?: () => void;
  onEnded?: () => void;
  onTimeUpdate?: (currentTime: number, duration: number) => void;
  onVolumeChange?: (volume: number) => void;
  className?: string;
}

const AccessibleVideoPlayer: React.FC<AccessibleVideoPlayerProps> = ({
  src,
  title,
  description,
  poster,
  tracks = [],
  autoPlay = false,
  muted = false,
  loop = false,
  controls = true,
  width = '100%',
  height = 'auto',
  onPlay,
  onPause,
  onEnded,
  onTimeUpdate,
  onVolumeChange,
  className,
}) => {
  const theme = useTheme();
  const { settings } = useAccessibilitySettings();
  const { announce } = useScreenReader();

  const videoRef = useRef<HTMLVideoElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const [showControls, setShowControls] = useState(true);
  const [controlsTimeout, setControlsTimeout] = useState<NodeJS.Timeout | null>(null);
  const [settingsAnchor, setSettingsAnchor] = useState<null | HTMLElement>(null);

  // Video ID'leri
  const videoId = `video-${Math.random().toString(36).substr(2, 9)}`;
  const descriptionId = `${videoId}-description`;
  const transcriptId = `${videoId}-transcript`;

  // --- HOOKS ---
  const {
    isPlaying, setIsPlaying,
    currentTime, setCurrentTime,
    duration, setDuration,
    volume, setVolume,
    isMuted, setIsMuted,
    playbackRate, setPlaybackRate,
    togglePlay, handleSeek, toggleMute
  } = useVideoControls(videoRef, announce);

  const {
    activeTrack, setActiveTrack,
    showCaptions, setShowCaptions,
    showTranscript, setShowTranscript,
    transcript, setTranscript,
    toggleCaptions, selectTrack
  } = useVideoCaptions(videoRef, announce);

  const { isFullscreen, setIsFullscreen, toggleFullscreen } = useVideoFullscreen(containerRef, announce);

  // Helper for keyboard and mouse to show controls
  const showControlsTemporarily = useCallback(() => {
    setShowControls(true);
    if (controlsTimeout) {
      clearTimeout(controlsTimeout);
    }
    const timeout = setTimeout(() => {
      if (isPlaying) {
        setShowControls(false);
      }
    }, 3000);
    setControlsTimeout(timeout);
  }, [isPlaying, controlsTimeout]);

  // Hook 4
  const skipBackward = useCallback(() => {
    handleSeek(Math.max(0, currentTime - 10));
  }, [currentTime, handleSeek]);

  const skipForward = useCallback(() => {
    handleSeek(Math.min(duration, currentTime + 10));
  }, [currentTime, duration, handleSeek]);

  const { handleKeyDown: hookHandleKeyDown } = useVideoKeyboard(
    togglePlay,
    toggleFullscreen,
    toggleMute,
    skipBackward,
    skipForward,
    showControlsTemporarily,
    announce
  );

  const handleKeyDown = useCallback((event: React.KeyboardEvent) => {
    if (event.target !== containerRef.current) return;

    // Default hook handles basic keys
    hookHandleKeyDown(event);

    // Add additional specialized keys
    switch (event.key) {
      case 'ArrowUp':
        event.preventDefault();
        {
          const nv = Math.min(1, volume + 0.1);
          if (videoRef.current) videoRef.current.volume = nv;
          setVolume(nv);
          setIsMuted(nv === 0);
          announce(`Ses seviyesi %${Math.round(nv * 100)}`, 'polite');
        }
        break;
      case 'ArrowDown':
        event.preventDefault();
        {
          const nv = Math.max(0, volume - 0.1);
          if (videoRef.current) videoRef.current.volume = nv;
          setVolume(nv);
          setIsMuted(nv === 0);
          announce(`Ses seviyesi %${Math.round(nv * 100)}`, 'polite');
        }
        break;
      case 'c':
        event.preventDefault();
        toggleCaptions();
        break;
      case '0':
      case '1':
      case '2':
      case '3':
      case '4':
      case '5':
      case '6':
      case '7':
      case '8':
      case '9': {
        event.preventDefault();
        const percentage = parseInt(event.key) / 10;
        handleSeek(duration * percentage);
        break;
      }
      case 'Home':
        event.preventDefault();
        handleSeek(0);
        break;
      case 'End':
        event.preventDefault();
        handleSeek(duration);
        break;
    }
  }, [hookHandleKeyDown, volume, setVolume, setIsMuted, announce, toggleCaptions, duration, handleSeek]);


  // Video event handlers
  const handleLoadedMetadata = useCallback(() => {
    if (videoRef.current) {
      setDuration(videoRef.current.duration);

      // Varsayılan track'i etkinleştir
      const defaultTrack = tracks.find(track => track.default);
      if (defaultTrack) {
        setActiveTrack(defaultTrack.id);
        setShowCaptions(true);
      }
    }
  }, [tracks, setDuration, setActiveTrack, setShowCaptions]);

  const handleTimeUpdate = useCallback(() => {
    if (videoRef.current) {
      const current = videoRef.current.currentTime;
      setCurrentTime(current);
      onTimeUpdate?.(current, duration);
    }
  }, [duration, onTimeUpdate, setCurrentTime]);

  const handlePlay = useCallback(() => {
    setIsPlaying(true);
    onPlay?.();
    announce('Video oynatılıyor', 'polite');
  }, [onPlay, announce, setIsPlaying]);

  const handlePause = useCallback(() => {
    setIsPlaying(false);
    onPause?.();
    announce('Video duraklatıldı', 'polite');
  }, [onPause, announce, setIsPlaying]);

  const handleEnded = useCallback(() => {
    setIsPlaying(false);
    onEnded?.();
    announce('Video sona erdi', 'polite');
  }, [onEnded, announce, setIsPlaying]);

  const handleVolumeChange = useCallback(() => {
    if (videoRef.current) {
      const newVolume = videoRef.current.volume;
      setVolume(newVolume);
      setIsMuted(videoRef.current.muted);
      onVolumeChange?.(newVolume);
    }
  }, [onVolumeChange, setVolume, setIsMuted]);

  const handleVolumeSliderChange = useCallback((newVolume: number) => {
    if (videoRef.current) {
      videoRef.current.volume = newVolume;
      setVolume(newVolume);
      setIsMuted(newVolume === 0);
      announce(`Ses seviyesi %${Math.round(newVolume * 100)}`, 'polite');
    }
  }, [setVolume, setIsMuted, announce]);

  const changePlaybackRate = useCallback((rate: number) => {
    if (videoRef.current) {
      videoRef.current.playbackRate = rate;
      setPlaybackRate(rate);
      announce(`Oynatma hızı ${rate}x olarak değiştirildi`, 'polite');
    }
  }, [announce, setPlaybackRate]);

  // Mouse hareket takibi
  const handleMouseMove = useCallback(() => {
    showControlsTemporarily();
  }, [showControlsTemporarily]);

  // Zaman formatı
  const formatTime = (time: number): string => {
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  // Component mount/unmount
  useEffect(() => {
    const video = videoRef.current;
    if (!video) {return;}

    video.addEventListener('loadedmetadata', handleLoadedMetadata);
    video.addEventListener('timeupdate', handleTimeUpdate);
    video.addEventListener('play', handlePlay);
    video.addEventListener('pause', handlePause);
    video.addEventListener('ended', handleEnded);
    video.addEventListener('volumechange', handleVolumeChange);

    return () => {
      video.removeEventListener('loadedmetadata', handleLoadedMetadata);
      video.removeEventListener('timeupdate', handleTimeUpdate);
      video.removeEventListener('play', handlePlay);
      video.removeEventListener('pause', handlePause);
      video.removeEventListener('ended', handleEnded);
      video.removeEventListener('volumechange', handleVolumeChange);
    };
  }, [
    handleLoadedMetadata, handleTimeUpdate, handlePlay, handlePause,
    handleEnded, handleVolumeChange,
  ]);

  // Fullscreen değişikliklerini dinle
  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };

    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
  }, [setIsFullscreen]);

  // Cleanup timeout
  useEffect(() => {
    return () => {
      if (controlsTimeout) {
        clearTimeout(controlsTimeout);
      }
    };
  }, [controlsTimeout]);

  return (
    <Box
      ref={containerRef}
      role="region"
      aria-label={`Video player: ${title}`}
      className={className}
      sx={{
        position: 'relative',
        width,
        height,
        backgroundColor: 'black',
        borderRadius: 1,
        overflow: 'hidden',
        '&:focus': {
          outline: `2px solid ${theme.palette.primary.main}`,
          outlineOffset: 2,
        },
      }}
      tabIndex={0}
      onKeyDown={handleKeyDown}
      onMouseMove={handleMouseMove}
      onMouseLeave={() => {
        if (isPlaying) {
          setShowControls(false);
        }
      }}
    >
      {/* Video Element */}
      <video
        ref={videoRef}
        id={videoId}
        src={src}
        poster={poster}
        autoPlay={autoPlay}
        muted={muted}
        loop={loop}
        controls={false} // Özel kontroller kullanıyoruz
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'contain',
        }}
        aria-label={title}
        aria-describedby={description ? descriptionId : undefined}
        crossOrigin="anonymous"
      >
        {/* Text Tracks */}
        {tracks.map((track) => (
          <track
            key={track.id}
            id={track.id}
            kind={track.kind}
            src={track.src}
            srcLang={track.language}
            label={track.label}
            default={track.default}
          />
        ))}

        {/* Fallback */}
        <Typography color="white" sx={{ p: 2 }}>
          Tarayıcınız video oynatmayı desteklemiyor.
          <Button
            component="a"
            href={src}
            download
            color="primary"
            sx={{ ml: 1 }}
          >
            Videoyu İndir
          </Button>
        </Typography>
      </video>

      {/* Video Açıklaması */}
      {description && (
        <Typography
          id={descriptionId}
          sx={{
            position: 'absolute',
            left: -9999,
            width: 1,
            height: 1,
            overflow: 'hidden',
          }}
        >
          {description}
        </Typography>
      )}

      {/* Kontroller */}
      {controls && (
        <Box
          sx={{
            position: 'absolute',
            bottom: 0,
            left: 0,
            right: 0,
            background: 'linear-gradient(transparent, rgba(0,0,0,0.8))',
            opacity: showControls ? 1 : 0,
            transition: 'opacity 0.3s',
            p: 2,
          }}
        >
          {/* Progress Bar */}
          <Box sx={{ mb: 2 }}>
            <Slider
              value={currentTime}
              max={duration}
              onChange={(_, value) => handleSeek(value as number)}
              aria-label="Video ilerleme çubuğu"
              aria-valuetext={`${formatTime(currentTime)} / ${formatTime(duration)}`}
              sx={{
                color: 'primary.main',
                '& .MuiSlider-thumb': {
                  width: 16,
                  height: 16,
                },
                '& .MuiSlider-rail': {
                  backgroundColor: 'rgba(255,255,255,0.3)',
                },
                '& .MuiSlider-track': {
                  backgroundColor: 'primary.main',
                },
              }}
            />
          </Box>

          {/* Kontrol Butonları */}
          <Box sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: 1,
          }}>
            {/* Sol Kontroller */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              {/* Geri Sar */}
              <Tooltip title="10 saniye geri (←)">
                <IconButton
                  onClick={skipBackward}
                  sx={{ color: 'white' }}
                  aria-label="10 saniye geri sar"
                  className="wcag-aa-target-size"
                >
                  <Replay10 />
                </IconButton>
              </Tooltip>

              {/* Oynat/Duraklat */}
              <Tooltip title={isPlaying ? 'Duraklat (Space/K)' : 'Oynat (Space/K)'}>
                <IconButton
                  onClick={togglePlay}
                  sx={{ color: 'white' }}
                  aria-label={isPlaying ? 'Videoyu duraklat' : 'Videoyu oynat'}
                  className="wcag-aa-target-size"
                >
                  {isPlaying ? <Pause /> : <PlayArrow />}
                </IconButton>
              </Tooltip>

              {/* İleri Sar */}
              <Tooltip title="10 saniye ileri (→)">
                <IconButton
                  onClick={skipForward}
                  sx={{ color: 'white' }}
                  aria-label="10 saniye ileri sar"
                  className="wcag-aa-target-size"
                >
                  <Forward10 />
                </IconButton>
              </Tooltip>

              {/* Ses Kontrolü */}
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, minWidth: 120 }}>
                <Tooltip title={isMuted ? 'Sesi aç (M)' : 'Sesi kapat (M)'}>
                  <IconButton
                    onClick={toggleMute}
                    sx={{ color: 'white' }}
                    aria-label={isMuted ? 'Sesi aç' : 'Sesi kapat'}
                    className="wcag-aa-target-size"
                  >
                    {isMuted ? <VolumeOff /> : <VolumeUp />}
                  </IconButton>
                </Tooltip>

                <Slider
                  value={isMuted ? 0 : volume}
                  max={1}
                  step={0.1}
                  onChange={(_, value) => handleVolumeSliderChange(value as number)}
                  aria-label="Ses seviyesi"
                  aria-valuetext={`Ses seviyesi %${Math.round((isMuted ? 0 : volume) * 100)}`}
                  sx={{
                    width: 80,
                    color: 'white',
                    '& .MuiSlider-thumb': {
                      width: 12,
                      height: 12,
                    },
                  }}
                />
              </Box>

              {/* Zaman Göstergesi */}
              <Typography variant="body2" sx={{ color: 'white', minWidth: 100 }}>
                {formatTime(currentTime)} / {formatTime(duration)}
              </Typography>
            </Box>

            {/* Sağ Kontroller */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              {/* Altyazı */}
              {tracks.length > 0 && (
                <Tooltip title={showCaptions ? 'Altyazıları kapat (C)' : 'Altyazıları aç (C)'}>
                  <IconButton
                    onClick={toggleCaptions}
                    sx={{ color: showCaptions ? 'primary.main' : 'white' }}
                    aria-label={showCaptions ? 'Altyazıları kapat' : 'Altyazıları aç'}
                    className="wcag-aa-target-size"
                  >
                    {showCaptions ? <Subtitles /> : <SubtitlesOff />}
                  </IconButton>
                </Tooltip>
              )}

              {/* Ayarlar */}
              <Tooltip title="Video ayarları">
                <IconButton
                  onClick={(e) => setSettingsAnchor(e.currentTarget)}
                  sx={{ color: 'white' }}
                  aria-label="Video ayarlarını aç"
                  className="wcag-aa-target-size"
                >
                  <Settings />
                </IconButton>
              </Tooltip>

              {/* Tam Ekran */}
              <Tooltip title={isFullscreen ? 'Tam ekrandan çık (F)' : 'Tam ekran (F)'}>
                <IconButton
                  onClick={toggleFullscreen}
                  sx={{ color: 'white' }}
                  aria-label={isFullscreen ? 'Tam ekrandan çık' : 'Tam ekrana geç'}
                  className="wcag-aa-target-size"
                >
                  {isFullscreen ? <FullscreenExit /> : <Fullscreen />}
                </IconButton>
              </Tooltip>
            </Box>
          </Box>
        </Box>
      )}

      {/* Ayarlar Menüsü */}
      <Menu
        anchorEl={settingsAnchor}
        open={Boolean(settingsAnchor)}
        onClose={() => setSettingsAnchor(null)}
        PaperProps={{
          sx: { minWidth: 200 },
        }}
      >
        {/* Oynatma Hızı */}
        <MenuItem>
          <Box sx={{ width: '100%' }}>
            <Typography variant="subtitle2" gutterBottom>
              Oynatma Hızı
            </Typography>
            {[0.5, 0.75, 1, 1.25, 1.5, 2].map((rate) => (
              <Button
                key={rate}
                size="small"
                variant={playbackRate === rate ? 'contained' : 'text'}
                onClick={() => changePlaybackRate(rate)}
                sx={{ mr: 0.5, mb: 0.5 }}
              >
                {rate}x
              </Button>
            ))}
          </Box>
        </MenuItem>

        {/* Altyazı Seçimi */}
        {tracks.length > 0 && (
          <MenuItem>
            <Box sx={{ width: '100%' }}>
              <Typography variant="subtitle2" gutterBottom>
                Altyazı Dili
              </Typography>
              {tracks.map((track) => (
                <Button
                  key={track.id}
                  size="small"
                  variant={activeTrack === track.id ? 'contained' : 'text'}
                  onClick={() => selectTrack(track.id)}
                  sx={{ mr: 0.5, mb: 0.5, display: 'block', textAlign: 'left' }}
                >
                  {track.label}
                </Button>
              ))}
            </Box>
          </MenuItem>
        )}

        {/* Transkript */}
        <MenuItem onClick={() => setShowTranscript(true)}>
          <Typography>Transkript Göster</Typography>
        </MenuItem>
      </Menu>

      {/* Transkript Dialog */}
      <Dialog
        open={showTranscript}
        onClose={() => setShowTranscript(false)}
        maxWidth="md"
        fullWidth
        aria-labelledby="transcript-title"
      >
        <DialogTitle id="transcript-title">
          Video Transkripti: {title}
        </DialogTitle>
        <DialogContent>
          <Typography
            id={transcriptId}
            variant="body1"
            sx={{
              lineHeight: 1.8,
              fontSize: settings.fontSize === 'large' ? '1.2rem' : '1rem',
            }}
          >
            {transcript || 'Transkript henüz mevcut değil.'}
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowTranscript(false)}>
            Kapat
          </Button>
        </DialogActions>
      </Dialog>

      {/* Klavye Kısayolları Yardımı */}
      {settings.keyboardNavigation && (
        <Box
          sx={{
            position: 'absolute',
            top: 8,
            right: 8,
            opacity: showControls ? 1 : 0,
            transition: 'opacity 0.3s',
          }}
        >
          <Chip
            label="? Kısayollar"
            size="small"
            sx={{
              backgroundColor: 'rgba(0,0,0,0.7)',
              color: 'white',
              cursor: 'pointer',
            }}
            onClick={() => {
              announce(
                'Klavye kısayolları: Space veya K: Oynat/Duraklat, Sol/Sağ ok: Geri/İleri sar, ' +
                'Yukarı/Aşağı ok: Ses ayarı, M: Sessiz, F: Tam ekran, C: Altyazı, 0-9: Konuma git',
                'polite',
              );
            }}
          />
        </Box>
      )}
    </Box>
  );
};

export default AccessibleVideoPlayer;
"""
with open('frontend/src/components/Common/AccessibleVideoPlayer.tsx', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated AccessibleVideoPlayer.tsx")
