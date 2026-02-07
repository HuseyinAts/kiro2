/**
 * VideoLoadingUI Usage Examples
 * 
 * Bu dosya, VideoLoadingUI bileşeninin nasıl kullanılacağını gösterir.
 * 
 * @module VideoLoadingUI.example
 */

import * as React from 'react';
import { VideoLoadingUI } from './VideoLoadingUI';
import { VideoLoadingManager, VideoLoadingState } from '../services/VideoLoadingManager';

/**
 * Example 1: Basic Usage with VideoLoadingManager
 * 
 * En basit kullanım şekli - VideoLoadingManager ile entegrasyon
 */
export const BasicUsageExample: React.FC = () => {
  const [videoState, setVideoState] = React.useState<VideoLoadingState>({
    status: 'idle',
    videos: [],
    error: null,
    loadingProgress: 0,
    retryCount: 0,
    requestId: '',
    loadingTime: 0,
  });

  const videoManagerRef = React.useRef<VideoLoadingManager | null>(null);

  // Initialize VideoLoadingManager
  React.useEffect(() => {
    videoManagerRef.current = new VideoLoadingManager();

    // Subscribe to state changes
    const unsubscribe = videoManagerRef.current.subscribe((state) => {
      setVideoState(state);
    });

    return () => {
      unsubscribe();
    };
  }, []);

  // Load videos
  const handleLoadVideos = async () => {
    if (!videoManagerRef.current) return;

    try {
      await videoManagerRef.current.loadVideos({
        goals: ['TYT Matematik', 'TYT Fizik'],
        currentLevel: { matematik: 65, fizik: 50 },
        learningStyle: 'visual',
        preferences: {},
      });
    } catch (error) {
      console.error('Video loading failed:', error);
    }
  };

  // Retry handler
  const handleRetry = () => {
    handleLoadVideos();
  };

  // Fallback handler
  const handleShowFallback = () => {
    console.log('Showing fallback videos...');
    // Show fallback videos logic here
  };

  return (
    <div style={{ padding: '20px' }}>
      <h1>Video Loading UI - Basic Example</h1>

      <button
        onClick={handleLoadVideos}
        style={{
          padding: '12px 24px',
          backgroundColor: '#007bff',
          color: 'white',
          border: 'none',
          borderRadius: '8px',
          fontSize: '15px',
          cursor: 'pointer',
          marginBottom: '30px',
        }}
      >
        Load Videos
      </button>

      <VideoLoadingUI
        state={videoState}
        onRetry={handleRetry}
        onShowFallback={handleShowFallback}
      />

      {/* Display videos when loaded */}
      {videoState.status === 'success' && videoState.videos.length > 0 && (
        <div style={{ marginTop: '30px' }}>
          <h2>Loaded Videos:</h2>
          {videoState.videos.map((subject, index) => (
            <div key={index} style={{ marginBottom: '20px' }}>
              <h3>{subject.subject_exam}</h3>
              <p>Video count: {subject.videos.length}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

/**
 * Example 2: Manual State Control
 * 
 * VideoLoadingManager kullanmadan manuel state kontrolü
 */
export const ManualStateExample: React.FC = () => {
  const [videoState, setVideoState] = React.useState<VideoLoadingState>({
    status: 'idle',
    videos: [],
    error: null,
    loadingProgress: 0,
    retryCount: 0,
    requestId: '',
    loadingTime: 0,
  });

  // Simulate loading
  const simulateLoading = () => {
    setVideoState({
      status: 'loading',
      videos: [],
      error: null,
      loadingProgress: 0,
      retryCount: 0,
      requestId: 'req_123',
      loadingTime: 0,
    });

    // Simulate progress
    let progress = 0;
    const interval = setInterval(() => {
      progress += 10;
      setVideoState((prev) => ({
        ...prev,
        loadingProgress: progress,
      }));

      if (progress >= 100) {
        clearInterval(interval);
        // Simulate success
        setTimeout(() => {
          setVideoState({
            status: 'success',
            videos: [
              {
                subject_exam: 'TYT Matematik',
                videos: [
                  {
                    video_id: '123',
                    title: 'Test Video',
                    channel: 'Test Channel',
                    duration: '10:00',
                    quality_score: 8.5,
                    subject: 'matematik',
                    url: 'https://youtube.com/watch?v=123',
                  },
                ],
                total_count: 1,
              },
            ],
            error: null,
            loadingProgress: 100,
            retryCount: 0,
            requestId: 'req_123',
            loadingTime: 2500,
            cacheHit: false,
          });
        }, 500);
      }
    }, 200);
  };

  // Simulate error
  const simulateError = () => {
    setVideoState({
      status: 'error',
      videos: [],
      error: new Error('Network error'),
      loadingProgress: 0,
      retryCount: 1,
      requestId: 'req_456',
      loadingTime: 5000,
      errorMessage: 'İnternet bağlantınızı kontrol edin.',
    });
  };

  // Simulate fallback
  const simulateFallback = () => {
    setVideoState({
      status: 'fallback',
      videos: [],
      error: new Error('Timeout'),
      loadingProgress: 0,
      retryCount: 2,
      requestId: 'req_789',
      loadingTime: 20000,
      errorMessage: 'Videoları 20 saniye içinde yükleyemedik. Örnek videolar gösteriliyor.',
    });
  };

  return (
    <div style={{ padding: '20px' }}>
      <h1>Video Loading UI - Manual State Example</h1>

      <div style={{ display: 'flex', gap: '10px', marginBottom: '30px' }}>
        <button
          onClick={simulateLoading}
          style={{
            padding: '10px 20px',
            backgroundColor: '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
          }}
        >
          Simulate Loading
        </button>

        <button
          onClick={simulateError}
          style={{
            padding: '10px 20px',
            backgroundColor: '#dc3545',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
          }}
        >
          Simulate Error
        </button>

        <button
          onClick={simulateFallback}
          style={{
            padding: '10px 20px',
            backgroundColor: '#ffc107',
            color: '#212529',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
          }}
        >
          Simulate Fallback
        </button>
      </div>

      <VideoLoadingUI
        state={videoState}
        onRetry={() => {
          console.log('Retry clicked');
          simulateLoading();
        }}
        onShowFallback={() => {
          console.log('Show fallback clicked');
        }}
      />
    </div>
  );
};

/**
 * Example 3: Integration with Learning Path Page
 * 
 * Learning Path sayfasında kullanım örneği
 */
export const LearningPathIntegrationExample: React.FC = () => {
  const [videoState, setVideoState] = React.useState<VideoLoadingState>({
    status: 'idle',
    videos: [],
    error: null,
    loadingProgress: 0,
    retryCount: 0,
    requestId: '',
    loadingTime: 0,
  });

  const [showFallbackVideos, setShowFallbackVideos] = React.useState(false);

  const videoManagerRef = React.useRef<VideoLoadingManager | null>(null);

  React.useEffect(() => {
    videoManagerRef.current = new VideoLoadingManager();

    const unsubscribe = videoManagerRef.current.subscribe((state) => {
      setVideoState(state);

      // Auto-show fallback on fallback state
      if (state.status === 'fallback') {
        setShowFallbackVideos(true);
      }
    });

    return () => {
      unsubscribe();
    };
  }, []);

  const loadVideos = async (profile: any) => {
    if (!videoManagerRef.current) return;

    setShowFallbackVideos(false);

    try {
      await videoManagerRef.current.loadVideos(profile);
    } catch (error) {
      console.error('Video loading failed:', error);
    }
  };

  const handleRetry = () => {
    loadVideos({
      goals: ['TYT Matematik'],
      currentLevel: { matematik: 50 },
      learningStyle: 'visual',
      preferences: {},
    });
  };

  const handleShowFallback = () => {
    setShowFallbackVideos(true);
  };

  return (
    <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
      <h1>Learning Path - Video Recommendations</h1>

      {/* Video Loading UI */}
      {!showFallbackVideos && (
        <VideoLoadingUI
          state={videoState}
          onRetry={handleRetry}
          onShowFallback={handleShowFallback}
        />
      )}

      {/* Success: Display videos */}
      {videoState.status === 'success' && videoState.videos.length > 0 && (
        <div style={{ marginTop: '30px' }}>
          {videoState.videos.map((subject, index) => (
            <div
              key={index}
              style={{
                backgroundColor: 'white',
                padding: '20px',
                borderRadius: '12px',
                boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                marginBottom: '20px',
              }}
            >
              <h2 style={{ margin: '0 0 15px 0', color: '#333' }}>
                {subject.subject_exam}
              </h2>

              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
                  gap: '15px',
                }}
              >
                {subject.videos.map((video, vIndex) => (
                  <div
                    key={vIndex}
                    style={{
                      border: '1px solid #e9ecef',
                      borderRadius: '8px',
                      padding: '15px',
                      transition: 'transform 0.2s ease',
                      cursor: 'pointer',
                    }}
                    onMouseOver={(e) => {
                      e.currentTarget.style.transform = 'translateY(-5px)';
                      e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
                    }}
                    onMouseOut={(e) => {
                      e.currentTarget.style.transform = 'translateY(0)';
                      e.currentTarget.style.boxShadow = 'none';
                    }}
                  >
                    <h4 style={{ margin: '0 0 8px 0', fontSize: '15px', color: '#333' }}>
                      {video.title}
                    </h4>
                    <p style={{ margin: '0', fontSize: '13px', color: '#666' }}>
                      📺 {video.channel} • ⏱️ {video.duration}
                    </p>
                    <p style={{ margin: '8px 0 0 0', fontSize: '13px', color: '#007bff' }}>
                      ⭐ Kalite: {video.quality_score.toFixed(1)}/10
                    </p>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Fallback videos */}
      {showFallbackVideos && (
        <div
          style={{
            backgroundColor: '#fff3cd',
            padding: '20px',
            borderRadius: '12px',
            marginTop: '30px',
            border: '2px solid #ffc107',
          }}
        >
          <h2 style={{ margin: '0 0 15px 0', color: '#856404' }}>
            📺 Örnek Videolar
          </h2>
          <p style={{ margin: '0 0 15px 0', color: '#856404' }}>
            Kişiselleştirilmiş videolar yüklenemedi. İşte genel eğitim içerikleri:
          </p>
          {/* Fallback video list here */}
        </div>
      )}
    </div>
  );
};

export default {
  BasicUsageExample,
  ManualStateExample,
  LearningPathIntegrationExample,
};
