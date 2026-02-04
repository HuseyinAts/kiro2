"""
Base Repository Pattern Implementation
Generic CRUD operations for all models
"""

import logging
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.database import Base

logger = logging.getLogger(__name__)

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Generic repository for CRUD operations"""

    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def create(self, **kwargs) -> ModelType:
        """Create a new record"""
        try:
            instance = self.model(**kwargs)
            self.session.add(instance)
            await self.session.flush()
            await self.session.refresh(instance)
            return instance
        except SQLAlchemyError as e:
            logger.error(f"Error creating {self.model.__name__}: {str(e)}")
            await self.session.rollback()
            raise

    async def get_by_id(self, id: str) -> Optional[ModelType]:
        """Get record by ID"""
        try:
            result = await self.session.execute(
                select(self.model).where(self.model.id == id)
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Error getting {self.model.__name__} by id {id}: {str(e)}")
            raise

    async def get_by_field(self, field_name: str, value: Any) -> Optional[ModelType]:
        """Get record by specific field"""
        try:
            field = getattr(self.model, field_name)
            result = await self.session.execute(
                select(self.model).where(field == value)
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(
                f"Error getting {self.model.__name__} by {field_name}: {str(e)}"
            )
            raise

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[ModelType]:
        """Get all records with pagination and filtering"""
        try:
            query = select(self.model)

            # Apply filters
            if filters:
                for field_name, value in filters.items():
                    if hasattr(self.model, field_name):
                        field = getattr(self.model, field_name)
                        if isinstance(value, list):
                            query = query.where(field.in_(value))
                        else:
                            query = query.where(field == value)

            # Apply ordering
            if order_by and hasattr(self.model, order_by):
                order_field = getattr(self.model, order_by)
                query = query.order_by(order_field)

            # Apply pagination
            query = query.offset(skip).limit(limit)

            result = await self.session.execute(query)
            return result.scalars().all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting all {self.model.__name__}: {str(e)}")
            raise

    async def update(self, id: str, **kwargs) -> Optional[ModelType]:
        """Update record by ID"""
        try:
            # Remove None values
            update_data = {k: v for k, v in kwargs.items() if v is not None}

            if not update_data:
                return await self.get_by_id(id)

            await self.session.execute(
                update(self.model).where(self.model.id == id).values(**update_data)
            )

            return await self.get_by_id(id)
        except SQLAlchemyError as e:
            logger.error(f"Error updating {self.model.__name__} {id}: {str(e)}")
            await self.session.rollback()
            raise

    async def delete(self, id: str) -> bool:
        """Delete record by ID"""
        try:
            result = await self.session.execute(
                delete(self.model).where(self.model.id == id)
            )
            return result.rowcount > 0
        except SQLAlchemyError as e:
            logger.error(f"Error deleting {self.model.__name__} {id}: {str(e)}")
            await self.session.rollback()
            raise

    async def soft_delete(self, id: str) -> Optional[ModelType]:
        """Soft delete record (set is_active = False)"""
        if hasattr(self.model, "is_active"):
            return await self.update(id, is_active=False)
        else:
            raise NotImplementedError(
                f"{self.model.__name__} does not support soft delete"
            )

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records with optional filtering"""
        try:
            query = select(func.count(self.model.id))

            # Apply filters
            if filters:
                for field_name, value in filters.items():
                    if hasattr(self.model, field_name):
                        field = getattr(self.model, field_name)
                        if isinstance(value, list):
                            query = query.where(field.in_(value))
                        else:
                            query = query.where(field == value)

            result = await self.session.execute(query)
            return result.scalar()
        except SQLAlchemyError as e:
            logger.error(f"Error counting {self.model.__name__}: {str(e)}")
            raise

    async def exists(self, **kwargs) -> bool:
        """Check if record exists"""
        try:
            query = select(self.model.id)

            for field_name, value in kwargs.items():
                if hasattr(self.model, field_name):
                    field = getattr(self.model, field_name)
                    query = query.where(field == value)

            result = await self.session.execute(query.limit(1))
            return result.scalar() is not None
        except SQLAlchemyError as e:
            logger.error(f"Error checking existence in {self.model.__name__}: {str(e)}")
            raise

    async def bulk_create(self, objects: List[Dict[str, Any]]) -> List[ModelType]:
        """Bulk create multiple records"""
        try:
            instances = [self.model(**obj) for obj in objects]
            self.session.add_all(instances)
            await self.session.flush()

            # Refresh all instances to get generated IDs
            for instance in instances:
                await self.session.refresh(instance)

            return instances
        except SQLAlchemyError as e:
            logger.error(f"Error bulk creating {self.model.__name__}: {str(e)}")
            await self.session.rollback()
            raise

    async def bulk_update(self, updates: List[Dict[str, Any]]) -> int:
        """Bulk update multiple records"""
        try:
            updated_count = 0
            for update_data in updates:
                if "id" not in update_data:
                    continue

                record_id = update_data.pop("id")
                result = await self.session.execute(
                    update(self.model)
                    .where(self.model.id == record_id)
                    .values(**update_data)
                )
                updated_count += result.rowcount

            return updated_count
        except SQLAlchemyError as e:
            logger.error(f"Error bulk updating {self.model.__name__}: {str(e)}")
            await self.session.rollback()
            raise

    async def search(
        self,
        search_term: str,
        search_fields: List[str],
        skip: int = 0,
        limit: int = 100,
    ) -> List[ModelType]:
        """Search records by text in specified fields"""
        try:
            query = select(self.model)

            # Build search conditions
            search_conditions = []
            for field_name in search_fields:
                if hasattr(self.model, field_name):
                    field = getattr(self.model, field_name)
                    # Use ILIKE for case-insensitive search
                    search_conditions.append(field.ilike(f"%{search_term}%"))

            if search_conditions:
                query = query.where(or_(*search_conditions))

            query = query.offset(skip).limit(limit)

            result = await self.session.execute(query)
            return result.scalars().all()
        except SQLAlchemyError as e:
            logger.error(f"Error searching {self.model.__name__}: {str(e)}")
            raise

    async def get_with_relations(
        self, id: str, relations: List[str]
    ) -> Optional[ModelType]:
        """Get record with specified relationships loaded"""
        try:
            query = select(self.model).where(self.model.id == id)

            # Add relationship loading
            for relation in relations:
                if hasattr(self.model, relation):
                    query = query.options(selectinload(getattr(self.model, relation)))

            result = await self.session.execute(query)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(
                f"Error getting {self.model.__name__} with relations: {str(e)}"
            )
            raise

    async def commit(self):
        """Commit transaction"""
        try:
            await self.session.commit()
        except SQLAlchemyError as e:
            logger.error(f"Error committing transaction: {str(e)}")
            await self.session.rollback()
            raise

    async def rollback(self):
        """Rollback transaction"""
        await self.session.rollback()

    async def refresh(self, instance: ModelType):
        """Refresh instance from database"""
        await self.session.refresh(instance)
