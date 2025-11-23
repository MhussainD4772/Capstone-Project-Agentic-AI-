"""Tracing module.

This module provides lightweight tracing utilities for timing and logging
pipeline stages in the QA Sentinel project. It includes:
- TraceSpan context manager for manual stage tracing
- trace_stage decorator for automatic function tracing
"""

import time
import inspect
from contextlib import contextmanager
from typing import Callable, Any, Awaitable, Optional
from logging import Logger
from functools import wraps
from observability.logging_config import get_logger


@contextmanager
def TraceSpan(logger: Optional[Logger] = None, stage_name: str = "unknown"):
    """
    Context manager for tracing pipeline stages.
    
    Logs start and end times, calculates duration, and handles exceptions.
    Uses monotonic time for accurate duration measurement.
    
    Args:
        logger: Logger instance (defaults to "qa-sentinel" logger if None)
        stage_name: Name of the stage being traced
    
    Example:
        >>> logger = get_logger("orchestrator")
        >>> with TraceSpan(logger, stage_name="planner"):
        ...     # run planner call
        ...     result = planner.run()
    
    Raises:
        Re-raises any exception that occurs within the context
    """
    if logger is None:
        logger = get_logger("qa-sentinel")
    
    # Log start
    logger.info(f"Starting stage: {stage_name}")
    
    # Record start time using monotonic clock
    start_time = time.monotonic()
    
    try:
        yield
        # Calculate duration on successful exit
        end_time = time.monotonic()
        duration_ms = (end_time - start_time) * 1000
        logger.info(f"Finished stage: {stage_name} in {duration_ms:.2f} ms")
    
    except Exception as e:
        # Calculate duration even on exception
        end_time = time.monotonic()
        duration_ms = (end_time - start_time) * 1000
        logger.error(
            f"Failed stage: {stage_name} after {duration_ms:.2f} ms - {type(e).__name__}: {str(e)}"
        )
        # Re-raise the exception
        raise


def trace_stage(stage_name: str):
    """
    Decorator to trace async pipeline functions.
    
    Automatically logs start/end times and duration for async functions.
    Works with both async and sync functions.
    
    Args:
        stage_name: Name of the stage being traced
    
    Example:
        >>> @trace_stage("planner")
        ... async def run_planner():
        ...     # planner logic
        ...     return result
    
    Returns:
        Decorated function with tracing enabled
    """
    def decorator(func: Callable) -> Callable:
        # Check if function is async using inspect
        is_async = inspect.iscoroutinefunction(func)
        
        if is_async:
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                logger = get_logger(func.__module__ or "qa-sentinel")
                with TraceSpan(logger, stage_name=stage_name):
                    return await func(*args, **kwargs)
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                logger = get_logger(func.__module__ or "qa-sentinel")
                with TraceSpan(logger, stage_name=stage_name):
                    return func(*args, **kwargs)
            return sync_wrapper
    
    return decorator

