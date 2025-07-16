"""
Progress Batch Manager for BlueLibrary DJ

Advanced progress management with batching and throttling to prevent UI freezing
during large operations like track loading and analysis.
"""

import time
from collections import deque
from typing import Dict, Any, Optional, Callable
from PyQt6.QtCore import QTimer, QObject, pyqtSignal
from PyQt6.QtWidgets import QProgressBar, QLabel, QWidget, QVBoxLayout, QHBoxLayout


class ProgressBatchManager(QObject):
    """Advanced progress management with batching and throttling"""
    
    progress_updated = pyqtSignal(int, int, str)  # current, total, message
    operation_started = pyqtSignal(str)  # operation name
    operation_finished = pyqtSignal(str, float)  # operation name, duration
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Batching configuration
        self.batch_size = 50
        self.update_interval = 100  # ms
        self.min_update_interval = 50  # ms for high-frequency updates
        self.max_queue_size = 1000  # Prevent memory issues
        
        # Progress tracking
        self.pending_updates = deque()
        self.last_update_time = 0
        self.current_operation = None
        self.operation_history = []
        
        # Timers (disabled to avoid QTimer warnings)
        self.batch_timer = None
        # self.batch_timer = QTimer()
        # self.batch_timer.timeout.connect(self.process_batch)
        # self.batch_timer.setSingleShot(True)
        
        # Performance monitoring
        self.update_times = deque(maxlen=100)
        self.slow_update_threshold = 0.1  # 100ms
        self.total_updates_processed = 0
        
        # Adaptive throttling
        self.adaptive_throttling = True
        self.base_interval = self.update_interval
        self.load_factor = 0.0
    
    def start_operation(self, operation_name: str, total_items: int = 0, 
                       estimated_duration: float = 0):
        """Start a new progress operation"""
        # Finish any existing operation
        if self.current_operation:
            self.finish_operation("Interrupted")
        
        self.current_operation = {
            'name': operation_name,
            'total': total_items,
            'current': 0,
            'start_time': time.time(),
            'last_update': 0,
            'estimated_duration': estimated_duration,
            'updates_count': 0,
            'throughput': 0.0
        }
        
        # Clear pending updates from previous operation
        self.pending_updates.clear()
        
        # Emit signals
        self.operation_started.emit(operation_name)
        self.progress_updated.emit(0, total_items, f"Starting {operation_name}...")
        
        print(f"Started operation: {operation_name} (total: {total_items})")
    
    def update_progress(self, current: int, total: Optional[int] = None, 
                       message: str = "", force_update: bool = False):
        """Queue a progress update"""
        if not self.current_operation:
            return
        
        current_time = time.time()
        
        # Update current operation
        self.current_operation['current'] = current
        self.current_operation['updates_count'] += 1
        
        if total is not None:
            self.current_operation['total'] = total
        
        # Calculate throughput
        if self.current_operation['updates_count'] > 1:
            duration = current_time - self.current_operation['start_time']
            self.current_operation['throughput'] = current / duration if duration > 0 else 0
        
        # Adaptive throttling based on update frequency
        if self.adaptive_throttling:
            self._adjust_throttling()
        
        # Queue update
        update_data = {
            'current': current,
            'total': self.current_operation['total'],
            'message': message or self.current_operation['name'],
            'timestamp': current_time,
            'force': force_update
        }
        
        # Prevent queue overflow
        if len(self.pending_updates) >= self.max_queue_size:
            # Remove oldest updates, keep the most recent
            while len(self.pending_updates) > self.max_queue_size // 2:
                self.pending_updates.popleft()
        
        self.pending_updates.append(update_data)
        
        # Start or restart batch timer
        if force_update or (self.batch_timer and not self.batch_timer.isActive()):
            if self.batch_timer:
                self.batch_timer.start(self.update_interval)
    
    def _adjust_throttling(self):
        """Adjust throttling based on system load"""
        if not self.update_times:
            return
        
        # Calculate average update processing time
        avg_time = sum(self.update_times) / len(self.update_times)
        
        # Adjust interval based on processing time
        if avg_time > 0.05:  # 50ms
            self.load_factor = min(1.0, self.load_factor + 0.1)
        elif avg_time < 0.01:  # 10ms
            self.load_factor = max(0.0, self.load_factor - 0.05)
        
        # Apply load factor to interval
        self.update_interval = int(self.base_interval * (1 + self.load_factor))
        self.update_interval = max(self.min_update_interval, 
                                  min(self.update_interval, 500))  # Cap at 500ms
    
    def process_batch(self):
        """Process batched progress updates"""
        if not self.pending_updates:
            return
        
        start_time = time.time()
        
        # Process in batches to prevent UI blocking
        processed_count = 0
        latest_update = None
        
        while self.pending_updates and processed_count < self.batch_size:
            update = self.pending_updates.popleft()
            latest_update = update
            processed_count += 1
            
            # Process forced updates immediately
            if update['force']:
                self._emit_progress_update(update)
                latest_update = None
        
        # Emit the latest non-forced update
        if latest_update and not latest_update['force']:
            self._emit_progress_update(latest_update)
        
        # Performance monitoring
        process_time = time.time() - start_time
        self.update_times.append(process_time)
        self.total_updates_processed += processed_count
        
        if process_time > self.slow_update_threshold:
            print(f"Warning: Slow progress update: {process_time:.3f}s "
                  f"(processed {processed_count} updates)")
        
        # Continue processing if more updates are queued
        if self.pending_updates:
            if self.batch_timer:
                self.batch_timer.start(self.update_interval)
    
    def _emit_progress_update(self, update_data: Dict[str, Any]):
        """Emit a progress update signal"""
        self.progress_updated.emit(
            update_data['current'],
            update_data['total'],
            update_data['message']
        )
    
    def finish_operation(self, message: str = "Completed"):
        """Finish the current operation"""
        if not self.current_operation:
            return
        
        # Process any remaining updates
        if self.batch_timer:
            self.batch_timer.stop()
        if self.pending_updates:
            self.process_batch()
        
        # Final progress update
        total = self.current_operation['total']
        self.progress_updated.emit(total, total, message)
        
        # Calculate operation stats
        end_time = time.time()
        duration = end_time - self.current_operation['start_time']
        
        # Store operation history
        operation_stats = {
            'name': self.current_operation['name'],
            'duration': duration,
            'total_items': self.current_operation['total'],
            'updates_count': self.current_operation['updates_count'],
            'throughput': self.current_operation['throughput'],
            'avg_update_time': sum(self.update_times) / len(self.update_times) if self.update_times else 0,
            'timestamp': end_time
        }
        
        self.operation_history.append(operation_stats)
        
        # Keep only last 10 operations
        if len(self.operation_history) > 10:
            self.operation_history.pop(0)
        
        # Emit completion signal
        self.operation_finished.emit(self.current_operation['name'], duration)
        
        # Log completion
        print(f"Operation '{self.current_operation['name']}' completed in {duration:.2f}s")
        print(f"Throughput: {self.current_operation['throughput']:.2f} items/sec")
        print(f"Average update time: {operation_stats['avg_update_time']:.3f}s")
        
        # Reset
        self.current_operation = None
        self.update_times.clear()
        self.pending_updates.clear()
    
    def cancel_operation(self):
        """Cancel the current operation"""
        if self.current_operation:
            self.finish_operation("Cancelled")
    
    def get_current_operation(self) -> Optional[Dict[str, Any]]:
        """Get information about the current operation"""
        if not self.current_operation:
            return None
        
        current_time = time.time()
        duration = current_time - self.current_operation['start_time']
        
        return {
            'name': self.current_operation['name'],
            'current': self.current_operation['current'],
            'total': self.current_operation['total'],
            'duration': duration,
            'progress_percent': (self.current_operation['current'] / 
                               max(1, self.current_operation['total'])) * 100,
            'throughput': self.current_operation['throughput'],
            'estimated_time_remaining': self._estimate_time_remaining(),
            'updates_count': self.current_operation['updates_count']
        }
    
    def _estimate_time_remaining(self) -> float:
        """Estimate remaining time for current operation"""
        if not self.current_operation or self.current_operation['throughput'] <= 0:
            return 0.0
        
        remaining_items = (self.current_operation['total'] - 
                          self.current_operation['current'])
        
        return remaining_items / self.current_operation['throughput']
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        avg_update_time = (sum(self.update_times) / len(self.update_times) 
                          if self.update_times else 0)
        
        return {
            'total_updates_processed': self.total_updates_processed,
            'average_update_time': avg_update_time,
            'current_interval': self.update_interval,
            'load_factor': self.load_factor,
            'pending_updates': len(self.pending_updates),
            'operation_history_count': len(self.operation_history),
            'adaptive_throttling': self.adaptive_throttling
        }
    
    def get_operation_history(self) -> list:
        """Get history of completed operations"""
        return self.operation_history.copy()
    
    def set_adaptive_throttling(self, enabled: bool):
        """Enable or disable adaptive throttling"""
        self.adaptive_throttling = enabled
        if not enabled:
            self.update_interval = self.base_interval
            self.load_factor = 0.0


class ProgressWidget(QWidget):
    """Widget for displaying progress with enhanced information"""
    
    def __init__(self, progress_manager: ProgressBatchManager, parent=None):
        super().__init__(parent)
        self.progress_manager = progress_manager
        self.setup_ui()
        self.connect_signals()
    
    def setup_ui(self):
        """Setup the UI"""
        layout = QVBoxLayout(self)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        # Status and details
        info_layout = QHBoxLayout()
        
        self.status_label = QLabel("Ready")
        self.details_label = QLabel("")
        self.details_label.setStyleSheet("color: gray; font-size: 10px;")
        
        info_layout.addWidget(self.status_label)
        info_layout.addStretch()
        info_layout.addWidget(self.details_label)
        
        layout.addWidget(self.progress_bar)
        layout.addLayout(info_layout)
        
        # Update timer for real-time info (disabled to avoid QTimer warnings)
        self.update_timer = None
        # self.update_timer = QTimer()
        # self.update_timer.timeout.connect(self.update_details)
        # self.update_timer.start(1000)  # Update every second
    
    def connect_signals(self):
        """Connect progress manager signals"""
        self.progress_manager.progress_updated.connect(self.update_progress)
        self.progress_manager.operation_started.connect(self.show_progress)
        self.progress_manager.operation_finished.connect(self.hide_progress)
    
    def update_progress(self, current: int, total: int, message: str):
        """Update progress display"""
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.status_label.setText(message)
        
        # Calculate and show percentage
        if total > 0:
            percentage = (current / total) * 100
            self.progress_bar.setFormat(f"{percentage:.1f}%")
    
    def show_progress(self, operation_name: str):
        """Show progress bar for operation"""
        self.progress_bar.setVisible(True)
        self.status_label.setText(f"Starting {operation_name}...")
    
    def hide_progress(self, operation_name: str, duration: float):
        """Hide progress bar after operation completion"""
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"Completed {operation_name} in {duration:.2f}s")
        
        # Reset details after a delay
        QTimer.singleShot(3000, lambda: self.details_label.setText(""))
    
    def update_details(self):
        """Update detailed information"""
        current_op = self.progress_manager.get_current_operation()
        
        if current_op:
            throughput = current_op['throughput']
            eta = current_op['estimated_time_remaining']
            
            details = f"Speed: {throughput:.1f} items/sec"
            if eta > 0:
                details += f" | ETA: {eta:.1f}s"
            
            self.details_label.setText(details)
        else:
            stats = self.progress_manager.get_performance_stats()
            if stats['total_updates_processed'] > 0:
                self.details_label.setText(
                    f"Updates: {stats['total_updates_processed']} | "
                    f"Avg: {stats['average_update_time']*1000:.1f}ms"
                )


class ProgressManagerFactory:
    """Factory for creating progress managers with different configurations"""
    
    @staticmethod
    def create_fast_manager() -> ProgressBatchManager:
        """Create manager optimized for fast operations"""
        manager = ProgressBatchManager()
        manager.update_interval = 50  # Fast updates
        manager.batch_size = 100
        manager.adaptive_throttling = True
        return manager
    
    @staticmethod
    def create_slow_manager() -> ProgressBatchManager:
        """Create manager optimized for slow operations"""
        manager = ProgressBatchManager()
        manager.update_interval = 200  # Slower updates
        manager.batch_size = 25
        manager.adaptive_throttling = True
        return manager
    
    @staticmethod
    def create_bulk_manager() -> ProgressBatchManager:
        """Create manager optimized for bulk operations"""
        manager = ProgressBatchManager()
        manager.update_interval = 100
        manager.batch_size = 200  # Large batches
        manager.max_queue_size = 2000
        manager.adaptive_throttling = True
        return manager