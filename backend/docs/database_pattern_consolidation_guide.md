# Database Pattern Consolidation Guide

## Overview

This guide documents the comprehensive database pattern consolidation system implemented for the Türkiye Üniversite Sınavları Hazırlık Platformu. The system provides unified database connection management, advanced query building, transaction handling, migration framework, and connection pool optimization.

## 🎯 Key Features

- **Enhanced Database Connection Management**: Advanced connection pooling with health monitoring
- **Type-Safe Query Builder**: Fluent API for building complex queries with type safety
- **Advanced Transaction Management**: Nested transactions, savepoints, and automatic retry logic
- **Database Migration Framework**: Version control for database schema and data changes
- **Connection Pool Optimization**: Intelligent pool sizing and performance optimization
- **Error Handling Integration**: Comprehensive error tracking and recovery mechanisms
- **Performance Monitoring**: Real-time metrics and optimization recommendations

## 📋 System Architecture

### Core Components

#### 1. Enhanced Database Manager
```python
from backend.core.enhanced_database import EnhancedDatabaseManager, ConnectionPoolConfig

# Configure connection pooling
config = ConnectionPoolConfig(
    pool_size=20,
    max_overflow=30,
    pool_timeout=30,
    pool_recycle=3600,
    pool_pre_ping=True
)

# Initialize enhanced database manager
db_manager = EnhancedDatabaseManager(config)
await db_manager.initialize()
```

#### 2. Query Builder System
```python
from backend.core.query_builder import QueryBuilder, ComparisonOperator, SortOrder

# Type-safe query building
async def get_active_users(session):
    query_builder = QueryBuilder(User, session)
    
    results = await query_builder.filter(
        status="active",
        created_at={"operator": "gte", "value": datetime.now() - timedelta(days=30)}
    ).order_by("created_at", SortOrder.DESC).paginate(
        PaginationParams(page=1, page_size=20)
    ).all()
    
    return results
```

#### 3. Transaction Management
```python
from backend.core.transaction_manager import managed_transaction, TransactionConfig

# Managed transactions with automatic retry
async def create_user_with_profile(user_data, profile_data):
    config = TransactionConfig(
        isolation_level=TransactionIsolationLevel.READ_COMMITTED,
        retry_attempts=3,
        enable_savepoints=True
    )
    
    async with managed_transaction(config) as tx_ctx:
        # Create user
        user = User(**user_data)
        tx_ctx.session.add(user)
        await tx_ctx.session.flush()
        
        # Create savepoint
        sp = await tx_ctx.create_savepoint("after_user_creation")
        
        try:
            # Create profile
            profile = UserProfile(user_id=user.id, **profile_data)
            tx_ctx.session.add(profile)
            await tx_ctx.session.flush()
            
        except Exception as e:
            # Rollback to savepoint
            await tx_ctx.rollback_to_savepoint(sp)
            # Create minimal profile instead
            profile = UserProfile(user_id=user.id, name=user_data["username"])
            tx_ctx.session.add(profile)
        
        return user, profile
```

#### 4. Migration Framework
```python
from backend.core.migration_framework import create_migration, apply_pending_migrations

# Create new migration
migration_file = create_migration(
    name="Add user preferences table",
    migration_type=MigrationType.SCHEMA,
    author="developer@example.com"
)

# Apply pending migrations
results = await apply_pending_migrations(executed_by="admin@example.com")
print(f"Applied {len(results['applied_migrations'])} migrations")
```

#### 5. Connection Pool Optimization
```python
from backend.core.connection_pool_optimizer import optimize_pool, OptimizationStrategy

# Optimize connection pool
optimization_result = await optimize_pool(
    pool_id="main_pool",
    current_config=current_config,
    strategy=OptimizationStrategy.BALANCED,
    apply_changes=True
)

if optimization_result["optimized"]:
    print(f"Pool optimized: {optimization_result['recommendation'].reason}")
```

## 🔧 Enhanced Database Sessions

### Basic Session Usage

```python
from backend.core.enhanced_database import enhanced_db_manager

# Basic session with auto-commit
async with enhanced_db_manager.get_session() as session:
    user = await session.get(User, user_id)
    user.last_login = datetime.now()
    # Auto-commit on exit

# Read-only session
async with enhanced_db_manager.get_session(read_only=True) as session:
    users = await session.execute(select(User).where(User.status == "active"))
    return users.scalars().all()

# Custom isolation level
async with enhanced_db_manager.get_session(
    isolation_level="REPEATABLE READ"
) as session:
    # Critical operations requiring consistent reads
    result = await session.execute(complex_query)
```

### Session with Error Handling

```python
from backend.core.enhanced_database import enhanced_db_manager
from backend.core.exceptions import DatabaseError

async def update_user_safely(user_id: str, updates: dict):
    try:
        async with enhanced_db_manager.get_session() as session:
            user = await session.get(User, user_id)
            if not user:
                raise DatabaseError(f"User {user_id} not found")
            
            for key, value in updates.items():
                setattr(user, key, value)
            
            await session.flush()
            return user
            
    except DatabaseError:
        raise
    except Exception as e:
        # Enhanced error handling will wrap this automatically
        raise DatabaseError(
            message="Failed to update user",
            operation="update_user",
            details={"user_id": user_id, "updates": updates}
        )
```

## 🔍 Advanced Query Building

### Basic Query Operations

```python
from backend.core.query_builder import QueryBuilder, ComparisonOperator

async def search_users(session, search_term: str, role: str = None):
    query_builder = QueryBuilder(User, session)
    
    # Add search filter
    query_builder.filter(
        email={"operator": "ilike", "value": f"%{search_term}%", "case_sensitive": False}
    )
    
    # Add role filter if provided
    if role:
        query_builder.filter(role=role)
    
    # Add ordering
    query_builder.order_by("created_at", SortOrder.DESC)
    
    # Execute with pagination
    pagination = PaginationParams(page=1, page_size=20)
    return await query_builder.paginated(pagination)
```

### Complex Queries with Relationships

```python
async def get_user_with_stats(session, user_id: str):
    query_builder = QueryBuilder(User, session)
    
    # Eager load relationships
    results = await query_builder.filter(id=user_id).select_related(
        "profile", "preferences"
    ).prefetch_related(
        "exam_sessions", "learning_progress"
    ).first()
    
    return results

async def get_exam_leaderboard(session, exam_id: str):
    # Complex query with joins and aggregation
    query_builder = QueryBuilder(ExamSession, session)
    
    results = await query_builder.filter(
        exam_id=exam_id,
        status="completed"
    ).join(User, JoinType.INNER).order_by(
        "score", SortOrder.DESC
    ).limit(100).all()
    
    return results
```

### Repository Pattern Implementation

```python
from backend.core.query_builder import BaseRepository

class UserRepository(BaseRepository[User, str]):
    """Enhanced user repository with business logic"""
    
    async def get_active_users_by_role(self, role: str) -> List[User]:
        """Get active users by role"""
        return await self.query().filter(
            status="active",
            role=role
        ).order_by("username").all()
    
    async def search_users(self, 
                          search_term: str,
                          pagination: PaginationParams) -> QueryResult[User]:
        """Search users with pagination"""
        return await self.query().filter(
            username={"operator": "ilike", "value": f"%{search_term}%"}
        ).or_filter(
            email={"operator": "ilike", "value": f"%{search_term}%"}
        ).order_by("username").paginated(pagination)
    
    async def get_user_with_full_profile(self, user_id: str) -> Optional[User]:
        """Get user with all related data"""
        return await self.query().filter(id=user_id).select_related(
            "profile", "preferences", "settings"
        ).prefetch_related(
            "exam_sessions", "learning_progress", "achievements"
        ).first()

# Usage
async with enhanced_db_manager.get_session() as session:
    user_repo = UserRepository(session, User)
    active_students = await user_repo.get_active_users_by_role("student")
```

## 🔄 Advanced Transaction Management

### Nested Transactions with Savepoints

```python
from backend.core.transaction_manager import managed_transaction, TransactionConfig

async def complex_user_operation(user_data, additional_data):
    config = TransactionConfig(
        isolation_level=TransactionIsolationLevel.REPEATABLE_READ,
        enable_savepoints=True,
        timeout_seconds=300
    )
    
    async with managed_transaction(config) as tx_ctx:
        # Step 1: Create user
        user = User(**user_data)
        tx_ctx.session.add(user)
        await tx_ctx.session.flush()
        
        sp1 = await tx_ctx.create_savepoint("user_created")
        
        try:
            # Step 2: Create profile
            profile = UserProfile(user_id=user.id, **additional_data["profile"])
            tx_ctx.session.add(profile)
            await tx_ctx.session.flush()
            
            sp2 = await tx_ctx.create_savepoint("profile_created")
            
            try:
                # Step 3: Send welcome email
                await send_welcome_email(user.email)
                
                # Step 4: Create initial settings
                settings = UserSettings(user_id=user.id, **additional_data["settings"])
                tx_ctx.session.add(settings)
                
            except EmailError:
                # Email failed, rollback to after profile creation
                await tx_ctx.rollback_to_savepoint(sp2)
                # Continue without email
                
        except ValidationError:
            # Profile creation failed, rollback to after user creation
            await tx_ctx.rollback_to_savepoint(sp1)
            # Create minimal profile
            minimal_profile = UserProfile(user_id=user.id, name=user.username)
            tx_ctx.session.add(minimal_profile)
        
        return user
```

### Transaction Retry with Automatic Recovery

```python
from backend.core.transaction_manager import execute_with_transaction_retry

async def update_user_score(user_id: str, score_delta: int):
    """Update user score with automatic retry on conflicts"""
    
    async def score_update_operation(tx_ctx):
        user = await tx_ctx.session.get(User, user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        # This might conflict with concurrent updates
        user.total_score += score_delta
        user.updated_at = datetime.now()
        
        # Flush to detect conflicts early
        await tx_ctx.session.flush()
        
        return user.total_score
    
    config = TransactionConfig(
        retry_attempts=5,
        retry_delay=0.5,
        enable_deadlock_retry=True
    )
    
    return await execute_with_transaction_retry(score_update_operation, config)
```

### Transaction Decorators

```python
from backend.core.transaction_manager import transactional, retryable_transaction

@retryable_transaction(max_attempts=3, delay=1.0)
async def create_exam_session(user_id: str, exam_id: str):
    """Create exam session with automatic retry"""
    # This function will automatically run in a retryable transaction
    session = get_current_session()  # Injected by decorator
    
    exam_session = ExamSession(
        user_id=user_id,
        exam_id=exam_id,
        started_at=datetime.now()
    )
    session.add(exam_session)
    return exam_session

@transactional()
async def batch_update_user_progress(updates: List[Dict]):
    """Batch update user progress in a transaction"""
    session = get_current_session()  # Injected by decorator
    
    for update in updates:
        user_id = update["user_id"]
        progress = await session.get(UserProgress, user_id)
        if progress:
            for key, value in update["data"].items():
                setattr(progress, key, value)
```

## 📈 Database Migration Management

### Creating Migrations

```python
from backend.core.migration_framework import create_migration, MigrationType

# Create schema migration
schema_migration = create_migration(
    name="Add user preferences table",
    migration_type=MigrationType.SCHEMA,
    author="developer@example.com"
)

# Create data migration
data_migration = create_migration(
    name="Migrate old user settings",
    migration_type=MigrationType.DATA,
    author="developer@example.com"
)
```

### Custom Migration Implementation

```python
from backend.core.migration_framework import BaseMigration, MigrationInfo
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

class Migration_20240101_120000_add_user_preferences(BaseMigration):
    """Add user preferences table with default values"""
    
    def __init__(self):
        info = MigrationInfo(
            id="20240101_120000_add_user_preferences",
            name="Add user preferences table",
            description="Add comprehensive user preferences system",
            version="1.0.0",
            migration_type=MigrationType.MIXED,
            dependencies=["20231215_100000_update_user_table"],
            author="developer@example.com",
            tags=["preferences", "user_system"]
        )
        super().__init__(info)
    
    async def up(self, session: AsyncSession) -> None:
        """Create preferences table and populate defaults"""
        
        # Create table
        await session.execute(text("""
            CREATE TABLE user_preferences (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(255) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                theme VARCHAR(50) DEFAULT 'light',
                language VARCHAR(10) DEFAULT 'tr',
                notifications_enabled BOOLEAN DEFAULT true,
                email_notifications BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id)
            )
        """))
        
        # Create indexes
        await session.execute(text("""
            CREATE INDEX idx_user_preferences_user_id ON user_preferences(user_id)
        """))
        
        # Populate defaults for existing users
        await session.execute(text("""
            INSERT INTO user_preferences (user_id, theme, language)
            SELECT id, 'light', 'tr' FROM users
            WHERE id NOT IN (SELECT user_id FROM user_preferences)
        """))
    
    async def down(self, session: AsyncSession) -> None:
        """Remove preferences table"""
        await session.execute(text("DROP TABLE IF EXISTS user_preferences"))
    
    async def validate_preconditions(self, session: AsyncSession) -> List[str]:
        """Validate that users table exists"""
        result = await session.execute(text("""
            SELECT 1 FROM information_schema.tables 
            WHERE table_name = 'users'
        """))
        
        if not result.fetchone():
            return ["Users table does not exist"]
        
        return []
    
    async def validate_postconditions(self, session: AsyncSession) -> List[str]:
        """Validate that preferences table was created correctly"""
        errors = []
        
        # Check table exists
        result = await session.execute(text("""
            SELECT 1 FROM information_schema.tables 
            WHERE table_name = 'user_preferences'
        """))
        
        if not result.fetchone():
            errors.append("user_preferences table was not created")
        
        # Check all users have preferences
        result = await session.execute(text("""
            SELECT COUNT(*) as missing_count FROM users u
            LEFT JOIN user_preferences up ON u.id = up.user_id
            WHERE up.user_id IS NULL
        """))
        
        missing_count = result.scalar()
        if missing_count > 0:
            errors.append(f"{missing_count} users missing preferences")
        
        return errors

# Register migration
from backend.core.migration_framework import migration_manager
migration_manager.register_migration(Migration_20240101_120000_add_user_preferences())
```

### Migration Management Operations

```python
from backend.core.migration_framework import (
    initialize_migrations, apply_pending_migrations,
    get_migration_status, migration_manager
)

# Initialize migration system
await initialize_migrations("backend/migrations")

# Check migration status
status = await get_migration_status()
print(f"Pending migrations: {len(status['migration_details']['pending'])}")

# Apply specific migration
await migration_manager.apply_migration(
    "20240101_120000_add_user_preferences",
    executed_by="admin@example.com"
)

# Apply all pending migrations
results = await apply_pending_migrations(executed_by="admin@example.com")

# Rollback migration if needed
await migration_manager.rollback_migration(
    "20240101_120000_add_user_preferences",
    reason="Found critical bug in preferences logic",
    executed_by="admin@example.com"
)
```

## 🔧 Connection Pool Optimization

### Automatic Pool Optimization

```python
from backend.core.connection_pool_optimizer import (
    optimize_pool, OptimizationStrategy, track_pool_metrics, 
    get_pool_health, PoolMetrics
)

# Configure optimization strategy
strategy = OptimizationStrategy.BALANCED  # or CONSERVATIVE, AGGRESSIVE

# Get current pool metrics
current_metrics = PoolMetrics(
    pool_id="main_pool",
    timestamp=datetime.now(),
    pool_size=20,
    checked_out=15,
    checked_in=5,
    overflow=3,
    invalid=0,
    avg_checkout_time=0.05,
    checkout_timeouts=2,
    connection_errors=0,
    utilization_ratio=0.75
)

# Track metrics for optimization
track_pool_metrics("main_pool", current_metrics)

# Check pool health
health_status, issues = get_pool_health("main_pool")
if health_status != PoolHealthStatus.HEALTHY:
    print(f"Pool health issues: {', '.join(issues)}")

# Optimize pool configuration
optimization_result = await optimize_pool(
    pool_id="main_pool",
    current_config=current_config,
    strategy=strategy,
    apply_changes=True  # Apply recommendations automatically
)

if optimization_result["optimized"]:
    recommendation = optimization_result["recommendation"]
    print(f"Pool optimized: {recommendation.reason}")
    print(f"Confidence: {recommendation.confidence_score:.2f}")
    print(f"Risk level: {recommendation.risk_level}")
```

### Manual Pool Tuning

```python
from backend.core.enhanced_database import ConnectionPoolConfig

# Create optimized configuration based on load patterns
high_load_config = ConnectionPoolConfig(
    pool_size=50,           # Larger pool for high concurrency
    max_overflow=75,        # Allow significant overflow
    pool_timeout=45,        # Longer timeout for high load
    pool_recycle=7200,      # 2 hour recycle time
    pool_pre_ping=True,     # Enable connection validation
    pool_reset_on_return='commit'  # Clean state on return
)

# Low latency configuration
low_latency_config = ConnectionPoolConfig(
    pool_size=15,           # Smaller pool for faster access
    max_overflow=10,        # Limited overflow
    pool_timeout=5,         # Quick timeout for fast fail
    pool_recycle=1800,      # 30 minute recycle time
    pool_pre_ping=True,     # Validate connections
    pool_reset_on_return='rollback'  # Fast reset
)

# Apply configuration
db_manager = EnhancedDatabaseManager(high_load_config)
await db_manager.initialize()
```

## 📊 Performance Monitoring

### Database Metrics Collection

```python
from backend.core.enhanced_database import enhanced_db_manager

# Get comprehensive health status
health_status = await enhanced_db_manager.health_check()

print(f"Database Status: {health_status['status']}")
print(f"Total Queries: {health_status['metrics']['queries_executed']}")
print(f"Average Query Time: {health_status['metrics']['average_query_time']:.3f}s")
print(f"Connection Pool Status: {health_status['pool_status']}")

# Get optimization statistics
from backend.core.connection_pool_optimizer import get_optimization_statistics

opt_stats = get_optimization_statistics()
print(f"Optimization Recommendations: {opt_stats['total_recommendations']}")
print(f"Average Confidence: {opt_stats['average_confidence']:.2f}")
```

### Query Performance Analysis

```python
from backend.core.query_builder import QueryOptimizer

# Analyze query performance
query_builder = QueryBuilder(User, session).filter(
    status="active"
).join(UserProfile).order_by("created_at", SortOrder.DESC)

# Get performance analysis
analysis = QueryOptimizer.analyze_query_performance(query_builder)
print(f"Query Complexity: {analysis['estimated_complexity']}")
print(f"Join Count: {analysis['join_count']}")
print(f"Filter Count: {analysis['filter_count']}")

# Get optimization suggestions
suggestions = QueryOptimizer.suggest_optimizations(query_builder)
for suggestion in suggestions:
    print(f"💡 {suggestion}")

# View generated SQL for debugging
sql = query_builder.to_sql()
print(f"Generated SQL: {sql}")
```

## 🛠️ FastAPI Integration

### Enhanced Database Dependencies

```python
from fastapi import Depends
from backend.core.enhanced_database import get_enhanced_db_dependency
from backend.core.transaction_manager import managed_transaction
from backend.core.query_builder import create_repository

# Basic database dependency
async def get_db_session():
    async with get_enhanced_db_dependency() as session:
        yield session

# Read-only dependency
async def get_readonly_db_session():
    async with get_enhanced_db_dependency(read_only=True) as session:
        yield session

# Repository dependency
async def get_user_repository(session: AsyncSession = Depends(get_db_session)):
    return create_repository(User, session)

# API endpoint with enhanced database handling
@router.post("/users", response_model=SuccessResponse[UserResponse])
async def create_user_enhanced(
    user_data: UserCreate,
    user_repo: UserRepository = Depends(get_user_repository)
):
    """Create user with enhanced database patterns"""
    
    # Use repository for business logic
    existing_user = await user_repo.query().filter(email=user_data.email).first()
    if existing_user:
        raise ValidationError("Email already exists")
    
    # Create user with transaction management
    async with managed_transaction() as tx_ctx:
        # Create user
        user = await user_repo.create(
            username=user_data.username,
            email=user_data.email,
            password_hash=hash_password(user_data.password)
        )
        
        # Create profile with savepoint
        sp = await tx_ctx.create_savepoint("user_created")
        
        try:
            profile = UserProfile(
                user_id=user.id,
                name=user_data.full_name or user_data.username
            )
            tx_ctx.session.add(profile)
            await tx_ctx.session.flush()
            
        except Exception as e:
            await tx_ctx.rollback_to_savepoint(sp)
            # Create minimal profile
            profile = UserProfile(user_id=user.id, name=user.username)
            tx_ctx.session.add(profile)
        
        return SuccessResponse(
            data=UserResponse.from_orm(user),
            message="User created successfully"
        )
```

## 🧪 Testing Database Patterns

### Unit Testing with Transactions

```python
import pytest
from backend.core.enhanced_database import enhanced_db_manager
from backend.core.transaction_manager import managed_transaction

@pytest.mark.asyncio
async def test_user_creation_with_transaction():
    """Test user creation with transaction rollback on test completion"""
    
    async with managed_transaction() as tx_ctx:
        # Create test user
        user = User(username="testuser", email="test@example.com")
        tx_ctx.session.add(user)
        await tx_ctx.session.flush()
        
        # Verify creation
        assert user.id is not None
        
        # Create profile
        profile = UserProfile(user_id=user.id, name="Test User")
        tx_ctx.session.add(profile)
        await tx_ctx.session.flush()
        
        # Test business logic
        assert profile.user_id == user.id
        
        # Transaction will auto-rollback due to test teardown
        raise Exception("Trigger rollback for test cleanup")

@pytest.mark.asyncio
async def test_query_builder_functionality():
    """Test query builder with mock data"""
    
    async with enhanced_db_manager.get_session() as session:
        # Create test data
        users = [
            User(username=f"user{i}", email=f"user{i}@test.com", status="active")
            for i in range(5)
        ]
        
        for user in users:
            session.add(user)
        await session.flush()
        
        # Test query builder
        query_builder = QueryBuilder(User, session)
        
        # Test filtering
        active_users = await query_builder.filter(status="active").all()
        assert len(active_users) == 5
        
        # Test pagination
        pagination = PaginationParams(page=1, page_size=3)
        paginated_result = await query_builder.paginated(pagination)
        
        assert len(paginated_result.items) == 3
        assert paginated_result.total_count == 5
        assert paginated_result.has_next is True
        
        # Cleanup
        for user in users:
            await session.delete(user)
```

### Integration Testing

```python
@pytest.mark.asyncio
async def test_migration_system():
    """Test migration system functionality"""
    
    from backend.core.migration_framework import migration_manager
    
    # Test migration creation
    migration_file = migration_manager.generate_migration_file(
        name="test_migration",
        migration_type=MigrationType.SCHEMA
    )
    
    assert Path(migration_file).exists()
    
    # Test migration status
    status = await migration_manager.get_migration_status()
    assert "total_migrations" in status
    
    # Clean up
    Path(migration_file).unlink()

@pytest.mark.asyncio
async def test_connection_pool_optimization():
    """Test connection pool optimization"""
    
    from backend.core.connection_pool_optimizer import optimize_pool
    from backend.core.enhanced_database import ConnectionPoolConfig
    
    current_config = ConnectionPoolConfig(
        pool_size=10,
        max_overflow=20,
        pool_timeout=30
    )
    
    # Test optimization analysis
    result = await optimize_pool(
        pool_id="test_pool",
        current_config=current_config,
        apply_changes=False
    )
    
    assert "optimized" in result
    assert "current_config" in result
```

## 📚 Best Practices

### 1. Connection Management
```python
# ✅ Good - Use enhanced session management
async with enhanced_db_manager.get_session() as session:
    result = await session.execute(query)
    return result.scalars().all()

# ❌ Bad - Manual session management
session = async_session_maker()
try:
    result = await session.execute(query)
    await session.commit()
    return result.scalars().all()
finally:
    await session.close()
```

### 2. Query Building
```python
# ✅ Good - Use type-safe query builder
results = await QueryBuilder(User, session).filter(
    status="active",
    created_at={"operator": "gte", "value": cutoff_date}
).order_by("created_at", SortOrder.DESC).limit(100).all()

# ❌ Bad - Raw SQL strings
results = await session.execute(text(
    "SELECT * FROM users WHERE status = 'active' AND created_at >= :cutoff ORDER BY created_at DESC LIMIT 100"
), {"cutoff": cutoff_date})
```

### 3. Transaction Handling
```python
# ✅ Good - Use managed transactions
async with managed_transaction() as tx_ctx:
    user = await create_user(user_data, tx_ctx.session)
    profile = await create_profile(user.id, profile_data, tx_ctx.session)
    return user, profile

# ❌ Bad - Manual transaction management
async with session.begin() as transaction:
    try:
        user = await create_user(user_data, session)
        profile = await create_profile(user.id, profile_data, session)
        await transaction.commit()
        return user, profile
    except Exception:
        await transaction.rollback()
        raise
```

### 4. Error Handling
```python
# ✅ Good - Use structured error handling
try:
    result = await database_operation()
except DatabaseError as e:
    logger.error(f"Database operation failed: {e}")
    raise
except Exception as e:
    raise DatabaseError(
        message="Unexpected database error",
        operation="database_operation",
        details={"error": str(e)}
    )

# ❌ Bad - Generic error handling
try:
    result = await database_operation()
except Exception as e:
    print(f"Something went wrong: {e}")
    raise
```

## 🔧 Configuration

### Environment Variables
```bash
# Enhanced database configuration
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600
DB_POOL_PRE_PING=true
DB_POOL_RESET_ON_RETURN=commit

# Optimization settings
DB_OPTIMIZATION_STRATEGY=balanced
DB_AUTO_OPTIMIZE=true
DB_OPTIMIZATION_INTERVAL=300

# Migration settings
MIGRATION_DIRECTORY=backend/migrations
AUTO_APPLY_MIGRATIONS=false
```

### Application Configuration
```python
from backend.core.enhanced_database import ConnectionPoolConfig, EnhancedDatabaseManager
from backend.core.connection_pool_optimizer import OptimizationStrategy

# Production configuration
production_config = ConnectionPoolConfig(
    pool_size=50,
    max_overflow=100,
    pool_timeout=60,
    pool_recycle=7200,
    pool_pre_ping=True,
    pool_reset_on_return='commit',
    echo=False,
    echo_pool=False
)

# Development configuration
development_config = ConnectionPoolConfig(
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=3600,
    pool_pre_ping=True,
    pool_reset_on_return='rollback',
    echo=True,
    echo_pool=False
)

# Initialize based on environment
config = production_config if is_production else development_config
db_manager = EnhancedDatabaseManager(config)
```

## 📈 Monitoring and Maintenance

### Health Monitoring
```python
# Regular health checks
async def monitor_database_health():
    health = await enhanced_db_manager.health_check()
    
    if not health["healthy"]:
        # Send alerts
        await send_alert(f"Database unhealthy: {health.get('error', 'Unknown error')}")
    
    # Log metrics
    metrics = health["metrics"]
    logger.info(f"DB Metrics - Queries: {metrics['queries_executed']}, "
                f"Avg Time: {metrics['average_query_time']:.3f}s, "
                f"Pool Size: {health['pool_status']['pool_size']}")

# Connection leak detection
async def detect_and_report_leaks():
    leaks = await detect_connection_leaks()
    if leaks:
        logger.warning(f"Detected {len(leaks)} potential connection leaks: {leaks}")
        # Take corrective action
```

### Performance Optimization
```python
# Automated optimization
async def optimize_database_performance():
    # Get current configuration
    current_config = enhanced_db_manager.config
    
    # Analyze and optimize
    optimization_result = await optimize_pool(
        pool_id="main_pool",
        current_config=current_config,
        strategy=OptimizationStrategy.BALANCED,
        apply_changes=True
    )
    
    if optimization_result["optimized"]:
        logger.info(f"Database optimized: {optimization_result['recommendation'].reason}")

# Schedule optimization checks
import asyncio

async def scheduled_maintenance():
    while True:
        try:
            await monitor_database_health()
            await detect_and_report_leaks()
            await optimize_database_performance()
            
            # Wait 5 minutes
            await asyncio.sleep(300)
        except Exception as e:
            logger.error(f"Maintenance task failed: {e}")
            await asyncio.sleep(60)  # Wait 1 minute on error

# Start maintenance task
asyncio.create_task(scheduled_maintenance())
```

## 📚 Additional Resources

- [Enhanced Database Manager](../core/enhanced_database.py)
- [Query Builder System](../core/query_builder.py)
- [Transaction Manager](../core/transaction_manager.py)
- [Migration Framework](../core/migration_framework.py)
- [Connection Pool Optimizer](../core/connection_pool_optimizer.py)
- [Integration Examples](../examples/database_integration_examples.py)

---

This comprehensive database pattern consolidation provides a robust foundation for scalable, maintainable, and high-performance database operations in the Türkiye Üniversite Sınavları Hazırlık Platformu.