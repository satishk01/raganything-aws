"""
Caching and performance optimization utilities for AWS Bedrock
"""

import json
import hashlib
import asyncio
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import logging


@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    data: Any
    timestamp: float
    ttl: Optional[float] = None
    access_count: int = 0
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired"""
        if self.ttl is None:
            return False
        return time.time() - self.timestamp > self.ttl
    
    def access(self):
        """Mark cache entry as accessed"""
        self.access_count += 1


class BedrockCache:
    """In-memory cache for Bedrock responses with TTL and LRU eviction"""
    
    def __init__(self, max_size: int = 1000, default_ttl: float = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: Dict[str, CacheEntry] = {}
        self.access_order: List[str] = []
        self.logger = logging.getLogger(__name__)
        
    def _generate_key(self, data: Dict[str, Any]) -> str:
        """Generate cache key from request data"""
        # Create a normalized representation for consistent caching
        cache_data = {
            k: v for k, v in data.items() 
            if k not in ['timestamp', 'request_id']
        }
        
        # Sort keys for consistent hashing
        cache_str = json.dumps(cache_data, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(cache_str.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Get item from cache"""
        if key not in self.cache:
            return None
            
        entry = self.cache[key]
        
        # Check if expired
        if entry.is_expired():
            self.remove(key)
            return None
        
        # Update access order for LRU
        entry.access()
        if key in self.access_order:
            self.access_order.remove(key)
        self.access_order.append(key)
        
        return entry.data
    
    def put(self, key: str, data: Any, ttl: Optional[float] = None) -> None:
        """Put item in cache"""
        # Use default TTL if not specified
        if ttl is None:
            ttl = self.default_ttl
            
        # Create cache entry
        entry = CacheEntry(
            data=data,
            timestamp=time.time(),
            ttl=ttl
        )
        
        # Add to cache
        self.cache[key] = entry
        
        # Update access order
        if key in self.access_order:
            self.access_order.remove(key)
        self.access_order.append(key)
        
        # Evict if over capacity
        self._evict_if_needed()
    
    def remove(self, key: str) -> None:
        """Remove item from cache"""
        if key in self.cache:
            del self.cache[key]
        if key in self.access_order:
            self.access_order.remove(key)
    
    def clear(self) -> None:
        """Clear all cache entries"""
        self.cache.clear()
        self.access_order.clear()
    
    def _evict_if_needed(self) -> None:
        """Evict least recently used items if over capacity"""
        while len(self.cache) > self.max_size:
            if not self.access_order:
                break
                
            # Remove least recently used item
            lru_key = self.access_order.pop(0)
            if lru_key in self.cache:
                del self.cache[lru_key]
    
    def cleanup_expired(self) -> int:
        """Remove expired entries and return count removed"""
        expired_keys = []
        
        for key, entry in self.cache.items():
            if entry.is_expired():
                expired_keys.append(key)
        
        for key in expired_keys:
            self.remove(key)
            
        if expired_keys:
            self.logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
            
        return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_access_count = sum(entry.access_count for entry in self.cache.values())
        
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "total_accesses": total_access_count,
            "hit_rate": 0.0 if total_access_count == 0 else 
                       sum(1 for entry in self.cache.values() if entry.access_count > 0) / len(self.cache)
        }


class BedrockBatchProcessor:
    """Batch processor for optimizing Bedrock API calls"""
    
    def __init__(self, batch_size: int = 10, batch_timeout: float = 1.0):
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.pending_requests: List[Dict[str, Any]] = []
        self.batch_futures: List[asyncio.Future] = []
        self.logger = logging.getLogger(__name__)
        self._batch_lock = asyncio.Lock()
        
    async def add_request(self, request_data: Dict[str, Any], processor_func) -> Any:
        """Add request to batch and return future result"""
        future = asyncio.Future()
        
        async with self._batch_lock:
            self.pending_requests.append({
                'data': request_data,
                'future': future,
                'processor': processor_func
            })
            
            # Process batch if full or timeout reached
            if len(self.pending_requests) >= self.batch_size:
                await self._process_batch()
        
        # Set timeout for batch processing
        try:
            return await asyncio.wait_for(future, timeout=self.batch_timeout * 2)
        except asyncio.TimeoutError:
            # Process remaining batch on timeout
            async with self._batch_lock:
                if self.pending_requests:
                    await self._process_batch()
            return await future
    
    async def _process_batch(self) -> None:
        """Process current batch of requests"""
        if not self.pending_requests:
            return
            
        batch = self.pending_requests.copy()
        self.pending_requests.clear()
        
        self.logger.debug(f"Processing batch of {len(batch)} requests")
        
        # Group requests by processor type
        processor_groups = {}
        for request in batch:
            processor = request['processor']
            if processor not in processor_groups:
                processor_groups[processor] = []
            processor_groups[processor].append(request)
        
        # Process each group concurrently
        tasks = []
        for processor, requests in processor_groups.items():
            task = asyncio.create_task(self._process_group(processor, requests))
            tasks.append(task)
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _process_group(self, processor_func, requests: List[Dict[str, Any]]) -> None:
        """Process a group of requests with the same processor"""
        try:
            # Extract data for batch processing
            batch_data = [req['data'] for req in requests]
            
            # Process batch
            results = await processor_func(batch_data)
            
            # Set results for futures
            for i, request in enumerate(requests):
                if i < len(results):
                    request['future'].set_result(results[i])
                else:
                    request['future'].set_exception(
                        Exception("Batch processing returned insufficient results")
                    )
                    
        except Exception as e:
            # Set exception for all futures in this group
            for request in requests:
                if not request['future'].done():
                    request['future'].set_exception(e)
    
    async def flush(self) -> None:
        """Process any remaining requests in batch"""
        async with self._batch_lock:
            if self.pending_requests:
                await self._process_batch()


class BedrockRateLimiter:
    """Rate limiter for Bedrock API calls"""
    
    def __init__(self, requests_per_second: float = 10.0, burst_size: int = 20):
        self.requests_per_second = requests_per_second
        self.burst_size = burst_size
        self.tokens = burst_size
        self.last_update = time.time()
        self.lock = asyncio.Lock()
        
    async def acquire(self) -> None:
        """Acquire permission to make a request"""
        async with self.lock:
            now = time.time()
            
            # Add tokens based on time elapsed
            elapsed = now - self.last_update
            self.tokens = min(
                self.burst_size,
                self.tokens + elapsed * self.requests_per_second
            )
            self.last_update = now
            
            # Wait if no tokens available
            if self.tokens < 1:
                wait_time = (1 - self.tokens) / self.requests_per_second
                await asyncio.sleep(wait_time)
                self.tokens = 0
            else:
                self.tokens -= 1


class BedrockPerformanceMonitor:
    """Monitor performance metrics for Bedrock operations"""
    
    def __init__(self):
        self.metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_response_time': 0.0,
            'cache_hits': 0,
            'cache_misses': 0,
            'rate_limit_hits': 0,
        }
        self.request_times: List[float] = []
        self.max_history = 1000
        
    def record_request(self, success: bool, response_time: float, cached: bool = False):
        """Record a request metric"""
        self.metrics['total_requests'] += 1
        
        if success:
            self.metrics['successful_requests'] += 1
        else:
            self.metrics['failed_requests'] += 1
            
        self.metrics['total_response_time'] += response_time
        
        if cached:
            self.metrics['cache_hits'] += 1
        else:
            self.metrics['cache_misses'] += 1
            
        # Keep recent response times for percentile calculations
        self.request_times.append(response_time)
        if len(self.request_times) > self.max_history:
            self.request_times.pop(0)
    
    def record_rate_limit(self):
        """Record a rate limit hit"""
        self.metrics['rate_limit_hits'] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        total_requests = self.metrics['total_requests']
        
        if total_requests == 0:
            return self.metrics.copy()
        
        stats = self.metrics.copy()
        stats.update({
            'success_rate': self.metrics['successful_requests'] / total_requests,
            'average_response_time': self.metrics['total_response_time'] / total_requests,
            'cache_hit_rate': self.metrics['cache_hits'] / total_requests,
        })
        
        # Add percentiles if we have request times
        if self.request_times:
            sorted_times = sorted(self.request_times)
            stats.update({
                'p50_response_time': self._percentile(sorted_times, 0.5),
                'p95_response_time': self._percentile(sorted_times, 0.95),
                'p99_response_time': self._percentile(sorted_times, 0.99),
            })
        
        return stats
    
    def _percentile(self, sorted_list: List[float], percentile: float) -> float:
        """Calculate percentile from sorted list"""
        if not sorted_list:
            return 0.0
            
        index = int(len(sorted_list) * percentile)
        if index >= len(sorted_list):
            index = len(sorted_list) - 1
            
        return sorted_list[index]
    
    def reset(self):
        """Reset all metrics"""
        self.metrics = {key: 0 if isinstance(value, (int, float)) else value 
                       for key, value in self.metrics.items()}
        self.request_times.clear()