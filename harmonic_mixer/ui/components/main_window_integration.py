"""
Main Window Integration for Optimized Components

This module provides integration between the existing main window and the new
optimized UI components, allowing for gradual migration while maintaining
backward compatibility.
"""

from typing import List, Optional, Dict, Any
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QSplitter, 
                             QGroupBox, QLabel, QProgressBar, QPushButton,
                             QTabWidget, QStackedWidget, QComboBox)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QModelIndex
from PyQt6.QtGui import QIcon

from .base_component import BaseUIComponent
from .virtual_table import VirtualTableWidget, VirtualTrackTableModel
from .search_filter import SearchFilterWidget
from .progress_manager import ProgressBatchManager, ProgressWidget
from .ui_cache import cache_manager, track_cache
from ..enhanced_theme import ModernBlueLibraryTheme as BlueLibraryTheme
from ..enhanced_components import ModernButton


class OptimizedTrackView(BaseUIComponent):
    """Optimized track view combining virtual table, search, and filtering"""
    
    track_selected = pyqtSignal(object)
    tracks_filtered = pyqtSignal(list)
    
    def __init__(self, facade=None, parent=None):
        self.search_widget = None
        self.table_widget = None
        self.view_mode_combo = None
        self.tracks = []
        self.filtered_tracks = []
        
        super().__init__(facade, parent)
        
        # Performance monitoring
        self.performance_timer = QTimer()
        self.performance_timer.timeout.connect(self.log_performance)
        self.performance_timer.start(30000)  # Every 30 seconds
    
    def setup_ui(self):
        """Setup the optimized UI"""
        layout = QVBoxLayout(self)
        
        # Top controls
        controls_layout = QHBoxLayout()
        
        # View mode selector
        controls_layout.addWidget(QLabel("View:"))
        self.view_mode_combo = QComboBox()
        self.view_mode_combo.addItems(["Table", "Cards", "List"])
        self.view_mode_combo.setCurrentText("Table")
        controls_layout.addWidget(self.view_mode_combo)
        
        controls_layout.addStretch()
        
        # Performance info
        self.performance_label = QLabel("")
        self.performance_label.setStyleSheet("color: gray; font-size: 10px;")
        controls_layout.addWidget(self.performance_label)
        
        layout.addLayout(controls_layout)
        
        # Search and filter widget
        self.search_widget = SearchFilterWidget(self.facade)
        layout.addWidget(self.search_widget)
        
        # Main content area
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Track views container
        from .cards_view import CardsView
        from .list_view import ListView
        
        self.table_widget = VirtualTableWidget(self.facade)
        self.cards_view = CardsView(self.facade)
        self.list_view = ListView(self.facade)
        
        # Only show table view initially
        content_splitter.addWidget(self.table_widget)
        content_splitter.addWidget(self.cards_view)
        content_splitter.addWidget(self.list_view)
        
        # Hide non-table views initially
        self.cards_view.setVisible(False)
        self.list_view.setVisible(False)
        
        # Set splitter proportions
        content_splitter.setSizes([1000])  # Full width for table
        
        layout.addWidget(content_splitter)
        
        # Apply styling
        self.setStyleSheet(f"""
            OptimizedTrackView {{
                background-color: {BlueLibraryTheme.SURFACE_LOW};
                border-radius: 8px;
            }}
        """)
    
    def connect_signals(self):
        """Connect component signals"""
        # Search widget signals
        self.search_widget.filter_applied.connect(self.on_tracks_filtered)
        self.search_widget.search_cleared.connect(self.on_search_cleared)
        
        # Table widget signals
        self.table_widget.selection_changed.connect(self.on_track_selected)
        
        # Cards and List view signals
        self.cards_view.track_selected.connect(self.on_track_selected)
        self.list_view.track_selected.connect(self.on_track_selected)
        
        # View mode changes
        self.view_mode_combo.currentTextChanged.connect(self.on_view_mode_changed)
    
    def setTracks(self, tracks: List):
        """Set tracks for the view"""
        self.tracks = tracks
        self.filtered_tracks = tracks.copy()
        
        # Update components
        self.search_widget.setTracks(tracks)
        self.table_widget.setTracks(tracks)
        
        # Cache track data
        for track in tracks:
            track_cache.cache_track_metadata(track.id, {
                'title': track.title,
                'artist': track.artist,
                'key': track.key,
                'bpm': track.bpm,
                'energy': track.energy,
                'genre': track.genre
            })
    
    def on_tracks_filtered(self, filtered_tracks: List):
        """Handle filtered tracks"""
        self.filtered_tracks = filtered_tracks
        
        # Use incremental filtering instead of recreating entire table
        if hasattr(self.table_widget, 'filterTracks'):
            # Apply filter to virtual table (more efficient)
            def filter_func(track):
                return track in filtered_tracks
            self.table_widget.filterTracks(filter_func)
        else:
            # Fallback for non-virtual tables
            self.table_widget.setTracks(filtered_tracks)
            
        self.tracks_filtered.emit(filtered_tracks)
    
    def on_search_cleared(self):
        """Handle search cleared"""
        self.filtered_tracks = self.tracks.copy()
        
        # Use incremental filtering instead of recreating entire table
        if hasattr(self.table_widget, 'filterTracks'):
            # Clear filter on virtual table (more efficient)
            self.table_widget.filterTracks(None, "")  # No filter function, no search text
        else:
            # Fallback for non-virtual tables
            self.table_widget.setTracks(self.filtered_tracks)
            
        self.tracks_filtered.emit(self.filtered_tracks)
    
    def on_track_selected(self, track):
        """Handle track selection"""
        self.track_selected.emit(track)
    
    def on_view_mode_changed(self, mode: str):
        """Handle view mode changes"""
        # Hide all views first
        self.table_widget.setVisible(False)
        self.cards_view.setVisible(False)
        self.list_view.setVisible(False)
        
        # Show selected view
        if mode == "Table":
            self.table_widget.setVisible(True)
        elif mode == "Cards":
            self.cards_view.setVisible(True)
            self.cards_view.setTracks(self.filtered_tracks)
        elif mode == "List":
            self.list_view.setVisible(True)
            self.list_view.setTracks(self.filtered_tracks)
    
    def add_track(self, track):
        """Add a single track to the view"""
        self.tracks.append(track)
        
        # Update search widget
        self.search_widget.setTracks(self.tracks)
        
        # If no filters active, add to filtered tracks too
        if not self.search_widget.current_search and not self.search_widget.current_filters:
            self.filtered_tracks.append(track)
            
            # We need to update the model's track list to match our filtered_tracks
            if hasattr(self.table_widget, 'model'):
                model = self.table_widget.model
                
                # Update model's filtered_tracks to match ours
                if hasattr(model, 'filtered_tracks'):
                    # Method 1: Try incremental insert (more efficient)
                    if hasattr(model, 'beginInsertRows'):
                        row_count = len(self.filtered_tracks) - 1  # New row index
                        model.beginInsertRows(QModelIndex(), row_count, row_count)
                        model.filtered_tracks = self.filtered_tracks.copy()  # Sync the lists
                        model.endInsertRows()
                    else:
                        # Method 2: Direct sync (still better than full reset)
                        model.filtered_tracks = self.filtered_tracks.copy()
                        model.dataChanged.emit(model.index(0, 0), 
                                             model.index(len(self.filtered_tracks)-1, model.columnCount()-1))
                else:
                    # Fallback: recreate table (less efficient but works)
                    self.table_widget.model.setTracks(self.filtered_tracks)
            else:
                # Fallback: recreate table (less efficient but works)
                self.table_widget.model.setTracks(self.filtered_tracks)
    
    def refresh_track_data(self, track_id: str):
        """Refresh data for a specific track"""
        # Find and update track in current tracks
        for i, track in enumerate(self.tracks):
            if track.id == track_id:
                # Update cache
                track_cache.cache_track_metadata(track_id, {
                    'title': track.title,
                    'artist': track.artist,
                    'key': track.key,
                    'bpm': track.bpm,
                    'energy': track.energy,
                    'genre': track.genre
                })
                
                # Update filtered tracks if present
                for j, filtered_track in enumerate(self.filtered_tracks):
                    if filtered_track.id == track_id:
                        self.filtered_tracks[j] = track
                        break
                
                break
        
        # Optimized refresh: only update the specific track instead of recreating entire table
        if hasattr(self.table_widget, 'model') and hasattr(self.table_widget.model, 'dataChanged'):
            # Find the row index of the updated track in filtered tracks
            for row, filtered_track in enumerate(self.filtered_tracks):
                if filtered_track.id == track_id:
                    # Emit dataChanged signal for this specific row
                    model = self.table_widget.model
                    top_left = model.index(row, 0)
                    bottom_right = model.index(row, model.columnCount() - 1)
                    model.dataChanged.emit(top_left, bottom_right)
                    break
        else:
            # Fallback: recreate table (less efficient but works)
            self.table_widget.model.setTracks(self.filtered_tracks)
    
    def clear_tracks(self):
        """Clear all tracks"""
        self.tracks.clear()
        self.filtered_tracks.clear()
        self.search_widget.setTracks([])
        self.table_widget.setTracks([])
    
    def log_performance(self):
        """Log performance metrics"""
        table_stats = self.table_widget.table.get_performance_stats()
        search_stats = self.search_widget.get_search_stats()
        
        if table_stats:
            avg_render = table_stats.get('avg_render_time', 0) * 1000
            total_tracks = len(self.tracks)
            visible_tracks = table_stats.get('visible_rows', 0)
            
            self.performance_label.setText(
                f"Tracks: {total_tracks} | Visible: {visible_tracks} | "
                f"Render: {avg_render:.1f}ms"
            )
        
        # Log to console if performance is poor
        if table_stats and table_stats.get('avg_render_time', 0) > 0.05:
            print(f"Performance warning: Average render time {table_stats['avg_render_time']:.3f}s")
    
    def get_selected_tracks(self) -> List:
        """Get currently selected tracks"""
        if self.table_widget and self.table_widget.table:
            selected_indices = self.table_widget.table.get_selected_indices()
            selected_tracks = []
            
            for index in selected_indices:
                if 0 <= index < len(self.filtered_tracks):
                    selected_tracks.append(self.filtered_tracks[index])
            
            return selected_tracks
        return []
    
    def select_track(self, track_id: str):
        """Select a specific track"""
        # Find track in filtered tracks
        for track in self.filtered_tracks:
            if track.id == track_id:
                self.table_widget.table.scrollToTrack(track)
                break
    
    def selectedItems(self):
        """Compatibility method for QTableWidget API"""
        # Return a list of objects representing selected tracks
        selected_tracks = self.get_selected_tracks()
        
        # Create mock QTableWidgetItem-like objects for compatibility
        class MockTableItem:
            def __init__(self, track, row):
                self.track = track
                self.row_index = row
                
            def row(self):
                return self.row_index
                
            def data(self, role=None):
                return self.track
        
        items = []
        for i, track in enumerate(selected_tracks):
            # Find the row index in filtered tracks
            try:
                row_index = self.filtered_tracks.index(track)
                items.append(MockTableItem(track, row_index))
            except ValueError:
                continue
                
        return items
    
    def selectionModel(self):
        """Compatibility method for QTableWidget API"""
        # Return a mock selection model
        class MockSelectionModel:
            def __init__(self, parent_view):
                self.parent_view = parent_view
                
            def selectedRows(self):
                """Return selected row indices"""
                selected_tracks = self.parent_view.get_selected_tracks()
                selected_indices = []
                
                for track in selected_tracks:
                    try:
                        row_index = self.parent_view.filtered_tracks.index(track)
                        # Create mock QModelIndex
                        class MockIndex:
                            def __init__(self, row):
                                self._row = row
                            def row(self):
                                return self._row
                        selected_indices.append(MockIndex(row_index))
                    except ValueError:
                        continue
                        
                return selected_indices
        
        return MockSelectionModel(self)
    
    def rowCount(self) -> int:
        """Return number of rows in the table (compatibility method)"""
        return len(self.filtered_tracks)
    
    def columnCount(self) -> int:
        """Return number of columns in the table (compatibility method)"""
        return 8  # Standard number of columns
    
    def item(self, row: int, column: int = 0):
        """Get item at row/column (compatibility method)"""
        if 0 <= row < len(self.filtered_tracks):
            track = self.filtered_tracks[row]
            
            # Create mock QTableWidgetItem
            class MockTableItem:
                def __init__(self, track, column):
                    self.track = track
                    self.column = column
                    
                def data(self, role=None):
                    return self.track
                    
                def row(self):
                    return row
                    
                def column(self):
                    return self.column
                    
                def text(self):
                    # Return appropriate text based on column
                    if self.column == 0:
                        return track.title
                    elif self.column == 1:
                        return track.artist
                    elif self.column == 2:
                        return track.key
                    elif self.column == 3:
                        return str(track.bpm)
                    elif self.column == 4:
                        return str(track.energy)
                    elif self.column == 5:
                        return track.genre
                    else:
                        return ""
            
            return MockTableItem(track, column)
        return None
    
    def viewport(self):
        """Return the viewport widget (compatibility method)"""
        # Return self as the viewport since this is the main widget
        return self


class OptimizedProgressManager(BaseUIComponent):
    """Optimized progress manager for the main window"""
    
    def __init__(self, facade=None, parent=None):
        self.progress_manager = None
        self.progress_widget = None
        super().__init__(facade, parent)
    
    def setup_ui(self):
        """Setup progress management UI"""
        layout = QVBoxLayout(self)
        
        # Create progress manager
        self.progress_manager = ProgressBatchManager()
        
        # Create progress widget
        self.progress_widget = ProgressWidget(self.progress_manager)
        layout.addWidget(self.progress_widget)
        
        # Apply styling
        self.setStyleSheet(f"""
            OptimizedProgressManager {{
                background-color: {BlueLibraryTheme.SURFACE_MEDIUM};
                border-radius: 6px;
                padding: 5px;
            }}
        """)
    
    def connect_signals(self):
        """Connect progress manager signals"""
        pass
    
    def start_operation(self, name: str, total: int = 0):
        """Start a progress operation"""
        self.progress_manager.start_operation(name, total)
    
    def update_progress(self, current: int, total: int = None, message: str = ""):
        """Update progress"""
        self.progress_manager.update_progress(current, total, message)
    
    def finish_operation(self, message: str = "Completed"):
        """Finish current operation"""
        self.progress_manager.finish_operation(message)


class MainWindowIntegration:
    """Integration layer for the main window"""
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.track_view = None
        self.progress_manager = None
        self.is_optimized = False
        
        # Performance monitoring
        self.performance_stats = {
            'track_loads': 0,
            'search_operations': 0,
            'render_times': []
        }
    
    def enable_optimizations(self):
        """Enable optimized components"""
        if self.is_optimized:
            return
        
        try:
            # Create optimized components
            self.track_view = OptimizedTrackView(self.main_window.facade)
            self.progress_manager = OptimizedProgressManager(self.main_window.facade)
            
            # Connect to existing main window signals
            self.track_view.track_selected.connect(self.on_track_selected)
            self.track_view.tracks_filtered.connect(self.on_tracks_filtered)
            
            # Replace existing components if they exist
            if hasattr(self.main_window, 'track_table'):
                self._replace_track_table()
            
            if hasattr(self.main_window, 'progress_bar'):
                self._replace_progress_bar()
            
            self.is_optimized = True
            print("Optimized UI components enabled")
            
        except Exception as e:
            print(f"Failed to enable optimizations: {e}")
            self.is_optimized = False
    
    def _replace_track_table(self):
        """Replace the existing track table with optimized version"""
        try:
            # Get the parent layout
            central_widget = self.main_window.centralWidget()
            if not central_widget:
                return
            
            # Find the table in the layout
            old_table = self.main_window.track_table
            parent_layout = old_table.parent().layout()
            
            if parent_layout:
                # Remove old table
                parent_layout.removeWidget(old_table)
                old_table.hide()
                
                # Add new optimized view
                parent_layout.addWidget(self.track_view)
                
                # Copy existing tracks
                tracks = self.main_window.facade.get_tracks()
                if tracks:
                    self.track_view.setTracks(tracks)
                
                print("Track table replaced with optimized version")
                
        except Exception as e:
            print(f"Failed to replace track table: {e}")
    
    def _replace_progress_bar(self):
        """Replace the existing progress bar with optimized version"""
        try:
            # Get the parent layout
            old_progress = self.main_window.progress_bar
            parent_layout = old_progress.parent().layout()
            
            if parent_layout:
                # Remove old progress bar
                parent_layout.removeWidget(old_progress)
                old_progress.hide()
                
                # Add new optimized progress manager
                parent_layout.addWidget(self.progress_manager)
                
                print("Progress bar replaced with optimized version")
                
        except Exception as e:
            print(f"Failed to replace progress bar: {e}")
    
    def on_track_selected(self, track):
        """Handle track selection in optimized view"""
        # Update main window state
        if hasattr(self.main_window, 'current_track'):
            self.main_window.current_track = track
        
        # Update button states
        if hasattr(self.main_window, 'update_button_states'):
            self.main_window.update_button_states()
    
    def on_tracks_filtered(self, filtered_tracks):
        """Handle track filtering"""
        # Update performance stats
        self.performance_stats['search_operations'] += 1
        
        # Update main window if needed
        if hasattr(self.main_window, 'status_bar'):
            self.main_window.status_bar.show_info(
                f"Showing {len(filtered_tracks)} of {len(self.track_view.tracks)} tracks"
            )
    
    def add_track(self, track):
        """Add track through optimized components"""
        if self.is_optimized and self.track_view:
            self.track_view.add_track(track)
            self.performance_stats['track_loads'] += 1
        else:
            # Fall back to original method
            self.main_window.add_track_to_table(track)
    
    def update_progress(self, current: int, total: int, message: str = ""):
        """Update progress through optimized components"""
        if self.is_optimized and self.progress_manager:
            self.progress_manager.update_progress(current, total, message)
        else:
            # Fall back to original method
            if hasattr(self.main_window, 'update_progress'):
                self.main_window.update_progress(current, total)
    
    def clear_tracks(self):
        """Clear tracks through optimized components"""
        if self.is_optimized and self.track_view:
            self.track_view.clear_tracks()
        else:
            # Fall back to original method
            if hasattr(self.main_window, 'clear_track_table'):
                self.main_window.clear_track_table()
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        stats = self.performance_stats.copy()
        
        if self.is_optimized:
            if self.track_view:
                stats['track_view'] = {
                    'total_tracks': len(self.track_view.tracks),
                    'filtered_tracks': len(self.track_view.filtered_tracks),
                    'cache_stats': track_cache.get_stats()
                }
            
            if self.progress_manager:
                stats['progress_manager'] = self.progress_manager.progress_manager.get_performance_stats()
        
        stats['optimized'] = self.is_optimized
        return stats
    
    def cleanup(self):
        """Cleanup integration resources"""
        if self.track_view:
            self.track_view.cleanup()
        
        if self.progress_manager:
            self.progress_manager.cleanup()
        
        # Clear cache
        cache_manager.clear_all()


def create_integration(main_window) -> MainWindowIntegration:
    """Create and return a main window integration"""
    return MainWindowIntegration(main_window)