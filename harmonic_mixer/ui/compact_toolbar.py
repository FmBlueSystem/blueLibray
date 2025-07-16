"""
Compact Toolbar for BlueLibrary
Provides quick access to the most important actions
"""

from PyQt6.QtWidgets import (
    QToolBar, QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
    QPushButton, QProgressBar, QSizePolicy, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon
from .enhanced_theme import ModernBlueLibraryTheme as BlueLibraryTheme
from .enhanced_components import ModernButton, GradientProgressBar


class CompactToolbar(QWidget):
    """Compact toolbar with most important actions"""
    
    # Signals for main window communication
    load_folder = pyqtSignal()
    clear_library = pyqtSignal()
    generate_playlist = pyqtSignal()
    enhance_tracks = pyqtSignal()
    play_pause = pyqtSignal()
    stop = pyqtSignal()
    toggle_controls = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.apply_styling()
    
    def setup_ui(self):
        """Setup the compact toolbar UI"""
        layout = QHBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # File Operations Section
        file_ops_widget = self.create_section_widget("File Operations")
        file_ops_layout = QHBoxLayout(file_ops_widget)
        file_ops_layout.setSpacing(5)
        
        # Load folder button
        self.load_folder_btn = ModernButton("📁 Load Folder", "primary")
        self.load_folder_btn.clicked.connect(self.load_folder.emit)
        self.load_folder_btn.setMinimumWidth(100)
        file_ops_layout.addWidget(self.load_folder_btn)
        
        # Clear library button
        self.clear_library_btn = ModernButton("🗑️ Clear", "danger")
        self.clear_library_btn.clicked.connect(self.clear_library.emit)
        self.clear_library_btn.setMinimumWidth(60)
        file_ops_layout.addWidget(self.clear_library_btn)
        
        layout.addWidget(file_ops_widget)
        
        # Separator
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.Shape.VLine)
        separator1.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator1)
        
        # Playlist Generation Section
        playlist_widget = self.create_section_widget("Playlist")
        playlist_layout = QHBoxLayout(playlist_widget)
        playlist_layout.setSpacing(5)
        
        # Generate playlist button
        self.generate_playlist_btn = ModernButton("🎵 Generate Playlist", "success")
        self.generate_playlist_btn.clicked.connect(self.generate_playlist.emit)
        self.generate_playlist_btn.setEnabled(False)
        self.generate_playlist_btn.setMinimumWidth(120)
        playlist_layout.addWidget(self.generate_playlist_btn)
        
        layout.addWidget(playlist_widget)
        
        # Separator
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.VLine)
        separator2.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator2)
        
        # AI Enhancement Section
        ai_widget = self.create_section_widget("AI Enhancement")
        ai_layout = QHBoxLayout(ai_widget)
        ai_layout.setSpacing(5)
        
        # Enhance tracks button
        self.enhance_tracks_btn = ModernButton("🤖 Enhance Tracks", "secondary")
        self.enhance_tracks_btn.clicked.connect(self.enhance_tracks.emit)
        self.enhance_tracks_btn.setEnabled(False)
        self.enhance_tracks_btn.setMinimumWidth(110)
        ai_layout.addWidget(self.enhance_tracks_btn)
        
        layout.addWidget(ai_widget)
        
        # Separator
        separator3 = QFrame()
        separator3.setFrameShape(QFrame.Shape.VLine)
        separator3.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator3)
        
        # Player Controls Section
        player_widget = self.create_section_widget("Player")
        player_layout = QHBoxLayout(player_widget)
        player_layout.setSpacing(5)
        
        # Play/pause button
        self.play_pause_btn = ModernButton("▶", "primary")
        self.play_pause_btn.clicked.connect(self.play_pause.emit)
        self.play_pause_btn.setEnabled(False)
        self.play_pause_btn.setMinimumWidth(40)
        self.play_pause_btn.setMaximumWidth(40)
        player_layout.addWidget(self.play_pause_btn)
        
        # Stop button
        self.stop_btn = ModernButton("⏹", "secondary")
        self.stop_btn.clicked.connect(self.stop.emit)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setMinimumWidth(40)
        self.stop_btn.setMaximumWidth(40)
        player_layout.addWidget(self.stop_btn)
        
        layout.addWidget(player_widget)
        
        # Stretch to push everything to the left
        layout.addStretch(1)
        
        # Progress section (right side)
        progress_widget = self.create_section_widget("Progress")
        progress_layout = QHBoxLayout(progress_widget)
        progress_layout.setSpacing(5)
        
        # Progress bar
        self.progress_bar = GradientProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMinimumWidth(200)
        self.progress_bar.setMaximumHeight(20)
        progress_layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setMinimumWidth(80)
        progress_layout.addWidget(self.status_label)
        
        layout.addWidget(progress_widget)
        
        # Separator
        separator4 = QFrame()
        separator4.setFrameShape(QFrame.Shape.VLine)
        separator4.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator4)
        
        # Controls toggle section
        toggle_widget = self.create_section_widget("View")
        toggle_layout = QHBoxLayout(toggle_widget)
        toggle_layout.setSpacing(5)
        
        # Toggle controls button
        self.toggle_controls_btn = ModernButton("⚙️ Controls", "info")
        self.toggle_controls_btn.clicked.connect(self.toggle_controls.emit)
        self.toggle_controls_btn.setMinimumWidth(80)
        self.toggle_controls_btn.setCheckable(True)
        self.toggle_controls_btn.setChecked(True)
        toggle_layout.addWidget(self.toggle_controls_btn)
        
        layout.addWidget(toggle_widget)
        
        # Set size policy
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMaximumHeight(60)
        self.setMinimumHeight(50)
    
    def create_section_widget(self, title: str) -> QWidget:
        """Create a section widget with title"""
        widget = QWidget()
        widget.setObjectName(f"section_{title.lower().replace(' ', '_')}")
        return widget
    
    def apply_styling(self):
        """Apply modern styling to the toolbar"""
        self.setStyleSheet(f"""
            CompactToolbar {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {BlueLibraryTheme.SURFACE_HIGH}, 
                    stop:1 {BlueLibraryTheme.SURFACE_MEDIUM});
                border: 1px solid {BlueLibraryTheme.ACCENT_PRIMARY};
                border-radius: 8px;
                padding: 3px;
            }}
            
            QFrame[frameShape="5"] {{
                color: {BlueLibraryTheme.ACCENT_PRIMARY};
                max-width: 1px;
                margin: 5px 3px;
            }}
            
            QLabel {{
                color: {BlueLibraryTheme.TEXT_PRIMARY};
                font-size: 12px;
                font-weight: 500;
            }}
            
            QWidget[id^="section_"] {{
                background: transparent;
                border: none;
                padding: 2px;
            }}
        """)
    
    def set_generate_enabled(self, enabled: bool):
        """Enable/disable generate playlist button"""
        self.generate_playlist_btn.setEnabled(enabled)
    
    def set_enhance_enabled(self, enabled: bool):
        """Enable/disable enhance tracks button"""
        self.enhance_tracks_btn.setEnabled(enabled)
    
    def set_play_enabled(self, enabled: bool):
        """Enable/disable play button"""
        self.play_pause_btn.setEnabled(enabled)
    
    def set_stop_enabled(self, enabled: bool):
        """Enable/disable stop button"""
        self.stop_btn.setEnabled(enabled)
    
    def set_play_text(self, text: str):
        """Set play button text (▶ or ⏸)"""
        self.play_pause_btn.setText(text)
    
    def show_progress(self, message: str = ""):
        """Show progress bar with optional message"""
        self.progress_bar.setVisible(True)
        if message:
            self.status_label.setText(message)
    
    def hide_progress(self):
        """Hide progress bar"""
        self.progress_bar.setVisible(False)
        self.status_label.setText("Ready")
    
    def update_progress(self, value: int, maximum: int = 100):
        """Update progress bar value"""
        self.progress_bar.setMaximum(maximum)
        self.progress_bar.setValue(value)
    
    def set_status(self, status: str):
        """Set status label text"""
        self.status_label.setText(status)
    
    def set_controls_visible(self, visible: bool):
        """Set controls panel visibility state"""
        self.toggle_controls_btn.setChecked(visible)
        if visible:
            self.toggle_controls_btn.setText("⚙️ Controls")
        else:
            self.toggle_controls_btn.setText("⚙️ Show")


class QuickActionPanel(QWidget):
    """Secondary quick action panel for less frequent actions"""
    
    # Signals for main window communication
    analyze_folder = pyqtSignal()
    export_playlist = pyqtSignal()
    settings = pyqtSignal()
    zoom_in = pyqtSignal()
    zoom_out = pyqtSignal()
    reset_zoom = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.apply_styling()
    
    def setup_ui(self):
        """Setup the quick action panel UI"""
        layout = QHBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(5, 2, 5, 2)
        
        # Analysis actions
        self.analyze_folder_btn = ModernButton("🔍 Analyze", "info")
        self.analyze_folder_btn.clicked.connect(self.analyze_folder.emit)
        self.analyze_folder_btn.setMinimumWidth(70)
        layout.addWidget(self.analyze_folder_btn)
        
        # Export actions
        self.export_playlist_btn = ModernButton("📤 Export", "secondary")
        self.export_playlist_btn.clicked.connect(self.export_playlist.emit)
        self.export_playlist_btn.setMinimumWidth(70)
        layout.addWidget(self.export_playlist_btn)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)
        
        # Zoom controls
        self.zoom_in_btn = ModernButton("🔍+", "success")
        self.zoom_in_btn.clicked.connect(self.zoom_in.emit)
        self.zoom_in_btn.setMinimumWidth(40)
        self.zoom_in_btn.setMaximumWidth(40)
        layout.addWidget(self.zoom_in_btn)
        
        self.zoom_out_btn = ModernButton("🔍-", "success")
        self.zoom_out_btn.clicked.connect(self.zoom_out.emit)
        self.zoom_out_btn.setMinimumWidth(40)
        self.zoom_out_btn.setMaximumWidth(40)
        layout.addWidget(self.zoom_out_btn)
        
        self.reset_zoom_btn = ModernButton("🔄", "info")
        self.reset_zoom_btn.clicked.connect(self.reset_zoom.emit)
        self.reset_zoom_btn.setMinimumWidth(40)
        self.reset_zoom_btn.setMaximumWidth(40)
        layout.addWidget(self.reset_zoom_btn)
        
        # Stretch to push everything to the left
        layout.addStretch(1)
        
        # Settings
        self.settings_btn = ModernButton("⚙️ Settings", "secondary")
        self.settings_btn.clicked.connect(self.settings.emit)
        self.settings_btn.setMinimumWidth(80)
        layout.addWidget(self.settings_btn)
        
        # Set size policy
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMaximumHeight(35)
        self.setMinimumHeight(30)
    
    def apply_styling(self):
        """Apply modern styling to the quick action panel"""
        self.setStyleSheet(f"""
            QuickActionPanel {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {BlueLibraryTheme.SURFACE_MEDIUM}, 
                    stop:1 {BlueLibraryTheme.SURFACE_LOW});
                border: 1px solid {BlueLibraryTheme.ACCENT_PRIMARY};
                border-radius: 6px;
                padding: 2px;
            }}
            
            QFrame[frameShape="5"] {{
                color: {BlueLibraryTheme.ACCENT_PRIMARY};
                max-width: 1px;
                margin: 2px 3px;
            }}
        """)
    
    def set_analyze_enabled(self, enabled: bool):
        """Enable/disable analyze button"""
        self.analyze_folder_btn.setEnabled(enabled)
    
    def set_export_enabled(self, enabled: bool):
        """Enable/disable export button"""
        self.export_playlist_btn.setEnabled(enabled)