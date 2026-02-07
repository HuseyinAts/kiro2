# BÖLÜM 17: Risk Yönetimi

## 17.1 Risk Kategorileri

### KIRO2 Risk Matrisi

| Kategori | Örnekler | Etki |
|----------|----------|------|
| Teknik | API kesintisi, veri kaybı, performans | Yüksek |
| Operasyonel | Maliyet aşımı, deadline kaçırma | Orta |
| Güvenlik | Veri sızıntısı, unauthorized access | Kritik |
| Kalite | Düşük soru kalitesi, hatalı içerik | Orta |
| Yasal | Telif hakkı, KVKK uyumsuzluk | Kritik |

### Risk Değerlendirme Formülü

```
Risk Score = Probability × Impact × (1 - Mitigation Effectiveness)

Probability: 1 (düşük) - 5 (yüksek)
Impact: 1 (minimal) - 5 (kritik)
Mitigation: 0 (yok) - 1 (tam)
```

---

## 17.2 Teknik Riskler

### Risk 1: API Rate Limiting

**Açıklama:** Anthropic API rate limit'ine takılma

**Probability:** 4/5 (yüksek kullanımda)

**Impact:** 3/5 (workflow kesintisi)

**Önleme:**
```python
# orchestrator/utils/rate_limiter.py

import time
from functools import wraps
from collections import deque

class RateLimiter:
    """Token bucket rate limiter."""
    
    def __init__(self, requests_per_minute: int = 60):
        self.rpm = requests_per_minute
        self.window = deque()
        self.window_size = 60  # seconds
    
    def acquire(self) -> bool:
        """Rate limit kontrolü ve bekleme."""
        now = time.time()
        
        # Eski kayıtları temizle
        while self.window and now - self.window[0] > self.window_size:
            self.window.popleft()
        
        if len(self.window) >= self.rpm:
            # Limit aşıldı, bekle
            sleep_time = self.window[0] + self.window_size - now
            time.sleep(max(0, sleep_time))
            return self.acquire()  # Tekrar dene
        
        self.window.append(now)
        return True

def rate_limited(limiter: RateLimiter):
    """Rate limiting decorator."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            limiter.acquire()
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Kullanım
api_limiter = RateLimiter(requests_per_minute=50)

@rate_limited(api_limiter)
def call_anthropic_api(prompt: str):
    # API çağrısı
    pass
```

### Risk 2: Context Overflow

**Açıklama:** 200K token limitinin aşılması

**Probability:** 3/5

**Impact:** 4/5 (işlem başarısız)

**Önleme:**
```python
# orchestrator/utils/context_manager.py

class ContextManager:
    """Context window yönetimi."""
    
    MAX_TOKENS = 180000  # 200K'nın %90'ı güvenli alan
    
    def __init__(self):
        self.current_usage = 0
    
    def estimate_tokens(self, text: str) -> int:
        """Token tahmini (Türkçe için)."""
        return len(text) // 2  # Kabaca
    
    def can_add(self, text: str) -> bool:
        """Eklenebilir mi?"""
        estimated = self.estimate_tokens(text)
        return (self.current_usage + estimated) < self.MAX_TOKENS
    
    def add(self, text: str) -> bool:
        """Context'e ekle."""
        if not self.can_add(text):
            return False
        self.current_usage += self.estimate_tokens(text)
        return True
    
    def clear(self):
        """Context'i temizle."""
        self.current_usage = 0
    
    def usage_percentage(self) -> float:
        """Kullanım yüzdesi."""
        return self.current_usage / self.MAX_TOKENS * 100
```

### Risk 3: Database Connection Loss

**Açıklama:** PostgreSQL bağlantı kaybı

**Probability:** 2/5

**Impact:** 4/5 (veri kaybı riski)

**Önleme:**
```python
# orchestrator/db/connection.py

import psycopg2
from psycopg2 import pool
from contextlib import contextmanager
import time

class DatabasePool:
    """Connection pool with retry logic."""
    
    def __init__(self, dsn: str, min_conn: int = 2, max_conn: int = 10):
        self.dsn = dsn
        self.pool = None
        self._init_pool(min_conn, max_conn)
    
    def _init_pool(self, min_conn: int, max_conn: int):
        """Pool oluştur."""
        self.pool = pool.ThreadedConnectionPool(
            min_conn, max_conn, self.dsn
        )
    
    @contextmanager
    def get_connection(self, max_retries: int = 3):
        """Connection al (retry ile)."""
        conn = None
        last_error = None
        
        for attempt in range(max_retries):
            try:
                conn = self.pool.getconn()
                yield conn
                self.pool.putconn(conn)
                return
            except psycopg2.OperationalError as e:
                last_error = e
                if conn:
                    try:
                        self.pool.putconn(conn, close=True)
                    except:
                        pass
                
                # Exponential backoff
                time.sleep(2 ** attempt)
                
                # Pool'u yeniden başlat
                try:
                    self._init_pool(2, 10)
                except:
                    pass
        
        raise last_error
```

---

## 17.3 Güvenlik Riskleri

### Risk 4: API Key Exposure

**Açıklama:** API anahtarının sızması

**Probability:** 2/5

**Impact:** 5/5 (kritik)

**Önleme:**
```python
# .env dosyası (gitignore'da)
ANTHROPIC_API_KEY=sk-ant-xxx

# orchestrator/config.py
import os
from pathlib import Path

def load_api_key() -> str:
    """API key'i güvenli yükle."""
    
    # 1. Environment variable
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        return key
    
    # 2. .env dosyası
    env_file = Path(".env")
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith("ANTHROPIC_API_KEY="):
                return line.split("=", 1)[1]
    
    # 3. Secrets manager (production)
    # return get_from_secrets_manager("ANTHROPIC_API_KEY")
    
    raise ValueError("API key not found")
```

**.gitignore:**
```gitignore
.env
.env.local
*.pem
*_key.json
secrets/
```

### Risk 5: SQL Injection

**Açıklama:** Veritabanı sorgu manipülasyonu

**Probability:** 2/5 (parametrized query kullanılırsa düşük)

**Impact:** 5/5 (veri sızıntısı/kaybı)

**Önleme:**
```python
# YANLIŞ - SQL Injection riski
def get_questions_bad(topic: str):
    query = f"SELECT * FROM questions WHERE topic = '{topic}'"
    cursor.execute(query)

# DOĞRU - Parametrized query
def get_questions_good(topic: str):
    query = "SELECT * FROM questions WHERE topic = %s"
    cursor.execute(query, (topic,))

# DAHA İYİ - ORM kullanımı
from sqlalchemy.orm import Session

def get_questions_orm(db: Session, topic: str):
    return db.query(Question).filter(Question.topic == topic).all()
```

### Risk 6: Unauthorized Data Access

**Açıklama:** Yetkisiz veri erişimi

**Probability:** 2/5

**Impact:** 5/5 (KVKK ihlali)

**Önleme:**
```python
# orchestrator/auth/rbac.py

from enum import Enum
from functools import wraps

class Role(Enum):
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"

class Permission(Enum):
    READ_QUESTIONS = "read_questions"
    WRITE_QUESTIONS = "write_questions"
    DELETE_QUESTIONS = "delete_questions"
    MANAGE_USERS = "manage_users"

ROLE_PERMISSIONS = {
    Role.ADMIN: [p for p in Permission],
    Role.EDITOR: [Permission.READ_QUESTIONS, Permission.WRITE_QUESTIONS],
    Role.VIEWER: [Permission.READ_QUESTIONS]
}

def require_permission(permission: Permission):
    """Permission decorator."""
    def decorator(func):
        @wraps(func)
        def wrapper(user, *args, **kwargs):
            user_role = Role(user.role)
            if permission not in ROLE_PERMISSIONS[user_role]:
                raise PermissionError(
                    f"User lacks permission: {permission.value}"
                )
            return func(user, *args, **kwargs)
        return wrapper
    return decorator

# Kullanım
@require_permission(Permission.WRITE_QUESTIONS)
def create_question(user, question_data):
    # Soru oluştur
    pass
```

---

## 17.4 Kalite Riskleri

### Risk 7: Düşük Soru Kalitesi

**Açıklama:** Üretilen soruların pedagojik değersizliği

**Probability:** 3/5

**Impact:** 3/5 (kullanıcı memnuniyetsizliği)

**Önleme:**
```python
# orchestrator/quality/gates.py

class QualityGate:
    """Kalite kapısı."""
    
    def __init__(self, threshold: float = 0.7):
        self.threshold = threshold
        self.validators = [
            SchemaValidator(weight=0.2),
            ContentValidator(weight=0.3),
            PedagogicalValidator(weight=0.3),
            DuplicateDetector(weight=0.2)
        ]
    
    def evaluate(self, question: dict) -> dict:
        """Soruyu değerlendir."""
        total_score = 0
        all_issues = []
        
        for validator in self.validators:
            result = validator.validate(question)
            total_score += result["score"] * validator.weight
            all_issues.extend(result.get("issues", []))
        
        passed = total_score >= self.threshold and len(all_issues) == 0
        
        return {
            "passed": passed,
            "score": total_score,
            "issues": all_issues,
            "action": "approve" if passed else "reject"
        }
```

### Risk 8: Duplicate Content

**Açıklama:** Tekrarlayan soru üretimi

**Probability:** 4/5

**Impact:** 2/5 (kullanıcı deneyimi)

**Önleme:**
```python
# orchestrator/quality/duplicate_detector.py

from sentence_transformers import SentenceTransformer
import numpy as np

class DuplicateDetector:
    """Semantic duplicate tespiti."""
    
    def __init__(self, threshold: float = 0.85):
        self.threshold = threshold
        self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        self.embeddings_cache = {}
    
    def get_embedding(self, text: str) -> np.ndarray:
        """Embedding hesapla (cache ile)."""
        if text not in self.embeddings_cache:
            self.embeddings_cache[text] = self.model.encode(text)
        return self.embeddings_cache[text]
    
    def is_duplicate(self, new_question: str, existing_questions: list[str]) -> tuple[bool, float, str]:
        """Duplicate kontrolü."""
        new_emb = self.get_embedding(new_question)
        
        max_similarity = 0
        most_similar = ""
        
        for existing in existing_questions:
            existing_emb = self.get_embedding(existing)
            similarity = np.dot(new_emb, existing_emb) / (
                np.linalg.norm(new_emb) * np.linalg.norm(existing_emb)
            )
            
            if similarity > max_similarity:
                max_similarity = similarity
                most_similar = existing
        
        is_dup = max_similarity >= self.threshold
        return is_dup, max_similarity, most_similar
```

---

## 17.5 Operasyonel Riskler

### Risk 9: Maliyet Aşımı

**Açıklama:** API maliyetlerinin bütçeyi aşması

**Probability:** 3/5

**Impact:** 3/5

**Önleme:**
```python
# orchestrator/cost/tracker.py

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
import json

@dataclass
class UsageRecord:
    timestamp: datetime
    model: str
    input_tokens: int
    output_tokens: int
    cost: float

class CostTracker:
    """Maliyet takip sistemi."""
    
    PRICING = {
        "claude-sonnet-4-5-20250929": {"input": 3.0, "output": 15.0},  # per 1M tokens
        "claude-opus-4-5-20251101": {"input": 15.0, "output": 75.0},
        "claude-haiku-4-5-20251001": {"input": 0.25, "output": 1.25}
    }
    
    def __init__(self, daily_limit: float = 50.0, monthly_limit: float = 1000.0):
        self.daily_limit = daily_limit
        self.monthly_limit = monthly_limit
        self.records: list[UsageRecord] = []
    
    def record_usage(self, model: str, input_tokens: int, output_tokens: int):
        """Kullanım kaydet."""
        pricing = self.PRICING.get(model, {"input": 3.0, "output": 15.0})
        
        cost = (
            (input_tokens / 1_000_000) * pricing["input"] +
            (output_tokens / 1_000_000) * pricing["output"]
        )
        
        self.records.append(UsageRecord(
            timestamp=datetime.utcnow(),
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=cost
        ))
        
        # Limit kontrolü
        self._check_limits()
    
    def _check_limits(self):
        """Limit kontrolü."""
        daily = self.get_daily_cost()
        monthly = self.get_monthly_cost()
        
        if daily >= self.daily_limit:
            raise CostLimitExceeded(f"Daily limit reached: ${daily:.2f}")
        
        if monthly >= self.monthly_limit:
            raise CostLimitExceeded(f"Monthly limit reached: ${monthly:.2f}")
        
        # Warning at 80%
        if daily >= self.daily_limit * 0.8:
            print(f"⚠️ Daily cost at 80%: ${daily:.2f}")
    
    def get_daily_cost(self) -> float:
        """Günlük maliyet."""
        today = datetime.utcnow().date()
        return sum(
            r.cost for r in self.records 
            if r.timestamp.date() == today
        )
    
    def get_monthly_cost(self) -> float:
        """Aylık maliyet."""
        this_month = datetime.utcnow().replace(day=1).date()
        return sum(
            r.cost for r in self.records 
            if r.timestamp.date() >= this_month
        )

class CostLimitExceeded(Exception):
    pass
```

### Risk 10: System Downtime

**Açıklama:** Sistem kesintisi

**Probability:** 2/5

**Impact:** 4/5

**Önleme:**
```python
# orchestrator/monitoring/health.py

import asyncio
import aiohttp
from datetime import datetime
from dataclasses import dataclass

@dataclass
class HealthStatus:
    service: str
    healthy: bool
    latency_ms: float
    message: str
    checked_at: datetime

class HealthChecker:
    """Sistem sağlık kontrolü."""
    
    async def check_all(self) -> list[HealthStatus]:
        """Tüm servisleri kontrol et."""
        checks = [
            self.check_database(),
            self.check_redis(),
            self.check_anthropic_api(),
            self.check_langsmith()
        ]
        return await asyncio.gather(*checks)
    
    async def check_database(self) -> HealthStatus:
        """PostgreSQL kontrolü."""
        start = datetime.utcnow()
        try:
            # Simple query
            # await db.execute("SELECT 1")
            latency = (datetime.utcnow() - start).total_seconds() * 1000
            return HealthStatus(
                service="PostgreSQL",
                healthy=True,
                latency_ms=latency,
                message="OK",
                checked_at=datetime.utcnow()
            )
        except Exception as e:
            return HealthStatus(
                service="PostgreSQL",
                healthy=False,
                latency_ms=0,
                message=str(e),
                checked_at=datetime.utcnow()
            )
    
    async def check_anthropic_api(self) -> HealthStatus:
        """Anthropic API kontrolü."""
        start = datetime.utcnow()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://api.anthropic.com/v1/messages",
                    headers={"x-api-key": "test"},
                    timeout=5
                ) as resp:
                    latency = (datetime.utcnow() - start).total_seconds() * 1000
                    # 401 bekleniyor (invalid key), ama API çalışıyor
                    return HealthStatus(
                        service="Anthropic API",
                        healthy=resp.status in [200, 401],
                        latency_ms=latency,
                        message="Reachable",
                        checked_at=datetime.utcnow()
                    )
        except Exception as e:
            return HealthStatus(
                service="Anthropic API",
                healthy=False,
                latency_ms=0,
                message=str(e),
                checked_at=datetime.utcnow()
            )
```

---

## 17.6 Risk Dashboard

### Risk Overview

```python
# orchestrator/monitoring/risk_dashboard.py

from dataclasses import dataclass
from typing import List
from datetime import datetime

@dataclass
class Risk:
    id: str
    name: str
    category: str
    probability: int  # 1-5
    impact: int  # 1-5
    mitigation: float  # 0-1
    status: str  # "open", "mitigated", "accepted"
    owner: str
    last_review: datetime

class RiskDashboard:
    """Risk yönetim dashboard'u."""
    
    def __init__(self):
        self.risks = self._load_risks()
    
    def _load_risks(self) -> List[Risk]:
        """KIRO2 risklerini yükle."""
        return [
            Risk("R001", "API Rate Limiting", "Technical", 4, 3, 0.8, "mitigated", "DevOps", datetime.now()),
            Risk("R002", "Context Overflow", "Technical", 3, 4, 0.7, "mitigated", "Backend", datetime.now()),
            Risk("R003", "Database Connection Loss", "Technical", 2, 4, 0.9, "mitigated", "DevOps", datetime.now()),
            Risk("R004", "API Key Exposure", "Security", 2, 5, 0.9, "mitigated", "Security", datetime.now()),
            Risk("R005", "SQL Injection", "Security", 2, 5, 0.95, "mitigated", "Backend", datetime.now()),
            Risk("R006", "Unauthorized Access", "Security", 2, 5, 0.85, "mitigated", "Security", datetime.now()),
            Risk("R007", "Low Question Quality", "Quality", 3, 3, 0.7, "open", "Content", datetime.now()),
            Risk("R008", "Duplicate Content", "Quality", 4, 2, 0.8, "mitigated", "Content", datetime.now()),
            Risk("R009", "Cost Overrun", "Operational", 3, 3, 0.75, "open", "Finance", datetime.now()),
            Risk("R010", "System Downtime", "Operational", 2, 4, 0.8, "mitigated", "DevOps", datetime.now()),
        ]
    
    def calculate_score(self, risk: Risk) -> float:
        """Risk skoru hesapla."""
        return risk.probability * risk.impact * (1 - risk.mitigation)
    
    def get_summary(self) -> dict:
        """Risk özeti."""
        total = len(self.risks)
        by_status = {}
        by_category = {}
        top_risks = []
        
        for risk in self.risks:
            # Status
            by_status[risk.status] = by_status.get(risk.status, 0) + 1
            
            # Category
            by_category[risk.category] = by_category.get(risk.category, 0) + 1
            
            # Score
            score = self.calculate_score(risk)
            top_risks.append((risk.name, score))
        
        top_risks.sort(key=lambda x: x[1], reverse=True)
        
        return {
            "total_risks": total,
            "by_status": by_status,
            "by_category": by_category,
            "top_5_risks": top_risks[:5],
            "average_score": sum(self.calculate_score(r) for r in self.risks) / total
        }
    
    def print_report(self):
        """Risk raporu yazdır."""
        summary = self.get_summary()
        
        print("=" * 60)
        print("KIRO2 RISK DASHBOARD")
        print("=" * 60)
        print(f"\nTotal Risks: {summary['total_risks']}")
        print(f"Average Risk Score: {summary['average_score']:.2f}")
        
        print("\nBy Status:")
        for status, count in summary["by_status"].items():
            print(f"  {status}: {count}")
        
        print("\nBy Category:")
        for cat, count in summary["by_category"].items():
            print(f"  {cat}: {count}")
        
        print("\nTop 5 Risks:")
        for name, score in summary["top_5_risks"]:
            print(f"  {name}: {score:.2f}")
```

---

## 17.7 Özet

### Checklist

- [ ] Tüm riskler tanımlandı
- [ ] Risk skorları hesaplandı
- [ ] Mitigation stratejileri belirlendi
- [ ] Owner'lar atandı
- [ ] Monitoring kuruldu
- [ ] Review schedule belirlendi

### Risk Matrix

| Risk | Probability | Impact | Score | Status |
|------|-------------|--------|-------|--------|
| API Rate Limit | 4 | 3 | 2.4 | Mitigated |
| Context Overflow | 3 | 4 | 3.6 | Mitigated |
| API Key Exposure | 2 | 5 | 1.0 | Mitigated |
| SQL Injection | 2 | 5 | 0.5 | Mitigated |
| Low Quality | 3 | 3 | 2.7 | Open |
| Cost Overrun | 3 | 3 | 2.25 | Open |

### Metrikler

| Metrik | Hedef |
|--------|-------|
| Open risks | < 5 |
| Average risk score | < 3.0 |
| Mitigated % | > 80% |
| Review frequency | Monthly |

---

**Önceki Bölüm:** [16 - Test ve Kalite](./16-test-ve-kalite.md)  
**Sonraki Bölüm:** [18 - Sonuç ve Yol Haritası](./18-sonuc-yol-haritasi.md)
