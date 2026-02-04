import React, { useRef, useState, useEffect } from 'react';
import './AccessibleVideoPlayer.css';

interface Subtitle {
  startTime: number;
  endTime: number;
  text: string;
}

interface AccessibleVideoPlayerProps {
  src: string;
  title: string;
  subtitles?: string; // VTT or SRT file URL
  audioDescription?: string; // Secondary audio track URL
  poster?: string;
  autoplay?: boolean;
  className?: string;
}

export const AccessibleVideoPlayer: React.FC<AccessibleVideoPlayerProps> = ({
  src,
  title,
  subtitles,
  audioDescription,
  poster,
  autoplay = false,
  className = '',
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const progressBarRef = useRef<HTMLDivElement>(null);
  const volumeBarRef = useRef<HTMLInputElement>(null);

  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showCaptions, setShowCaptions] = useState(true);
  const [showAudioDescription, setShowAudioDescription] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(1);
  const [showSettings, setShowSettings] = useState(false);

  // Caption settings
  const [captionSettings, setCaptionSettings] = useState({
    fontSize: 16,
    color: '#FFFFFF',
    backgroundColor: '#000000',
    opacity: 0.75,
  });

  const [currentSubtitle, setCurrentSubtitle] = useState<string>('');
  const [parsedSubtitles, setParsedSubtitles] = useState<Subtitle[]>([]);

  // Load caption settings from localStorage
  useEffect(() => {
    const savedSettings = localStorage.getItem('videoCaptionSettings');
    if (savedSettings) {
      setCaptionSettings(JSON.parse(savedSettings));
    }
  }, []);

  // Save caption settings to localStorage
  useEffect(() => {
    localStorage.setItem('videoCaptionSettings', JSON.stringify(captionSettings));
  }, [captionSettings]);

  // Parse subtitles (VTT format)
  useEffect(() => {
    if (subtitles) {
      fetch(subtitles)
        .then(response => response.text())
        .then(text => {
          const parsed = parseVTT(text);
          setParsedSubtitles(parsed);
        })
        .catch(error => console.error('Error loading subtitles:', error));
    }
  }, [subtitles]);

  // Update current subtitle based on video time
  useEffect(() => {
    if (parsedSubtitles.length > 0 && showCaptions) {
      const current = parsedSubtitles.find(
        sub => currentTime >= sub.startTime && currentTime <= sub.endTime
      );
      setCurrentSubtitle(current ? current.text : '');
    } else {
      setCurrentSubtitle('');
    }
  }, [currentTime, parsedSubtitles, showCaptions]);

  const parseVTT = (vttText: string): Subtitle[] => {
    const lines = vttText.split('\n');
    const subtitles: Subtitle[] = [];
    let i = 0;

    while (i < lines.length) {
      const line = lines[i].trim();

      // Look for timestamp line (e.g., "00:00:01.000 --> 00:00:04.000")
      if (line.includes('-->')) {
        const [startStr, endStr] = line.split('-->').map(s => s.trim());
        const startTime = parseTimestamp(startStr);
        const endTime = parseTimestamp(endStr);

        i++;
        let text = '';

        // Collect subtitle text (until empty line)
        while (i < lines.length && lines[i].trim() !== '') {
          text += lines[i].trim() + ' ';
          i++;
        }

        subtitles.push({
          startTime,
          endTime,
          text: text.trim(),
        });
      }
      i++;
    }

    return subtitles;
  };

  const parseTimestamp = (timestamp: string): number => {
    // Parse timestamp format: "00:00:01.000" or "00:01:00.000"
    const parts = timestamp.split(':');
    const hours = parseInt(parts[0], 10);
    const minutes = parseInt(parts[1], 10);
    const seconds = parseFloat(parts[2]);
    return hours * 3600 + minutes * 60 + seconds;
  };

  const formatTime = (time: number): string => {
    const hours = Math.floor(time / 3600);
    const minutes = Math.floor((time % 3600) / 60);
    const seconds = Math.floor(time % 60);

    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  const togglePlayPause = () => {
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

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      videoRef.current?.requestFullscreen();
      setIsFullscreen(true);
    } else {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  };

  const handleTimeUpdate = () => {
    if (videoRef.current) {
      setCurrentTime(videoRef.current.currentTime);
    }
  };

  const handleLoadedMetadata = () => {
    if (videoRef.current) {
      setDuration(videoRef.current.duration);
    }
  };

  const handleVolumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newVolume = parseFloat(e.target.value);
    setVolume(newVolume);
    if (videoRef.current) {
      videoRef.current.volume = newVolume;
      setIsMuted(newVolume === 0);
    }
  };

  const handleProgressClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (progressBarRef.current && videoRef.current) {
      const rect = progressBarRef.current.getBoundingClientRect();
      const clickX = e.clientX - rect.left;
      const percentage = clickX / rect.width;
      videoRef.current.currentTime = percentage * duration;
    }
  };

  const skipBackward = () => {
    if (videoRef.current) {
      videoRef.current.currentTime = Math.max(0, videoRef.current.currentTime - 5);
    }
  };

  const skipForward = () => {
    if (videoRef.current) {
      videoRef.current.currentTime = Math.min(duration, videoRef.current.currentTime + 5);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    switch (e.key.toLowerCase()) {
      case ' ':
      case 'k':
        e.preventDefault();
        togglePlayPause();
        break;
      case 'arrowleft':
        e.preventDefault();
        skipBackward();
        break;
      case 'arrowright':
        e.preventDefault();
        skipForward();
        break;
      case 'arrowup':
        e.preventDefault();
        setVolume(prev => Math.min(1, prev + 0.1));
        if (videoRef.current) videoRef.current.volume = Math.min(1, volume + 0.1);
        break;
      case 'arrowdown':
        e.preventDefault();
        setVolume(prev => Math.max(0, prev - 0.1));
        if (videoRef.current) videoRef.current.volume = Math.max(0, volume - 0.1);
        break;
      case 'm':
        e.preventDefault();
        toggleMute();
        break;
      case 'f':
        e.preventDefault();
        toggleFullscreen();
        break;
      case 'c':
        e.preventDefault();
        setShowCaptions(!showCaptions);
        break;
    }
  };

  return (
    <div
      className={`accessible-video-player ${className}`}
      onKeyDown={handleKeyPress}
      tabIndex={0}
      role="region"
      aria-label={`Video oynatıcı: ${title}`}
    >
      <div className="video-container">
        <video
          ref={videoRef}
          src={src}
          poster={poster}
          onTimeUpdate={handleTimeUpdate}
          onLoadedMetadata={handleLoadedMetadata}
          autoPlay={autoplay}
          aria-label={title}
          aria-describedby="video-description"
        >
          {subtitles && (
            <track
              kind="subtitles"
              src={subtitles}
              srcLang="tr"
              label="Türkçe"
              default
            />
          )}
          {audioDescription && (
            <track
              kind="descriptions"
              src={audioDescription}
              srcLang="tr"
              label="Sesli Betimleme"
            />
          )}
          Tarayıcınız video öğesini desteklemiyor.
        </video>

        {/* Custom Captions */}
        {showCaptions && currentSubtitle && (
          <div
            className="video-captions"
            style={{
              fontSize: `${captionSettings.fontSize}px`,
              color: captionSettings.color,
              backgroundColor: captionSettings.backgroundColor,
              opacity: captionSettings.opacity,
            }}
            role="status"
            aria-live="polite"
          >
            {currentSubtitle}
          </div>
        )}
      </div>

      {/* Control Bar */}
      <div className="video-controls" role="toolbar" aria-label="Video kontrolleri">
        {/* Play/Pause Button */}
        <button
          onClick={togglePlayPause}
          aria-label={isPlaying ? 'Duraklat' : 'Oynat'}
          className="control-button"
        >
          {isPlaying ? (
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z" fill="currentColor" />
            </svg>
          ) : (
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M8 5v14l11-7z" fill="currentColor" />
            </svg>
          )}
        </button>

        {/* Skip Backward */}
        <button
          onClick={skipBackward}
          aria-label="5 saniye geri sar"
          className="control-button"
        >
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M11.99 5V1l-5 5 5 5V7c3.31 0 6 2.69 6 6s-2.69 6-6 6-6-2.69-6-6h-2c0 4.42 3.58 8 8 8s8-3.58 8-8-3.58-8-8-8z" fill="currentColor" />
          </svg>
          <span className="skip-text">-5s</span>
        </button>

        {/* Skip Forward */}
        <button
          onClick={skipForward}
          aria-label="5 saniye ileri sar"
          className="control-button"
        >
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M12.01 5V1l5 5-5 5V7c-3.31 0-6 2.69-6 6s2.69 6 6 6 6-2.69 6-6h2c0 4.42-3.58 8-8 8s-8-3.58-8-8 3.58-8 8-8z" fill="currentColor" />
          </svg>
          <span className="skip-text">+5s</span>
        </button>

        {/* Volume Control */}
        <div className="volume-control">
          <button
            onClick={toggleMute}
            aria-label={isMuted ? 'Sesi aç' : 'Sesi kapat'}
            className="control-button"
          >
            {isMuted || volume === 0 ? (
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M16.5 12c0-1.77-1.02-3.29-2.5-4.03v2.21l2.45 2.45c.03-.2.05-.41.05-.63zm2.5 0c0 .94-.2 1.82-.54 2.64l1.51 1.51C20.63 14.91 21 13.5 21 12c0-4.28-2.99-7.86-7-8.77v2.06c2.89.86 5 3.54 5 6.71zM4.27 3L3 4.27 7.73 9H3v6h4l5 5v-6.73l4.25 4.25c-.67.52-1.42.93-2.25 1.18v2.06c1.38-.31 2.63-.95 3.69-1.81L19.73 21 21 19.73l-9-9L4.27 3zM12 4L9.91 6.09 12 8.18V4z" fill="currentColor" />
              </svg>
            ) : (
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z" fill="currentColor" />
              </svg>
            )}
          </button>
          <input
            ref={volumeBarRef}
            type="range"
            min="0"
            max="1"
            step="0.1"
            value={volume}
            onChange={handleVolumeChange}
            aria-label="Ses seviyesi"
            className="volume-slider"
          />
        </div>

        {/* Time Display */}
        <div className="time-display" aria-live="off">
          <span>{formatTime(currentTime)}</span>
          <span> / </span>
          <span>{formatTime(duration)}</span>
        </div>

        {/* Progress Bar */}
        <div
          ref={progressBarRef}
          className="progress-container"
          onClick={handleProgressClick}
          role="slider"
          aria-label="Video ilerleme çubuğu"
          aria-valuemin={0}
          aria-valuemax={duration}
          aria-valuenow={currentTime}
          aria-valuetext={`${formatTime(currentTime)} / ${formatTime(duration)}`}
          tabIndex={0}
        >
          <div
            className="progress-bar"
            style={{ width: `${(currentTime / duration) * 100}%` }}
          />
        </div>

        {/* Caption Toggle */}
        {subtitles && (
          <button
            onClick={() => setShowCaptions(!showCaptions)}
            aria-label={showCaptions ? 'Altyazıları kapat' : 'Altyazıları aç'}
            className="control-button"
            aria-pressed={showCaptions}
          >
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M20 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zM4 12h4v2H4v-2zm10 6H4v-2h10v2zm6 0h-4v-2h4v2zm0-4H10v-2h10v2z" fill="currentColor" />
            </svg>
          </button>
        )}

        {/* Audio Description Toggle */}
        {audioDescription && (
          <button
            onClick={() => setShowAudioDescription(!showAudioDescription)}
            aria-label={showAudioDescription ? 'Sesli betimlemeyi kapat' : 'Sesli betimlemeyi aç'}
            className="control-button"
            aria-pressed={showAudioDescription}
          >
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M12 3v9.28c-.47-.17-.97-.28-1.5-.28C8.01 12 6 14.01 6 16.5S8.01 21 10.5 21c2.31 0 4.2-1.75 4.45-4H15V6h4V3h-7z" fill="currentColor" />
            </svg>
          </button>
        )}

        {/* Settings Button */}
        <button
          onClick={() => setShowSettings(!showSettings)}
          aria-label="Altyazı ayarları"
          aria-expanded={showSettings}
          className="control-button"
        >
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.05.3-.09.63-.09.94s.02.64.07.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z" fill="currentColor" />
          </svg>
        </button>

        {/* Fullscreen Button */}
        <button
          onClick={toggleFullscreen}
          aria-label={isFullscreen ? 'Tam ekrandan çık' : 'Tam ekran'}
          className="control-button"
        >
          {isFullscreen ? (
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M5 16h3v3h2v-5H5v2zm3-8H5v2h5V5H8v3zm6 11h2v-3h3v-2h-5v5zm2-11V5h-2v5h5V8h-3z" fill="currentColor" />
            </svg>
          ) : (
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z" fill="currentColor" />
            </svg>
          )}
        </button>
      </div>

      {/* Caption Settings Panel */}
      {showSettings && (
        <div className="caption-settings-panel" role="dialog" aria-label="Altyazı ayarları">
          <h3>Altyazı Ayarları</h3>

          <div className="setting-item">
            <label htmlFor="caption-font-size">Yazı Boyutu:</label>
            <input
              id="caption-font-size"
              type="range"
              min="12"
              max="24"
              value={captionSettings.fontSize}
              onChange={(e) => setCaptionSettings({ ...captionSettings, fontSize: parseInt(e.target.value) })}
              aria-valuemin={12}
              aria-valuemax={24}
              aria-valuenow={captionSettings.fontSize}
            />
            <span>{captionSettings.fontSize}px</span>
          </div>

          <div className="setting-item">
            <label htmlFor="caption-color">Yazı Rengi:</label>
            <input
              id="caption-color"
              type="color"
              value={captionSettings.color}
              onChange={(e) => setCaptionSettings({ ...captionSettings, color: e.target.value })}
            />
          </div>

          <div className="setting-item">
            <label htmlFor="caption-bg-color">Arka Plan Rengi:</label>
            <input
              id="caption-bg-color"
              type="color"
              value={captionSettings.backgroundColor}
              onChange={(e) => setCaptionSettings({ ...captionSettings, backgroundColor: e.target.value })}
            />
          </div>

          <div className="setting-item">
            <label htmlFor="caption-opacity">Arka Plan Şeffaflığı:</label>
            <input
              id="caption-opacity"
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={captionSettings.opacity}
              onChange={(e) => setCaptionSettings({ ...captionSettings, opacity: parseFloat(e.target.value) })}
            />
            <span>{Math.round(captionSettings.opacity * 100)}%</span>
          </div>

          <button onClick={() => setShowSettings(false)} className="close-settings">
            Kapat
          </button>
        </div>
      )}

      {/* Keyboard Shortcuts Help (Hidden, for screen readers) */}
      <div id="video-description" className="visually-hidden">
        Klavye kısayolları: Boşluk veya K tuşu ile oynat/duraklat,
        Sol/Sağ ok tuşları ile 5 saniye geri/ileri,
        Yukarı/Aşağı ok tuşları ile ses seviyesi,
        M tuşu ile sessize al,
        F tuşu ile tam ekran,
        C tuşu ile altyazı aç/kapat.
      </div>
    </div>
  );
};

export default AccessibleVideoPlayer;
