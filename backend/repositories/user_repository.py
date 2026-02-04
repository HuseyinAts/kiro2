"""
User Repository
Kullanıcı ve profil yönetimi için özel repository
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from models.database import (
    LearningStyle,
    ParentProfile,
    StudentProfile,
    TeacherProfile,
    User,
    UserRole,
)

from .base import BaseRepository


class UserRepository(BaseRepository[User]):
    """User repository with authentication methods"""

    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return await self.get_by_field("email", email)

    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return await self.get_by_field("username", username)

    async def get_with_profile(self, user_id: str) -> Optional[User]:
        """Get user with appropriate profile loaded"""
        try:
            result = await self.session.execute(
                select(User)
                .options(
                    selectinload(User.student_profile),
                    selectinload(User.teacher_profile),
                    selectinload(User.parent_profile),
                )
                .where(User.id == user_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user with profile: {str(e)}")
            raise

    async def create_user_with_profile(
        self, user_data: Dict[str, Any], profile_data: Dict[str, Any], role: UserRole
    ) -> User:
        """Create user with appropriate profile"""
        try:
            # Create user
            user = await self.create(**user_data)

            # Create profile based on role
            if role == UserRole.STUDENT:
                profile = StudentProfile(user_id=user.id, **profile_data)
            elif role == UserRole.TEACHER:
                profile = TeacherProfile(user_id=user.id, **profile_data)
            elif role == UserRole.PARENT:
                profile = ParentProfile(user_id=user.id, **profile_data)
            else:
                return user  # Admin doesn't need profile

            self.session.add(profile)
            await self.session.flush()
            await self.session.refresh(user)

            return user
        except Exception as e:
            logger.error(f"Error creating user with profile: {str(e)}")
            await self.session.rollback()
            raise

    async def update_last_login(self, user_id: str) -> None:
        """Update user's last login timestamp"""
        await self.update(user_id, last_login=datetime.now())

    async def get_active_users(
        self, role: Optional[UserRole] = None, skip: int = 0, limit: int = 100
    ) -> List[User]:
        """Get active users by role"""
        filters = {"is_active": True}
        if role:
            filters["role"] = role

        return await self.get_all(skip=skip, limit=limit, filters=filters)

    async def search_users(
        self,
        search_term: str,
        role: Optional[UserRole] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[User]:
        """Search users by name, email, or username"""
        try:
            query = select(User).where(User.is_active == True)

            if role:
                query = query.where(User.role == role)

            # Search in multiple fields
            search_condition = or_(
                User.first_name.ilike(f"%{search_term}%"),
                User.last_name.ilike(f"%{search_term}%"),
                User.email.ilike(f"%{search_term}%"),
                User.username.ilike(f"%{search_term}%"),
            )
            query = query.where(search_condition)

            query = query.offset(skip).limit(limit)

            result = await self.session.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error searching users: {str(e)}")
            raise


class StudentRepository(BaseRepository[StudentProfile]):
    """Student profile repository"""

    def __init__(self, session: AsyncSession):
        super().__init__(StudentProfile, session)

    async def get_by_user_id(self, user_id: str) -> Optional[StudentProfile]:
        """Get student profile by user ID"""
        return await self.get_by_field("user_id", user_id)

    async def get_with_user(self, student_id: str) -> Optional[StudentProfile]:
        """Get student with user information"""
        try:
            result = await self.session.execute(
                select(StudentProfile)
                .options(joinedload(StudentProfile.user))
                .where(StudentProfile.id == student_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting student with user: {str(e)}")
            raise

    async def get_by_grade_level(
        self, grade_level: int, skip: int = 0, limit: int = 100
    ) -> List[StudentProfile]:
        """Get students by grade level"""
        return await self.get_all(
            skip=skip, limit=limit, filters={"grade_level": grade_level}
        )

    async def get_by_learning_style(
        self, learning_style: LearningStyle, skip: int = 0, limit: int = 100
    ) -> List[StudentProfile]:
        """Get students by learning style"""
        return await self.get_all(
            skip=skip, limit=limit, filters={"learning_style": learning_style}
        )

    async def update_performance_stats(
        self,
        student_id: str,
        questions_solved: int,
        correct_answers: int,
        study_hours: int,
    ) -> Optional[StudentProfile]:
        """Update student performance statistics"""
        try:
            student = await self.get_by_id(student_id)
            if not student:
                return None

            # Update cumulative stats
            new_total_questions = student.total_questions_solved + questions_solved
            new_correct_answers = student.correct_answers + correct_answers
            new_study_hours = student.total_study_hours + study_hours

            # Calculate new current level based on performance
            if new_total_questions > 0:
                accuracy = new_correct_answers / new_total_questions
                new_level = min(10.0, accuracy * 10.0)  # Scale to 0-10
            else:
                new_level = student.current_level

            return await self.update(
                student_id,
                total_questions_solved=new_total_questions,
                correct_answers=new_correct_answers,
                total_study_hours=new_study_hours,
                current_level=new_level,
            )
        except Exception as e:
            logger.error(f"Error updating student performance: {str(e)}")
            raise

    async def update_learning_profile(
        self,
        student_id: str,
        vark_profile: Optional[Dict[str, Any]] = None,
        zpd_range: Optional[Dict[str, Any]] = None,
        irt_ability: Optional[float] = None,
        fsrs_parameters: Optional[Dict[str, Any]] = None,
    ) -> Optional[StudentProfile]:
        """Update student's revolutionary learning features"""
        update_data = {}

        if vark_profile is not None:
            update_data["vark_profile"] = vark_profile
        if zpd_range is not None:
            update_data["zpd_range"] = zpd_range
        if irt_ability is not None:
            update_data["irt_ability"] = irt_ability
        if fsrs_parameters is not None:
            update_data["fsrs_parameters"] = fsrs_parameters

        if update_data:
            return await self.update(student_id, **update_data)

        return await self.get_by_id(student_id)


class TeacherRepository(BaseRepository[TeacherProfile]):
    """Teacher profile repository"""

    def __init__(self, session: AsyncSession):
        super().__init__(TeacherProfile, session)

    async def get_by_user_id(self, user_id: str) -> Optional[TeacherProfile]:
        """Get teacher profile by user ID"""
        return await self.get_by_field("user_id", user_id)

    async def get_with_classes(self, teacher_id: str) -> Optional[TeacherProfile]:
        """Get teacher with classes"""
        try:
            result = await self.session.execute(
                select(TeacherProfile)
                .options(selectinload(TeacherProfile.classes))
                .where(TeacherProfile.id == teacher_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting teacher with classes: {str(e)}")
            raise

    async def get_by_subject_area(
        self, subject_area: str, skip: int = 0, limit: int = 100
    ) -> List[TeacherProfile]:
        """Get teachers by subject area"""
        try:
            result = await self.session.execute(
                select(TeacherProfile)
                .where(TeacherProfile.subject_areas.contains([subject_area]))
                .offset(skip)
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting teachers by subject: {str(e)}")
            raise


class ParentRepository(BaseRepository[ParentProfile]):
    """Parent profile repository"""

    def __init__(self, session: AsyncSession):
        super().__init__(ParentProfile, session)

    async def get_by_user_id(self, user_id: str) -> Optional[ParentProfile]:
        """Get parent profile by user ID"""
        return await self.get_by_field("user_id", user_id)

    async def add_child(self, parent_id: str, child_id: str) -> Optional[ParentProfile]:
        """Add child to parent's children list"""
        try:
            parent = await self.get_by_id(parent_id)
            if not parent:
                return None

            if child_id not in parent.children_ids:
                new_children = parent.children_ids + [child_id]
                return await self.update(parent_id, children_ids=new_children)

            return parent
        except Exception as e:
            logger.error(f"Error adding child to parent: {str(e)}")
            raise

    async def remove_child(
        self, parent_id: str, child_id: str
    ) -> Optional[ParentProfile]:
        """Remove child from parent's children list"""
        try:
            parent = await self.get_by_id(parent_id)
            if not parent:
                return None

            if child_id in parent.children_ids:
                new_children = [cid for cid in parent.children_ids if cid != child_id]
                return await self.update(parent_id, children_ids=new_children)

            return parent
        except Exception as e:
            logger.error(f"Error removing child from parent: {str(e)}")
            raise
