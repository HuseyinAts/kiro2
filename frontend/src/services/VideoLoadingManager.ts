/**
 * VideoLoadingManager - Merkezi video yükleme state management
 *
 * Bu servis, Learning Path sayfasında video yükleme işlemlerini yönetir.
 * State management, retry logic, timeout handling ve error handling sağlar.
 *
 * @module VideoLoadingManager
 * @requires Requirements: 3.1, 3.2, 3.9, 3.14, 10.1, 10.2, 10.3
 */

/**
 * Video öneri veri modeli
 */
export interface VideoRecommendation {
  video_id: string;
  title: string;
  channel: string;
  channel_id?: string;
  duration: string;
  view_count?: number;
  upload_date?: string;
  thumbnail?: string;
  quality_score: number;
  subject: string;
  difficulty?: string;
  exam_type?: string;
  url: string;
  language_score?: number;
  relevance_score?: number;
  difficulty_match?: number;
}

/**
 * Konu bazlı video kategorisi
 */
export interface SubjectVideos {
  subject_exam: string;
  videos: VideoRecommendation[];
  total_count?: number;
  cache_hit?: boolean;
  response_time_ms?: number;
}

/**
 * Öğrenci profili (video yükleme için)
 */
export interface StudentProfile {
  goals: string[];
  current_level: Record<string, number>;  // ✅ Fixed: snake_case for backend
  learning_style: string;  // ✅ Fixed: snake_case for backend
  preferences?: Record<string, any>;
}

/**
 * Video yükleme durumu
 */
export type VideoLoadingStatus = 'idle' | 'loading' | 'success' | 'error' | 'fallback';

/**
 * Video yükleme state
 */
export interface VideoLoadingState {
  status: VideoLoadingStatus;
  videos: SubjectVideos[];
  error: Error | null;
  loadingProgress: number; // 0-100
  retryCount: number;
  requestId: string;
  loadingTime: number; // milliseconds
  cacheHit?: boolean;
  errorMessage?: string;
}

/**
 * State değişiklik callback tipi
 */
export type StateChangeCallback = (state: VideoLoadingState) => void;

/**
 * VideoLoadingManager - Video yükleme orchestration
 *
 * Özellikler:
 * - Merkezi state management
 * - Automatic retry with exponential backoff
 * - Request cancellation (AbortController)
 * - Progress tracking
 * - Error handling
 * - State subscription mechanism
 */
export class VideoLoadingManager {
  private state: VideoLoadingState;
  private abortController: AbortController | null = null;
  private subscribers: Set<StateChangeCallback> = new Set();
  private apiBaseUrl: string;
  private timeout: number;
  private maxRetries: number;

  /**
   * VideoLoadingManager constructor
   *
   * @param apiBaseUrl - Backend API base URL
   * @param timeout - Request timeout in milliseconds (default: 20000)
   * @param maxRetries - Maximum retry attempts (default: 2)
   */
  constructor(
    apiBaseUrl: string = import.meta.env.VITE_API_URL || 'http://localhost:8001',
    timeout: number = 20000,
    maxRetries: number = 2,
  ) {
    this.apiBaseUrl = apiBaseUrl;
    this.timeout = timeout;
    this.maxRetries = maxRetries;

    // Initialize state
    this.state = {
      status: 'idle',
      videos: [],
      error: null,
      loadingProgress: 0,
      retryCount: 0,
      requestId: '',
      loadingTime: 0,
    };
  }

  /**
   * Video yükleme işlemini başlat
   *
   * @param profile - Öğrenci profili
   * @returns Promise<SubjectVideos[]>
   */
  async loadVideos(profile: StudentProfile): Promise<SubjectVideos[]> {
    // Generate unique request ID
    const requestId = this._generateRequestId();
    const startTime = Date.now();

    // Update state to loading
    this._updateState({
      status: 'loading',
      videos: [],
      error: null,
      loadingProgress: 10,
      retryCount: 0,
      requestId,
      loadingTime: 0,
    });

    try {
      // Create abort controller for cancellation
      this.abortController = new AbortController();

      // Set timeout
      const timeoutId = setTimeout(() => {
        if (this.abortController) {
          console.warn(`⏰ Video API timeout after ${this.timeout}ms`);
          this.abortController.abort();
        }
      }, this.timeout);

      // Update progress
      this._updateProgress(30);

      // Extract subject from goals (first goal as primary subject)
      const primaryGoal = profile.goals && profile.goals.length > 0 ? profile.goals[0] : 'Genel';
      const subject = primaryGoal.split(' ')[0]; // Extract subject name from goal string

      // Determine difficulty from current level
      const avgLevel = Object.values(profile.current_level || {}).reduce((a, b) => a + b, 0) /
                       Math.max(Object.keys(profile.current_level || {}).length, 1);
      const difficulty = avgLevel < 30 ? 'kolay' : avgLevel < 70 ? 'orta' : 'zor';

      // Make API call
      // VideoLoadingManager: Starting API call

      // Get auth token
      const token = localStorage.getItem('access_token');
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(`${this.apiBaseUrl}/api/learning-path/search-resources`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          subject,
          topic: primaryGoal,
          difficulty,
          max_results: 10,
          student_profile: {
            learning_style: profile.learning_style,
            goals: profile.goals,
            current_level: profile.current_level,
          },
        }),
        signal: this.abortController.signal,
      });

      // Clear timeout
      clearTimeout(timeoutId);

      // Update progress
      this._updateProgress(70);

      // Check response
      if (!response.ok) {
        throw new Error(`Backend error: ${response.status} ${response.statusText}`);
      }

      // Parse response
      const data = await response.json();
      const recommendations: SubjectVideos[] = data.recommendations || data || [];

      // Calculate loading time
      const loadingTime = Date.now() - startTime;

      // Update progress
      this._updateProgress(100);

      // Update state to success
      this._updateState({
        status: 'success',
        videos: recommendations,
        error: null,
        loadingProgress: 100,
        retryCount: this.state.retryCount,
        requestId,
        loadingTime,
        cacheHit: data.cache_hit,
      });

      // VideoLoadingManager: Videos loaded successfully

      return recommendations;

    } catch (error) {
      const loadingTime = Date.now() - startTime;

      // Handle abort (timeout)
      if (error instanceof Error && error.name === 'AbortError') {
        console.warn('⏰ VideoLoadingManager: Request timeout', {
          requestId,
          timeout: this.timeout,
          loadingTime: `${loadingTime}ms`,
        });

        // Check if we should retry
        if (this.state.retryCount < this.maxRetries) {
          // VideoLoadingManager: Retrying
          return this.retryLoad(profile);
        }

        // Max retries reached - use fallback
        this._updateState({
          status: 'fallback',
          videos: [],
          error: new Error('Request timeout - max retries reached'),
          loadingProgress: 0,
          retryCount: this.state.retryCount,
          requestId,
          loadingTime,
          errorMessage: `Videoları ${this.timeout / 1000} saniye içinde yükleyemedik. Örnek videolar gösteriliyor.`,
        });

        throw error;
      }

      // Handle other errors
      console.error('❌ VideoLoadingManager: Error loading videos', {
        requestId,
        error: error instanceof Error ? error.message : String(error),
        loadingTime: `${loadingTime}ms`,
      });

      // Check if we should retry
      if (this.state.retryCount < this.maxRetries && this._isRetryableError(error)) {
        // VideoLoadingManager: Retrying
        return this.retryLoad(profile);
      }

      // Update state to error
      this._updateState({
        status: 'error',
        videos: [],
        error: error instanceof Error ? error : new Error(String(error)),
        loadingProgress: 0,
        retryCount: this.state.retryCount,
        requestId,
        loadingTime,
        errorMessage: this._getUserFriendlyErrorMessage(error),
      });

      throw error;
    } finally {
      this.abortController = null;
    }
  }

  /**
   * Retry video loading with exponential backoff
   *
   * @param profile - Öğrenci profili
   * @returns Promise<SubjectVideos[]>
   */
  async retryLoad(profile: StudentProfile): Promise<SubjectVideos[]> {
    const retryCount = this.state.retryCount + 1;

    // Calculate exponential backoff delay
    const delay = Math.min(1000 * Math.pow(2, retryCount - 1), 5000); // Max 5 seconds

    // VideoLoadingManager: Waiting before retry

    // Update retry count
    this._updateState({
      ...this.state,
      retryCount,
    });

    // Wait before retry
    await new Promise(resolve => setTimeout(resolve, delay));

    // Retry load
    return this.loadVideos(profile);
  }

  /**
   * Cancel ongoing video loading
   */
  cancelLoad(): void {
    if (this.abortController) {
      // VideoLoadingManager: Cancelling request
      this.abortController.abort();
      this.abortController = null;

      this._updateState({
        status: 'idle',
        videos: [],
        error: new Error('Request cancelled by user'),
        loadingProgress: 0,
        retryCount: 0,
        requestId: '',
        loadingTime: 0,
      });
    }
  }

  /**
   * Get current state
   *
   * @returns VideoLoadingState
   */
  getState(): VideoLoadingState {
    return { ...this.state };
  }

  /**
   * Subscribe to state changes
   *
   * @param callback - State change callback
   * @returns Unsubscribe function
   */
  subscribe(callback: StateChangeCallback): () => void {
    this.subscribers.add(callback);

    // Return unsubscribe function
    return () => {
      this.subscribers.delete(callback);
    };
  }

  /**
   * Reset state to idle
   */
  reset(): void {
    this._updateState({
      status: 'idle',
      videos: [],
      error: null,
      loadingProgress: 0,
      retryCount: 0,
      requestId: '',
      loadingTime: 0,
    });
  }

  // Private methods

  /**
   * Update state and notify subscribers
   */
  private _updateState(newState: Partial<VideoLoadingState>): void {
    this.state = {
      ...this.state,
      ...newState,
    };

    // Notify all subscribers
    this.subscribers.forEach(callback => {
      try {
        callback(this.state);
      } catch (error) {
        console.error('❌ VideoLoadingManager: Error in subscriber callback', error);
      }
    });
  }

  /**
   * Update loading progress
   */
  private _updateProgress(progress: number): void {
    this._updateState({
      loadingProgress: Math.min(100, Math.max(0, progress)),
    });
  }

  /**
   * Generate unique request ID
   */
  private _generateRequestId(): string {
    return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Check if error is retryable
   */
  private _isRetryableError(error: unknown): boolean {
    if (error instanceof Error) {
      // Network errors are retryable
      if (error.name === 'TypeError' || error.message.includes('fetch')) {
        return true;
      }

      // Timeout errors are retryable
      if (error.name === 'AbortError') {
        return true;
      }

      // Server errors (5xx) are retryable
      if (error.message.includes('500') || error.message.includes('502') || error.message.includes('503')) {
        return true;
      }
    }

    return false;
  }

  /**
   * Get user-friendly error message
   */
  private _getUserFriendlyErrorMessage(error: unknown): string {
    if (error instanceof Error) {
      // Timeout
      if (error.name === 'AbortError') {
        return 'İstek zaman aşımına uğradı. Lütfen tekrar deneyin.';
      }

      // Network error
      if (error.name === 'TypeError' || error.message.includes('fetch')) {
        return 'İnternet bağlantınızı kontrol edin.';
      }

      // Backend error
      if (error.message.includes('Backend error')) {
        return 'Video servisi şu anda erişilebilir değil. Lütfen birkaç dakika sonra tekrar deneyin.';
      }

      // CORS error
      if (error.message.includes('CORS')) {
        return 'Bağlantı hatası oluştu. Lütfen sistem yöneticisi ile iletişime geçin.';
      }

      // Rate limit
      if (error.message.includes('429') || error.message.includes('rate limit')) {
        return 'Çok fazla istek gönderildi. Lütfen biraz bekleyin.';
      }

      // Generic server error
      if (error.message.includes('500') || error.message.includes('502') || error.message.includes('503')) {
        return 'Sunucu hatası oluştu. Lütfen tekrar deneyin.';
      }
    }

    return 'Beklenmeyen bir hata oluştu. Lütfen tekrar deneyin.';
  }
}

/**
 * Singleton instance for global usage
 */
let globalInstance: VideoLoadingManager | null = null;

/**
 * Get or create global VideoLoadingManager instance
 *
 * @returns VideoLoadingManager
 */
export function getVideoLoadingManager(): VideoLoadingManager {
  if (!globalInstance) {
    globalInstance = new VideoLoadingManager();
  }
  return globalInstance;
}

/**
 * Create new VideoLoadingManager instance
 *
 * @param apiBaseUrl - Backend API base URL
 * @param timeout - Request timeout in milliseconds
 * @param maxRetries - Maximum retry attempts
 * @returns VideoLoadingManager
 */
export function createVideoLoadingManager(
  apiBaseUrl?: string,
  timeout?: number,
  maxRetries?: number,
): VideoLoadingManager {
  return new VideoLoadingManager(apiBaseUrl, timeout, maxRetries);
}

export default VideoLoadingManager;
