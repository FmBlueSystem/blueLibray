"""
Smart Caching System for BlueLibrary DJ

Advanced caching system with LRU eviction, TTL support, and specialized caches
for different types of UI data including track metadata and compatibility scores.
"""

import time
import hashlib
import weakref
from typing import Any, Dict, Optional, Tuple, List, Callable
from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from PyQt6.QtWidgets import QWidget


class CacheEntry:
    """Represents a single cache entry with metadata"""
    
    def __init__(self, value: Any, ttl: int = 300, size: int = 1):
        self.value = value
        self.created_at = time.time()
        self.last_accessed = time.time()
        self.ttl = ttl
        self.size = size
        self.access_count = 1
    
    def is_expired(self) -> bool:
        """Check if entry has expired"""
        return time.time() - self.created_at > self.ttl
    
    def touch(self):
        """Update last accessed time"""
        self.last_accessed = time.time()
        self.access_count += 1
    
    def get_age(self) -> float:
        """Get age of entry in seconds"""
        return time.time() - self.created_at


class UICache(QObject):
    """Smart caching system for UI components and data"""
    
    # Signals
    cache_hit = pyqtSignal(str)  # key
    cache_miss = pyqtSignal(str)  # key
    cache_evicted = pyqtSignal(str, str)  # key, reason
    cache_cleaned = pyqtSignal(int)  # items_removed
    
    def __init__(self, max_size: int = 1000, max_memory: int = 50 * 1024 * 1024,  # 50MB
                 ttl: int = 300, cleanup_interval: int = 60):
        super().__init__()
        
        # Configuration
        self.max_size = max_size
        self.max_memory = max_memory  # in bytes
        self.default_ttl = ttl
        self.cleanup_interval = cleanup_interval
        
        # Cache storage
        self.cache: Dict[str, CacheEntry] = {}
        self.current_memory = 0
        
        # Statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'expired': 0,
            'memory_evictions': 0,
            'cleanups': 0
        }
        
        # Cleanup timer
        self.cleanup_timer = QTimer()
        self.cleanup_timer.timeout.connect(self.cleanup_expired)
        self.cleanup_timer.start(cleanup_interval * 1000)
        
        # Memory pressure monitoring
        self.memory_pressure_threshold = 0.8  # 80% of max memory
        self.memory_check_timer = QTimer()
        self.memory_check_timer.timeout.connect(self.check_memory_pressure)
        self.memory_check_timer.start(10000)  # Check every 10 seconds
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached value"""
        if key not in self.cache:
            self.stats['misses'] += 1
            self.cache_miss.emit(key)
            return None
        
        entry = self.cache[key]
        
        # Check if expired
        if entry.is_expired():
            self.invalidate(key)
            self.stats['expired'] += 1
            self.cache_miss.emit(key)
            return None
        
        # Update access info
        entry.touch()
        self.stats['hits'] += 1
        self.cache_hit.emit(key)
        
        return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None, size: Optional[int] = None):
        """Set cached value"""
        if ttl is None:
            ttl = self.default_ttl
        
        if size is None:
            size = self._estimate_size(value)
        
        # Check if we need to evict
        if key not in self.cache:
            self._ensure_space(size)
        else:
            # Update existing entry
            old_entry = self.cache[key]
            self.current_memory -= old_entry.size
        
        # Create new entry
        entry = CacheEntry(value, ttl, size)
        self.cache[key] = entry
        self.current_memory += size
        
        # Check memory limits after insertion
        if self.current_memory > self.max_memory:
            self._evict_by_memory()
    
    def _estimate_size(self, value: Any) -> int:
        """Estimate memory size of value"""
        try:
            if isinstance(value, str):
                return len(value.encode('utf-8'))
            elif isinstance(value, (int, float)):
                return 8
            elif isinstance(value, dict):
                return sum(self._estimate_size(k) + self._estimate_size(v) 
                          for k, v in value.items())
            elif isinstance(value, (list, tuple)):
                return sum(self._estimate_size(item) for item in value)
            else:
                # Fallback estimation
                return 1024  # 1KB default
        except:
            return 1024
    
    def _ensure_space(self, needed_size: int):
        """Ensure there's enough space for new entry"""
        # Check size limit
        if len(self.cache) >= self.max_size:
            self._evict_lru()
        
        # Check memory limit
        if self.current_memory + needed_size > self.max_memory:
            self._evict_by_memory(needed_size)
    
    def _evict_lru(self):
        """Evict least recently used item"""
        if not self.cache:
            return
        
        # Find LRU entry
        lru_key = min(self.cache.keys(), 
                     key=lambda k: self.cache[k].last_accessed)
        
        self._evict_entry(lru_key, "LRU")
    
    def _evict_by_memory(self, needed_size: int = 0):
        """Evict entries to free memory"""
        target_memory = self.max_memory * 0.7  # Target 70% of max
        if needed_size > 0:
            target_memory = min(target_memory, 
                               self.max_memory - needed_size)
        
        # Sort by access time (LRU first)
        sorted_keys = sorted(self.cache.keys(), 
                           key=lambda k: self.cache[k].last_accessed)
        
        for key in sorted_keys:
            if self.current_memory <= target_memory:
                break
            
            self._evict_entry(key, "memory")
            self.stats['memory_evictions'] += 1
    
    def _evict_entry(self, key: str, reason: str):
        """Evict a specific entry"""
        if key in self.cache:
            entry = self.cache[key]
            self.current_memory -= entry.size
            del self.cache[key]
            self.stats['evictions'] += 1
            self.cache_evicted.emit(key, reason)
    
    def invalidate(self, key: str):
        """Invalidate cached value"""
        if key in self.cache:
            entry = self.cache[key]
            self.current_memory -= entry.size
            del self.cache[key]
    
    def invalidate_pattern(self, pattern: str):
        """Invalidate all keys matching pattern"""
        keys_to_remove = []
        for key in self.cache.keys():
            if pattern in key:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            self.invalidate(key)
    
    def cleanup_expired(self):
        """Clean up expired cache entries"""
        current_time = time.time()
        expired_keys = []
        
        for key, entry in self.cache.items():
            if entry.is_expired():
                expired_keys.append(key)
        
        for key in expired_keys:
            self.invalidate(key)
            self.stats['expired'] += 1
        
        if expired_keys:
            self.stats['cleanups'] += 1
            self.cache_cleaned.emit(len(expired_keys))
    
    def check_memory_pressure(self):
        """Check and handle memory pressure"""
        if self.current_memory > self.max_memory * self.memory_pressure_threshold:
            self._evict_by_memory()
    
    def clear(self):
        """Clear all cache entries"""
        self.cache.clear()
        self.current_memory = 0
        for stat in self.stats:
            self.stats[stat] = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = self.stats['hits'] / total_requests if total_requests > 0 else 0
        
        return {
            'hit_count': self.stats['hits'],
            'miss_count': self.stats['misses'],
            'hit_rate': hit_rate,
            'cache_size': len(self.cache),
            'max_size': self.max_size,
            'memory_usage': self.current_memory,
            'max_memory': self.max_memory,
            'memory_usage_percent': (self.current_memory / self.max_memory) * 100,
            'evictions': self.stats['evictions'],
            'expired': self.stats['expired'],
            'memory_evictions': self.stats['memory_evictions'],
            'cleanups': self.stats['cleanups']
        }
    
    def get_cache_info(self) -> List[Dict[str, Any]]:
        """Get detailed information about cache entries"""
        current_time = time.time()
        info = []
        
        for key, entry in self.cache.items():
            info.append({
                'key': key,
                'size': entry.size,
                'age': current_time - entry.created_at,
                'last_accessed': current_time - entry.last_accessed,
                'access_count': entry.access_count,
                'ttl': entry.ttl,
                'expired': entry.is_expired()
            })
        
        return sorted(info, key=lambda x: x['last_accessed'])
    
    def optimize(self):
        """Optimize cache by removing expired entries and defragmenting"""
        self.cleanup_expired()
        
        # If still over memory limit, evict more aggressively
        if self.current_memory > self.max_memory * 0.9:
            self._evict_by_memory()


class TrackDataCache(UICache):
    """Specialized cache for track data"""
    
    def __init__(self):
        super().__init__(
            max_size=5000,
            max_memory=100 * 1024 * 1024,  # 100MB for track data
            ttl=600,  # 10 minutes for track data
            cleanup_interval=120  # Clean every 2 minutes
        )
    
    def get_track_key(self, track_id: str, data_type: str) -> str:
        """Generate cache key for track data"""
        return f"track_{track_id}_{data_type}"
    
    def cache_track_metadata(self, track_id: str, metadata: Dict[str, Any]):
        """Cache track metadata"""
        key = self.get_track_key(track_id, "metadata")
        self.set(key, metadata, ttl=3600)  # 1 hour for metadata
    
    def get_track_metadata(self, track_id: str) -> Optional[Dict[str, Any]]:
        """Get cached track metadata"""
        key = self.get_track_key(track_id, "metadata")
        return self.get(key)
    
    def cache_track_analysis(self, track_id: str, analysis: Dict[str, Any]):
        """Cache track analysis results"""
        key = self.get_track_key(track_id, "analysis")
        self.set(key, analysis, ttl=1800)  # 30 minutes for analysis
    
    def get_track_analysis(self, track_id: str) -> Optional[Dict[str, Any]]:
        """Get cached track analysis"""
        key = self.get_track_key(track_id, "analysis")
        return self.get(key)
    
    def cache_compatibility_score(self, track1_id: str, track2_id: str, score: float):
        """Cache compatibility score between tracks"""
        # Create deterministic key regardless of track order
        key = f"compat_{min(track1_id, track2_id)}_{max(track1_id, track2_id)}"
        self.set(key, score, ttl=1800)  # 30 minutes for compatibility
    
    def get_compatibility_score(self, track1_id: str, track2_id: str) -> Optional[float]:
        """Get cached compatibility score"""
        key = f"compat_{min(track1_id, track2_id)}_{max(track1_id, track2_id)}"
        return self.get(key)
    
    def cache_enhanced_data(self, track_id: str, enhanced_data: Dict[str, Any]):
        """Cache AI-enhanced track data"""
        key = self.get_track_key(track_id, "enhanced")
        self.set(key, enhanced_data, ttl=7200)  # 2 hours for enhanced data
    
    def get_enhanced_data(self, track_id: str) -> Optional[Dict[str, Any]]:
        """Get cached enhanced track data"""
        key = self.get_track_key(track_id, "enhanced")
        return self.get(key)
    
    def invalidate_track(self, track_id: str):
        """Invalidate all cached data for a track"""
        self.invalidate_pattern(f"track_{track_id}")


class UIComponentCache(UICache):
    """Specialized cache for UI components and rendered items"""
    
    def __init__(self):
        super().__init__(
            max_size=2000,
            max_memory=50 * 1024 * 1024,  # 50MB for UI components
            ttl=300,  # 5 minutes for UI data
            cleanup_interval=60
        )
    
    def cache_rendered_item(self, item_id: str, rendered_data: Any):
        """Cache rendered UI item"""
        key = f"rendered_{item_id}"
        self.set(key, rendered_data, ttl=600)  # 10 minutes for rendered items
    
    def get_rendered_item(self, item_id: str) -> Optional[Any]:
        """Get cached rendered item"""
        key = f"rendered_{item_id}"
        return self.get(key)
    
    def cache_widget_state(self, widget_id: str, state: Dict[str, Any]):
        """Cache widget state"""
        key = f"widget_state_{widget_id}"
        self.set(key, state, ttl=1800)  # 30 minutes for widget state
    
    def get_widget_state(self, widget_id: str) -> Optional[Dict[str, Any]]:
        """Get cached widget state"""
        key = f"widget_state_{widget_id}"
        return self.get(key)
    
    def cache_search_results(self, search_hash: str, results: List[Any]):
        """Cache search results"""
        key = f"search_{search_hash}"
        self.set(key, results, ttl=180)  # 3 minutes for search results
    
    def get_search_results(self, search_hash: str) -> Optional[List[Any]]:
        """Get cached search results"""
        key = f"search_{search_hash}"
        return self.get(key)
    
    def generate_search_hash(self, search_terms: str, filters: Dict[str, Any]) -> str:
        """Generate hash for search query"""
        search_data = f"{search_terms}_{str(sorted(filters.items()))}"
        return hashlib.md5(search_data.encode()).hexdigest()


class CacheManager:
    """Global cache manager for coordinating multiple caches"""
    
    def __init__(self):
        self.caches = {}
        self.global_stats = {
            'total_memory': 0,
            'total_entries': 0,
            'total_hits': 0,
            'total_misses': 0
        }
    
    def register_cache(self, name: str, cache: UICache):
        """Register a cache with the manager"""
        self.caches[name] = cache
        
        # Connect to cache signals for global stats
        cache.cache_hit.connect(lambda key: self._update_global_stats('hits', 1))
        cache.cache_miss.connect(lambda key: self._update_global_stats('misses', 1))
    
    def _update_global_stats(self, stat_type: str, value: int):
        """Update global statistics"""
        if stat_type in self.global_stats:
            self.global_stats[f"total_{stat_type}"] += value
    
    def get_cache(self, name: str) -> Optional[UICache]:
        """Get cache by name"""
        return self.caches.get(name)
    
    def get_global_stats(self) -> Dict[str, Any]:
        """Get global cache statistics"""
        total_memory = 0
        total_entries = 0
        
        for cache in self.caches.values():
            stats = cache.get_stats()
            total_memory += stats['memory_usage']
            total_entries += stats['cache_size']
        
        total_requests = self.global_stats['total_hits'] + self.global_stats['total_misses']
        global_hit_rate = (self.global_stats['total_hits'] / total_requests 
                          if total_requests > 0 else 0)
        
        return {
            'total_memory': total_memory,
            'total_entries': total_entries,
            'total_hits': self.global_stats['total_hits'],
            'total_misses': self.global_stats['total_misses'],
            'global_hit_rate': global_hit_rate,
            'cache_count': len(self.caches)
        }
    
    def cleanup_all(self):
        """Cleanup all registered caches"""
        for cache in self.caches.values():
            cache.cleanup_expired()
    
    def optimize_all(self):
        """Optimize all registered caches"""
        for cache in self.caches.values():
            cache.optimize()
    
    def clear_all(self):
        """Clear all registered caches"""
        for cache in self.caches.values():
            cache.clear()
    
    def get_detailed_stats(self) -> Dict[str, Any]:
        """Get detailed statistics for all caches"""
        stats = {}
        
        for name, cache in self.caches.items():
            stats[name] = cache.get_stats()
        
        stats['global'] = self.get_global_stats()
        return stats


# Global cache manager instance
cache_manager = CacheManager()

# Create and register default caches
track_cache = TrackDataCache()
ui_cache = UIComponentCache()

cache_manager.register_cache('track', track_cache)
cache_manager.register_cache('ui', ui_cache)