"""
Helper utilities for agent implementations with error handling and retry logic.

This module provides common utilities that agents can use to handle external
API calls with proper retry logic and error handling.
"""

import asyncio
from typing import Any, Dict, List, Optional, Callable
from app.utils.retry import retry_with_backoff, RetryConfig, CircuitBreaker
from app.utils.exceptions import (
    DataSourceException,
    RateLimitException,
    TimeoutException,
    AgentProcessingException
)
from app.config.logging import get_logger

logger = get_logger(__name__)


class AgentRetryConfig:
    """Predefined retry configurations for different agent operations."""
    
    # Configuration for external API calls (more aggressive retries)
    EXTERNAL_API = RetryConfig(
        max_attempts=5,
        base_delay=1.0,
        max_delay=30.0,
        exponential_base=2.0,
        jitter=True
    )
    
    # Configuration for LLM API calls (moderate retries)
    LLM_API = RetryConfig(
        max_attempts=3,
        base_delay=2.0,
        max_delay=60.0,
        exponential_base=2.0,
        jitter=True
    )
    
    # Configuration for quick operations (minimal retries)
    QUICK_OPERATION = RetryConfig(
        max_attempts=2,
        base_delay=0.5,
        max_delay=5.0,
        exponential_base=2.0,
        jitter=False
    )


# Circuit breakers for different services
yahoo_finance_breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60.0,
    expected_exception=DataSourceException
)

groq_api_breaker = CircuitBreaker(
    failure_threshold=3,
    recovery_timeout=30.0,
    expected_exception=(RateLimitException, TimeoutException)
)


async def safe_external_api_call(
    operation: Callable,
    operation_name: str,
    retry_config: Optional[RetryConfig] = None,
    circuit_breaker: Optional[CircuitBreaker] = None,
    *args,
    **kwargs
) -> Any:
    """
    Safely execute an external API call with retry logic and circuit breaker.
    
    Args:
        operation: The async function to execute
        operation_name: Name of the operation for logging
        retry_config: Retry configuration to use
        circuit_breaker: Circuit breaker to use
        *args: Arguments to pass to the operation
        **kwargs: Keyword arguments to pass to the operation
        
    Returns:
        Result of the operation
        
    Raises:
        The last exception if all retries fail
    """
    if retry_config is None:
        retry_config = AgentRetryConfig.EXTERNAL_API
    
    @retry_with_backoff(retry_config)
    async def wrapped_operation():
        try:
            if circuit_breaker:
                return await circuit_breaker._execute_async(operation, *args, **kwargs)
            else:
                return await operation(*args, **kwargs)
        except Exception as e:
            logger.error(f"Operation {operation_name} failed: {e}")
            # Convert generic exceptions to more specific ones
            if "timeout" in str(e).lower():
                raise TimeoutException(operation_name, 30)
            elif "rate limit" in str(e).lower():
                raise RateLimitException(operation_name)
            elif "connection" in str(e).lower():
                raise DataSourceException(operation_name, str(e))
            else:
                raise AgentProcessingException(operation_name, str(e))
    
    return await wrapped_operation()


async def safe_llm_call(
    llm_function: Callable,
    prompt: str,
    operation_name: str = "llm_call",
    **llm_kwargs
) -> str:
    """
    Safely execute an LLM API call with appropriate retry logic.
    
    Args:
        llm_function: The LLM function to call
        prompt: The prompt to send to the LLM
        operation_name: Name of the operation for logging
        **llm_kwargs: Additional arguments for the LLM call
        
    Returns:
        LLM response text
        
    Raises:
        AgentProcessingException if LLM call fails after retries
    """
    return await safe_external_api_call(
        llm_function,
        f"llm_{operation_name}",
        retry_config=AgentRetryConfig.LLM_API,
        circuit_breaker=groq_api_breaker,
        prompt=prompt,
        **llm_kwargs
    )


async def safe_data_fetch(
    fetch_function: Callable,
    data_source: str,
    **fetch_kwargs
) -> Dict[str, Any]:
    """
    Safely fetch data from external sources with retry logic.
    
    Args:
        fetch_function: The function to fetch data
        data_source: Name of the data source
        **fetch_kwargs: Arguments for the fetch function
        
    Returns:
        Fetched data
        
    Raises:
        DataSourceException if data fetch fails after retries
    """
    # Choose appropriate circuit breaker based on data source
    breaker = None
    if "yahoo" in data_source.lower():
        breaker = yahoo_finance_breaker
    
    return await safe_external_api_call(
        fetch_function,
        f"fetch_{data_source}",
        retry_config=AgentRetryConfig.EXTERNAL_API,
        circuit_breaker=breaker,
        **fetch_kwargs
    )


def handle_agent_errors(operation_name: str):
    """
    Decorator to handle common agent errors and convert them to appropriate exceptions.
    
    Args:
        operation_name: Name of the operation for error context
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except (DataSourceException, RateLimitException, TimeoutException, AgentProcessingException):
                # Re-raise our custom exceptions as-is
                raise
            except Exception as e:
                logger.error(f"Unexpected error in {operation_name}: {e}", exc_info=True)
                raise AgentProcessingException(
                    operation_name,
                    f"Unexpected error: {str(e)}"
                )
        return wrapper
    return decorator


class BatchProcessor:
    """
    Utility for processing multiple items with error handling and progress tracking.
    """
    
    def __init__(self, max_concurrent: int = 5, fail_fast: bool = False):
        """
        Initialize batch processor.
        
        Args:
            max_concurrent: Maximum number of concurrent operations
            fail_fast: Whether to stop on first failure
        """
        self.max_concurrent = max_concurrent
        self.fail_fast = fail_fast
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_batch(
        self,
        items: List[Any],
        processor: Callable,
        operation_name: str = "batch_operation"
    ) -> List[Dict[str, Any]]:
        """
        Process a batch of items with error handling.
        
        Args:
            items: List of items to process
            processor: Async function to process each item
            operation_name: Name of the operation for logging
            
        Returns:
            List of results with success/error information
        """
        results = []
        
        async def process_item(item, index):
            async with self.semaphore:
                try:
                    result = await processor(item)
                    return {
                        "index": index,
                        "item": item,
                        "success": True,
                        "result": result,
                        "error": None
                    }
                except Exception as e:
                    error_result = {
                        "index": index,
                        "item": item,
                        "success": False,
                        "result": None,
                        "error": str(e)
                    }
                    
                    if self.fail_fast:
                        raise AgentProcessingException(
                            operation_name,
                            f"Batch processing failed at item {index}: {e}"
                        )
                    
                    logger.warning(f"Item {index} failed in {operation_name}: {e}")
                    return error_result
        
        # Process all items concurrently
        tasks = [
            process_item(item, i) 
            for i, item in enumerate(items)
        ]
        
        try:
            results = await asyncio.gather(*tasks, return_exceptions=not self.fail_fast)
        except Exception as e:
            if self.fail_fast:
                raise
            # Handle any remaining exceptions
            results = [
                {"success": False, "error": str(e)} 
                if isinstance(r, Exception) else r 
                for r in results
            ]
        
        return results


# Example usage functions for agents
async def example_research_with_retry():
    """Example of how to use retry logic in research agent."""
    
    async def search_web(query: str) -> List[Dict]:
        # This would be the actual web search implementation
        # For demo purposes, we'll simulate a failure
        import random
        if random.random() < 0.3:  # 30% chance of failure
            raise DataSourceException("duckduckgo", "Search service temporarily unavailable")
        return [{"title": "Example", "url": "https://example.com", "snippet": "Example content"}]
    
    # Use safe data fetch with retry logic
    try:
        results = await safe_data_fetch(
            search_web,
            "duckduckgo",
            query="AI market trends"
        )
        logger.info(f"Successfully fetched {len(results)} search results")
        return results
    except DataSourceException as e:
        logger.error(f"Failed to fetch search results after retries: {e}")
        raise


async def example_stock_data_with_retry():
    """Example of how to use retry logic in stock agent."""
    
    async def fetch_stock_data(symbol: str) -> Dict:
        # This would be the actual Yahoo Finance implementation
        import random
        if random.random() < 0.2:  # 20% chance of failure
            raise DataSourceException("yahoo_finance", f"Failed to fetch data for {symbol}")
        return {"symbol": symbol, "price": 150.0, "volume": 1000000}
    
    # Use safe data fetch with circuit breaker
    try:
        data = await safe_data_fetch(
            fetch_stock_data,
            "yahoo_finance",
            symbol="AAPL"
        )
        logger.info(f"Successfully fetched stock data: {data}")
        return data
    except DataSourceException as e:
        logger.error(f"Failed to fetch stock data after retries: {e}")
        raise