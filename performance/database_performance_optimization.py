"""
KIRO2 Database Performance Optimization Engine
Advanced database performance optimization for Turkish exam preparation platform
Türkiye Üniversite Sınavları Hazırlık Platformu - Veritabanı Performans Optimizasyon Motoru
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Union, Callable, Tuple
from enum import Enum
import json
import uuid
import sqlite3
import asyncpg
import aiomysql
import aioredis
from pathlib import Path
import hashlib
import statistics
import math
from collections import defaultdict, deque
import psutil
import time
import re
from functools import wraps

from backend.core.structured_logging import get_logger, LogCategory
from backend.core.unified_config import get_unified_config

logger = get_logger(__name__, LogCategory.PERFORMANCE)
config = get_unified_config()


class DatabaseType(Enum):
    """Supported database types"""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLITE = "sqlite"
    MONGODB = "mongodb"
    REDIS = "redis"
    ELASTICSEARCH = "elasticsearch"


class QueryType(Enum):
    """SQL query types"""
    SELECT = "select"
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    BULK_INSERT = "bulk_insert"
    BULK_UPDATE = "bulk_update"
    ANALYTICAL = "analytical"
    EXAM_SPECIFIC = "exam_specific"  # Turkish exam queries


class OptimizationType(Enum):
    """Database optimization types"""
    INDEX_OPTIMIZATION = "index_optimization"
    QUERY_REWRITE = "query_rewrite"
    PARTITION_STRATEGY = "partition_strategy"
    CONNECTION_POOLING = "connection_pooling"
    CACHING_LAYER = "caching_layer"
    READ_REPLICA = "read_replica"
    MATERIALIZED_VIEW = "materialized_view"
    EXAM_DATA_OPTIMIZATION = "exam_data_optimization"


class PerformanceIssue(Enum):
    """Performance issue types"""
    SLOW_QUERY = "slow_query"
    HIGH_CPU = "high_cpu"
    HIGH_MEMORY = "high_memory"
    LOCK_CONTENTION = "lock_contention"
    CONNECTION_EXHAUSTION = "connection_exhaustion"
    INDEX_MISSING = "index_missing"
    FULL_TABLE_SCAN = "full_table_scan"
    EXAM_TRAFFIC_SPIKE = "exam_traffic_spike"


@dataclass
class QueryPerformanceMetrics:
    """Query performance metrics"""
    query_id: str
    query_hash: str
    query_text: str
    query_type: QueryType
    
    # Execution metrics
    execution_count: int = 0
    total_execution_time: float = 0.0
    average_execution_time: float = 0.0
    min_execution_time: float = float('inf')
    max_execution_time: float = 0.0
    
    # Resource usage
    cpu_usage: float = 0.0
    memory_usage: int = 0  # bytes
    io_reads: int = 0
    io_writes: int = 0
    
    # Query plan metrics
    estimated_cost: float = 0.0
    actual_rows: int = 0
    estimated_rows: int = 0
    
    # Optimization opportunities
    missing_indexes: List[str] = field(default_factory=list)
    suggested_indexes: List[str] = field(default_factory=list)
    optimization_recommendations: List[str] = field(default_factory=list)
    
    # Turkish exam specific
    exam_related: bool = False
    subject_area: Optional[str] = None
    peak_usage_during_exams: bool = False
    
    # Timestamps
    first_seen: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_seen: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def update_metrics(self, execution_time: float, rows_affected: int = 0) -> None:
        """Update performance metrics with new execution"""
        self.execution_count += 1
        self.total_execution_time += execution_time
        self.average_execution_time = self.total_execution_time / self.execution_count
        
        self.min_execution_time = min(self.min_execution_time, execution_time)
        self.max_execution_time = max(self.max_execution_time, execution_time)
        
        self.actual_rows = rows_affected
        self.last_seen = datetime.now(timezone.utc)
    
    def is_slow_query(self, threshold: float = 1.0) -> bool:
        """Check if query is considered slow"""
        return self.average_execution_time > threshold
    
    def get_performance_score(self) -> float:
        """Calculate performance score (0-100, higher is better)"""
        base_score = 100.0
        
        # Penalize slow execution
        if self.average_execution_time > 1.0:
            base_score -= min(self.average_execution_time * 10, 50)
        
        # Penalize high resource usage
        if self.cpu_usage > 50.0:
            base_score -= (self.cpu_usage - 50) * 0.5
        
        # Penalize missing indexes
        base_score -= len(self.missing_indexes) * 5
        
        # Bonus for optimizations
        base_score += len(self.optimization_recommendations) * 2
        
        return max(0.0, min(base_score, 100.0))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "query_id": self.query_id,
            "query_hash": self.query_hash,
            "query_text": self.query_text,
            "query_type": self.query_type.value,
            "execution_metrics": {
                "count": self.execution_count,
                "total_time": self.total_execution_time,
                "average_time": self.average_execution_time,
                "min_time": self.min_execution_time,
                "max_time": self.max_execution_time
            },
            "resource_usage": {
                "cpu_usage": self.cpu_usage,
                "memory_usage": self.memory_usage,
                "io_reads": self.io_reads,
                "io_writes": self.io_writes
            },
            "optimization": {
                "missing_indexes": self.missing_indexes,
                "suggested_indexes": self.suggested_indexes,
                "recommendations": self.optimization_recommendations,
                "performance_score": self.get_performance_score()
            },
            "exam_context": {
                "exam_related": self.exam_related,
                "subject_area": self.subject_area,
                "peak_usage": self.peak_usage_during_exams
            },
            "timestamps": {
                "first_seen": self.first_seen.isoformat(),
                "last_seen": self.last_seen.isoformat()
            }
        }


@dataclass
class DatabaseConnection:
    """Database connection configuration"""
    connection_id: str
    database_type: DatabaseType
    host: str
    port: int
    database: str
    username: str
    
    # Connection pool settings
    min_pool_size: int = 5
    max_pool_size: int = 50
    pool_timeout: int = 30
    idle_timeout: int = 300
    
    # Performance settings
    query_timeout: int = 30
    connection_timeout: int = 10
    statement_timeout: int = 60
    
    # Turkish exam specific settings
    exam_mode_pool_size: int = 100  # Increased pool during exams
    exam_query_timeout: int = 10    # Faster timeout during exams
    
    # Current status
    active_connections: int = 0
    idle_connections: int = 0
    total_connections: int = 0
    
    # Performance metrics
    connection_attempts: int = 0
    successful_connections: int = 0
    failed_connections: int = 0
    average_connection_time: float = 0.0
    
    def __post_init__(self):
        if not self.connection_id:
            self.connection_id = str(uuid.uuid4())
    
    def get_connection_string(self) -> str:
        """Get database connection string"""
        if self.database_type == DatabaseType.POSTGRESQL:
            return f"postgresql://{self.username}@{self.host}:{self.port}/{self.database}"
        elif self.database_type == DatabaseType.MYSQL:
            return f"mysql://{self.username}@{self.host}:{self.port}/{self.database}"
        elif self.database_type == DatabaseType.SQLITE:
            return f"sqlite:///{self.database}"
        else:
            return f"{self.database_type.value}://{self.host}:{self.port}/{self.database}"
    
    def is_healthy(self) -> bool:
        """Check if connection is healthy"""
        connection_success_rate = (
            self.successful_connections / max(self.connection_attempts, 1)
        ) * 100
        
        return (
            connection_success_rate > 95.0 and
            self.active_connections < self.max_pool_size * 0.9 and
            self.average_connection_time < 5.0
        )


class QueryOptimizer:
    """Advanced query optimization engine"""
    
    def __init__(self):
        self.optimization_rules: List[Callable] = []
        self.index_recommendations: Dict[str, List[str]] = defaultdict(list)
        self.query_patterns: Dict[str, str] = {}
        
        self._load_optimization_rules()
        self._load_turkish_exam_patterns()
    
    def _load_optimization_rules(self) -> None:
        """Load SQL optimization rules"""
        self.optimization_rules = [
            self._optimize_select_star,
            self._optimize_missing_where_clause,
            self._optimize_function_in_where,
            self._optimize_join_conditions,
            self._optimize_subqueries,
            self._optimize_union_vs_union_all,
            self._optimize_exam_queries
        ]
    
    def _load_turkish_exam_patterns(self) -> None:
        """Load Turkish exam-specific query patterns"""
        self.query_patterns = {
            "student_exam_results": """
                SELECT s.student_id, s.name, er.exam_type, er.score, er.subject_scores
                FROM students s
                JOIN exam_results er ON s.student_id = er.student_id
                WHERE er.exam_type IN ('TYT', 'AYT', 'YKS')
                AND er.exam_date >= $1
            """,
            "subject_performance": """
                SELECT subject, AVG(score) as avg_score, COUNT(*) as student_count
                FROM exam_results
                WHERE exam_type = $1 AND exam_date BETWEEN $2 AND $3
                GROUP BY subject
                ORDER BY avg_score DESC
            """,
            "university_rankings": """
                SELECT u.university_name, u.department, MIN(er.score) as min_score
                FROM universities u
                JOIN exam_results er ON u.min_score <= er.score
                WHERE er.exam_type = 'YKS'
                GROUP BY u.university_name, u.department
                ORDER BY min_score DESC
            """
        }
    
    async def optimize_query(self, query_text: str, query_metrics: QueryPerformanceMetrics) -> Dict[str, Any]:
        """Optimize SQL query and provide recommendations"""
        optimization_result = {
            "original_query": query_text,
            "optimized_query": query_text,
            "recommendations": [],
            "index_suggestions": [],
            "estimated_improvement": 0.0,
            "complexity_reduction": 0.0
        }
        
        try:
            # Apply optimization rules
            optimized_query = query_text
            for rule in self.optimization_rules:
                rule_result = await rule(optimized_query, query_metrics)
                if rule_result["modified"]:
                    optimized_query = rule_result["query"]
                    optimization_result["recommendations"].extend(rule_result["recommendations"])
            
            optimization_result["optimized_query"] = optimized_query
            
            # Generate index suggestions
            index_suggestions = await self._generate_index_suggestions(query_text, query_metrics)
            optimization_result["index_suggestions"] = index_suggestions
            
            # Calculate estimated improvement
            improvement = await self._estimate_performance_improvement(
                query_text, optimized_query, query_metrics
            )
            optimization_result["estimated_improvement"] = improvement
            
            return optimization_result
            
        except Exception as e:
            logger.error(f"Query optimization failed: {e}")
            optimization_result["error"] = str(e)
            return optimization_result
    
    async def _optimize_select_star(self, query: str, metrics: QueryPerformanceMetrics) -> Dict[str, Any]:
        """Optimize SELECT * queries"""
        result = {"modified": False, "query": query, "recommendations": []}
        
        if re.search(r'\bSELECT\s+\*\s+FROM\b', query, re.IGNORECASE):
            result["recommendations"].append(
                "Consider specifying only the columns you need instead of SELECT *"
            )
            
            # For exam-related queries, suggest specific columns
            if metrics.exam_related:
                if "exam_results" in query.lower():
                    suggested_columns = "student_id, exam_type, score, subject_scores, exam_date"
                    optimized_query = re.sub(
                        r'\bSELECT\s+\*\s+FROM\b',
                        f'SELECT {suggested_columns} FROM',
                        query,
                        flags=re.IGNORECASE
                    )
                    result["query"] = optimized_query
                    result["modified"] = True
                    result["recommendations"].append(
                        f"Replaced SELECT * with specific exam-related columns: {suggested_columns}"
                    )
        
        return result
    
    async def _optimize_missing_where_clause(self, query: str, metrics: QueryPerformanceMetrics) -> Dict[str, Any]:
        """Detect and optimize queries without WHERE clauses"""
        result = {"modified": False, "query": query, "recommendations": []}
        
        # Check for SELECT without WHERE
        if (re.search(r'\bSELECT\b.*\bFROM\b', query, re.IGNORECASE) and 
            not re.search(r'\bWHERE\b', query, re.IGNORECASE)):
            
            result["recommendations"].append(
                "Query lacks WHERE clause - may result in full table scan"
            )
            
            # For exam queries, suggest date filtering
            if metrics.exam_related and "exam_results" in query.lower():
                result["recommendations"].append(
                    "Consider adding date filtering: WHERE exam_date >= CURRENT_DATE - INTERVAL '1 year'"
                )
        
        return result
    
    async def _optimize_function_in_where(self, query: str, metrics: QueryPerformanceMetrics) -> Dict[str, Any]:
        """Optimize functions in WHERE clause"""
        result = {"modified": False, "query": query, "recommendations": []}
        
        # Detect functions on columns in WHERE clause
        function_patterns = [
            r'\bWHERE\s+\w+\([^)]*\w+\.[^)]*\)',
            r'\bWHERE\s+UPPER\(\w+\)',
            r'\bWHERE\s+LOWER\(\w+\)',
            r'\bWHERE\s+SUBSTR\(\w+',
        ]
        
        for pattern in function_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                result["recommendations"].append(
                    "Functions in WHERE clause prevent index usage - consider functional indexes or query rewrite"
                )
                break
        
        return result
    
    async def _optimize_join_conditions(self, query: str, metrics: QueryPerformanceMetrics) -> Dict[str, Any]:
        """Optimize JOIN conditions"""
        result = {"modified": False, "query": query, "recommendations": []}
        
        # Check for CROSS JOINs or missing JOIN conditions
        if re.search(r'\bCROSS\s+JOIN\b', query, re.IGNORECASE):
            result["recommendations"].append(
                "CROSS JOIN detected - ensure this is intentional as it creates cartesian product"
            )
        
        # Check for implicit joins (comma-separated tables without proper WHERE conditions)
        join_count = len(re.findall(r'\bJOIN\b', query, re.IGNORECASE))
        from_tables = len(re.findall(r',\s*\w+', query)) + 1
        
        if from_tables > 1 and join_count == 0:
            result["recommendations"].append(
                "Consider using explicit JOIN syntax instead of comma-separated tables"
            )
        
        return result
    
    async def _optimize_subqueries(self, query: str, metrics: QueryPerformanceMetrics) -> Dict[str, Any]:
        """Optimize subqueries"""
        result = {"modified": False, "query": query, "recommendations": []}
        
        # Detect correlated subqueries
        if re.search(r'\bEXISTS\s*\(', query, re.IGNORECASE):
            result["recommendations"].append(
                "EXISTS subquery detected - consider if it can be rewritten as a JOIN"
            )
        
        # Detect IN subqueries
        if re.search(r'\bIN\s*\(\s*SELECT\b', query, re.IGNORECASE):
            result["recommendations"].append(
                "IN subquery detected - consider rewriting as EXISTS or JOIN for better performance"
            )
        
        return result
    
    async def _optimize_union_vs_union_all(self, query: str, metrics: QueryPerformanceMetrics) -> Dict[str, Any]:
        """Optimize UNION vs UNION ALL"""
        result = {"modified": False, "query": query, "recommendations": []}
        
        if re.search(r'\bUNION\b(?!\s+ALL)', query, re.IGNORECASE):
            result["recommendations"].append(
                "UNION removes duplicates - use UNION ALL if duplicates are acceptable for better performance"
            )
        
        return result
    
    async def _optimize_exam_queries(self, query: str, metrics: QueryPerformanceMetrics) -> Dict[str, Any]:
        """Optimize Turkish exam-specific queries"""
        result = {"modified": False, "query": query, "recommendations": []}
        
        if not metrics.exam_related:
            return result
        
        # Optimize exam result queries
        if "exam_results" in query.lower():
            # Suggest partitioning by exam_date
            result["recommendations"].append(
                "Consider partitioning exam_results table by exam_date for better performance"
            )
            
            # Suggest specific indexes for Turkish exams
            result["recommendations"].append(
                "Create indexes on (exam_type, exam_date) and (student_id, exam_type) for Turkish exam queries"
            )
        
        # Optimize university ranking queries
        if "university" in query.lower() and "ranking" in query.lower():
            result["recommendations"].append(
                "Consider materializing university ranking views for faster YKS placement queries"
            )
        
        return result
    
    async def _generate_index_suggestions(
        self, 
        query: str, 
        metrics: QueryPerformanceMetrics
    ) -> List[str]:
        """Generate index suggestions based on query analysis"""
        suggestions = []
        
        # Extract table and column information
        tables = re.findall(r'\bFROM\s+(\w+)', query, re.IGNORECASE)
        where_columns = re.findall(r'\bWHERE\s+.*?(\w+)\s*[=<>]', query, re.IGNORECASE)
        join_columns = re.findall(r'\bON\s+.*?(\w+)\s*=', query, re.IGNORECASE)
        order_columns = re.findall(r'\bORDER\s+BY\s+(\w+)', query, re.IGNORECASE)
        
        # Suggest indexes for WHERE clauses
        for table in tables:
            for column in where_columns:
                suggestions.append(f"CREATE INDEX idx_{table}_{column} ON {table}({column})")
        
        # Suggest composite indexes for JOIN conditions
        if join_columns and len(join_columns) >= 2:
            table = tables[0] if tables else "table"
            columns = ", ".join(join_columns[:3])  # Limit to 3 columns
            suggestions.append(f"CREATE INDEX idx_{table}_composite ON {table}({columns})")
        
        # Turkish exam-specific index suggestions
        if metrics.exam_related:
            if "exam_results" in query.lower():
                suggestions.extend([
                    "CREATE INDEX idx_exam_results_type_date ON exam_results(exam_type, exam_date)",
                    "CREATE INDEX idx_exam_results_student_type ON exam_results(student_id, exam_type)",
                    "CREATE INDEX idx_exam_results_score_desc ON exam_results(score DESC) -- For ranking queries"
                ])
            
            if "students" in query.lower():
                suggestions.append(
                    "CREATE INDEX idx_students_registration_date ON students(registration_date) -- For student cohort analysis"
                )
        
        return suggestions
    
    async def _estimate_performance_improvement(
        self, 
        original_query: str, 
        optimized_query: str, 
        metrics: QueryPerformanceMetrics
    ) -> float:
        """Estimate performance improvement percentage"""
        if original_query == optimized_query:
            return 0.0
        
        # Basic heuristics for improvement estimation
        improvement = 0.0
        
        # SELECT * to specific columns
        if "SELECT *" in original_query and "SELECT *" not in optimized_query:
            improvement += 15.0  # ~15% improvement
        
        # Added WHERE clause
        if "WHERE" not in original_query and "WHERE" in optimized_query:
            improvement += 30.0  # ~30% improvement
        
        # Function optimization
        function_count_original = len(re.findall(r'\w+\(', original_query))
        function_count_optimized = len(re.findall(r'\w+\(', optimized_query))
        if function_count_optimized < function_count_original:
            improvement += (function_count_original - function_count_optimized) * 10.0
        
        # Join optimization
        if "CROSS JOIN" in original_query and "CROSS JOIN" not in optimized_query:
            improvement += 40.0  # ~40% improvement
        
        return min(improvement, 80.0)  # Cap at 80% improvement


class ConnectionPoolManager:
    """Advanced database connection pool management"""
    
    def __init__(self):
        self.connection_pools: Dict[str, Dict[str, Any]] = {}
        self.pool_metrics: Dict[str, Dict[str, float]] = defaultdict(dict)
        self.exam_mode_active = False
        self.exam_mode_start_time: Optional[datetime] = None
    
    async def create_connection_pool(self, db_config: DatabaseConnection) -> bool:
        """Create database connection pool"""
        try:
            pool_config = {
                "connection_config": db_config,
                "pool": None,
                "created_at": datetime.now(timezone.utc),
                "last_health_check": datetime.now(timezone.utc)
            }
            
            if db_config.database_type == DatabaseType.POSTGRESQL:
                pool = await asyncpg.create_pool(
                    host=db_config.host,
                    port=db_config.port,
                    database=db_config.database,
                    user=db_config.username,
                    min_size=db_config.min_pool_size,
                    max_size=db_config.max_pool_size,
                    command_timeout=db_config.query_timeout
                )
                pool_config["pool"] = pool
            
            elif db_config.database_type == DatabaseType.MYSQL:
                pool = await aiomysql.create_pool(
                    host=db_config.host,
                    port=db_config.port,
                    db=db_config.database,
                    user=db_config.username,
                    minsize=db_config.min_pool_size,
                    maxsize=db_config.max_pool_size
                )
                pool_config["pool"] = pool
            
            elif db_config.database_type == DatabaseType.REDIS:
                pool = aioredis.ConnectionPool.from_url(
                    f"redis://{db_config.host}:{db_config.port}",
                    max_connections=db_config.max_pool_size
                )
                pool_config["pool"] = pool
            
            self.connection_pools[db_config.connection_id] = pool_config
            
            logger.info(f"Created connection pool for {db_config.database_type.value}: {db_config.connection_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create connection pool: {e}")
            return False
    
    async def get_connection(self, connection_id: str):
        """Get database connection from pool"""
        if connection_id not in self.connection_pools:
            raise ValueError(f"Connection pool {connection_id} not found")
        
        pool_info = self.connection_pools[connection_id]
        pool = pool_info["pool"]
        
        if pool is None:
            raise RuntimeError(f"Connection pool {connection_id} not initialized")
        
        start_time = time.time()
        
        try:
            # Get connection from pool
            connection = await pool.acquire()
            
            # Update metrics
            connection_time = time.time() - start_time
            self.pool_metrics[connection_id]["last_connection_time"] = connection_time
            self.pool_metrics[connection_id]["total_connections"] = (
                self.pool_metrics[connection_id].get("total_connections", 0) + 1
            )
            
            return connection
            
        except Exception as e:
            logger.error(f"Failed to get connection from pool {connection_id}: {e}")
            raise
    
    async def release_connection(self, connection_id: str, connection):
        """Release connection back to pool"""
        if connection_id not in self.connection_pools:
            return
        
        pool_info = self.connection_pools[connection_id]
        pool = pool_info["pool"]
        
        if pool:
            await pool.release(connection)
    
    async def enable_exam_mode(self) -> None:
        """Enable exam mode with increased connection limits"""
        self.exam_mode_active = True
        self.exam_mode_start_time = datetime.now(timezone.utc)
        
        for connection_id, pool_info in self.connection_pools.items():
            db_config = pool_info["connection_config"]
            
            # Increase pool size for exam mode
            original_max_size = db_config.max_pool_size
            exam_max_size = db_config.exam_mode_pool_size
            
            if exam_max_size > original_max_size:
                # Recreate pool with larger size
                await self.close_connection_pool(connection_id)
                db_config.max_pool_size = exam_max_size
                await self.create_connection_pool(db_config)
                
                logger.info(f"Expanded connection pool {connection_id} for exam mode: {original_max_size} -> {exam_max_size}")
    
    async def disable_exam_mode(self) -> None:
        """Disable exam mode and restore normal connection limits"""
        self.exam_mode_active = False
        
        for connection_id, pool_info in self.connection_pools.items():
            db_config = pool_info["connection_config"]
            
            # Restore original pool size
            if db_config.max_pool_size == db_config.exam_mode_pool_size:
                await self.close_connection_pool(connection_id)
                db_config.max_pool_size = 50  # Default max size
                await self.create_connection_pool(db_config)
                
                logger.info(f"Restored connection pool {connection_id} from exam mode")
        
        if self.exam_mode_start_time:
            exam_duration = datetime.now(timezone.utc) - self.exam_mode_start_time
            logger.info(f"Exam mode was active for {exam_duration}")
    
    async def close_connection_pool(self, connection_id: str) -> None:
        """Close database connection pool"""
        if connection_id not in self.connection_pools:
            return
        
        pool_info = self.connection_pools[connection_id]
        pool = pool_info["pool"]
        
        if pool:
            await pool.close()
        
        del self.connection_pools[connection_id]
        logger.info(f"Closed connection pool: {connection_id}")
    
    async def health_check_pools(self) -> Dict[str, Dict[str, Any]]:
        """Perform health check on all connection pools"""
        health_status = {}
        
        for connection_id, pool_info in self.connection_pools.items():
            pool = pool_info["pool"]
            db_config = pool_info["connection_config"]
            
            try:
                # Test connection
                start_time = time.time()
                connection = await pool.acquire()
                
                # Perform simple query
                if db_config.database_type == DatabaseType.POSTGRESQL:
                    await connection.execute("SELECT 1")
                elif db_config.database_type == DatabaseType.MYSQL:
                    async with connection.cursor() as cursor:
                        await cursor.execute("SELECT 1")
                
                await pool.release(connection)
                response_time = time.time() - start_time
                
                health_status[connection_id] = {
                    "status": "healthy",
                    "response_time": response_time,
                    "pool_size": pool.get_size() if hasattr(pool, 'get_size') else 0,
                    "available_connections": pool.get_idle_size() if hasattr(pool, 'get_idle_size') else 0,
                    "last_check": datetime.now(timezone.utc).isoformat()
                }
                
            except Exception as e:
                health_status[connection_id] = {
                    "status": "unhealthy",
                    "error": str(e),
                    "last_check": datetime.now(timezone.utc).isoformat()
                }
        
        return health_status


class DatabasePerformanceOptimizer:
    """Main database performance optimization engine"""
    
    def __init__(self):
        self.query_metrics: Dict[str, QueryPerformanceMetrics] = {}
        self.query_optimizer = QueryOptimizer()
        self.connection_manager = ConnectionPoolManager()
        
        # Performance monitoring
        self.slow_query_threshold = 1.0  # seconds
        self.monitoring_enabled = True
        self.optimization_history: deque = deque(maxlen=1000)
        
        # Turkish exam-specific settings
        self.exam_peak_hours = [(19, 22), (14, 17)]  # Evening and afternoon peaks
        self.exam_subjects = ["matematik", "türkçe", "fen", "sosyal", "yabanci_dil"]
        
        # Performance statistics
        self.total_queries_analyzed = 0
        self.total_optimizations_applied = 0
        self.total_performance_improvement = 0.0
    
    def query_performance_monitor(self, query_type: QueryType = QueryType.SELECT):
        """Decorator to monitor query performance"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                if not self.monitoring_enabled:
                    return await func(*args, **kwargs)
                
                query_text = kwargs.get("query", "")
                if not query_text and args:
                    query_text = str(args[0])
                
                query_hash = hashlib.md5(query_text.encode()).hexdigest()
                
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    execution_time = time.time() - start_time
                    
                    # Update query metrics
                    await self._update_query_metrics(
                        query_text, query_hash, query_type, execution_time, success=True
                    )
                    
                    return result
                    
                except Exception as e:
                    execution_time = time.time() - start_time
                    await self._update_query_metrics(
                        query_text, query_hash, query_type, execution_time, success=False, error=str(e)
                    )
                    raise
                
            return wrapper
        return decorator
    
    async def _update_query_metrics(
        self,
        query_text: str,
        query_hash: str,
        query_type: QueryType,
        execution_time: float,
        success: bool = True,
        error: Optional[str] = None
    ) -> None:
        """Update query performance metrics"""
        
        if query_hash not in self.query_metrics:
            # Create new metrics entry
            metrics = QueryPerformanceMetrics(
                query_id=str(uuid.uuid4()),
                query_hash=query_hash,
                query_text=query_text,
                query_type=query_type,
                exam_related=self._is_exam_related_query(query_text)
            )
            
            # Detect subject area for Turkish exams
            if metrics.exam_related:
                metrics.subject_area = self._detect_subject_area(query_text)
            
            self.query_metrics[query_hash] = metrics
        
        # Update execution metrics
        metrics = self.query_metrics[query_hash]
        metrics.update_metrics(execution_time)
        
        # Check if query is slow and needs optimization
        if execution_time > self.slow_query_threshold:
            await self._analyze_slow_query(metrics)
        
        self.total_queries_analyzed += 1
    
    def _is_exam_related_query(self, query_text: str) -> bool:
        """Check if query is related to Turkish exam system"""
        exam_keywords = [
            "exam_results", "exam_type", "TYT", "AYT", "YKS",
            "students", "university", "score", "ranking",
            "matematik", "türkçe", "fen", "sosyal"
        ]
        
        query_lower = query_text.lower()
        return any(keyword.lower() in query_lower for keyword in exam_keywords)
    
    def _detect_subject_area(self, query_text: str) -> Optional[str]:
        """Detect subject area from query text"""
        query_lower = query_text.lower()
        
        for subject in self.exam_subjects:
            if subject in query_lower:
                return subject
        
        # Check for English variations
        subject_mapping = {
            "math": "matematik",
            "turkish": "türkçe",
            "science": "fen",
            "social": "sosyal",
            "english": "yabanci_dil"
        }
        
        for english_subject, turkish_subject in subject_mapping.items():
            if english_subject in query_lower:
                return turkish_subject
        
        return None
    
    async def _analyze_slow_query(self, metrics: QueryPerformanceMetrics) -> None:
        """Analyze slow query and generate optimization recommendations"""
        try:
            # Run query optimization
            optimization_result = await self.query_optimizer.optimize_query(
                metrics.query_text, metrics
            )
            
            # Update metrics with optimization recommendations
            metrics.optimization_recommendations = optimization_result["recommendations"]
            metrics.suggested_indexes = optimization_result["index_suggestions"]
            
            # Log slow query analysis
            logger.warning(f"Slow query detected: {metrics.query_id} ({metrics.average_execution_time:.2f}s)")
            
            # Store optimization history
            optimization_event = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "query_id": metrics.query_id,
                "query_hash": metrics.query_hash,
                "execution_time": metrics.average_execution_time,
                "optimization_result": optimization_result,
                "exam_related": metrics.exam_related
            }
            self.optimization_history.append(optimization_event)
            
        except Exception as e:
            logger.error(f"Slow query analysis failed: {e}")
    
    async def optimize_database_schema(self, database_connection: DatabaseConnection) -> Dict[str, Any]:
        """Optimize database schema based on query patterns"""
        optimization_results = {
            "indexes_created": [],
            "partitions_created": [],
            "materialized_views": [],
            "schema_changes": [],
            "estimated_improvement": 0.0
        }
        
        try:
            # Analyze query patterns for index recommendations
            index_recommendations = await self._generate_schema_indexes()
            optimization_results["indexes_created"] = index_recommendations
            
            # Create Turkish exam-specific optimizations
            exam_optimizations = await self._create_exam_specific_optimizations()
            optimization_results["schema_changes"].extend(exam_optimizations)
            
            # Create partitioning strategy for large tables
            partitioning_strategy = await self._create_partitioning_strategy()
            optimization_results["partitions_created"] = partitioning_strategy
            
            # Calculate estimated improvement
            total_improvement = 0.0
            for metrics in self.query_metrics.values():
                if metrics.optimization_recommendations:
                    total_improvement += 20.0  # Assume 20% improvement per optimization
            
            optimization_results["estimated_improvement"] = min(total_improvement / len(self.query_metrics), 60.0)
            
            self.total_optimizations_applied += len(optimization_results["indexes_created"])
            self.total_performance_improvement += optimization_results["estimated_improvement"]
            
            logger.info(f"Database schema optimization completed: {len(optimization_results['indexes_created'])} indexes, {optimization_results['estimated_improvement']:.1f}% improvement")
            
        except Exception as e:
            logger.error(f"Database schema optimization failed: {e}")
            optimization_results["error"] = str(e)
        
        return optimization_results
    
    async def _generate_schema_indexes(self) -> List[str]:
        """Generate index creation statements based on query analysis"""
        index_statements = []
        column_usage = defaultdict(int)
        
        # Analyze column usage patterns
        for metrics in self.query_metrics.values():
            query_text = metrics.query_text.lower()
            
            # Extract commonly used columns in WHERE clauses
            where_patterns = re.findall(r'where\s+.*?(\w+)\s*[=<>]', query_text)
            for column in where_patterns:
                column_usage[column] += metrics.execution_count
            
            # Extract JOIN columns
            join_patterns = re.findall(r'on\s+.*?(\w+)\s*=', query_text)
            for column in join_patterns:
                column_usage[column] += metrics.execution_count * 1.5  # Higher weight for JOINs
        
        # Create indexes for most used columns
        for column, usage_count in sorted(column_usage.items(), key=lambda x: x[1], reverse=True)[:10]:
            if usage_count > 5:  # Minimum usage threshold
                index_statements.append(f"CREATE INDEX IF NOT EXISTS idx_{column} ON table_name({column})")
        
        # Turkish exam-specific indexes
        exam_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_exam_results_composite ON exam_results(exam_type, exam_date, student_id)",
            "CREATE INDEX IF NOT EXISTS idx_exam_results_score ON exam_results(score DESC)",
            "CREATE INDEX IF NOT EXISTS idx_students_registration ON students(registration_date, status)",
            "CREATE INDEX IF NOT EXISTS idx_universities_score ON universities(min_score, department_id)"
        ]
        index_statements.extend(exam_indexes)
        
        return index_statements
    
    async def _create_exam_specific_optimizations(self) -> List[str]:
        """Create Turkish exam-specific database optimizations"""
        optimizations = []
        
        # Exam results partitioning by exam_date
        optimizations.append(
            "ALTER TABLE exam_results PARTITION BY RANGE (exam_date) "
            "(PARTITION p_2024 VALUES LESS THAN ('2025-01-01'), "
            "PARTITION p_2025 VALUES LESS THAN ('2026-01-01'))"
        )
        
        # Materialized view for university rankings
        optimizations.append("""
            CREATE MATERIALIZED VIEW university_rankings AS
            SELECT u.university_name, u.department, u.min_score, u.quota,
                   COUNT(er.student_id) as applicants
            FROM universities u
            LEFT JOIN exam_results er ON er.score >= u.min_score
            WHERE er.exam_type = 'YKS'
            GROUP BY u.university_name, u.department, u.min_score, u.quota
            ORDER BY u.min_score DESC
        """)
        
        # Performance statistics view
        optimizations.append("""
            CREATE MATERIALIZED VIEW subject_performance_stats AS
            SELECT exam_type, subject, exam_date,
                   AVG(score) as avg_score,
                   STDDEV(score) as std_deviation,
                   COUNT(*) as student_count,
                   PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY score) as median_score
            FROM exam_results
            WHERE exam_date >= CURRENT_DATE - INTERVAL '2 years'
            GROUP BY exam_type, subject, exam_date
        """)
        
        return optimizations
    
    async def _create_partitioning_strategy(self) -> List[str]:
        """Create partitioning strategy for large tables"""
        partitioning_statements = []
        
        # Partition exam_results by exam_date (monthly partitions)
        partitioning_statements.append({
            "table": "exam_results",
            "strategy": "RANGE",
            "column": "exam_date",
            "interval": "MONTHLY",
            "description": "Monthly partitions for exam results"
        })
        
        # Partition student_activities by activity_date
        partitioning_statements.append({
            "table": "student_activities",
            "strategy": "RANGE", 
            "column": "activity_date",
            "interval": "WEEKLY",
            "description": "Weekly partitions for student activities"
        })
        
        return partitioning_statements
    
    async def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive database performance report"""
        
        # Calculate summary statistics
        slow_queries = [m for m in self.query_metrics.values() if m.is_slow_query()]
        exam_queries = [m for m in self.query_metrics.values() if m.exam_related]
        
        avg_execution_time = (
            sum(m.average_execution_time for m in self.query_metrics.values()) / 
            max(len(self.query_metrics), 1)
        )
        
        performance_scores = [m.get_performance_score() for m in self.query_metrics.values()]
        avg_performance_score = sum(performance_scores) / max(len(performance_scores), 1)
        
        report = {
            "summary": {
                "total_queries_analyzed": self.total_queries_analyzed,
                "unique_queries": len(self.query_metrics),
                "slow_queries": len(slow_queries),
                "exam_related_queries": len(exam_queries),
                "average_execution_time": avg_execution_time,
                "average_performance_score": avg_performance_score,
                "total_optimizations": self.total_optimizations_applied,
                "estimated_improvement": self.total_performance_improvement
            },
            "slow_queries": [
                {
                    "query_id": q.query_id,
                    "execution_time": q.average_execution_time,
                    "execution_count": q.execution_count,
                    "performance_score": q.get_performance_score(),
                    "recommendations": q.optimization_recommendations[:3]  # Top 3
                }
                for q in sorted(slow_queries, key=lambda x: x.average_execution_time, reverse=True)[:10]
            ],
            "exam_performance": {
                "exam_queries_count": len(exam_queries),
                "avg_exam_query_time": (
                    sum(q.average_execution_time for q in exam_queries) / 
                    max(len(exam_queries), 1)
                ),
                "subjects_analyzed": list(set(q.subject_area for q in exam_queries if q.subject_area)),
                "peak_usage_queries": len([q for q in exam_queries if q.peak_usage_during_exams])
            },
            "optimization_opportunities": {
                "missing_indexes": sum(len(q.missing_indexes) for q in self.query_metrics.values()),
                "suggested_indexes": sum(len(q.suggested_indexes) for q in self.query_metrics.values()),
                "total_recommendations": sum(len(q.optimization_recommendations) for q in self.query_metrics.values())
            },
            "connection_pools": await self.connection_manager.health_check_pools(),
            "exam_mode_status": {
                "active": self.connection_manager.exam_mode_active,
                "start_time": (
                    self.connection_manager.exam_mode_start_time.isoformat() 
                    if self.connection_manager.exam_mode_start_time else None
                )
            },
            "recent_optimizations": list(self.optimization_history)[-10:]  # Last 10 optimizations
        }
        
        return report
    
    async def enable_exam_mode(self) -> None:
        """Enable exam mode optimizations"""
        await self.connection_manager.enable_exam_mode()
        
        # Adjust performance settings for exam period
        self.slow_query_threshold = 0.5  # Stricter threshold during exams
        
        logger.info("Database exam mode enabled - performance optimizations active")
    
    async def disable_exam_mode(self) -> None:
        """Disable exam mode optimizations"""
        await self.connection_manager.disable_exam_mode()
        
        # Restore normal performance settings
        self.slow_query_threshold = 1.0
        
        logger.info("Database exam mode disabled - normal performance settings restored")


if __name__ == "__main__":
    # Example usage and testing
    print("KIRO2 Database Performance Optimization Engine")
    print("=" * 50)
    
    async def test_database_optimization():
        """Test database performance optimization"""
        
        # Create performance optimizer
        optimizer = DatabasePerformanceOptimizer()
        
        # Create test database connection
        db_config = DatabaseConnection(
            connection_id="test_db",
            database_type=DatabaseType.POSTGRESQL,
            host="localhost",
            port=5432,
            database="kiro2_exam",
            username="kiro_user",
            max_pool_size=20
        )
        
        # Create connection pool
        await optimizer.connection_manager.create_connection_pool(db_config)
        
        # Simulate query monitoring
        print("Simulating query performance monitoring...")
        
        # Mock query executions
        test_queries = [
            ("SELECT * FROM exam_results WHERE exam_type = 'TYT'", QueryType.SELECT),
            ("SELECT student_id, score FROM exam_results WHERE exam_date > '2024-01-01'", QueryType.SELECT),
            ("INSERT INTO exam_results (student_id, exam_type, score) VALUES ($1, $2, $3)", QueryType.INSERT),
            ("UPDATE students SET last_login = NOW() WHERE student_id = $1", QueryType.UPDATE),
            ("SELECT AVG(score) FROM exam_results WHERE subject = 'matematik'", QueryType.ANALYTICAL)
        ]
        
        for query_text, query_type in test_queries:
            query_hash = hashlib.md5(query_text.encode()).hexdigest()
            
            # Simulate execution times
            execution_time = 0.5 + (hash(query_text) % 100) / 100.0  # 0.5-1.5 seconds
            
            await optimizer._update_query_metrics(
                query_text, query_hash, query_type, execution_time
            )
        
        # Test schema optimization
        print("Testing database schema optimization...")
        schema_optimization = await optimizer.optimize_database_schema(db_config)
        
        print(f"Schema optimization results:")
        print(f"- Indexes created: {len(schema_optimization['indexes_created'])}")
        print(f"- Schema changes: {len(schema_optimization['schema_changes'])}")
        print(f"- Estimated improvement: {schema_optimization['estimated_improvement']:.1f}%")
        
        # Test exam mode
        print("Testing exam mode...")
        await optimizer.enable_exam_mode()
        
        # Simulate more queries during exam mode
        for i in range(5):
            query_text = f"SELECT score FROM exam_results WHERE student_id = {i}"
            query_hash = hashlib.md5(query_text.encode()).hexdigest()
            execution_time = 0.3  # Faster during exam mode
            
            await optimizer._update_query_metrics(
                query_text, query_hash, QueryType.SELECT, execution_time
            )
        
        await optimizer.disable_exam_mode()
        
        # Generate performance report
        print("Generating performance report...")
        report = await optimizer.get_performance_report()
        
        print(f"\nPerformance Report Summary:")
        print(f"- Total queries analyzed: {report['summary']['total_queries_analyzed']}")
        print(f"- Unique queries: {report['summary']['unique_queries']}")
        print(f"- Slow queries: {report['summary']['slow_queries']}")
        print(f"- Exam-related queries: {report['summary']['exam_related_queries']}")
        print(f"- Average execution time: {report['summary']['average_execution_time']:.3f}s")
        print(f"- Average performance score: {report['summary']['average_performance_score']:.1f}/100")
        print(f"- Total optimizations applied: {report['summary']['total_optimizations']}")
        
        print(f"\nExam Performance:")
        print(f"- Exam queries: {report['exam_performance']['exam_queries_count']}")
        print(f"- Avg exam query time: {report['exam_performance']['avg_exam_query_time']:.3f}s")
        print(f"- Subjects analyzed: {report['exam_performance']['subjects_analyzed']}")
        
        print(f"\nOptimization Opportunities:")
        print(f"- Missing indexes: {report['optimization_opportunities']['missing_indexes']}")
        print(f"- Suggested indexes: {report['optimization_opportunities']['suggested_indexes']}")
        print(f"- Total recommendations: {report['optimization_opportunities']['total_recommendations']}")
        
        # Cleanup
        await optimizer.connection_manager.close_connection_pool("test_db")
        
        print("\nDatabase performance optimization test completed!")
    
    # Run test
    asyncio.run(test_database_optimization())