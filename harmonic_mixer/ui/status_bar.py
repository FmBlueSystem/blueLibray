"""
Enhanced Status Bar Widget with visual feedback
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QRect, pyqtProperty
from PyQt6.QtGui import QPalette, QColor, QPainter, QBrush, QPen
from typing import Optional


class StatusBar(QWidget):
    """Enhanced status bar with colors, animations and auto-clear"""
    
    # Status types with associated colors (Material Design inspired)
    STATUS_COLORS = {
        'success': '#4CAF50',  # Green
        'info': '#2196F3',     # Blue
        'warning': '#FF9800',  # Orange
        'error': '#F44336',    # Red
        'progress': '#9C27B0', # Purple
        'neutral': '#607D8B'   # Blue Grey
    }
    
    # Emoji mappings for different contexts
    STATUS_EMOJIS = {
        'music': '🎵',
        'ai': '🤖',
        'folder': '📁',
        'playlist': '🎶',
        'success': '✅',
        'error': '❌',
        'warning': '⚠️',
        'loading': '⏳',
        'complete': '✨'
    }
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self._background_color = QColor(self.STATUS_COLORS['neutral'])
        self._opacity = 1.0
        self.auto_clear_timer = QTimer()
        self.auto_clear_timer.timeout.connect(self.clear_status)
        self.fade_animation = None
        
    def setup_ui(self):
        """Initialize the status bar UI"""
        self.setFixedHeight(32)
        self.setStyleSheet("""
            QWidget {
                border-radius: 16px;
                padding: 4px 12px;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("""
            QLabel {
                color: white;
                font-weight: bold;
                font-size: 13px;
            }
        """)
        layout.addWidget(self.status_label)
        
    def paintEvent(self, event):
        """Custom paint for rounded corners and background"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Set opacity
        painter.setOpacity(self._opacity)
        
        # Draw rounded rectangle background
        brush = QBrush(self._background_color)
        painter.setBrush(brush)
        painter.setPen(QPen(Qt.PenStyle.NoPen))
        painter.drawRoundedRect(self.rect(), 16, 16)
        
    @pyqtProperty(float)
    def opacity(self):
        return self._opacity
    
    @opacity.setter
    def opacity(self, value):
        self._opacity = value
        self.update()
        
    def show_status(self, message: str, status_type: str = 'info', 
                   emoji_type: Optional[str] = None, auto_clear: bool = True):
        """Show a status message with appropriate styling"""
        # Add emoji if specified
        if emoji_type and emoji_type in self.STATUS_EMOJIS:
            message = f"{self.STATUS_EMOJIS[emoji_type]} {message}"
        
        self.status_label.setText(message)
        
        # Set background color based on status type
        if status_type in self.STATUS_COLORS:
            self._background_color = QColor(self.STATUS_COLORS[status_type])
            self.update()
        
        # Reset opacity
        self._opacity = 1.0
        self.update()
        
        # Auto-clear after 5 seconds if enabled
        if auto_clear:
            self.auto_clear_timer.stop()
            self.auto_clear_timer.start(5000)
    
    def show_progress(self, message: str):
        """Show a progress message (doesn't auto-clear)"""
        self.show_status(message, 'progress', 'loading', auto_clear=False)
    
    def show_success(self, message: str):
        """Show a success message"""
        self.show_status(message, 'success', 'success')
    
    def show_error(self, message: str):
        """Show an error message"""
        self.show_status(message, 'error', 'error')
    
    def show_info(self, message: str, emoji_type: Optional[str] = None):
        """Show an info message"""
        self.show_status(message, 'info', emoji_type)
    
    def clear_status(self):
        """Clear the status with fade animation"""
        self.auto_clear_timer.stop()
        
        # Create fade out animation
        self.fade_animation = QPropertyAnimation(self, b"opacity")
        self.fade_animation.setDuration(500)
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.finished.connect(self._on_fade_complete)
        self.fade_animation.start()
    
    def _on_fade_complete(self):
        """Called when fade animation completes"""
        self.status_label.setText("")
        self._opacity = 1.0
        self.update()