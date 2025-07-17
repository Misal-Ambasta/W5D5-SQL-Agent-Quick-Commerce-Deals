"""
Comprehensive monitoring and metrics collection system
"""
import time
import asyncio
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict, deque
from dataclasses import dataclass
import threading
from contextlib import contextmanager

from app.core.logging import logger


@dataclass
class QueryMetric:
    """Individual query execution metric"""
    sql: str
    execution_time: float
    timestamp: datetime
    success: bool
    error_message: Optional[str] = None
    affected_rows: Optional[int] = None


@dataclass
class SystemMetrics:
    """System-level performance metrics"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    active_connections: int
    queries_per_minute: float
    cache_hit_ratio: float
    error_rate: float


class DatabaseMonitor:
    """Database query and performance monitoring"""
    
    def __init__(self):
        self.query_history: deque = deque(maxlen=10000)
        self.slow_queries: deque = deque(maxlen=1000)
        self.error_queries: deque = deque(maxlen=1000)
        self.total_queries = 0
        self.total_errors = 0
        self.slow_query_threshold = 1.0
        self._lock = threading.Lock()
        self.hourly_stats = defaultdict(lambda: {'queries': 0, 'errors': 0, 'total_time': 0})
        self.daily_stats = defaultdict(lambda: {'queries': 0, 'errors': 0, 'total_time': 0})
    
    def record_query(self, sql: str, execution_time: float, success: bool = True, 
                    error_message: str = None, affected_rows: int = None):
        """Record a database query execution"""
        with self._lock:
            timestamp = datetime.utcnow()
            metric = QueryMetric(
                sql=sql,
                execution_time=execution_time,
                timestamp=timestamp,
                success=success,
                error_message=error_message,
                affected_rows=affected_rows
            )
            
            self.query_history.append(metric)
            self.total_queries += 1
            
            if not success:
                self.error_queries.append(metric)
                self.total_errors += 1
                logger.error(f"Database query failed: {error_message}")
            
            if execution_time > self.slow_query_threshold:
                self.slow_queries.append(metric)
                logger.warning(f"Slow query detected: {execution_time:.2f}s")
            
            hour_key = timestamp.strftime('%Y-%m-%d-%H')
            day_key = timestamp.strftime('%Y-%m-%d')
            
            self.hourly_stats[hour_key]['queries'] += 1
            self.hourly_stats[hour_key]['total_time'] += execution_time
            self.daily_stats[day_key]['queries'] += 1
            self.daily_stats[day_key]['total_time'] += execution_time
            
            if not success:
                self.hourly_stats[hour_key]['errors'] += 1
                self.daily_stats[day_key]['errors'] += 1
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        with self._lock:
            if not self.query_history:
                return {
                    'overall_stats': {
                        'total_queries': 0,
                        'total_errors': 0,
                        'error_rate': 0,
                        'avg_execution_time': 0
                    },
                    'recent_performance': {
                        'queries_last_hour': 0,
                        'errors_last_hour': 0,
                        'avg_response_time': 0
                    }
                }
            
            total_time = sum(q.execution_time for q in self.query_history)
            avg_execution_time = total_time / len(self.query_history) if self.query_history else 0
            error_rate = self.total_errors / self.total_queries if self.total_queries > 0 else 0
            
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            recent_queries = [q for q in self.query_history if q.timestamp > one_hour_ago]
            recent_errors = [q for q in recent_queries if not q.success]
            
            recent_avg_time = (
                sum(q.execution_time for q in recent_queries) / len(recent_queries)
                if recent_queries else 0
            )
            
            return {
                'overall_stats': {
                    'total_queries': self.total_queries,
                    'total_errors': self.total_errors,
                    'error_rate': error_rate,
                    'avg_execution_time': avg_execution_time
                },
                'recent_performance': {
                    'queries_last_hour': len(recent_queries),
                    'errors_last_hour': len(recent_errors),
                    'avg_response_time': recent_avg_time
                }
            }
    
    def get_slow_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent slow queries"""
        with self._lock:
            return [
                {
                    'sql': q.sql,
                    'execution_time': q.execution_time,
                    'timestamp': q.timestamp.isoformat(),
                    'affected_rows': q.affected_rows
                }
                for q in sorted(self.slow_queries, key=lambda x: x.execution_time, reverse=True)[:limit]
            ]
    
    def get_query_optimization_suggestions(self) -> List[str]:
        """Generate query optimization suggestions"""
        suggestions = []
        with self._lock:
            if len(self.slow_queries) > 5:
                suggestions.append("Consider adding indexes for frequently slow queries")
            
            error_rate = self.total_errors / self.total_queries if self.total_queries > 0 else 0
            if error_rate > 0.05:
                suggestions.append("High error rate detected - review query validation")
        
        return suggestions


class CacheMonitor:
    """Cache performance monitoring"""
    
    def __init__(self):
        self.cache_hits = 0
        self.cache_misses = 0
        self.cache_sets = 0
        self.cache_deletes = 0
        self._lock = threading.Lock()
        self.hourly_cache_stats = defaultdict(lambda: {
            'hits': 0, 'misses': 0, 'sets': 0, 'deletes': 0
        })
    
    def record_cache_hit(self):
        """Record a cache hit"""
        with self._lock:
            self.cache_hits += 1
            hour_key = datetime.utcnow().strftime('%Y-%m-%d-%H')
            self.hourly_cache_stats[hour_key]['hits'] += 1
    
    def record_cache_miss(self):
        """Record a cache miss"""
        with self._lock:
            self.cache_misses += 1
            hour_key = datetime.utcnow().strftime('%Y-%m-%d-%H')
            self.hourly_cache_stats[hour_key]['misses'] += 1
    
    def record_cache_set(self):
        """Record a cache set operation"""
        with self._lock:
            self.cache_sets += 1
            hour_key = datetime.utcnow().strftime('%Y-%m-%d-%H')
            self.hourly_cache_stats[hour_key]['sets'] += 1
    
    def record_cache_delete(self):
        """Record a cache delete operation"""
        with self._lock:
            self.cache_deletes += 1
            hour_key = datetime.utcnow().strftime('%Y-%m-%d-%H')
            self.hourly_cache_stats[hour_key]['deletes'] += 1
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        with self._lock:
            total_operations = self.cache_hits + self.cache_misses
            hit_ratio = self.cache_hits / total_operations if total_operations > 0 else 0
            
            current_hour = datetime.utcnow().strftime('%Y-%m-%d-%H')
            recent_stats = self.hourly_cache_stats[current_hour]
            recent_total = recent_stats['hits'] + recent_stats['misses']
            recent_hit_ratio = recent_stats['hits'] / recent_total if recent_total > 0 else 0
            
            return {
                'performance': {
                    'cache_hits': self.cache_hits,
                    'cache_misses': self.cache_misses,
                    'hit_ratio': hit_ratio,
                    'total_operations': total_operations
                },
                'operations': {
                    'cache_sets': self.cache_sets,
                    'cache_deletes': self.cache_deletes
                },
                'recent_performance': {
                    'hits_last_hour': recent_stats['hits'],
                    'misses_last_hour': recent_stats['misses'],
                    'hit_ratio_last_hour': recent_hit_ratio
                }
            }


class SystemMonitor:
    """System resource monitoring"""
    
    def __init__(self):
        self.metrics_history: deque = deque(maxlen=1440)
        self._monitoring = False
        self._monitor_task = None
    
    async def start_monitoring(self, interval_seconds: int = 60):
        """Start continuous system monitoring"""
        self._monitoring = True
        self._monitor_task = asyncio.create_task(self._monitor_loop(interval_seconds))
        logger.info("System monitoring started")
    
    async def stop_monitoring(self):
        """Stop system monitoring"""
        self._monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("System monitoring stopped")
    
    async def _monitor_loop(self, interval_seconds: int):
        """Main monitoring loop"""
        while self._monitoring:
            try:
                metrics = await self._collect_system_metrics()
                self.metrics_history.append(metrics)
                
                if metrics.cpu_percent > 80:
                    logger.warning(f"High CPU usage: {metrics.cpu_percent:.1f}%")
                if metrics.memory_percent > 85:
                    logger.warning(f"High memory usage: {metrics.memory_percent:.1f}%")
                
                await asyncio.sleep(interval_seconds)
            except Exception as e:
                logger.error(f"Error in system monitoring loop: {e}")
                await asyncio.sleep(interval_seconds)
    
    async def _collect_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        active_connections = getattr(self, '_active_connections', 0)
        queries_per_minute = getattr(self, '_queries_per_minute', 0)
        cache_hit_ratio = getattr(self, '_cache_hit_ratio', 0)
        error_rate = getattr(self, '_error_rate', 0)
        
        return SystemMetrics(
            timestamp=datetime.utcnow(),
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            disk_usage_percent=disk.percent,
            active_connections=active_connections,
            queries_per_minute=queries_per_minute,
            cache_hit_ratio=cache_hit_ratio,
            error_rate=error_rate
        )
    
    def update_database_metrics(self, active_connections: int, queries_per_minute: float, error_rate: float):
        """Update database-related metrics"""
        self._active_connections = active_connections
        self._queries_per_minute = queries_per_minute
        self._error_rate = error_rate
    
    def update_cache_metrics(self, hit_ratio: float):
        """Update cache-related metrics"""
        self._cache_hit_ratio = hit_ratio
    
    def get_current_metrics(self) -> Optional[SystemMetrics]:
        """Get the most recent system metrics"""
        return self.metrics_history[-1] if self.metrics_history else None
    
    def get_metrics_summary(self, hours: int = 1) -> Dict[str, Any]:
        """Get system metrics summary"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        recent_metrics = [m for m in self.metrics_history if m.timestamp > cutoff_time]
        
        if not recent_metrics:
            return {}
        
        return {
            'period_hours': hours,
            'data_points': len(recent_metrics),
            'cpu': {
                'avg': sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics),
                'max': max(m.cpu_percent for m in recent_metrics),
                'min': min(m.cpu_percent for m in recent_metrics)
            },
            'memory': {
                'avg': sum(m.memory_percent for m in recent_metrics) / len(recent_metrics),
                'max': max(m.memory_percent for m in recent_metrics),
                'min': min(m.memory_percent for m in recent_metrics)
            }
        }


class AlertManager:
    """Alert and notification management"""
    
    def __init__(self):
        self.alert_thresholds = {
            'cpu_percent': 80.0,
            'memory_percent': 85.0,
            'error_rate': 0.05,
            'cache_hit_ratio_min': 0.7
        }
        self.active_alerts = {}
        self.alert_history: deque = deque(maxlen=1000)
    
    def check_thresholds(self, metrics: SystemMetrics, db_stats: Dict, cache_stats: Dict):
        """Check all metrics against thresholds and generate alerts"""
        alerts = []
        
        if metrics.cpu_percent > self.alert_thresholds['cpu_percent']:
            alerts.append({
                'type': 'cpu_high',
                'severity': 'warning',
                'message': f"High CPU usage: {metrics.cpu_percent:.1f}%",
                'value': metrics.cpu_percent,
                'threshold': self.alert_thresholds['cpu_percent']
            })
        
        if metrics.memory_percent > self.alert_thresholds['memory_percent']:
            alerts.append({
                'type': 'memory_high',
                'severity': 'warning',
                'message': f"High memory usage: {metrics.memory_percent:.1f}%",
                'value': metrics.memory_percent,
                'threshold': self.alert_thresholds['memory_percent']
            })
        
        for alert in alerts:
            self._process_alert(alert)
    
    def _process_alert(self, alert: Dict):
        """Process and log an alert"""
        alert_key = f"{alert['type']}_{alert['value']}"
        alert['timestamp'] = datetime.utcnow()
        
        if alert_key in self.active_alerts:
            last_alert_time = self.active_alerts[alert_key]
            if datetime.utcnow() - last_alert_time < timedelta(minutes=5):
                return
        
        self.active_alerts[alert_key] = alert['timestamp']
        self.alert_history.append(alert)
        
        log_level = logger.critical if alert['severity'] == 'critical' else logger.warning
        log_level(f"ALERT: {alert['message']}")
    
    def get_active_alerts(self) -> List[Dict]:
        """Get currently active alerts"""
        cutoff_time = datetime.utcnow() - timedelta(hours=1)
        return [alert for alert in self.alert_history if alert['timestamp'] > cutoff_time]


# Global monitoring instances
db_monitor = DatabaseMonitor()
cache_monitor = CacheMonitor()
system_monitor = SystemMonitor()
alert_manager = AlertManager()


@contextmanager
def monitor_database_query(sql: str):
    """Context manager for monitoring database queries"""
    start_time = time.time()
    success = True
    error_message = None
    
    try:
        yield
    except Exception as e:
        success = False
        error_message = str(e)
        raise
    finally:
        execution_time = time.time() - start_time
        db_monitor.record_query(
            sql=sql,
            execution_time=execution_time,
            success=success,
            error_message=error_message
        )


def get_comprehensive_metrics() -> Dict[str, Any]:
    """Get comprehensive system metrics from all monitors"""
    db_stats = db_monitor.get_performance_summary()
    cache_stats = cache_monitor.get_cache_statistics()
    system_metrics = system_monitor.get_current_metrics()
    active_alerts = alert_manager.get_active_alerts()
    
    if system_metrics:
        system_monitor.update_database_metrics(
            active_connections=system_metrics.active_connections,
            queries_per_minute=db_stats.get('recent_performance', {}).get('queries_last_hour', 0) / 60,
            error_rate=db_stats.get('overall_stats', {}).get('error_rate', 0)
        )
        system_monitor.update_cache_metrics(
            hit_ratio=cache_stats.get('performance', {}).get('hit_ratio', 0)
        )
        
        alert_manager.check_thresholds(system_metrics, db_stats, cache_stats)
    
    return {
        'timestamp': datetime.utcnow().isoformat(),
        'database': db_stats,
        'cache': cache_stats,
        'system': {
            'current': system_metrics.__dict__ if system_metrics else None,
            'summary': system_monitor.get_metrics_summary(hours=1)
        },
        'alerts': {
            'active': active_alerts,
            'total_count': len(active_alerts)
        }
    }