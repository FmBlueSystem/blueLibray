"""
Event-driven architecture for loose coupling and extensibility
"""

import asyncio
from typing import Any, Callable, Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import threading
import queue
from collections import defaultdict


class EventType(Enum):
    """Standard application events"""
    # Track events
    TRACK_LOADED = "track_loaded"
    TRACK_ANALYZED = "track_analyzed"
    TRACK_SELECTED = "track_selected"
    TRACKS_CLEARED = "tracks_cleared"
    
    # Analysis events
    ANALYSIS_STARTED = "analysis_started"
    ANALYSIS_PROGRESS = "analysis_progress"
    ANALYSIS_COMPLETED = "analysis_completed"
    ANALYSIS_FAILED = "analysis_failed"
    ANALYSIS_CANCELLED = "analysis_cancelled"
    
    # Playlist events
    PLAYLIST_GENERATED = "playlist_generated"
    PLAYLIST_SAVED = "playlist_saved"
    PLAYLIST_LOADED = "playlist_loaded"
    PLAYLIST_EXPORTED = "playlist_exported"
    
    # Engine events
    MIX_MODE_CHANGED = "mix_mode_changed"
    WEIGHTS_CHANGED = "weights_changed"
    COMPATIBILITY_CALCULATED = "compatibility_calculated"
    
    # UI events
    WINDOW_GEOMETRY_CHANGED = "window_geometry_changed"
    SETTINGS_CHANGED = "settings_changed"
    THEME_CHANGED = "theme_changed"
    
    # System events
    APPLICATION_STARTED = "application_started"
    APPLICATION_CLOSING = "application_closing"
    ERROR_OCCURRED = "error_occurred"
    PLUGIN_LOADED = "plugin_loaded"
    PLUGIN_UNLOADED = "plugin_unloaded"


@dataclass
class Event:
    """Event data structure"""
    event_type: EventType
    data: Any = None
    source: str = "unknown"
    timestamp: datetime = field(default_factory=datetime.now)
    event_id: str = field(default_factory=lambda: str(datetime.now().timestamp()))


class EventHandler:
    """Base class for event handlers"""
    
    def __init__(self, handler_func: Callable[[Event], None], 
                 filter_func: Optional[Callable[[Event], bool]] = None,
                 priority: int = 0):
        self.handler_func = handler_func
        self.filter_func = filter_func
        self.priority = priority
        self.enabled = True
    
    def can_handle(self, event: Event) -> bool:
        """Check if handler can process this event"""
        if not self.enabled:
            return False
        
        if self.filter_func:
            return self.filter_func(event)
        
        return True
    
    def handle(self, event: Event):
        """Handle the event"""
        if self.can_handle(event):
            self.handler_func(event)


class AsyncEventHandler(EventHandler):
    """Async event handler"""
    
    def __init__(self, handler_func: Callable[[Event], Any], 
                 filter_func: Optional[Callable[[Event], bool]] = None,
                 priority: int = 0):
        super().__init__(None, filter_func, priority)
        self.async_handler_func = handler_func
    
    async def handle_async(self, event: Event):
        """Handle event asynchronously"""
        if self.can_handle(event):
            await self.async_handler_func(event)


class EventBus:
    """Central event bus for application-wide event handling"""
    
    def __init__(self):
        self.handlers: Dict[EventType, List[EventHandler]] = defaultdict(list)
        self.async_handlers: Dict[EventType, List[AsyncEventHandler]] = defaultdict(list)
        self.event_history: List[Event] = []
        self.max_history = 1000
        self.enabled = True
        self._lock = threading.Lock()
    
    def subscribe(self, event_type: EventType, handler: Callable[[Event], None], 
                  filter_func: Optional[Callable[[Event], bool]] = None,
                  priority: int = 0) -> EventHandler:
        """Subscribe to events"""
        event_handler = EventHandler(handler, filter_func, priority)
        
        with self._lock:
            self.handlers[event_type].append(event_handler)
            # Sort by priority (higher priority first)
            self.handlers[event_type].sort(key=lambda h: h.priority, reverse=True)
        
        return event_handler
    
    def subscribe_async(self, event_type: EventType, handler: Callable[[Event], Any],
                       filter_func: Optional[Callable[[Event], bool]] = None,
                       priority: int = 0) -> AsyncEventHandler:
        """Subscribe to events with async handler"""
        event_handler = AsyncEventHandler(handler, filter_func, priority)
        
        with self._lock:
            self.async_handlers[event_type].append(event_handler)
            self.async_handlers[event_type].sort(key=lambda h: h.priority, reverse=True)
        
        return event_handler
    
    def unsubscribe(self, event_type: EventType, handler: EventHandler):
        """Unsubscribe from events"""
        with self._lock:
            if handler in self.handlers[event_type]:
                self.handlers[event_type].remove(handler)
            
            if isinstance(handler, AsyncEventHandler) and handler in self.async_handlers[event_type]:
                self.async_handlers[event_type].remove(handler)
    
    def publish(self, event_type: EventType, data: Any = None, source: str = "unknown"):
        """Publish an event"""
        if not self.enabled:
            return
        
        event = Event(event_type, data, source)
        
        # Add to history
        self.event_history.append(event)
        if len(self.event_history) > self.max_history:
            self.event_history.pop(0)
        
        # Handle synchronous events
        for handler in self.handlers[event_type]:
            try:
                handler.handle(event)
            except Exception as e:
                print(f"Error in event handler: {e}")
        
        # Handle async events in background
        async_handlers = self.async_handlers[event_type]
        if async_handlers:
            asyncio.create_task(self._handle_async_events(event, async_handlers))
    
    async def _handle_async_events(self, event: Event, handlers: List[AsyncEventHandler]):
        """Handle async events"""
        for handler in handlers:
            try:
                await handler.handle_async(event)
            except Exception as e:
                print(f"Error in async event handler: {e}")
    
    def get_event_history(self, event_type: Optional[EventType] = None, 
                         limit: int = 100) -> List[Event]:
        """Get event history"""
        events = self.event_history
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        return events[-limit:] if limit > 0 else events
    
    def clear_history(self):
        """Clear event history"""
        self.event_history.clear()
    
    def enable(self):
        """Enable event bus"""
        self.enabled = True
    
    def disable(self):
        """Disable event bus"""
        self.enabled = False


class EventMetrics:
    """Event system metrics and monitoring"""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.metrics = defaultdict(int)
        self.handler_metrics = defaultdict(lambda: defaultdict(int))
        
        # Subscribe to all events for metrics
        for event_type in EventType:
            event_bus.subscribe(event_type, self._track_event, priority=1000)
    
    def _track_event(self, event: Event):
        """Track event for metrics"""
        self.metrics[event.event_type] += 1
        self.metrics['total_events'] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get event metrics"""
        return {
            'total_events': self.metrics['total_events'],
            'events_by_type': dict(self.metrics),
            'handler_count': {
                event_type.value: len(handlers) 
                for event_type, handlers in self.event_bus.handlers.items()
            },
            'async_handler_count': {
                event_type.value: len(handlers)
                for event_type, handlers in self.event_bus.async_handlers.items()
            }
        }
    
    def reset_metrics(self):
        """Reset all metrics"""
        self.metrics.clear()
        self.handler_metrics.clear()


class ApplicationEventManager:
    """High-level event management for the application"""
    
    def __init__(self):
        self.event_bus = EventBus()
        self.metrics = EventMetrics(self.event_bus)
        self._setup_system_handlers()
    
    def _setup_system_handlers(self):
        """Setup system-level event handlers"""
        # Log important events
        self.event_bus.subscribe(
            EventType.ERROR_OCCURRED,
            self._log_error,
            priority=1000
        )
        
        self.event_bus.subscribe(
            EventType.APPLICATION_STARTED,
            self._log_application_start,
            priority=1000
        )
        
        self.event_bus.subscribe(
            EventType.APPLICATION_CLOSING,
            self._log_application_close,
            priority=1000
        )
    
    def _log_error(self, event: Event):
        """Log error events"""
        error_data = event.data
        print(f"ERROR [{event.timestamp}]: {error_data}")
    
    def _log_application_start(self, event: Event):
        """Log application start"""
        print(f"Application started at {event.timestamp}")
    
    def _log_application_close(self, event: Event):
        """Log application close"""
        print(f"Application closing at {event.timestamp}")
    
    # Convenience methods for common events
    
    def track_loaded(self, track):
        """Publish track loaded event"""
        self.event_bus.publish(EventType.TRACK_LOADED, track, "track_manager")
    
    def track_analyzed(self, track):
        """Publish track analyzed event"""
        self.event_bus.publish(EventType.TRACK_ANALYZED, track, "analyzer")
    
    def analysis_progress(self, current: int, total: int):
        """Publish analysis progress event"""
        self.event_bus.publish(
            EventType.ANALYSIS_PROGRESS, 
            {'current': current, 'total': total, 'percentage': (current / total) * 100},
            "analyzer"
        )
    
    def playlist_generated(self, playlist, settings):
        """Publish playlist generated event"""
        self.event_bus.publish(
            EventType.PLAYLIST_GENERATED,
            {'playlist': playlist, 'settings': settings},
            "playlist_manager"
        )
    
    def mix_mode_changed(self, old_mode, new_mode):
        """Publish mix mode changed event"""
        self.event_bus.publish(
            EventType.MIX_MODE_CHANGED,
            {'old_mode': old_mode, 'new_mode': new_mode},
            "mixing_engine"
        )
    
    def weights_changed(self, old_weights, new_weights):
        """Publish weights changed event"""
        self.event_bus.publish(
            EventType.WEIGHTS_CHANGED,
            {'old_weights': old_weights, 'new_weights': new_weights},
            "mixing_engine"
        )
    
    def error_occurred(self, error, context=None):
        """Publish error event"""
        self.event_bus.publish(
            EventType.ERROR_OCCURRED,
            {'error': str(error), 'context': context},
            "system"
        )
    
    def application_started(self):
        """Publish application started event"""
        self.event_bus.publish(EventType.APPLICATION_STARTED, None, "system")
    
    def application_closing(self):
        """Publish application closing event"""
        self.event_bus.publish(EventType.APPLICATION_CLOSING, None, "system")


# Global event manager instance
event_manager = ApplicationEventManager()


# Decorator for automatic event publishing
def publishes_event(event_type: EventType, source: str = "unknown"):
    """Decorator to automatically publish events when function is called"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                event_manager.event_bus.publish(event_type, result, source)
                return result
            except Exception as e:
                event_manager.error_occurred(e, func.__name__)
                raise
        return wrapper
    return decorator


# Context manager for event scoping
class EventScope:
    """Context manager for scoped event handling"""
    
    def __init__(self, event_bus: EventBus, scope_name: str):
        self.event_bus = event_bus
        self.scope_name = scope_name
        self.handlers = []
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Unsubscribe all handlers added in this scope
        for event_type, handler in self.handlers:
            self.event_bus.unsubscribe(event_type, handler)
    
    def subscribe(self, event_type: EventType, handler: Callable[[Event], None],
                  filter_func: Optional[Callable[[Event], bool]] = None,
                  priority: int = 0) -> EventHandler:
        """Subscribe within this scope"""
        event_handler = self.event_bus.subscribe(event_type, handler, filter_func, priority)
        self.handlers.append((event_type, event_handler))
        return event_handler