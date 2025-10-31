"""
Logging configuration and utilities.
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional
import sys
from datetime import datetime

from config import settings


def setup_logging(
    log_level: str = None,
    log_file: str = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Set up logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file
        max_bytes: Maximum log file size before rotation
        backup_count: Number of backup files to keep
        
    Returns:
        Configured logger instance
    """
    # Use settings if not provided
    log_level = log_level or settings.log_level
    log_file = log_file or settings.log_file
    
    # Ensure log directory exists
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler with rotation
    if log_file:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get logger instance for specific module."""
    return logging.getLogger(name)


class BotLogger:
    """Enhanced logger for bot operations."""
    
    def __init__(self, name: str = "bot"):
        """Initialize bot logger."""
        self.logger = logging.getLogger(name)
    
    def log_user_action(self, user_id: int, action: str, details: str = None):
        """Log user action with structured format."""
        message = f"User {user_id} - {action}"
        if details:
            message += f" - {details}"
        self.logger.info(message)
    
    def log_admin_action(self, admin_id: int, action: str, target_id: int = None, details: str = None):
        """Log admin action."""
        message = f"Admin {admin_id} - {action}"
        if target_id:
            message += f" - Target: {target_id}"
        if details:
            message += f" - {details}"
        self.logger.info(message)
    
    def log_payment(self, user_id: int, amount: float, currency: str, provider: str, status: str):
        """Log payment operation."""
        message = f"Payment - User: {user_id}, Amount: {amount} {currency}, Provider: {provider}, Status: {status}"
        self.logger.info(message)
    
    def log_error(self, error: Exception, context: str = None, user_id: int = None):
        """Log error with context."""
        message = f"Error in {context or 'unknown context'}"
        if user_id:
            message += f" for user {user_id}"
        message += f": {str(error)}"
        self.logger.error(message, exc_info=True)
    
    def log_api_call(self, service: str, endpoint: str, status: str, duration: float = None):
        """Log external API call."""
        message = f"API Call - {service} {endpoint} - {status}"
        if duration:
            message += f" - {duration:.2f}s"
        self.logger.info(message)
    
    def log_webhook(self, provider: str, event_type: str, status: str, details: str = None):
        """Log webhook events."""
        message = f"Webhook - {provider} - {event_type} - {status}"
        if details:
            message += f" - {details}"
        self.logger.info(message)
    
    def log_moderation(self, ad_id: int, moderator_id: int, action: str, reason: str = None):
        """Log moderation actions."""
        message = f"Moderation - Ad {ad_id} - {action} by {moderator_id}"
        if reason:
            message += f" - Reason: {reason}"
        self.logger.info(message)


class SecurityLogger:
    """Logger for security events."""
    
    def __init__(self):
        """Initialize security logger."""
        self.logger = logging.getLogger("security")
        
        # Create separate handler for security logs
        security_log_path = Path("logs") / "security.log"
        security_log_path.parent.mkdir(exist_ok=True)
        
        handler = logging.handlers.RotatingFileHandler(
            security_log_path,
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=10
        )
        
        formatter = logging.Formatter(
            '%(asctime)s - SECURITY - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.WARNING)
    
    def log_failed_auth(self, user_id: int, reason: str):
        """Log failed authentication."""
        self.logger.warning(f"Failed auth - User {user_id} - {reason}")
    
    def log_banned_user_attempt(self, user_id: int, action: str):
        """Log banned user activity."""
        self.logger.warning(f"Banned user attempt - User {user_id} - {action}")
    
    def log_suspicious_activity(self, user_id: int, activity: str, details: str = None):
        """Log suspicious activity."""
        message = f"Suspicious activity - User {user_id} - {activity}"
        if details:
            message += f" - {details}"
        self.logger.warning(message)
    
    def log_admin_access(self, admin_id: int, action: str):
        """Log admin access."""
        self.logger.info(f"Admin access - {admin_id} - {action}")


class PerformanceLogger:
    """Logger for performance monitoring."""
    
    def __init__(self):
        """Initialize performance logger."""
        self.logger = logging.getLogger("performance")
    
    def log_slow_operation(self, operation: str, duration: float, threshold: float = 5.0):
        """Log slow operations."""
        if duration > threshold:
            self.logger.warning(f"Slow operation - {operation} - {duration:.2f}s")
    
    def log_database_query(self, query: str, duration: float, rows: int = None):
        """Log database query performance."""
        message = f"DB Query - {duration:.3f}s"
        if rows is not None:
            message += f" - {rows} rows"
        if duration > 1.0:  # Log slow queries
            message += f" - SLOW: {query[:100]}..."
            self.logger.warning(message)
        else:
            self.logger.debug(message)


def create_file_logger(name: str, filename: str, level: str = "INFO") -> logging.Logger:
    """Create a separate file logger for specific purposes."""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Ensure log directory exists
    log_path = Path("logs") / filename
    log_path.parent.mkdir(exist_ok=True)
    
    # File handler
    handler = logging.handlers.RotatingFileHandler(
        log_path,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger


# Global logger instances
bot_logger = BotLogger()
security_logger = SecurityLogger()
performance_logger = PerformanceLogger()


def setup_admin_notification_logger(admin_chat_id: Optional[int] = None):
    """Set up logger that sends critical errors to admin."""
    if not admin_chat_id:
        admin_chat_id = settings.admin_id
    
    # This would require a Telegram handler implementation
    # For now, just log to file
    admin_logger = create_file_logger("admin_notifications", "admin_alerts.log", "ERROR")
    return admin_logger


# Context manager for timing operations
class TimingContext:
    """Context manager for timing operations."""
    
    def __init__(self, operation_name: str, logger: logging.Logger = None):
        """Initialize timing context."""
        self.operation_name = operation_name
        self.logger = logger or performance_logger.logger
        self.start_time = None
    
    def __enter__(self):
        """Start timing."""
        self.start_time = datetime.now()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """End timing and log."""
        if self.start_time:
            duration = (datetime.now() - self.start_time).total_seconds()
            self.logger.info(f"Operation '{self.operation_name}' took {duration:.3f}s")
            
            # Log to performance logger if slow
            performance_logger.log_slow_operation(self.operation_name, duration)


def log_function_call(func):
    """Decorator to log function calls."""
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
        
        try:
            with TimingContext(f"{func.__module__}.{func.__name__}"):
                result = func(*args, **kwargs)
            logger.debug(f"{func.__name__} completed successfully")
            return result
        except Exception as e:
            logger.error(f"{func.__name__} failed: {e}", exc_info=True)
            raise
    
    return wrapper


# Initialize logging on import
setup_logging()