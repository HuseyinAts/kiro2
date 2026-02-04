"""
Enhanced User Service - Demonstrates Database Pattern Consolidation
Refactored user service using the new enhanced database patterns

Bu dosya yeni database pattern'lerin kullanımını gösterir:
- Enhanced database connection management
- Type-safe query builder
- Advanced transaction management
- Repository pattern implementation
- Error handling integration
- Performance monitoring
"""

import logging
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from passlib.context import CryptContext

# Import enhanced database patterns
from core.enhanced_database import enhanced_db_manager
from core.error_context import (
    annotate_error_context,
    async_error_context,
    error_context_decorator,
)
from core.error_monitoring import log_error
from core.exceptions import (
    DatabaseError,
    ErrorFactory,
    ErrorSeverity,
    ValidationError,
)
from core.query_builder import (
    BaseRepository,
    PaginationParams,
    QueryResult,
    SortOrder,
)
from core.transaction_manager import (
    TransactionConfig,
    TransactionIsolationLevel,
    managed_transaction,
    retryable_transaction,
)

# Import models (these would be the actual SQLAlchemy models)
# NOTE: UserProfile uses StudentProfile as it contains the necessary user profile fields
# UserSession and UserSettings are defined below as service-specific models
# If production requires separate tables, create migrations and update models.database
from models.database import User, StudentProfile as UserProfile
from sqlalchemy import or_, Column, String, DateTime, JSON, Integer
from sqlalchemy.ext.asyncio import AsyncSession
from models_unified import Base

logger = logging.getLogger(__name__)

# Password hashing using bcrypt (same as user_service.py)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Service-specific models for user session and settings management
class UserSession(Base):
    """
    User session model for tracking active sessions
    NOTE: This is a service-specific model. If you need persistent sessions,
    add migration to create user_sessions table in database
    """

    __tablename__ = "user_sessions_placeholder"
    id = Column(String, primary_key=True)
    user_id = Column(Integer)
    token = Column(String)
    created_at = Column(DateTime)
    expires_at = Column(DateTime)


class UserSettings(Base):
    """
    User settings model for storing user preferences
    NOTE: This is a service-specific model. If you need persistent settings,
    add migration to create user_settings table in database
    """

    __tablename__ = "user_settings_placeholder"
    id = Column(String, primary_key=True)
    user_id = Column(Integer)
    settings_data = Column(JSON)


# ==================== ENHANCED REPOSITORY CLASSES ====================


class UserRepository(BaseRepository[User, str]):
    """Enhanced user repository with business logic"""

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email address"""
        return await self.query().filter(email=email).first()

    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return await self.query().filter(username=username).first()

    async def get_active_users(self, role: Optional[str] = None) -> List[User]:
        """Get all active users, optionally filtered by role"""
        query_builder = self.query().filter(status="active")

        if role:
            query_builder.filter(role=role)

        return await query_builder.order_by("created_at", SortOrder.DESC).all()

    async def search_users(
        self,
        search_term: str,
        role: Optional[str] = None,
        pagination: Optional[PaginationParams] = None,
    ) -> QueryResult[User]:
        """Search users with optional role filter and pagination"""

        query_builder = self.query().filter(
            or_(
                username={"operator": "ilike", "value": f"%{search_term}%"},
                email={"operator": "ilike", "value": f"%{search_term}%"},
                full_name={"operator": "ilike", "value": f"%{search_term}%"},
            )
        )

        if role:
            query_builder.filter(role=role)

        query_builder.order_by("username", SortOrder.ASC)

        if pagination:
            return await query_builder.paginated(pagination)
        else:
            items = await query_builder.all()
            return QueryResult.create(items, len(items), PaginationParams(), 0)

    async def get_user_with_profile(self, user_id: str) -> Optional[User]:
        """Get user with profile eagerly loaded"""
        return (
            await self.query()
            .filter(id=user_id)
            .select_related("profile", "settings")
            .first()
        )

    async def get_users_created_after(self, date: datetime) -> List[User]:
        """Get users created after specific date"""
        return (
            await self.query()
            .filter(created_at={"operator": "gte", "value": date})
            .order_by("created_at", SortOrder.ASC)
            .all()
        )

    async def update_last_login(self, user_id: str) -> bool:
        """Update user's last login timestamp"""
        try:
            user = await self.get_by_id(user_id)
            if user:
                user.last_login_at = datetime.utcnow()
                await self.session.flush()
                return True
            return False
        except Exception as e:
            await log_error(e, {"user_id": user_id}, ErrorSeverity.MEDIUM)
            return False

    async def get_user_statistics(self) -> Dict[str, Any]:
        """Get comprehensive user statistics"""

        # Total users
        total_users = await self.count()

        # Users by status
        active_users = await self.query().filter(status="active").count()
        inactive_users = await self.query().filter(status="inactive").count()

        # Users by role
        students = await self.query().filter(role="student").count()
        teachers = await self.query().filter(role="teacher").count()
        admins = await self.query().filter(role="admin").count()

        # Recent users (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_users = (
            await self.query()
            .filter(created_at={"operator": "gte", "value": thirty_days_ago})
            .count()
        )

        return {
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": inactive_users,
            "users_by_role": {
                "students": students,
                "teachers": teachers,
                "admins": admins,
            },
            "recent_users_30_days": recent_users,
            "last_updated": datetime.utcnow(),
        }


class UserProfileRepository(BaseRepository[UserProfile, str]):
    """Repository for user profile management"""

    async def get_by_user_id(self, user_id: str) -> Optional[UserProfile]:
        """Get profile by user ID"""
        return await self.query().filter(user_id=user_id).first()

    async def update_profile_data(
        self, user_id: str, profile_data: Dict[str, Any]
    ) -> Optional[UserProfile]:
        """Update profile data for user"""
        profile = await self.get_by_user_id(user_id)
        if profile:
            for key, value in profile_data.items():
                if hasattr(profile, key):
                    setattr(profile, key, value)

            profile.updated_at = datetime.utcnow()
            await self.session.flush()

        return profile


# ==================== ENHANCED USER SERVICE ====================


class EnhancedUserService:
    """Enhanced user service with comprehensive database patterns"""

    def __init__(self):
        self.password_salt_rounds = 12
        self.token_expiry_hours = 24

    def _hash_password(self, password: str) -> str:
        """Hash password with bcrypt (same as user_service.py)"""
        return pwd_context.hash(password)

    def _verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify password against bcrypt hash"""
        return pwd_context.verify(password, hashed_password)

    def _generate_token(self) -> str:
        """Generate secure access token"""
        return secrets.token_urlsafe(32)

    @error_context_decorator("create_user_enhanced", capture_args=True)
    async def create_user(
        self, user_data: Dict[str, Any], profile_data: Optional[Dict[str, Any]] = None
    ) -> Tuple[User, UserProfile]:
        """
        Create user with profile using enhanced transaction management

        Demonstrates:
        - Transaction with savepoints
        - Repository pattern usage
        - Error handling with context
        - Automatic retry on conflicts
        """

        # Validate input data
        if not user_data.get("email"):
            raise ErrorFactory.validation_error(
                field="email",
                value=user_data.get("email"),
                constraint="required",
                message="Email is required",
            )

        if not user_data.get("password"):
            raise ErrorFactory.validation_error(
                field="password",
                value="[HIDDEN]",
                constraint="required",
                message="Password is required",
            )

        if len(user_data.get("password", "")) < 8:
            raise ErrorFactory.validation_error(
                field="password",
                value="[HIDDEN]",
                constraint="min_length_8",
                message="Password must be at least 8 characters long",
            )

        # Use retryable transaction for conflict handling
        config = TransactionConfig(
            isolation_level=TransactionIsolationLevel.READ_COMMITTED,
            retry_attempts=3,
            retry_delay=1.0,
            enable_savepoints=True,
        )

        async with managed_transaction(config) as tx_ctx:
            user_repo = UserRepository(tx_ctx.session, User)
            profile_repo = UserProfileRepository(tx_ctx.session, UserProfile)

            annotate_error_context("Starting user creation process")

            # Check for existing email
            existing_user = await user_repo.get_by_email(user_data["email"])
            if existing_user:
                raise ErrorFactory.business_logic_error(
                    rule_name="unique_email",
                    context={"email": user_data["email"]},
                    message="Email address is already in use",
                )

            # Check for existing username if provided
            if user_data.get("username"):
                existing_username = await user_repo.get_by_username(
                    user_data["username"]
                )
                if existing_username:
                    raise ErrorFactory.business_logic_error(
                        rule_name="unique_username",
                        context={"username": user_data["username"]},
                        message="Username is already taken",
                    )

            # Create user
            user_id = str(uuid.uuid4())
            password_hash = self._hash_password(user_data["password"])

            user = await user_repo.create(
                id=user_id,
                username=user_data.get("username", user_data["email"].split("@")[0]),
                email=user_data["email"],
                password_hash=password_hash,
                full_name=user_data.get("full_name", ""),
                role=user_data.get("role", "student"),
                status="active",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            annotate_error_context(f"User created with ID: {user.id}")

            # Create savepoint after user creation
            savepoint = await tx_ctx.create_savepoint("user_created")

            try:
                # Create user profile
                profile_info = profile_data or {}
                profile = UserProfile(
                    id=str(uuid.uuid4()),
                    user_id=user.id,
                    bio=profile_info.get("bio", ""),
                    avatar_url=profile_info.get("avatar_url"),
                    date_of_birth=profile_info.get("date_of_birth"),
                    phone_number=profile_info.get("phone_number"),
                    address=profile_info.get("address"),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )

                tx_ctx.session.add(profile)
                await tx_ctx.session.flush()

                annotate_error_context("User profile created successfully")

            except Exception as profile_error:
                # Rollback to savepoint and create minimal profile
                await tx_ctx.rollback_to_savepoint(savepoint)

                annotate_error_context(
                    "Profile creation failed, creating minimal profile"
                )

                # Create minimal profile
                minimal_profile = UserProfile(
                    id=str(uuid.uuid4()),
                    user_id=user.id,
                    bio="",
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )

                tx_ctx.session.add(minimal_profile)
                await tx_ctx.session.flush()

                profile = minimal_profile

                # Log the original error but don't fail the operation
                await log_error(
                    profile_error,
                    {"user_id": user.id, "profile_data": profile_data},
                    ErrorSeverity.MEDIUM,
                )

            # Create user settings with another savepoint
            settings_savepoint = await tx_ctx.create_savepoint("profile_created")

            try:
                settings = UserSettings(
                    id=str(uuid.uuid4()),
                    user_id=user.id,
                    theme="light",
                    language="tr",
                    notifications_enabled=True,
                    email_notifications=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )

                tx_ctx.session.add(settings)
                await tx_ctx.session.flush()

                annotate_error_context("User settings created successfully")

            except Exception as settings_error:
                # Settings creation failed, but continue without it
                await tx_ctx.rollback_to_savepoint(settings_savepoint)

                annotate_error_context(
                    "Settings creation failed, continuing without default settings"
                )

                await log_error(settings_error, {"user_id": user.id}, ErrorSeverity.LOW)

            annotate_error_context("User creation process completed successfully")

            return user, profile

    @error_context_decorator(
        "authenticate_user", capture_args=False
    )  # Don't capture password
    async def authenticate_user(
        self, email: str, password: str
    ) -> Optional[Dict[str, Any]]:
        """
        Authenticate user with enhanced error handling and monitoring

        Demonstrates:
        - Read-only session usage
        - Repository pattern for queries
        - Structured error handling
        """

        async with async_error_context(
            operation_name="user_authentication", business_operation="login"
        ) as ctx:
            ctx.tags.update({"email": email, "authentication_method": "password"})

            try:
                # Use read-only session for authentication check
                async with enhanced_db_manager.get_session(read_only=True) as session:
                    user_repo = UserRepository(session, User)

                    # Get user by email
                    user = await user_repo.get_by_email(email)

                    if not user:
                        ctx.add_annotation("User not found")
                        return None

                    # Check if user is active
                    if user.status != "active":
                        ctx.add_annotation("User account is not active")
                        return None

                    # Verify password
                    if not self._verify_password(password, user.password_hash):
                        ctx.add_annotation("Password verification failed")
                        return None

                    # Update last login (in separate transaction)
                    try:
                        async with enhanced_db_manager.get_session() as update_session:
                            update_repo = UserRepository(update_session, User)
                            await update_repo.update_last_login(user.id)
                    except Exception as update_error:
                        # Log but don't fail authentication
                        await log_error(
                            update_error, {"user_id": user.id}, ErrorSeverity.LOW
                        )

                    # Generate access token
                    access_token = self._generate_token()

                    # Create session record
                    async with enhanced_db_manager.get_session() as session_db:
                        session_record = UserSession(
                            id=str(uuid.uuid4()),
                            user_id=user.id,
                            access_token=access_token,
                            expires_at=datetime.utcnow()
                            + timedelta(hours=self.token_expiry_hours),
                            ip_address=ctx.tags.get("client_ip"),
                            user_agent=ctx.tags.get("user_agent"),
                            created_at=datetime.utcnow(),
                        )
                        session_db.add(session_record)
                        await session_db.commit()

                    ctx.add_annotation("Authentication successful")

                    return {
                        "user_id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "role": user.role,
                        "access_token": access_token,
                        "expires_at": session_record.expires_at,
                        "full_name": user.full_name,
                    }

            except Exception as e:
                ctx.add_annotation(f"Authentication failed due to error: {str(e)}")
                await log_error(e, ctx.to_dict(), ErrorSeverity.HIGH)
                raise DatabaseError(
                    message="Authentication process failed",
                    operation="authenticate_user",
                    details={"email": email},
                )

    @error_context_decorator("get_user_profile")
    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive user profile

        Demonstrates:
        - Query builder with eager loading
        - Repository pattern
        - Structured data return
        """

        async with enhanced_db_manager.get_session(read_only=True) as session:
            user_repo = UserRepository(session, User)

            # Get user with profile using eager loading
            user = await user_repo.get_user_with_profile(user_id)

            if not user:
                return None

            return {
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name,
                    "role": user.role,
                    "status": user.status,
                    "created_at": user.created_at,
                    "last_login_at": user.last_login_at,
                },
                "profile": {
                    "bio": user.profile.bio if user.profile else "",
                    "avatar_url": user.profile.avatar_url if user.profile else None,
                    "date_of_birth": user.profile.date_of_birth
                    if user.profile
                    else None,
                    "phone_number": user.profile.phone_number if user.profile else None,
                    "address": user.profile.address if user.profile else None,
                }
                if user.profile
                else None,
                "settings": {
                    "theme": user.settings.theme if user.settings else "light",
                    "language": user.settings.language if user.settings else "tr",
                    "notifications_enabled": user.settings.notifications_enabled
                    if user.settings
                    else True,
                    "email_notifications": user.settings.email_notifications
                    if user.settings
                    else True,
                }
                if user.settings
                else None,
            }

    @error_context_decorator("update_user_profile")
    @retryable_transaction(max_attempts=3, delay=1.0)
    async def update_user_profile(
        self,
        user_id: str,
        user_data: Optional[Dict[str, Any]] = None,
        profile_data: Optional[Dict[str, Any]] = None,
        tx_ctx=None,
    ) -> Optional[Dict[str, Any]]:
        """
        Update user and profile data

        Demonstrates:
        - Retryable transaction decorator
        - Partial updates
        - Validation with business rules
        """

        # Get injected transaction context from decorator
        session = tx_ctx.session

        user_repo = UserRepository(session, User)
        profile_repo = UserProfileRepository(session, UserProfile)

        # Get user
        user = await user_repo.get_by_id(user_id)
        if not user:
            raise ErrorFactory.not_found_error("user", user_id, "User not found")

        # Update user data if provided
        if user_data:
            # Validate email uniqueness if changing
            if "email" in user_data and user_data["email"] != user.email:
                existing_user = await user_repo.get_by_email(user_data["email"])
                if existing_user:
                    raise ErrorFactory.business_logic_error(
                        rule_name="unique_email",
                        context={
                            "email": user_data["email"],
                            "current_user_id": user_id,
                        },
                        message="Email address is already in use by another user",
                    )

            # Validate username uniqueness if changing
            if "username" in user_data and user_data["username"] != user.username:
                existing_user = await user_repo.get_by_username(user_data["username"])
                if existing_user:
                    raise ErrorFactory.business_logic_error(
                        rule_name="unique_username",
                        context={
                            "username": user_data["username"],
                            "current_user_id": user_id,
                        },
                        message="Username is already taken by another user",
                    )

            # Update user fields
            await user_repo.update(user, **user_data, updated_at=datetime.utcnow())

        # Update profile data if provided
        if profile_data:
            profile = await profile_repo.get_by_user_id(user_id)
            if profile:
                await profile_repo.update(
                    profile, **profile_data, updated_at=datetime.utcnow()
                )
            else:
                # Create profile if it doesn't exist
                profile = UserProfile(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    **profile_data,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                session.add(profile)

        # Return updated profile
        return await self.get_user_profile(user_id)

    @error_context_decorator("search_users_advanced")
    async def search_users(
        self,
        search_term: str,
        filters: Optional[Dict[str, Any]] = None,
        pagination: Optional[PaginationParams] = None,
    ) -> QueryResult[Dict[str, Any]]:
        """
        Advanced user search with filtering and pagination

        Demonstrates:
        - Complex query building
        - Advanced filtering
        - Pagination with metadata
        """

        async with enhanced_db_manager.get_session(read_only=True) as session:
            user_repo = UserRepository(session, User)

            # Build base search query
            query_builder = user_repo.query().filter(
                or_(
                    username={"operator": "ilike", "value": f"%{search_term}%"},
                    email={"operator": "ilike", "value": f"%{search_term}%"},
                    full_name={"operator": "ilike", "value": f"%{search_term}%"},
                )
            )

            # Apply additional filters
            if filters:
                if "role" in filters:
                    query_builder.filter(role=filters["role"])

                if "status" in filters:
                    query_builder.filter(status=filters["status"])

                if "created_after" in filters:
                    query_builder.filter(
                        created_at={
                            "operator": "gte",
                            "value": filters["created_after"],
                        }
                    )

                if "created_before" in filters:
                    query_builder.filter(
                        created_at={
                            "operator": "lte",
                            "value": filters["created_before"],
                        }
                    )

            # Apply ordering
            query_builder.order_by("username", SortOrder.ASC)

            # Execute with pagination
            pagination = pagination or PaginationParams(page=1, page_size=20)
            result = await query_builder.paginated(pagination)

            # Convert to serializable format
            user_data = []
            for user in result.items:
                user_data.append(
                    {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "full_name": user.full_name,
                        "role": user.role,
                        "status": user.status,
                        "created_at": user.created_at,
                        "last_login_at": user.last_login_at,
                    }
                )

            # Return result with converted data
            return QueryResult.create(
                user_data, result.total_count, pagination, result.query_time_ms
            )

    @error_context_decorator("get_user_statistics")
    async def get_user_statistics(self) -> Dict[str, Any]:
        """Get comprehensive user statistics"""

        async with enhanced_db_manager.get_session(read_only=True) as session:
            user_repo = UserRepository(session, User)
            return await user_repo.get_user_statistics()

    @error_context_decorator("bulk_update_user_status")
    async def bulk_update_user_status(
        self, user_ids: List[str], status: str
    ) -> Dict[str, Any]:
        """
        Bulk update user status

        Demonstrates:
        - Bulk operations
        - Transaction management for batch operations
        - Progress tracking
        """

        if not user_ids:
            return {
                "updated_count": 0,
                "failed_ids": [],
                "message": "No user IDs provided",
            }

        if status not in ["active", "inactive", "suspended"]:
            raise ValidationError("Invalid status value")

        async with managed_transaction() as tx_ctx:
            user_repo = UserRepository(tx_ctx.session, User)

            updated_count = 0
            failed_ids = []

            for user_id in user_ids:
                try:
                    user = await user_repo.get_by_id(user_id)
                    if user:
                        user.status = status
                        user.updated_at = datetime.utcnow()
                        updated_count += 1
                    else:
                        failed_ids.append(user_id)

                except Exception as e:
                    failed_ids.append(user_id)
                    await log_error(
                        e,
                        {"user_id": user_id, "target_status": status},
                        ErrorSeverity.MEDIUM,
                    )

            # Batch flush
            if updated_count > 0:
                await tx_ctx.session.flush()

            return {
                "updated_count": updated_count,
                "failed_ids": failed_ids,
                "total_requested": len(user_ids),
                "success_rate": updated_count / len(user_ids) if user_ids else 0,
            }


# ==================== DEPENDENCY INJECTION ====================


async def get_enhanced_user_service() -> EnhancedUserService:
    """FastAPI dependency for enhanced user service"""
    return EnhancedUserService()


async def get_user_repository(session: AsyncSession) -> UserRepository:
    """FastAPI dependency for user repository"""
    return UserRepository(session, User)


async def get_user_profile_repository(session: AsyncSession) -> UserProfileRepository:
    """FastAPI dependency for user profile repository"""
    return UserProfileRepository(session, UserProfile)


# ==================== SERVICE FACTORY ====================


def create_enhanced_user_service() -> EnhancedUserService:
    """Factory function to create enhanced user service"""
    return EnhancedUserService()
