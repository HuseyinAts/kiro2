# Watcher Pattern

## Açıklama

Worker'ı izleyen ayrı bir agent. Sorun tespit ederse müdahale eder, gerekirse
rollback tetikler. Kritik operasyonlar için güvenlik katmanı sağlar.

## Diyagram

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  ┌─────────────────┐           ┌─────────────────┐         │
│  │  Worker Agent   │──────────▶│  Watcher Agent  │         │
│  │   (Primary)     │  Output   │   (Observer)    │         │
│  └────────┬────────┘           └────────┬────────┘         │
│           │                             │                   │
│           │ Execute                     │ Monitor           │
│           ▼                             ▼                   │
│  ┌─────────────────┐           ┌─────────────────┐         │
│  │   Operation     │           │  Health Check   │         │
│  │   (Deploy,      │           │  (Metrics,      │         │
│  │   Migration)    │           │   Errors)       │         │
│  └────────┬────────┘           └────────┬────────┘         │
│           │                             │                   │
│           │                             │ Alert!            │
│           │                             ▼                   │
│           │                    ┌─────────────────┐         │
│           │◀───────────────────│ Rollback Agent  │         │
│           │   Rollback         │   (Recovery)    │         │
│           │                    └─────────────────┘         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Ne Zaman Kullanılır

- Production deployments
- Database migrations
- Kritik veri operasyonları
- Long-running jobs
- Resource-intensive operations
- Irreversible actions

## Rol Tanımları

### Worker Agent
```yaml
role: Ana işlemi gerçekleştir
model: Sonnet
tools: [Read, Edit, Write, Bash]
responsibilities:
  - İşlemi başlat
  - Progress raporla
  - Hata durumunda watcher'a bildir
```

### Watcher Agent
```yaml
role: İşlemi izle ve doğrula
model: Sonnet (paralel çalışır)
tools: [Read, Bash, Grep]
responsibilities:
  - Metrikleri izle
  - Anomali tespit et
  - Rollback kararı ver
```

### Rollback Agent
```yaml
role: Geri alma işlemi
model: Sonnet
tools: [Read, Edit, Bash]
responsibilities:
  - Checkpoint'e dön
  - Temizlik yap
  - Durum raporla
```

## Implementasyon

### Watcher Sınıfı

```python
import asyncio
from dataclasses import dataclass
from enum import Enum

class WatcherStatus(Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"

@dataclass
class HealthCheck:
    status: WatcherStatus
    message: str
    metrics: dict
    timestamp: float

class OperationWatcher:
    """
    İşlem izleyici.

    Belirli aralıklarla sağlık kontrolü yapar,
    anomali tespit ederse müdahale eder.
    """

    def __init__(
        self,
        check_interval: float = 5.0,
        error_threshold: int = 3,
        rollback_on_critical: bool = True,
    ):
        self.check_interval = check_interval
        self.error_threshold = error_threshold
        self.rollback_on_critical = rollback_on_critical
        self.consecutive_errors = 0
        self._running = False

    async def start(self, operation_id: str):
        """İzlemeyi başlat."""
        self._running = True

        while self._running:
            health = await self.check_health(operation_id)

            if health.status == WatcherStatus.CRITICAL:
                if self.rollback_on_critical:
                    await self.trigger_rollback(operation_id)
                    break

            elif health.status == WatcherStatus.WARNING:
                self.consecutive_errors += 1
                if self.consecutive_errors >= self.error_threshold:
                    await self.trigger_alert(operation_id, health)

            else:
                self.consecutive_errors = 0

            await asyncio.sleep(self.check_interval)

    async def check_health(self, operation_id: str) -> HealthCheck:
        """Sağlık kontrolü yap."""
        # Metrikleri topla
        metrics = await self.collect_metrics()

        # Durumu değerlendir
        if metrics["error_rate"] > 0.1:
            status = WatcherStatus.CRITICAL
        elif metrics["error_rate"] > 0.05:
            status = WatcherStatus.WARNING
        else:
            status = WatcherStatus.HEALTHY

        return HealthCheck(
            status=status,
            message=f"Error rate: {metrics['error_rate']:.2%}",
            metrics=metrics,
            timestamp=time.time(),
        )

    async def trigger_rollback(self, operation_id: str):
        """Rollback tetikle."""
        print(f"⚠️ Triggering rollback for {operation_id}")
        # Rollback agent'ı çağır
        Task(
            name=f"rollback-{operation_id}",
            prompt=f"Rollback operation {operation_id}",
            subagent_type="kiro2-devops-engineer",
        )

    async def trigger_alert(self, operation_id: str, health: HealthCheck):
        """Alert gönder."""
        print(f"⚠️ Alert for {operation_id}: {health.message}")
```

### Claude Code Kullanımı

```python
# Worker ve Watcher'ı paralel başlat
async def monitored_operation():
    operation_id = str(uuid.uuid4())

    # Worker task
    worker_task = Task(
        name=f"worker-{operation_id}",
        prompt="Database migration uygula",
        subagent_type="kiro2-devops-engineer",
    )

    # Watcher task (paralel)
    watcher_task = Task(
        name=f"watcher-{operation_id}",
        prompt=f"""
        Operation {operation_id}'yi izle:
        1. Her 5 saniyede health check yap
        2. Error rate %5'i geçerse uyar
        3. Error rate %10'u geçerse rollback tetikle
        4. Migration bitene kadar izlemeye devam et
        """,
        subagent_type="test-runner",
        parallel=True,  # Worker ile paralel
    )
```

## KIRO2 Örneği

### Production Deployment Watcher

```python
deployment_id = "deploy-v1.2.3"

# Deployment başlat
Task(
    name=f"deploy-{deployment_id}",
    prompt="v1.2.3'ü production'a deploy et",
    subagent_type="kiro2-devops-engineer",
)

# Watcher başlat
Task(
    name=f"watch-{deployment_id}",
    prompt=f"""
    Deployment {deployment_id}'yi izle:

    Kontrol edilecekler:
    - /health endpoint'i 200 dönüyor mu?
    - API response time < 500ms mi?
    - Error rate < %1 mi?
    - Memory usage < %85 mi?

    Kritik hata durumunda:
    1. Alert gönder
    2. Rollback tetikle
    3. Eski version'a dön

    İzleme süresi: 10 dakika
    Kontrol aralığı: 30 saniye
    """,
    subagent_type="kiro2-devops-engineer",
    parallel=True,
)
```

### Database Migration Watcher

```python
migration_id = "migration-add-indexes"

# Migration ve Watcher'ı paralel başlat
Task(
    name=f"migrate-{migration_id}",
    prompt="""
    Performance indexlerini ekle:
    1. Backup al
    2. Index oluştur
    3. REINDEX çalıştır
    """,
    subagent_type="kiro2-devops-engineer",
)

Task(
    name=f"watch-{migration_id}",
    prompt=f"""
    Migration {migration_id}'yi izle:

    Kontroller:
    - Database connection aktif mi?
    - Lock wait time < 30s mi?
    - Disk space yeterli mi?
    - Replication lag < 10s mi?

    Tehlike durumunda:
    - ROLLBACK çalıştır
    - Backup'tan restore et
    """,
    subagent_type="kiro2-devops-engineer",
    parallel=True,
)
```

## Watcher Kuralları

### Metric Thresholds

| Metrik | Warning | Critical |
|--------|---------|----------|
| Error rate | > 5% | > 10% |
| Response time p99 | > 500ms | > 2000ms |
| CPU usage | > 70% | > 90% |
| Memory usage | > 75% | > 90% |
| Disk usage | > 80% | > 95% |
| Connection count | > 80 | > 100 |

### Alert Seviyeleri

```python
class AlertLevel(Enum):
    INFO = "info"      # Log only
    WARNING = "warn"   # Notify team
    CRITICAL = "crit"  # Page on-call
    EMERGENCY = "emrg" # Auto-rollback
```

## Rollback Stratejileri

### Immediate Rollback

```python
async def immediate_rollback(operation_id: str):
    """Anında rollback (kritik durumlar)."""
    # 1. Aktif operasyonu durdur
    await stop_operation(operation_id)

    # 2. Son checkpoint'e dön
    await restore_checkpoint(operation_id)

    # 3. Health check
    await verify_health()
```

### Gradual Rollback

```python
async def gradual_rollback(operation_id: str):
    """Kademeli rollback (traffic shifting)."""
    # 1. Traffic'i eski version'a yönlendir
    for percentage in [25, 50, 75, 100]:
        await shift_traffic(old_version, percentage)
        await asyncio.sleep(30)

    # 2. Yeni deployment'ı kaldır
    await remove_deployment(operation_id)
```

## Best Practices

1. **İzleme süresini belirle**: İşlem bitene kadar veya X dakika
2. **Check interval'i optimize et**: Çok sık → overhead, çok seyrek → geç tespit
3. **Threshold'ları kalibre et**: False positive minimize et
4. **Rollback planı hazırla**: Her işlem için geri alma senaryosu
5. **Checkpoint kullan**: Rollback için geri dönüş noktası
6. **Logging**: Tüm kararları logla

## Karşılaştırma

| Özellik | Watcher | Pipeline | Fan-Out |
|---------|---------|----------|---------|
| Asıl amaç | İzleme | İş akışı | Paralel işleme |
| Agent sayısı | 2-3 | N | N |
| Müdahale | Aktif | Pasif | Yok |
| Use case | Kritik ops | Workflow | Bağımsız işler |

## İlgili Patternler

- [Pipeline](pipeline.md) - Sıralı iş akışı
- [Fan-Out](fan-out.md) - Paralel dağıtım
- [Map-Reduce](map-reduce.md) - Büyük veri işleme
