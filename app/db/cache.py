"""
Simple in-memory caching layer for database queries.

Used for high-throughput, low-volatility data (e.g., framework registries, 
connector configurations, and policy definitions).
Designed for single-container Cloud Run instances.
"""
import time
from typing import Any, Dict, Tuple, Callable
from functools import wraps

# Global cache store: dict mapping string keys to (expiration_timestamp, value)
_CACHE: Dict[str, Tuple[float, Any]] = {}

def get_from_cache(key: str) -> Any:
    """Retrieve a value from the cache if it exists and is not expired."""
    if key in _CACHE:
        expire_at, value = _CACHE[key]
        if time.time() < expire_at:
            return value
        else:
            del _CACHE[key]
    return None

def set_in_cache(key: str, value: Any, ttl_seconds: int = 60) -> None:
    """Store a value in the cache with a time-to-live."""
    _CACHE[key] = (time.time() + ttl_seconds, value)

def clear_cache() -> None:
    """Clear all cached items."""
    _CACHE.clear()

def ttl_cache(ttl_seconds: int = 60):
    """
    Decorator to cache the results of a function.
    Keys are generated based on function arguments.
    Works with both sync and async functions.
    """
    def decorator(func: Callable):
        import inspect
        
        if inspect.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                # Create a simple cache key
                key_args = [str(a) for a in args]
                key_kwargs = [f"{k}={v}" for k, v in sorted(kwargs.items())]
                cache_key = f"{func.__name__}:{','.join(key_args)}:{','.join(key_kwargs)}"
                
                cached_val = get_from_cache(cache_key)
                if cached_val is not None:
                    return cached_val
                    
                result = await func(*args, **kwargs)
                set_in_cache(cache_key, result, ttl_seconds)
                return result
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                key_args = [str(a) for a in args]
                key_kwargs = [f"{k}={v}" for k, v in sorted(kwargs.items())]
                cache_key = f"{func.__name__}:{','.join(key_args)}:{','.join(key_kwargs)}"
                
                cached_val = get_from_cache(cache_key)
                if cached_val is not None:
                    return cached_val
                    
                result = func(*args, **kwargs)
                set_in_cache(cache_key, result, ttl_seconds)
                return result
            return sync_wrapper
            
    return decorator
