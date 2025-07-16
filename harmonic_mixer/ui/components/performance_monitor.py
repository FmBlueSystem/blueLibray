"""
Performance Monitoring System for BlueLibrary DJ

Comprehensive performance monitoring and reporting system for tracking
UI performance, memory usage, and system health.
"""

import time
import psutil
import threading
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from collections import deque
from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QPushButton, QTextEdit


@dataclass
class PerformanceMetric:
    """Single performance metric measurement"""
    name: str
    value: float
    timestamp: float
    unit: str = ""
    category: str = "general"
    threshold_warning: float = 0.0
    threshold_critical: float = 0.0
    
    def is_warning(self) -> bool:
        """Check if metric is in warning state"""
        return self.threshold_warning > 0 and self.value > self.threshold_warning
    
    def is_critical(self) -> bool:
        """Check if metric is in critical state"""
        return self.threshold_critical > 0 and self.value > self.threshold_critical


@dataclass
class PerformanceReport:
    """Performance report containing metrics and analysis"""
    timestamp: float
    metrics: Dict[str, PerformanceMetric] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    
    def add_metric(self, metric: PerformanceMetric):
        """Add a metric to the report"""
        self.metrics[metric.name] = metric
        
        # Check for warnings and errors
        if metric.is_critical():
            self.errors.append(f"{metric.name}: {metric.value:.3f}{metric.unit} (Critical)")
        elif metric.is_warning():
            self.warnings.append(f"{metric.name}: {metric.value:.3f}{metric.unit} (Warning)")
    
    def get_summary(self) -> str:
        """Get a summary of the performance report"""
        total_metrics = len(self.metrics)
        warnings = len(self.warnings)
        errors = len(self.errors)
        
        return f"Metrics: {total_metrics} | Warnings: {warnings} | Errors: {errors}"


class PerformanceCollector:
    """Collects performance metrics from various sources"""
    
    def __init__(self):
        self.process = psutil.Process()
        self.collectors: Dict[str, Callable] = {}
        self.register_default_collectors()
    
    def register_default_collectors(self):
        """Register default system performance collectors"""
        self.collectors.update({
            'cpu_percent': self.collect_cpu_percent,
            'memory_usage': self.collect_memory_usage,
            'memory_percent': self.collect_memory_percent,
            'disk_io': self.collect_disk_io,
            'network_io': self.collect_network_io,
            'thread_count': self.collect_thread_count,
            'open_files': self.collect_open_files
        })
    
    def register_collector(self, name: str, collector: Callable):
        """Register a custom metric collector"""
        self.collectors[name] = collector
    
    def collect_cpu_percent(self) -> PerformanceMetric:
        """Collect CPU usage percentage"""
        cpu_percent = self.process.cpu_percent()
        return PerformanceMetric(
            name="cpu_percent",
            value=cpu_percent,
            timestamp=time.time(),
            unit="%",
            category="system",
            threshold_warning=50.0,
            threshold_critical=80.0
        )
    
    def collect_memory_usage(self) -> PerformanceMetric:
        """Collect memory usage in MB"""
        memory_info = self.process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        return PerformanceMetric(
            name="memory_usage",
            value=memory_mb,
            timestamp=time.time(),
            unit="MB",
            category="system",
            threshold_warning=500.0,
            threshold_critical=1000.0
        )
    
    def collect_memory_percent(self) -> PerformanceMetric:
        """Collect memory usage percentage"""
        memory_percent = self.process.memory_percent()
        return PerformanceMetric(
            name="memory_percent",
            value=memory_percent,
            timestamp=time.time(),
            unit="%",
            category="system",
            threshold_warning=20.0,
            threshold_critical=40.0
        )
    
    def collect_disk_io(self) -> PerformanceMetric:
        """Collect disk I/O operations"""
        try:
            io_counters = self.process.io_counters()
            disk_ops = io_counters.read_count + io_counters.write_count
            return PerformanceMetric(
                name="disk_io_ops",
                value=disk_ops,
                timestamp=time.time(),
                unit="ops",
                category="system"
            )
        except (AttributeError, psutil.AccessDenied):
            return PerformanceMetric(
                name="disk_io_ops",
                value=0,
                timestamp=time.time(),
                unit="ops",
                category="system"
            )
    
    def collect_network_io(self) -> PerformanceMetric:
        """Collect network I/O"""
        try:
            io_counters = psutil.net_io_counters()
            if io_counters:
                network_bytes = io_counters.bytes_sent + io_counters.bytes_recv
                return PerformanceMetric(
                    name="network_io_bytes",
                    value=network_bytes / 1024 / 1024,  # MB
                    timestamp=time.time(),
                    unit="MB",
                    category="system"
                )
        except (AttributeError, psutil.AccessDenied):
            pass
        
        return PerformanceMetric(
            name="network_io_bytes",
            value=0,
            timestamp=time.time(),
            unit="MB",
            category="system"
        )
    
    def collect_thread_count(self) -> PerformanceMetric:
        """Collect thread count"""
        try:
            thread_count = self.process.num_threads()
            return PerformanceMetric(
                name="thread_count",
                value=thread_count,
                timestamp=time.time(),
                unit="threads",
                category="system",
                threshold_warning=50,
                threshold_critical=100
            )
        except psutil.AccessDenied:
            return PerformanceMetric(
                name="thread_count",
                value=0,
                timestamp=time.time(),
                unit="threads",
                category="system"
            )
    
    def collect_open_files(self) -> PerformanceMetric:
        """Collect open file count"""
        try:
            open_files = len(self.process.open_files())
            return PerformanceMetric(
                name="open_files",
                value=open_files,
                timestamp=time.time(),
                unit="files",
                category="system",
                threshold_warning=100,
                threshold_critical=200
            )
        except psutil.AccessDenied:
            return PerformanceMetric(
                name="open_files",
                value=0,
                timestamp=time.time(),
                unit="files",
                category="system"
            )
    
    def collect_all(self) -> Dict[str, PerformanceMetric]:
        """Collect all registered metrics"""
        metrics = {}
        
        for name, collector in self.collectors.items():
            try:
                metric = collector()
                metrics[name] = metric
            except Exception as e:
                print(f"Error collecting metric {name}: {e}")
                # Create error metric
                metrics[name] = PerformanceMetric(
                    name=name,
                    value=0,
                    timestamp=time.time(),
                    unit="error",
                    category="error"
                )
        
        return metrics


class PerformanceMonitor(QObject):
    """Main performance monitoring system"""
    
    # Signals
    report_ready = pyqtSignal(object)  # PerformanceReport
    alert_raised = pyqtSignal(str, str)  # level, message
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Configuration
        self.collection_interval = 1000  # ms
        self.report_interval = 10000  # ms
        self.max_history = 1000
        
        # Components
        self.collector = PerformanceCollector()
        self.history: deque = deque(maxlen=self.max_history)
        self.current_report: Optional[PerformanceReport] = None
        
        # Timers
        self.collection_timer = QTimer()
        self.collection_timer.timeout.connect(self.collect_metrics)
        
        self.report_timer = QTimer()
        self.report_timer.timeout.connect(self.generate_report)
        
        # Performance tracking
        self.ui_metrics = {}
        self.custom_metrics = {}
        
        # Start monitoring
        self.start_monitoring()
    
    def start_monitoring(self):
        """Start performance monitoring"""
        self.collection_timer.start(self.collection_interval)
        self.report_timer.start(self.report_interval)
        print("Performance monitoring started")
    
    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.collection_timer.stop()
        self.report_timer.stop()
        print("Performance monitoring stopped")
    
    def collect_metrics(self):
        """Collect performance metrics"""
        try:
            # Collect system metrics
            system_metrics = self.collector.collect_all()
            
            # Collect UI metrics
            ui_metrics = self.collect_ui_metrics()
            
            # Combine all metrics
            all_metrics = {**system_metrics, **ui_metrics, **self.custom_metrics}
            
            # Store in history
            self.history.append({
                'timestamp': time.time(),
                'metrics': all_metrics
            })
            
            # Clear custom metrics (they need to be re-added each cycle)
            self.custom_metrics.clear()
            
        except Exception as e:
            print(f"Error collecting metrics: {e}")
    
    def collect_ui_metrics(self) -> Dict[str, PerformanceMetric]:
        """Collect UI-specific metrics"""
        metrics = {}
        
        # Collect metrics from registered UI components
        for component_name, component_metrics in self.ui_metrics.items():
            for metric_name, metric_value in component_metrics.items():
                full_name = f"{component_name}_{metric_name}"
                
                # Create metric based on type
                if isinstance(metric_value, (int, float)):
                    metric = PerformanceMetric(
                        name=full_name,
                        value=metric_value,
                        timestamp=time.time(),
                        category="ui"
                    )
                    metrics[full_name] = metric
        
        return metrics
    
    def register_ui_component(self, name: str, metrics_provider: Callable):
        """Register a UI component for monitoring"""
        self.ui_metrics[name] = metrics_provider
    
    def add_custom_metric(self, name: str, value: float, unit: str = "", 
                         category: str = "custom", threshold_warning: float = 0.0,
                         threshold_critical: float = 0.0):
        """Add a custom metric for this collection cycle"""
        metric = PerformanceMetric(
            name=name,
            value=value,
            timestamp=time.time(),
            unit=unit,
            category=category,
            threshold_warning=threshold_warning,
            threshold_critical=threshold_critical
        )
        self.custom_metrics[name] = metric
    
    def generate_report(self):
        """Generate a performance report"""
        if not self.history:
            return
        
        # Create report
        report = PerformanceReport(timestamp=time.time())
        
        # Get recent metrics for analysis
        recent_metrics = list(self.history)[-10:]  # Last 10 collections
        
        # Calculate averages and trends
        for metric_name in self.get_all_metric_names():
            values = []
            for entry in recent_metrics:
                if metric_name in entry['metrics']:
                    values.append(entry['metrics'][metric_name].value)
            
            if values:
                avg_value = sum(values) / len(values)
                
                # Get the latest metric for thresholds
                latest_metric = recent_metrics[-1]['metrics'].get(metric_name)
                if latest_metric:
                    # Create average metric
                    avg_metric = PerformanceMetric(
                        name=f"{metric_name}_avg",
                        value=avg_value,
                        timestamp=time.time(),
                        unit=latest_metric.unit,
                        category=latest_metric.category,
                        threshold_warning=latest_metric.threshold_warning,
                        threshold_critical=latest_metric.threshold_critical
                    )
                    report.add_metric(avg_metric)
        
        # Store and emit report
        self.current_report = report
        self.report_ready.emit(report)
        
        # Check for alerts
        self.check_alerts(report)
    
    def get_all_metric_names(self) -> List[str]:
        """Get all metric names from history"""
        metric_names = set()
        for entry in self.history:
            metric_names.update(entry['metrics'].keys())
        return list(metric_names)
    
    def check_alerts(self, report: PerformanceReport):
        """Check for performance alerts"""
        # Check for errors
        for error in report.errors:
            self.alert_raised.emit("error", error)
        
        # Check for warnings
        for warning in report.warnings:
            self.alert_raised.emit("warning", warning)
    
    def get_current_stats(self) -> Dict[str, Any]:
        """Get current performance statistics"""
        if not self.history:
            return {}
        
        latest = self.history[-1]
        stats = {
            'timestamp': latest['timestamp'],
            'metric_count': len(latest['metrics']),
            'history_size': len(self.history)
        }
        
        # Add key metrics
        for metric_name, metric in latest['metrics'].items():
            if metric.category == "system":
                stats[metric_name] = {
                    'value': metric.value,
                    'unit': metric.unit,
                    'is_warning': metric.is_warning(),
                    'is_critical': metric.is_critical()
                }
        
        return stats
    
    def get_metric_history(self, metric_name: str, window_size: int = 100) -> List[Dict]:
        """Get history for a specific metric"""
        history = []
        
        for entry in list(self.history)[-window_size:]:
            if metric_name in entry['metrics']:
                metric = entry['metrics'][metric_name]
                history.append({
                    'timestamp': entry['timestamp'],
                    'value': metric.value,
                    'unit': metric.unit
                })
        
        return history
    
    def export_metrics(self, filename: str = None):
        """Export metrics to file"""
        if not filename:
            filename = f"performance_metrics_{int(time.time())}.json"
        
        import json
        
        # Convert history to JSON-serializable format
        export_data = {
            'exported_at': time.time(),
            'history': []
        }
        
        for entry in self.history:
            metrics_data = {}
            for name, metric in entry['metrics'].items():
                metrics_data[name] = {
                    'value': metric.value,
                    'unit': metric.unit,
                    'category': metric.category,
                    'timestamp': metric.timestamp
                }
            
            export_data['history'].append({
                'timestamp': entry['timestamp'],
                'metrics': metrics_data
            })
        
        try:
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)
            print(f"Metrics exported to {filename}")
        except Exception as e:
            print(f"Error exporting metrics: {e}")


class PerformanceWidget(QWidget):
    """Widget for displaying performance information"""
    
    def __init__(self, monitor: PerformanceMonitor, parent=None):
        super().__init__(parent)
        self.monitor = monitor
        self.setup_ui()
        self.connect_signals()
    
    def setup_ui(self):
        """Setup the UI"""
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        
        self.title_label = QLabel("Performance Monitor")
        self.title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        # Export button
        self.export_btn = QPushButton("Export Metrics")
        self.export_btn.clicked.connect(self.export_metrics)
        header_layout.addWidget(self.export_btn)
        
        layout.addLayout(header_layout)
        
        # Current stats
        self.stats_layout = QVBoxLayout()
        
        self.cpu_label = QLabel("CPU: --")
        self.memory_label = QLabel("Memory: --")
        self.thread_label = QLabel("Threads: --")
        
        self.stats_layout.addWidget(self.cpu_label)
        self.stats_layout.addWidget(self.memory_label)
        self.stats_layout.addWidget(self.thread_label)
        
        layout.addLayout(self.stats_layout)
        
        # Alerts
        self.alerts_text = QTextEdit()
        self.alerts_text.setMaximumHeight(100)
        self.alerts_text.setPlaceholderText("No alerts")
        layout.addWidget(self.alerts_text)
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(1000)  # Update every second
    
    def connect_signals(self):
        """Connect monitor signals"""
        self.monitor.report_ready.connect(self.on_report_ready)
        self.monitor.alert_raised.connect(self.on_alert_raised)
    
    def update_display(self):
        """Update the display with current stats"""
        stats = self.monitor.get_current_stats()
        
        if 'cpu_percent' in stats:
            cpu_data = stats['cpu_percent']
            color = "red" if cpu_data['is_critical'] else "orange" if cpu_data['is_warning'] else "black"
            self.cpu_label.setText(f"CPU: {cpu_data['value']:.1f}%")
            self.cpu_label.setStyleSheet(f"color: {color};")
        
        if 'memory_usage' in stats:
            mem_data = stats['memory_usage']
            color = "red" if mem_data['is_critical'] else "orange" if mem_data['is_warning'] else "black"
            self.memory_label.setText(f"Memory: {mem_data['value']:.1f} MB")
            self.memory_label.setStyleSheet(f"color: {color};")
        
        if 'thread_count' in stats:
            thread_data = stats['thread_count']
            color = "red" if thread_data['is_critical'] else "orange" if thread_data['is_warning'] else "black"
            self.thread_label.setText(f"Threads: {thread_data['value']:.0f}")
            self.thread_label.setStyleSheet(f"color: {color};")
    
    def on_report_ready(self, report):
        """Handle new performance report"""
        # Could add more detailed report display here
        pass
    
    def on_alert_raised(self, level: str, message: str):
        """Handle performance alert"""
        timestamp = time.strftime("%H:%M:%S")
        color = "red" if level == "error" else "orange"
        
        self.alerts_text.append(
            f"<span style='color: {color};'>[{timestamp}] {level.upper()}: {message}</span>"
        )
        
        # Scroll to bottom
        self.alerts_text.verticalScrollBar().setValue(
            self.alerts_text.verticalScrollBar().maximum()
        )
    
    def export_metrics(self):
        """Export metrics to file"""
        self.monitor.export_metrics()


# Global performance monitor instance
performance_monitor = PerformanceMonitor()