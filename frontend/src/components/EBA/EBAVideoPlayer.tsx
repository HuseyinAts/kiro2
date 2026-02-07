/**
 * Task 97.4: EBA Video Player Component
 * Video player with watch tracking and resume functionality
 */

import * as React from 'react';
import {  useState, useEffect, useRef  } from 'react';
import './EBAVideoPlayer.css';

export interface EBAVideoMetadata {
  video_id: string;
  title: string;
  description?: string;
  duration_seconds: number;
  thumbnail_url?: string;
  video_url: string;
  subject: string;
  grade_level: string;
  topic?: string;
  quality: string;
}

export interface EBAVideoPlayerProps {
  video: EBAVideoMetadata;
  userId: string;
  apiBaseUrl?: string;
  onComplete?: () => void;
  onProgress?: (percentage: number) => void;
}

export const EBAVideoPlayer: React.FC<EBAVideoPlayerProps> = ({
  video,
  userId: _userId,
  apiBaseUrl = '/api/v1/eba',
  onComplete,
  onProgress,
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [resumePosition, setResumePosition] = useState<number>(0);
  const [currentTime, setCurrentTime] = useState<number>(0);
  const [watchPercentage, setWatchPercentage] = useState<number>(0);
  const [isCompleted, setIsCompleted] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const progressUpdateIntervalRef = useRef<number | null>(null);

  // Start watch session on mount
  useEffect(() => {
    startWatchSession();

    return () => {
      // Cleanup: end session when component unmounts
      if (sessionId) {
        endWatchSession();
      }

      if (progressUpdateIntervalRef.current) {
        clearInterval(progressUpdateIntervalRef.current);
      }
    };
  }, []);

  // Resume video when resume position is set
  useEffect(() => {
    if (videoRef.current && resumePosition > 0) {
      videoRef.current.currentTime = resumePosition;
    }
  }, [resumePosition]);

  // Start progress update interval
  useEffect(() => {
    if (sessionId && videoRef.current) {
      // Update progress every 10 seconds
      progressUpdateIntervalRef.current = window.setInterval(() => {
        if (videoRef.current && !videoRef.current.paused) {
          updateProgress(videoRef.current.currentTime);
        }
      }, 10000); // 10 seconds
    }

    return () => {
      if (progressUpdateIntervalRef.current) {
        clearInterval(progressUpdateIntervalRef.current);
      }
    };
  }, [sessionId]);

  const startWatchSession = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${apiBaseUrl}/watch/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          // Add auth token here
        },
        body: JSON.stringify({
          eba_video_id: video.video_id,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to start watch session');
      }

      const data = await response.json();
      setSessionId(data.session_id);
      setResumePosition(data.resume_position || 0);

      console.log('[EBA WATCH] Session started:', data.session_id);
      console.log('[EBA WATCH] Resume position:', data.resume_position);

    } catch (err) {
      console.error('[EBA WATCH] Failed to start session:', err);
      setError('Video yüklenemedi. Lütfen tekrar deneyin.');
    } finally {
      setIsLoading(false);
    }
  };

  const updateProgress = async (currentTimeSeconds: number) => {
    if (!sessionId) {return;}

    try {
      const response = await fetch(`${apiBaseUrl}/watch/progress`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          current_time: Math.floor(currentTimeSeconds),
          video_duration: video.duration_seconds,
        }),
      });

      if (!response.ok) {
        console.error('[EBA WATCH] Failed to update progress');
        return;
      }

      const data = await response.json();

      setWatchPercentage(data.watch_percentage);

      if (data.completed && !isCompleted) {
        setIsCompleted(true);
        console.log('[EBA WATCH] Video completed!');
        onComplete?.();
      }

      if (onProgress) {
        onProgress(data.watch_percentage);
      }

    } catch (err) {
      console.error('[EBA WATCH] Progress update failed:', err);
    }
  };

  const endWatchSession = async () => {
    if (!sessionId || !videoRef.current) {return;}

    try {
      const finalTime = Math.floor(videoRef.current.currentTime);

      await fetch(`${apiBaseUrl}/watch/end/${sessionId}?final_time=${finalTime}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      console.log('[EBA WATCH] Session ended');

    } catch (err) {
      console.error('[EBA WATCH] Failed to end session:', err);
    }
  };

  const handleTimeUpdate = () => {
    if (videoRef.current) {
      const current = videoRef.current.currentTime;
      setCurrentTime(current);

      // Calculate percentage
      const percentage = (current / video.duration_seconds) * 100;
      setWatchPercentage(percentage);
    }
  };

  const handleEnded = () => {
    console.log('[EBA WATCH] Video ended');
    if (sessionId) {
      updateProgress(video.duration_seconds);
    }
  };

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (isLoading) {
    return (
      <div className="eba-video-player loading">
        <div className="spinner"></div>
        <p>Video yükleniyor...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="eba-video-player error">
        <div className="error-icon">⚠️</div>
        <p>{error}</p>
        <button onClick={startWatchSession}>Tekrar Dene</button>
      </div>
    );
  }

  return (
    <div className="eba-video-player">
      <div className="video-header">
        <h2 className="video-title">{video.title}</h2>
        <div className="video-meta">
          <span className="subject">{video.subject}</span>
          <span className="grade">{video.grade_level}</span>
          {video.topic && <span className="topic">{video.topic}</span>}
        </div>
      </div>

      <div className="video-container">
        <video
          ref={videoRef}
          className="video-element"
          controls
          poster={video.thumbnail_url}
          onTimeUpdate={handleTimeUpdate}
          onEnded={handleEnded}
          src={video.video_url}
        >
          <source src={video.video_url} type="video/mp4" />
          Tarayıcınız video oynatmayı desteklemiyor.
        </video>

        {resumePosition > 0 && currentTime < 5 && (
          <div className="resume-notification">
            <p>Kaldığın yerden devam et</p>
            <p className="resume-time">{formatTime(resumePosition)}</p>
          </div>
        )}

        {isCompleted && (
          <div className="completion-badge">
            <span className="badge-icon">✅</span>
            <span>Tamamlandı!</span>
          </div>
        )}
      </div>

      <div className="video-progress-bar">
        <div
          className="progress-fill"
          style={{ width: `${watchPercentage}%` }}
        ></div>
      </div>

      <div className="video-info">
        <div className="time-display">
          <span className="current">{formatTime(currentTime)}</span>
          <span className="separator">/</span>
          <span className="duration">{formatTime(video.duration_seconds)}</span>
        </div>

        <div className="watch-stats">
          <span className="percentage">{watchPercentage.toFixed(1)}% izlendi</span>
          {isCompleted && <span className="completed-badge">Tamamlandı ✓</span>}
        </div>
      </div>

      {video.description && (
        <div className="video-description">
          <h3>Açıklama</h3>
          <p>{video.description}</p>
        </div>
      )}

      <div className="video-footer">
        <div className="quality-badge">{video.quality}</div>
        <div className="eba-badge">
          <img src="/eba-logo.png" alt="EBA TV" className="eba-logo" />
          <span>MEB Onaylı İçerik</span>
        </div>
      </div>
    </div>
  );
};

export default EBAVideoPlayer;
