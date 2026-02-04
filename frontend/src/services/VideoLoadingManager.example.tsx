/**
 * VideoLoadingManager Usage Examples
 * 
 * Bu dosya VideoLoadingManager servisinin nasıl kullanılacağını gösterir.
 */

import React, { useEffect, useState } from 'react';
import { 
  VideoLoadingManager, 
  getVideoLoadingManager,
  VideoLoadingState,
  StudentProfile,
  SubjectVideos 
} from './VideoLoadingManager';

/**
 * Example 1: Basic Usage with React Hook
 */
export function useVideoLoading() {
  const [state, setState] = useState<VideoLoadingState | null>(null);
  const [manager] = useState(() => getVideoLoadingManager());

  useEffect(() => {
    // Subscribe to state changes
    const unsubscribe = manager.subscribe((newState) => {
      setState(newState);
    });

    // Cleanup
    return () => {
      unsubscribe();
    };
  }, [manager]);

  const loadVideos = async (profile: StudentProfile) => {
    try {
      const videos = await manager.loadVideos(profile);
      return videos;
    } catch (error) {
      console.error('Failed to load videos:', error);
      throw error;
    }
  };

  const retry = async (profile: StudentProfile) => {
    try {
      const videos = await manager.retryLoad(profile);
      return videos;
    } catch (error) {
      console.error('Failed to retry:', error);
      throw error;
    }
  };

  const cancel = () => {
    manager.cancelLoad();
  };

  const reset = () => {
    manager.reset();
  };

  return {
    state,
    loadVideos,
    retry,
    cancel,
    reset,
  };
}

/**
 * Example 2: React Component with VideoLoadingManager
 */
export function VideoLoadingExample() {
  const { state, loadVideos, retry, cancel } = useVideoLoading();

  const handleLoadVideos = async () => {
    const profile: StudentProfile = {
      goals: ['TYT Matematik', 'TYT Fizik'],
      currentLevel: {
        matematik: 65,
        fizik: 50,
      },
      learningStyle: 'visual',
      preferences: {
        video_duration: 'medium',
      },
    };

    try {
      await loadVideos(profile);
    } catch (error) {
      console.error('Error loading videos:', error);
    }
  };

  const handleRetry = async () => {
    const profile: StudentProfile = {
      goals: ['TYT Matematik'],
      currentLevel: { matematik: 50 },
      learningStyle: 'visual',
    };

    try {
      await retry(profile);
    } catch (error) {
      console.error('Error retrying:', error);
    }
  };

  if (!state) {
    return <div>Initializing...</div>;
  }

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial' }}>
      <h2>🎥 Video Loading Manager Example</h2>

      {/* Status Display */}
      <div style={{ 
        padding: '15px', 
        backgroundColor: '#f8f9fa', 
        borderRadius: '8px',
        marginBottom: '20px' 
      }}>
        <h3>Current Status</h3>
        <p><strong>Status:</strong> {state.status}</p>
        <p><strong>Progress:</strong> {state.loadingProgress}%</p>
        <p><strong>Retry Count:</strong> {state.retryCount}</p>
        <p><strong>Request ID:</strong> {state.requestId || 'N/A'}</p>
        <p><strong>Loading Time:</strong> {state.loadingTime}ms</p>
        {state.cacheHit !== undefined && (
          <p><strong>Cache Hit:</strong> {state.cacheHit ? '✅ Yes' : '❌ No'}</p>
        )}
      </div>

      {/* Loading State */}
      {state.status === 'loading' && (
        <div style={{ 
          padding: '20px', 
          backgroundColor: '#e3f2fd', 
          borderRadius: '8px',
          marginBottom: '20px' 
        }}>
          <h3>🔄 Loading Videos...</h3>
          <div style={{ 
            width: '100%', 
            backgroundColor: '#ccc', 
            borderRadius: '10px',
            height: '20px',
            overflow: 'hidden' 
          }}>
            <div style={{ 
              width: `${state.loadingProgress}%`, 
              backgroundColor: '#2196F3',
              height: '100%',
              transition: 'width 0.3s ease' 
            }} />
          </div>
          <p style={{ marginTop: '10px' }}>
            🤖 AI size özel videoları buluyor... {state.loadingProgress}%
          </p>
          <button 
            onClick={cancel}
            style={{
              padding: '10px 20px',
              backgroundColor: '#dc3545',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              marginTop: '10px'
            }}
          >
            ❌ Cancel
          </button>
        </div>
      )}

      {/* Success State */}
      {state.status === 'success' && (
        <div style={{ 
          padding: '20px', 
          backgroundColor: '#d4edda', 
          borderRadius: '8px',
          marginBottom: '20px' 
        }}>
          <h3>✅ Videos Loaded Successfully!</h3>
          <p>
            <strong>Total Categories:</strong> {state.videos.length}
          </p>
          <p>
            <strong>Total Videos:</strong> {
              state.videos.reduce((sum, cat) => sum + cat.videos.length, 0)
            }
          </p>
          <p>
            <strong>Loading Time:</strong> {state.loadingTime}ms
          </p>
          
          {/* Video List */}
          <div style={{ marginTop: '15px' }}>
            {state.videos.map((category, idx) => (
              <div 
                key={idx}
                style={{ 
                  padding: '10px', 
                  backgroundColor: 'white',
                  borderRadius: '6px',
                  marginBottom: '10px' 
                }}
              >
                <h4>{category.subject_exam}</h4>
                <p>Videos: {category.videos.length}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Error State */}
      {state.status === 'error' && (
        <div style={{ 
          padding: '20px', 
          backgroundColor: '#f8d7da', 
          borderRadius: '8px',
          marginBottom: '20px' 
        }}>
          <h3>❌ Error Loading Videos</h3>
          <p><strong>Error:</strong> {state.errorMessage || state.error?.message}</p>
          <button 
            onClick={handleRetry}
            style={{
              padding: '10px 20px',
              backgroundColor: '#ffc107',
              color: '#212529',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              marginTop: '10px'
            }}
          >
            🔄 Retry
          </button>
        </div>
      )}

      {/* Fallback State */}
      {state.status === 'fallback' && (
        <div style={{ 
          padding: '20px', 
          backgroundColor: '#fff3cd', 
          borderRadius: '8px',
          marginBottom: '20px' 
        }}>
          <h3>⚠️ Using Fallback Videos</h3>
          <p>{state.errorMessage}</p>
          <button 
            onClick={handleRetry}
            style={{
              padding: '10px 20px',
              backgroundColor: '#17a2b8',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              marginTop: '10px'
            }}
          >
            🔄 Try Again
          </button>
        </div>
      )}

      {/* Action Buttons */}
      <div style={{ display: 'flex', gap: '10px', marginTop: '20px' }}>
        <button 
          onClick={handleLoadVideos}
          disabled={state.status === 'loading'}
          style={{
            padding: '12px 24px',
            backgroundColor: state.status === 'loading' ? '#ccc' : '#28a745',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            cursor: state.status === 'loading' ? 'not-allowed' : 'pointer',
            fontSize: '16px',
            fontWeight: 'bold'
          }}
        >
          🚀 Load Videos
        </button>
      </div>
    </div>
  );
}

/**
 * Example 3: Standalone Usage (without React)
 */
export async function standaloneExample() {
  // Create manager instance
  const manager = new VideoLoadingManager(
    'http://localhost:8001',
    20000, // 20 second timeout
    2      // 2 retry attempts
  );

  // Subscribe to state changes
  const unsubscribe = manager.subscribe((state) => {
    console.log('State changed:', state);
  });

  // Student profile
  const profile: StudentProfile = {
    goals: ['TYT Matematik', 'AYT Fizik'],
    currentLevel: {
      matematik: 70,
      fizik: 60,
    },
    learningStyle: 'visual',
  };

  try {
    // Load videos
    console.log('Loading videos...');
    const videos = await manager.loadVideos(profile);
    console.log('Videos loaded:', videos);

  } catch (error) {
    console.error('Error:', error);

    // Check if we should show fallback
    const state = manager.getState();
    if (state.status === 'fallback') {
      console.log('Using fallback videos');
    }
  } finally {
    // Cleanup
    unsubscribe();
  }
}

/**
 * Example 4: Advanced Usage with Custom Configuration
 */
export function advancedExample() {
  // Create custom manager with specific configuration
  const manager = new VideoLoadingManager(
    'https://api.production.com',
    30000, // 30 second timeout for production
    3      // 3 retry attempts
  );

  // Multiple subscribers
  const logSubscriber = manager.subscribe((state) => {
    console.log('[LOG]', state.status, state.loadingProgress);
  });

  const analyticsSubscriber = manager.subscribe((state) => {
    // Send analytics
    if (state.status === 'success') {
      console.log('[ANALYTICS] Videos loaded in', state.loadingTime, 'ms');
    }
  });

  const errorSubscriber = manager.subscribe((state) => {
    // Error tracking
    if (state.status === 'error') {
      console.error('[ERROR TRACKING]', state.error);
    }
  });

  // Cleanup all subscribers
  return () => {
    logSubscriber();
    analyticsSubscriber();
    errorSubscriber();
  };
}

export default VideoLoadingExample;
