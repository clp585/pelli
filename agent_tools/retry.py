"""
Retry logic module with exponential backoff.
"""
import time
import random
from functools import wraps
from typing import Callable, Optional

from .config import (
    logger,
    RETRY_MAX_ATTEMPTS,
    RETRY_INITIAL_DELAY,
    RETRY_BACKOFF_FACTOR,
    RETRY_MAX_DELAY,
    RETRY_JITTER,
)


def is_retryable_error(exception: Exception) -> bool:
    """
    Determine if an exception should trigger a retry.
    Retries on: rate limits, server errors, timeouts, connection errors.
    Does NOT retry on: client errors (400, 401, 403, 404, 422).
    """
    # Check for specific exception types from google.genai
    error_type = type(exception).__name__
    
    # Retry on these exception types
    retryable_types = [
        "RateLimitError",
        "InternalServerError",
        "APIConnectionError",
        "APITimeoutError",
        "ServerError",
    ]
    
    if any(retryable_type in error_type for retryable_type in retryable_types):
        return True
    
    # Check for APIError with retryable status codes
    if hasattr(exception, "response") and hasattr(exception.response, "status_code"):
        status_code = exception.response.status_code
        # Retry on 429 (rate limit) and 5xx (server errors)
        if status_code == 429 or (500 <= status_code < 600):
            return True
    
    # Check for httpx errors (network issues)
    if "httpx" in str(type(exception)) or "Connection" in error_type:
        return True
    
    # Check for timeout errors
    if "Timeout" in error_type or "timeout" in str(exception).lower():
        return True
    
    # Don't retry on client errors (4xx except 429)
    if hasattr(exception, "response") and hasattr(exception.response, "status_code"):
        status_code = exception.response.status_code
        if 400 <= status_code < 500 and status_code != 429:
            return False
    
    # Default: retry on unknown errors (safer to retry than fail)
    # But log them so we can identify non-retryable errors
    return True


def retry_with_backoff(
    max_attempts: int = RETRY_MAX_ATTEMPTS,
    initial_delay: float = RETRY_INITIAL_DELAY,
    backoff_factor: float = RETRY_BACKOFF_FACTOR,
    max_delay: float = RETRY_MAX_DELAY,
    jitter: bool = RETRY_JITTER,
    retryable_check: Optional[Callable[[Exception], bool]] = None,
):
    """
    Decorator that retries a function with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts (default: 3)
        initial_delay: Initial delay in seconds (default: 1.0)
        backoff_factor: Multiplier for delay after each retry (default: 2.0)
        max_delay: Maximum delay in seconds (default: 60.0)
        jitter: Add random jitter to prevent thundering herd (default: True)
        retryable_check: Custom function to check if exception is retryable
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            check_fn = retryable_check or is_retryable_error
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    # Check if we should retry this error
                    if not check_fn(e):
                        logger.warning(f"Non-retryable error in {func.__name__}: {type(e).__name__}: {str(e)}")
                        raise
                    
                    # Don't retry on last attempt
                    if attempt == max_attempts - 1:
                        logger.error(f"Max attempts ({max_attempts}) reached for {func.__name__}. Giving up.")
                        raise
                    
                    # Calculate delay with exponential backoff
                    delay = initial_delay * (backoff_factor ** attempt)
                    delay = min(delay, max_delay)
                    
                    # Add jitter (random value between 0 and 20% of delay)
                    if jitter:
                        jitter_amount = delay * 0.2 * random.random()
                        delay += jitter_amount
                    
                    error_msg = str(e)[:100]  # Truncate long error messages
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_attempts} failed for {func.__name__}: "
                        f"{type(e).__name__}: {error_msg}. Retrying in {delay:.2f}s..."
                    )
                    
                    time.sleep(delay)
            
            # Should never reach here, but just in case
            if last_exception:
                raise last_exception
            
        return wrapper
    return decorator

