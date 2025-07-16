"""
Search and Filter Widget for BlueLibrary DJ

Advanced search and filtering system for large track collections with
real-time results, smart filters, and performance optimization.
"""

import re
from typing import List, Dict, Any, Callable, Optional
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
                             QComboBox, QSlider, QLabel, QPushButton, 
                             QCheckBox, QSpinBox, QDoubleSpinBox, QGroupBox,
                             QScrollArea, QFrame, QButtonGroup)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, pyqtSlot
from PyQt6.QtGui import QIcon, QFont

from .base_component import BaseUIComponent
from .ui_cache import ui_cache


class SearchWorker(QThread):
    """Background thread for performing search operations"""
    
    results_ready = pyqtSignal(list)
    search_progress = pyqtSignal(int, int)
    
    def __init__(self, tracks, search_terms, filters, parent=None):
        super().__init__(parent)
        self.tracks = tracks
        self.search_terms = search_terms
        self.filters = filters
        self.should_stop = False
    
    def run(self):
        """Perform search in background"""
        try:
            results = []
            total_tracks = len(self.tracks)
            
            for i, track in enumerate(self.tracks):
                if self.should_stop:
                    break
                
                # Emit progress every 100 tracks
                if i % 100 == 0:
                    self.search_progress.emit(i, total_tracks)
                
                if self._matches_criteria(track):
                    results.append(track)
            
            if not self.should_stop:
                self.results_ready.emit(results)
                self.search_progress.emit(total_tracks, total_tracks)
        
        except Exception as e:
            print(f"Search error: {e}")
            self.results_ready.emit([])
    
    def _matches_criteria(self, track) -> bool:
        """Check if track matches search criteria"""
        # Text search
        if self.search_terms:
            search_text = self.search_terms.lower()
            
            # Search in multiple fields
            searchable_fields = [
                getattr(track, 'title', '') or '',
                getattr(track, 'artist', '') or '',
                getattr(track, 'genre', '') or '',
                getattr(track, 'album', '') or ''
            ]
            
            found_in_field = False
            for field in searchable_fields:
                if search_text in field.lower():
                    found_in_field = True
                    break
            
            if not found_in_field:
                return False
        
        # Apply filters
        for filter_name, filter_value in self.filters.items():
            if not self._apply_filter(track, filter_name, filter_value):
                return False
        
        return True
    
    def _apply_filter(self, track, filter_name: str, filter_value: Any) -> bool:
        """Apply a specific filter to track"""
        if filter_name == 'genre' and filter_value and filter_value != 'All':
            return getattr(track, 'genre', '') == filter_value
        
        elif filter_name == 'key' and filter_value and filter_value != 'All':
            return getattr(track, 'key', '') == filter_value
        
        elif filter_name == 'bpm_min' and filter_value > 0:
            track_bpm = getattr(track, 'bpm', 0) or 0
            return track_bpm >= filter_value
        
        elif filter_name == 'bpm_max' and filter_value > 0:
            track_bpm = getattr(track, 'bpm', 0) or 0
            return track_bpm <= filter_value
        
        elif filter_name == 'energy_min' and filter_value > 0:
            track_energy = getattr(track, 'energy', 0) or 0
            return track_energy >= filter_value
        
        elif filter_name == 'energy_max' and filter_value < 10:
            track_energy = getattr(track, 'energy', 0) or 0
            return track_energy <= filter_value
        
        elif filter_name == 'enhanced_only' and filter_value:
            return hasattr(track, 'enhanced_data') and track.enhanced_data is not None
        
        elif filter_name == 'available_only' and filter_value:
            import os
            return (hasattr(track, 'file_path') and track.file_path and 
                   os.path.exists(track.file_path))
        
        return True
    
    def stop(self):
        """Stop the search operation"""
        self.should_stop = True


class QuickFilterButton(QPushButton):
    """Quick filter button with count display"""
    
    def __init__(self, name: str, filter_func: Callable, parent=None):
        super().__init__(name, parent)
        self.filter_name = name
        self.filter_func = filter_func
        self.track_count = 0
        self.setCheckable(True)
        # Use theme-aware styling instead of hardcoded colors
        self.setStyleSheet("""
            QPushButton {
                padding: 8px 15px;
                border: 2px solid #374151;
                border-radius: 6px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #21262d, stop:1 #161b22);
                color: #f7fafc;
                font-weight: 500;
                min-width: 80px;
            }
            QPushButton:checked {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3b82f6, stop:1 #1e40af);
                border: 2px solid #60a5fa;
                color: #f7fafc;
                font-weight: 600;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #30363d, stop:1 #21262d);
                border: 2px solid #3b82f6;
                color: #90cdf4;
            }
            QPushButton:checked:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #60a5fa, stop:1 #3b82f6);
                border: 2px solid #90cdf4;
            }
        """)
    
    def update_count(self, count: int):
        """Update the track count display"""
        self.track_count = count
        self.setText(f"{self.filter_name} ({count})")


class SearchFilterWidget(BaseUIComponent):
    """Advanced search and filter widget for track collections"""
    
    # Signals
    search_changed = pyqtSignal(str, dict)  # search_terms, filters
    filter_applied = pyqtSignal(list)  # filtered_tracks
    search_cleared = pyqtSignal()
    
    def __init__(self, facade=None, parent=None):
        self.tracks = []
        self.current_search = ""
        self.current_filters = {}
        self.search_worker = None
        
        # UI components
        self.search_input = None
        self.genre_combo = None
        self.key_combo = None
        self.bpm_min_spin = None
        self.bpm_max_spin = None
        self.energy_min_spin = None
        self.energy_max_spin = None
        self.quick_filter_buttons = []
        
        super().__init__(facade, parent)
        
        # Search delay timer
        self.search_delay_timer = QTimer()
        self.search_delay_timer.setSingleShot(True)
        self.search_delay_timer.timeout.connect(self.perform_search)
        
        # Performance monitoring
        self.search_times = []
        self.last_search_time = 0
    
    def setup_ui(self):
        """Setup the UI components"""
        layout = QVBoxLayout(self)
        
        # Search input
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search tracks... (artist, title, genre, album)")
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 10px 12px;
                border: 2px solid #374151;
                border-radius: 8px;
                font-size: 13px;
                background-color: #161b22;
                color: #f7fafc;
                selection-background-color: #3b82f6;
            }
            QLineEdit:focus {
                border: 2px solid #3b82f6;
                background-color: #21262d;
            }
            QLineEdit:hover {
                border: 2px solid #60a5fa;
                background-color: #21262d;
            }
        """)
        
        self.clear_button = QPushButton("Clear")
        self.clear_button.setMaximumWidth(80)
        self.clear_button.setStyleSheet("""
            QPushButton {
                padding: 8px 12px;
                border: 2px solid #e74c3c;
                border-radius: 6px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ef4444, stop:1 #dc2626);
                color: #f7fafc;
                font-weight: 600;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f87171, stop:1 #ef4444);
                border: 2px solid #fca5a5;
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #dc2626, stop:1 #b91c1c);
            }
        """)
        
        search_layout.addWidget(QLabel("Search:"))
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.clear_button)
        
        layout.addLayout(search_layout)
        
        # Quick filters
        quick_filter_group = QGroupBox("Quick Filters")
        quick_filter_layout = QHBoxLayout(quick_filter_group)
        
        self.quick_filters = {
            "High Energy": lambda t: getattr(t, 'energy', 0) > 7.0,
            "Chill": lambda t: getattr(t, 'energy', 0) < 4.0,
            "Enhanced": lambda t: hasattr(t, 'enhanced_data') and t.enhanced_data is not None,
            "Recent": lambda t: hasattr(t, 'year') and getattr(t, 'year', 0) > 2018,
            "Available": lambda t: hasattr(t, 'file_path') and t.file_path and 
                                   __import__('os').path.exists(t.file_path)
        }
        
        self.quick_filter_group = QButtonGroup()
        self.quick_filter_group.setExclusive(False)
        
        for name, filter_func in self.quick_filters.items():
            button = QuickFilterButton(name, filter_func)
            self.quick_filter_buttons.append(button)
            self.quick_filter_group.addButton(button)
            quick_filter_layout.addWidget(button)
        
        quick_filter_layout.addStretch()
        layout.addWidget(quick_filter_group)
        
        # Advanced filters
        advanced_group = QGroupBox("Advanced Filters")
        advanced_group.setObjectName("advancedFiltersGroup")
        advanced_layout = QVBoxLayout(advanced_group)
        
        # Genre and Key filters
        combo_layout = QHBoxLayout()
        
        genre_label = QLabel("Genre:")
        combo_layout.addWidget(genre_label)
        
        self.genre_combo = QComboBox()
        self.genre_combo.addItem("All")
        combo_layout.addWidget(self.genre_combo)
        
        key_label = QLabel("Key:")
        combo_layout.addWidget(key_label)
        
        self.key_combo = QComboBox()
        self.key_combo.addItem("All")
        combo_layout.addWidget(self.key_combo)
        
        advanced_layout.addLayout(combo_layout)
        
        # BPM range
        bpm_layout = QHBoxLayout()
        
        bpm_label = QLabel("BPM:")
        bpm_layout.addWidget(bpm_label)
        
        self.bpm_min_spin = QSpinBox()
        self.bpm_min_spin.setRange(0, 300)
        self.bpm_min_spin.setValue(0)
        self.bpm_min_spin.setSpecialValueText("Min")
        bpm_layout.addWidget(self.bpm_min_spin)
        
        to_label = QLabel("to")
        bpm_layout.addWidget(to_label)
        
        self.bpm_max_spin = QSpinBox()
        self.bpm_max_spin.setRange(0, 300)
        self.bpm_max_spin.setValue(300)
        self.bpm_max_spin.setSpecialValueText("Max")
        bpm_layout.addWidget(self.bpm_max_spin)
        
        advanced_layout.addLayout(bpm_layout)
        
        # Energy range
        energy_layout = QHBoxLayout()
        energy_layout.addWidget(QLabel("Energy:"))
        
        self.energy_min_spin = QDoubleSpinBox()
        self.energy_min_spin.setRange(0.0, 10.0)
        self.energy_min_spin.setValue(0.0)
        self.energy_min_spin.setDecimals(1)
        self.energy_min_spin.setSpecialValueText("Min")
        energy_layout.addWidget(self.energy_min_spin)
        
        energy_layout.addWidget(QLabel("to"))
        
        self.energy_max_spin = QDoubleSpinBox()
        self.energy_max_spin.setRange(0.0, 10.0)
        self.energy_max_spin.setValue(10.0)
        self.energy_max_spin.setDecimals(1)
        self.energy_max_spin.setSpecialValueText("Max")
        energy_layout.addWidget(self.energy_max_spin)
        
        advanced_layout.addLayout(energy_layout)
        
        # Additional filters
        additional_layout = QHBoxLayout()
        
        self.enhanced_only_check = QCheckBox("Enhanced tracks only")
        self.available_only_check = QCheckBox("Available tracks only")
        
        additional_layout.addWidget(self.enhanced_only_check)
        additional_layout.addWidget(self.available_only_check)
        additional_layout.addStretch()
        
        advanced_layout.addLayout(additional_layout)
        
        layout.addWidget(advanced_group)
        
        # Results info
        self.results_label = QLabel("Ready")
        self.results_label.setStyleSheet("""
            QLabel {
                color: #a0aec0;
                font-size: 11px;
                font-weight: 500;
                padding: 5px;
                background-color: #161b22;
                border-radius: 4px;
                border: 1px solid #374151;
            }
        """)
        layout.addWidget(self.results_label)
        
        # Make collapsible
        advanced_group.setCheckable(True)
        advanced_group.setChecked(False)
    
    def connect_signals(self):
        """Connect signals and slots"""
        # Search input
        self.search_input.textChanged.connect(self.on_search_changed)
        self.clear_button.clicked.connect(self.clear_search)
        
        # Quick filters
        for button in self.quick_filter_buttons:
            button.clicked.connect(self.on_quick_filter_changed)
        
        # Advanced filters
        self.genre_combo.currentTextChanged.connect(self.on_filter_changed)
        self.key_combo.currentTextChanged.connect(self.on_filter_changed)
        self.bpm_min_spin.valueChanged.connect(self.on_filter_changed)
        self.bpm_max_spin.valueChanged.connect(self.on_filter_changed)
        self.energy_min_spin.valueChanged.connect(self.on_filter_changed)
        self.energy_max_spin.valueChanged.connect(self.on_filter_changed)
        self.enhanced_only_check.stateChanged.connect(self.on_filter_changed)
        self.available_only_check.stateChanged.connect(self.on_filter_changed)
    
    def setTracks(self, tracks: List):
        """Set the tracks to search/filter"""
        self.tracks = tracks
        self.update_filter_options()
        self.update_quick_filter_counts()
    
    def update_filter_options(self):
        """Update filter dropdown options based on tracks"""
        # Update genre combo
        genres = set()
        keys = set()
        
        for track in self.tracks:
            if hasattr(track, 'genre') and track.genre:
                genres.add(track.genre)
            if hasattr(track, 'key') and track.key:
                keys.add(track.key)
        
        # Update genre combo
        current_genre = self.genre_combo.currentText()
        self.genre_combo.clear()
        self.genre_combo.addItem("All")
        for genre in sorted(genres):
            self.genre_combo.addItem(genre)
        
        # Restore selection
        index = self.genre_combo.findText(current_genre)
        if index >= 0:
            self.genre_combo.setCurrentIndex(index)
        
        # Update key combo
        current_key = self.key_combo.currentText()
        self.key_combo.clear()
        self.key_combo.addItem("All")
        for key in sorted(keys):
            self.key_combo.addItem(key)
        
        # Restore selection
        index = self.key_combo.findText(current_key)
        if index >= 0:
            self.key_combo.setCurrentIndex(index)
    
    def update_quick_filter_counts(self):
        """Update quick filter button counts"""
        for button in self.quick_filter_buttons:
            count = sum(1 for track in self.tracks if button.filter_func(track))
            button.update_count(count)
    
    def on_search_changed(self, text: str):
        """Handle search input changes"""
        self.current_search = text
        
        # Delay search to avoid excessive operations
        self.search_delay_timer.stop()
        self.search_delay_timer.start(300)  # 300ms delay
    
    def on_filter_changed(self):
        """Handle filter changes"""
        self.search_delay_timer.stop()
        self.search_delay_timer.start(100)  # Shorter delay for filters
    
    def on_quick_filter_changed(self):
        """Handle quick filter button changes"""
        self.search_delay_timer.stop()
        self.search_delay_timer.start(100)
    
    def clear_search(self):
        """Clear all search and filters"""
        self.search_input.clear()
        self.genre_combo.setCurrentText("All")
        self.key_combo.setCurrentText("All")
        self.bpm_min_spin.setValue(0)
        self.bpm_max_spin.setValue(300)
        self.energy_min_spin.setValue(0.0)
        self.energy_max_spin.setValue(10.0)
        self.enhanced_only_check.setChecked(False)
        self.available_only_check.setChecked(False)
        
        # Clear quick filters
        for button in self.quick_filter_buttons:
            button.setChecked(False)
        
        self.current_search = ""
        self.current_filters = {}
        self.search_cleared.emit()
    
    def get_current_filters(self) -> Dict[str, Any]:
        """Get current filter values"""
        filters = {}
        
        # Basic filters
        if self.genre_combo.currentText() != "All":
            filters['genre'] = self.genre_combo.currentText()
        
        if self.key_combo.currentText() != "All":
            filters['key'] = self.key_combo.currentText()
        
        # BPM range
        if self.bpm_min_spin.value() > 0:
            filters['bpm_min'] = self.bpm_min_spin.value()
        
        if self.bpm_max_spin.value() < 300:
            filters['bpm_max'] = self.bpm_max_spin.value()
        
        # Energy range
        if self.energy_min_spin.value() > 0.0:
            filters['energy_min'] = self.energy_min_spin.value()
        
        if self.energy_max_spin.value() < 10.0:
            filters['energy_max'] = self.energy_max_spin.value()
        
        # Checkboxes
        if self.enhanced_only_check.isChecked():
            filters['enhanced_only'] = True
        
        if self.available_only_check.isChecked():
            filters['available_only'] = True
        
        # Quick filters
        active_quick_filters = []
        for button in self.quick_filter_buttons:
            if button.isChecked():
                active_quick_filters.append(button.filter_name)
        
        if active_quick_filters:
            filters['quick_filters'] = active_quick_filters
        
        return filters
    
    def perform_search(self):
        """Perform the search operation"""
        if not self.tracks:
            return
        
        # Stop any existing search
        if self.search_worker and self.search_worker.isRunning():
            self.search_worker.stop()
            self.search_worker.wait()
        
        # Get current criteria
        search_terms = self.current_search.strip()
        filters = self.get_current_filters()
        
        # Check cache first
        cache_key = ui_cache.generate_search_hash(search_terms, filters)
        cached_results = ui_cache.get_search_results(cache_key)
        
        if cached_results is not None:
            self.on_search_completed(cached_results)
            return
        
        # Start search
        self.show_loading("Searching...")
        self.results_label.setText("Searching...")
        
        # Create and start search worker
        self.search_worker = SearchWorker(self.tracks, search_terms, filters)
        self.search_worker.results_ready.connect(
            lambda results: self.on_search_completed(results, cache_key)
        )
        self.search_worker.search_progress.connect(self.on_search_progress)
        self.search_worker.start()
        
        # Track search time
        self.search_start_time = __import__('time').time()
    
    def on_search_progress(self, current: int, total: int):
        """Handle search progress updates"""
        if total > 0:
            percent = (current / total) * 100
            self.results_label.setText(f"Searching... {percent:.1f}%")
    
    def on_search_completed(self, results: List, cache_key: str = None):
        """Handle search completion"""
        # Cache results if we have a cache key
        if cache_key:
            ui_cache.cache_search_results(cache_key, results)
        
        # Update UI
        self.hide_loading()
        self.results_label.setText(f"Found {len(results)} tracks")
        
        # Track performance
        if hasattr(self, 'search_start_time'):
            search_time = __import__('time').time() - self.search_start_time
            self.search_times.append(search_time)
            self.last_search_time = search_time
            
            # Keep only last 10 search times
            if len(self.search_times) > 10:
                self.search_times.pop(0)
        
        # Emit results
        self.filter_applied.emit(results)
        self.search_changed.emit(self.current_search, self.get_current_filters())
    
    def get_search_stats(self) -> Dict[str, Any]:
        """Get search performance statistics"""
        if not self.search_times:
            return {}
        
        return {
            'avg_search_time': sum(self.search_times) / len(self.search_times),
            'last_search_time': self.last_search_time,
            'total_searches': len(self.search_times),
            'tracks_count': len(self.tracks)
        }
    
    def cleanup(self):
        """Cleanup resources"""
        if self.search_worker and self.search_worker.isRunning():
            self.search_worker.stop()
            self.search_worker.wait()
        
        self.search_delay_timer.stop()
        super().cleanup()