# Database Query Optimization Guide - KIRO2

## Overview

Comprehensive guide for efficient SQLAlchemy queries with focus on N+1 problem prevention, bulk loading, and performance optimization.

---

## Table of Contents

1. [The N+1 Problem](#the-n1-problem)
2. [Loading Strategies](#loading-strategies)
3. [Bulk Loading Patterns](#bulk-loading-patterns)
4. [Query Optimization](#query-optimization)
5. [Performance Monitoring](#performance-monitoring)
6. [Real-World Examples](#real-world-examples)

---

## The N+1 Problem

### What is it?

The N+1 problem occurs when you load a collection of N objects, then access a relationship on each object, triggering N additional queries.

### Example of N+1 Problem

```python
# ❌ BAD: N+1 queries
students = await session.execute(select(Kullanici))

for student in students.scalars():
    # Each iteration triggers a new query!
    profile = student.ogrenme_profili  # Query 1
    exams = student.sinav_sonuclari     # Query 2
    # Total: 1 + (N × 2) queries
```

**Result:** For 100 students → **201 queries!**

### Solution: Eager Loading

```python
# ✅ GOOD: 2-3 queries total
students = await session.execute(
    select(Kullanici)
    .options(
        joinedload(Kullanici.ogrenme_profili),    # Query 1 (JOIN)
        selectinload(Kullanici.sinav_sonuclari)   # Query 2 (SELECT IN)
    )
)

for student in students.scalars().unique():
    profile = student.ogrenme_profili  # No query!
    exams = student.sinav_sonuclari     # No query!
```

**Result:** For 100 students → **2 queries!** (99.5% reduction)

---

## Loading Strategies

### 1. Joined Loading (`joinedload`)

**When to use:**
- One-to-one relationships
- Small one-to-many collections (< 10 items)
- When related data is ALWAYS needed

**How it works:**
- Uses SQL JOIN
- Loads everything in one query
- Higher memory usage

**Example:**
```python
# Student with profile (one-to-one)
query = (
    select(Kullanici)
    .options(joinedload(Kullanici.ogrenme_profili))
)
```

**SQL Generated:**
```sql
SELECT kullanicilar.*, ogrenme_profilleri.*
FROM kullanicilar
LEFT OUTER JOIN ogrenme_profilleri
    ON kullanicilar.id = ogrenme_profilleri.kullanici_id
```

**Pros:**
- ✅ Single query
- ✅ Fast for small datasets
- ✅ No additional roundtrips

**Cons:**
- ❌ Cartesian product with large collections
- ❌ Higher memory usage
- ❌ Duplicate parent data in results

---

### 2. Select In Loading (`selectinload`)

**When to use:**
- Collections (one-to-many)
- Medium to large collections (10-1000 items)
- Most common use case

**How it works:**
- Two queries: parent + collections
- Uses `WHERE id IN (...)` clause
- Efficient for multiple parents

**Example:**
```python
# Students with exam results (one-to-many)
query = (
    select(Kullanici)
    .options(selectinload(Kullanici.sinav_sonuclari))
)
```

**SQL Generated:**
```sql
-- Query 1: Get students
SELECT * FROM kullanicilar;

-- Query 2: Get all exam results
SELECT * FROM sinav_sonuclari
WHERE ogrenci_id IN (1, 2, 3, 4, 5, ...);
```

**Pros:**
- ✅ Efficient for collections
- ✅ No cartesian products
- ✅ Scalable to many parents

**Cons:**
- ❌ Two queries instead of one
- ❌ Large IN clauses (if many parents)

---

### 3. Subquery Loading (`subqueryload`)

**When to use:**
- Very large collections (> 1000 items)
- When memory is a concern
- Complex filtering on collections

**How it works:**
- Uses subquery instead of IN clause
- Separate query with JOIN to subquery

**Example:**
```python
# Students with many solved questions
query = (
    select(Kullanici)
    .options(subqueryload(Kullanici.cozulen_sorular))
)
```

**SQL Generated:**
```sql
-- Query 1: Get students
SELECT * FROM kullanicilar;

-- Query 2: Get questions via subquery
SELECT cozulen_sorular.*
FROM cozulen_sorular
WHERE ogrenci_id IN (
    SELECT kullanicilar.id FROM kullanicilar
);
```

**Pros:**
- ✅ No large IN clauses
- ✅ Efficient for very large collections
- ✅ Better for complex filters

**Cons:**
- ❌ More complex SQL
- ❌ May be slower than selectin for small datasets

---

### Strategy Selection Matrix

| Relationship | Collection Size | Best Strategy | Queries |
|-------------|----------------|---------------|---------|
| One-to-one | N/A | `joinedload` | 1 |
| One-to-many | Small (< 10) | `joinedload` | 1 |
| One-to-many | Medium (10-100) | `selectinload` | 2 |
| One-to-many | Large (> 100) | `selectinload` | 2 |
| One-to-many | Very large (> 1000) | `subqueryload` | 2 |
| Many-to-many | Any | `selectinload` | 2 |

---

## Bulk Loading Patterns

### Pattern 1: Student Dashboard

**Requirements:**
- Load student
- Load profile (one-to-one)
- Load exam results (one-to-many)
- Load learning paths (one-to-many)

**Optimized Query:**
```python
from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload
from models_unified import Kullanici

query = (
    select(Kullanici)
    .where(Kullanici.id == student_id)
    .options(
        joinedload(Kullanici.ogrenme_profili),  # One-to-one
        selectinload(Kullanici.sinav_sonuclari),  # Collection
        selectinload(Kullanici.ogrenme_yollari)   # Collection
    )
)

result = await session.execute(query)
student = result.scalar_one_or_none()

# All relationships loaded! No additional queries
profile = student.ogrenme_profili
exams = student.sinav_sonuclari
paths = student.ogrenme_yollari
```

**Result:** 3 queries total (vs 100+ without optimization)

---

### Pattern 2: Class Performance Report

**Requirements:**
- Load all students in a class
- Load their exam results
- Calculate aggregates

**Optimized Query:**
```python
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

# Method 1: Load with relationships
students = await session.execute(
    select(Kullanici)
    .where(Kullanici.sinif == class_id)
    .options(
        selectinload(Kullanici.sinav_sonuclari)
    )
)

# Method 2: Aggregation query (better for stats only)
stats = await session.execute(
    select(
        Kullanici.id,
        Kullanici.ad,
        Kullanici.soyad,
        func.count(SinavSonucu.id).label('exam_count'),
        func.avg(SinavSonucu.puan).label('avg_score')
    )
    .join(SinavSonucu)
    .where(Kullanici.sinif == class_id)
    .group_by(Kullanici.id, Kullanici.ad, Kullanici.soyad)
)
```

---

### Pattern 3: Exam with Questions

**Requirements:**
- Load exam
- Load all questions
- Load question options

**Optimized Query:**
```python
exam = await session.execute(
    select(Sinav)
    .where(Sinav.id == exam_id)
    .options(
        selectinload(Sinav.sorular)  # All questions
    )
)

exam = exam.scalar_one_or_none()
questions = exam.sorular  # Already loaded!
```

---

## Query Optimization

### 1. Column-Level Loading

**Load only needed columns:**
```python
from sqlalchemy.orm import load_only

# Only load id, ad, soyad (skip email, parola_hash, etc.)
query = (
    select(Kullanici)
    .options(load_only(Kullanici.id, Kullanici.ad, Kullanici.soyad))
)
```

**Defer heavy columns:**
```python
from sqlalchemy.orm import defer

# Skip heavy text/binary columns
query = (
    select(Soru)
    .options(
        defer(Soru.aciklama),
        defer(Soru.cozum_videosu)
    )
)
```

---

### 2. Pagination

**Always use pagination for lists:**
```python
# Page 1: First 20 results
query = (
    select(Kullanici)
    .where(Kullanici.aktif == True)
    .limit(20)
    .offset(0)
)

# Page 2: Next 20 results
query = query.offset(20)
```

---

### 3. Filtering and Ordering

**Push filtering to database:**
```python
# ✅ GOOD: Filter in database
query = (
    select(Kullanici)
    .where(Kullanici.sinif == 11)
    .where(Kullanici.alan == 'Sayisal')
    .order_by(Kullanici.ad)
    .limit(100)
)

# ❌ BAD: Filter in Python
all_students = await session.execute(select(Kullanici))
filtered = [s for s in all_students if s.sinif == 11]  # Loads EVERYTHING!
```

---

### 4. Counting

**Use database COUNT:**
```python
# ✅ GOOD: Database COUNT
count = await session.scalar(
    select(func.count(Kullanici.id))
    .where(Kullanici.aktif == True)
)

# ❌ BAD: Load all then count in Python
students = await session.execute(select(Kullanici))
count = len(list(students.scalars()))  # Loads all data!
```

---

## Performance Monitoring

### Using QueryOptimizer

```python
from core.database_query_optimizer import get_optimizer

async with get_async_session() as session:
    optimizer = await get_optimizer(session)

    # Your queries here
    students = await optimizer.load_students_with_data(limit=100)

    # Get performance stats
    stats = optimizer.get_performance_stats()

    print(f"Total queries: {stats['total_queries']}")
    print(f"Average time: {stats['avg_time']}")
    print(f"Slow queries: {stats['slow_queries_count']}")
```

### Manual Monitoring

```python
import time
from datetime import datetime

# Track query time
start = datetime.now()
result = await session.execute(query)
elapsed = (datetime.now() - start).total_seconds()

if elapsed > 1.0:
    logger.warning(f"Slow query: {elapsed:.2f}s")
```

---

## Real-World Examples

### Example 1: Teacher Dashboard

**Requirements:**
- Teacher info
- Classes they teach
- Student count per class
- Recent exam results

```python
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload, selectinload

async def get_teacher_dashboard(teacher_id: int):
    # Get teacher with relationships
    teacher = await session.execute(
        select(Kullanici)
        .where(Kullanici.id == teacher_id)
        .options(
            # Get classes (if using separate model)
            selectinload(Kullanici.siniflar)
        )
    )
    teacher = teacher.scalar_one_or_none()

    # Get student counts per class
    class_stats = await session.execute(
        select(
            Kullanici.sinif,
            func.count(Kullanici.id).label('student_count')
        )
        .where(
            Kullanici.sinif.in_([c.id for c in teacher.siniflar])
        )
        .group_by(Kullanici.sinif)
    )

    return {
        'teacher': teacher,
        'classes': teacher.siniflar,
        'class_stats': class_stats.all()
    }
```

**Queries:** 3 (teacher + classes + stats)

---

### Example 2: Exam Results Report

**Requirements:**
- Exam details
- All student results
- Statistics (min, max, avg, median)

```python
async def get_exam_report(exam_id: int):
    # Load exam with results
    exam = await session.execute(
        select(Sinav)
        .where(Sinav.id == exam_id)
        .options(
            selectinload(Sinav.sinav_sonuclari)
            .joinedload(SinavSonucu.ogrenci)  # Nested loading
        )
    )
    exam = exam.scalar_one_or_none()

    # Calculate statistics
    stats = await session.execute(
        select(
            func.count(SinavSonucu.id).label('count'),
            func.min(SinavSonucu.puan).label('min'),
            func.max(SinavSonucu.puan).label('max'),
            func.avg(SinavSonucu.puan).label('avg')
        )
        .where(SinavSonucu.sinav_id == exam_id)
    )

    return {
        'exam': exam,
        'results': exam.sinav_sonuclari,
        'statistics': stats.one()._asdict()
    }
```

**Queries:** 3 (exam + results with students + statistics)

---

### Example 3: Student Progress Tracking

**Requirements:**
- Student info
- All completed exams
- Learning path progress
- Weak topics

```python
async def get_student_progress(student_id: int):
    # Load student with all data
    student = await session.execute(
        select(Kullanici)
        .where(Kullanici.id == student_id)
        .options(
            joinedload(Kullanici.ogrenme_profili),
            selectinload(Kullanici.sinav_sonuclari),
            selectinload(Kullanici.ogrenme_yollari),
            selectinload(Kullanici.cozulen_sorular)
        )
    )
    student = student.scalar_one_or_none()

    # Calculate weak topics (pure SQL aggregation)
    weak_topics = await session.execute(
        select(
            Soru.konu,
            func.count(CozulenSoru.id).label('total'),
            func.sum(
                case((CozulenSoru.dogru == True, 1), else_=0)
            ).label('correct'),
            (func.sum(case((CozulenSoru.dogru == True, 1), else_=0)) /
             func.count(CozulenSoru.id) * 100).label('success_rate')
        )
        .join(CozulenSoru, CozulenSoru.soru_id == Soru.id)
        .where(CozulenSoru.ogrenci_id == student_id)
        .group_by(Soru.konu)
        .having(
            (func.sum(case((CozulenSoru.dogru == True, 1), else_=0)) /
             func.count(CozulenSoru.id)) < 0.7  # Less than 70% success
        )
        .order_by('success_rate')
    )

    return {
        'student': student,
        'profile': student.ogrenme_profili,
        'exams': student.sinav_sonuclari,
        'paths': student.ogrenme_yollari,
        'weak_topics': weak_topics.all()
    }
```

**Queries:** 5 (efficient for comprehensive dashboard)

---

## Best Practices Summary

### ✅ DO

1. **Use eager loading** for relationships you WILL access
2. **Choose the right strategy** (joined vs selectin vs subquery)
3. **Use pagination** for lists
4. **Filter in database**, not Python
5. **Use aggregations** for statistics
6. **Monitor slow queries** (> 1s)
7. **Load only needed columns** for large tables
8. **Use bulk operations** for multiple inserts/updates

### ❌ DON'T

1. **Access relationships without eager loading** (N+1 problem)
2. **Load entire tables** without filters
3. **Use Python for filtering/aggregation** when SQL can do it
4. **Forget to use `unique()`** with joinedload
5. **Mix eager loading strategies** without understanding
6. **Load heavy columns** you don't need
7. **Execute queries in loops**

---

## Quick Reference

```python
# One-to-one: Use joinedload
.options(joinedload(Model.relationship))

# One-to-many: Use selectinload
.options(selectinload(Model.collection))

# Nested loading
.options(
    selectinload(Model.collection)
    .joinedload(Collection.relationship)
)

# Multiple relationships
.options(
    joinedload(Model.profile),
    selectinload(Model.exams),
    selectinload(Model.paths)
)

# Column selection
.options(load_only(Model.col1, Model.col2))

# Defer heavy columns
.options(defer(Model.heavy_column))

# With filters
.where(Model.field == value)

# With ordering
.order_by(Model.field.desc())

# With pagination
.limit(20).offset(0)

# Don't forget unique()!
result.scalars().unique().all()
```

---

## Performance Checklist

Before deploying a query to production, check:

- [ ] No N+1 queries (use eager loading)
- [ ] Appropriate loading strategy selected
- [ ] Pagination implemented for lists
- [ ] Filtering done in database
- [ ] Only necessary columns loaded
- [ ] Aggregations use SQL, not Python
- [ ] Query time < 1 second
- [ ] Proper indexes exist for filters/joins
- [ ] `unique()` called with joinedload
- [ ] Performance tested with realistic data volumes

---

## Additional Resources

- **SQLAlchemy Docs:** https://docs.sqlalchemy.org/
- **Loading Strategies:** https://docs.sqlalchemy.org/en/14/orm/loading_relationships.html
- **Query API:** https://docs.sqlalchemy.org/en/14/orm/queryguide/

---

**Last Updated:** 2025-10-02
**Version:** 1.0.0
**Author:** KIRO2 Development Team
