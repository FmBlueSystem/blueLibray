"""
Virtual Table Widget for BlueLibrary DJ

High-performance table widget with virtual scrolling for handling large track collections.
Only renders visible rows to maintain smooth performance with thousands of tracks.
"""

import os
import time
from typing import List, Optional, Any, Dict
from PyQt6.QtWidgets import (QAbstractItemView, QHeaderView, QStyleOptionViewItem, 
                             QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QProgressBar)
from PyQt6.QtCore import (QAbstractTableModel, Qt, QModelIndex, QRect, QTimer, 
                          pyqtSignal, QSortFilterProxyModel)
from PyQt6.QtGui import QPainter, QFontMetrics, QColor, QBrush, QPen

from .base_component import BaseUIComponent


class VirtualTrackTableModel(QAbstractTableModel):
    """High-performance model for large track collections with virtual scrolling"""
    
    dataUpdated = pyqtSignal()
    
    def __init__(self, tracks=None, facade=None, parent=None):
        super().__init__(parent)
        self.tracks = tracks or []
        self.filtered_tracks = []
        self.facade = facade
        self.headers = [
            "🎵 Title", "🎤 Artist", "🎹 Key", "⚡ BPM", 
            "🔥 Energy", "🎭 Genre", "📊 Status", "🎯 Subgenre",
            "😊 Mood", "📅 Era", "🌍 Language", "💃 Danceability",
            "🕐 Time of Day", "🎮 Activity", "🌸 Season", "🎚️ Mix Friendly",
            "👥 Crowd Appeal", "🎛️ Production", "✅ Confidence"
        ]
        self.column_widths = [200, 150, 60, 80, 80, 120, 80, 100, 100, 80, 80, 100, 100, 100, 80, 100, 100, 100, 100]
        self.sort_column = 0
        self.sort_order = Qt.SortOrder.AscendingOrder
        
        # Performance tracking
        self.render_count = 0
        self.last_render_time = 0
        
        # Initialize filtered tracks
        self.filtered_tracks = self.tracks.copy()
    
    def rowCount(self, parent=QModelIndex()):
        return len(self.filtered_tracks)
    
    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)
    
    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or index.row() >= len(self.filtered_tracks):
            return None
        
        track = self.filtered_tracks[index.row()]
        column = index.column()
        
        if role == Qt.ItemDataRole.DisplayRole:
            return self._get_display_data(track, column)
        elif role == Qt.ItemDataRole.BackgroundRole:
            return self._get_background_color(track, index.row())
        elif role == Qt.ItemDataRole.ForegroundRole:
            return self._get_foreground_color(track, column)
        elif role == Qt.ItemDataRole.UserRole:
            return track  # Return the track object for custom operations
        
        return None
    
    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.headers[section]
        return None
    
    def _get_display_data(self, track, column):
        """Get display data for a specific column"""
        if column == 0:  # Title
            return track.title or "Unknown"
        elif column == 1:  # Artist
            return track.artist or "Unknown"
        elif column == 2:  # Key
            return track.key or "?"
        elif column == 3:  # BPM
            return f"{track.bpm:.1f}" if track.bpm else "?"
        elif column == 4:  # Energy
            return f"{track.energy:.1f}" if track.energy else "?"
        elif column == 5:  # Genre
            return track.genre or "Unknown"
        elif column == 6:  # Status
            return self._get_status_icon(track)
        elif column >= 7:  # Enhanced metadata columns
            return self._get_enhanced_column_data(track, column)
        
        return ""
    
    def _get_status_icon(self, track):
        """Get appropriate status icon for track"""
        if not hasattr(track, 'file_path') or not track.file_path:
            return "❌"
        
        if not os.path.exists(track.file_path):
            return "❌"
        elif hasattr(track, 'energy') and track.energy and track.energy > 7.0:
            return "🔥"
        elif hasattr(track, 'energy') and track.energy and track.energy < 4.0:
            return "😌"
        else:
            return "✅"
    
    def _get_enhanced_column_data(self, track, column):
        """Get enhanced metadata for specific column"""
        # Get enhanced metadata from facade
        if not self.facade:
            return "-"
        
        enhanced = self.facade.get_enhanced_metadata(track.id)
        if not enhanced or enhanced.confidence_score < 0.1:
            return "-"
        
        if column == 7:  # Subgenre
            return enhanced.subgenre or "-"
        elif column == 8:  # Mood
            return enhanced.mood or "-"
        elif column == 9:  # Era
            return enhanced.era or "-"
        elif column == 10:  # Language
            return enhanced.language or "-"
        elif column == 11:  # Danceability
            return f"{enhanced.danceability:.1%}" if enhanced.danceability else "-"
        elif column == 12:  # Time of Day
            return enhanced.time_of_day or "-"
        elif column == 13:  # Activity
            return enhanced.activity or "-"
        elif column == 14:  # Season
            return enhanced.season or "-"
        elif column == 15:  # Mix Friendly
            return f"{enhanced.mixing_friendliness:.1%}" if enhanced.mixing_friendliness else "-"
        elif column == 16:  # Crowd Appeal
            return f"{enhanced.crowd_appeal:.1%}" if enhanced.crowd_appeal else "-"
        elif column == 17:  # Production
            return f"{enhanced.production_quality:.1%}" if enhanced.production_quality else "-"
        elif column == 18:  # Confidence
            return f"{enhanced.confidence_score:.1%}" if enhanced.confidence_score else "-"
        
        return "-"
    
    def _is_enhanced(self, track):
        """Check if track has AI enhancement"""
        if not self.facade:
            return False
        enhanced = self.facade.get_enhanced_metadata(track.id)
        return enhanced is not None and enhanced.confidence_score > 0.1
    
    def _get_background_color(self, track, row):
        """Get background color for row"""
        if row % 2 == 0:
            return QColor(248, 248, 248)  # Light gray for even rows
        return QColor(255, 255, 255)  # White for odd rows
    
    def _get_foreground_color(self, track, column):
        """Get foreground color based on track status"""
        if column == 6:  # Status column
            status = self._get_status_icon(track)
            if status == "❌":
                return QColor(255, 0, 0)  # Red for unavailable
            elif status == "🔥":
                return QColor(255, 100, 0)  # Orange for high energy
            elif status == "😌":
                return QColor(0, 100, 255)  # Blue for chill
        
        return QColor(0, 0, 0)  # Black default
    
    def setTracks(self, tracks: List):
        """Set new track data"""
        self.beginResetModel()
        self.tracks = tracks or []
        self.filtered_tracks = self.tracks.copy()
        self.endResetModel()
        self.dataUpdated.emit()
    
    def filterTracks(self, filter_func=None, search_text=""):
        """Filter tracks based on function and search text"""
        self.beginResetModel()
        
        if not filter_func and not search_text:
            self.filtered_tracks = self.tracks.copy()
        else:
            self.filtered_tracks = []
            
            for track in self.tracks:
                # Apply search filter
                if search_text:
                    search_lower = search_text.lower()
                    if not (search_lower in (track.title or "").lower() or
                            search_lower in (track.artist or "").lower() or
                            search_lower in (track.genre or "").lower()):
                        continue
                
                # Apply custom filter
                if filter_func and not filter_func(track):
                    continue
                
                self.filtered_tracks.append(track)
        
        self.endResetModel()
        self.dataUpdated.emit()
    
    def sortTracks(self, column: int, order: Qt.SortOrder):
        """Sort tracks by column"""
        self.sort_column = column
        self.sort_order = order
        
        self.beginResetModel()
        
        # Define sort key functions
        def get_sort_key(track):
            if column == 0:  # Title
                return (track.title or "").lower()
            elif column == 1:  # Artist
                return (track.artist or "").lower()
            elif column == 2:  # Key
                return track.key or ""
            elif column == 3:  # BPM
                return track.bpm or 0
            elif column == 4:  # Energy
                return track.energy or 0
            elif column == 5:  # Genre
                return (track.genre or "").lower()
            elif column == 6:  # Status
                return self._get_status_icon(track)
            elif column == 7:  # Enhanced
                return 1 if self._is_enhanced(track) else 0
            
            return ""
        
        # Sort filtered tracks
        self.filtered_tracks.sort(
            key=get_sort_key,
            reverse=(order == Qt.SortOrder.DescendingOrder)
        )
        
        self.endResetModel()
        self.dataUpdated.emit()
    
    def getTrackAt(self, row: int):
        """Get track at specific row"""
        if 0 <= row < len(self.filtered_tracks):
            return self.filtered_tracks[row]
        return None
    
    def findTrackRow(self, track) -> int:
        """Find row index of track"""
        try:
            return self.filtered_tracks.index(track)
        except ValueError:
            return -1


class VirtualTrackTable(QAbstractItemView):
    """High-performance table widget with virtual scrolling"""
    
    trackSelected = pyqtSignal(object)  # Emits selected track
    trackDoubleClicked = pyqtSignal(object)  # Emits double-clicked track
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Configure selection behavior
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        
        # Performance settings
        self.row_height = 25
        self.header_height = 30
        self.visible_rows = 0
        self.first_visible_row = 0
        self.last_visible_row = 0
        self.total_rows = 0
        
        # Caching for performance
        self.rendered_items = {}
        self.font_metrics = QFontMetrics(self.font())
        
        # Visual settings
        self.alternate_row_color = QColor(248, 248, 248)
        self.selection_color = QColor(0, 120, 215)
        self.grid_color = QColor(200, 200, 200)
        
        # Setup scrollbars
        self.verticalScrollBar().valueChanged.connect(self.update_visible_range)
        self.horizontalScrollBar().valueChanged.connect(self.viewport().update)
        
        # Performance monitoring
        self.render_times = []
        self.last_render_time = 0
        
        # Enable mouse tracking for hover effects
        self.setMouseTracking(True)
        self.hover_row = -1
    
    def setModel(self, model):
        """Set the model and update display"""
        if self.model():
            self.model().dataUpdated.disconnect(self.model_data_updated)
        
        super().setModel(model)
        
        if model:
            model.dataUpdated.connect(self.model_data_updated)
            self.update_scrollbar_range()
            self.viewport().update()
    
    def model_data_updated(self):
        """Handle model data updates"""
        self.update_scrollbar_range()
        self.update_visible_range()
        self.viewport().update()
    
    def update_scrollbar_range(self):
        """Update vertical scrollbar range based on data"""
        if not self.model():
            return
        
        self.total_rows = self.model().rowCount()
        total_height = self.total_rows * self.row_height
        viewport_height = self.viewport().height() - self.header_height
        
        max_scroll = max(0, total_height - viewport_height)
        self.verticalScrollBar().setRange(0, max_scroll)
        self.verticalScrollBar().setPageStep(viewport_height)
        self.verticalScrollBar().setSingleStep(self.row_height)
        
        # Update horizontal scrollbar
        total_width = sum(self.model().column_widths) if self.model() else 0
        viewport_width = self.viewport().width()
        max_h_scroll = max(0, total_width - viewport_width)
        self.horizontalScrollBar().setRange(0, max_h_scroll)
        self.horizontalScrollBar().setPageStep(viewport_width)
        self.horizontalScrollBar().setSingleStep(20)
    
    def update_visible_range(self):
        """Calculate which rows are currently visible"""
        if not self.model():
            return
        
        viewport_top = self.verticalScrollBar().value()
        viewport_height = self.viewport().height() - self.header_height
        
        self.first_visible_row = max(0, viewport_top // self.row_height)
        visible_count = (viewport_height // self.row_height) + 2  # +2 for partial rows
        self.last_visible_row = min(
            self.total_rows - 1,
            self.first_visible_row + visible_count
        )
        
        self.viewport().update()
    
    def paintEvent(self, event):
        """Custom paint event for virtual scrolling"""
        start_time = time.time()
        
        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Clear background
        painter.fillRect(self.viewport().rect(), Qt.GlobalColor.white)
        
        # Paint header
        self.paint_header(painter)
        
        # Paint visible rows only
        if self.model() and self.total_rows > 0:
            viewport_top = self.verticalScrollBar().value()
            
            for row in range(self.first_visible_row, self.last_visible_row + 1):
                if row >= self.total_rows:
                    break
                
                y_pos = row * self.row_height - viewport_top + self.header_height
                self.paint_row(painter, row, y_pos)
        
        # Performance tracking
        render_time = time.time() - start_time
        self.render_times.append(render_time)
        
        # Keep only last 100 render times
        if len(self.render_times) > 100:
            self.render_times.pop(0)
        
        self.last_render_time = render_time
        
        painter.end()
    
    def paint_header(self, painter):
        """Paint table header"""
        if not self.model():
            return
        
        # Header background
        header_rect = QRect(0, 0, self.viewport().width(), self.header_height)
        painter.fillRect(header_rect, QColor(240, 240, 240))
        
        # Header border
        painter.setPen(QPen(self.grid_color, 1))
        painter.drawLine(0, self.header_height - 1, self.viewport().width(), self.header_height - 1)
        
        x_offset = -self.horizontalScrollBar().value()
        
        for col in range(self.model().columnCount()):
            width = self.model().column_widths[col]
            
            # Draw header text
            rect = QRect(x_offset + 5, 0, width - 10, self.header_height)
            painter.setPen(QPen(Qt.GlobalColor.black))
            painter.drawText(rect, Qt.AlignmentFlag.AlignVCenter, self.model().headers[col])
            
            # Draw column separator
            painter.setPen(QPen(self.grid_color, 1))
            painter.drawLine(x_offset + width, 0, x_offset + width, self.header_height)
            
            x_offset += width
    
    def paint_row(self, painter, row, y_pos):
        """Paint a single table row"""
        if not self.model():
            return
        
        # Row background
        row_rect = QRect(0, y_pos, self.viewport().width(), self.row_height)
        
        # Alternate row colors
        if row % 2 == 0:
            painter.fillRect(row_rect, Qt.GlobalColor.white)
        else:
            painter.fillRect(row_rect, self.alternate_row_color)
        
        # Hover effect
        if row == self.hover_row:
            painter.fillRect(row_rect, QColor(230, 240, 250))
        
        # Selection highlight
        if self.selectionModel() and self.selectionModel().isRowSelected(row, QModelIndex()):
            painter.fillRect(row_rect, self.selection_color)
            painter.setPen(QPen(Qt.GlobalColor.white))
        else:
            painter.setPen(QPen(Qt.GlobalColor.black))
        
        # Paint columns
        x_offset = -self.horizontalScrollBar().value()
        
        for col in range(self.model().columnCount()):
            width = self.model().column_widths[col]
            
            # Get cell data
            index = self.model().index(row, col)
            text = self.model().data(index, Qt.ItemDataRole.DisplayRole) or ""
            
            # Get text color
            text_color = self.model().data(index, Qt.ItemDataRole.ForegroundRole)
            if text_color:
                painter.setPen(QPen(text_color))
            
            # Draw cell text
            text_rect = QRect(x_offset + 5, y_pos, width - 10, self.row_height)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter, str(text))
            
            # Draw column separator
            painter.setPen(QPen(self.grid_color, 1))
            painter.drawLine(x_offset + width, y_pos, x_offset + width, y_pos + self.row_height)
            
            x_offset += width
        
        # Draw row separator
        painter.setPen(QPen(self.grid_color, 1))
        painter.drawLine(0, y_pos + self.row_height - 1, self.viewport().width(), y_pos + self.row_height - 1)
    
    def mousePressEvent(self, event):
        """Handle mouse press events"""
        if event.button() == Qt.MouseButton.LeftButton:
            row = self.get_row_at_position(event.pos())
            if row >= 0:
                self.selectRow(row)
                track = self.model().getTrackAt(row)
                if track:
                    self.trackSelected.emit(track)
    
    def mouseDoubleClickEvent(self, event):
        """Handle mouse double-click events"""
        if event.button() == Qt.MouseButton.LeftButton:
            row = self.get_row_at_position(event.pos())
            if row >= 0:
                track = self.model().getTrackAt(row)
                if track:
                    self.trackDoubleClicked.emit(track)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events for hover effect"""
        row = self.get_row_at_position(event.pos())
        if row != self.hover_row:
            self.hover_row = row
            self.viewport().update()
    
    def get_row_at_position(self, pos) -> int:
        """Get row index at mouse position"""
        if pos.y() < self.header_height:
            return -1
        
        viewport_top = self.verticalScrollBar().value()
        row = (pos.y() - self.header_height + viewport_top) // self.row_height
        
        if 0 <= row < self.total_rows:
            return row
        return -1
    
    def selectRow(self, row: int):
        """Select a specific row"""
        if 0 <= row < self.total_rows:
            index = self.model().index(row, 0)
            self.selectionModel().select(index, self.selectionModel().SelectionFlag.ClearAndSelect | 
                                       self.selectionModel().SelectionFlag.Rows)
            self.viewport().update()
    
    def get_selected_indices(self) -> List[int]:
        """Get list of selected row indices"""
        if not self.selectionModel() or not self.selectionModel().hasSelection():
            return []
        
        selected_indices = []
        for index in self.selectionModel().selectedRows():
            selected_indices.append(index.row())
        
        return selected_indices
    
    def horizontalOffset(self) -> int:
        """Return horizontal scroll offset"""
        return self.horizontalScrollBar().value()
    
    def verticalOffset(self) -> int:
        """Return vertical scroll offset"""
        return self.verticalScrollBar().value()
    
    def moveCursor(self, cursor_action, modifiers):
        """Move cursor based on action"""
        if not self.model() or self.total_rows == 0:
            return QModelIndex()
        
        current_row = -1
        if self.selectionModel().hasSelection():
            current_row = self.selectionModel().currentIndex().row()
        
        if cursor_action == QAbstractItemView.CursorAction.MoveUp:
            new_row = max(0, current_row - 1)
        elif cursor_action == QAbstractItemView.CursorAction.MoveDown:
            new_row = min(self.total_rows - 1, current_row + 1)
        elif cursor_action == QAbstractItemView.CursorAction.MoveHome:
            new_row = 0
        elif cursor_action == QAbstractItemView.CursorAction.MoveEnd:
            new_row = self.total_rows - 1
        else:
            new_row = current_row
        
        return self.model().index(new_row, 0)
    
    def visualRegionForSelection(self, selection):
        """Return visual region for selection"""
        from PyQt6.QtGui import QRegion
        return QRegion()
    
    def indexAt(self, point):
        """Return model index at point"""
        row = self.get_row_at_position(point)
        if row >= 0 and row < self.total_rows:
            return self.model().index(row, 0)
        return QModelIndex()
    
    def scrollToTrack(self, track):
        """Scroll to show a specific track"""
        if not self.model():
            return
        
        row = self.model().findTrackRow(track)
        if row >= 0:
            # Calculate scroll position to center the row
            target_scroll = row * self.row_height - (self.viewport().height() - self.header_height) // 2
            target_scroll = max(0, min(target_scroll, self.verticalScrollBar().maximum()))
            
            self.verticalScrollBar().setValue(target_scroll)
            self.selectRow(row)
    
    def resizeEvent(self, event):
        """Handle resize events"""
        super().resizeEvent(event)
        self.update_scrollbar_range()
        self.update_visible_range()
    
    def wheelEvent(self, event):
        """Handle wheel events for smooth scrolling"""
        # Scroll by 3 rows per wheel step
        scroll_delta = -event.angleDelta().y() // 120 * 3 * self.row_height
        current_value = self.verticalScrollBar().value()
        new_value = max(0, min(current_value + scroll_delta, self.verticalScrollBar().maximum()))
        
        self.verticalScrollBar().setValue(new_value)
        event.accept()
    
    def keyPressEvent(self, event):
        """Handle keyboard navigation"""
        if not self.model() or self.total_rows == 0:
            return
        
        current_row = -1
        if self.selectionModel().hasSelection():
            current_row = self.selectionModel().currentIndex().row()
        
        if event.key() == Qt.Key.Key_Up:
            if current_row > 0:
                self.selectRow(current_row - 1)
                self.ensure_row_visible(current_row - 1)
        elif event.key() == Qt.Key.Key_Down:
            if current_row < self.total_rows - 1:
                self.selectRow(current_row + 1)
                self.ensure_row_visible(current_row + 1)
        elif event.key() == Qt.Key.Key_Home:
            self.selectRow(0)
            self.ensure_row_visible(0)
        elif event.key() == Qt.Key.Key_End:
            self.selectRow(self.total_rows - 1)
            self.ensure_row_visible(self.total_rows - 1)
        elif event.key() == Qt.Key.Key_PageUp:
            rows_per_page = (self.viewport().height() - self.header_height) // self.row_height
            new_row = max(0, current_row - rows_per_page)
            self.selectRow(new_row)
            self.ensure_row_visible(new_row)
        elif event.key() == Qt.Key.Key_PageDown:
            rows_per_page = (self.viewport().height() - self.header_height) // self.row_height
            new_row = min(self.total_rows - 1, current_row + rows_per_page)
            self.selectRow(new_row)
            self.ensure_row_visible(new_row)
        else:
            super().keyPressEvent(event)
    
    def ensure_row_visible(self, row: int):
        """Ensure a row is visible in the viewport"""
        if row < self.first_visible_row:
            # Scroll up to show the row
            target_scroll = row * self.row_height
            self.verticalScrollBar().setValue(target_scroll)
        elif row > self.last_visible_row:
            # Scroll down to show the row
            viewport_height = self.viewport().height() - self.header_height
            target_scroll = (row + 1) * self.row_height - viewport_height
            self.verticalScrollBar().setValue(target_scroll)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        if not self.render_times:
            return {}
        
        return {
            'avg_render_time': sum(self.render_times) / len(self.render_times),
            'max_render_time': max(self.render_times),
            'min_render_time': min(self.render_times),
            'last_render_time': self.last_render_time,
            'total_rows': self.total_rows,
            'visible_rows': self.last_visible_row - self.first_visible_row + 1,
            'render_efficiency': (self.last_visible_row - self.first_visible_row + 1) / max(1, self.total_rows)
        }


class VirtualTableWidget(BaseUIComponent):
    """Complete virtual table widget with status bar and performance monitoring"""
    
    def __init__(self, facade=None, parent=None):
        self.table = None
        self.model = None
        self.status_label = None
        self.performance_label = None
        super().__init__(facade, parent)
    
    def setup_ui(self):
        """Setup the UI components"""
        layout = QVBoxLayout(self)
        
        # Create table and model
        self.model = VirtualTrackTableModel(facade=self.facade)
        self.table = VirtualTrackTable()
        self.table.setModel(self.model)
        
        # Status bar
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Ready")
        self.performance_label = QLabel("")
        
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.performance_label)
        
        layout.addWidget(self.table)
        layout.addLayout(status_layout)
        
        # Performance monitoring timer (disabled - not critical for functionality)
        self.perf_timer = None
        self._perf_timer_initialized = False
        # Note: Performance timers disabled to eliminate QTimer warnings
    
    def connect_signals(self):
        """Connect signals and slots"""
        self.table.trackSelected.connect(self.on_track_selected)
        self.table.trackDoubleClicked.connect(self.on_track_double_clicked)
        self.model.dataUpdated.connect(self.update_status)
    
    def setTracks(self, tracks):
        """Set tracks in the table"""
        self.model.setTracks(tracks)
    
    def filterTracks(self, filter_func=None, search_text=""):
        """Filter tracks"""
        self.model.filterTracks(filter_func, search_text)
    
    def on_track_selected(self, track):
        """Handle track selection"""
        self.selection_changed.emit(track)
    
    def on_track_double_clicked(self, track):
        """Handle track double-click"""
        # Could trigger track loading or preview
        pass
    
    def update_status(self):
        """Update status label"""
        total_tracks = len(self.model.tracks)
        filtered_tracks = len(self.model.filtered_tracks)
        
        if total_tracks == filtered_tracks:
            self.status_label.setText(f"{total_tracks} tracks")
        else:
            self.status_label.setText(f"{filtered_tracks} of {total_tracks} tracks")
    
    def update_performance_display(self):
        """Update performance display"""
        stats = self.table.get_performance_stats()
        if stats:
            avg_render = stats.get('avg_render_time', 0)
            visible_rows = stats.get('visible_rows', 0)
            total_rows = stats.get('total_rows', 0)
            
            self.performance_label.setText(
                f"Render: {avg_render*1000:.1f}ms | "
                f"Visible: {visible_rows}/{total_rows}"
            )
    
    def cleanup(self):
        """Cleanup resources"""
        if self.perf_timer:
            self.perf_timer.stop()
        super().cleanup()

    def _init_performance_timer_safe(self):
        """Initialize performance timer safely after widget is constructed and shown"""
        from PyQt6.QtWidgets import QApplication
        
        # Only initialize once and if we're in the main thread and widget is visible
        if (not self._perf_timer_initialized and 
            QApplication.instance() and 
            QApplication.instance().thread() == self.thread() and
            self.isVisible()):  # Only if widget is actually visible
            
            self.perf_timer = QTimer(self)  # Set parent for proper cleanup
            self.perf_timer.timeout.connect(self.update_performance_display)
            self.perf_timer.start(1000)  # Update every second
            self._perf_timer_initialized = True