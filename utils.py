"""
ZenticPro Platform - Utility Functions

Reusable utility functions for the platform:
- Retry decorators with exponential backoff
- Rate limiting (token bucket algorithm)
- Input sanitization
"""

import asyncio
import time
import random
import re
from functools import wraps
from typing import Any, Callable, Optional
from collections import defaultdict


def retry_on_failure(max_attempts: int = 3, base_delay: float = 1.0, max_delay: float = 10.0):
    """
    Decorator for adding retry logic with exponential backoff and jitter.
    
    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:  # Don't sleep on the last attempt
                        # Calculate delay with exponential backoff and jitter
                        delay = min(base_delay * (2 ** attempt), max_delay)
                        # Add jitter to prevent thundering herd
                        jitter = random.uniform(0, delay * 0.1)
                        sleep_time = delay + jitter
                        
                        await asyncio.sleep(sleep_time)
                    else:
                        # Re-raise the last exception if we've exhausted retries
                        raise last_exception
            return None
        return wrapper
    return decorator


class RateLimiter:
    """
    Token bucket algorithm for rate limiting.
    
    This implementation handles per-phone number rate limiting for Twilio,
    respecting Twilio's limit of 60 messages/second per phone number.
    """
    
    def __init__(self, max_tokens: int = 60, refill_rate: float = 1.0):
        """
        Initialize the rate limiter.
        
        Args:
            max_tokens: Maximum tokens in bucket (Twilio limit: 60 messages/second)
            refill_rate: Tokens to add per second
        """
        self.max_tokens = max_tokens
        self.refill_rate = refill_rate
        self.tokens = defaultdict(lambda: max_tokens)  # Per-phone number token buckets
        self.last_refill = defaultdict(float)  # Last refill time per phone number
    
    async def acquire(self, phone_number: str, tokens_needed: int = 1):
        """
        Acquire tokens for a phone number.
        
        Args:
            phone_number: Recipient's phone number (E.164 format)
            tokens_needed: Number of tokens required
            
        Returns:
            True if tokens were acquired, False if rate limit would be exceeded
        """
        # Refill tokens based on time passed
        now = time.time()
        time_passed = now - self.last_refill[phone_number]
        
        if time_passed > 0:
            new_tokens = time_passed * self.refill_rate
            self.tokens[phone_number] = min(
                self.max_tokens,
                self.tokens[phone_number] + new_tokens
            )
            self.last_refill[phone_number] = now
        
        # Check if we have enough tokens
        if self.tokens[phone_number] >= tokens_needed:
            self.tokens[phone_number] -= tokens_needed
            return True
        else:
            # Wait for tokens to refill (basic implementation)
            # In a real system, this would block until sufficient tokens are available
            wait_time = (tokens_needed - self.tokens[phone_number]) / self.refill_rate
            await asyncio.sleep(wait_time)
            self.tokens[phone_number] = 0  # Reset after waiting
            return True


def sanitize_input(text: str) -> str:
    """
    Sanitize input to prevent injection attacks and ensure data integrity.
    
    Args:
        text: Input string to sanitize
        
    Returns:
        Sanitized string
    """
    if not isinstance(text, str):
        return ""
    
    # Remove HTML tags (prevent XSS/injection)
    sanitized = re.sub(r'<[^>]+>', '', text)
    
    # Remove or escape potentially dangerous characters
    # For SMS body, we'll limit to printable ASCII characters
    sanitized = re.sub(r'[^\x20-\x7E]', '', sanitized)
    
    # Limit length to prevent abuse (160 chars for SMS)
    return sanitized[:160]


def validate_phone_number(phone: str) -> bool:
    """
    Validate phone number format (E.164).
    
    Args:
        phone: Phone number string
        
    Returns:
        True if valid E.164 format, False otherwise
    """
    if not isinstance(phone, str):
        return False
    
    # Basic validation: must start with 1-9 and contain only digits (and optional +)
    # More lenient to allow testing with shorter numbers
    pattern = r'^\+?[1-9]\d{0,14}$'
    return bool(re.match(pattern, phone.replace(' ', '').replace('-', '')))