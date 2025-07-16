#!/usr/bin/env python3
"""
BlueLibrary - Main Window (Clean Integration)
Clean version with proper UI organization for maximum file display space
"""

import sys
import os
from pathlib import Path
from typing import List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QSplitter, QMessageBox, QProgressBar, QLabel, QStatusBar,
    QMenuBar, QMenu, QFileDialog, QHeaderView
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QSize
from PyQt6.QtGui import QAction, QIcon, QFont, QPixmap

# Core imports
from harmonic_mixer.core.application_facade import BlueLibraryFacade
from harmonic_mixer.core.event_system import event_manager, EventType
from harmonic_mixer.core.harmonic_engine import Track

# UI Components
from harmonic_mixer.ui.tabbed_control_panel import TabbedControlPanel
from harmonic_mixer.ui.compact_toolbar import CompactToolbar
from harmonic_mixer.ui.reorganized_ui_styles import ReorganizedUIStyles
from harmonic_mixer.ui.components.main_window_integration import OptimizedTrackView

class MainWindow(QMainWindow):
    """
    Main application window with optimized UI organization
    Prioritizes file display space with reorganized controls
    """
    
    def __init__(self):
        super().__init__()
        
        # Initialize facade
        self.facade = BlueLibraryFacade()
        
        # Initialize UI state
        self.is_playing = False
        self.controls_visible = True
        self.current_track = None
        
        # Initialize UI components
        self.init_ui()
        self.setup_event_connections()
        self.setup_status_bar()
        
        # Apply modern styling
        self.setStyleSheet(ReorganizedUIStyles.get_combined_styles())
        
        print("✅ MainWindow initialized with clean integration")
    
    def init_ui(self):
        """Initialize the main UI layout"""
        self.setWindowTitle("BlueLibrary - Harmonic DJ Mixing")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create compact toolbar
        self.toolbar = CompactToolbar()
        main_layout.addWidget(self.toolbar)
        
        # Create main splitter (horizontal)
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Create optimized track view
        self.track_view = OptimizedTrackView(facade=self.facade)
        self.main_splitter.addWidget(self.track_view)
        
        # Create tabbed control panel
        self.control_panel = TabbedControlPanel()
        self.main_splitter.addWidget(self.control_panel)
        
        # Configure splitter proportions (82% for files, 18% for controls)
        self.main_splitter.setStretchFactor(0, 82)
        self.main_splitter.setStretchFactor(1, 18)
        self.main_splitter.setSizes([1148, 252])  # Default sizes for 1400px width
        
        main_layout.addWidget(self.main_splitter)
        
        # Setup menu bar
        self.setup_menu_bar()
        
        print("✅ UI initialized with optimized layout")
    
    def setup_menu_bar(self):
        """Setup the menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        load_action = QAction('Load Music Folder', self)
        load_action.triggered.connect(self.load_music_folder)
        file_menu.addAction(load_action)
        
        clear_action = QAction('Clear Library', self)
        clear_action.triggered.connect(self.clear_library)
        file_menu.addAction(clear_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('Exit', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu('View')
        
        toggle_controls_action = QAction('Toggle Controls Panel', self)
        toggle_controls_action.triggered.connect(self.toggle_controls_panel)
        view_menu.addAction(toggle_controls_action)
        
        # Tools menu
        tools_menu = menubar.addMenu('Tools')
        
        enhance_action = QAction('Enhance Tracks with AI', self)
        enhance_action.triggered.connect(self.enhance_tracks)
        tools_menu.addAction(enhance_action)
        
        playlist_action = QAction('Generate Playlist', self)
        playlist_action.triggered.connect(self.generate_playlist)
        tools_menu.addAction(playlist_action)
    
    def setup_event_connections(self):
        """Setup event connections between components"""
        
        # Toolbar connections
        self.toolbar.load_folder.connect(self.load_music_folder)
        self.toolbar.clear_library.connect(self.clear_library)
        self.toolbar.generate_playlist.connect(self.generate_playlist)
        self.toolbar.enhance_tracks.connect(self.enhance_tracks)
        self.toolbar.play_pause.connect(self.toggle_playback)
        self.toolbar.stop.connect(self.stop_playback)
        self.toolbar.toggle_controls.connect(self.toggle_controls_panel)
        
        # Control panel connections
        if hasattr(self.control_panel, 'mixing_tab'):
            # Connect mixing controls
            pass
        
        # Event system connections
        event_manager.event_bus.subscribe(
            EventType.TRACK_ANALYZED,
            self.on_track_analyzed
        )
        
        event_manager.event_bus.subscribe(
            EventType.ANALYSIS_PROGRESS,
            self.on_analysis_progress
        )
        
        event_manager.event_bus.subscribe(
            EventType.PLAYLIST_GENERATED,
            self.on_playlist_generated
        )
        
        event_manager.event_bus.subscribe(
            EventType.ANALYSIS_COMPLETED,
            self.on_enhancement_complete
        )
    
    def setup_status_bar(self):
        """Setup the status bar"""
        self.statusBar().showMessage("Ready")
        
        # Add progress bar to status bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.statusBar().addPermanentWidget(self.progress_bar)
        
        # Add track count label
        self.track_count_label = QLabel("0 tracks")
        self.statusBar().addPermanentWidget(self.track_count_label)
    
    def load_music_folder(self):
        """Load music folder dialog"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Music Folder",
            str(Path.home() / "Music")
        )
        
        if folder:
            self.statusBar().showMessage(f"Loading music from: {folder}")
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate
            
            # Load through facade
            self.facade.load_music_folder(folder)
    
    def clear_library(self):
        """Clear the music library"""
        reply = QMessageBox.question(
            self,
            "Clear Library",
            "Are you sure you want to clear the entire music library?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.facade.clear_library()
            self.track_view.clear_tracks()
            self.update_track_count(0)
            self.statusBar().showMessage("Library cleared")
    
    def generate_playlist(self):
        """Generate playlist from selected tracks"""
        selected_tracks = self.track_view.get_selected_tracks()
        
        if not selected_tracks:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select at least one track to generate a playlist."
            )
            return
        
        self.statusBar().showMessage("Generating playlist...")
        playlist = self.facade.generate_playlist(selected_tracks)
        
        if playlist:
            self.statusBar().showMessage(f"Playlist generated with {len(playlist)} tracks")
        else:
            self.statusBar().showMessage("Failed to generate playlist")
    
    def enhance_tracks(self):
        """Enhance selected tracks with AI"""
        selected_tracks = self.track_view.get_selected_tracks()
        
        if not selected_tracks:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select tracks to enhance with AI."
            )
            return
        
        self.statusBar().showMessage("Enhancing tracks with AI...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, len(selected_tracks))
        
        # Enhance through facade
        self.facade.enhance_tracks(selected_tracks)
    
    def toggle_playback(self):
        """Toggle playback state"""
        if self.is_playing:
            self.facade.pause_playback()
            self.is_playing = False
            self.statusBar().showMessage("Playback paused")
        else:
            current_track = self.track_view.get_current_track()
            if current_track:
                self.facade.play_track(current_track)
                self.is_playing = True
                self.statusBar().showMessage(f"Playing: {current_track.title}")
    
    def stop_playback(self):
        """Stop playback"""
        self.facade.stop_playback()
        self.is_playing = False
        self.statusBar().showMessage("Playback stopped")
    
    def toggle_controls_panel(self):
        """Toggle controls panel visibility"""
        if self.controls_visible:
            self.control_panel.setVisible(False)
            self.main_splitter.setSizes([1400, 0])  # 100% for files
            self.controls_visible = False
            self.statusBar().showMessage("Controls hidden - 100% space for files")
        else:
            self.control_panel.setVisible(True)
            self.main_splitter.setSizes([1148, 252])  # 82% for files, 18% for controls
            self.controls_visible = True
            self.statusBar().showMessage("Controls shown")
    
    def update_track_count(self, count: int):
        """Update track count in status bar"""
        self.track_count_label.setText(f"{count} tracks")
    
    # Event handlers
    def on_track_analyzed(self, event):
        """Handle track analyzed event"""
        track = event.data
        self.track_view.add_track(track)
        self.update_track_count(self.track_view.get_track_count())
    
    def on_analysis_progress(self, event):
        """Handle analysis progress event"""
        current, total = event.data
        self.progress_bar.setValue(current)
        self.progress_bar.setMaximum(total)
        self.statusBar().showMessage(f"Analyzing: {current}/{total}")
        
        if current >= total:
            self.progress_bar.setVisible(False)
            self.statusBar().showMessage(f"Analysis complete - {total} tracks loaded")
    
    def on_playlist_generated(self, event):
        """Handle playlist generated event"""
        playlist = event.data
        self.statusBar().showMessage(f"Playlist generated with {len(playlist)} tracks")
    
    def on_enhancement_complete(self, event):
        """Handle enhancement complete event"""
        enhanced_tracks = event.data
        
        # Refresh the enhanced tracks in the view
        self.track_view.refresh_enhanced_tracks(enhanced_tracks)
        
        self.progress_bar.setVisible(False)
        self.statusBar().showMessage(f"Enhancement complete - {len(enhanced_tracks)} tracks enhanced")
    
    def closeEvent(self, event):
        """Handle window close event"""
        reply = QMessageBox.question(
            self,
            "Exit BlueLibrary",
            "Are you sure you want to exit?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Clean shutdown
            event.accept()
        else:
            event.ignore()

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("BlueLibrary")
    app.setApplicationVersion("2.0")
    app.setOrganizationName("BlueLibrary")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Run application
    sys.exit(app.exec())

if __name__ == "__main__":
    main()