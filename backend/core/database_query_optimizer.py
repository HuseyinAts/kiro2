"""
KIRO2 Database Query Optimizer
Efficient bulk loading and query optimization patterns for SQLAlchemy
"""

import logging
from typing import List, Optional, Any, Type, TypeVar
from datetime import datetime

from sqlalchemy import select, func, and_
from sqlalchemy.orm import (
    joinedload,
    selectinload,
    subqueryload,
    load_only,
    defer,
)
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

T = TypeVar("T")


class QueryOptimizer:
    """
    SQLAlchemy query optimization utilities

    Features:
    - Intelligent relationship loading strategies
    - N+1 query prevention
    - Efficient bulk operations
    - Query performance monitoring
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.query_stats = {"total_queries": 0, "total_time": 0.0, "slow_queries": []}

    # ========================================================================
    # RELATIONSHIP LOADING STRATEGIES
    # ========================================================================

    async def load_with_relationships(
        self,
        model: Type[T],
        *,
        joined: Optional[List[str]] = None,
        subquery: Optional[List[str]] = None,
        selectin: Optional[List[str]] = None,
        filters: Optional[Any] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[T]:
        """
        Load entities with optimized relationship loading

        Args:
            model: SQLAlchemy model class
            joined: Relationships to load with JOIN (one-to-one, small one-to-many)
            subquery: Relationships to load with subquery (large one-to-many)
            selectin: Relationships to load with SELECT IN (collections)
            filters: Filter conditions
            limit: Result limit
            offset: Result offset

        Returns:
            List of model instances with loaded relationships

        Example:
            students = await optimizer.load_with_relationships(
                Kullanici,
                joined=['ogrenme_profili'],  # One-to-one
                selectin=['sinav_sonuclari'],  # One-to-many collection
                filters=Kullanici.rol == 'ogrenci',
                limit=100
            )
        """
        query = select(model)

        # Apply joined loading (best for one-to-one, small one-to-many)
        if joined:
            for rel in joined:
                query = query.options(joinedload(getattr(model, rel)))

        # Apply subquery loading (for large collections)
        if subquery:
            for rel in subquery:
                query = query.options(subqueryload(getattr(model, rel)))

        # Apply selectin loading (efficient for collections)
        if selectin:
            for rel in selectin:
                query = query.options(selectinload(getattr(model, rel)))

        # Apply filters
        if filters is not None:
            query = query.where(filters)

        # Apply pagination
        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)

        # Execute and track performance
        start_time = datetime.now()
        result = await self.session.execute(query)
        elapsed = (datetime.now() - start_time).total_seconds()

        self._track_query(query, elapsed)

        return result.scalars().unique().all()

    async def load_students_with_data(
        self,
        student_ids: Optional[List[int]] = None,
        include_exam_results: bool = True,
        include_learning_path: bool = True,
        include_profile: bool = True,
        limit: Optional[int] = None,
    ) -> List:
        """
        Optimized student data loading

        Example of efficient bulk loading for common use case
        """
        from models_unified import Kullanici

        query = select(Kullanici).where(Kullanici.rol == "ogrenci")

        # Filter by specific IDs if provided
        if student_ids:
            query = query.where(Kullanici.id.in_(student_ids))

        # Load profile (one-to-one) with JOIN
        if include_profile:
            query = query.options(joinedload(Kullanici.ogrenme_profili))

        # Load exam results (one-to-many) with selectin
        if include_exam_results:
            query = query.options(selectinload(Kullanici.sinav_sonuclari))

        # Load learning paths (one-to-many) with selectin
        if include_learning_path:
            query = query.options(selectinload(Kullanici.ogrenme_yollari))

        # Apply limit
        if limit:
            query = query.limit(limit)

        result = await self.session.execute(query)
        return result.scalars().unique().all()

    # ========================================================================
    # LOADING STRATEGY SELECTION
    # ========================================================================

    @staticmethod
    def get_optimal_loading_strategy(
        relationship_type: str, collection_size: str = "medium"
    ) -> str:
        """
        Determine optimal loading strategy based on relationship characteristics

        Args:
            relationship_type: "one-to-one", "one-to-many", "many-to-many"
            collection_size: "small" (<10), "medium" (10-100), "large" (>100)

        Returns:
            Recommended strategy: "joined", "selectin", or "subquery"
        """
        strategy_matrix = {
            ("one-to-one", "small"): "joined",
            ("one-to-one", "medium"): "joined",
            ("one-to-one", "large"): "joined",
            ("one-to-many", "small"): "joined",
            ("one-to-many", "medium"): "selectin",
            ("one-to-many", "large"): "selectin",
            ("many-to-many", "small"): "selectin",
            ("many-to-many", "medium"): "selectin",
            ("many-to-many", "large"): "subquery",
        }

        return strategy_matrix.get(
            (relationship_type, collection_size), "selectin"  # Safe default
        )

    # ========================================================================
    # COLUMN-LEVEL OPTIMIZATION
    # ========================================================================

    async def load_with_selected_columns(
        self, model: Type[T], columns: List[str], filters: Optional[Any] = None
    ) -> List[T]:
        """
        Load only specific columns (deferred loading)

        Use when you only need a subset of columns

        Example:
            # Only load id, ad, soyad (skip email, parola_hash, etc.)
            students = await optimizer.load_with_selected_columns(
                Kullanici,
                columns=['id', 'ad', 'soyad'],
                filters=Kullanici.aktif == True
            )
        """
        query = select(model).options(
            load_only(*[getattr(model, col) for col in columns])
        )

        if filters is not None:
            query = query.where(filters)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def load_with_deferred_columns(
        self, model: Type[T], defer_columns: List[str], filters: Optional[Any] = None
    ) -> List[T]:
        """
        Load all columns except specified ones

        Use when you want to skip heavy columns (text, binary data)

        Example:
            # Skip heavy columns
            exams = await optimizer.load_with_deferred_columns(
                Sinav,
                defer_columns=['soru_icerik', 'cevap_anahtari'],
                filters=Sinav.durum == 'aktif'
            )
        """
        query = select(model)

        for col in defer_columns:
            query = query.options(defer(getattr(model, col)))

        if filters is not None:
            query = query.where(filters)

        result = await self.session.execute(query)
        return result.scalars().all()

    # ========================================================================
    # BULK OPERATIONS
    # ========================================================================

    async def bulk_insert(
        self, model: Type[T], data: List[dict], batch_size: int = 1000
    ) -> int:
        """
        Efficient bulk insert

        Example:
            students_data = [
                {'ad': 'Ali', 'soyad': 'Yılmaz', 'email': 'ali@example.com'},
                {'ad': 'Ayşe', 'soyad': 'Demir', 'email': 'ayse@example.com'},
                # ... 1000s more
            ]

            count = await optimizer.bulk_insert(
                Kullanici,
                students_data,
                batch_size=500
            )
        """
        total_inserted = 0

        # Process in batches
        for i in range(0, len(data), batch_size):
            batch = data[i : i + batch_size]

            # Create instances
            instances = [model(**item) for item in batch]

            # Add all at once
            self.session.add_all(instances)

            # Commit batch
            await self.session.flush()

            total_inserted += len(instances)

            logger.info(f"Bulk inserted {total_inserted}/{len(data)} records")

        await self.session.commit()

        return total_inserted

    async def bulk_update(
        self, model: Type[T], updates: List[dict], id_field: str = "id"
    ) -> int:
        """
        Efficient bulk update

        Example:
            updates = [
                {'id': 1, 'puan': 85.5, 'basari_durumu': 'başarılı'},
                {'id': 2, 'puan': 92.0, 'basari_durumu': 'başarılı'},
                # ... more
            ]

            count = await optimizer.bulk_update(
                SinavSonucu,
                updates
            )
        """
        # Use bulk_update_mappings for efficiency
        if updates:
            await self.session.execute(model.__table__.update(), updates)
            await self.session.commit()

        return len(updates)

    # ========================================================================
    # COMPLEX QUERIES
    # ========================================================================

    async def get_students_with_exam_stats(
        self, class_id: Optional[int] = None, min_exam_count: int = 0
    ) -> List[dict]:
        """
        Complex aggregation query example

        Returns students with their exam statistics
        """
        from models_unified import Kullanici, SinavSonucu

        query = (
            select(
                Kullanici.id,
                Kullanici.ad,
                Kullanici.soyad,
                func.count(SinavSonucu.id).label("sinav_sayisi"),
                func.avg(SinavSonucu.puan).label("ortalama_puan"),
                func.max(SinavSonucu.puan).label("en_yuksek_puan"),
                func.min(SinavSonucu.puan).label("en_dusuk_puan"),
            )
            .join(SinavSonucu, Kullanici.id == SinavSonucu.ogrenci_id)
            .where(Kullanici.rol == "ogrenci")
            .group_by(Kullanici.id, Kullanici.ad, Kullanici.soyad)
            .having(func.count(SinavSonucu.id) >= min_exam_count)
        )

        if class_id:
            query = query.where(Kullanici.sinif == class_id)

        result = await self.session.execute(query)

        return [
            {
                "id": row.id,
                "ad": row.ad,
                "soyad": row.soyad,
                "sinav_sayisi": row.sinav_sayisi,
                "ortalama_puan": float(row.ortalama_puan or 0),
                "en_yuksek_puan": float(row.en_yuksek_puan or 0),
                "en_dusuk_puan": float(row.en_dusuk_puan or 0),
            }
            for row in result
        ]

    async def get_top_performers(
        self, subject: Optional[str] = None, limit: int = 10
    ) -> List[dict]:
        """
        Get top performing students with efficient loading
        """
        from models_unified import Kullanici, SinavSonucu, Sinav

        query = (
            select(
                Kullanici.id,
                Kullanici.ad,
                Kullanici.soyad,
                func.avg(SinavSonucu.puan).label("ortalama"),
            )
            .join(SinavSonucu, Kullanici.id == SinavSonucu.ogrenci_id)
            .join(Sinav, SinavSonucu.sinav_id == Sinav.id)
            .where(Kullanici.rol == "ogrenci")
        )

        if subject:
            query = query.where(Sinav.konu == subject)

        query = (
            query.group_by(Kullanici.id, Kullanici.ad, Kullanici.soyad)
            .order_by(func.avg(SinavSonucu.puan).desc())
            .limit(limit)
        )

        result = await self.session.execute(query)

        return [
            {
                "id": row.id,
                "ad": row.ad,
                "soyad": row.soyad,
                "ortalama_puan": float(row.ortalama or 0),
            }
            for row in result
        ]

    # ========================================================================
    # PERFORMANCE MONITORING
    # ========================================================================

    def _track_query(self, query: Any, elapsed: float):
        """Track query performance"""
        self.query_stats["total_queries"] += 1
        self.query_stats["total_time"] += elapsed

        # Track slow queries (>1s)
        if elapsed > 1.0:
            self.query_stats["slow_queries"].append(
                {"query": str(query), "elapsed": elapsed, "timestamp": datetime.now()}
            )

            logger.warning(
                f"Slow query detected: {elapsed:.2f}s", extra={"query": str(query)}
            )

    def get_performance_stats(self) -> dict:
        """Get query performance statistics"""
        total_queries = self.query_stats["total_queries"]
        total_time = self.query_stats["total_time"]

        return {
            "total_queries": total_queries,
            "total_time": f"{total_time:.2f}s",
            "avg_time": f"{(total_time / total_queries if total_queries > 0 else 0):.3f}s",
            "slow_queries_count": len(self.query_stats["slow_queries"]),
            "slow_queries": self.query_stats["slow_queries"][-5:],  # Last 5
        }

    def reset_stats(self):
        """Reset performance statistics"""
        self.query_stats = {"total_queries": 0, "total_time": 0.0, "slow_queries": []}


# ============================================================================
# COMMON PATTERNS & EXAMPLES
# ============================================================================


class CommonQueryPatterns:
    """Collection of common query patterns for KIRO2"""

    @staticmethod
    async def get_student_dashboard_data(
        session: AsyncSession, student_id: int
    ) -> dict:
        """
        Efficient loading for student dashboard

        Loads all necessary data in minimal queries
        """
        from models_unified import Kullanici

        # Single query with all relationships
        query = (
            select(Kullanici)
            .where(Kullanici.id == student_id)
            .options(
                joinedload(Kullanici.ogrenme_profili),  # One-to-one
                selectinload(Kullanici.sinav_sonuclari),  # Collection
                selectinload(Kullanici.ogrenme_yollari),  # Collection
                selectinload(Kullanici.cozulen_sorular),  # Collection
            )
        )

        result = await session.execute(query)
        student = result.scalar_one_or_none()

        if not student:
            return None

        return {
            "student": student,
            "profile": student.ogrenme_profili,
            "exam_results": student.sinav_sonuclari,
            "learning_paths": student.ogrenme_yollari,
            "solved_questions": student.cozulen_sorular,
        }

    @staticmethod
    async def get_exam_with_questions(session: AsyncSession, exam_id: int) -> dict:
        """
        Load exam with all questions efficiently
        """
        from models_unified import Sinav

        query = (
            select(Sinav)
            .where(Sinav.id == exam_id)
            .options(selectinload(Sinav.sorular))  # All questions
        )

        result = await session.execute(query)
        exam = result.scalar_one_or_none()

        return {"exam": exam, "questions": exam.sorular if exam else []}

    @staticmethod
    async def get_class_performance_summary(
        session: AsyncSession, class_id: int
    ) -> dict:
        """
        Get class-wide performance summary with aggregations
        """
        from models_unified import Kullanici, SinavSonucu
        from sqlalchemy import func

        # Student count
        student_count_query = select(func.count(Kullanici.id)).where(
            and_(Kullanici.sinif == class_id, Kullanici.rol == "ogrenci")
        )
        student_count = await session.scalar(student_count_query)

        # Average score
        avg_score_query = (
            select(func.avg(SinavSonucu.puan))
            .join(Kullanici, SinavSonucu.ogrenci_id == Kullanici.id)
            .where(Kullanici.sinif == class_id)
        )
        avg_score = await session.scalar(avg_score_query) or 0

        # Total exams taken
        total_exams_query = (
            select(func.count(SinavSonucu.id))
            .join(Kullanici, SinavSonucu.ogrenci_id == Kullanici.id)
            .where(Kullanici.sinif == class_id)
        )
        total_exams = await session.scalar(total_exams_query)

        return {
            "class_id": class_id,
            "student_count": student_count,
            "average_score": float(avg_score),
            "total_exams_taken": total_exams,
        }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


async def get_optimizer(session: AsyncSession) -> QueryOptimizer:
    """Get query optimizer instance"""
    return QueryOptimizer(session)


def explain_loading_strategy(strategy: str) -> str:
    """Explain when to use each loading strategy"""
    explanations = {
        "joined": """
        JOINED LOADING (joinedload)
        - Best for: One-to-one relationships, small collections
        - Uses: SQL JOIN
        - Queries: Single query
        - Memory: Higher (loads all data at once)
        - Use when: Related data is always needed, collections are small
        """,
        "selectin": """
        SELECTIN LOADING (selectinload)
        - Best for: Collections, one-to-many relationships
        - Uses: IN clause (SELECT ... WHERE id IN (...))
        - Queries: N+1 → 2 (parent query + one collection query)
        - Memory: Moderate
        - Use when: Loading multiple parents with collections
        """,
        "subquery": """
        SUBQUERY LOADING (subqueryload)
        - Best for: Large collections
        - Uses: Subquery
        - Queries: 2 (parent + subquery for collections)
        - Memory: Lower
        - Use when: Very large collections, memory is concern
        """,
    }

    return explanations.get(strategy, "Unknown strategy")


# Example usage in documentation
"""
USAGE EXAMPLES:

1. Basic student loading with relationships:

   optimizer = await get_optimizer(session)
   students = await optimizer.load_students_with_data(
       student_ids=[1, 2, 3],
       include_exam_results=True,
       include_profile=True
   )

2. Custom relationship loading:

   students = await optimizer.load_with_relationships(
       Kullanici,
       joined=['ogrenme_profili'],
       selectin=['sinav_sonuclari', 'ogrenme_yollari'],
       filters=Kullanici.aktif == True,
       limit=100
   )

3. Column-level optimization:

   # Only load necessary columns
   students = await optimizer.load_with_selected_columns(
       Kullanici,
       columns=['id', 'ad', 'soyad', 'email'],
       filters=Kullanici.sinif == 11
   )

4. Bulk operations:

   # Bulk insert
   new_students = [
       {'ad': 'Ali', 'soyad': 'Yılmaz'},
       {'ad': 'Ayşe', 'soyad': 'Demir'},
       # ... more
   ]
   count = await optimizer.bulk_insert(Kullanici, new_students)

5. Performance monitoring:

   stats = optimizer.get_performance_stats()
   print(f"Total queries: {stats['total_queries']}")
   print(f"Slow queries: {stats['slow_queries_count']}")
"""
