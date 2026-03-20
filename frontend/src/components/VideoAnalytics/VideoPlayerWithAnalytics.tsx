/**
 * Task 100.1: Video Player with Analytics Tracking
 *
 * HTML5 video player with automatic progress tracking,
 * pause/seek detection, and completion tracking
 */

import * as React from 'react';
import {  useRef, useEffect, useState  } from 'react';
import './VideoPlayerWithAnalytics.css';

export interface VideoPlayerProps {
  videoUrl: string;
  videoId: string;
  videoSource: 'youtube' | 'eba' | 'khan' | 'vimeo';
  userId: string;
  videoDuration?: number;
  initialPosition?: number;
  onProgress?: (position: number, percentage: number) => void;
  onComplete?: () => void;
  onNote?: (timestamp: number) => void;
  onBookmark?: (timestamp: number) => void;
}

interface WatchSession {
  sessionId: string;
  videoId: string;
  startedAt: string;
}

const API_BASE = '/api/v1/video-analytics';
const PROGRESS_UPDATE_INTERVAL = 10000; // 10 seconds

export const VideoPlayerWithAnalytics: React.FC<VideoPlayerProps> = ({
  videoUrl,
  videoId,
  videoSource,
  userId,
  videoDuration,
  initialPosition = 0,
  onProgress,
  onComplete,
  onNote,
  onBookmark,
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [session, setSession] = useState<WatchSession | null>(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(videoDuration || 0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1.0);
  const [completionPercentage, setCompletionPercentage] = useState(0);
  const [showControls, setShowControls] = useState(true);

  const progressIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const lastPositionRef = useRef(0);

  // Start watch session
  useEffect(() => {
    const startSession = async () => {
      // If videoDuration prop is provided, don't require videoRef
      // This enables testing and server-side rendering scenarios
      const actualDuration = videoDuration || videoRef.current?.duration;
      if (!actualDuration) {return;}

      try {
        const response = await fetch(`${API_BASE}/sessions/start?user_id=${userId}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            video_id: videoId,
            video_source: videoSource,
            video_duration: Math.floor(actualDuration),
          }),
        });

        const data = await response.json();
        setSession({
          sessionId: data.session_id,
          videoId: data.video_id,
          startedAt: data.started_at,
        });
      } catch (error) {
        console.error('Failed to start watch session:', error);
      }
    };

    startSession();

    return () => {
      // End session on unmount
      if (session && videoRef.current) {
        endSession(Math.floor(videoRef.current.currentTime));
      }
    };
  }, [videoId, videoSource, userId, videoDuration]);

  // Set initial position
  useEffect(() => {
    if (videoRef.current && initialPosition > 0) {
      videoRef.current.currentTime = initialPosition;
    }
  }, [initialPosition]);

  // Progress tracking interval
  useEffect(() => {
    if (isPlaying && session) {
      progressIntervalRef.current = setInterval(() => {
        updateProgress();
      }, PROGRESS_UPDATE_INTERVAL);

      return () => {
        if (progressIntervalRef.current) {
          clearInterval(progressIntervalRef.current);
        }
      };
    }
  }, [isPlaying, session]);

  const updateProgress = async () => {
    if (!session || !videoRef.current) {return;}

    const currentPosition = Math.floor(videoRef.current.currentTime);

    try {
      const response = await fetch(
        `${API_BASE}/sessions/${session.sessionId}/progress`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            current_position: currentPosition,
            playback_speed: playbackSpeed,
          }),
        },
      );

      const data = await response.json();
      setCompletionPercentage(data.completion_percentage);

      if (onProgress) {
        onProgress(currentPosition, data.completion_percentage);
      }

      if (data.is_completed && onComplete) {
        onComplete();
      }
    } catch (error) {
      console.error('Failed to update progress:', error);
    }
  };

  const endSession = async (finalPosition: number) => {
    if (!session) {return;}

    try {
      await fetch(
        `${API_BASE}/sessions/${session.sessionId}/end?final_position=${finalPosition}`,
        { method: 'POST' },
      );
    } catch (error) {
      console.error('Failed to end session:', error);
    }
  };

  const recordPause = async () => {
    if (!session) {return;}

    try {
      await fetch(`${API_BASE}/sessions/${session.sessionId}/pause`, {
        method: 'POST',
      });
    } catch (error) {
      console.error('Failed to record pause:', error);
    }
  };

  const recordSeek = async (fromPosition: number, toPosition: number) => {
    if (!session) {return;}

    try {
      await fetch(`${API_BASE}/sessions/${session.sessionId}/seek`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          from_position: Math.floor(fromPosition),
          to_position: Math.floor(toPosition),
        }),
      });
    } catch (error) {
      console.error('Failed to record seek:', error);
    }
  };

  // Event handlers
  const handlePlay = () => {
    setIsPlaying(true);
  };

  const handlePause = () => {
    setIsPlaying(false);
    recordPause();
    updateProgress(); // Update progress on pause
  };

  const handleTimeUpdate = () => {
    if (!videoRef.current) {return;}
    setCurrentTime(videoRef.current.currentTime);
  };

  const handleLoadedMetadata = () => {
    if (videoRef.current) {
      setDuration(videoRef.current.duration);
    }
  };

  const handleSeeked = () => {
    if (!videoRef.current) {return;}

    const currentPosition = videoRef.current.currentTime;
    recordSeek(lastPositionRef.current, currentPosition);
    lastPositionRef.current = currentPosition;
  };

  const handleSpeedChange = (speed: number) => {
    if (videoRef.current) {
      videoRef.current.playbackRate = speed;
      setPlaybackSpeed(speed);
    }
  };

  const handleAddNote = () => {
    if (onNote && videoRef.current) {
      onNote(Math.floor(videoRef.current.currentTime));
    }
  };

  const handleAddBookmark = () => {
    if (onBookmark && videoRef.current) {
      onBookmark(Math.floor(videoRef.current.currentTime));
    }
  };

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="video-player-analytics">
      <div
        className="video-container"
        onMouseEnter={() => setShowControls(true)}
        onMouseLeave={() => setShowControls(false)}
      >
        <video
          ref={videoRef}
          src={videoUrl}
          onPlay={handlePlay}
          onPause={handlePause}
          onTimeUpdate={handleTimeUpdate}
          onLoadedMetadata={handleLoadedMetadata}
          onSeeked={handleSeeked}
          className="video-element"
        />

        {showControls && (
          <div className="video-controls">
            <div className="progress-bar-container">
              <div className="progress-bar">
                <div
                  className="progress-filled"
                  style={{ width: `${(currentTime / duration) * 100}%` }}
                />
              </div>
            </div>

            <div className="controls-bottom">
              <div className="controls-left">
                <button
                  className="control-btn"
                  onClick={() => videoRef.current?.paused ? videoRef.current?.play() : videoRef.current?.pause()}
                  aria-label={isPlaying ? 'Pause' : 'Play'}
                >
                  {isPlaying ? '⏸' : '▶'}
                </button>

                <span className="time-display">
                  {formatTime(currentTime)} / {formatTime(duration)}
                </span>

                <span className="completion-badge">
                  {(completionPercentage ?? 0).toFixed(0)}%
                </span>
              </div>

              <div className="controls-center">
                <button
                  className="control-btn-secondary"
                  onClick={handleAddNote}
                  title="Not al"
                  aria-label="Add note"
                >
                  📝
                </button>

                <button
                  className="control-btn-secondary"
                  onClick={handleAddBookmark}
                  title="Yer imi ekle"
                  aria-label="Add bookmark"
                >
                  🔖
                </button>
              </div>

              <div className="controls-right">
                <select
                  className="speed-selector"
                  value={playbackSpeed}
                  onChange={(e) => handleSpeedChange(parseFloat(e.target.value))}
                  aria-label="Playback speed"
                >
                  <option value="0.5">0.5x</option>
                  <option value="0.75">0.75x</option>
                  <option value="1">1x</option>
                  <option value="1.25">1.25x</option>
                  <option value="1.5">1.5x</option>
                  <option value="2">2x</option>
                </select>
              </div>
            </div>
          </div>
        )}
      </div>

      {session && (
        <div className="session-info">
          <small>Session: {session.sessionId}</small>
        </div>
      )}
    </div>
  );
};

export default VideoPlayerWithAnalytics;
