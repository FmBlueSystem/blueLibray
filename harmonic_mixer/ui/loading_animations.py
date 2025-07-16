"""
Enhanced loading animations and progress indicators
"""

from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QProgressBar
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QRect, QEasingCurve, pyqtSignal, QParallelAnimationGroup, pyqtProperty
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QConicalGradient, QFont


class PulsingDot(QWidget):
    """Animated pulsing dot indicator"""
    
    def __init__(self, color="#3498db", size=12):
        super().__init__()
        self.color = QColor(color)
        self.base_size = size
        self.current_size = size
        self.setFixedSize(size * 2, size * 2)
        
        # Animation
        self.animation = QPropertyAnimation(self, b"dot_size")
        self.animation.setDuration(1000)
        self.animation.setStartValue(size)
        self.animation.setEndValue(size * 1.5)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.animation.setLoopCount(-1)  # Infinite loop
        self.animation.finished.connect(self.reverse_animation)
        
        self._animating = False
        self._direction = 1
    
    def start(self):
        """Start the pulsing animation"""
        if not self._animating:
            self._animating = True
            self.animation.start()
    
    def stop(self):
        """Stop the pulsing animation"""
        self._animating = False
        self.animation.stop()
        self.current_size = self.base_size
        self.update()
    
    def reverse_animation(self):
        """Reverse animation direction"""
        if self._animating:
            if self._direction == 1:
                self.animation.setStartValue(self.base_size * 1.5)
                self.animation.setEndValue(self.base_size)
                self._direction = -1
            else:
                self.animation.setStartValue(self.base_size)
                self.animation.setEndValue(self.base_size * 1.5)
                self._direction = 1
            self.animation.start()
    
    @pyqtProperty(float)
    def dot_size(self):
        return self.current_size
    
    @dot_size.setter
    def dot_size(self, value):
        self.current_size = value
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calculate center
        center_x = self.width() // 2
        center_y = self.height() // 2
        
        # Draw outer glow
        glow_color = QColor(self.color)
        glow_color.setAlpha(50)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(glow_color))
        painter.drawEllipse(
            center_x - self.current_size,
            center_y - self.current_size,
            self.current_size * 2,
            self.current_size * 2
        )
        
        # Draw main dot
        painter.setBrush(QBrush(self.color))
        painter.drawEllipse(
            center_x - self.current_size // 2,
            center_y - self.current_size // 2,
            self.current_size,
            self.current_size
        )


class ThreeDotsLoader(QWidget):
    """Three dots loading animation"""
    
    def __init__(self, color="#3498db", dot_size=8):
        super().__init__()
        self.dots = []
        self.color = color
        self.dot_size = dot_size
        self.setFixedHeight(dot_size * 3)
        
        layout = QHBoxLayout()
        layout.setSpacing(dot_size)
        
        # Create three dots
        for i in range(3):
            dot = PulsingDot(color, dot_size)
            self.dots.append(dot)
            layout.addWidget(dot)
        
        self.setLayout(layout)
        
        # Stagger animations
        self.timer = QTimer()
        self.timer.timeout.connect(self.start_next_dot)
        self.current_dot = 0
        self._animating = False
    
    def start(self):
        """Start the loading animation"""
        if not self._animating:
            self._animating = True
            self.current_dot = 0
            self.timer.start(200)  # 200ms delay between dots
            self.dots[0].start()
    
    def stop(self):
        """Stop the loading animation"""
        self._animating = False
        self.timer.stop()
        for dot in self.dots:
            dot.stop()
    
    def start_next_dot(self):
        """Start the next dot in sequence"""
        self.current_dot += 1
        if self.current_dot < len(self.dots):
            self.dots[self.current_dot].start()
        else:
            self.timer.stop()


class CircularProgress(QWidget):
    """Circular progress indicator with percentage"""
    
    def __init__(self, size=100, color="#3498db"):
        super().__init__()
        self.setFixedSize(size, size)
        self._progress = 0
        self._color = QColor(color)
        self._animation_angle = 0
        
        # Animation timer for spinning effect
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(50)  # 20 FPS
    
    def set_progress(self, value):
        """Set progress value (0-100)"""
        self._progress = max(0, min(100, value))
        self.update()
    
    def update_animation(self):
        """Update spinning animation"""
        self._animation_angle = (self._animation_angle + 5) % 360
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calculate dimensions
        size = min(self.width(), self.height())
        margin = size * 0.1
        rect = QRect(int(margin), int(margin), 
                    int(size - 2 * margin), int(size - 2 * margin))
        
        # Draw background circle
        painter.setPen(QPen(QColor("#e0e0e0"), 8))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(rect)
        
        # Draw progress arc
        if self._progress > 0:
            center = rect.center()
            gradient = QConicalGradient(center.x(), center.y(), self._animation_angle)
            gradient.setColorAt(0, self._color)
            gradient.setColorAt(1, self._color.darker(150))
            
            painter.setPen(QPen(QBrush(gradient), 8))
            start_angle = 90 * 16  # Start from top
            span_angle = -int(self._progress * 360 * 16 / 100)  # Clockwise
            painter.drawArc(rect, start_angle, span_angle)
        
        # Draw percentage text
        painter.setPen(QPen(QColor("#2c3e50")))
        font = QFont()
        font.setPointSize(int(size * 0.2))
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, f"{self._progress}%")


class GeneratingPlaylistAnimation(QWidget):
    """Full playlist generation animation with stages"""
    completed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.stages = [
            "Analyzing tracks...",
            "Calculating compatibility...",
            "Optimizing sequence...",
            "Finalizing playlist..."
        ]
        self.current_stage = 0
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Circular progress
        self.progress = CircularProgress(120, "#3498db")
        layout.addWidget(self.progress, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Stage label
        self.stage_label = QLabel(self.stages[0])
        self.stage_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stage_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                color: #2c3e50;
                margin-top: 20px;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.stage_label)
        
        # Sub-progress for current stage
        self.stage_progress = QProgressBar()
        self.stage_progress.setTextVisible(False)
        self.stage_progress.setMaximumWidth(300)
        self.stage_progress.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 3px;
                background-color: #e0e0e0;
                height: 6px;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.stage_progress, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Three dots loader
        self.dots_loader = ThreeDotsLoader("#3498db", 6)
        layout.addWidget(self.dots_loader, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.setLayout(layout)
        
        # Animation timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
    
    def start(self):
        """Start the generation animation"""
        self.current_stage = 0
        self.progress.set_progress(0)
        self.stage_label.setText(self.stages[0])
        self.stage_progress.setValue(0)
        self.dots_loader.start()
        self.timer.start(50)  # Update every 50ms
    
    def stop(self):
        """Stop the animation"""
        self.timer.stop()
        self.dots_loader.stop()
    
    def update_progress(self):
        """Update progress animation"""
        # Update stage progress
        current_stage_progress = self.stage_progress.value()
        if current_stage_progress < 100:
            self.stage_progress.setValue(current_stage_progress + 2)
        else:
            # Move to next stage
            self.current_stage += 1
            if self.current_stage < len(self.stages):
                self.stage_label.setText(self.stages[self.current_stage])
                self.stage_progress.setValue(0)
            else:
                # Completed
                self.progress.set_progress(100)
                self.stop()
                self.completed.emit()
                return
        
        # Update overall progress
        overall_progress = (self.current_stage * 100 + current_stage_progress) / len(self.stages)
        self.progress.set_progress(int(overall_progress))


class SuccessAnimation(QWidget):
    """Success checkmark animation"""
    
    def __init__(self, size=80):
        super().__init__()
        self.setFixedSize(size, size)
        self._animation_progress = 0
        
        # Animation
        self.animation = QPropertyAnimation(self, b"animation_progress")
        self.animation.setDuration(600)
        self.animation.setStartValue(0)
        self.animation.setEndValue(100)
        self.animation.setEasingCurve(QEasingCurve.Type.OutBack)
    
    def start(self):
        """Start the success animation"""
        self._animation_progress = 0
        self.animation.start()
    
    @pyqtProperty(float)
    def animation_progress(self):
        return self._animation_progress
    
    @animation_progress.setter
    def animation_progress(self, value):
        self._animation_progress = value
        self.update()
    
    def paintEvent(self, event):
        if self._animation_progress == 0:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calculate dimensions
        size = min(self.width(), self.height())
        center = size // 2
        radius = size * 0.4
        
        # Draw circle
        circle_size = radius * 2 * self._animation_progress / 100
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#27ae60")))
        painter.drawEllipse(
            int(center - circle_size / 2),
            int(center - circle_size / 2),
            int(circle_size),
            int(circle_size)
        )
        
        # Draw checkmark when circle is complete
        if self._animation_progress > 50:
            checkmark_progress = (self._animation_progress - 50) * 2
            painter.setPen(QPen(QColor("white"), 4, Qt.PenStyle.SolidLine, 
                              Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            
            # Calculate checkmark points
            start_x = center - radius * 0.3
            start_y = center
            mid_x = center - radius * 0.1
            mid_y = center + radius * 0.2
            end_x = center + radius * 0.3
            end_y = center - radius * 0.2
            
            # Draw partial checkmark based on progress
            if checkmark_progress < 50:
                # First line
                progress_ratio = checkmark_progress / 50
                current_x = start_x + (mid_x - start_x) * progress_ratio
                current_y = start_y + (mid_y - start_y) * progress_ratio
                painter.drawLine(int(start_x), int(start_y), 
                               int(current_x), int(current_y))
            else:
                # Complete first line
                painter.drawLine(int(start_x), int(start_y), 
                               int(mid_x), int(mid_y))
                
                # Second line
                progress_ratio = (checkmark_progress - 50) / 50
                current_x = mid_x + (end_x - mid_x) * progress_ratio
                current_y = mid_y + (end_y - mid_y) * progress_ratio
                painter.drawLine(int(mid_x), int(mid_y), 
                               int(current_x), int(current_y))