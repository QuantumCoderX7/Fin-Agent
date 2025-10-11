"""
Retry utilities with exponential backoff for external API calls.

This module provides decorators and utilities for implementing retry logic
with exponential backoff for handling transient failures in external services.
"""

import asyncio
import functools
import random
import time
from typing import Callable, Type, Tuple, Optional, Any, Union, List
from app.config.logging import get_logger
from app.utils.exceptions import (
    DataSourceException,
    RateLimitException,
    TimeoutException,
    FinancialAgentException
)

logger = get_logger(__name__)


class RetryConfig:
    """Configuration for retry behavior."""
    
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retryable_exceptions: Optional[Tuple[Type[Exception], ...]] = None
    ):
        """
        Initialize retry configuration.
        
        Args:
            max_attempts: Maximum number of retry attempts
            base_delay: Base delay in seconds before first retry
            max_delay: Maximum delay in seconds between retries
            exponential_base: Base for exponential backoff calculation
            jitter: Whether to add random jitter to delays
            retryable_exceptions: Tuple of exception types that should trigger retries
        """
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions or (
            DataSourceException,
            RateLimitException,
            TimeoutException,
            ConnectionError,
            TimeoutError,
        )
    
    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for a given attempt number.
        
        Args:
            attempt: Current attempt number (0-based)
            
        Returns:
            Delay in seconds
        """
        # Calculate exponential backoff
        delay = self.base_delay * (self.exponential_base ** attempt)
        
        # Apply maximum delay limit
        delay = min(delay, self.max_delay)
        
        # Add jitter if enabled
        if self.jitter:
            # Add random jitter of ±25%
            jitter_range = delay * 0.25
            delay += random.uniform(-jitter_range, jitter_range)
        
        return max(0, delay)
    
    def should_retry(self, exception: Exception, attempt: int) -> bool:
        """
        Determine if an exception should trigger a retry.
        
        Args:
            exception: The exception that occurred
            attempt: Current attempt number (0-based)
            
        Returns:
            True if should retry, False otherwise
        """
        # Check if we've exceeded max attempts
        if attempt >= self.max_attempts:
            return False
        
        # Check if exception type is retryable
        if not isinstance(exception, self.retryable_exceptions):
            return False
        
        # Special handling for rate limit exceptions
        if isinstance(exception, RateLimitException):
            # Always retry rate limit exceptions (up to max attempts)
            return True
        
        # Special handling for data source exceptions
        if isinstance(exception, DataSourceException):
            # Check if it's a temporary failure (5xx status codes)
            if hasattr(exception, 'details') and 'status_code' in exception.details:
                status_code = exception.details['status_code']
                # Retry on 5xx server errors, but not on 4xx client errors
                return 500 <= status_code < 600
            # If no status code, assume it's retryable
            return True
        
        return True


def retry_with_backoff(
    config: Optional[RetryConfig] = None,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: Optional[Tuple[Type[Exception], ...]] = None
):
    """
    Decorator for adding retry logic with exponential backoff to functions.
    
    Args:
        config: RetryConfig instance (if provided, other parameters are ignored)
        max_attempts: Maximum number of retry attempts
        base_delay: Base delay in seconds before first retry
        max_delay: Maximum delay in seconds between retries
        exponential_base: Base for exponential backoff calculation
        jitter: Whether to add random jitter to delays
        retryable_exceptions: Tuple of exception types that should trigger retries
    """
    if config is None:
        config = RetryConfig(
            max_attempts=max_attempts,
            base_delay=base_delay,
            max_delay=max_delay,
            exponential_base=exponential_base,
            jitter=jitter,
            retryable_exceptions=retryable_exceptions
        )
    
    def decorator(func: Callable) -> Callable:
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                last_exception = None
                
                for attempt in range(config.max_attempts):
                    try:
                        logger.debug(
                            f"Attempting {func.__name__} (attempt {attempt + 1}/{config.max_attempts})"
                        )
                        result = await func(*args, **kwargs)
                        
                        if attempt > 0:
                            logger.info(
                                f"Function {func.__name__} succeeded on attempt {attempt + 1}"
                            )
                        
                        return result
                        
                    except Exception as e:
                        last_exception = e
                        
                        if not config.should_retry(e, attempt):
                            logger.debug(
                                f"Not retrying {func.__name__} due to non-retryable exception: {e}"
                            )
                            break
                        
                        if attempt < config.max_attempts - 1:
                            delay = config.calculate_delay(attempt)
                            logger.warning(
                                f"Function {func.__name__} failed on attempt {attempt + 1}: {e}. "
                                f"Retrying in {delay:.2f} seconds..."
                            )
                            await asyncio.sleep(delay)
                        else:
                            logger.error(
                                f"Function {func.__name__} failed on final attempt {attempt + 1}: {e}"
                            )
                
                # If we get here, all attempts failed
                logger.error(
                    f"Function {func.__name__} failed after {config.max_attempts} attempts. "
                    f"Last exception: {last_exception}"
                )
                raise last_exception
            
            return async_wrapper
        
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                last_exception = None
                
                for attempt in range(config.max_attempts):
                    try:
                        logger.debug(
                            f"Attempting {func.__name__} (attempt {attempt + 1}/{config.max_attempts})"
                        )
                        result = func(*args, **kwargs)
                        
                        if attempt > 0:
                            logger.info(
                                f"Function {func.__name__} succeeded on attempt {attempt + 1}"
                            )
                        
                        return result
                        
                    except Exception as e:
                        last_exception = e
                        
                        if not config.should_retry(e, attempt):
                            logger.debug(
                                f"Not retrying {func.__name__} due to non-retryable exception: {e}"
                            )
                            break
                        
                        if attempt < config.max_attempts - 1:
                            delay = config.calculate_delay(attempt)
                            logger.warning(
                                f"Function {func.__name__} failed on attempt {attempt + 1}: {e}. "
                                f"Retrying in {delay:.2f} seconds..."
                            )
                            time.sleep(delay)
                        else:
                            logger.error(
                                f"Function {func.__name__} failed on final attempt {attempt + 1}: {e}"
                            )
                
                # If we get here, all attempts failed
                logger.error(
                    f"Function {func.__name__} failed after {config.max_attempts} attempts. "
                    f"Last exception: {last_exception}"
                )
                raise last_exception
            
            return sync_wrapper
    
    return decorator


async def retry_async_operation(
    operation: Callable,
    config: Optional[RetryConfig] = None,
    *args,
    **kwargs
) -> Any:
    """
    Retry an async operation with exponential backoff.
    
    Args:
        operation: Async function to retry
        config: Retry configuration
        *args: Arguments to pass to the operation
        **kwargs: Keyword arguments to pass to the operation
        
    Returns:
        Result of the operation
        
    Raises:
        The last exception if all retries fail
    """
    if config is None:
        config = RetryConfig()
    
    @retry_with_backoff(config)
    async def wrapper():
        return await operation(*args, **kwargs)
    
    return await wrapper()


def retry_sync_operation(
    operation: Callable,
    config: Optional[RetryConfig] = None,
    *args,
    **kwargs
) -> Any:
    """
    Retry a sync operation with exponential backoff.
    
    Args:
        operation: Function to retry
        config: Retry configuration
        *args: Arguments to pass to the operation
        **kwargs: Keyword arguments to pass to the operation
        
    Returns:
        Result of the operation
        
    Raises:
        The last exception if all retries fail
    """
    if config is None:
        config = RetryConfig()
    
    @retry_with_backoff(config)
    def wrapper():
        return operation(*args, **kwargs)
    
    return wrapper()


class CircuitBreaker:
    """
    Circuit breaker pattern implementation for external service calls.
    
    This helps prevent cascading failures by temporarily stopping calls
    to a failing service and allowing it time to recover.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: Type[Exception] = Exception
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Time to wait before attempting recovery
            expected_exception: Exception type that counts as failure
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def __call__(self, func: Callable) -> Callable:
        """Decorator to apply circuit breaker to a function."""
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await self._execute_async(func, *args, **kwargs)
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                return self._execute_sync(func, *args, **kwargs)
            return sync_wrapper
    
    async def _execute_async(self, func: Callable, *args, **kwargs):
        """Execute async function with circuit breaker logic."""
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
            else:
                raise DataSourceException(
                    "circuit_breaker",
                    f"Circuit breaker is OPEN. Service unavailable."
                )
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e
    
    def _execute_sync(self, func: Callable, *args, **kwargs):
        """Execute sync function with circuit breaker logic."""
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
            else:
                raise DataSourceException(
                    "circuit_breaker",
                    f"Circuit breaker is OPEN. Service unavailable."
                )
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self.last_failure_time is None:
            return True
        return time.time() - self.last_failure_time >= self.recovery_timeout
    
    def _on_success(self):
        """Handle successful operation."""
        self.failure_count = 0
        self.state = "CLOSED"
    
    def _on_failure(self):
        """Handle failed operation."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(
                f"Circuit breaker opened after {self.failure_count} failures"
            )