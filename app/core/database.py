"""
Database configuration and connection management with advanced monitoring
"""
import logging
import time
import threading
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Generator
from dataclasses import dataclass, field
from collections import defaultdict, deque

from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool, Pool
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class QueryMetrics:
    """Metrics for individual query execution"""
    query_hash: str
    sql_text: str
    execution_time: float
    timestamp: datetime
    success: bool
    error_message: Optional[str] = None
    rows_affected: Optional[int] = None
    connection_id: Optional[str] = None


@dataclass
class ConnectionPoolMetrics:
    """Metrics for database connection pool"""
    pool_size: int
    checked_out: int
    overflow: int
    checked_in: int
    total_connections: int
    invalid_connections: int
    timestamp: datetime = field(default_factory=datetime.now)


class DatabaseMonitor:
    """
    Advanced database monitoring and performance metrics collection
    """
    
    def __init__(self, max_query_history: int = 1000):
        self.max_query_history = max_query_history
        self.query_history: deque = deque(maxlen=max_query_history)
        self.slow_queries: deque = deque(maxlen=100)  # Keep last 100 slow queries
        self.query_stats: Dict[str, Dict] = defaultdict(lambda: {
            'count': 0,
            'total_time': 0.0,
            'avg_time': 0.0,
            'min_time': float('inf'),
            'max_time': 0.0,
            'error_count': 0
        })
        
        # Performance thresholds
        self.slow_query_threshold = 1.0  # seconds
        self.very_slow_query_threshold = 5.0  # seconds
        
        # Connection pool metrics
        self.pool_metrics_history: deque = deque(maxlen=100)
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Performance counters
        self.total_queries = 0
        self.total_errors = 0
        self.total_execution_time = 0.0
        
        logger.info("Database monitor initialized")
    
    def record_query(self, metrics: QueryMetrics):
        """Record query execution metrics"""
        with self._lock:
            # Add to history
            self.query_history.append(metrics)
            
            # Update statistics
            query_key = self._get_query_key(metrics.sql_text)
            stats = self.query_stats[query_key]
            
            stats['count'] += 1
            self.total_queries += 1
            
            if metrics.success:
                stats['total_time'] += metrics.execution_time
                stats['avg_time'] = stats['total_time'] / stats['count']
                stats['min_time'] = min(stats['min_time'], metrics.execution_time)
                stats['max_time'] = max(stats['max_time'], metrics.execution_time)
                self.total_execution_time += metrics.execution_time
                
                # Track slow queries
                if metrics.execution_time >= self.slow_query_threshold:
                    self.slow_queries.append(metrics)
                    
                    if metrics.execution_time >= self.very_slow_query_threshold:
                        logger.warning(
                            f"Very slow query detected: {metrics.execution_time:.2f}s - "
                            f"{metrics.sql_text[:100]}..."
                        )
            else:
                stats['error_count'] += 1
                self.total_errors += 1
                logger.error(f"Query error: {metrics.error_message}")
    
    def record_pool_metrics(self, pool: Pool):
        """Record connection pool metrics"""
        try:
            # Get basic pool metrics (some methods may not be available on all pool types)
            pool_size = getattr(pool, 'size', lambda: 0)()
            checked_out = getattr(pool, 'checkedout', lambda: 0)()
            overflow = getattr(pool, 'overflow', lambda: 0)()
            checked_in = getattr(pool, 'checkedin', lambda: 0)()
            
            # invalidated() method doesn't exist on QueuePool, use 0 as default
            invalid_connections = 0
            if hasattr(pool, 'invalidated'):
                try:
                    invalid_connections = pool.invalidated()
                except:
                    invalid_connections = 0
            
            metrics = ConnectionPoolMetrics(
                pool_size=pool_size,
                checked_out=checked_out,
                overflow=overflow,
                checked_in=checked_in,
                total_connections=pool_size + overflow,
                invalid_connections=invalid_connections
            )
            
            with self._lock:
                self.pool_metrics_history.append(metrics)
                
        except Exception as e:
            logger.warning(f"Failed to collect pool metrics: {e}")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        with self._lock:
            current_time = datetime.now()
            
            # Calculate recent performance (last hour)
            recent_queries = [
                q for q in self.query_history 
                if (current_time - q.timestamp) <= timedelta(hours=1)
            ]
            
            recent_successful = [q for q in recent_queries if q.success]
            recent_errors = [q for q in recent_queries if not q.success]
            
            # Top slow queries
            top_slow_queries = sorted(
                list(self.slow_queries)[-20:], 
                key=lambda x: x.execution_time, 
                reverse=True
            )[:10]
            
            # Most frequent queries
            query_frequency = sorted(
                self.query_stats.items(),
                key=lambda x: x[1]['count'],
                reverse=True
            )[:10]
            
            # Current pool status
            latest_pool_metrics = (
                self.pool_metrics_history[-1] 
                if self.pool_metrics_history 
                else None
            )
            
            return {
                'overall_stats': {
                    'total_queries': self.total_queries,
                    'total_errors': self.total_errors,
                    'error_rate': (
                        self.total_errors / self.total_queries 
                        if self.total_queries > 0 else 0
                    ),
                    'avg_execution_time': (
                        self.total_execution_time / (self.total_queries - self.total_errors)
                        if (self.total_queries - self.total_errors) > 0 else 0
                    )
                },
                'recent_performance': {
                    'queries_last_hour': len(recent_queries),
                    'successful_queries': len(recent_successful),
                    'failed_queries': len(recent_errors),
                    'avg_response_time': (
                        sum(q.execution_time for q in recent_successful) / len(recent_successful)
                        if recent_successful else 0
                    )
                },
                'slow_queries': [
                    {
                        'sql': q.sql_text[:200] + '...' if len(q.sql_text) > 200 else q.sql_text,
                        'execution_time': q.execution_time,
                        'timestamp': q.timestamp.isoformat()
                    }
                    for q in top_slow_queries
                ],
                'frequent_queries': [
                    {
                        'query_pattern': key[:100] + '...' if len(key) > 100 else key,
                        'count': stats['count'],
                        'avg_time': stats['avg_time'],
                        'error_count': stats['error_count']
                    }
                    for key, stats in query_frequency
                ],
                'connection_pool': (
                    {
                        'pool_size': latest_pool_metrics.pool_size,
                        'checked_out': latest_pool_metrics.checked_out,
                        'overflow': latest_pool_metrics.overflow,
                        'utilization': (
                            latest_pool_metrics.checked_out / latest_pool_metrics.pool_size
                            if latest_pool_metrics.pool_size > 0 else 0
                        ),
                        'timestamp': latest_pool_metrics.timestamp.isoformat()
                    }
                    if latest_pool_metrics else None
                )
            }
    
    def get_slow_queries(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent slow queries"""
        with self._lock:
            recent_slow = sorted(
                list(self.slow_queries)[-limit:],
                key=lambda x: x.execution_time,
                reverse=True
            )
            
            return [
                {
                    'sql': q.sql_text,
                    'execution_time': q.execution_time,
                    'timestamp': q.timestamp.isoformat(),
                    'success': q.success,
                    'error': q.error_message
                }
                for q in recent_slow
            ]
    
    def get_query_optimization_suggestions(self) -> List[str]:
        """Generate query optimization suggestions based on collected metrics"""
        suggestions = []
        
        with self._lock:
            # Analyze slow queries for patterns
            if self.slow_queries:
                slow_query_patterns = defaultdict(int)
                for query in self.slow_queries:
                    pattern = self._extract_query_pattern(query.sql_text)
                    slow_query_patterns[pattern] += 1
                
                # Suggest optimizations for common slow patterns
                for pattern, count in slow_query_patterns.items():
                    if count >= 3:  # Pattern appears frequently
                        if 'JOIN' in pattern.upper():
                            suggestions.append(
                                f"Consider adding indexes for JOIN operations in: {pattern[:100]}..."
                            )
                        elif 'WHERE' in pattern.upper():
                            suggestions.append(
                                f"Consider adding indexes for WHERE clauses in: {pattern[:100]}..."
                            )
                        elif 'ORDER BY' in pattern.upper():
                            suggestions.append(
                                f"Consider adding indexes for ORDER BY clauses in: {pattern[:100]}..."
                            )
            
            # Check connection pool utilization
            if self.pool_metrics_history:
                recent_metrics = list(self.pool_metrics_history)[-10:]
                avg_utilization = sum(
                    m.checked_out / m.pool_size for m in recent_metrics
                ) / len(recent_metrics)
                
                if avg_utilization > 0.8:
                    suggestions.append(
                        "High connection pool utilization detected. "
                        "Consider increasing pool size or optimizing query performance."
                    )
                elif avg_utilization < 0.2:
                    suggestions.append(
                        "Low connection pool utilization. "
                        "Consider reducing pool size to save resources."
                    )
            
            # Check error rates
            if self.total_queries > 100:
                error_rate = self.total_errors / self.total_queries
                if error_rate > 0.05:  # More than 5% error rate
                    suggestions.append(
                        f"High query error rate ({error_rate:.1%}). "
                        "Review query patterns and error handling."
                    )
        
        return suggestions
    
    def _get_query_key(self, sql_text: str) -> str:
        """Generate a key for query grouping (normalize similar queries)"""
        # Simple normalization - replace numbers and strings with placeholders
        import re
        normalized = re.sub(r'\b\d+\b', '?', sql_text)
        normalized = re.sub(r"'[^']*'", "'?'", normalized)
        normalized = re.sub(r'"[^"]*"', '"?"', normalized)
        return normalized[:200]  # Limit length
    
    def _extract_query_pattern(self, sql_text: str) -> str:
        """Extract query pattern for analysis"""
        # Extract main SQL operation and table names
        import re
        
        # Get the main operation
        operation_match = re.match(r'\s*(SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP)', 
                                 sql_text.upper())
        operation = operation_match.group(1) if operation_match else 'UNKNOWN'
        
        # Extract table names (simplified)
        table_matches = re.findall(r'\b(?:FROM|JOIN|INTO|UPDATE)\s+(\w+)', 
                                 sql_text.upper())
        tables = list(set(table_matches))
        
        return f"{operation} {' '.join(tables)}"


# Global database monitor instance
db_monitor = DatabaseMonitor()


class MonitoredEngine:
    """Database engine wrapper with monitoring capabilities"""
    
    def __init__(self, engine: Engine, monitor: DatabaseMonitor):
        self.engine = engine
        self.monitor = monitor
        self._setup_event_listeners()
    
    def _setup_event_listeners(self):
        """Set up SQLAlchemy event listeners for monitoring"""
        
        @event.listens_for(self.engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            context._query_start_time = time.time()
            context._query_statement = statement
        
        @event.listens_for(self.engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            execution_time = time.time() - context._query_start_time
            
            metrics = QueryMetrics(
                query_hash=str(hash(statement)),
                sql_text=statement,
                execution_time=execution_time,
                timestamp=datetime.now(),
                success=True,
                rows_affected=cursor.rowcount if hasattr(cursor, 'rowcount') else None,
                connection_id=str(id(conn))
            )
            
            self.monitor.record_query(metrics)
        
        @event.listens_for(self.engine, "handle_error")
        def handle_error(exception_context):
            execution_time = (
                time.time() - exception_context.execution_context._query_start_time
                if hasattr(exception_context.execution_context, '_query_start_time')
                else 0.0
            )
            
            metrics = QueryMetrics(
                query_hash=str(hash(exception_context.statement or "")),
                sql_text=exception_context.statement or "Unknown",
                execution_time=execution_time,
                timestamp=datetime.now(),
                success=False,
                error_message=str(exception_context.original_exception),
                connection_id=str(id(exception_context.connection)) if exception_context.connection else None
            )
            
            self.monitor.record_query(metrics)
    
    def __getattr__(self, name):
        """Delegate all other attributes to the wrapped engine"""
        return getattr(self.engine, name)


# Create database engine with advanced connection pooling
# Check if we should use SQLite for development
database_url = settings.database_url
connect_args = {}

if database_url.startswith('sqlite'):
    # SQLite configuration
    connect_args = {
        "check_same_thread": False,  # Allow SQLite to be used across threads
        "timeout": 20
    }
    # Use simpler pooling for SQLite
    base_engine = create_engine(
        database_url,
        pool_pre_ping=True,
        echo=False,
        connect_args=connect_args
    )
else:
    # PostgreSQL configuration
    connect_args = {
        "connect_timeout": 10,
        "application_name": "quick_commerce_deals"
    }
    base_engine = create_engine(
        database_url,
        poolclass=QueuePool,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_pre_ping=True,
        pool_recycle=3600,  # Recycle connections every hour
        pool_timeout=30,    # Timeout for getting connection from pool
        echo=False,         # Set to True for SQL query logging
        echo_pool=False,    # Set to True for connection pool logging
        connect_args=connect_args
    )

# Wrap engine with monitoring
engine = MonitoredEngine(base_engine, db_monitor)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=base_engine)

# Create base class for models
Base = declarative_base()


@contextmanager
def get_monitored_db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions with monitoring
    """
    session = SessionLocal()
    start_time = time.time()
    
    try:
        # Record pool metrics before session use
        db_monitor.record_pool_metrics(base_engine.pool)
        
        yield session
        session.commit()
        
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session_duration = time.time() - start_time
        if session_duration > 5.0:  # Log long-running sessions
            logger.warning(f"Long-running database session: {session_duration:.2f}s")
        
        session.close()


def get_db():
    """
    Dependency to get database session with monitoring
    """
    with get_monitored_db_session() as session:
        yield session


class DatabaseHealthChecker:
    """Database health monitoring and diagnostics"""
    
    @staticmethod
    async def check_database_health() -> Dict[str, Any]:
        """Comprehensive database health check"""
        health_status = {
            "status": "unknown",
            "connection_pool": {},
            "query_performance": {},
            "recent_errors": [],
            "recommendations": []
        }
        
        try:
            # Test basic connectivity
            with get_monitored_db_session() as session:
                session.execute(text("SELECT 1"))
                health_status["status"] = "healthy"
            
            # Get pool status
            pool_stats = db_health_checker.get_connection_pool_stats()
            health_status["connection_pool"] = pool_stats
            
            # Get performance metrics
            perf_summary = db_monitor.get_performance_summary()
            health_status["query_performance"] = perf_summary["overall_stats"]
            health_status["recent_errors"] = [
                q for q in db_monitor.query_history 
                if not q.success and (datetime.now() - q.timestamp) <= timedelta(minutes=30)
            ][-10:]  # Last 10 errors in 30 minutes
            
            # Get optimization recommendations
            health_status["recommendations"] = db_monitor.get_query_optimization_suggestions()
            
        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["error"] = str(e)
            logger.error(f"Database health check failed: {e}")
        
        return health_status
    
    @staticmethod
    def get_connection_pool_stats() -> Dict[str, Any]:
        """Get detailed connection pool statistics"""
        try:
            pool = base_engine.pool
            
            # Get basic pool metrics (some methods may not be available on all pool types)
            pool_size = getattr(pool, 'size', lambda: 0)()
            checked_out = getattr(pool, 'checkedout', lambda: 0)()
            overflow = getattr(pool, 'overflow', lambda: 0)()
            checked_in = getattr(pool, 'checkedin', lambda: 0)()
            
            # invalidated() method doesn't exist on QueuePool, use 0 as default
            invalid_connections = 0
            if hasattr(pool, 'invalidated'):
                try:
                    invalid_connections = pool.invalidated()
                except:
                    invalid_connections = 0
            
            return {
                "pool_size": pool_size,
                "max_overflow": overflow,
                "checked_out": checked_out,
                "checked_in": checked_in,
                "invalid_connections": invalid_connections,
                "total_capacity": pool_size + overflow,
                "utilization_percent": (
                    (checked_out / pool_size * 100) 
                    if pool_size > 0 else 0
                ),
                "available_connections": pool_size - checked_out
            }
        except Exception as e:
            logger.error(f"Failed to get pool stats: {e}")
            return {"error": str(e)}


# Initialize database health checker
db_health_checker = DatabaseHealthChecker()

# Log initialization
logger.info(f"Database engine initialized with pool size: {settings.DB_POOL_SIZE}, "
           f"max overflow: {settings.DB_MAX_OVERFLOW}")
logger.info("Database monitoring and performance tracking enabled")