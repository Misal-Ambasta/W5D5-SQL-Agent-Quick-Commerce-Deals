"""
Enhanced logging configuration for the application with comprehensive monitoring
"""
import logging
import logging.handlers
import structlog
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

from app.core.config import settings


class APIUsageLogger:
    """Logger for API usage analytics and rate limiting monitoring"""
    
    def __init__(self):
        self.usage_stats = {}
        self.rate_limit_violations = []
        self.endpoint_performance = {}
    
    def log_api_request(self, endpoint: str, method: str, client_ip: str, 
                       response_time: float, status_code: int, user_agent: str = None):
        """Log API request for analytics"""
        timestamp = datetime.utcnow()
        
        # Update usage stats
        key = f"{method}:{endpoint}"
        if key not in self.usage_stats:
            self.usage_stats[key] = {
                'total_requests': 0,
                'success_count': 0,
                'error_count': 0,
                'total_response_time': 0,
                'unique_ips': set(),
                'first_seen': timestamp,
                'last_seen': timestamp
            }
        
        stats = self.usage_stats[key]
        stats['total_requests'] += 1
        stats['total_response_time'] += response_time
        stats['unique_ips'].add(client_ip)
        stats['last_seen'] = timestamp
        
        if 200 <= status_code < 400:
            stats['success_count'] += 1
        else:
            stats['error_count'] += 1
        
        # Log the request
        logger.info(
            f"API Request: {method} {endpoint}",
            extra={
                'event_type': 'api_request',
                'endpoint': endpoint,
                'method': method,
                'client_ip': client_ip,
                'response_time': response_time,
                'status_code': status_code,
                'user_agent': user_agent,
                'timestamp': timestamp.isoformat()
            }
        )
    
    def log_rate_limit_violation(self, client_ip: str, endpoint: str, limit: str):
        """Log rate limit violations"""
        violation = {
            'client_ip': client_ip,
            'endpoint': endpoint,
            'limit': limit,
            'timestamp': datetime.utcnow()
        }
        self.rate_limit_violations.append(violation)
        
        logger.warning(
            f"Rate limit exceeded: {client_ip} on {endpoint}",
            extra={
                'event_type': 'rate_limit_violation',
                'client_ip': client_ip,
                'endpoint': endpoint,
                'limit': limit,
                'timestamp': violation['timestamp'].isoformat()
            }
        )
    
    def get_usage_analytics(self) -> Dict[str, Any]:
        """Get comprehensive API usage analytics"""
        analytics = {}
        
        for endpoint, stats in self.usage_stats.items():
            avg_response_time = (
                stats['total_response_time'] / stats['total_requests'] 
                if stats['total_requests'] > 0 else 0
            )
            
            analytics[endpoint] = {
                'total_requests': stats['total_requests'],
                'success_rate': stats['success_count'] / stats['total_requests'] if stats['total_requests'] > 0 else 0,
                'error_rate': stats['error_count'] / stats['total_requests'] if stats['total_requests'] > 0 else 0,
                'avg_response_time': avg_response_time,
                'unique_users': len(stats['unique_ips']),
                'first_seen': stats['first_seen'].isoformat(),
                'last_seen': stats['last_seen'].isoformat()
            }
        
        return {
            'endpoints': analytics,
            'rate_limit_violations': len(self.rate_limit_violations),
            'total_unique_ips': len(set(ip for stats in self.usage_stats.values() for ip in stats['unique_ips']))
        }


class ErrorTracker:
    """Error tracking and alerting system"""
    
    def __init__(self):
        self.error_counts = {}
        self.critical_errors = []
        self.error_patterns = {}
    
    def track_error(self, error_type: str, error_message: str, context: Dict[str, Any] = None):
        """Track application errors"""
        timestamp = datetime.utcnow()
        
        # Update error counts
        if error_type not in self.error_counts:
            self.error_counts[error_type] = 0
        self.error_counts[error_type] += 1
        
        # Track error patterns
        error_key = f"{error_type}:{error_message[:100]}"
        if error_key not in self.error_patterns:
            self.error_patterns[error_key] = {
                'count': 0,
                'first_seen': timestamp,
                'last_seen': timestamp,
                'contexts': []
            }
        
        pattern = self.error_patterns[error_key]
        pattern['count'] += 1
        pattern['last_seen'] = timestamp
        if context and len(pattern['contexts']) < 5:  # Keep last 5 contexts
            pattern['contexts'].append(context)
        
        # Check if this is a critical error pattern
        if pattern['count'] > 10:  # More than 10 occurrences
            self.critical_errors.append({
                'error_type': error_type,
                'error_message': error_message,
                'count': pattern['count'],
                'first_seen': pattern['first_seen'],
                'last_seen': pattern['last_seen']
            })
        
        # Log the error
        logger.error(
            f"Application error: {error_type}",
            extra={
                'event_type': 'application_error',
                'error_type': error_type,
                'error_message': error_message,
                'context': context,
                'timestamp': timestamp.isoformat()
            }
        )
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get error tracking summary"""
        return {
            'error_counts': self.error_counts,
            'critical_errors': self.critical_errors[-10:],  # Last 10 critical errors
            'total_error_types': len(self.error_counts),
            'total_errors': sum(self.error_counts.values())
        }


def setup_file_logging():
    """Set up file-based logging with rotation"""
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Set up rotating file handler for application logs
    app_handler = logging.handlers.RotatingFileHandler(
        log_dir / "app.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    app_handler.setLevel(logging.INFO)
    
    # Set up rotating file handler for error logs
    error_handler = logging.handlers.RotatingFileHandler(
        log_dir / "errors.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    
    # Set up rotating file handler for API access logs
    api_handler = logging.handlers.RotatingFileHandler(
        log_dir / "api_access.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    api_handler.setLevel(logging.INFO)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    app_handler.setFormatter(detailed_formatter)
    error_handler.setFormatter(detailed_formatter)
    api_handler.setFormatter(detailed_formatter)
    
    return app_handler, error_handler, api_handler


def configure_logging():
    """Configure comprehensive structured logging for the application"""
    
    # Set up file logging
    app_handler, error_handler, api_handler = setup_file_logging()
    
    # Configure structlog with enhanced processors
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.dev.ConsoleRenderer() if sys.stdout.isatty() else structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            app_handler
        ]
    )
    
    # Add error handler to root logger
    logging.getLogger().addHandler(error_handler)
    
    # Set up specific loggers
    api_logger = logging.getLogger('api_access')
    api_logger.addHandler(api_handler)
    api_logger.setLevel(logging.INFO)
    
    # Reduce noise from third-party libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)


# Initialize logger and tracking systems
logger = structlog.get_logger()
api_usage_logger = APIUsageLogger()
error_tracker = ErrorTracker()