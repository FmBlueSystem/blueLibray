"""
Enhanced Playlist Generator Widget with improved UX, mobile support, and accessibility
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, 
    QPushButton, QComboBox, QSlider, QProgressBar, QStackedWidget,
    QScrollArea, QSizePolicy, QButtonGroup, QRadioButton,
    QSpinBox, QFrame, QGridLayout, QToolTip, QApplication
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QRect, QEasingCurve, QSize
from PyQt6.QtGui import QPalette, QFont, QIcon, QColor, QPainter, QLinearGradient, QPixmap
from typing import List, Optional, Dict, Any

from ..core.harmonic_engine import Track
from .enhanced_components import ModernButton, EnhancedSlider, StatusIndicator


class VisualModeSelector(QWidget):
    """Visual mode selector with icons and descriptions"""
    mode_selected = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QGridLayout()
        layout.setSpacing(10)
        
        self.mode_buttons = {}
        modes = [
            {
                "id": "intelligent",
                "name": "Intelligent Mix",
                "icon": "🎯",
                "description": "Balanced multi-factor approach",
                "color": "#3498db"
            },
            {
                "id": "classic",
                "name": "Classic Camelot",
                "icon": "🎵",
                "description": "Traditional harmonic mixing",
                "color": "#9b59b6"
            },
            {
                "id": "energy",
                "name": "Energy Flow",
                "icon": "⚡",
                "description": "Focus on energy progression",
                "color": "#e74c3c"
            },
            {
                "id": "emotional",
                "name": "Emotional Journey",
                "icon": "💫",
                "description": "Prioritize emotional continuity",
                "color": "#f39c12"
            }
        ]
        
        for i, mode in enumerate(modes):
            button = self.create_mode_button(mode)
            self.mode_buttons[mode["id"]] = button
            layout.addWidget(button, i // 2, i % 2)
        
        # Select first mode by default
        self.mode_buttons["intelligent"].setChecked(True)
        self.setLayout(layout)
    
    def create_mode_button(self, mode: Dict[str, Any]) -> QPushButton:
        """Create a visual mode button with icon and description"""
        button = QPushButton()
        button.setCheckable(True)
        button.setObjectName("modeButton")
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Create button content
        content = f"""
        <div style='text-align: center; padding: 10px;'>
            <div style='font-size: 32px; margin-bottom: 5px;'>{mode['icon']}</div>
            <div style='font-weight: bold; font-size: 14px; margin-bottom: 3px;'>{mode['name']}</div>
            <div style='font-size: 11px; color: #888;'>{mode['description']}</div>
        </div>
        """
        button.setText(content)
        button.setStyleSheet(f"""
            QPushButton#modeButton {{
                border: 2px solid #ddd;
                border-radius: 10px;
                padding: 15px;
                background-color: white;
                min-height: 100px;
                min-width: 150px;
            }}
            QPushButton#modeButton:hover {{
                border-color: {mode['color']};
                background-color: #f8f9fa;
            }}
            QPushButton#modeButton:checked {{
                border-color: {mode['color']};
                background-color: {mode['color']}10;
                border-width: 3px;
            }}
        """)
        
        # Connect signal
        button.clicked.connect(lambda: self.on_mode_selected(mode["id"]))
        
        # Accessibility
        button.setAccessibleName(f"{mode['name']} mode")
        button.setAccessibleDescription(mode['description'])
        
        return button
    
    def on_mode_selected(self, mode_id: str):
        """Handle mode selection"""
        # Uncheck all other buttons
        for mid, button in self.mode_buttons.items():
            if mid != mode_id:
                button.setChecked(False)
        
        self.mode_selected.emit(mode_id)


class PlaylistPreviewWidget(QWidget):
    """Widget for previewing generated playlist with visual feedback"""
    
    def __init__(self):
        super().__init__()
        self.tracks = []
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header = QLabel("Playlist Preview")
        header.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                padding: 10px;
                background-color: #2c3e50;
                color: white;
                border-radius: 5px 5px 0 0;
            }
        """)
        layout.addWidget(header)
        
        # Track list container
        self.track_container = QWidget()
        self.track_layout = QVBoxLayout(self.track_container)
        self.track_layout.setSpacing(2)
        
        # Scroll area for tracks
        scroll = QScrollArea()
        scroll.setWidget(self.track_container)
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(400)
        scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #ddd;
                border-radius: 0 0 5px 5px;
                background-color: #f8f9fa;
            }
        """)
        
        layout.addWidget(scroll)
        self.setLayout(layout)
        
        # Show placeholder
        self.show_placeholder()
    
    def show_placeholder(self):
        """Show placeholder when no playlist is generated"""
        placeholder = QLabel("No playlist generated yet.\nClick 'Generate Playlist' to create one!")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("""
            QLabel {
                padding: 40px;
                color: #7f8c8d;
                font-size: 14px;
            }
        """)
        self.track_layout.addWidget(placeholder)
    
    def update_playlist(self, tracks: List[Track]):
        """Update the preview with new tracks"""
        # Clear existing tracks
        while self.track_layout.count():
            item = self.track_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.tracks = tracks
        
        # Add track items
        for i, track in enumerate(tracks):
            item = self.create_track_item(track, i + 1)
            self.track_layout.addWidget(item)
            
            # Animate appearance
            self.animate_track_appearance(item, i)
    
    def create_track_item(self, track: Track, position: int) -> QWidget:
        """Create a visual track item"""
        item = QFrame()
        item.setObjectName("trackItem")
        item.setStyleSheet("""
            QFrame#trackItem {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                padding: 10px;
                margin: 2px;
            }
            QFrame#trackItem:hover {
                background-color: #f0f7ff;
                border-color: #3498db;
            }
        """)
        
        layout = QHBoxLayout(item)
        
        # Position number
        pos_label = QLabel(f"{position}")
        pos_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #3498db;
                min-width: 30px;
                text-align: center;
            }
        """)
        layout.addWidget(pos_label)
        
        # Track info
        info_layout = QVBoxLayout()
        
        title_label = QLabel(f"<b>{track.title}</b>")
        title_label.setStyleSheet("font-size: 14px;")
        info_layout.addWidget(title_label)
        
        details_label = QLabel(f"{track.artist} • {track.key} • {track.bpm} BPM")
        details_label.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        info_layout.addWidget(details_label)
        
        layout.addLayout(info_layout, 1)
        
        # Compatibility indicator (if not first track)
        if position > 1 and len(self.tracks) >= position - 1:
            try:
                prev_track = self.tracks[position - 2]  # Previous track
                # Calculate simple compatibility based on key matching
                compat_score = self.calculate_compatibility(prev_track, track)
                compat_percent = int(compat_score * 100)
                
                # Choose color based on compatibility
                if compat_percent >= 80:
                    color = "#27ae60"  # Green
                elif compat_percent >= 60:
                    color = "#f39c12"  # Orange
                else:
                    color = "#e74c3c"  # Red
                
                compat_label = QLabel(f"{compat_percent}%")
                compat_label.setStyleSheet(f"""
                    QLabel {{
                        background-color: {color};
                        color: white;
                        padding: 5px 10px;
                        border-radius: 15px;
                        font-size: 12px;
                        font-weight: bold;
                    }}
                """)
                compat_label.setToolTip(f"Compatibility with previous track: {compat_percent}%")
                layout.addWidget(compat_label)
            except (IndexError, AttributeError):
                # Fallback if compatibility calculation fails
                pass
        
        return item
    
    def animate_track_appearance(self, widget: QWidget, index: int):
        """Animate track item appearance"""
        # Start invisible
        widget.setWindowOpacity(0)
        
        # Create fade-in animation
        timer = QTimer()
        timer.timeout.connect(lambda: self.fade_in_widget(widget, timer))
        timer.start(50 + index * 30)  # Stagger animations
    
    def fade_in_widget(self, widget: QWidget, timer: QTimer):
        """Fade in a widget"""
        opacity = widget.windowOpacity()
        if opacity < 1:
            widget.setWindowOpacity(opacity + 0.1)
        else:
            timer.stop()
    
    def calculate_compatibility(self, track1, track2):
        """Calculate simple compatibility between two tracks"""
        try:
            score = 0.5  # Base compatibility
            
            # Key compatibility (simplified)
            if hasattr(track1, 'key') and hasattr(track2, 'key'):
                if track1.key and track2.key:
                    if track1.key == track2.key:
                        score += 0.3
                    elif track1.key[:-1] == track2.key[:-1]:  # Same number, different mode
                        score += 0.2
            
            # BPM compatibility
            if hasattr(track1, 'bpm') and hasattr(track2, 'bpm'):
                if track1.bpm and track2.bpm:
                    bpm_diff = abs(track1.bpm - track2.bpm)
                    if bpm_diff <= 5:
                        score += 0.2
                    elif bpm_diff <= 15:
                        score += 0.1
            
            return min(score, 1.0)  # Cap at 1.0
            
        except Exception:
            return 0.5  # Default compatibility if calculation fails


class PlaylistGeneratorWidget(QWidget):
    """Main playlist generator widget with enhanced UX"""
    playlist_generated = pyqtSignal(list)  # List of tracks
    generation_started = pyqtSignal()
    generation_completed = pyqtSignal()
    
    def __init__(self, facade):
        super().__init__()
        self.facade = facade
        self.current_playlist = []
        self.is_generating = False
        self.init_ui()
    
    def init_ui(self):
        # Main layout with responsive design
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        
        # Title
        title = QLabel("🎵 Playlist Generator")
        title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px;
            }
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)
        
        # Content area with two columns (responsive)
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setSpacing(20)
        
        # Left column - Settings
        left_widget = self.create_settings_panel()
        content_layout.addWidget(left_widget, 1)
        
        # Right column - Preview
        self.preview_widget = PlaylistPreviewWidget()
        content_layout.addWidget(self.preview_widget, 1)
        
        # Make scrollable for mobile
        scroll = QScrollArea()
        scroll.setWidget(content_widget)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        main_layout.addWidget(scroll)
        
        # Bottom action bar
        action_bar = self.create_action_bar()
        main_layout.addWidget(action_bar)
        
        self.setLayout(main_layout)
        
        # Apply responsive styling
        self.apply_responsive_styling()
    
    def create_settings_panel(self) -> QWidget:
        """Create the settings panel with all controls"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(15)
        
        # Mode selector
        mode_group = QGroupBox("Select Mixing Mode")
        mode_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #ddd;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 10px;
            }
        """)
        mode_layout = QVBoxLayout()
        
        self.mode_selector = VisualModeSelector()
        self.mode_selector.mode_selected.connect(self.on_mode_changed)
        mode_layout.addWidget(self.mode_selector)
        
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)
        
        # Playlist parameters
        params_group = QGroupBox("Playlist Parameters")
        params_group.setStyleSheet(mode_group.styleSheet())
        params_layout = QVBoxLayout()
        
        # Length control with visual feedback
        length_container = QWidget()
        length_layout = QVBoxLayout(length_container)
        
        length_header = QHBoxLayout()
        length_header.addWidget(QLabel("Playlist Length"))
        self.length_display = QLabel("15 tracks")
        self.length_display.setStyleSheet("color: #3498db; font-weight: bold;")
        length_header.addWidget(self.length_display)
        length_header.addStretch()
        length_layout.addLayout(length_header)
        
        self.length_slider = EnhancedSlider(Qt.Orientation.Horizontal)
        self.length_slider.setRange(5, 50)
        self.length_slider.setValue(15)
        self.length_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.length_slider.setTickInterval(5)
        self.length_slider.valueChanged.connect(self.on_length_changed)
        
        # Add keyboard accessibility
        self.length_slider.setAccessibleName("Playlist length slider")
        self.length_slider.setAccessibleDescription("Adjust the number of tracks in the playlist")
        
        length_layout.addWidget(self.length_slider)
        params_layout.addWidget(length_container)
        
        # Energy curve selector with visual representation
        curve_container = QWidget()
        curve_layout = QVBoxLayout(curve_container)
        
        curve_label = QLabel("Energy Progression")
        curve_layout.addWidget(curve_label)
        
        self.curve_buttons = QButtonGroup()
        curves = [
            ("neutral", "Steady", "→"),
            ("ascending", "Build Up", "↗"),
            ("descending", "Wind Down", "↘"),
            ("peak", "Peak Time", "⚡")
        ]
        
        curve_button_layout = QHBoxLayout()
        for i, (curve_id, name, icon) in enumerate(curves):
            btn = QPushButton(f"{icon}\n{name}")
            btn.setCheckable(True)
            btn.setObjectName("curveButton")
            btn.setStyleSheet("""
                QPushButton#curveButton {
                    padding: 10px;
                    border: 2px solid #ddd;
                    border-radius: 5px;
                    background-color: white;
                    min-width: 70px;
                }
                QPushButton#curveButton:hover {
                    border-color: #3498db;
                    background-color: #f0f7ff;
                }
                QPushButton#curveButton:checked {
                    border-color: #3498db;
                    background-color: #3498db;
                    color: white;
                }
            """)
            btn.setAccessibleName(f"{name} energy curve")
            self.curve_buttons.addButton(btn, i)
            if curve_id == "neutral":
                btn.setChecked(True)
            curve_button_layout.addWidget(btn)
        
        curve_layout.addLayout(curve_button_layout)
        params_layout.addWidget(curve_container)
        
        # Advanced options (collapsible)
        self.advanced_widget = self.create_advanced_options()
        params_layout.addWidget(self.advanced_widget)
        
        params_group.setLayout(params_layout)
        layout.addWidget(params_group)
        
        layout.addStretch()
        return panel
    
    def create_advanced_options(self) -> QWidget:
        """Create collapsible advanced options"""
        container = QWidget()
        layout = QVBoxLayout(container)
        
        # Toggle button
        self.advanced_toggle = QPushButton("▶ Advanced Options")
        self.advanced_toggle.setObjectName("advancedToggle")
        self.advanced_toggle.setStyleSheet("""
            QPushButton#advancedToggle {
                text-align: left;
                padding: 8px;
                border: none;
                background: none;
                color: #3498db;
                font-weight: bold;
            }
            QPushButton#advancedToggle:hover {
                text-decoration: underline;
            }
        """)
        self.advanced_toggle.clicked.connect(self.toggle_advanced)
        layout.addWidget(self.advanced_toggle)
        
        # Advanced content
        self.advanced_content = QWidget()
        self.advanced_content.setVisible(False)
        advanced_layout = QVBoxLayout(self.advanced_content)
        
        # Start from selected track option
        self.start_from_selected = QRadioButton("Start from selected track")
        self.start_from_selected.setChecked(True)
        advanced_layout.addWidget(self.start_from_selected)
        
        # Contextual filters
        context_label = QLabel("Contextual Filters:")
        context_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        advanced_layout.addWidget(context_label)
        
        # Time of day
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("Time of Day:"))
        self.time_combo = QComboBox()
        self.time_combo.addItems(["Any", "Morning", "Afternoon", "Evening", "Night"])
        time_layout.addWidget(self.time_combo)
        time_layout.addStretch()
        advanced_layout.addLayout(time_layout)
        
        # Activity
        activity_layout = QHBoxLayout()
        activity_layout.addWidget(QLabel("Activity:"))
        self.activity_combo = QComboBox()
        self.activity_combo.addItems(["Any", "Party", "Workout", "Chill", "Focus"])
        activity_layout.addWidget(self.activity_combo)
        activity_layout.addStretch()
        advanced_layout.addLayout(activity_layout)
        
        layout.addWidget(self.advanced_content)
        
        return container
    
    def create_action_bar(self) -> QWidget:
        """Create the bottom action bar"""
        bar = QWidget()
        bar.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border-top: 1px solid #ddd;
                padding: 10px;
            }
        """)
        
        layout = QHBoxLayout(bar)
        
        # Progress indicator
        self.progress_widget = QWidget()
        progress_layout = QHBoxLayout(self.progress_widget)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        
        self.progress_spinner = StatusIndicator()
        progress_layout.addWidget(self.progress_spinner)
        
        self.progress_label = QLabel("Ready to generate")
        progress_layout.addWidget(self.progress_label)
        
        self.progress_widget.setVisible(False)
        layout.addWidget(self.progress_widget)
        
        layout.addStretch()
        
        # Action buttons
        self.generate_btn = ModernButton("Generate Playlist", "success")
        self.generate_btn.setMinimumWidth(150)
        self.generate_btn.clicked.connect(self.generate_playlist)
        self.generate_btn.setAccessibleName("Generate playlist button")
        layout.addWidget(self.generate_btn)
        
        self.export_btn = ModernButton("Export", "secondary")
        self.export_btn.setMinimumWidth(100)
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self.export_playlist)
        layout.addWidget(self.export_btn)
        
        return bar
    
    def apply_responsive_styling(self):
        """Apply responsive styling for different screen sizes"""
        # Get screen size
        screen = QApplication.primaryScreen()
        screen_size = screen.size()
        
        if screen_size.width() < 768:  # Mobile
            # Stack columns vertically on mobile
            self.setStyleSheet("""
                QWidget {
                    font-size: 14px;
                }
                QPushButton {
                    min-height: 44px;
                }
            """)
        elif screen_size.width() < 1200:  # Tablet
            self.setStyleSheet("""
                QWidget {
                    font-size: 13px;
                }
                QPushButton {
                    min-height: 38px;
                }
            """)
        else:  # Desktop
            self.setStyleSheet("""
                QWidget {
                    font-size: 12px;
                }
                QPushButton {
                    min-height: 32px;
                }
            """)
    
    def toggle_advanced(self):
        """Toggle advanced options visibility"""
        is_visible = self.advanced_content.isVisible()
        self.advanced_content.setVisible(not is_visible)
        
        if is_visible:
            self.advanced_toggle.setText("▶ Advanced Options")
        else:
            self.advanced_toggle.setText("▼ Advanced Options")
    
    def on_mode_changed(self, mode: str):
        """Handle mode change"""
        # Update any mode-dependent UI elements
        pass
    
    def on_length_changed(self, value: int):
        """Handle length slider change"""
        self.length_display.setText(f"{value} tracks")
    
    def generate_playlist(self):
        """Generate playlist with visual feedback"""
        if self.is_generating:
            return
        
        self.is_generating = True
        self.generation_started.emit()
        
        # Update UI state
        self.generate_btn.setEnabled(False)
        self.generate_btn.setText("Generating...")
        self.progress_widget.setVisible(True)
        self.progress_spinner.set_status("loading")
        self.progress_label.setText("Analyzing tracks...")
        
        # Get parameters
        length = self.length_slider.value()
        curve_index = self.curve_buttons.checkedId()
        curves = ["neutral", "ascending", "descending", "peak"]
        curve = curves[curve_index] if curve_index >= 0 else "neutral"
        
        # Simulate generation with timer (replace with actual generation)
        QTimer.singleShot(100, lambda: self.perform_generation(length, curve))
    
    def perform_generation(self, length: int, curve: str):
        """Perform the actual playlist generation"""
        try:
            # Validate that tracks are available
            tracks = self.facade.get_tracks()
            if not tracks:
                self.show_error("No tracks loaded. Please load tracks first.")
                return
            
            # Get current track if "start from selected" is checked
            start_track_id = None
            if self.start_from_selected.isChecked():
                current_track = self.facade.get_current_track()
                if current_track and hasattr(current_track, 'id'):
                    start_track_id = current_track.id
            
            # Generate playlist using correct method signature
            self.progress_label.setText("Generating optimal sequence...")
            playlist = self.facade.generate_playlist(
                target_length=length,
                progression_curve=curve,
                start_track_id=start_track_id
            )
            
            if playlist:
                self.current_playlist = playlist
                self.preview_widget.update_playlist(playlist)
                self.export_btn.setEnabled(True)
                
                self.progress_spinner.set_status("success")
                self.progress_label.setText(f"Generated {len(playlist)} tracks!")
                
                # Hide progress after delay
                QTimer.singleShot(2000, self.hide_progress)
                
                self.playlist_generated.emit(playlist)
            else:
                self.show_error("Failed to generate playlist")
        
        except Exception as e:
            self.show_error(f"Error: {str(e)}")
        
        finally:
            self.is_generating = False
            self.generate_btn.setEnabled(True)
            self.generate_btn.setText("Generate Playlist")
            self.generation_completed.emit()
    
    def hide_progress(self):
        """Hide progress indicator"""
        self.progress_widget.setVisible(False)
    
    def show_error(self, message: str):
        """Show error message"""
        self.progress_spinner.set_status("error")
        self.progress_label.setText(message)
        QTimer.singleShot(3000, self.hide_progress)
    
    def export_playlist(self):
        """Export the current playlist"""
        if not self.current_playlist:
            return
        
        # Emit signal or handle export
        # This would typically open a file dialog
        pass
    
    def set_tracks_available(self, available: bool):
        """Update UI based on track availability"""
        self.generate_btn.setEnabled(available)
        if not available:
            self.generate_btn.setToolTip("Load tracks first to generate playlist")
        else:
            self.generate_btn.setToolTip("Generate an optimized playlist")