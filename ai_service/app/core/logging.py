"""
Advanced logging configuration for SchemaSculpt AI Service.
Provides structured logging with correlation IDs and performance metrics.
"""

import asyncio
import logging
import json
import time
import uuid
from contextvars import ContextVar
from typing import Any, Dict, Optional
from functools import wraps

from .config import settings


# Context variable for request correlation
correlation_id: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        log_entry = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add correlation ID if available
        if correlation_id.get():
            log_entry["correlation_id"] = correlation_id.get()

        # Add extra fields
        if hasattr(record, "extra"):
            log_entry.update(record.extra)

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, default=str)


def setup_logging() -> None:
    """Configure application logging."""

    # Create logger
    logger = logging.getLogger("schemasculpt_ai")
    logger.setLevel(getattr(logging, settings.log_level.upper()))

    # Remove default handlers
    logger.handlers.clear()

    # Create console handler
    console_handler = logging.StreamHandler()

    if settings.log_format.lower() == "json":
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Set library log levels
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn").setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name."""
    return logging.getLogger(f"schemasculpt_ai.{name}")


def log_performance(func_name: str = None):
    """Decorator to log function performance metrics."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            func_name_actual = func_name or func.__name__
            logger = get_logger("performance")

            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(
                    f"Function {func_name_actual} completed",
                    extra={
                        "function": func_name_actual,
                        "duration_ms": round(duration * 1000, 2),
                        "status": "success"
                    }
                )
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"Function {func_name_actual} failed",
                    extra={
                        "function": func_name_actual,
                        "duration_ms": round(duration * 1000, 2),
                        "status": "error",
                        "error": str(e)
                    }
                )
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            func_name_actual = func_name or func.__name__
            logger = get_logger("performance")

            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(
                    f"Function {func_name_actual} completed",
                    extra={
                        "function": func_name_actual,
                        "duration_ms": round(duration * 1000, 2),
                        "status": "success"
                    }
                )
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"Function {func_name_actual} failed",
                    extra={
                        "function": func_name_actual,
                        "duration_ms": round(duration * 1000, 2),
                        "status": "error",
                        "error": str(e)
                    }
                )
                raise

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


def set_correlation_id(cid: str = None) -> str:
    """Set correlation ID for request tracking."""
    if cid is None:
        cid = str(uuid.uuid4())
    correlation_id.set(cid)
    return cid


# Setup logging on import
setup_logging()