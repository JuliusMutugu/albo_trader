"""
Performance measurement utilities for monitoring system performance.

This module provides decorators and utilities for measuring execution time
and performance metrics throughout the trading system.
"""

import time
import logging
import functools
from typing import Callable, Any


def measure_time(func: Callable) -> Callable:
    """
    Decorator to measure function execution time.
    
    Args:
        func: Function to measure
        
    Returns:
        Wrapped function with timing measurement
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start_time = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            execution_time = time.perf_counter() - start_time
            
            logger = logging.getLogger(func.__module__)
            logger.debug(f"{func.__name__} executed in {execution_time:.4f} seconds")
            
            return result
        except Exception as e:
            execution_time = time.perf_counter() - start_time
            logger = logging.getLogger(func.__module__)
            logger.error(f"{func.__name__} failed after {execution_time:.4f} seconds: {e}")
            raise
            
    return wrapper


async def measure_time_async(func: Callable) -> Callable:
    """
    Decorator to measure async function execution time.
    
    Args:
        func: Async function to measure
        
    Returns:
        Wrapped async function with timing measurement
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        start_time = time.perf_counter()
        try:
            result = await func(*args, **kwargs)
            execution_time = time.perf_counter() - start_time
            
            logger = logging.getLogger(func.__module__)
            logger.debug(f"{func.__name__} executed in {execution_time:.4f} seconds")
            
            return result
        except Exception as e:
            execution_time = time.perf_counter() - start_time
            logger = logging.getLogger(func.__module__)
            logger.error(f"{func.__name__} failed after {execution_time:.4f} seconds: {e}")
            raise
            
    return wrapper
