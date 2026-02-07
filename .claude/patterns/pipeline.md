# Pipeline Pattern

## Açıklama

Sıralı, bağımlı görevleri zincirler. Her aşama önceki aşamanın çıktısını alır.
Feature development, code review ve deployment süreçleri için ideal.

## Diyagram

```
┌─────────┐    ┌───────────┐    ┌─────────────┐    ┌────────┐    ┌──────────┐    ┌──────────┐
│  Scout  │───▶│ Architect │───▶│ Implementer │───▶│ Tester │───▶│ Reviewer │───▶│ Deployer │
└─────────┘    └───────────┘    └─────────────┘    └────────┘    └──────────┘    └──────────┘
   Araştır        Tasarla           Uygula           Test Et       İncele         Deploy Et
```

## Ne Zaman Kullanılır

- Feature development lifecycle
- Code review süreçleri
- Deployment pipeline
- Refactoring workflow
- Bug fix süreci
- Migration işlemleri

## Aşamalar ve Rolleri

### 1. Scout (Araştırma)
```yaml
role: Keşif ve araştırma
model: Sonnet
tools: [Read, Grep, Glob, WebSearch]
output: Araştırma raporu
```

### 2. Architect (Tasarım)
```yaml
role: Mimari tasarım
model: Opus
tools: [Read, Glob]
input: Scout raporu
output: Tasarım dokümanı
```

### 3. Implementer (Uygulama)
```yaml
role: Kod yazımı
model: Sonnet
tools: [Read, Edit, Write, Bash]
input: Tasarım dokümanı
output: Kod değişiklikleri
```

### 4. Tester (Test)
```yaml
role: Test yazımı ve çalıştırma
model: Sonnet
tools: [Read, Edit, Bash]
input: Kod değişiklikleri
output: Test sonuçları
```

### 5. Reviewer (İnceleme)
```yaml
role: Kod inceleme
model: Opus
tools: [Read, Grep]
input: Kod + Test sonuçları
output: Review raporu
```

### 6. Deployer (Dağıtım)
```yaml
role: Production deployment
model: Sonnet
tools: [Bash]
input: Onaylanmış kod
output: Deployment durumu
note: Sadece kullanıcı tetikleyebilir
```

## Implementasyon

### Task Dependency ile

```python
# Tasks sistemi ile pipeline
Task(id="scout", name="Araştır", blockedBy=[])
Task(id="architect", name="Tasarla", blockedBy=["scout"])
Task(id="implement", name="Uygula", blockedBy=["architect"])
Task(id="test", name="Test Et", blockedBy=["implement"])
Task(id="review", name="İncele", blockedBy=["test"])
```

### Workflow Definition ile

```python
from backend.sdk.workflow_definitions import workflow, WorkflowStep

@workflow(
    name="feature-pipeline",
    steps=[
        WorkflowStep(name="scout", description="Araştırma"),
        WorkflowStep(name="architect", description="Tasarım", depends_on=["scout"]),
        WorkflowStep(name="implement", description="Uygulama", depends_on=["architect"]),
        WorkflowStep(name="test", description="Test", depends_on=["implement"]),
        WorkflowStep(name="review", description="İnceleme", depends_on=["test"]),
    ]
)
async def feature_pipeline(feature_description: str):
    # Her aşama otomatik sırayla çalışır
    ...
```

## KIRO2 Örneği

### Soru Ekleme Pipeline

```
1. Scout: Mevcut soru bankasını analiz et
   ├── Konu dağılımı
   ├── Zorluk dağılımı
   └── Eksik alanlar

2. Architect: Soru stratejisi belirle
   ├── Hangi konulara soru gerekiyor
   ├── Zorluk hedefleri
   └── IRT parametre aralıkları

3. Implementer: Soruları oluştur
   ├── Soru metinleri
   ├── Seçenekler
   └── Doğru cevaplar

4. Tester: Soruları doğrula
   ├── IRT parametre validasyonu
   ├── ZPD uygunluğu
   └── Duplicate kontrolü

5. Reviewer: Kalite kontrolü
   ├── Türkçe dil kontrolü
   ├── Müfredata uygunluk
   └── Pedagojik değerlendirme
```

### Bug Fix Pipeline

```python
# Bug fix için kısaltılmış pipeline
pipeline = [
    {
        "name": "investigate",
        "prompt": "Bug'ı araştır ve root cause bul",
        "agent": "debugger",
    },
    {
        "name": "fix",
        "prompt": "Bug'ı düzelt",
        "agent": "python-pro",
        "depends_on": ["investigate"],
    },
    {
        "name": "verify",
        "prompt": "Fix'i doğrula ve test yaz",
        "agent": "test-runner",
        "depends_on": ["fix"],
    },
]
```

## State Management

Pipeline boyunca state yönetimi:

```python
class PipelineState:
    def __init__(self):
        self.context = {}
        self.current_stage = None
        self.completed_stages = []

    def advance(self, stage: str, output: dict):
        self.completed_stages.append(self.current_stage)
        self.current_stage = stage
        self.context[stage] = output

    def get_context_for(self, stage: str) -> dict:
        # Önceki aşamaların çıktılarını birleştir
        return {
            k: v for k, v in self.context.items()
            if k in self.get_dependencies(stage)
        }
```

## Hata Yönetimi

```python
class PipelineError(Exception):
    def __init__(self, stage: str, error: str):
        self.stage = stage
        self.error = error

def handle_pipeline_error(error: PipelineError):
    if error.stage in ["test", "review"]:
        # Geri dön ve düzelt
        return "implement"
    elif error.stage == "deploy":
        # Rollback
        return "rollback"
    else:
        # Durdur
        raise error
```

## Checkpoint & Resume

```python
# Pipeline checkpoint
def save_checkpoint(state: PipelineState):
    with open(f".claude/checkpoints/pipeline-{state.id}.json", "w") as f:
        json.dump(state.to_dict(), f)

# Resume from checkpoint
def resume_pipeline(checkpoint_id: str):
    with open(f".claude/checkpoints/pipeline-{checkpoint_id}.json") as f:
        state = PipelineState.from_dict(json.load(f))
    return run_pipeline_from(state)
```

## Best Practices

1. **Her aşamayı atomik yap**: Tek sorumluluk
2. **Açık input/output**: Her aşamanın beklentileri net
3. **Checkpoint kullan**: Uzun pipeline'larda kayıp önleme
4. **Fail-fast**: Erken aşamalarda hızlı fail
5. **Rollback planı**: Her aşama için geri alma stratejisi

## Karşılaştırma

| Özellik | Pipeline | Fan-Out |
|---------|----------|---------|
| Bağımlılık | Sıralı | Bağımsız |
| Hız | Yavaş (sıralı) | Hızlı (paralel) |
| Hata yönetimi | Kolay | Zor |
| State yönetimi | Gerekli | Minimal |

## İlgili Patternler

- [Fan-Out](fan-out.md) - Paralel dağıtım
- [Watcher](watcher.md) - İzleme
- [Map-Reduce](map-reduce.md) - Dağıtılmış işleme
