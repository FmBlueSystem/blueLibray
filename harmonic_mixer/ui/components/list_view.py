"""
List View Widget for BlueLibrary DJ
Displays tracks as a compact list with essential information
"""

from typing import List
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, 
                             QFrame, QLabel, QListWidget, QListWidgetItem,
                             QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QPalette


class TrackListItem(QFrame):
    """Individual track list item widget"""
    
    track_selected = pyqtSignal(object)
    track_double_clicked = pyqtSignal(object)
    
    def __init__(self, track, parent=None):
        super().__init__(parent)
        self.track = track
        self.setup_ui()
        self.setFixedHeight(60)
        self.setStyleSheet("""
            TrackListItem {
                border: 1px solid #374151;
                border-radius: 4px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1a202c, stop:1 #161b22);
                margin: 1px;
                padding: 4px;
            }
            TrackListItem:hover {
                border: 1px solid #3b82f6;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #21262d, stop:1 #1a202c);
            }
        """)
    
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)
        
        # Main info (title, artist)
        main_info_layout = QVBoxLayout()
        main_info_layout.setSpacing(2)
        
        title_label = QLabel(getattr(self.track, 'title', 'Unknown Title'))
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(11)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #ffffff;")
        main_info_layout.addWidget(title_label)
        
        artist_label = QLabel(getattr(self.track, 'artist', 'Unknown Artist'))
        artist_label.setStyleSheet("color: #e2e8f0; font-size: 9px;")
        main_info_layout.addWidget(artist_label)
        
        layout.addLayout(main_info_layout, 3)  # 3 parts width
        
        # Key info
        key_layout = QVBoxLayout()
        key_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        key_label = QLabel("Key")
        key_label.setStyleSheet("color: #a0aec0; font-size: 8px;")
        key_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        key_layout.addWidget(key_label)
        
        key_value = QLabel(str(getattr(self.track, 'key', 'N/A')))
        key_value.setStyleSheet("color: #3b82f6; font-weight: bold; font-size: 11px;")
        key_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        key_layout.addWidget(key_value)
        
        layout.addLayout(key_layout, 1)  # 1 part width
        
        # BPM info
        bpm_layout = QVBoxLayout()
        bpm_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bpm_label = QLabel("BPM")
        bpm_label.setStyleSheet("color: #a0aec0; font-size: 8px;")
        bpm_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bpm_layout.addWidget(bpm_label)
        
        bpm_value = QLabel(str(getattr(self.track, 'bpm', 0)))
        bpm_value.setStyleSheet("color: #06b6d4; font-weight: bold; font-size: 11px;")
        bpm_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bpm_layout.addWidget(bpm_value)
        
        layout.addLayout(bpm_layout, 1)  # 1 part width
        
        # Energy info
        energy_layout = QVBoxLayout()
        energy_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        energy_label = QLabel("Energy")
        energy_label.setStyleSheet("color: #a0aec0; font-size: 8px;")
        energy_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        energy_layout.addWidget(energy_label)
        
        energy_value = getattr(self.track, 'energy', 0)
        energy_display = QLabel(f"{energy_value:.1f}")
        energy_color = self.get_energy_color(energy_value)
        energy_display.setStyleSheet(f"color: {energy_color}; font-weight: bold; font-size: 11px;")
        energy_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        energy_layout.addWidget(energy_display)
        
        layout.addLayout(energy_layout, 1)  # 1 part width
        
        # Genre info
        genre_layout = QVBoxLayout()
        genre_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        genre_label = QLabel("Genre")
        genre_label.setStyleSheet("color: #a0aec0; font-size: 8px;")
        genre_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        genre_layout.addWidget(genre_label)
        
        genre_value = QLabel(str(getattr(self.track, 'genre', 'Unknown'))[:10])  # Truncate long genres
        genre_value.setStyleSheet("color: #cbd5e0; font-size: 9px;")
        genre_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        genre_layout.addWidget(genre_value)
        
        layout.addLayout(genre_layout, 1)  # 1 part width
        
        # Enhanced indicator
        if hasattr(self.track, 'enhanced_data') and self.track.enhanced_data:
            enhanced_label = QLabel("✨")
            enhanced_label.setStyleSheet("color: #10b981; font-size: 16px;")
            enhanced_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            enhanced_label.setToolTip("Enhanced with AI metadata")
            layout.addWidget(enhanced_label)
    
    def get_energy_color(self, energy: float) -> str:
        """Get color based on energy level"""
        if energy >= 8.0:
            return "#ec4899"  # Pink for very high
        elif energy >= 6.0:
            return "#ef4444"  # Red for high
        elif energy >= 4.0:
            return "#f59e0b"  # Amber for medium
        else:
            return "#6b7280"  # Gray for low
    
    def mousePressEvent(self, event):
        """Handle mouse press for selection"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.track_selected.emit(self.track)
        super().mousePressEvent(event)
    
    def mouseDoubleClickEvent(self, event):
        """Handle double click"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.track_double_clicked.emit(self.track)
        super().mouseDoubleClickEvent(event)


class ListView(QWidget):
    """List view for displaying tracks as compact list items"""
    
    track_selected = pyqtSignal(object)
    track_double_clicked = pyqtSignal(object)
    
    def __init__(self, facade=None, parent=None):
        super().__init__(parent)
        self.facade = facade
        self.tracks = []
        self.list_items = []
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header with column labels
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2d3748, stop:1 #1a202c);
                border: 1px solid #374151;
                border-radius: 4px;
                padding: 4px;
            }
        """)
        header_frame.setFixedHeight(30)
        
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(8, 4, 8, 4)
        
        # Header labels
        title_header = QLabel("Track")
        title_header.setStyleSheet("color: #63b3ed; font-weight: bold; font-size: 10px;")
        header_layout.addWidget(title_header, 3)
        
        for label_text in ["Key", "BPM", "Energy", "Genre"]:
            label = QLabel(label_text)
            label.setStyleSheet("color: #63b3ed; font-weight: bold; font-size: 10px;")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            header_layout.addWidget(label, 1)
        
        layout.addWidget(header_frame)
        
        # Scroll area for list items
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Container widget for list items
        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setSpacing(2)
        self.list_layout.setContentsMargins(4, 4, 4, 4)
        
        self.scroll_area.setWidget(self.list_container)
        layout.addWidget(self.scroll_area)
    
    def setTracks(self, tracks: List):
        """Set tracks to display as list items"""
        self.tracks = tracks
        self.update_list()
    
    def update_list(self):
        """Update the list display"""
        # Clear existing items
        for item in self.list_items:
            item.setParent(None)
        self.list_items.clear()
        
        # Add new items
        for track in self.tracks:
            item = TrackListItem(track)
            item.track_selected.connect(self.track_selected.emit)
            item.track_double_clicked.connect(self.track_double_clicked.emit)
            
            self.list_layout.addWidget(item)
            self.list_items.append(item)
        
        # Add stretch to push items to top
        self.list_layout.addStretch()