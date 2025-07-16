"""
Async audio analysis with improved performance and resource management
"""

import asyncio
import hashlib
import os
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from typing import List, Optional, Callable, Dict, Any, AsyncGenerator
from pathlib import Path
import json
import pickle
from dataclasses import asdict

from .audio_analyzer import AudioAnalyzer
from ..core.harmonic_engine import Track
from ..core.event_system import event_manager


class AnalysisCache:
    """File-based cache for audio analysis results"""
    
    def __init__(self, cache_dir: str = None):
        if cache_dir is None:
            cache_dir = Path.home() / '.bluelibrary' / 'cache'
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def _get_file_hash(self, filepath: str) -> str:
        """Generate hash based on file path, modification time, and analyzer version"""
        stat = os.stat(filepath)
        # Include analyzer version to invalidate cache when analysis logic changes
        analyzer_version = "v2.1"  # Increment when analysis logic changes
        content = f"{filepath}:{stat.st_mtime}:{stat.st_size}:{analyzer_version}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get_analysis(self, filepath: str) -> Optional[Track]:
        """Get cached analysis result"""
        try:
            file_hash = self._get_file_hash(filepath)
            cache_file = self.cache_dir / f"{file_hash}.cache"
            
            if cache_file.exists():
                with open(cache_file, 'rb') as f:
                    track_data = pickle.load(f)
                    return Track(**track_data)
        except Exception:
            pass
        return None
    
    def store_analysis(self, filepath: str, track: Track):
        """Store analysis result in cache"""
        try:
            file_hash = self._get_file_hash(filepath)
            cache_file = self.cache_dir / f"{file_hash}.cache"
            
            # Convert track to dict for serialization
            track_data = asdict(track)
            
            with open(cache_file, 'wb') as f:
                pickle.dump(track_data, f)
        except Exception as e:
            print(f"Failed to cache analysis for {filepath}: {e}")
    
    def clear_cache(self):
        """Clear all cached analysis results"""
        for cache_file in self.cache_dir.glob("*.cache"):
            cache_file.unlink()


class SecurityValidator:
    """Security validation for file paths and operations"""
    
    ALLOWED_EXTENSIONS = {'.mp3', '.flac', '.mp4', '.m4a', '.wav', '.aac', '.ogg'}
    MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB limit
    
    @classmethod
    def validate_audio_file(cls, filepath: str) -> bool:
        """Validate that file is safe to process"""
        try:
            path = Path(filepath)
            
            # Check if file exists and is a file
            if not path.exists() or not path.is_file():
                return False
            
            # Check file extension
            if path.suffix.lower() not in cls.ALLOWED_EXTENSIONS:
                return False
            
            # Check file size
            if path.stat().st_size > cls.MAX_FILE_SIZE:
                return False
            
            # Check for path traversal attempts
            resolved_path = path.resolve()
            if '..' in str(resolved_path):
                return False
            
            return True
            
        except Exception:
            return False
    
    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """Sanitize filename for safe storage"""
        # Remove dangerous characters
        dangerous_chars = '<>:"/\\|?*'
        for char in dangerous_chars:
            filename = filename.replace(char, '_')
        
        # Limit length
        if len(filename) > 255:
            filename = filename[:255]
        
        return filename


class AsyncAudioAnalyzer:
    """Async audio analyzer with caching, security, and performance optimizations"""
    
    def __init__(self, max_workers: int = 4, cache_enabled: bool = True):
        self.analyzer = AudioAnalyzer()
        self.cache = AnalysisCache() if cache_enabled else None
        self.max_workers = max_workers
        self.semaphore = asyncio.Semaphore(max_workers)
        
    async def analyze_file_async(self, filepath: str, track_id: str) -> Optional[Track]:
        """Analyze single file asynchronously with caching and validation"""
        # Security validation
        if not SecurityValidator.validate_audio_file(filepath):
            print(f"Security validation failed for: {filepath}")
            return None
        
        # Check cache first
        if self.cache:
            cached_result = self.cache.get_analysis(filepath)
            if cached_result:
                cached_result.id = track_id  # Update ID
                return cached_result
        
        # Limit concurrent processing
        async with self.semaphore:
            # Run analysis in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                track = await loop.run_in_executor(
                    executor, 
                    self.analyzer.analyze_file, 
                    filepath, 
                    track_id
                )
        
        # Cache result
        if track and self.cache:
            self.cache.store_analysis(filepath, track)
        
        return track
    
    async def batch_analyze_async(
        self, 
        filepaths: List[str], 
        progress_callback: Optional[Callable[[int, int], None]] = None,
        batch_size: int = 50
    ) -> List[Track]:
        """Analyze multiple files in batches with progress reporting"""
        tracks = []
        total_files = len(filepaths)
        
        # Process in batches to manage memory
        for batch_start in range(0, total_files, batch_size):
            batch_end = min(batch_start + batch_size, total_files)
            batch_paths = filepaths[batch_start:batch_end]
            
            # Create async tasks for batch
            tasks = [
                self.analyze_file_async(filepath, str(batch_start + i))
                for i, filepath in enumerate(batch_paths)
            ]
            
            # Execute batch
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter successful results and publish events
            for result in batch_results:
                if isinstance(result, Track):
                    tracks.append(result)
                    # Publish track analyzed event
                    event_manager.track_analyzed(result)
                elif isinstance(result, Exception):
                    print(f"Analysis failed: {result}")
            
            # Report progress
            if progress_callback:
                progress_callback(batch_end, total_files)
        
        return tracks
    
    def clear_cache(self):
        """Clear analysis cache"""
        if self.cache:
            self.cache.clear_cache()


class MemoryEfficientProcessor:
    """Memory-efficient processing for large collections"""
    
    def __init__(self, batch_size: int = 100):
        self.batch_size = batch_size
    
    async def process_large_collection(
        self, 
        filepaths: List[str],
        analyzer: AsyncAudioAnalyzer,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> AsyncGenerator[Track, None]:
        """Process large collections with memory management"""
        total_files = len(filepaths)
        
        for i in range(0, total_files, self.batch_size):
            batch = filepaths[i:i + self.batch_size]
            
            # Process batch
            batch_tracks = await analyzer.batch_analyze_async(
                batch, 
                progress_callback
            )
            
            # Yield tracks one by one to avoid memory buildup
            for track in batch_tracks:
                yield track
            
            # Force garbage collection between batches
            import gc
            gc.collect()


# High-level async interface
async def analyze_tracks_async(
    filepaths: List[str],
    progress_callback: Optional[Callable[[int, int], None]] = None,
    max_workers: int = 4,
    cache_enabled: bool = True,
    batch_size: int = 50
) -> List[Track]:
    """
    High-level async function for analyzing audio tracks
    
    Args:
        filepaths: List of audio file paths
        progress_callback: Optional callback for progress updates
        max_workers: Maximum concurrent workers
        cache_enabled: Enable result caching
        batch_size: Batch size for processing
    
    Returns:
        List of analyzed Track objects
    """
    analyzer = AsyncAudioAnalyzer(max_workers, cache_enabled)
    return await analyzer.batch_analyze_async(
        filepaths, 
        progress_callback, 
        batch_size
    )