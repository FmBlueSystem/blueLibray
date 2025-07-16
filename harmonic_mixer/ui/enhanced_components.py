"""
Enhanced UI Components with Modern Design
Custom widgets with improved UX and visual appeal
"""

from PyQt6.QtWidgets import (
    QPushButton, QLabel, QFrame, QHBoxLayout, QVBoxLayout, 
    QWidget, QGraphicsDropShadowEffect, QProgressBar, QSlider,
    QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor, QPalette, QPainter, QLinearGradient
from .enhanced_theme import ModernBlueLibraryTheme
from typing import Optional


class ModernButton(QPushButton):
    """Enhanced button with modern styling and hover effects"""
    
    def __init__(self, text: str = "", button_type: str = "primary", parent=None):
        super().__init__(text, parent)
        self.button_type = button_type
        self.setProperty("buttonType", button_type)
        self.setup_styling()
        self.setup_animations()
    
    def setup_styling(self):
        """Apply modern styling"""
        self.setMinimumHeight(40)
        self.setFont(QFont("SF Pro Display", 13, QFont.Weight.DemiBold))
        
        # Add subtle shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)
    
    def setup_animations(self):
        """Setup hover animations"""
        self.hover_animation = QPropertyAnimation(self, b"geometry")
        self.hover_animation.setDuration(150)
        self.hover_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    
    def enterEvent(self, event):
        """Animate on hover enter"""
        super().enterEvent(event)
        # Subtle scale effect would go here in a full implementation
    
    def leaveEvent(self, event):
        """Animate on hover leave"""
        super().leaveEvent(event)
        # Reset scale effect would go here


class GradientProgressBar(QProgressBar):
    """Enhanced progress bar with gradient and animations"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_styling()
    
    def setup_styling(self):
        """Apply gradient styling"""
        self.setMinimumHeight(25)
        self.setTextVisible(True)
        
        # Custom stylesheet for gradient effect
        self.setStyleSheet(f"""
            QProgressBar {{
                border: 2px solid {ModernBlueLibraryTheme.BACKGROUND_TERTIARY};
                border-radius: 12px;
                text-align: center;
                color: {ModernBlueLibraryTheme.TEXT_PRIMARY};
                background-color: {ModernBlueLibraryTheme.SURFACE_LOW};
                font-weight: 600;
                font-size: 12px;
            }}
            
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {ModernBlueLibraryTheme.ACCENT_PRIMARY}, 
                    stop:0.5 {ModernBlueLibraryTheme.MIXING_ACCENT},
                    stop:1 {ModernBlueLibraryTheme.ACCENT_LIGHT});
                border-radius: 10px;
                margin: 2px;
            }}
        """)


class EnhancedSlider(QSlider):
    """Enhanced slider with modern styling and value display"""
    
    valueDisplayed = pyqtSignal(str)  # Signal for value display
    
    def __init__(self, orientation=Qt.Orientation.Horizontal, parent=None):
        super().__init__(orientation, parent)
        self.setup_styling()
        self.value_label = None
        self.valueChanged.connect(self.update_value_display)
    
    def setup_styling(self):
        """Apply modern slider styling"""
        self.setMinimumHeight(30)
        
        self.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                height: 10px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {ModernBlueLibraryTheme.BACKGROUND_TERTIARY}, 
                    stop:1 {ModernBlueLibraryTheme.SURFACE_HIGH});
                border-radius: 5px;
                border: 1px solid {ModernBlueLibraryTheme.BACKGROUND_TERTIARY};
            }}
            
            QSlider::handle:horizontal {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {ModernBlueLibraryTheme.ACCENT_LIGHT}, 
                    stop:1 {ModernBlueLibraryTheme.ACCENT_PRIMARY});
                width: 24px;
                height: 24px;
                margin: -7px 0;
                border-radius: 12px;
                border: 3px solid {ModernBlueLibraryTheme.TEXT_PRIMARY};
            }}
            
            QSlider::handle:horizontal:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {ModernBlueLibraryTheme.MIXING_LIGHT}, 
                    stop:1 {ModernBlueLibraryTheme.MIXING_ACCENT});
                border: 3px solid {ModernBlueLibraryTheme.ACCENT_LIGHT};
                transform: scale(1.1);
            }}
            
            QSlider::sub-page:horizontal {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {ModernBlueLibraryTheme.ACCENT_PRIMARY}, 
                    stop:1 {ModernBlueLibraryTheme.MIXING_ACCENT});
                border-radius: 5px;
            }}
        """)
    
    def update_value_display(self, value):
        """Update value display"""
        percentage = value / (self.maximum() - self.minimum()) * 100
        self.valueDisplayed.emit(f"{percentage:.0f}%")


class StatusIndicator(QLabel):
    """Animated status indicator with color-coded states"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_styling()
        self.animation = None
        self.current_status = "neutral"
    
    def setup_styling(self):
        """Setup base styling"""
        self.setFixedSize(12, 12)
        self.setStyleSheet(f"""
            QLabel {{
                border-radius: 6px;
                background-color: {ModernBlueLibraryTheme.TEXT_DISABLED};
            }}
        """)
    
    def set_status(self, status: str, animated: bool = True):
        """Set status with optional animation"""
        self.current_status = status
        colors = ModernBlueLibraryTheme.get_status_colors()
        color = colors.get(status, ModernBlueLibraryTheme.TEXT_DISABLED)
        
        self.setStyleSheet(f"""
            QLabel {{
                border-radius: 6px;
                background-color: {color};
                border: 2px solid {ModernBlueLibraryTheme.TEXT_PRIMARY};
            }}
        """)
        
        if animated:
            self.animate_pulse()
    
    def animate_pulse(self):
        """Pulse animation for status changes"""
        if self.animation:
            self.animation.stop()
        
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.Type.OutElastic)
        # In a full implementation, this would animate the size


class EnhancedTableItem(QTableWidgetItem):
    """Enhanced table item with status indicators and styling"""
    
    def __init__(self, text: str = "", item_type: str = "default"):
        super().__init__(text)
        self.item_type = item_type
        self.setup_styling()
    
    def setup_styling(self):
        """Apply styling based on item type"""
        if self.item_type == "enhanced":
            # LLM-enhanced tracks
            self.setBackground(QColor(ModernBlueLibraryTheme.TRACK_ENHANCED + "20"))  # 20% opacity
            font = self.font()
            font.setWeight(QFont.Weight.DemiBold)
            self.setFont(font)
        
        elif self.item_type == "unavailable":
            # Unavailable tracks
            self.setForeground(QColor(ModernBlueLibraryTheme.TEXT_DISABLED))
            font = self.font()
            font.setItalic(True)
            self.setFont(font)
        
        elif self.item_type == "energy_high":
            # High energy tracks
            self.setBackground(QColor(ModernBlueLibraryTheme.ENERGY_HIGH + "15"))
        
        elif self.item_type == "energy_low":
            # Low energy tracks  
            self.setBackground(QColor(ModernBlueLibraryTheme.ENERGY_LOW + "15"))


class ModernHeaderView(QHeaderView):
    """Enhanced header view with modern styling"""
    
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self.setup_styling()
    
    def setup_styling(self):
        """Apply modern header styling"""
        self.setDefaultSectionSize(120)
        self.setMinimumSectionSize(80)
        self.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.setHighlightSections(True)
        
        # Enhanced header stylesheet
        self.setStyleSheet(f"""
            QHeaderView::section {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {ModernBlueLibraryTheme.BACKGROUND_TERTIARY}, 
                    stop:1 {ModernBlueLibraryTheme.BACKGROUND_SECONDARY});
                color: {ModernBlueLibraryTheme.TEXT_ACCENT};
                padding: 12px 16px;
                border: none;
                border-right: 1px solid {ModernBlueLibraryTheme.BACKGROUND_PRIMARY};
                border-bottom: 2px solid {ModernBlueLibraryTheme.ACCENT_PRIMARY};
                font-weight: 700;
                font-size: 11px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            
            QHeaderView::section:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {ModernBlueLibraryTheme.SURFACE_HIGH}, 
                    stop:1 {ModernBlueLibraryTheme.BACKGROUND_TERTIARY});
                color: {ModernBlueLibraryTheme.ACCENT_LIGHT};
                border-bottom: 3px solid {ModernBlueLibraryTheme.MIXING_ACCENT};
            }}
            
            QHeaderView::section:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {ModernBlueLibraryTheme.ACCENT_PRIMARY}, 
                    stop:1 {ModernBlueLibraryTheme.ACCENT_SECONDARY});
                color: {ModernBlueLibraryTheme.TEXT_PRIMARY};
            }}
        """)


class LoadingSpinner(QLabel):
    """Modern loading spinner with animation"""
    
    def __init__(self, size: int = 32, parent=None):
        super().__init__(parent)
        self.size = size
        self.setFixedSize(size, size)
        self.setup_animation()
    
    def setup_animation(self):
        """Setup rotation animation"""
        self.setStyleSheet(f"""
            QLabel {{
                border: 3px solid {ModernBlueLibraryTheme.BACKGROUND_TERTIARY};
                border-top: 3px solid {ModernBlueLibraryTheme.ACCENT_PRIMARY};
                border-radius: {self.size // 2}px;
                background-color: transparent;
            }}
        """)
        
        # Rotation animation
        self.animation = QPropertyAnimation(self, b"rotation")
        self.animation.setDuration(1000)
        self.animation.setStartValue(0)
        self.animation.setEndValue(360)
        self.animation.setLoopCount(-1)  # Infinite loop
    
    def start_spinning(self):
        """Start the spinning animation"""
        self.animation.start()
        self.show()
    
    def stop_spinning(self):
        """Stop the spinning animation"""
        self.animation.stop()
        self.hide()


class CompatibilityBadge(QLabel):
    """Badge showing compatibility score with color coding"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_styling()
    
    def setup_styling(self):
        """Setup badge styling"""
        self.setFixedSize(60, 24)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont("SF Pro Display", 10, QFont.Weight.Bold)
        self.setFont(font)
    
    def set_score(self, score: float):
        """Set compatibility score and update styling"""
        self.setText(f"{score:.0%}")
        
        # Color based on score
        if score >= 0.9:
            bg_color = ModernBlueLibraryTheme.SUCCESS
            text_color = ModernBlueLibraryTheme.TEXT_PRIMARY
        elif score >= 0.7:
            bg_color = ModernBlueLibraryTheme.ACCENT_PRIMARY
            text_color = ModernBlueLibraryTheme.TEXT_PRIMARY
        elif score >= 0.5:
            bg_color = ModernBlueLibraryTheme.WARNING
            text_color = ModernBlueLibraryTheme.BACKGROUND_PRIMARY
        else:
            bg_color = ModernBlueLibraryTheme.ERROR
            text_color = ModernBlueLibraryTheme.TEXT_PRIMARY
        
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {bg_color};
                color: {text_color};
                border-radius: 12px;
                border: 2px solid {ModernBlueLibraryTheme.TEXT_PRIMARY};
            }}
        """)


class AnimatedCard(QFrame):
    """Animated card widget with hover effects"""
    
    clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_styling()
        self.setup_animations()
    
    def setup_styling(self):
        """Setup card styling"""
        self.setFrameStyle(QFrame.Shape.Box)
        self.setLineWidth(0)
        self.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {ModernBlueLibraryTheme.SURFACE_MEDIUM}, 
                    stop:1 {ModernBlueLibraryTheme.SURFACE_LOW});
                border: 1px solid {ModernBlueLibraryTheme.BACKGROUND_TERTIARY};
                border-radius: 12px;
                padding: 16px;
            }}
            
            QFrame:hover {{
                border: 2px solid {ModernBlueLibraryTheme.ACCENT_PRIMARY};
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {ModernBlueLibraryTheme.SURFACE_HIGH}, 
                    stop:1 {ModernBlueLibraryTheme.SURFACE_MEDIUM});
            }}
        """)
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)
    
    def setup_animations(self):
        """Setup hover animations"""
        self.hover_animation = QPropertyAnimation(self, b"geometry")
        self.hover_animation.setDuration(200)
        self.hover_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    
    def mousePressEvent(self, event):
        """Handle mouse press"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)