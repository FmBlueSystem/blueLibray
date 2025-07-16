"""
Cards View Widget for BlueLibrary DJ
Displays tracks as cards with enhanced visual information
"""

from typing import List
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, 
                             QFrame, QLabel, QPushButton, QGridLayout, QSpacerItem,
                             QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPalette


class TrackCard(QFrame):
    """Individual track card widget"""
    
    track_selected = pyqtSignal(object)
    track_double_clicked = pyqtSignal(object)
    
    def __init__(self, track, parent=None):
        super().__init__(parent)
        self.track = track
        self.setup_ui()
        self.setFrameStyle(QFrame.Shape.Box)
        self.setStyleSheet("""
            TrackCard {
                border: 2px solid #374151;
                border-radius: 8px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #21262d, stop:1 #161b22);
                margin: 4px;
                padding: 8px;
            }
            TrackCard:hover {
                border: 2px solid #3b82f6;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #30363d, stop:1 #21262d);
            }
        """)
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        
        # Title and Artist
        title_label = QLabel(getattr(self.track, 'title', 'Unknown Title'))
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #ffffff; margin-bottom: 2px;")
        layout.addWidget(title_label)
        
        artist_label = QLabel(getattr(self.track, 'artist', 'Unknown Artist'))
        artist_label.setStyleSheet("color: #e2e8f0; font-size: 10px;")
        layout.addWidget(artist_label)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #374151; margin: 4px 0;")
        layout.addWidget(separator)
        
        # Track info grid
        info_layout = QGridLayout()
        info_layout.setSpacing(2)
        
        # Key and BPM
        key_value = getattr(self.track, 'key', 'N/A')
        bpm_value = getattr(self.track, 'bpm', 0)
        
        info_layout.addWidget(QLabel("Key:"), 0, 0)
        key_label = QLabel(str(key_value))
        key_label.setStyleSheet("color: #3b82f6; font-weight: bold;")
        info_layout.addWidget(key_label, 0, 1)
        
        info_layout.addWidget(QLabel("BPM:"), 0, 2)
        bpm_label = QLabel(str(bpm_value))
        bpm_label.setStyleSheet("color: #06b6d4; font-weight: bold;")
        info_layout.addWidget(bpm_label, 0, 3)
        
        # Energy and Genre
        energy_value = getattr(self.track, 'energy', 0)
        genre_value = getattr(self.track, 'genre', 'Unknown')
        
        info_layout.addWidget(QLabel("Energy:"), 1, 0)
        energy_label = QLabel(f"{energy_value:.1f}")
        energy_color = self.get_energy_color(energy_value)
        energy_label.setStyleSheet(f"color: {energy_color}; font-weight: bold;")
        info_layout.addWidget(energy_label, 1, 1)
        
        info_layout.addWidget(QLabel("Genre:"), 1, 2)
        genre_label = QLabel(str(genre_value))
        genre_label.setStyleSheet("color: #cbd5e0; font-size: 9px;")
        info_layout.addWidget(genre_label, 1, 3)
        
        # Style all info labels
        for i in range(info_layout.count()):
            widget = info_layout.itemAt(i).widget()
            if isinstance(widget, QLabel) and widget.text().endswith(':'):
                widget.setStyleSheet("color: #a0aec0; font-size: 9px; font-weight: 500;")
        
        layout.addLayout(info_layout)
        
        # Enhanced indicator
        if hasattr(self.track, 'enhanced_data') and self.track.enhanced_data:
            enhanced_label = QLabel("✨ Enhanced")
            enhanced_label.setStyleSheet("""
                color: #10b981; 
                background-color: rgba(16, 185, 129, 0.1);
                border: 1px solid #10b981;
                border-radius: 3px;
                padding: 2px 4px;
                font-size: 8px;
                font-weight: bold;
            """)
            enhanced_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(enhanced_label)
        
        layout.addStretch()
    
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


class CardsView(QWidget):
    """Cards view for displaying tracks as cards"""
    
    track_selected = pyqtSignal(object)
    track_double_clicked = pyqtSignal(object)
    
    def __init__(self, facade=None, parent=None):
        super().__init__(parent)
        self.facade = facade
        self.tracks = []
        self.cards = []
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Scroll area for cards
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Container widget for cards
        self.cards_container = QWidget()
        self.cards_layout = QGridLayout(self.cards_container)
        self.cards_layout.setSpacing(8)
        self.cards_layout.setContentsMargins(8, 8, 8, 8)
        
        self.scroll_area.setWidget(self.cards_container)
        layout.addWidget(self.scroll_area)
    
    def setTracks(self, tracks: List):
        """Set tracks to display as cards"""
        self.tracks = tracks
        self.update_cards()
    
    def update_cards(self):
        """Update the cards display"""
        # Clear existing cards
        for card in self.cards:
            card.setParent(None)
        self.cards.clear()
        
        # Add new cards
        columns = 4  # Number of columns
        for i, track in enumerate(self.tracks):
            card = TrackCard(track)
            card.track_selected.connect(self.track_selected.emit)
            card.track_double_clicked.connect(self.track_double_clicked.emit)
            
            row = i // columns
            col = i % columns
            self.cards_layout.addWidget(card, row, col)
            self.cards.append(card)
        
        # Add stretch to push cards to top
        self.cards_layout.setRowStretch(len(self.tracks) // columns + 1, 1)