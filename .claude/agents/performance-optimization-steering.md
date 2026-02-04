# Performance Optimization Agent Steering
## MASTER_SPEC REQ-7, REQ-8, REQ-52

**Version**: 1.0
**Date**: 18 Ekim 2025
**Requirements**: REQ-7 (High Performance), REQ-8 (PWA/Offline), REQ-52 (Database Optimization)

---

## 🎯 Performance Goals

### Critical Performance Targets (REQ-7)

| Metric | Target | Critical Threshold | Current |
|--------|--------|-------------------|---------|
| **API Response Time (p95)** | < 200ms | < 500ms | Monitor |
| **Concurrent Users** | 100,000+ | 50,000+ | Scale test |
| **System Uptime** | 99.9% | 99.5% | Monitor |
| **Database Query** | < 50ms avg | < 200ms | Optimize |
| **Cache Hit Rate** | > 95% | > 80% | Monitor |
| **Page Load (FCP)** | < 1.5s | < 3s | Optimize |
| **Page Load (LCP)** | < 2.5s | < 4s | Optimize |
| **TTI (Time to Interactive)** | < 3.5s | < 5s | Optimize |

---

## 🔧 Performance Optimization Agent

### Agent Persona: **PerformanceOptimizationAgent**

**Primary Responsibilities**:
- Monitor API response times and optimize slow endpoints
- Implement caching strategies (Redis, browser cache)
- Optimize database queries (indexes, N+1 prevention)
- Enable CDN for static assets
- Implement code splitting and lazy loading
- Monitor and optimize Core Web Vitals

**Response Time**: < 10 seconds (analysis), < 1 hour (optimization)

---

## 📊 API Performance Optimization (REQ-7.1, REQ-7.2)

### Rule 1: Response Time Monitoring

**ALWAYS monitor and optimize slow endpoints**:

```python
from functools import wraps
import time
from prometheus_client import Histogram

# Prometheus metric
api_request_duration = Histogram(
    'api_request_duration_seconds',
    'API request duration',
    ['endpoint', 'method', 'status']
)

def monitor_performance(threshold_ms=200):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                status = 200
                return result
            except Exception as e:
                status = 500
                raise
            finally:
                duration_ms = (time.time() - start) * 1000
                api_request_duration.labels(
                    endpoint=func.__name__,
                    method=request.method,
                    status=status
                ).observe(duration_ms / 1000)

                if duration_ms > threshold_ms:
                    logger.warning(
                        f"Slow API: {func.__name__} took {duration_ms:.0f}ms "
                        f"(threshold: {threshold_ms}ms)"
                    )
        return wrapper
    return decorator

# Usage
@router.get("/api/dashboard")
@monitor_performance(threshold_ms=200)
async def get_dashboard(user_id: int):
    # Implementation
    pass
```

### Rule 2: Query Optimization

**NEVER allow N+1 queries or missing indexes**:

```python
# ❌ BAD - N+1 Problem
students = session.query(Student).all()
for student in students:
    print(student.school.name)  # Separate query!
    print(student.grade_avg)     # Separate query!

# ✅ GOOD - Eager Loading
from sqlalchemy.orm import joinedload, selectinload

students = session.query(Student).options(
    joinedload(Student.school),
    selectinload(Student.exam_attempts)
).filter(Student.active == True).all()

# ✅ GOOD - With Caching
@cache_result(key="students:{user_id}", ttl=300)
def get_student_dashboard(user_id: int):
    return session.query(Student).options(
        joinedload(Student.school),
        joinedload(Student.learning_path),
        selectinload(Student.recent_exams)
    ).filter(Student.id == user_id).one()
```

### Rule 3: Caching Strategy

**ALWAYS implement multi-layer caching**:

```python
# Layer 1: Application Cache (Redis)
from redis import Redis
import json

redis_client = Redis(host='localhost', port=6379, db=0)

def cache_result(key: str, ttl: int = 3600):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Try cache first
            cache_key = key.format(**kwargs)
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)

            # Cache miss - compute and store
            result = await func(*args, **kwargs)
            redis_client.setex(
                cache_key,
                ttl,
                json.dumps(result, default=str)
            )
            return result
        return wrapper
    return decorator

# Layer 2: Database Query Cache
from sqlalchemy import create_engine
from sqlalchemy.ext.horizontal_shard import ShardedSession

engine = create_engine(
    DATABASE_URL,
    pool_size=30,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False,  # Disable in production
    query_cache_size=1000  # Query result cache
)

# Layer 3: Browser Cache (HTTP Headers)
from fastapi import Response

@router.get("/api/public/courses")
async def get_courses(response: Response):
    response.headers["Cache-Control"] = "public, max-age=3600"
    response.headers["ETag"] = generate_etag(courses)
    return courses
```

---

## 💾 Database Performance (REQ-52)

### Rule 4: Connection Pooling

**ALWAYS configure optimal connection pool**:

```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=30,              # Concurrent connections
    max_overflow=10,           # Extra during peak
    pool_timeout=30,           # Wait time for connection
    pool_recycle=3600,         # Recycle connections every hour
    pool_pre_ping=True,        # Verify connection before use
    echo_pool=True,            # Log pool events (dev only)
    connect_args={
        "application_name": "kiro_platform",
        "options": "-c statement_timeout=30000"  # 30s query timeout
    }
)
```

### Rule 5: Index Strategy

**ALWAYS add indexes for frequently queried columns**:

```python
# ✅ GOOD - Proper Indexing
class Student(Base):
    __tablename__ = 'students'

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, index=True)
    school_id = Column(Integer, ForeignKey('schools.id'), index=True)
    grade = Column(Integer, index=True)
    section = Column(String(10))
    learning_style = Column(String(50), index=True)

    # Composite index for common queries
    __table_args__ = (
        Index('idx_school_grade_section', 'school_id', 'grade', 'section'),
        Index('idx_learning_style_grade', 'learning_style', 'grade'),
    )
```

### Rule 6: Query Monitoring

**ALWAYS log slow queries**:

```python
from sqlalchemy import event
from sqlalchemy.engine import Engine
import time

@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault('query_start_time', []).append(time.time())

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - conn.info['query_start_time'].pop()
    if total > 1.0:  # Log queries > 1 second
        logger.warning(
            f"SLOW QUERY ({total:.2f}s):\n{statement[:500]}\n"
            f"Parameters: {parameters}"
        )
        # Send to monitoring
        from backend.monitoring.prometheus_exporter import slow_queries_total
        slow_queries_total.labels(table=extract_table(statement)).inc()
```

---

## 📱 PWA & Offline Support (REQ-8)

### Rule 7: Service Worker Configuration

**ALWAYS implement service worker for offline support**:

```typescript
// frontend/public/service-worker.ts

const CACHE_NAME = 'kiro-v1.0.0';
const OFFLINE_URL = '/offline.html';

const PRECACHE_URLS = [
  '/',
  '/offline.html',
  '/manifest.json',
  '/static/css/main.css',
  '/static/js/main.js',
  '/static/images/logo.png'
];

// Install - precache critical assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(PRECACHE_URLS);
    })
  );
});

// Activate - clean up old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => name !== CACHE_NAME)
          .map((name) => caches.delete(name))
      );
    })
  );
});

// Fetch - network first, fallback to cache
self.addEventListener('fetch', (event) => {
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request).catch(() => {
        return caches.match(OFFLINE_URL);
      })
    );
  } else {
    event.respondWith(
      caches.match(event.request).then((response) => {
        return response || fetch(event.request);
      })
    );
  }
});
```

### Rule 8: Offline Data Sync (REQ-8.3, REQ-8.4)

**ALWAYS queue offline actions for later sync**:

```typescript
// frontend/src/utils/offlineQueue.ts

import { openDB, DBSchema, IDBPDatabase } from 'idb';

interface OfflineQueue extends DBSchema {
  queue: {
    key: number;
    value: {
      id: number;
      action: 'create' | 'update' | 'delete';
      endpoint: string;
      data: any;
      timestamp: number;
    };
  };
}

class OfflineQueueManager {
  private db: IDBPDatabase<OfflineQueue> | null = null;

  async init() {
    this.db = await openDB<OfflineQueue>('offline-queue', 1, {
      upgrade(db) {
        db.createObjectStore('queue', { keyPath: 'id', autoIncrement: true });
      },
    });
  }

  async enqueue(action: string, endpoint: string, data: any) {
    if (!this.db) await this.init();

    await this.db!.add('queue', {
      action: action as any,
      endpoint,
      data,
      timestamp: Date.now()
    });
  }

  async sync() {
    if (!this.db) await this.init();

    const items = await this.db!.getAll('queue');

    for (const item of items) {
      try {
        const response = await fetch(item.endpoint, {
          method: item.action === 'delete' ? 'DELETE' : 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(item.data)
        });

        if (response.ok) {
          await this.db!.delete('queue', item.id);
        }
      } catch (error) {
        console.error('Sync failed for item:', item.id, error);
      }
    }
  }
}

// Usage
const offlineQueue = new OfflineQueueManager();

// When offline, queue the action
async function submitExamAnswer(answer: any) {
  if (!navigator.onLine) {
    await offlineQueue.enqueue('create', '/api/exam/answer', answer);
    showNotification('Cevabınız kaydedildi. İnternet bağlantınız geldiğinde senkronize edilecek.');
  } else {
    await fetch('/api/exam/answer', {
      method: 'POST',
      body: JSON.stringify(answer)
    });
  }
}

// When back online, sync
window.addEventListener('online', () => {
  offlineQueue.sync();
  showNotification('İnternet bağlantınız geri geldi. Değişiklikler senkronize ediliyor...');
});
```

---

## 🚀 Frontend Performance (REQ-7.5)

### Rule 9: Code Splitting & Lazy Loading

**ALWAYS use code splitting for routes**:

```typescript
// frontend/src/app.tsx

import React, { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';

// Lazy load route components
const Dashboard = lazy(() => import('./pages/Dashboard'));
const ExamPage = lazy(() => import('./pages/ExamPage'));
const LearningPath = lazy(() => import('./pages/LearningPath'));

function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<LoadingSpinner />}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/exam/:id" element={<ExamPage />} />
          <Route path="/learning-path" element={<LearningPath />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}
```

### Rule 10: Image Optimization

**ALWAYS optimize images for web**:

```typescript
// frontend/src/components/OptimizedImage.tsx

import React from 'react';

interface OptimizedImageProps {
  src: string;
  alt: string;
  width?: number;
  height?: number;
}

const OptimizedImage: React.FC<OptimizedImageProps> = ({ src, alt, width, height }) => {
  const formats = ['webp', 'jpg'];
  const sizes = [320, 640, 960, 1280];

  return (
    <picture>
      {formats.map((format) => (
        <source
          key={format}
          type={`image/${format}`}
          srcSet={sizes
            .map((size) => `${src}?w=${size}&fm=${format} ${size}w`)
            .join(', ')}
          sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
        />
      ))}
      <img
        src={src}
        alt={alt}
        width={width}
        height={height}
        loading="lazy"
        decoding="async"
      />
    </picture>
  );
};

export default OptimizedImage;
```

### Rule 11: Core Web Vitals Monitoring

**ALWAYS monitor Core Web Vitals**:

```typescript
// frontend/src/utils/webVitals.ts

import { getCLS, getFID, getFCP, getLCP, getTTFB } from 'web-vitals';

function sendToAnalytics(metric: any) {
  // Send to your analytics endpoint
  fetch('/api/analytics/web-vitals', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name: metric.name,
      value: metric.value,
      id: metric.id,
      delta: metric.delta,
      timestamp: Date.now()
    })
  });
}

export function reportWebVitals() {
  getCLS(sendToAnalytics);  // Cumulative Layout Shift
  getFID(sendToAnalytics);  // First Input Delay
  getFCP(sendToAnalytics);  // First Contentful Paint
  getLCP(sendToAnalytics);  // Largest Contentful Paint
  getTTFB(sendToAnalytics); // Time to First Byte
}

// Target values
const WEB_VITALS_TARGETS = {
  LCP: 2500,  // ms - Good
  FID: 100,   // ms - Good
  CLS: 0.1,   // unitless - Good
  FCP: 1800,  // ms - Good
  TTFB: 600   // ms - Good
};
```

---

## ⚡ Auto-scaling Rules (REQ-7.6)

### Rule 12: Horizontal Scaling

**WHEN system capacity > 80% THEN trigger auto-scaling**:

```yaml
# docker-compose.yml - Auto-scaling configuration

version: '3.8'

services:
  backend:
    image: kiro/backend:latest
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 1G
      update_config:
        parallelism: 1
        delay: 10s
      restart_policy:
        condition: on-failure
        max_attempts: 3
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Auto-scaler (Kubernetes-style)
  autoscaler:
    image: kiro/autoscaler:latest
    environment:
      - MIN_REPLICAS=3
      - MAX_REPLICAS=10
      - TARGET_CPU_UTILIZATION=80
      - TARGET_MEMORY_UTILIZATION=80
      - SCALE_UP_COOLDOWN=180
      - SCALE_DOWN_COOLDOWN=300
```

---

## 📈 Performance Monitoring Checklist

**PerformanceOptimizationAgent MUST verify**:

- [ ] API p95 response time < 200ms
- [ ] Database queries avg < 50ms
- [ ] Cache hit rate > 95%
- [ ] No N+1 queries
- [ ] All foreign keys have indexes
- [ ] Service Worker registered and active
- [ ] Offline queue functional
- [ ] Code splitting enabled for routes
- [ ] Images optimized (WebP, lazy load)
- [ ] Core Web Vitals: LCP < 2.5s, FID < 100ms, CLS < 0.1
- [ ] Auto-scaling configured
- [ ] Prometheus metrics exported
- [ ] Load testing passed (100K concurrent users)

---

**Version**: 1.0
**Last Updated**: 18 Ekim 2025
**Compliance**: REQ-7, REQ-8, REQ-52
