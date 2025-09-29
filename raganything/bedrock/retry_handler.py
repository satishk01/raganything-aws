"""
Retry handler for AWS Bedrock operations
"""

import asyncio
import logging
import random
import time
from typing import Callable, Any
from botocore.exceptions import ClientError

from .config import RetryConfig
from .exceptions import BedrockRateLimitError, BedrockServiceError


logger = logging.getLogger(__name__)


class BedrockRetryHandler:
    """Handle retry logic with exponential backoff for Bedrock operations"""
    
    def __init__(self, config: RetryConfig):
        self.config = config
    
    async def execute_with_retry(
        self,
        operation: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Execute operation with exponential backoff retry"""
        
        last_exception = None
        
        for attempt in range(self.config.max_attempts):
            try:
                # Execute the operation
                result = await self._execute_operation(operation, *args, **kwargs)
                
                # Log successful retry if this wasn't the first attempt
                if attempt > 0:
                    logger.info(f"Operation succeeded on attempt {attempt + 1}")
                
                return result
                
            except Exception as e:
                last_exception = e
                
                # Check if we should retry this error
                if not self.should_retry(e):
                    logger.error(f"Non-retryable error: {str(e)}")
                    raise e
                
                # Check if we have more attempts left
                if attempt == self.config.max_attempts - 1:
                    logger.error(f"Max retry attempts ({self.config.max_attempts}) exceeded")
                    break
                
                # Calculate backoff delay
                delay = self.calculate_backoff(attempt)
                
                logger.warning(
                    f"Operation failed on attempt {attempt + 1}/{self.config.max_attempts}: {str(e)}. "
                    f"Retrying in {delay:.2f} seconds..."
                )
                
                # Wait before retrying
                await asyncio.sleep(delay)
        
        # If we get here, all retries failed
        raise last_exception
    
    async def _execute_operation(self, operation: Callable, *args, **kwargs) -> Any:
        """Execute operation, handling both sync and async functions"""
        if asyncio.iscoroutinefunction(operation):
            return await operation(*args, **kwargs)
        else:
            return operation(*args, **kwargs)
    
    def should_retry(self, error: Exception) -> bool:
        """Determine if error is retryable"""
        
        # Handle ClientError from boto3
        if isinstance(error, ClientError):
            error_code = error.response.get('Error', {}).get('Code', '')
            
            # Check if error code is in retryable list
            if error_code in self.config.retryable_errors:
                return True
            
            # Additional specific checks
            if error_code == 'ThrottlingException':
                return True
            elif error_code == 'ServiceUnavailableException':
                return True
            elif error_code == 'InternalServerException':
                return True
            elif error_code == 'ModelTimeoutException':
                return True
            elif error_code == 'ModelNotReadyException':
                return True
            
            # Don't retry client errors like validation or access denied
            return False
        
        # Handle custom Bedrock exceptions
        if isinstance(error, BedrockRateLimitError):
            return True
        elif isinstance(error, BedrockServiceError):
            return True
        
        # Handle network-related errors
        if isinstance(error, (ConnectionError, TimeoutError)):
            return True
        
        # Don't retry other exceptions by default
        return False
    
    def calculate_backoff(self, attempt: int) -> float:
        """Calculate backoff delay for retry attempt"""
        
        # Base delay with exponential backoff
        base_delay = self.config.backoff_factor ** attempt
        
        # Add jitter to avoid thundering herd
        jitter = random.uniform(0.1, 0.3) * base_delay
        delay = base_delay + jitter
        
        # Cap at maximum backoff
        delay = min(delay, self.config.max_backoff)
        
        return delay
    
    def get_retry_info(self, attempt: int, error: Exception) -> dict:
        """Get information about retry attempt for logging"""
        return {
            "attempt": attempt + 1,
            "max_attempts": self.config.max_attempts,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "is_retryable": self.should_retry(error),
            "next_delay": self.calculate_backoff(attempt) if attempt < self.config.max_attempts - 1 else None
        }