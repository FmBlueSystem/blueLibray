"""
Base UI Component for BlueLibrary DJ

Provides common functionality for all UI components including caching,
event handling, and loading state management.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
import time


class BaseUIComponentMeta(type(QWidget), type(ABC)):
    """Metaclass to resolve conflicts between QWidget and ABC"""
    pass


class BaseUIComponent(QWidget, ABC, metaclass=BaseUIComponentMeta):
    """Base class for all UI components with common functionality"""
    
    # Signals for component communication
    data_changed = pyqtSignal(object)
    selection_changed = pyqtSignal(object)
    loading_started = pyqtSignal()
    loading_finished = pyqtSignal()
    error_occurred = pyqtSignal(str)
    
    def __init__(self, facade=None, parent=None):
        super().__init__(parent)
        self.facade = facade
        self.is_loading = False
        self.cache = {}
        self.performance_metrics = {
            'render_times': [],
            'update_times': [],
            'cache_hits': 0,
            'cache_misses': 0
        }
        
        # Setup component
        self.setup_ui()
        self.connect_signals()
        
        # Performance monitoring
        self.performance_timer = QTimer()
        self.performance_timer.timeout.connect(self._log_performance)
        self.performance_timer.start(30000)  # Log every 30 seconds
    
    @abstractmethod
    def setup_ui(self):
        """Initialize UI components - must be implemented by subclasses"""
        pass
    
    @abstractmethod
    def connect_signals(self):
        """Connect signals and slots - must be implemented by subclasses"""
        pass
    
    def show_loading(self, message: str = "Loading..."):
        """Show loading state with optional message"""
        if not self.is_loading:
            self.is_loading = True
            self.loading_started.emit()
            self.setEnabled(False)
            self.setStyleSheet("QWidget { opacity: 0.7; }")
    
    def hide_loading(self):
        """Hide loading state"""
        if self.is_loading:
            self.is_loading = False
            self.loading_finished.emit()
            self.setEnabled(True)
            self.setStyleSheet("")
    
    def cache_get(self, key: str) -> Optional[Any]:
        """Get value from component cache"""
        if key in self.cache:
            self.performance_metrics['cache_hits'] += 1
            return self.cache[key]
        
        self.performance_metrics['cache_misses'] += 1
        return None
    
    def cache_set(self, key: str, value: Any, ttl: int = 300):
        """Set value in component cache with optional TTL"""
        self.cache[key] = {
            'value': value,
            'timestamp': time.time(),
            'ttl': ttl
        }
    
    def cache_clear(self):
        """Clear component cache"""
        self.cache.clear()
    
    def cache_cleanup(self):
        """Remove expired cache entries"""
        current_time = time.time()
        expired_keys = []
        
        for key, data in self.cache.items():
            if current_time - data['timestamp'] > data['ttl']:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache[key]
    
    def measure_performance(self, operation_name: str):
        """Decorator for measuring operation performance"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                start_time = time.time()
                result = func(*args, **kwargs)
                end_time = time.time()
                
                duration = end_time - start_time
                if operation_name == 'render':
                    self.performance_metrics['render_times'].append(duration)
                elif operation_name == 'update':
                    self.performance_metrics['update_times'].append(duration)
                
                # Log slow operations
                if duration > 0.1:  # 100ms threshold
                    print(f"Warning: Slow {operation_name} in {self.__class__.__name__}: {duration:.3f}s")
                
                return result
            return wrapper
        return decorator
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for this component"""
        render_times = self.performance_metrics['render_times']
        update_times = self.performance_metrics['update_times']
        
        return {
            'component': self.__class__.__name__,
            'cache_hit_rate': self._calculate_cache_hit_rate(),
            'avg_render_time': sum(render_times) / len(render_times) if render_times else 0,
            'avg_update_time': sum(update_times) / len(update_times) if update_times else 0,
            'max_render_time': max(render_times) if render_times else 0,
            'max_update_time': max(update_times) if update_times else 0,
            'cache_size': len(self.cache)
        }
    
    def _calculate_cache_hit_rate(self) -> float:
        """Calculate cache hit rate"""
        total_requests = self.performance_metrics['cache_hits'] + self.performance_metrics['cache_misses']
        if total_requests == 0:
            return 0.0
        return self.performance_metrics['cache_hits'] / total_requests
    
    def _log_performance(self):
        """Log performance metrics periodically"""
        stats = self.get_performance_stats()
        if stats['avg_render_time'] > 0.05:  # Log if average render time > 50ms
            print(f"Performance: {stats['component']} - Avg render: {stats['avg_render_time']:.3f}s, "
                  f"Cache hit rate: {stats['cache_hit_rate']:.2%}")
    
    def handle_error(self, error_message: str):
        """Handle and emit error"""
        print(f"Error in {self.__class__.__name__}: {error_message}")
        self.error_occurred.emit(error_message)
        self.hide_loading()
    
    def cleanup(self):
        """Cleanup resources when component is destroyed"""
        self.performance_timer.stop()
        self.cache_clear()
        if hasattr(self, 'facade') and self.facade:
            # Disconnect any facade signals if connected
            pass


class AsyncUIComponent(BaseUIComponent):
    """Base class for components that perform async operations"""
    
    def __init__(self, facade=None, parent=None):
        super().__init__(facade, parent)
        self.pending_operations = set()
    
    def start_async_operation(self, operation_id: str):
        """Start tracking an async operation"""
        self.pending_operations.add(operation_id)
        if len(self.pending_operations) == 1:
            self.show_loading()
    
    def finish_async_operation(self, operation_id: str):
        """Finish tracking an async operation"""
        self.pending_operations.discard(operation_id)
        if len(self.pending_operations) == 0:
            self.hide_loading()
    
    def cancel_all_operations(self):
        """Cancel all pending operations"""
        self.pending_operations.clear()
        self.hide_loading()
    
    def cleanup(self):
        """Cleanup with async operation cancellation"""
        self.cancel_all_operations()
        super().cleanup()