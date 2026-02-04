"""
Advanced Query Builder and ORM Patterns
Unified query building system for the enhanced database pattern consolidation

Bu dosya kapsamlı query building ve ORM pattern'leri sağlar:
- Type-safe query builder
- Advanced filtering ve sorting
- Relationship loading strategies
- Query optimization ve caching
- Pagination helpers
- Bulk operations
- Raw SQL execution helpers
"""

import logging
from abc import ABC
from dataclasses import dataclass
from enum import Enum
from typing import Any, Generic, TypeVar

from sqlalchemy import func, select, text, update
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, joinedload, selectinload
from sqlalchemy.sql import Select
from sqlalchemy.sql.elements import BinaryExpression

from .error_context import async_error_context
from .error_monitoring import log_error
from .exceptions import DatabaseError, ErrorSeverity, ValidationError

# Type variables
T = TypeVar("T", bound=DeclarativeBase)
PK = TypeVar("PK")

logger = logging.getLogger(__name__)


# ==================== QUERY BUILDER ENUMS ====================


class SortOrder(Enum):
    """Sort order options"""

    ASC = "asc"
    DESC = "desc"


class JoinType(Enum):
    """Join type options"""

    INNER = "inner"
    LEFT = "left"
    RIGHT = "right"
    FULL = "full"


class ComparisonOperator(Enum):
    """Comparison operators for filtering"""

    EQ = "eq"  # Equal
    NE = "ne"  # Not equal
    LT = "lt"  # Less than
    LE = "le"  # Less than or equal
    GT = "gt"  # Greater than
    GE = "ge"  # Greater than or equal
    LIKE = "like"  # Like (pattern matching)
    ILIKE = "ilike"  # Case insensitive like
    IN = "in"  # In list
    NOT_IN = "not_in"  # Not in list
    IS_NULL = "is_null"  # Is null
    IS_NOT_NULL = "is_not_null"  # Is not null
    BETWEEN = "between"  # Between values
    CONTAINS = "contains"  # Contains (for arrays/JSON)
    STARTS_WITH = "starts_with"  # Starts with
    ENDS_WITH = "ends_with"  # Ends with


# ==================== QUERY FILTER CLASSES ====================


@dataclass
class QueryFilter:
    """Represents a single query filter"""

    field: str
    operator: ComparisonOperator
    value: Any
    case_sensitive: bool = True

    def to_sql_condition(self, model_class: type[T]):
        """Convert filter to SQLAlchemy condition"""
        try:
            # Get the column from the model
            column = getattr(model_class, self.field)

            if self.operator == ComparisonOperator.EQ:
                return column == self.value
            if self.operator == ComparisonOperator.NE:
                return column != self.value
            if self.operator == ComparisonOperator.LT:
                return column < self.value
            if self.operator == ComparisonOperator.LE:
                return column <= self.value
            if self.operator == ComparisonOperator.GT:
                return column > self.value
            if self.operator == ComparisonOperator.GE:
                return column >= self.value
            if self.operator == ComparisonOperator.LIKE:
                if self.case_sensitive:
                    return column.like(f"%{self.value}%")
                return column.ilike(f"%{self.value}%")
            if self.operator == ComparisonOperator.ILIKE:
                return column.ilike(f"%{self.value}%")
            if self.operator == ComparisonOperator.IN:
                return column.in_(self.value)
            if self.operator == ComparisonOperator.NOT_IN:
                return ~column.in_(self.value)
            if self.operator == ComparisonOperator.IS_NULL:
                return column.is_(None)
            if self.operator == ComparisonOperator.IS_NOT_NULL:
                return column.is_not(None)
            if self.operator == ComparisonOperator.BETWEEN:
                if isinstance(self.value, (list, tuple)) and len(self.value) == 2:
                    return column.between(self.value[0], self.value[1])
                raise ValidationError("Between operator requires exactly 2 values")
            if self.operator == ComparisonOperator.CONTAINS:
                # For JSON/array columns
                return column.contains(self.value)
            if self.operator == ComparisonOperator.STARTS_WITH:
                if self.case_sensitive:
                    return column.like(f"{self.value}%")
                return column.ilike(f"{self.value}%")
            if self.operator == ComparisonOperator.ENDS_WITH:
                if self.case_sensitive:
                    return column.like(f"%{self.value}")
                return column.ilike(f"%{self.value}")
            raise ValidationError(f"Unsupported operator: {self.operator}")

        except AttributeError:
            raise ValidationError(
                f"Field '{self.field}' not found in model {model_class.__name__}"
            )


@dataclass
class QuerySort:
    """Represents query sorting"""

    field: str
    order: SortOrder = SortOrder.ASC

    def to_sql_order(self, model_class: type[T]):
        """Convert sort to SQLAlchemy order_by clause"""
        try:
            column = getattr(model_class, self.field)

            if self.order == SortOrder.ASC:
                return column.asc()
            return column.desc()

        except AttributeError:
            raise ValidationError(
                f"Field '{self.field}' not found in model {model_class.__name__}"
            )


@dataclass
class QueryJoin:
    """Represents a query join"""

    target_class: type[T]
    join_type: JoinType = JoinType.LEFT
    on_condition: Any | None = None
    alias: str | None = None


@dataclass
class PaginationParams:
    """Pagination parameters"""

    page: int = 1
    page_size: int = 20

    def __post_init__(self):
        if self.page < 1:
            raise ValidationError("Page number must be >= 1")
        if self.page_size < 1 or self.page_size > 1000:
            raise ValidationError("Page size must be between 1 and 1000")

    @property
    def offset(self) -> int:
        """Calculate offset for database query"""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """Get limit for database query"""
        return self.page_size


@dataclass
class QueryResult(Generic[T]):
    """Query result with metadata"""

    items: list[T]
    total_count: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool
    total_pages: int
    query_time_ms: float

    @classmethod
    def create(
        cls,
        items: list[T],
        total_count: int,
        pagination: PaginationParams,
        query_time_ms: float,
    ) -> "QueryResult[T]":
        """Create query result from items and pagination"""
        total_pages = (total_count + pagination.page_size - 1) // pagination.page_size

        return cls(
            items=items,
            total_count=total_count,
            page=pagination.page,
            page_size=pagination.page_size,
            has_next=pagination.page < total_pages,
            has_prev=pagination.page > 1,
            total_pages=total_pages,
            query_time_ms=query_time_ms,
        )


# ==================== ADVANCED QUERY BUILDER ====================


class QueryBuilder(Generic[T]):
    """Advanced type-safe query builder"""

    def __init__(self, model_class: type[T], session: AsyncSession):
        self.model_class = model_class
        self.session = session
        self._base_query = select(model_class)
        self._filters: list[QueryFilter] = []
        self._sorts: list[QuerySort] = []
        self._joins: list[QueryJoin] = []
        self._select_related: list[str] = []
        self._prefetch_related: list[str] = []
        self._group_by: list[str] = []
        self._having_filters: list[QueryFilter] = []
        self._distinct = False
        self._limit_value: int | None = None
        self._offset_value: int | None = None

    def filter(self, **kwargs) -> "QueryBuilder[T]":
        """Add filters using keyword arguments"""
        for field, value in kwargs.items():
            if isinstance(value, dict) and "operator" in value:
                # Advanced filter: {'operator': 'like', 'value': 'test'}
                operator = ComparisonOperator(value["operator"])
                filter_value = value["value"]
                case_sensitive = value.get("case_sensitive", True)

                filter_obj = QueryFilter(
                    field=field,
                    operator=operator,
                    value=filter_value,
                    case_sensitive=case_sensitive,
                )
            else:
                # Simple equality filter
                filter_obj = QueryFilter(
                    field=field, operator=ComparisonOperator.EQ, value=value
                )

            self._filters.append(filter_obj)

        return self

    def filter_by_condition(self, condition: BinaryExpression) -> "QueryBuilder[T]":
        """Add raw SQLAlchemy condition"""
        self._base_query = self._base_query.where(condition)
        return self

    def order_by(
        self, field: str, order: SortOrder = SortOrder.ASC
    ) -> "QueryBuilder[T]":
        """Add ordering"""
        self._sorts.append(QuerySort(field=field, order=order))
        return self

    def join(
        self,
        target_class: type[T],
        join_type: JoinType = JoinType.LEFT,
        on_condition: Any | None = None,
        alias: str | None = None,
    ) -> "QueryBuilder[T]":
        """Add join"""
        self._joins.append(
            QueryJoin(
                target_class=target_class,
                join_type=join_type,
                on_condition=on_condition,
                alias=alias,
            )
        )
        return self

    def select_related(self, *fields: str) -> "QueryBuilder[T]":
        """Add eager loading for relationships (joinedload)"""
        self._select_related.extend(fields)
        return self

    def prefetch_related(self, *fields: str) -> "QueryBuilder[T]":
        """Add eager loading for relationships (selectinload)"""
        self._prefetch_related.extend(fields)
        return self

    def distinct(self, distinct: bool = True) -> "QueryBuilder[T]":
        """Add DISTINCT clause"""
        self._distinct = distinct
        return self

    def group_by(self, *fields: str) -> "QueryBuilder[T]":
        """Add GROUP BY clause"""
        self._group_by.extend(fields)
        return self

    def having(self, **kwargs) -> "QueryBuilder[T]":
        """Add HAVING clause filters"""
        for field, value in kwargs.items():
            if isinstance(value, dict) and "operator" in value:
                operator = ComparisonOperator(value["operator"])
                filter_value = value["value"]
                case_sensitive = value.get("case_sensitive", True)

                filter_obj = QueryFilter(
                    field=field,
                    operator=operator,
                    value=filter_value,
                    case_sensitive=case_sensitive,
                )
            else:
                filter_obj = QueryFilter(
                    field=field, operator=ComparisonOperator.EQ, value=value
                )

            self._having_filters.append(filter_obj)

        return self

    def limit(self, limit: int) -> "QueryBuilder[T]":
        """Add LIMIT clause"""
        self._limit_value = limit
        return self

    def offset(self, offset: int) -> "QueryBuilder[T]":
        """Add OFFSET clause"""
        self._offset_value = offset
        return self

    def paginate(self, pagination: PaginationParams) -> "QueryBuilder[T]":
        """Add pagination"""
        return self.limit(pagination.limit).offset(pagination.offset)

    def _build_query(self) -> Select:
        """Build the final SQLAlchemy query"""
        query = self._base_query

        # Apply joins
        for join_obj in self._joins:
            if join_obj.join_type == JoinType.INNER:
                query = query.join(join_obj.target_class, join_obj.on_condition)
            elif join_obj.join_type == JoinType.LEFT:
                query = query.outerjoin(join_obj.target_class, join_obj.on_condition)
            # Add other join types as needed

        # Apply filters
        for filter_obj in self._filters:
            condition = filter_obj.to_sql_condition(self.model_class)
            query = query.where(condition)

        # Apply GROUP BY
        if self._group_by:
            group_columns = []
            for field in self._group_by:
                try:
                    column = getattr(self.model_class, field)
                    group_columns.append(column)
                except AttributeError:
                    raise ValidationError(
                        f"Field '{field}' not found in model {self.model_class.__name__}"
                    )
            query = query.group_by(*group_columns)

        # Apply HAVING
        for having_filter in self._having_filters:
            condition = having_filter.to_sql_condition(self.model_class)
            query = query.having(condition)

        # Apply ORDER BY
        if self._sorts:
            order_columns = []
            for sort_obj in self._sorts:
                order_column = sort_obj.to_sql_order(self.model_class)
                order_columns.append(order_column)
            query = query.order_by(*order_columns)

        # Apply DISTINCT
        if self._distinct:
            query = query.distinct()

        # Apply LIMIT and OFFSET
        if self._limit_value is not None:
            query = query.limit(self._limit_value)

        if self._offset_value is not None:
            query = query.offset(self._offset_value)

        # Apply eager loading
        if self._select_related or self._prefetch_related:
            options = []

            for field in self._select_related:
                options.append(joinedload(getattr(self.model_class, field)))

            for field in self._prefetch_related:
                options.append(selectinload(getattr(self.model_class, field)))

            query = query.options(*options)

        return query

    async def all(self) -> list[T]:
        """Execute query and return all results"""
        async with async_error_context(
            operation_name="query_builder_all",
            entity_type=self.model_class.__name__.lower(),
            business_operation="query_execution",
        ) as ctx:
            try:
                query = self._build_query()

                # Log query for debugging
                ctx.add_annotation(f"Executing query for {self.model_class.__name__}")

                import time

                start_time = time.time()

                result = await self.session.execute(query)
                items = result.scalars().all()

                query_time = (time.time() - start_time) * 1000

                ctx.add_annotation(
                    f"Query returned {len(items)} results in {query_time:.2f}ms"
                )

                return list(items)

            except Exception as e:
                ctx.add_annotation(f"Query execution failed: {e!s}")
                await log_error(e, ctx.to_dict(), ErrorSeverity.HIGH)
                raise DatabaseError(
                    message="Query execution failed",
                    operation="query_builder_all",
                    details={"model": self.model_class.__name__, "error": str(e)},
                )

    async def first(self) -> T | None:
        """Execute query and return first result"""
        results = await self.limit(1).all()
        return results[0] if results else None

    async def one(self) -> T:
        """Execute query and return exactly one result"""
        results = await self.limit(2).all()  # Limit 2 to check for multiple

        if len(results) == 0:
            raise DatabaseError(
                message="No results found for query", operation="query_builder_one"
            )
        if len(results) > 1:
            raise DatabaseError(
                message="Multiple results found for query expecting one",
                operation="query_builder_one",
            )

        return results[0]

    async def count(self) -> int:
        """Get count of results"""
        async with async_error_context(
            operation_name="query_builder_count",
            entity_type=self.model_class.__name__.lower(),
            business_operation="count_query",
        ) as ctx:
            try:
                # Build count query
                count_query = select(func.count()).select_from(self.model_class)

                # Apply filters (but not ordering, limiting, etc.)
                for filter_obj in self._filters:
                    condition = filter_obj.to_sql_condition(self.model_class)
                    count_query = count_query.where(condition)

                # Apply joins for count
                for join_obj in self._joins:
                    if join_obj.join_type == JoinType.INNER:
                        count_query = count_query.join(
                            join_obj.target_class, join_obj.on_condition
                        )
                    elif join_obj.join_type == JoinType.LEFT:
                        count_query = count_query.outerjoin(
                            join_obj.target_class, join_obj.on_condition
                        )

                import time

                start_time = time.time()

                result = await self.session.execute(count_query)
                count = result.scalar()

                query_time = (time.time() - start_time) * 1000
                ctx.add_annotation(
                    f"Count query returned {count} in {query_time:.2f}ms"
                )

                return count

            except Exception as e:
                ctx.add_annotation(f"Count query failed: {e!s}")
                await log_error(e, ctx.to_dict(), ErrorSeverity.MEDIUM)
                raise DatabaseError(
                    message="Count query execution failed",
                    operation="query_builder_count",
                    details={"model": self.model_class.__name__, "error": str(e)},
                )

    async def paginated(self, pagination: PaginationParams) -> QueryResult[T]:
        """Execute paginated query"""
        async with async_error_context(
            operation_name="query_builder_paginated",
            entity_type=self.model_class.__name__.lower(),
            business_operation="paginated_query",
        ) as ctx:
            ctx.tags.update(
                {"page": str(pagination.page), "page_size": str(pagination.page_size)}
            )

            try:
                import time

                start_time = time.time()

                # Get total count and items in parallel
                count_task = asyncio.create_task(self.count())
                items_task = asyncio.create_task(self.paginate(pagination).all())

                total_count, items = await asyncio.gather(count_task, items_task)

                query_time = (time.time() - start_time) * 1000

                ctx.add_annotation(
                    f"Paginated query returned {len(items)}/{total_count} results in {query_time:.2f}ms"
                )

                return QueryResult.create(items, total_count, pagination, query_time)

            except Exception as e:
                ctx.add_annotation(f"Paginated query failed: {e!s}")
                await log_error(e, ctx.to_dict(), ErrorSeverity.HIGH)
                raise DatabaseError(
                    message="Paginated query execution failed",
                    operation="query_builder_paginated",
                    details={
                        "model": self.model_class.__name__,
                        "page": pagination.page,
                        "page_size": pagination.page_size,
                        "error": str(e),
                    },
                )

    async def exists(self) -> bool:
        """Check if any results exist"""
        count = await self.count()
        return count > 0

    def to_sql(self) -> str:
        """Get the SQL representation of the query (for debugging)"""
        query = self._build_query()
        return str(
            query.compile(
                dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
            )
        )


# ==================== REPOSITORY BASE CLASS ====================


class BaseRepository(Generic[T, PK], ABC):
    """Enhanced base repository with comprehensive CRUD operations"""

    def __init__(self, session: AsyncSession, model_class: type[T]):
        self.session = session
        self.model_class = model_class

    def query(self) -> QueryBuilder[T]:
        """Get a new query builder for this model"""
        return QueryBuilder(self.model_class, self.session)

    async def get_by_id(self, pk: PK) -> T | None:
        """Get entity by primary key"""
        async with async_error_context(
            operation_name="repository_get_by_id",
            entity_type=self.model_class.__name__.lower(),
            entity_id=str(pk),
            business_operation="get_by_id",
        ) as ctx:
            try:
                # Get primary key column name
                inspector = sa_inspect(self.model_class)
                pk_columns = inspector.primary_key

                if len(pk_columns) != 1:
                    raise ValidationError("get_by_id only supports single primary key")

                pk_column = pk_columns[0]

                result = await self.session.get(self.model_class, pk)

                ctx.add_annotation(f"Entity {'found' if result else 'not found'}")

                return result

            except Exception as e:
                ctx.add_annotation(f"Get by ID failed: {e!s}")
                await log_error(e, ctx.to_dict(), ErrorSeverity.MEDIUM)
                raise DatabaseError(
                    message=f"Failed to get {self.model_class.__name__} by ID",
                    operation="get_by_id",
                    details={"id": str(pk), "error": str(e)},
                )

    async def create(self, **kwargs) -> T:
        """Create new entity"""
        async with async_error_context(
            operation_name="repository_create",
            entity_type=self.model_class.__name__.lower(),
            business_operation="create",
        ) as ctx:
            try:
                entity = self.model_class(**kwargs)
                self.session.add(entity)
                await self.session.flush()
                await self.session.refresh(entity)

                ctx.add_annotation("Entity created successfully")

                return entity

            except Exception as e:
                ctx.add_annotation(f"Entity creation failed: {e!s}")
                await log_error(e, ctx.to_dict(), ErrorSeverity.HIGH)
                raise DatabaseError(
                    message=f"Failed to create {self.model_class.__name__}",
                    operation="create",
                    details={"data": kwargs, "error": str(e)},
                )

    async def update(self, entity: T, **kwargs) -> T:
        """Update existing entity"""
        async with async_error_context(
            operation_name="repository_update",
            entity_type=self.model_class.__name__.lower(),
            business_operation="update",
        ) as ctx:
            try:
                for key, value in kwargs.items():
                    if hasattr(entity, key):
                        setattr(entity, key, value)
                    else:
                        raise ValidationError(
                            f"Field '{key}' not found in {self.model_class.__name__}"
                        )

                await self.session.flush()
                await self.session.refresh(entity)

                ctx.add_annotation("Entity updated successfully")

                return entity

            except Exception as e:
                ctx.add_annotation(f"Entity update failed: {e!s}")
                await log_error(e, ctx.to_dict(), ErrorSeverity.HIGH)
                raise DatabaseError(
                    message=f"Failed to update {self.model_class.__name__}",
                    operation="update",
                    details={"data": kwargs, "error": str(e)},
                )

    async def delete(self, entity: T) -> bool:
        """Delete entity"""
        async with async_error_context(
            operation_name="repository_delete",
            entity_type=self.model_class.__name__.lower(),
            business_operation="delete",
        ) as ctx:
            try:
                await self.session.delete(entity)
                await self.session.flush()

                ctx.add_annotation("Entity deleted successfully")

                return True

            except Exception as e:
                ctx.add_annotation(f"Entity deletion failed: {e!s}")
                await log_error(e, ctx.to_dict(), ErrorSeverity.HIGH)
                raise DatabaseError(
                    message=f"Failed to delete {self.model_class.__name__}",
                    operation="delete",
                    details={"error": str(e)},
                )

    async def delete_by_id(self, pk: PK) -> bool:
        """Delete entity by primary key"""
        entity = await self.get_by_id(pk)
        if entity:
            return await self.delete(entity)
        return False

    async def bulk_create(self, entities_data: list[dict[str, Any]]) -> list[T]:
        """Bulk create entities"""
        async with async_error_context(
            operation_name="repository_bulk_create",
            entity_type=self.model_class.__name__.lower(),
            business_operation="bulk_create",
        ) as ctx:
            ctx.add_annotation(f"Bulk creating {len(entities_data)} entities")

            try:
                entities = []
                for data in entities_data:
                    entity = self.model_class(**data)
                    entities.append(entity)
                    self.session.add(entity)

                await self.session.flush()

                # Refresh all entities
                for entity in entities:
                    await self.session.refresh(entity)

                ctx.add_annotation("Bulk creation successful")

                return entities

            except Exception as e:
                ctx.add_annotation(f"Bulk creation failed: {e!s}")
                await log_error(e, ctx.to_dict(), ErrorSeverity.HIGH)
                raise DatabaseError(
                    message=f"Failed to bulk create {self.model_class.__name__}",
                    operation="bulk_create",
                    details={"count": len(entities_data), "error": str(e)},
                )

    async def bulk_update(self, updates: list[dict[str, Any]]) -> int:
        """Bulk update entities"""
        async with async_error_context(
            operation_name="repository_bulk_update",
            entity_type=self.model_class.__name__.lower(),
            business_operation="bulk_update",
        ) as ctx:
            ctx.add_annotation(f"Bulk updating {len(updates)} entities")

            try:
                updated_count = 0

                for update_data in updates:
                    if "id" not in update_data:
                        raise ValidationError(
                            "Bulk update requires 'id' field in each update"
                        )

                    pk = update_data.pop("id")

                    stmt = (
                        update(self.model_class)
                        .where(self.model_class.id == pk)
                        .values(**update_data)
                    )

                    result = await self.session.execute(stmt)
                    updated_count += result.rowcount

                ctx.add_annotation(
                    f"Bulk update successful: {updated_count} rows affected"
                )

                return updated_count

            except Exception as e:
                ctx.add_annotation(f"Bulk update failed: {e!s}")
                await log_error(e, ctx.to_dict(), ErrorSeverity.HIGH)
                raise DatabaseError(
                    message=f"Failed to bulk update {self.model_class.__name__}",
                    operation="bulk_update",
                    details={"count": len(updates), "error": str(e)},
                )


# ==================== FACTORY FUNCTIONS ====================


def create_repository(
    model_class: type[T], session: AsyncSession
) -> BaseRepository[T, Any]:
    """Factory function to create repository for a model"""

    class ConcreteRepository(BaseRepository[T, Any]):
        pass

    return ConcreteRepository(session, model_class)


async def execute_raw_sql(
    session: AsyncSession, sql: str, params: dict[str, Any] | None = None
) -> Any:
    """Execute raw SQL with error handling and monitoring"""

    async with async_error_context(
        operation_name="execute_raw_sql", business_operation="raw_sql_execution"
    ) as ctx:
        ctx.add_annotation(f"Executing raw SQL: {sql[:100]}...")

        try:
            import time

            start_time = time.time()

            if params:
                result = await session.execute(text(sql), params)
            else:
                result = await session.execute(text(sql))

            query_time = (time.time() - start_time) * 1000

            ctx.add_annotation(f"Raw SQL executed successfully in {query_time:.2f}ms")

            return result

        except Exception as e:
            ctx.add_annotation(f"Raw SQL execution failed: {e!s}")
            await log_error(e, ctx.to_dict(), ErrorSeverity.HIGH)
            raise DatabaseError(
                message="Raw SQL execution failed",
                operation="execute_raw_sql",
                details={"sql": sql[:200], "params": params, "error": str(e)},
            )


# ==================== QUERY OPTIMIZATION HELPERS ====================


class QueryOptimizer:
    """Query optimization utilities"""

    @staticmethod
    def analyze_query_performance(query_builder: QueryBuilder[T]) -> dict[str, Any]:
        """Analyze query performance characteristics"""

        sql = query_builder.to_sql()

        analysis = {
            "sql_length": len(sql),
            "has_joins": len(query_builder._joins) > 0,
            "join_count": len(query_builder._joins),
            "filter_count": len(query_builder._filters),
            "sort_count": len(query_builder._sorts),
            "has_eager_loading": bool(
                query_builder._select_related or query_builder._prefetch_related
            ),
            "has_distinct": query_builder._distinct,
            "has_group_by": bool(query_builder._group_by),
            "estimated_complexity": "low",
        }

        # Estimate complexity
        complexity_score = 0
        complexity_score += len(query_builder._joins) * 2
        complexity_score += len(query_builder._filters)
        complexity_score += len(query_builder._sorts)
        complexity_score += len(query_builder._select_related) * 3
        complexity_score += len(query_builder._prefetch_related) * 2

        if complexity_score < 5:
            analysis["estimated_complexity"] = "low"
        elif complexity_score < 15:
            analysis["estimated_complexity"] = "medium"
        else:
            analysis["estimated_complexity"] = "high"

        return analysis

    @staticmethod
    def suggest_optimizations(query_builder: QueryBuilder[T]) -> list[str]:
        """Suggest query optimizations"""

        suggestions = []

        # Check for N+1 queries
        if query_builder._select_related or query_builder._prefetch_related:
            suggestions.append("[CHECK] Using eager loading to prevent N+1 queries")
        elif len(query_builder._joins) == 0:
            suggestions.append(
                "⚠️ Consider using select_related() or prefetch_related() for related objects"
            )

        # Check for inefficient filtering
        if len(query_builder._filters) > 10:
            suggestions.append("⚠️ Large number of filters may impact performance")

        # Check for sorting on unindexed columns
        for sort in query_builder._sorts:
            suggestions.append(
                f"[BULB] Ensure '{sort.field}' column is indexed for optimal sorting"
            )

        # Check for DISTINCT usage
        if query_builder._distinct:
            suggestions.append("⚠️ DISTINCT can be expensive - ensure it's necessary")

        return suggestions
