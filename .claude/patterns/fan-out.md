# Fan-Out Pattern

## Açıklama

Bağımsız görevleri paralel olarak birden fazla worker agent'a dağıtır.
Sonuçlar merkezi olarak toplanır ve birleştirilir.

## Diyagram

```
                    Main Agent
                        │
          ┌─────────────┼─────────────┐
          │             │             │
          ▼             ▼             ▼
      Worker 1      Worker 2      Worker 3
          │             │             │
          └─────────────┼─────────────┘
                        │
                        ▼
                  Consolidation
```

## Ne Zaman Kullanılır

- Bağımsız dosya işleme (N dosyayı paralel analiz)
- Paralel test çalıştırma
- Çoklu API çağrıları
- Büyük veri setlerini parçalara ayırma
- Bağımsız modülleri aynı anda refactor etme

## Avantajlar

- ⚡ Hız: N worker ile N kat daha hızlı
- 🔄 Ölçeklenebilir: Worker sayısı artırılabilir
- 💪 Dayanıklı: Bir worker başarısız olsa da diğerleri devam eder

## Dezavantajlar

- 💰 Maliyet: Paralel API çağrıları daha pahalı
- 🔀 Karmaşıklık: Sonuç birleştirme mantığı gerekir
- ⚠️ Rate limiting: API limitlerine dikkat

## Implementasyon

### Python Örneği

```python
import asyncio
from dataclasses import dataclass

@dataclass
class Task:
    id: str
    prompt: str
    result: dict | None = None

async def fan_out(
    tasks: list[Task],
    max_workers: int = 7,
) -> list[Task]:
    """
    Görevleri paralel worker'lara dağıt.

    Args:
        tasks: Görev listesi
        max_workers: Maksimum paralel worker

    Returns:
        Tamamlanmış görevler
    """
    semaphore = asyncio.Semaphore(max_workers)

    async def worker(task: Task) -> Task:
        async with semaphore:
            # Agent'ı çağır
            result = await execute_agent(task.prompt)
            task.result = result
            return task

    # Tüm görevleri paralel çalıştır
    completed = await asyncio.gather(
        *[worker(t) for t in tasks],
        return_exceptions=True,
    )

    return completed
```

### Claude Code Kullanımı

```python
# 10 dosyayı paralel analiz et
files = glob.glob("backend/api/*.py")

# Fan-out: Her dosya için ayrı agent spawn et
tasks = []
for file in files[:10]:
    tasks.append(Task(
        name=f"analyze-{file}",
        prompt=f"Analyze {file} for security issues",
        subagent_type="code-reviewer",
        parallel=True,
    ))

# Tek mesajda tüm Task tool call'larını gönder
# Claude otomatik olarak paralel çalıştırır
```

## KIRO2 Örneği

### Soru Analizi Fan-Out

```python
# 100 soruyu 10 worker'a dağıt
questions = get_pending_questions(limit=100)
chunks = split_into_chunks(questions, 10)

for i, chunk in enumerate(chunks):
    Task(
        name=f"analyze-questions-{i}",
        prompt=f"""
        Bu {len(chunk)} soruyu analiz et:
        - IRT parametrelerini doğrula
        - ZPD uygunluğunu kontrol et
        - Duplicate kontrolü yap

        Sorular: {json.dumps(chunk)}
        """,
        subagent_type="python-pro",
        model="sonnet",
        parallel=True,
    )
```

### Ders Bazlı Paralel İşleme

```python
subjects = ["matematik", "fizik", "kimya", "biyoloji", "turkce"]

# Her ders için paralel analiz
for subject in subjects:
    Task(
        name=f"analyze-{subject}",
        prompt=f"{subject} dersinin soru dağılımını analiz et",
        subagent_type="turkish-nlp-specialist",
        parallel=True,
    )
```

## Sonuç Birleştirme (Consolidation)

```python
def consolidate_results(results: list[dict]) -> dict:
    """
    Fan-out sonuçlarını birleştir.

    Args:
        results: Worker sonuçları

    Returns:
        Birleştirilmiş sonuç
    """
    consolidated = {
        "total_processed": 0,
        "success_count": 0,
        "error_count": 0,
        "findings": [],
    }

    for result in results:
        if isinstance(result, Exception):
            consolidated["error_count"] += 1
            continue

        consolidated["total_processed"] += result.get("count", 0)
        consolidated["success_count"] += 1
        consolidated["findings"].extend(result.get("findings", []))

    return consolidated
```

## Best Practices

1. **Worker sayısını sınırla**: 7-10 paralel worker optimal
2. **Timeout ayarla**: Her worker için makul timeout
3. **Hata toleransı**: Bir worker fail olsa da devam et
4. **Progress tracking**: Tamamlanan görevleri izle
5. **Rate limiting**: API limitlerini aşma

## Karşılaştırma

| Özellik | Fan-Out | Sequential |
|---------|---------|------------|
| Hız | N kat hızlı | Yavaş |
| Maliyet | Yüksek | Düşük |
| Karmaşıklık | Orta | Düşük |
| Hata yönetimi | Zor | Kolay |

## İlgili Patternler

- [Map-Reduce](map-reduce.md) - Fan-out + reduce
- [Pipeline](pipeline.md) - Sıralı işleme
- [Watcher](watcher.md) - İzleme ve müdahale
