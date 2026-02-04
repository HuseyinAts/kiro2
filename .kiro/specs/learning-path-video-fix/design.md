# Design Document - Learning Path Video Yükleme Sorunu Çözümü

## Overview

Learning Path sayfasında video yükleme işlemi sistematik olarak başarısız oluyor. Bu doküman, sorunu çözmek için kapsamlı bir teknik tasarım sunmaktadır. Çözüm, backend servis diagnostics, performance optimization, error handling, cache stratejisi, Türkçe içerik filtreleme ve kullanıcı deneyimi iyileştirmelerini içermektedir.

### Problem Statement

**Mevcut Durum:**
- Frontend `/api/youtube/recommendations` endpoint'ine POST isteği gönderiyor
- 10 saniye timeout sonrası "Videoları 10 saniye içinde yükleyemedik" hatası
- Kullanıcılar fallback videolar görüyor
- Kişiselleştirilmiş video önerileri çalışmıyor
- Sistem başlangıcında bağımlı servislerin sağlık kontrolü yapılmıyor

**Hedef Durum:**
- Video önerileri 3 saniye içinde yüklenmeli (P95 latency)
- %99.9 başarı oranı
- Sadece Türkçe ve alakalı videolar
- Kapsamlı error handling ve monitoring
- Mükemmel kullanıcı deneyimi
- Sistem başlangıcında tüm bağımlı servislerin sağlık kontrolü

### Success Metrics

- **Performance:** P95 response time < 3 saniye
- **Reliability:** %99.9 uptime, %95+ başarı oranı
- **Quality:** %70+ relevance score, %100 Türkçe içerik
- **User Experience:** %90+ kullanıcı memnuniyeti
- **Cache:** %80+ cache hit rate
- **Startup Health:** Tüm kritik bağımlılıklar başlangıçta doğrulanmalı

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Learning Path Page (main.tsx)                           │  │
│  │  - Video Loading State Management                        │  │
│  │  - Error Handling & Retry Logic                          │  │
│  │  - User Feedback & Progress Indicators                   │  │
│  │  - Offline Mode & Network Detection                      │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP POST /api/youtube/recommendations
                              │ (20s timeout, retry logic)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Startup Health Check (Req 0)                           │  │
│  │  - Database connectivity verification                    │  │
│  │  - Redis cache availability check                        │  │
│  │  - YouTube API connection test                           │  │
│  │  - CORS configuration validation                         │  │
│  │  - Structured logging initialization                     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  API Layer (youtube_routes.py)                           │  │
│  │  - Request Validation                                    │  │
│  │  - Rate Limiting & Throttling                            │  │
│  │  - Health Check Endpoints                                │  │
│  │  - Circuit Breaker Protection                            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Service Layer                                           │  │
│  │  ┌────────────────────────────────────────────────────┐ │  │
│  │  │  VideoRecommendationService (NEW)                  │ │  │
│  │  │  - Orchestrates video discovery                    │ │  │
│  │  │  - Multi-layer cache management                    │ │  │
│  │  │  - Parallel video search execution                 │ │  │
│  │  │  - Request ID tracking                             │ │  │
│  │  └────────────────────────────────────────────────────┘ │  │
│  │                                                            │  │
│  │  ┌────────────────────────────────────────────────────┐ │  │
│  │  │  AdvancedYouTubeSearch                             │ │  │
│  │  │  - Video search with filters                       │ │  │
│  │  │  - Quality scoring                                  │ │  │
│  │  └────────────────────────────────────────────────────┘ │  │
│  │                                                            │  │
│  │  ┌────────────────────────────────────────────────────┐ │  │
│  │  │  SemanticYouTubeSearch                             │ │  │
│  │  │  - Embedding-based search                          │ │  │
│  │  │  - Cosine similarity matching                      │ │  │
│  │  └────────────────────────────────────────────────────┘ │  │
│  │                                                            │  │
│  │  ┌────────────────────────────────────────────────────┐ │  │
│  │  │  TurkishContentFilter (NEW) (Req 13-15)           │ │  │
│  │  │  - Multi-signal language detection                │ │  │
│  │  │  - MEB curriculum-based relevance scoring         │ │  │
│  │  │  - Adaptive difficulty matching                   │ │  │
│  │  │  - Subject taxonomy categorization                │ │  │
│  │  │  - Trusted channel verification                   │ │  │
│  │  └────────────────────────────────────────────────────┘ │  │
│  │                                                            │  │
│  │  ┌────────────────────────────────────────────────────┐ │  │
│  │  │  HealthCheckService (NEW)                          │ │  │
│  │  │  - Component health monitoring                     │ │  │
│  │  │  - System metrics collection                       │ │  │
│  │  └────────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Data Layer                                              │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────────────┐ │  │
│  │  │   Redis    │  │  SQLite    │  │  YouTube Data API  │ │  │
│  │  │   Cache    │  │  Database  │  │       v3           │ │  │
│  │  │ (Multi-    │  │ (Indexed)  │  │  (Rate Limited)    │ │  │
│  │  │  Layer)    │  │            │  │                    │ │  │
│  │  └────────────┘  └────────────┘  └────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Startup Sequence (Requirement 0)

```
1. Backend Application Start
   ↓
2. Initialize Configuration
   - Load environment variables
   - Validate API keys
   - Set CORS origins
   ↓
3. Initialize Structured Logging
   - Configure JSON format
   - Set log levels
   ↓
4. Health Check: Database
   - Test connection
   - Verify schema
   - Log result (INFO/WARNING)
   ↓
5. Health Check: Redis Cache
   - Test connection
   - Verify read/write
   - Log result (INFO/WARNING)
   ↓
6. Health Check: YouTube API
   - Test API key validity
   - Check quota availability
   - Log result (INFO/WARNING)
   ↓
7. Initialize Services
   - VideoRecommendationService
   - TurkishContentFilter
   - HealthCheckService
   ↓
8. Register API Routes
   - /api/youtube/recommendations
   - /api/youtube/health
   - /api/youtube/test
   ↓
9. Start Metrics Collection
   - Prometheus endpoint
   - Initial metrics
   ↓
10. Application Ready
    - Log startup summary
    - Report to metrics
    - Accept requests

Note: Kritik servis başarısız olsa bile uygulama başlar,
ancak WARNING seviyesinde log kaydedilir ve metrics'e raporlanır.
```


### Component Interaction Flow

```
1. User opens Learning Path page
   ↓
2. Frontend: Initialize video loading state
   ↓
3. Frontend: Show loading indicator "AI size özel videoları buluyor..."
   ↓
4. Frontend: POST /api/youtube/recommendations
   - Body: { goals, currentLevel, learningStyle, preferences }
   - Timeout: 20 seconds
   - Retry: 2 attempts with exponential backoff
   ↓
5. Backend: Receive request
   ↓
6. Backend: Generate request_id, log request
   ↓
7. Backend: Check cache (Redis)
   - Cache key: hash(student_profile)
   - TTL: 1 hour
   ↓
8a. Cache HIT (80% of requests)
   ↓
   Return cached videos (< 100ms)
   ↓
   Go to step 14
   
8b. Cache MISS (20% of requests)
   ↓
9. Backend: VideoRecommendationService.get_recommendations()
   ↓
10. For each goal (parallel execution):
    ↓
    10a. AdvancedYouTubeSearch.search_videos_with_filters()
    ↓
    10b. SemanticYouTubeSearch.semantic_search_videos()
    ↓
    10c. Merge and deduplicate results
    ↓
    10d. TurkishContentFilter.filter_videos()
         - Language detection
         - Relevance scoring (>70%)
         - Difficulty matching (±1 level)
    ↓
    10e. Sort by quality_score
    ↓
    10f. Take top 5 videos per subject
    ↓
11. Backend: Aggregate all results
    ↓
12. Backend: Cache results (Redis)
    ↓
13. Backend: Log metrics (response time, cache status)
    ↓
14. Backend: Return response
    - Status: 200 OK
    - Body: { recommendations: [...], total_count: X }
    ↓
15. Frontend: Receive response
    ↓
16. Frontend: Update UI with videos
    - Show success message
    - Display video cards
    - Enable video playback
    ↓
17. Frontend: Log success metrics

ERROR FLOW:
- If timeout (20s): Show fallback videos + retry option
- If 500 error: Log error, show user-friendly message
- If network error: Check connectivity, show offline message
- If CORS error: Log to Sentry, contact admin
```

## Components and Interfaces

### 0. Startup and Health Check Components (Requirement 0)

#### Startup Event Handler
**Responsibility:** Backend başlangıcında sağlık kontrolü yapma

```python
# backend/main.py

from fastapi import FastAPI
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan - startup ve shutdown events
    """
    # Startup
    logger.info("application_starting")
    
    # Initialize services
    health_service = HealthCheckService(
        youtube_api=youtube_api,
        database=database,
        cache=cache,
        metrics=metrics
    )
    
    # Perform startup health check (Req 0.1, 0.2, 0.6, 0.7)
    startup_result = await health_service.startup_health_check()
    
    if not startup_result.success:
        logger.warning(
            "application_started_with_warnings",
            warnings=startup_result.warnings,
            errors=startup_result.errors
        )
    else:
        logger.info(
            "application_started_successfully",
            startup_time_ms=startup_result.startup_time_ms
        )
    
    # Store health service in app state
    app.state.health_service = health_service
    
    yield
    
    # Shutdown
    logger.info("application_shutting_down")

app = FastAPI(lifespan=lifespan)

# CORS configuration (Req 0.4)
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3001",  # Frontend development
        "http://localhost:3000",
        os.getenv("FRONTEND_URL", "")
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### API Test Endpoint (Requirement 0.3)
**Responsibility:** API erişilebilirlik testi

```python
# backend/api/youtube_routes.py

@router.get("/test")
async def test_api_connectivity():
    """
    API erişilebilirlik testi endpoint'i (Req 0.3)
    
    Frontend bu endpoint'i kullanarak backend'in
    erişilebilir olduğunu doğrular.
    """
    return {
        "status": "ok",
        "message": "YouTube API service is reachable",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }
```

### 1. Frontend Components

#### VideoLoadingManager (NEW)
**Responsibility:** Merkezi video yükleme state management

```typescript
interface VideoLoadingState {
  status: 'idle' | 'loading' | 'success' | 'error' | 'fallback';
  videos: VideoRecommendation[];
  error: Error | null;
  loadingProgress: number; // 0-100
  retryCount: number;
  requestId: string;
  loadingTime: number; // milliseconds
}

class VideoLoadingManager {
  private state: VideoLoadingState;
  private abortController: AbortController;
  
  async loadVideos(profile: StudentProfile): Promise<void>;
  async retryLoad(): Promise<void>;
  cancelLoad(): void;
  getState(): VideoLoadingState;
  subscribe(callback: (state: VideoLoadingState) => void): void;
}
```

#### VideoErrorHandler (NEW)
**Responsibility:** Hata yönetimi ve kullanıcı geri bildirimi

```typescript
interface VideoError {
  type: 'timeout' | 'network' | 'server' | 'cors' | 'unknown';
  message: string;
  userMessage: string;
  retryable: boolean;
  statusCode?: number;
}

class VideoErrorHandler {
  handleError(error: Error): VideoError;
  getUserMessage(error: VideoError): string;
  shouldRetry(error: VideoError): boolean;
  logError(error: VideoError, context: any): void;
}
```

#### NetworkStatusManager (NEW)
**Responsibility:** Ağ durumu izleme ve offline mode yönetimi (Requirement 5.19)

```typescript
interface NetworkStatus {
  online: boolean;
  effectiveType?: string; // '4g', '3g', '2g', 'slow-2g'
  downlink?: number; // Mbps
  rtt?: number; // Round-trip time in ms
}

class NetworkStatusManager {
  private status: NetworkStatus;
  private listeners: Set<(status: NetworkStatus) => void>;
  
  constructor() {
    this.status = {
      online: navigator.onLine,
      effectiveType: (navigator as any).connection?.effectiveType,
      downlink: (navigator as any).connection?.downlink,
      rtt: (navigator as any).connection?.rtt
    };
    
    this.listeners = new Set();
    this.setupListeners();
  }
  
  private setupListeners(): void {
    // Online/offline events
    window.addEventListener('online', () => this.handleOnline());
    window.addEventListener('offline', () => this.handleOffline());
    
    // Connection change events
    (navigator as any).connection?.addEventListener('change', () => {
      this.updateStatus();
    });
  }
  
  private handleOnline(): void {
    this.status.online = true;
    this.notifyListeners();
    
    // Auto-retry pending requests
    this.retryPendingRequests();
  }
  
  private handleOffline(): void {
    this.status.online = false;
    this.notifyListeners();
  }
  
  private updateStatus(): void {
    const conn = (navigator as any).connection;
    this.status = {
      online: navigator.onLine,
      effectiveType: conn?.effectiveType,
      downlink: conn?.downlink,
      rtt: conn?.rtt
    };
    this.notifyListeners();
  }
  
  subscribe(callback: (status: NetworkStatus) => void): () => void {
    this.listeners.add(callback);
    
    // Return unsubscribe function
    return () => {
      this.listeners.delete(callback);
    };
  }
  
  private notifyListeners(): void {
    this.listeners.forEach(listener => listener(this.status));
  }
  
  getStatus(): NetworkStatus {
    return { ...this.status };
  }
  
  isOnline(): boolean {
    return this.status.online;
  }
  
  private async retryPendingRequests(): Promise<void> {
    // Trigger retry for any pending video requests
    // This will be called by VideoLoadingManager
  }
}
```

#### OfflineModeManager (NEW)
**Responsibility:** Offline mode UI ve data synchronization

```typescript
interface OfflineData {
  cachedVideos: VideoRecommendation[];
  lastSync: Date;
  pendingRequests: any[];
}

class OfflineModeManager {
  private offlineData: OfflineData;
  private networkManager: NetworkStatusManager;
  
  constructor(networkManager: NetworkStatusManager) {
    this.networkManager = networkManager;
    this.offlineData = this.loadOfflineData();
    
    // Subscribe to network status changes
    this.networkManager.subscribe((status) => {
      if (status.online) {
        this.syncWhenOnline();
      }
    });
  }
  
  private loadOfflineData(): OfflineData {
    // Load from localStorage
    const stored = localStorage.getItem('offline_video_data');
    return stored ? JSON.parse(stored) : {
      cachedVideos: [],
      lastSync: new Date(),
      pendingRequests: []
    };
  }
  
  cacheVideos(videos: VideoRecommendation[]): void {
    this.offlineData.cachedVideos = videos;
    this.offlineData.lastSync = new Date();
    this.saveOfflineData();
  }
  
  getCachedVideos(): VideoRecommendation[] {
    return this.offlineData.cachedVideos;
  }
  
  addPendingRequest(request: any): void {
    this.offlineData.pendingRequests.push(request);
    this.saveOfflineData();
  }
  
  private async syncWhenOnline(): Promise<void> {
    if (this.offlineData.pendingRequests.length === 0) {
      return;
    }
    
    // Process pending requests
    for (const request of this.offlineData.pendingRequests) {
      try {
        await this.processPendingRequest(request);
      } catch (error) {
        console.error('Failed to sync pending request:', error);
      }
    }
    
    // Clear pending requests
    this.offlineData.pendingRequests = [];
    this.saveOfflineData();
  }
  
  private async processPendingRequest(request: any): Promise<void> {
    // Re-send the request
    // Implementation depends on request type
  }
  
  private saveOfflineData(): void {
    localStorage.setItem('offline_video_data', JSON.stringify(this.offlineData));
  }
}
```



### 2. Backend Services

#### VideoRecommendationService (NEW)
**Responsibility:** Video öneri orchestration ve cache yönetimi

```python
from dataclasses import dataclass
from typing import List, Dict, Optional
import hashlib
import json

@dataclass
class VideoRecommendation:
    subject_exam: str
    videos: List[TurkishEducationVideo]
    total_count: int
    cache_hit: bool
    response_time_ms: int

class VideoRecommendationService:
    """
    Video öneri servisi - cache, filtering ve orchestration
    """
    
    def __init__(
        self,
        cache: RedisCache,
        advanced_search: AdvancedYouTubeSearch,
        semantic_search: SemanticYouTubeSearch,
        content_filter: TurkishContentFilter,
        metrics: MetricsCollector
    ):
        self.cache = cache
        self.advanced_search = advanced_search
        self.semantic_search = semantic_search
        self.content_filter = content_filter
        self.metrics = metrics
    
    async def get_recommendations(
        self,
        student_profile: StudentProfile,
        request_id: str
    ) -> List[VideoRecommendation]:
        """
        Öğrenci profiline göre video önerileri al
        
        Flow:
        1. Cache kontrolü
        2. Cache miss ise video discovery
        3. Türkçe içerik filtreleme
        4. Relevance ve difficulty filtering
        5. Cache'e yazma
        6. Metrik toplama
        """
        start_time = time.time()
        
        # 1. Cache key oluştur
        cache_key = self._generate_cache_key(student_profile)
        
        # 2. Cache kontrolü
        cached_result = await self.cache.get(cache_key)
        if cached_result:
            self.metrics.record_cache_hit(request_id)
            return self._deserialize_recommendations(cached_result)
        
        # 3. Cache miss - video discovery
        self.metrics.record_cache_miss(request_id)
        recommendations = await self._discover_videos(student_profile, request_id)
        
        # 4. Cache'e yaz
        await self.cache.set(
            cache_key,
            self._serialize_recommendations(recommendations),
            ttl=3600  # 1 hour
        )
        
        # 5. Metrik kaydet
        response_time = (time.time() - start_time) * 1000
        self.metrics.record_response_time(request_id, response_time)
        
        return recommendations
    
    async def _discover_videos(
        self,
        profile: StudentProfile,
        request_id: str
    ) -> List[VideoRecommendation]:
        """
        Paralel video discovery ve filtreleme
        """
        tasks = []
        
        # Her hedef için paralel arama
        for goal in profile.goals[:3]:  # İlk 3 hedef
            task = self._search_for_goal(goal, profile, request_id)
            tasks.append(task)
        
        # Paralel execution
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Hataları filtrele
        recommendations = [r for r in results if not isinstance(r, Exception)]
        
        return recommendations
    
    async def _search_for_goal(
        self,
        goal: str,
        profile: StudentProfile,
        request_id: str
    ) -> VideoRecommendation:
        """
        Tek bir hedef için video arama
        """
        # Konu ve zorluk seviyesi belirle
        subject = self._extract_subject(goal)
        difficulty = self._determine_difficulty(subject, profile.currentLevel)
        
        # Hybrid search: Advanced + Semantic
        advanced_videos = await self.advanced_search.search_videos_with_filters(
            subject=subject,
            exam_type='TYT',
            difficulty=difficulty,
            max_results=10
        )
        
        semantic_videos = await self.semantic_search.semantic_search_videos(
            subject=subject,
            exam_type='TYT',
            difficulty=difficulty,
            max_results=10
        )
        
        # Merge ve deduplicate
        all_videos = self._merge_videos(advanced_videos, semantic_videos)
        
        # Türkçe içerik filtreleme
        filtered_videos = await self.content_filter.filter_videos(
            videos=all_videos,
            min_relevance=0.7,
            target_difficulty=difficulty,
            language='tr'
        )
        
        # Quality score'a göre sırala ve top 5 al
        sorted_videos = sorted(
            filtered_videos,
            key=lambda v: v.quality_score,
            reverse=True
        )[:5]
        
        return VideoRecommendation(
            subject_exam=f"{subject.title()} TYT",
            videos=sorted_videos,
            total_count=len(sorted_videos),
            cache_hit=False,
            response_time_ms=0
        )
    
    def _generate_cache_key(self, profile: StudentProfile) -> str:
        """Cache key oluştur - student profile hash"""
        profile_str = json.dumps({
            'goals': sorted(profile.goals),
            'currentLevel': profile.currentLevel,
            'learningStyle': profile.learningStyle
        }, sort_keys=True)
        
        return f"video_rec:{hashlib.md5(profile_str.encode()).hexdigest()}"
    
    def _extract_subject(self, goal: str) -> str:
        """Hedeften konu çıkar"""
        goal_lower = goal.lower()
        
        subject_keywords = {
            'matematik': ['matematik', 'math', 'geometri', 'algebra'],
            'fizik': ['fizik', 'physics'],
            'kimya': ['kimya', 'chemistry'],
            'biyoloji': ['biyoloji', 'biology'],
            'türkçe': ['türkçe', 'turkish', 'edebiyat']
        }
        
        for subject, keywords in subject_keywords.items():
            if any(kw in goal_lower for kw in keywords):
                return subject
        
        return 'matematik'  # Default
    
    def _determine_difficulty(
        self,
        subject: str,
        current_level: Dict[str, int]
    ) -> str:
        """Zorluk seviyesi belirle"""
        level = current_level.get(subject, 50)
        
        if level < 30:
            return 'başlangıç'
        elif level < 70:
            return 'orta'
        else:
            return 'ileri'
```



#### TurkishContentFilter (NEW)
**Responsibility:** Türkçe içerik doğrulama ve relevance filtreleme

```python
from typing import List, Optional
import re
from langdetect import detect, LangDetectException

@dataclass
class FilterResult:
    video: TurkishEducationVideo
    language_score: float  # 0-1
    relevance_score: float  # 0-1
    difficulty_match: float  # 0-1
    overall_score: float  # 0-1
    passed: bool

class TurkishContentFilter:
    """
    Türkçe içerik filtreleme ve relevance scoring
    """
    
    # Türkçe karakterler (Req 13.6)
    TURKISH_CHARS = set('çğıöşüÇĞİÖŞÜ')
    
    # Güvenilir Türkçe eğitim kanalları (Req 13.15)
    TRUSTED_TURKISH_CHANNELS = [
        'tonguç akademi',
        'matematik öğretmeni',
        'fizik öğretmeni',
        'kimya öğretmeni',
        'biyoloji öğretmeni',
        'eba',
        'meb',
        'khan academy türkçe',
        'açık öğretim'
    ]
    
    # MEB müfredatı konu taxonomy (Req 14.1, 14.2)
    SUBJECT_TAXONOMY = {
        'matematik': {
            'keywords': ['matematik', 'geometri', 'algebra', 'trigonometri', 'sayılar', 'analiz'],
            'sub_topics': {
                'geometri': ['üçgen', 'dörtgen', 'çember', 'alan', 'hacim', 'açı', 'benzerlik'],
                'algebra': ['denklem', 'eşitsizlik', 'fonksiyon', 'polinom', 'logaritma'],
                'sayılar': ['tam sayılar', 'rasyonel sayılar', 'üslü sayılar', 'köklü sayılar'],
                'analiz': ['limit', 'türev', 'integral']
            },
            'synonyms': ['mat', 'mathematics']
        },
        'fizik': {
            'keywords': ['fizik', 'hareket', 'kuvvet', 'enerji', 'elektrik', 'manyetizma'],
            'sub_topics': {
                'hareket': ['hız', 'ivme', 'serbest düşme', 'atış hareketleri'],
                'enerji': ['kinetik', 'potansiyel', 'iş', 'güç', 'momentum'],
                'elektrik': ['akım', 'gerilim', 'direnç', 'devre']
            },
            'synonyms': ['physics']
        },
        'kimya': {
            'keywords': ['kimya', 'atom', 'molekül', 'reaksiyon', 'element', 'bileşik'],
            'sub_topics': {
                'atom': ['proton', 'nötron', 'elektron', 'periyodik tablo'],
                'reaksiyon': ['asit', 'baz', 'oksidasyon', 'indirgenme']
            },
            'synonyms': ['chemistry']
        },
        'biyoloji': {
            'keywords': ['biyoloji', 'hücre', 'genetik', 'ekosistem', 'evrim'],
            'sub_topics': {
                'hücre': ['organeller', 'mitoz', 'mayoz', 'fotosentez'],
                'genetik': ['dna', 'rna', 'gen', 'kromozom']
            },
            'synonyms': ['biology']
        },
        'türkçe': {
            'keywords': ['türkçe', 'edebiyat', 'dil bilgisi', 'yazım kuralları', 'noktalama'],
            'sub_topics': {
                'dil bilgisi': ['fiil', 'isim', 'sıfat', 'zarf', 'edat'],
                'edebiyat': ['şiir', 'roman', 'hikaye', 'makale']
            },
            'synonyms': ['turkish', 'literature']
        }
    }
    
    def __init__(self):
        self.language_detector = LanguageDetector()
        self.relevance_scorer = RelevanceScorer()
    
    async def filter_videos(
        self,
        videos: List[TurkishEducationVideo],
        min_relevance: float = 0.7,
        target_difficulty: str = 'orta',
        language: str = 'tr'
    ) -> List[TurkishEducationVideo]:
        """
        Videoları filtrele ve skorla
        
        Filtering criteria:
        1. Language: Türkçe olmalı (>0.8 confidence)
        2. Relevance: Konu ile alakalı olmalı (>0.7 score)
        3. Difficulty: Seviye uyumlu olmalı (±1 level)
        """
        filter_results = []
        
        for video in videos:
            result = await self._evaluate_video(
                video,
                min_relevance,
                target_difficulty,
                language
            )
            filter_results.append(result)
        
        # Sadece geçenleri al
        passed_videos = [
            r.video for r in filter_results
            if r.passed
        ]
        
        # Overall score'a göre sırala
        passed_videos.sort(
            key=lambda v: v.quality_score,
            reverse=True
        )
        
        return passed_videos
    
    async def _evaluate_video(
        self,
        video: TurkishEducationVideo,
        min_relevance: float,
        target_difficulty: str,
        language: str
    ) -> FilterResult:
        """
        Tek bir videoyu değerlendir
        """
        # 1. Language detection
        language_score = self._detect_language(video)
        
        # 2. Relevance scoring
        relevance_score = self._calculate_relevance(video)
        
        # 3. Difficulty matching
        difficulty_match = self._match_difficulty(
            video.difficulty,
            target_difficulty
        )
        
        # 4. Overall score (weighted average)
        overall_score = (
            language_score * 0.3 +
            relevance_score * 0.5 +
            difficulty_match * 0.2
        )
        
        # 5. Pass/fail decision
        passed = (
            language_score >= 0.8 and
            relevance_score >= min_relevance and
            difficulty_match >= 0.5 and
            overall_score >= 0.7
        )
        
        return FilterResult(
            video=video,
            language_score=language_score,
            relevance_score=relevance_score,
            difficulty_match=difficulty_match,
            overall_score=overall_score,
            passed=passed
        )
    
    def _detect_language(self, video: TurkishEducationVideo) -> float:
        """
        Dil tespiti - multiple signals
        
        Signals:
        1. Title language detection
        2. Description language detection
        3. Turkish character presence
        4. Channel language (if known)
        """
        scores = []
        
        # 1. Title language
        try:
            title_lang = detect(video.title)
            scores.append(1.0 if title_lang == 'tr' else 0.0)
        except LangDetectException:
            scores.append(0.5)  # Uncertain
        
        # 2. Description language
        if video.description:
            try:
                desc_lang = detect(video.description)
                scores.append(1.0 if desc_lang == 'tr' else 0.0)
            except LangDetectException:
                scores.append(0.5)
        
        # 3. Turkish character presence
        turkish_char_ratio = self._calculate_turkish_char_ratio(video.title)
        scores.append(turkish_char_ratio)
        
        # 4. Trusted channel bonus
        if self._is_trusted_turkish_channel(video.channel):
            scores.append(1.0)
        
        return sum(scores) / len(scores) if scores else 0.0
    
    def _calculate_turkish_char_ratio(self, text: str) -> float:
        """Türkçe karakter oranı"""
        if not text:
            return 0.0
        
        turkish_count = sum(1 for c in text if c in self.TURKISH_CHARS)
        total_alpha = sum(1 for c in text if c.isalpha())
        
        if total_alpha == 0:
            return 0.0
        
        # Türkçe karakterler varsa bonus
        return min(1.0, turkish_count / total_alpha * 5)
    
    def _calculate_relevance(self, video: TurkishEducationVideo) -> float:
        """
        Konu alakası hesapla
        
        Factors:
        1. Subject keyword match
        2. Sub-topic keyword match
        3. Title-subject semantic similarity
        4. Description-subject semantic similarity
        """
        subject = video.subject.lower()
        
        if subject not in self.SUBJECT_TAXONOMY:
            return 0.5  # Unknown subject
        
        taxonomy = self.SUBJECT_TAXONOMY[subject]
        
        # 1. Main keyword match
        title_lower = video.title.lower()
        desc_lower = video.description.lower() if video.description else ''
        
        main_keyword_score = 0.0
        for keyword in taxonomy['keywords']:
            if keyword in title_lower:
                main_keyword_score += 0.3
            if keyword in desc_lower:
                main_keyword_score += 0.1
        
        main_keyword_score = min(1.0, main_keyword_score)
        
        # 2. Sub-topic match
        sub_topic_score = 0.0
        for topic, keywords in taxonomy.get('sub_topics', {}).items():
            for keyword in keywords:
                if keyword in title_lower:
                    sub_topic_score += 0.2
                if keyword in desc_lower:
                    sub_topic_score += 0.1
        
        sub_topic_score = min(1.0, sub_topic_score)
        
        # 3. Weighted average
        relevance_score = (
            main_keyword_score * 0.6 +
            sub_topic_score * 0.4
        )
        
        return relevance_score
    
    def _match_difficulty(
        self,
        video_difficulty: str,
        target_difficulty: str
    ) -> float:
        """
        Zorluk seviyesi uyumu
        
        Difficulty levels: başlangıç (1), orta (2), ileri (3)
        Match score: 1.0 (exact), 0.7 (±1), 0.3 (±2)
        """
        difficulty_map = {
            'başlangıç': 1,
            'kolay': 1,
            'orta': 2,
            'zor': 3,
            'ileri': 3
        }
        
        video_level = difficulty_map.get(video_difficulty.lower(), 2)
        target_level = difficulty_map.get(target_difficulty.lower(), 2)
        
        diff = abs(video_level - target_level)
        
        if diff == 0:
            return 1.0  # Exact match
        elif diff == 1:
            return 0.7  # Close match
        else:
            return 0.3  # Poor match
    
    def _is_trusted_turkish_channel(self, channel_name: str) -> bool:
        """Güvenilir Türkçe eğitim kanalı mı? (Req 13.15)"""
        channel_lower = channel_name.lower()
        return any(tc in channel_lower for tc in self.TRUSTED_TURKISH_CHANNELS)


### Design Rationale: Turkish Content Filtering (Requirements 13-15)

**Multi-Signal Language Detection Approach:**
- **Rationale:** Tek bir dil tespit yöntemi yeterince güvenilir değil. Birden fazla sinyal kullanarak güvenilirliği artırıyoruz.
- **Signals:**
  1. Title language detection (langdetect library)
  2. Description language detection
  3. Turkish character presence (ç, ğ, ı, ö, ş, ü)
  4. Trusted Turkish channel verification
- **Threshold:** 0.8 minimum language score (4 sinyalden en az 3'ü pozitif olmalı)

**MEB Curriculum-Based Subject Taxonomy:**
- **Rationale:** Türk eğitim sistemine özgü konu yapısı kullanarak alakalılığı artırıyoruz.
- **Structure:** 
  - Ana konular (matematik, fizik, kimya, biyoloji, türkçe)
  - Alt konular (geometri, algebra, hareket, enerji, vb.)
  - Anahtar kelimeler ve eş anlamlılar
- **Matching Strategy:** 
  - Ana konu eşleşmesi: %60 ağırlık
  - Alt konu eşleşmesi: %40 ağırlık
  - Minimum eşik: 0.7 relevance score

**Adaptive Difficulty Matching:**
- **Rationale:** Öğrencinin mevcut seviyesine göre uygun zorlukta videolar önermek öğrenme verimliliğini artırır.
- **Difficulty Levels:** 
  - Başlangıç/Kolay: 1
  - Orta: 2
  - Zor/İleri: 3
- **Tolerance:** ±1 seviye (örn: orta seviye öğrenci için kolay veya zor videolar da kabul edilir)
- **Scoring:**
  - Tam eşleşme: 1.0
  - ±1 seviye: 0.7
  - ±2 seviye: 0.3

**Overall Quality Score Calculation:**
- **Formula:** `overall_score = (language_score * 0.3) + (relevance_score * 0.5) + (difficulty_match * 0.2)`
- **Rationale:** 
  - Relevance en önemli faktör (%50) - video konuyla alakalı olmalı
  - Language ikinci önemli faktör (%30) - Türkçe içerik şart
  - Difficulty üçüncü faktör (%20) - seviye uyumu önemli ama esnek olabilir
- **Pass Threshold:** 0.7 overall score (tüm faktörler dengeli olmalı)
```



#### HealthCheckService (NEW)
**Responsibility:** Servis sağlık durumu izleme ve startup validation (Requirement 0)

```python
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional
import time
from datetime import datetime

class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

@dataclass
class ComponentHealth:
    name: str
    status: HealthStatus
    response_time_ms: float
    error_message: Optional[str] = None
    last_check: datetime = None

@dataclass
class SystemHealth:
    overall_status: HealthStatus
    components: List[ComponentHealth]
    metrics: Dict[str, any]
    timestamp: datetime

@dataclass
class StartupHealthCheck:
    """Startup sağlık kontrolü sonucu (Req 0)"""
    success: bool
    components: List[ComponentHealth]
    warnings: List[str]
    errors: List[str]
    startup_time_ms: float
    timestamp: datetime

class HealthCheckService:
    """
    Sistem sağlık durumu izleme
    """
    
    def __init__(
        self,
        youtube_api: RealYouTubeAPI,
        database: Database,
        cache: RedisCache,
        metrics: MetricsCollector
    ):
        self.youtube_api = youtube_api
        self.database = database
        self.cache = cache
        self.metrics = metrics
    
    async def check_health(self) -> SystemHealth:
        """
        Tüm bileşenlerin sağlık kontrolü
        """
        components = []
        
        # 1. YouTube API health
        youtube_health = await self._check_youtube_api()
        components.append(youtube_health)
        
        # 2. Database health
        db_health = await self._check_database()
        components.append(db_health)
        
        # 3. Cache health
        cache_health = await self._check_cache()
        components.append(cache_health)
        
        # 4. Overall status
        overall_status = self._determine_overall_status(components)
        
        # 5. Collect metrics
        metrics = self._collect_metrics()
        
        return SystemHealth(
            overall_status=overall_status,
            components=components,
            metrics=metrics,
            timestamp=datetime.now()
        )
    
    async def _check_youtube_api(self) -> ComponentHealth:
        """YouTube API sağlık kontrolü"""
        start = time.time()
        
        try:
            # Simple test query
            await self.youtube_api.test_connection()
            
            response_time = (time.time() - start) * 1000
            
            return ComponentHealth(
                name="YouTube API",
                status=HealthStatus.HEALTHY,
                response_time_ms=response_time,
                last_check=datetime.now()
            )
        
        except Exception as e:
            return ComponentHealth(
                name="YouTube API",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=0,
                error_message=str(e),
                last_check=datetime.now()
            )
    
    async def _check_database(self) -> ComponentHealth:
        """Database sağlık kontrolü"""
        start = time.time()
        
        try:
            # Simple query
            await self.database.execute("SELECT 1")
            
            response_time = (time.time() - start) * 1000
            
            return ComponentHealth(
                name="Database",
                status=HealthStatus.HEALTHY,
                response_time_ms=response_time,
                last_check=datetime.now()
            )
        
        except Exception as e:
            return ComponentHealth(
                name="Database",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=0,
                error_message=str(e),
                last_check=datetime.now()
            )
    
    async def _check_cache(self) -> ComponentHealth:
        """Cache sağlık kontrolü"""
        start = time.time()
        
        try:
            # Ping Redis
            await self.cache.ping()
            
            response_time = (time.time() - start) * 1000
            
            return ComponentHealth(
                name="Redis Cache",
                status=HealthStatus.HEALTHY,
                response_time_ms=response_time,
                last_check=datetime.now()
            )
        
        except Exception as e:
            return ComponentHealth(
                name="Redis Cache",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=0,
                error_message=str(e),
                last_check=datetime.now()
            )
    
    def _determine_overall_status(
        self,
        components: List[ComponentHealth]
    ) -> HealthStatus:
        """Overall status belirle"""
        unhealthy_count = sum(
            1 for c in components
            if c.status == HealthStatus.UNHEALTHY
        )
        
        degraded_count = sum(
            1 for c in components
            if c.status == HealthStatus.DEGRADED
        )
        
        if unhealthy_count > 0:
            return HealthStatus.UNHEALTHY
        elif degraded_count > 0:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.HEALTHY
    
    def _collect_metrics(self) -> Dict[str, any]:
        """Sistem metriklerini topla"""
        return {
            'total_requests_24h': self.metrics.get_total_requests(hours=24),
            'success_rate_24h': self.metrics.get_success_rate(hours=24),
            'avg_response_time_1h': self.metrics.get_avg_response_time(hours=1),
            'cache_hit_rate_1h': self.metrics.get_cache_hit_rate(hours=1),
            'error_rate_1h': self.metrics.get_error_rate(hours=1)
        }
    
    async def startup_health_check(self) -> StartupHealthCheck:
        """
        Sistem başlangıç sağlık kontrolü (Requirement 0)
        
        Tüm kritik bağımlılıkları kontrol eder ve sonuçları loglar.
        Kritik servis başarısız olsa bile uygulama başlar,
        ancak WARNING seviyesinde log kaydedilir.
        """
        start_time = time.time()
        components = []
        warnings = []
        errors = []
        
        # 1. Database health check (Req 0.1)
        try:
            db_health = await self._check_database()
            components.append(db_health)
            
            if db_health.status == HealthStatus.UNHEALTHY:
                error_msg = f"Database unhealthy: {db_health.error_message}"
                errors.append(error_msg)
                logger.warning("startup_health_check_database_failed", error=error_msg)
            elif db_health.status == HealthStatus.DEGRADED:
                warning_msg = f"Database degraded: {db_health.error_message}"
                warnings.append(warning_msg)
                logger.warning("startup_health_check_database_degraded", warning=warning_msg)
        except Exception as e:
            errors.append(f"Database check failed: {str(e)}")
            logger.error("startup_health_check_database_error", error=str(e))
        
        # 2. Redis cache health check (Req 0.1)
        try:
            cache_health = await self._check_cache()
            components.append(cache_health)
            
            if cache_health.status == HealthStatus.UNHEALTHY:
                error_msg = f"Redis cache unhealthy: {cache_health.error_message}"
                errors.append(error_msg)
                logger.warning("startup_health_check_cache_failed", error=error_msg)
            elif cache_health.status == HealthStatus.DEGRADED:
                warning_msg = f"Redis cache degraded: {cache_health.error_message}"
                warnings.append(warning_msg)
                logger.warning("startup_health_check_cache_degraded", warning=warning_msg)
        except Exception as e:
            errors.append(f"Cache check failed: {str(e)}")
            logger.error("startup_health_check_cache_error", error=str(e))
        
        # 3. YouTube API health check (Req 0.1)
        try:
            youtube_health = await self._check_youtube_api()
            components.append(youtube_health)
            
            if youtube_health.status == HealthStatus.UNHEALTHY:
                error_msg = f"YouTube API unhealthy: {youtube_health.error_message}"
                errors.append(error_msg)
                logger.warning("startup_health_check_youtube_failed", error=error_msg)
            elif youtube_health.status == HealthStatus.DEGRADED:
                warning_msg = f"YouTube API degraded: {youtube_health.error_message}"
                warnings.append(warning_msg)
                logger.warning("startup_health_check_youtube_degraded", warning=warning_msg)
        except Exception as e:
            errors.append(f"YouTube API check failed: {str(e)}")
            logger.error("startup_health_check_youtube_error", error=str(e))
        
        # 4. Calculate startup time
        startup_time_ms = (time.time() - start_time) * 1000
        
        # 5. Determine success (başarılı = en az 1 component healthy)
        success = any(c.status == HealthStatus.HEALTHY for c in components)
        
        # 6. Create result
        result = StartupHealthCheck(
            success=success,
            components=components,
            warnings=warnings,
            errors=errors,
            startup_time_ms=startup_time_ms,
            timestamp=datetime.now()
        )
        
        # 7. Log structured result (Req 0.2)
        logger.info(
            "startup_health_check_complete",
            success=success,
            component_count=len(components),
            healthy_count=sum(1 for c in components if c.status == HealthStatus.HEALTHY),
            warning_count=len(warnings),
            error_count=len(errors),
            startup_time_ms=startup_time_ms
        )
        
        # 8. Report to metrics (Req 0.7)
        self.metrics.record_startup_health(result)
        
        return result
```

## Data Models

### Student Profile

```python
from pydantic import BaseModel, Field
from typing import List, Dict, Any

class StudentProfile(BaseModel):
    """Öğrenci profili"""
    goals: List[str] = Field(
        description="Öğrenci hedefleri (örn: ['TYT Matematik', 'AYT Fizik'])"
    )
    currentLevel: Dict[str, int] = Field(
        description="Konu bazında seviye (0-100 arası)"
    )
    learningStyle: str = Field(
        description="Öğrenme stili (visual, auditory, kinesthetic)"
    )
    preferences: Dict[str, Any] = Field(
        default_factory=dict,
        description="Ek tercihler"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "goals": ["TYT Matematik", "TYT Fizik"],
                "currentLevel": {
                    "matematik": 65,
                    "fizik": 50
                },
                "learningStyle": "visual",
                "preferences": {
                    "video_duration": "medium",
                    "channel_preference": ["Tonguç Akademi"]
                }
            }
        }
```

### Video Recommendation Response

```python
class VideoResponse(BaseModel):
    """Video response model"""
    video_id: str
    title: str
    channel: str
    channel_id: str
    duration: str
    view_count: int
    upload_date: str
    thumbnail: str
    quality_score: float = Field(ge=0, le=10)
    subject: str
    difficulty: str
    exam_type: str
    url: str
    
    # Filtreleme ve skorlama alanları (Req 13, 14, 15)
    language_score: float = Field(ge=0, le=1, description="Türkçe içerik güven skoru")
    relevance_score: float = Field(ge=0, le=1, description="Konu alakalılık skoru")
    difficulty_match: float = Field(ge=0, le=1, description="Zorluk seviyesi uyum skoru")
    overall_score: float = Field(ge=0, le=1, description="Genel kalite skoru")

class RecommendationResponse(BaseModel):
    """Öneri response model"""
    subject_exam: str
    videos: List[VideoResponse]
    total_count: int
    cache_hit: bool
    response_time_ms: int
    request_id: str = Field(description="İstek takip ID'si")
```

### Health Check Response

```python
class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str  # "healthy", "degraded", "unhealthy"
    components: List[Dict[str, Any]]
    metrics: Dict[str, Any]
    timestamp: datetime
```



## Error Handling

### Error Classification

```python
class VideoAPIError(Exception):
    """Base error class"""
    pass

class CacheError(VideoAPIError):
    """Cache işlem hatası"""
    pass

class YouTubeAPIError(VideoAPIError):
    """YouTube API hatası"""
    pass

class VideoDiscoveryError(VideoAPIError):
    """Video discovery hatası"""
    pass

class FilteringError(VideoAPIError):
    """Filtreleme hatası"""
    pass

class RateLimitError(VideoAPIError):
    """Rate limit aşıldı"""
    pass
```

### Error Handling Strategy

```python
class ErrorHandler:
    """Merkezi error handling"""
    
    @staticmethod
    async def handle_error(
        error: Exception,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Hata yönetimi
        
        Strategy:
        1. Error classification
        2. Logging
        3. Metrics recording
        4. User-friendly message generation
        5. Recovery action (if possible)
        """
        
        # 1. Classify error
        error_type = type(error).__name__
        
        # 2. Log error
        logger.error(
            f"Error occurred: {error_type}",
            extra={
                'error_message': str(error),
                'context': context,
                'stack_trace': traceback.format_exc()
            }
        )
        
        # 3. Record metrics
        metrics.record_error(error_type, context)
        
        # 4. Generate user message
        user_message = ErrorHandler._get_user_message(error)
        
        # 5. Determine recovery action
        recovery_action = ErrorHandler._get_recovery_action(error)
        
        return {
            'error_type': error_type,
            'user_message': user_message,
            'recovery_action': recovery_action,
            'retryable': ErrorHandler._is_retryable(error)
        }
    
    @staticmethod
    def _get_user_message(error: Exception) -> str:
        """Kullanıcı dostu hata mesajı"""
        
        error_messages = {
            'CacheError': 'Geçici bir sorun oluştu. Lütfen tekrar deneyin.',
            'YouTubeAPIError': 'Video servisi şu anda erişilebilir değil.',
            'RateLimitError': 'Çok fazla istek gönderildi. Lütfen biraz bekleyin.',
            'TimeoutError': 'İstek zaman aşımına uğradı. Lütfen tekrar deneyin.',
            'NetworkError': 'İnternet bağlantınızı kontrol edin.'
        }
        
        error_type = type(error).__name__
        return error_messages.get(
            error_type,
            'Beklenmeyen bir hata oluştu. Lütfen tekrar deneyin.'
        )
    
    @staticmethod
    def _get_recovery_action(error: Exception) -> str:
        """Recovery action belirle"""
        
        if isinstance(error, CacheError):
            return 'fallback_to_database'
        elif isinstance(error, YouTubeAPIError):
            return 'use_cached_data'
        elif isinstance(error, RateLimitError):
            return 'wait_and_retry'
        else:
            return 'show_fallback_videos'
    
    @staticmethod
    def _is_retryable(error: Exception) -> bool:
        """Retry yapılabilir mi?"""
        
        retryable_errors = [
            TimeoutError,
            ConnectionError,
            CacheError
        ]
        
        return any(isinstance(error, e) for e in retryable_errors)
```

### Circuit Breaker Pattern

```python
from enum import Enum
import time

class CircuitState(Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery

class CircuitBreaker:
    """
    Circuit breaker pattern implementation
    
    Prevents cascading failures by temporarily disabling
    failing services.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: int = 60,
        success_threshold: int = 2
    ):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.success_threshold = success_threshold
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
    
    async def call(self, func, *args, **kwargs):
        """
        Execute function with circuit breaker protection
        """
        
        # Check if circuit is open
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise CircuitBreakerOpenError(
                    "Circuit breaker is open, service unavailable"
                )
        
        try:
            # Execute function
            result = await func(*args, **kwargs)
            
            # Success
            self._on_success()
            
            return result
        
        except Exception as e:
            # Failure
            self._on_failure()
            raise e
    
    def _on_success(self):
        """Handle successful call"""
        
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            
            if self.success_count >= self.success_threshold:
                # Reset circuit
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
        
        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success
            self.failure_count = 0
    
    def _on_failure(self):
        """Handle failed call"""
        
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            # Open circuit
            self.state = CircuitState.OPEN
            logger.warning(
                f"Circuit breaker opened after {self.failure_count} failures"
            )
    
    def _should_attempt_reset(self) -> bool:
        """Should we attempt to reset circuit?"""
        
        if self.last_failure_time is None:
            return True
        
        elapsed = time.time() - self.last_failure_time
        return elapsed >= self.timeout
```

## Testing Strategy

### Unit Tests

```python
# test_video_recommendation_service.py

import pytest
from unittest.mock import Mock, AsyncMock

@pytest.mark.asyncio
async def test_get_recommendations_cache_hit():
    """Test cache hit scenario"""
    
    # Arrange
    cache = Mock()
    cache.get = AsyncMock(return_value='cached_data')
    
    service = VideoRecommendationService(
        cache=cache,
        advanced_search=Mock(),
        semantic_search=Mock(),
        content_filter=Mock(),
        metrics=Mock()
    )
    
    profile = StudentProfile(
        goals=['TYT Matematik'],
        currentLevel={'matematik': 50},
        learningStyle='visual'
    )
    
    # Act
    result = await service.get_recommendations(profile, 'req_123')
    
    # Assert
    assert cache.get.called
    assert result is not None

@pytest.mark.asyncio
async def test_get_recommendations_cache_miss():
    """Test cache miss scenario"""
    
    # Arrange
    cache = Mock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock()
    
    advanced_search = Mock()
    advanced_search.search_videos_with_filters = AsyncMock(
        return_value=[mock_video()]
    )
    
    service = VideoRecommendationService(
        cache=cache,
        advanced_search=advanced_search,
        semantic_search=Mock(),
        content_filter=Mock(),
        metrics=Mock()
    )
    
    # Act
    result = await service.get_recommendations(profile, 'req_123')
    
    # Assert
    assert cache.set.called
    assert advanced_search.search_videos_with_filters.called

@pytest.mark.asyncio
async def test_turkish_content_filter():
    """Test Turkish content filtering"""
    
    # Arrange
    filter_service = TurkishContentFilter()
    
    videos = [
        TurkishEducationVideo(
            title='Matematik Geometri Üçgenler',
            description='Türkçe açıklama',
            subject='matematik',
            difficulty='orta',
            # ... other fields
        ),
        TurkishEducationVideo(
            title='English Math Tutorial',
            description='English description',
            subject='matematik',
            difficulty='orta',
            # ... other fields
        )
    ]
    
    # Act
    filtered = await filter_service.filter_videos(
        videos,
        min_relevance=0.7,
        target_difficulty='orta',
        language='tr'
    )
    
    # Assert
    assert len(filtered) == 1
    assert 'Türkçe' in filtered[0].title or 'ü' in filtered[0].title
```

### Integration Tests

```python
# test_video_api_integration.py

@pytest.mark.integration
@pytest.mark.asyncio
async def test_video_recommendations_endpoint():
    """Test full video recommendations flow"""
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Arrange
        payload = {
            "goals": ["TYT Matematik"],
            "currentLevel": {"matematik": 50},
            "learningStyle": "visual",
            "preferences": {}
        }
        
        # Act
        response = await client.post(
            "/api/youtube/recommendations",
            json=payload
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert 'videos' in data[0]
        assert data[0]['total_count'] > 0
```

### Load Tests

```python
# load_test_video_api.py

from locust import HttpUser, task, between

class VideoAPIUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def get_video_recommendations(self):
        payload = {
            "goals": ["TYT Matematik"],
            "currentLevel": {"matematik": 50},
            "learningStyle": "visual"
        }
        
        self.client.post(
            "/api/youtube/recommendations",
            json=payload
        )

# Run: locust -f load_test_video_api.py --host=http://localhost:8000
```



## Performance Optimization

### Caching Strategy

**Multi-Layer Cache Architecture:**

```
┌─────────────────────────────────────────────────────────┐
│                    Cache Layers                          │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  Layer 1: In-Memory Cache (LRU)                         │
│  - Size: 100 entries                                     │
│  - TTL: 5 minutes                                        │
│  - Hit rate: ~40%                                        │
│  - Response time: <10ms                                  │
│                                                           │
│  Layer 2: Redis Cache                                    │
│  - Size: 10,000 entries                                  │
│  - TTL: 1 hour                                           │
│  - Hit rate: ~40%                                        │
│  - Response time: <100ms                                 │
│                                                           │
│  Layer 3: Database Cache                                 │
│  - Size: Unlimited                                       │
│  - TTL: 24 hours                                         │
│  - Hit rate: ~15%                                        │
│  - Response time: <500ms                                 │
│                                                           │
│  Layer 4: YouTube API (Cache Miss)                       │
│  - Hit rate: ~5%                                         │
│  - Response time: 2-5 seconds                            │
│                                                           │
└─────────────────────────────────────────────────────────┘

Total Cache Hit Rate: ~95%
Average Response Time: <200ms
```

**Cache Implementation:**

```python
from functools import lru_cache
from typing import Optional
import redis
import pickle

class MultiLayerCache:
    """Multi-layer caching system"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.memory_cache = {}  # In-memory LRU
        self.max_memory_size = 100
    
    @lru_cache(maxsize=100)
    def _memory_get(self, key: str) -> Optional[bytes]:
        """Layer 1: In-memory cache"""
        return self.memory_cache.get(key)
    
    async def get(self, key: str) -> Optional[Any]:
        """Get from cache (multi-layer)"""
        
        # Layer 1: Memory
        value = self._memory_get(key)
        if value:
            return pickle.loads(value)
        
        # Layer 2: Redis
        value = await self.redis.get(key)
        if value:
            # Promote to memory cache
            self._memory_set(key, value)
            return pickle.loads(value)
        
        return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = 3600
    ):
        """Set in cache (all layers)"""
        
        serialized = pickle.dumps(value)
        
        # Layer 1: Memory
        self._memory_set(key, serialized)
        
        # Layer 2: Redis
        await self.redis.setex(key, ttl, serialized)
    
    def _memory_set(self, key: str, value: bytes):
        """Set in memory cache with LRU eviction"""
        
        if len(self.memory_cache) >= self.max_memory_size:
            # Evict oldest
            oldest_key = next(iter(self.memory_cache))
            del self.memory_cache[oldest_key]
        
        self.memory_cache[key] = value
```

### Database Optimization

**Indexing Strategy:**

```sql
-- Video cache table
CREATE TABLE video_cache (
    id INTEGER PRIMARY KEY,
    video_id TEXT NOT NULL,
    subject TEXT NOT NULL,
    difficulty TEXT NOT NULL,
    exam_type TEXT NOT NULL,
    language TEXT NOT NULL,
    quality_score REAL NOT NULL,
    relevance_score REAL NOT NULL,
    metadata TEXT NOT NULL,  -- JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for fast lookup
CREATE INDEX idx_video_subject ON video_cache(subject, difficulty, exam_type);
CREATE INDEX idx_video_quality ON video_cache(quality_score DESC);
CREATE INDEX idx_video_language ON video_cache(language);
CREATE INDEX idx_video_updated ON video_cache(last_updated DESC);

-- Composite index for common queries
CREATE INDEX idx_video_search ON video_cache(
    subject, difficulty, exam_type, language, quality_score DESC
);
```

**Query Optimization:**

```python
class OptimizedVideoRepository:
    """Optimized database queries"""
    
    async def find_videos(
        self,
        subject: str,
        difficulty: str,
        exam_type: str,
        language: str = 'tr',
        min_quality: float = 7.0,
        limit: int = 20
    ) -> List[VideoCache]:
        """
        Optimized video search query
        
        Uses composite index for fast lookup
        """
        
        query = """
            SELECT *
            FROM video_cache
            WHERE subject = ?
              AND difficulty = ?
              AND exam_type = ?
              AND language = ?
              AND quality_score >= ?
            ORDER BY quality_score DESC, last_updated DESC
            LIMIT ?
        """
        
        # Use prepared statement for better performance
        return await self.db.fetch_all(
            query,
            (subject, difficulty, exam_type, language, min_quality, limit)
        )
```

### Parallel Processing

**Concurrent Video Discovery:**

```python
async def discover_videos_parallel(
    goals: List[str],
    profile: StudentProfile
) -> List[VideoRecommendation]:
    """
    Parallel video discovery for multiple goals
    
    Performance improvement: 3x faster than sequential
    """
    
    # Create tasks for each goal
    tasks = [
        discover_videos_for_goal(goal, profile)
        for goal in goals[:3]  # Limit to 3 goals
    ]
    
    # Execute in parallel
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Filter out exceptions
    valid_results = [
        r for r in results
        if not isinstance(r, Exception)
    ]
    
    return valid_results
```

### Response Compression

```python
from fastapi import Response
import gzip

@router.post("/recommendations")
async def get_recommendations(
    request: StudentProfileRequest,
    response: Response
):
    """
    Compressed response for faster transfer
    """
    
    # Get recommendations
    recommendations = await service.get_recommendations(request)
    
    # Serialize
    json_data = json.dumps(recommendations)
    
    # Compress if large
    if len(json_data) > 1024:  # > 1KB
        compressed = gzip.compress(json_data.encode())
        response.headers["Content-Encoding"] = "gzip"
        return Response(content=compressed, media_type="application/json")
    
    return recommendations
```

## Monitoring and Observability

### Metrics Collection

```python
from prometheus_client import Counter, Histogram, Gauge
import time

# Metrics
video_requests_total = Counter(
    'video_requests_total',
    'Total video recommendation requests',
    ['status', 'cache_hit']
)

video_response_time = Histogram(
    'video_response_time_seconds',
    'Video recommendation response time',
    buckets=[0.1, 0.5, 1.0, 2.0, 3.0, 5.0, 10.0]
)

cache_hit_rate = Gauge(
    'cache_hit_rate',
    'Cache hit rate percentage'
)

youtube_api_quota = Gauge(
    'youtube_api_quota_remaining',
    'Remaining YouTube API quota'
)

class MetricsCollector:
    """Metrics collection service"""
    
    def record_request(
        self,
        request_id: str,
        status: str,
        cache_hit: bool,
        response_time: float
    ):
        """Record request metrics"""
        
        # Increment counter
        video_requests_total.labels(
            status=status,
            cache_hit='hit' if cache_hit else 'miss'
        ).inc()
        
        # Record response time
        video_response_time.observe(response_time)
        
        # Update cache hit rate
        self._update_cache_hit_rate()
    
    def _update_cache_hit_rate(self):
        """Calculate and update cache hit rate"""
        
        # Get metrics from last hour
        total = self.get_total_requests(hours=1)
        hits = self.get_cache_hits(hours=1)
        
        if total > 0:
            hit_rate = (hits / total) * 100
            cache_hit_rate.set(hit_rate)
```

### Structured Logging

```python
import structlog
import json

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()

class StructuredLogger:
    """Structured logging for video API"""
    
    @staticmethod
    def log_request(
        request_id: str,
        endpoint: str,
        student_profile: StudentProfile,
        ip_address: str
    ):
        """Log incoming request"""
        
        logger.info(
            "video_request_received",
            request_id=request_id,
            endpoint=endpoint,
            goals=student_profile.goals,
            learning_style=student_profile.learningStyle,
            ip_address=ip_address
        )
    
    @staticmethod
    def log_response(
        request_id: str,
        status_code: int,
        response_time_ms: float,
        video_count: int,
        cache_hit: bool
    ):
        """Log response"""
        
        logger.info(
            "video_request_completed",
            request_id=request_id,
            status_code=status_code,
            response_time_ms=response_time_ms,
            video_count=video_count,
            cache_hit=cache_hit
        )
    
    @staticmethod
    def log_error(
        request_id: str,
        error_type: str,
        error_message: str,
        stack_trace: str,
        context: Dict[str, Any]
    ):
        """Log error"""
        
        logger.error(
            "video_request_error",
            request_id=request_id,
            error_type=error_type,
            error_message=error_message,
            stack_trace=stack_trace,
            context=context
        )
```

### Alerting Rules

```yaml
# Prometheus alerting rules
groups:
  - name: video_api_alerts
    interval: 30s
    rules:
      # High error rate
      - alert: HighErrorRate
        expr: rate(video_requests_total{status="error"}[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} (>5%)"
      
      # Slow response time
      - alert: SlowResponseTime
        expr: histogram_quantile(0.95, video_response_time_seconds) > 3
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Slow response time detected"
          description: "P95 response time is {{ $value }}s (>3s)"
      
      # Low cache hit rate
      - alert: LowCacheHitRate
        expr: cache_hit_rate < 60
        for: 10m
        labels:
          severity: info
        annotations:
          summary: "Low cache hit rate"
          description: "Cache hit rate is {{ $value }}% (<60%)"
      
      # YouTube API quota warning
      - alert: YouTubeQuotaLow
        expr: youtube_api_quota_remaining < 1000
        labels:
          severity: warning
        annotations:
          summary: "YouTube API quota running low"
          description: "Remaining quota: {{ $value }}"
```

## Deployment Strategy

### Rolling Deployment

```yaml
# kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: video-api
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    spec:
      containers:
      - name: backend
        image: video-api:latest
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /api/youtube/health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/youtube/health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

### Feature Flags

```python
class FeatureFlags:
    """Feature flag management"""
    
    # Feature flags
    ENABLE_SEMANTIC_SEARCH = True
    ENABLE_CACHE_WARMING = True
    ENABLE_CIRCUIT_BREAKER = True
    ENABLE_RATE_LIMITING = True
    
    # Performance tuning
    MAX_PARALLEL_SEARCHES = 3
    CACHE_TTL_SECONDS = 3600
    REQUEST_TIMEOUT_SECONDS = 20
    
    # Quality thresholds
    MIN_RELEVANCE_SCORE = 0.7
    MIN_LANGUAGE_SCORE = 0.8
    MIN_QUALITY_SCORE = 7.0
```

## Security Considerations

### Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/recommendations")
@limiter.limit("10/minute")  # 10 requests per minute per IP
async def get_recommendations(request: Request):
    """Rate limited endpoint"""
    pass
```

### Input Validation

```python
from pydantic import validator, Field

class StudentProfileRequest(BaseModel):
    goals: List[str] = Field(..., min_items=1, max_items=5)
    currentLevel: Dict[str, int]
    learningStyle: str
    
    @validator('goals')
    def validate_goals(cls, v):
        """Validate goals"""
        if not v:
            raise ValueError('At least one goal required')
        
        # Sanitize input
        sanitized = [goal.strip()[:100] for goal in v]
        return sanitized
    
    @validator('currentLevel')
    def validate_levels(cls, v):
        """Validate levels"""
        for subject, level in v.items():
            if not 0 <= level <= 100:
                raise ValueError(f'Level must be 0-100, got {level}')
        
        return v
```

## Key Design Decisions and Rationale

### 1. Startup Health Check Strategy (Requirement 0)
**Decision:** Uygulama kritik servis başarısız olsa bile başlar, ancak WARNING loglar.

**Rationale:**
- **Availability over perfection:** Kısmi işlevsellik hiç işlevsellik olmamasından iyidir
- **Graceful degradation:** Cache veya YouTube API down olsa bile, database'den veri sunabiliriz
- **Monitoring visibility:** WARNING logları sayesinde sorunları hızlıca tespit edebiliriz
- **User experience:** Kullanıcılar tamamen hizmet alamama yerine sınırlı hizmet alabilir

**Alternative considered:** Kritik servis başarısız olursa uygulamayı başlatmama
- **Rejected because:** Bu yaklaşım çok katı ve kullanıcı deneyimini olumsuz etkiler

### 2. Multi-Layer Cache Architecture (Requirements 2, 6)
**Decision:** 3-katmanlı cache (Memory → Redis → Database)

**Rationale:**
- **Performance tiers:** Farklı hız/kapasite dengesi için farklı katmanlar
- **Cost optimization:** Pahalı YouTube API çağrılarını minimize etmek
- **High availability:** Bir katman başarısız olsa bile diğerleri çalışır
- **Cache hit rate:** %95+ hedefine ulaşmak için çoklu katman gerekli

**Trade-offs:**
- **Complexity:** Daha fazla kod ve yönetim gerektirir
- **Consistency:** Cache invalidation zorlaşır
- **Benefit:** 10x-100x performance improvement

### 3. Parallel Video Discovery (Requirement 2.5, 2.8)
**Decision:** asyncio.gather ile paralel video arama

**Rationale:**
- **Performance:** 3 konu için sıralı arama ~9 saniye, paralel ~3 saniye
- **User experience:** Timeout riskini azaltır
- **Resource utilization:** I/O-bound işlemler için ideal

**Implementation notes:**
- Maximum 3 paralel arama (resource limit)
- Exception handling ile bir arama başarısız olsa bile diğerleri devam eder

### 4. Turkish Content Filtering Multi-Signal Approach (Requirements 13-15)
**Decision:** 4 farklı sinyal kullanarak dil tespiti

**Rationale:**
- **Accuracy:** Tek sinyal %70-80 doğruluk, çoklu sinyal %95+ doğruluk
- **Robustness:** Bir sinyal başarısız olsa bile diğerleri çalışır
- **Turkish-specific:** Türkçe karakterler ve güvenilir kanallar Türkiye'ye özgü

**Signals:**
1. Language detection library (langdetect)
2. Turkish character presence
3. Trusted Turkish educational channels
4. Description language analysis

### 5. Circuit Breaker Pattern (Requirement 5.18)
**Decision:** YouTube API için circuit breaker kullanımı

**Rationale:**
- **Cascading failure prevention:** API down olduğunda tüm sistemi etkilememesi
- **Fast failure:** Timeout beklemek yerine hızlıca cache'e geçiş
- **Auto-recovery:** Servis düzeldiğinde otomatik olarak tekrar deneme

**Configuration:**
- Failure threshold: 5 başarısız istek
- Timeout: 60 saniye
- Half-open success threshold: 2 başarılı istek

### 6. Offline Mode Support (Requirement 5.19)
**Decision:** localStorage ile offline data caching

**Rationale:**
- **Mobile users:** Mobil kullanıcılar için önemli (ağ bağlantısı kesintileri)
- **User experience:** Offline olsa bile cached videolar gösterilebilir
- **Progressive enhancement:** Online olduğunda otomatik sync

**Trade-offs:**
- **Storage limit:** localStorage ~5-10MB limit
- **Stale data:** Cached data güncel olmayabilir
- **Benefit:** Kesintisiz kullanıcı deneyimi

### 7. Structured Logging with JSON (Requirement 5.1, 5.11)
**Decision:** structlog ile JSON formatında loglama

**Rationale:**
- **Machine-readable:** Log aggregation ve analysis için ideal
- **Searchability:** Elasticsearch gibi araçlarla kolay arama
- **Context preservation:** Request ID, user ID gibi context bilgileri korunur
- **Debugging:** Production sorunlarını debug etmek için kritik

### 8. Rate Limiting Strategy (Requirement 7)
**Decision:** IP-based + user-based hybrid rate limiting

**Rationale:**
- **DDoS protection:** IP-based limiting ile brute force saldırıları engeller
- **Fair usage:** User-based limiting ile authenticated kullanıcılara daha yüksek limit
- **YouTube API quota:** Günlük quota'yı aşmamak için gerekli

**Configuration:**
- Anonymous users: 10 req/min per IP
- Authenticated users: 30 req/min per user
- YouTube API: Adaptive limiting (quota'ya göre)

## Migration Plan

### Phase 1: Backend Core Services (Week 1)
1. Implement startup health check (Req 0)
2. Implement VideoRecommendationService
3. Implement TurkishContentFilter with MEB taxonomy
4. Add health check endpoints
5. Implement multi-layer caching
6. Add structured logging

### Phase 2: Performance & Reliability (Week 2)
1. Database indexing and optimization
2. Parallel video discovery
3. Circuit breaker implementation
4. Response compression
5. Cache warming strategy

### Phase 3: Frontend Enhancements (Week 3)
1. VideoLoadingManager implementation
2. NetworkStatusManager and offline mode
3. Error handling improvements
4. Retry logic with exponential backoff
5. User feedback enhancements

### Phase 4: Monitoring & Testing (Week 4)
1. Metrics collection (Prometheus)
2. Alerting setup (high error rate, slow response)
3. Load testing (100 concurrent users)
4. Integration testing
5. E2E testing

