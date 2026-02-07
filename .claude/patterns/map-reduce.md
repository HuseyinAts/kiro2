# Map-Reduce Pattern

## Açıklama

Büyük işleri parçalara böl (Map), paralel işle, sonuçları birleştir (Reduce).
Fan-Out pattern'inin bir varyasyonu olup, sonuç birleştirme mantığı daha gelişmiştir.

## Diyagram

```
                  ┌─────────────────────────────────────────┐
                  │           Input Data (N items)          │
                  └─────────────────────────────────────────┘
                                      │
                                      ▼ Split
          ┌───────────────────────────┼───────────────────────────┐
          │                           │                           │
          ▼                           ▼                           ▼
    ┌──────────┐                ┌──────────┐                ┌──────────┐
    │ Worker 1 │                │ Worker 2 │                │ Worker 3 │
    │ (1-16)   │                │ (17-32)  │                │ (33-47)  │
    └────┬─────┘                └────┬─────┘                └────┬─────┘
         │ Map                       │ Map                       │ Map
         ▼                           ▼                           ▼
    ┌──────────┐                ┌──────────┐                ┌──────────┐
    │ Result 1 │                │ Result 2 │                │ Result 3 │
    └────┬─────┘                └────┬─────┘                └────┬─────┘
         │                           │                           │
         └───────────────────────────┼───────────────────────────┘
                                     │
                                     ▼ Reduce
                          ┌─────────────────────┐
                          │   Merged Results    │
                          └─────────────────────┘
```

## Ne Zaman Kullanılır

- Büyük ölçekli refactoring (47 service'i 3 worker'a böl)
- Batch veri işleme (1000 soru analizi)
- Test suite parallelization
- Log aggregation
- Metrik hesaplama
- Embedding generation

## Implementasyon

### Map Fonksiyonu

```python
from typing import TypeVar, Callable, Iterable

T = TypeVar("T")
R = TypeVar("R")

def map_parallel(
    items: list[T],
    mapper: Callable[[T], R],
    num_workers: int = 7,
) -> list[R]:
    """
    Items'ları paralel olarak map et.

    Args:
        items: İşlenecek öğeler
        mapper: Her öğeye uygulanacak fonksiyon
        num_workers: Worker sayısı

    Returns:
        Mapped sonuçlar
    """
    import asyncio

    async def worker(chunk: list[T]) -> list[R]:
        return [await mapper(item) for item in chunk]

    chunks = split_into_chunks(items, num_workers)
    results = asyncio.run(asyncio.gather(
        *[worker(chunk) for chunk in chunks]
    ))

    return flatten(results)
```

### Reduce Fonksiyonu

```python
from functools import reduce

def reduce_results(
    results: list[dict],
    reducer: Callable[[dict, dict], dict],
    initial: dict | None = None,
) -> dict:
    """
    Sonuçları birleştir.

    Args:
        results: Worker sonuçları
        reducer: Birleştirme fonksiyonu
        initial: Başlangıç değeri

    Returns:
        Birleştirilmiş sonuç
    """
    if initial is None:
        initial = {}

    return reduce(reducer, results, initial)
```

## KIRO2 Örneği

### Soru Bankası Analizi

```python
# 10,000 soruyu analiz et
all_questions = get_all_questions()  # 10,000 soru

# Map: Soruları 10 worker'a böl
NUM_WORKERS = 10
chunk_size = len(all_questions) // NUM_WORKERS

async def analyze_chunk(questions: list[Question]) -> dict:
    """Her chunk'ı analiz et."""
    return {
        "total": len(questions),
        "valid_irt": sum(1 for q in questions if validate_irt(q)),
        "in_zpd": sum(1 for q in questions if check_zpd(q)),
        "subjects": Counter(q.subject for q in questions),
        "difficulties": [q.difficulty for q in questions],
    }

# Paralel çalıştır
chunks = split_into_chunks(all_questions, NUM_WORKERS)
results = await asyncio.gather(
    *[analyze_chunk(chunk) for chunk in chunks]
)

# Reduce: Sonuçları birleştir
def merge_analysis(acc: dict, result: dict) -> dict:
    return {
        "total": acc["total"] + result["total"],
        "valid_irt": acc["valid_irt"] + result["valid_irt"],
        "in_zpd": acc["in_zpd"] + result["in_zpd"],
        "subjects": acc["subjects"] + result["subjects"],
        "difficulties": acc["difficulties"] + result["difficulties"],
    }

final = reduce_results(results, merge_analysis, {
    "total": 0,
    "valid_irt": 0,
    "in_zpd": 0,
    "subjects": Counter(),
    "difficulties": [],
})
```

### Büyük Ölçekli Refactoring

```python
# 47 service'i refactor et
services = glob.glob("backend/services/*.py")  # 47 dosya

# 3 worker'a böl
chunks = [
    services[0:16],   # Worker 1
    services[16:32],  # Worker 2
    services[32:47],  # Worker 3
]

# Her worker için Task oluştur
for i, chunk in enumerate(chunks):
    Task(
        name=f"refactor-chunk-{i}",
        prompt=f"""
        Bu {len(chunk)} service dosyasını refactor et:
        - Type hints ekle
        - Docstring ekle
        - Pydantic v2 migrate et

        Dosyalar: {chunk}
        """,
        subagent_type="python-pro",
        parallel=True,
    )

# Sonuçları topla ve birleştir
results = await collect_task_results()
summary = reduce_refactoring_results(results)
```

## Chunk Stratejileri

### Eşit Bölme

```python
def split_equal(items: list, n: int) -> list[list]:
    """Eşit parçalara böl."""
    k, m = divmod(len(items), n)
    return [
        items[i * k + min(i, m):(i + 1) * k + min(i + 1, m)]
        for i in range(n)
    ]
```

### Ağırlıklı Bölme

```python
def split_weighted(items: list, weights: list[int]) -> list[list]:
    """Ağırlıklara göre böl (büyük dosyalar dengelenir)."""
    sorted_items = sorted(items, key=lambda x: x.size, reverse=True)
    buckets = [[] for _ in range(len(weights))]
    bucket_weights = [0] * len(weights)

    for item in sorted_items:
        min_idx = bucket_weights.index(min(bucket_weights))
        buckets[min_idx].append(item)
        bucket_weights[min_idx] += item.size

    return buckets
```

## Reduce Stratejileri

### Sum Reduce

```python
def sum_reduce(results: list[dict]) -> dict:
    return {
        key: sum(r.get(key, 0) for r in results)
        for key in results[0].keys()
    }
```

### Merge Reduce

```python
def merge_reduce(results: list[dict]) -> dict:
    merged = {}
    for result in results:
        for key, value in result.items():
            if key not in merged:
                merged[key] = value
            elif isinstance(value, list):
                merged[key].extend(value)
            elif isinstance(value, dict):
                merged[key].update(value)
            else:
                merged[key] += value
    return merged
```

### Tree Reduce

```python
async def tree_reduce(
    results: list[dict],
    reducer: Callable,
    batch_size: int = 3,
) -> dict:
    """Hiyerarşik reduce (çok büyük sonuç setleri için)."""
    while len(results) > 1:
        batches = [
            results[i:i + batch_size]
            for i in range(0, len(results), batch_size)
        ]
        results = await asyncio.gather(
            *[reducer(batch) for batch in batches]
        )
    return results[0]
```

## Best Practices

1. **Chunk boyutunu dengele**: Çok küçük → overhead, çok büyük → yavaş
2. **Idempotent map**: Aynı input → aynı output
3. **Commutative reduce**: Sıra önemli olmamalı
4. **Hata toleransı**: Bir chunk fail olursa retry
5. **Progress tracking**: Her chunk'ın durumunu izle

## Karşılaştırma

| Özellik | Map-Reduce | Fan-Out | Pipeline |
|---------|------------|---------|----------|
| Parallelism | Yüksek | Yüksek | Düşük |
| Result merge | Kompleks | Basit | N/A |
| Use case | Büyük veri | Bağımsız işler | Sıralı işler |
| Hata kurtarma | Chunk retry | Task retry | Stage retry |

## İlgili Patternler

- [Fan-Out](fan-out.md) - Daha basit paralel dağıtım
- [Pipeline](pipeline.md) - Sıralı işleme
- [Watcher](watcher.md) - İzleme ve müdahale
