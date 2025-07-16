"""
Main window for the Harmonic Mixer application
"""

import sys
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTableWidget, QTableWidgetItem, QPushButton, QLabel, QSlider,
    QGroupBox, QComboBox, QProgressBar, QFileDialog, QHeaderView,
    QAbstractItemView, QMessageBox, QScrollArea, QApplication
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QUrl
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from typing import List, Optional
import os

from ..core.application_facade import BlueLibraryFacade
from ..core.event_system import event_manager, EventType
from ..core.harmonic_engine import Track
from ..utils.audio_analyzer import AudioAnalyzer
from .enhanced_theme import ModernBlueLibraryTheme as BlueLibraryTheme
from .enhanced_components import (
    ModernButton, GradientProgressBar, EnhancedTableItem, 
    ModernHeaderView, StatusIndicator, CompatibilityBadge, EnhancedSlider
)
from .status_bar import StatusBar
from .policy_editor import PolicyQuickSelector, PolicyEditorWidget
from .tabbed_control_panel import TabbedControlPanel
from .compact_toolbar import CompactToolbar, QuickActionPanel
from .reorganized_ui_styles import ReorganizedUIStyles

# Import optimized components
try:
    from .components.virtual_table import VirtualTableWidget
    from .components.search_filter import SearchFilterWidget
    from .components.progress_manager import ProgressBatchManager, ProgressWidget
    from .components.main_window_integration import OptimizedTrackView, OptimizedProgressManager
    OPTIMIZED_COMPONENTS_AVAILABLE = True
    print("✅ Optimized UI components loaded successfully!")
except ImportError as e:
    print(f"⚠️  Optimized components not available: {e}")
    OPTIMIZED_COMPONENTS_AVAILABLE = False


class AsyncLoadThread(QThread):
    """Thread for async folder loading"""
    load_failed = pyqtSignal()
    load_completed = pyqtSignal()
    track_analyzed = pyqtSignal(Track)
    progress_updated = pyqtSignal(int, int)
    
    def __init__(self, facade, folder):
        super().__init__()
        self.facade = facade
        self.folder = folder
    
    def run(self):
        import asyncio
        from ..core.event_system import event_manager, EventType
        
        # Set up event handlers to capture events and emit Qt signals
        def on_track_analyzed(event):
            self.track_analyzed.emit(event.data)
        
        def on_progress(event):
            data = event.data
            self.progress_updated.emit(data['current'], data['total'])
        
        # Subscribe to events temporarily
        event_manager.event_bus.subscribe(EventType.TRACK_ANALYZED, on_track_analyzed)
        event_manager.event_bus.subscribe(EventType.ANALYSIS_PROGRESS, on_progress)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            # Create progress callback
            def progress_callback(current, total):
                event_manager.analysis_progress(current, total)
            
            result = loop.run_until_complete(
                self.facade.load_music_folder(self.folder, progress_callback)
            )
            if result:
                self.load_completed.emit()
            else:
                self.load_failed.emit()
        finally:
            # Unsubscribe from events
            event_manager.event_bus.unsubscribe(EventType.TRACK_ANALYZED, on_track_analyzed)
            event_manager.event_bus.unsubscribe(EventType.ANALYSIS_PROGRESS, on_progress)
            loop.close()


class MetadataAnalyzerThread(QThread):
    """Background thread for analyzing audio metadata"""
    progress = pyqtSignal(int)
    track_analyzed = pyqtSignal(Track)
    finished = pyqtSignal()
    
    def __init__(self, file_paths: List[str]):
        super().__init__()
        self.file_paths = file_paths
        self.analyzer = AudioAnalyzer()
        
    def run(self):
        for i, filepath in enumerate(self.file_paths):
            track = self.analyzer.analyze_file(filepath, str(i))
            if track:
                self.track_analyzed.emit(track)
            self.progress.emit(int((i + 1) / len(self.file_paths) * 100))
        
        self.finished.emit()


class EnhancementThread(QThread):
    """Background thread for LLM track enhancement"""
    progress_updated = pyqtSignal(int, int)  # current, total
    enhancement_completed = pyqtSignal(int)  # enhanced_count
    enhancement_failed = pyqtSignal(str)     # error_message
    
    def __init__(self, facade, tracks):
        super().__init__()
        self.facade = facade
        self.tracks = tracks
        
    def run(self):
        import asyncio
        
        try:
            # Run the async enhancement
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            enhanced_count = loop.run_until_complete(self._enhance_tracks_async())
            self.enhancement_completed.emit(enhanced_count)
            
        except Exception as e:
            self.enhancement_failed.emit(str(e))
        finally:
            loop.close()
    
    async def _enhance_tracks_async(self):
        """Async method to enhance tracks"""
        enhanced_count = 0
        total = len(self.tracks)
        
        for i, track in enumerate(self.tracks):
            try:
                # Emit progress
                self.progress_updated.emit(i, total)
                
                # Enhance the track
                enhancement = await self.facade.enhance_track_metadata(track.id)
                if enhancement and enhancement.confidence_score > 0.1:
                    enhanced_count += 1
                
            except Exception as e:
                print(f"❌ Failed to enhance track {track.title}: {e}")
                # Continue with next track instead of failing completely
                continue
        
        # Final progress update
        self.progress_updated.emit(total, total)
        return enhanced_count


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.facade = BlueLibraryFacade()
        self.analyzer_thread = None
        self.load_thread = None
        
        # Initialize audio player
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(0.5)  # Set initial volume to 50%
        self.is_playing = False
        self.current_audio_file = None
        
        # Progress update throttling
        self._last_progress_update = 0
        
        # Initialize optimized components if available
        self.optimized_track_view = None
        self.optimized_progress_manager = None
        self.use_optimized_ui = OPTIMIZED_COMPONENTS_AVAILABLE
        
        # Initialize new UI components
        self.tabbed_control_panel = None
        self.compact_toolbar = None
        self.quick_action_panel = None
        self.controls_visible = True
        
        if self.use_optimized_ui:
            print("🚀 Initializing with optimized UI components...")
            self.optimized_track_view = OptimizedTrackView(self.facade)
            self.optimized_progress_manager = OptimizedProgressManager(self.facade)
        
        self.init_ui()
        self.setup_event_handlers()
        self.load_settings()
        
        # Auto-restore tracks after UI is fully initialized
        if self.facade.should_auto_restore():
            success = self.facade.restore_last_session()
            if success:
                # Load existing tracks into optimized components
                if self.use_optimized_ui and self.optimized_track_view:
                    tracks = self.facade.get_tracks()
                    if tracks:
                        print(f"📚 Loading {len(tracks)} existing tracks into optimized view...")
                        self.optimized_track_view.setTracks(tracks)
                
                # Update all button states after successful restore
                self.update_button_states()
        
        # Update button states initially
        self.update_button_states()
        
        # Initialize additional button states
        self.update_advanced_button_states()
        
        # Apply modern theme after UI initialization
        self.apply_modern_theme()
        
    def apply_modern_theme(self):
        """Apply the enhanced modern theme to the entire application"""
        # Apply main window stylesheet
        main_stylesheet = BlueLibraryTheme.get_main_window_stylesheet()
        
        # Add reorganized UI styles
        reorganized_stylesheet = ReorganizedUIStyles.get_combined_styles()
        
        # Add specific styling for enhanced components
        enhanced_stylesheet = f"""
            /* Enhanced Central Widget */
            #centralWidget {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {BlueLibraryTheme.BACKGROUND_PRIMARY}, 
                    stop:1 {BlueLibraryTheme.BACKGROUND_SECONDARY});
                border-radius: 10px;
                margin: 5px;
            }}
            
            /* Enhanced Track Table */
            #trackTable {{
                background-color: {BlueLibraryTheme.SURFACE_LOW};
                border: 2px solid {BlueLibraryTheme.ACCENT_PRIMARY};
                border-radius: 12px;
                gridline-color: {BlueLibraryTheme.BACKGROUND_TERTIARY};
                selection-background-color: {BlueLibraryTheme.ACCENT_PRIMARY};
            }}
            
            #trackTable::item {{
                padding: 12px 8px;
                border: none;
                color: {BlueLibraryTheme.TEXT_PRIMARY};
            }}
            
            #trackTable::item:selected {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {BlueLibraryTheme.ACCENT_PRIMARY}, 
                    stop:1 {BlueLibraryTheme.ACCENT_SECONDARY});
                color: {BlueLibraryTheme.TEXT_PRIMARY};
                border-radius: 6px;
                font-weight: 600;
            }}
            
            #trackTable::item:hover {{
                background-color: {BlueLibraryTheme.SURFACE_HIGH};
                border-radius: 6px;
            }}
            
            /* Enhanced Combo Boxes */
            #modeCombo {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {BlueLibraryTheme.SURFACE_MEDIUM}, 
                    stop:1 {BlueLibraryTheme.SURFACE_LOW});
                border: 2px solid {BlueLibraryTheme.ACCENT_PRIMARY};
                border-radius: 8px;
                padding: 8px 12px;
                color: {BlueLibraryTheme.TEXT_PRIMARY};
                font-weight: 600;
                min-width: 150px;
            }}
            
            /* Enhanced Labels */
            #modeLabel {{
                color: {BlueLibraryTheme.TEXT_ACCENT};
                font-weight: 700;
                font-size: 14px;
            }}
        """
        
        # Combine stylesheets
        combined_stylesheet = main_stylesheet + reorganized_stylesheet + enhanced_stylesheet
        self.setStyleSheet(combined_stylesheet)
        
        # Set object names for enhanced styling
        if hasattr(self, 'track_table'):
            self.track_table.setObjectName("trackTable")
        
    def init_ui(self):
        self.setWindowTitle("BlueLibrary - Advanced Harmonic Mixer")
        # Set more reasonable size for macOS screens
        self.setGeometry(100, 100, 1200, 700)
        self.setMinimumSize(1000, 600)
        
        # Apply enhanced modern theme
        self.setStyleSheet(BlueLibraryTheme.get_main_window_stylesheet())
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Compact toolbar
        self.compact_toolbar = CompactToolbar()
        self.setup_toolbar_connections()
        main_layout.addWidget(self.compact_toolbar)
        
        # Quick action panel
        self.quick_action_panel = QuickActionPanel()
        self.setup_quick_action_connections()
        main_layout.addWidget(self.quick_action_panel)
        
        # Keep reference to progress bar from toolbar
        self.progress_bar = self.compact_toolbar.progress_bar
        
        # Legacy buttons for backward compatibility
        self.load_folder_btn = self.compact_toolbar.load_folder_btn
        self.enhance_all_btn = self.compact_toolbar.enhance_tracks_btn
        self.enhance_selected_btn = self.compact_toolbar.enhance_tracks_btn
        
        # Main content area with splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - Track table (optimized or standard)
        if self.use_optimized_ui and self.optimized_track_view:
            print("📊 Using optimized virtual table...")
            self.track_table = self.optimized_track_view
            # Connect optimized signals
            self.optimized_track_view.track_selected.connect(self.on_optimized_track_selected)
        else:
            print("📊 Using standard table...")
            self.track_table = QTableWidget()
            self.setup_track_table()
        
        splitter.addWidget(self.track_table)
        
        # Right panel - Tabbed Controls
        self.tabbed_control_panel = TabbedControlPanel()
        self.setup_tabbed_panel_connections()
        self.tabbed_control_panel.setMinimumWidth(280)  # Reduced from 350 to save space
        self.tabbed_control_panel.setMaximumWidth(320)  # Prevent excessive width
        
        # Initialize references to new tabbed components
        self.initialize_tabbed_references()
        
        # Main content area with splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - Track table (optimized or standard)  
        if self.use_optimized_ui and self.optimized_track_view:
            print("📊 Using optimized virtual table...")
            self.track_table = self.optimized_track_view
            # Connect optimized signals
            self.optimized_track_view.track_selected.connect(self.on_optimized_track_selected)
        else:
            print("📊 Using standard table...")
            self.track_table = QTableWidget()
            self.setup_track_table()
        
        splitter.addWidget(self.track_table)
        
        # Right panel - Tabbed Controls
        splitter.addWidget(self.tabbed_control_panel)
        
        # Configure splitter proportions - Give more space to the table
        splitter.setStretchFactor(0, 6)  # Table gets 6/7 of space (increased from 4/5)
        splitter.setStretchFactor(1, 1)  # Controls get 1/7 of space
        
        # Set initial splitter sizes for better proportions
        splitter.setSizes([900, 200])  # Approximately 82% table, 18% controls (improved from 73%/27%)
        
        # Add splitter to main layout
        main_layout.addWidget(splitter)
        
        # Playlist generation
        playlist_group = QGroupBox("Playlist Generation")
        playlist_layout = QVBoxLayout()
        
        # Progression curve
        curve_layout = QHBoxLayout()
        curve_layout.addWidget(QLabel("Energy Curve:"))
        self.curve_combo = QComboBox()
        self.curve_combo.addItems(["Neutral", "Ascending", "Descending"])
        curve_layout.addWidget(self.curve_combo)
        playlist_layout.addLayout(curve_layout)
        
        # Enhanced target length control
        length_layout = QHBoxLayout()
        length_layout.setSpacing(15)  # Increased spacing for better readability
        
        length_label = QLabel("Playlist Length:")
        length_label.setMinimumWidth(100)
        length_layout.addWidget(length_label)
        
        self.length_slider = EnhancedSlider(Qt.Orientation.Horizontal)
        self.length_slider.setRange(5, 50)
        self.length_slider.setValue(15)
        self.length_label = QLabel("15")
        self.length_label.setMinimumWidth(30)
        self.length_slider.valueChanged.connect(
            lambda v: self.length_label.setText(str(v))
        )
        length_layout.addWidget(self.length_slider)
        length_layout.addWidget(self.length_label)
        playlist_layout.addLayout(length_layout)
        
        # Enhanced generate button
        self.generate_btn = ModernButton("Generate Playlist", "success")
        self.generate_btn.clicked.connect(self.generate_playlist)
        self.generate_btn.setEnabled(False)
        playlist_layout.addWidget(self.generate_btn)
        
        # Add Policies section
        policies_group = QGroupBox("Mixing Policies (Block 6)")
        policies_layout = QVBoxLayout()
        
        # Initialize policy manager
        try:
            from ..analysis.configurable_policies import ConfigurablePolicyManager
            import tempfile
            self.policy_manager = ConfigurablePolicyManager(config_dir=tempfile.gettempdir())
            
            # Policy quick selector
            self.policy_selector = PolicyQuickSelector(self.policy_manager)
            self.policy_selector.policy_selected.connect(self.on_policy_selected)
            policies_layout.addWidget(self.policy_selector)
            
            # Policy test button
            self.test_policy_btn = ModernButton("Test Policy", "secondary")
            self.test_policy_btn.clicked.connect(self.test_selected_policy)
            policies_layout.addWidget(self.test_policy_btn)
            
        except Exception as e:
            # Fallback if policies not available
            policies_layout.addWidget(QLabel(f"Policies not available: {e}"))
        
        policies_group.setLayout(policies_layout)
        right_layout.addWidget(policies_group)
        
        # Add spacing between sections  
        right_layout.addSpacing(5)
        
        # Add Contextual Generation (Block 3)
        contextual_group = QGroupBox("Contextual Generation (Block 3)")
        contextual_layout = QVBoxLayout()
        
        # Time of day selector
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("Time of Day:"))
        self.time_combo = QComboBox()
        self.time_combo.addItems(["any", "morning", "afternoon", "evening", "night"])
        time_layout.addWidget(self.time_combo)
        contextual_layout.addLayout(time_layout)
        
        # Activity selector
        activity_layout = QHBoxLayout()
        activity_layout.addWidget(QLabel("Activity:"))
        self.activity_combo = QComboBox()
        self.activity_combo.addItems(["any", "party", "workout", "chill", "focus", "social_dancing"])
        activity_layout.addWidget(self.activity_combo)
        contextual_layout.addLayout(activity_layout)
        
        # Season selector
        season_layout = QHBoxLayout()
        season_layout.addWidget(QLabel("Season:"))
        self.season_combo = QComboBox()
        self.season_combo.addItems(["any", "spring", "summer", "autumn", "winter"])
        season_layout.addWidget(self.season_combo)
        contextual_layout.addLayout(season_layout)
        
        # Contextual generate button
        self.contextual_generate_btn = ModernButton("Generate Contextual Playlist", "primary")
        self.contextual_generate_btn.clicked.connect(self.generate_contextual_playlist)
        self.contextual_generate_btn.setEnabled(False)
        contextual_layout.addWidget(self.contextual_generate_btn)
        
        contextual_group.setLayout(contextual_layout)
        right_layout.addWidget(contextual_group)
        
        # Add spacing between sections
        right_layout.addSpacing(5)
        
        # Add Temporal/Linguistic (Block 4)
        temporal_group = QGroupBox("Temporal & Linguistic (Block 4)")
        temporal_layout = QVBoxLayout()
        
        # Temporal flow
        temporal_flow_layout = QHBoxLayout()
        temporal_flow_layout.addWidget(QLabel("Temporal Flow:"))
        self.temporal_flow_combo = QComboBox()
        self.temporal_flow_combo.addItems(["none", "chronological", "reverse_chronological", "era_journey"])
        temporal_flow_layout.addWidget(self.temporal_flow_combo)
        temporal_layout.addLayout(temporal_flow_layout)
        
        # Linguistic flow
        linguistic_flow_layout = QHBoxLayout()
        linguistic_flow_layout.addWidget(QLabel("Linguistic Flow:"))
        self.linguistic_flow_combo = QComboBox()
        self.linguistic_flow_combo.addItems(["none", "monolingual", "bilingual_bridge", "multilingual_journey"])
        linguistic_flow_layout.addWidget(self.linguistic_flow_combo)
        temporal_layout.addLayout(linguistic_flow_layout)
        
        # Temporal generate button
        self.temporal_generate_btn = ModernButton("Generate Temporal Sequence", "secondary")
        self.temporal_generate_btn.clicked.connect(self.generate_temporal_sequence)
        self.temporal_generate_btn.setEnabled(False)
        temporal_layout.addWidget(self.temporal_generate_btn)
        
        temporal_group.setLayout(temporal_layout)
        right_layout.addWidget(temporal_group)
        
        # Add spacing between sections
        right_layout.addSpacing(5)
        
        # Add Global Optimization (Block 5)
        optimization_group = QGroupBox("Global Optimization (Block 5)")
        optimization_layout = QVBoxLayout()
        
        # Optimization objective
        objective_layout = QHBoxLayout()
        objective_layout.addWidget(QLabel("Objective:"))
        self.optimization_combo = QComboBox()
        self.optimization_combo.addItems(["balanced", "compatibility", "energy_flow", "cultural_journey", "narrative"])
        objective_layout.addWidget(self.optimization_combo)
        optimization_layout.addLayout(objective_layout)
        
        # Max alternatives slider
        alternatives_layout = QHBoxLayout()
        alternatives_layout.setSpacing(15)  # Add consistent spacing
        alternatives_layout.addWidget(QLabel("Alternatives:"))
        self.alternatives_slider = EnhancedSlider(Qt.Orientation.Horizontal)
        self.alternatives_slider.setRange(1, 5)
        self.alternatives_slider.setValue(3)
        self.alternatives_label = QLabel("3")
        self.alternatives_slider.valueChanged.connect(
            lambda v: self.alternatives_label.setText(str(v))
        )
        alternatives_layout.addWidget(self.alternatives_slider)
        alternatives_layout.addWidget(self.alternatives_label)
        optimization_layout.addLayout(alternatives_layout)
        
        # Global optimize button
        self.global_optimize_btn = ModernButton("Global Optimization", "success")
        self.global_optimize_btn.clicked.connect(self.generate_optimized_playlist)
        self.global_optimize_btn.setEnabled(False)
        optimization_layout.addWidget(self.global_optimize_btn)
        
        optimization_group.setLayout(optimization_layout)
        right_layout.addWidget(optimization_group)
        
        # Add spacing between sections
        right_layout.addSpacing(5)
        
        playlist_group.setLayout(playlist_layout)
        right_layout.addWidget(playlist_group)
        
        # Player controls (placeholder)
        player_group = QGroupBox("Player")
        player_layout = QVBoxLayout()
        
        self.current_track_label = QLabel("No track selected")
        self.current_track_label.setWordWrap(True)
        player_layout.addWidget(self.current_track_label)
        
        player_controls = QHBoxLayout()
        self.play_btn = ModernButton("▶", "primary")
        self.play_btn.setEnabled(False)
        self.play_btn.clicked.connect(self.play_pause_audio)
        self.play_btn.setMinimumWidth(60)
        player_controls.addWidget(self.play_btn)
        
        self.stop_btn = ModernButton("⏹", "secondary")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_audio)
        self.stop_btn.setMinimumWidth(60)
        player_controls.addWidget(self.stop_btn)
        
        # Enhanced volume control
        volume_label = QLabel("Volume:")
        player_controls.addWidget(volume_label)
        
        self.volume_slider = EnhancedSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.setMaximumWidth(100)
        self.volume_slider.valueChanged.connect(self.set_volume)
        player_controls.addWidget(self.volume_slider)
        
        player_layout.addLayout(player_controls)
        
        player_group.setLayout(player_layout)
        right_layout.addWidget(player_group)
        
        # Add minimal stretch to prevent cramping
        right_layout.addStretch(1)
        
        splitter.addWidget(self.tabbed_control_panel)
        # Give more space to the table, less to controls
        splitter.setStretchFactor(0, 6)  # Table gets 6/7 of space (increased from 4/5)
        splitter.setStretchFactor(1, 1)  # Controls get 1/7 of space
        
        # Set initial splitter sizes for better proportions
        splitter.setSizes([900, 200])  # Approximately 82% table, 18% controls (improved from 73%/27%)
        
        main_layout.addWidget(splitter)
        
        # Update initial weights display
        self.update_weight_display()
    
    def setup_event_handlers(self):
        """Setup event handlers for UI updates"""
        # Track events
        event_manager.event_bus.subscribe(
            EventType.TRACK_ANALYZED,
            lambda event: self.add_track_to_table(event.data)
        )
        
        event_manager.event_bus.subscribe(
            EventType.TRACKS_CLEARED,
            lambda event: self.clear_track_table()
        )
        
        # Analysis events
        event_manager.event_bus.subscribe(
            EventType.ANALYSIS_PROGRESS,
            lambda event: self.update_progress(event.data['current'], event.data['total'])
        )
        
        event_manager.event_bus.subscribe(
            EventType.ANALYSIS_COMPLETED,
            lambda event: self.on_analysis_finished()
        )
        
        # Playlist events
        event_manager.event_bus.subscribe(
            EventType.PLAYLIST_GENERATED,
            lambda event: self.show_playlist(event.data['playlist'])
        )
        
        # Load existing tracks on startup
        self.load_existing_tracks_on_startup()
    
    def load_existing_tracks_on_startup(self):
        """Load existing tracks from database on application startup"""
        try:
            # Get tracks that were already loaded by facade during initialization
            tracks = self.facade.get_tracks()
            if tracks:
                print(f"🚀 Loading {len(tracks)} existing tracks on startup...")
                self.populate_table()
                self.update_button_states()
                print(f"✅ Startup tracks loaded successfully")
            else:
                print("ℹ️  No existing tracks found on startup")
        except Exception as e:
            print(f"⚠️  Error loading startup tracks: {e}")
            # Don't show error to user, just log it
    
    def clear_track_table(self):
        """Clear the track table"""
        # Use optimized track view if available
        if self.use_optimized_ui and hasattr(self.track_table, 'clear_tracks'):
            self.track_table.clear_tracks()
        else:
            # Standard table implementation
            self.track_table.setRowCount(0)
        self.current_track_label.setText("No track selected")
        self.play_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.generate_btn.setEnabled(False)
        # Stop any current playback
        if self.is_playing:
            self.stop_audio()
    
    def update_progress(self, current: int, total: int):
        """Update progress bar with throttling to prevent excessive repaints"""
        import time
        
        # Throttle updates to reduce repaint frequency
        now = time.time()
        if now - self._last_progress_update < 0.1:  # 100ms throttle
            return
        self._last_progress_update = now
        
        if hasattr(self, 'progress_bar'):
            self.progress_bar.setValue(int((current / total) * 100))
        
    def create_menu_bar(self):
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        load_action = QAction("Load Folder", self)
        load_action.triggered.connect(self.load_music_folder)
        file_menu.addAction(load_action)
        
        # Clear library action
        clear_library_action = QAction("Clear Library", self)
        clear_library_action.triggered.connect(self.clear_library)
        file_menu.addAction(clear_library_action)
        
        file_menu.addSeparator()
        
        # Policies menu
        policies_action = QAction("Policy Editor", self)
        policies_action.triggered.connect(self.open_policy_editor)
        file_menu.addAction(policies_action)
        
        file_menu.addSeparator()
        
        # Export submenu
        export_menu = file_menu.addMenu("Export Playlist")
        
        # Serato DJ export (prioritized)
        export_serato_action = QAction("🎧 Serato DJ Pro Library", self)
        export_serato_action.triggered.connect(self.export_playlist_serato)
        export_menu.addAction(export_serato_action)
        
        export_menu.addSeparator()
        
        export_m3u_action = QAction("M3U Format", self)
        export_m3u_action.triggered.connect(self.export_playlist_m3u)
        export_menu.addAction(export_m3u_action)
        
        file_menu.addSeparator()
        
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)
        
        # Settings menu
        settings_menu = menubar.addMenu("Settings")
        
        llm_settings_action = QAction("LLM Configuration", self)
        llm_settings_action.triggered.connect(self.show_llm_settings)
        settings_menu.addAction(llm_settings_action)
        
        # Playlist menu
        playlist_menu = menubar.addMenu("Playlist")
        
        # Enhanced playlist generator
        generate_action = QAction("🎵 Generate Playlist", self)
        generate_action.setShortcut("Ctrl+G")
        generate_action.triggered.connect(self.generate_playlist)
        playlist_menu.addAction(generate_action)
        
        playlist_menu.addSeparator()
        
        # Quick playlist presets
        quick_menu = playlist_menu.addMenu("Quick Presets")
        
        presets = [
            ("Party Mix (20 tracks)", lambda: self.quick_generate_playlist("ascending", 20)),
            ("Chill Session (15 tracks)", lambda: self.quick_generate_playlist("neutral", 15)),
            ("Workout Mix (25 tracks)", lambda: self.quick_generate_playlist("peak", 25)),
            ("Quick Mix (10 tracks)", lambda: self.quick_generate_playlist("neutral", 10))
        ]
        
        for name, callback in presets:
            action = QAction(name, self)
            action.triggered.connect(callback)
            quick_menu.addAction(action)
        
        # View menu
        view_menu = menubar.addMenu("View")
        
        # Toggle columns submenu
        columns_menu = view_menu.addMenu("Columns")
        
        # Add column toggle actions
        column_actions = [
            ("Title", 0), ("Artist", 1), ("Key", 2), ("BPM", 3), ("Energy", 4),
            ("Emotion", 5), ("Genre", 6), ("Album", 7), ("Year", 8), ("Duration", 9),
            ("Compatibility", 10), ("Last Played", 11), ("Play Count", 12), ("Rating", 13),
            ("Status", 14), ("Enhanced", 15), ("Mood", 16), ("Danceability", 17), ("Valence", 18)
        ]
        
        for col_name, col_index in column_actions:
            action = QAction(col_name, self, checkable=True, checked=True)
            action.triggered.connect(lambda checked, idx=col_index: self.toggle_column(idx, checked))
            columns_menu.addAction(action)
        
        view_menu.addSeparator()
        
        # Zoom actions
        zoom_in_action = QAction("Zoom In", self)
        zoom_in_action.setShortcut("Ctrl++")
        zoom_in_action.triggered.connect(self.zoom_in)
        view_menu.addAction(zoom_in_action)
        
        zoom_out_action = QAction("Zoom Out", self)
        zoom_out_action.setShortcut("Ctrl+-")
        zoom_out_action.triggered.connect(self.zoom_out)
        view_menu.addAction(zoom_out_action)
        
        reset_zoom_action = QAction("Reset Zoom", self)
        reset_zoom_action.setShortcut("Ctrl+0")
        reset_zoom_action.triggered.connect(self.reset_zoom)
        view_menu.addAction(reset_zoom_action)
        
        view_menu.addSeparator()
        
        # Refresh action
        refresh_action = QAction("Refresh", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self.refresh_view)
        view_menu.addAction(refresh_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_track_table(self):
        # Expanded to include all LLM enhanced metadata columns
        self.track_table.setColumnCount(19)
        self.track_table.setHorizontalHeaderLabels([
            # Original columns
            "Title", "Artist", "Key", "BPM", "Energy", "Emotion", "Genre",
            # Enhanced metadata columns
            "Subgenre", "Mood", "Era", "Language", "Danceability",
            # Contextual columns
            "Time of Day", "Activity", "Season",
            # DJ-specific columns
            "Mix Friendly", "Crowd Appeal", "Production", "Confidence"
        ])
        
        # Configure table properties with enhanced styling
        self.track_table.setAlternatingRowColors(True)
        self.track_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.track_table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.track_table.verticalHeader().setVisible(False)
        
        # Use enhanced header view with modern styling
        header = ModernHeaderView(Qt.Orientation.Horizontal, self.track_table)
        self.track_table.setHorizontalHeader(header)
        header.setStretchLastSection(False)  # Don't stretch last section
        
        # Apply enhanced table styling
        self.track_table.setObjectName("trackTable")
        self.track_table.setShowGrid(True)
        self.track_table.setGridStyle(Qt.PenStyle.SolidLine)
        
        # Set minimum widths for readability
        column_widths = {
            0: 200,  # Title - wider for song names
            1: 150,  # Artist - wide for artist names
            2: 60,   # Key - small
            3: 60,   # BPM - small
            4: 60,   # Energy - small
            5: 60,   # Emotion - small
            6: 120,  # Genre - medium
            7: 120,  # Subgenre - medium
            8: 100,  # Mood - medium
            9: 80,   # Era - small
            10: 100, # Language - medium
            11: 80,  # Danceability - small
            12: 100, # Time of Day - medium
            13: 100, # Activity - medium
            14: 80,  # Season - small
            15: 80,  # Mix Friendly - small
            16: 80,  # Crowd Appeal - small
            17: 80,  # Production - small
            18: 80   # Confidence - small
        }
        
        for col, width in column_widths.items():
            self.track_table.setColumnWidth(col, width)
        
        # Make main columns (Title, Artist) resize with content
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)  # Title
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)  # Artist
        
        # Connect selection change
        self.track_table.itemSelectionChanged.connect(self.on_track_selected)
        
        # Add explanatory tooltips for LLM columns
        self.setup_column_tooltips()
    
    def setup_column_tooltips(self):
        """Setup explanatory tooltips for table columns"""
        tooltips = {
            0: "Track title",
            1: "Artist name",
            2: "Musical key (Camelot notation)",
            3: "Beats per minute (tempo)",
            4: "Energy level (1-10 scale)",
            5: "Emotional intensity (1-10 scale)",
            6: "Musical genre",
            # LLM Enhanced columns
            7: "Specific subgenre identified by AI (e.g., 'Deep House', 'Latin Trap')",
            8: "Overall mood/vibe identified by AI (e.g., 'uplifting', 'melancholic')",
            9: "Musical era/time period (e.g., '2020s', '90s', 'classic')",
            10: "Primary language of vocals or 'instrumental'",
            11: "How danceable this track is (0-100%)",
            12: "Best time of day to play this track",
            13: "Ideal activity context (workout, party, chill, focus)",
            14: "Seasonal feel of the track",
            15: "How easy this track is to mix with others (0-100%)",
            16: "How appealing this track is to crowds (0-100%)",
            17: "Production quality assessment (0-100%)",
            18: "AI confidence in the analysis (0-100%)"
        }
        
        # Set tooltips on header items (store for later use)
        self.column_tooltips = tooltips
    
    def get_selected_tracks(self):
        """Get list of currently selected tracks using track IDs for reliable mapping"""
        # Handle optimized track view
        if self.use_optimized_ui and hasattr(self.track_table, 'get_selected_tracks'):
            return self.track_table.get_selected_tracks()
        
        # Standard table implementation
        # Get selected rows directly from selection model (avoids duplicates from multiple columns)
        selected_indices = self.track_table.selectionModel().selectedRows()
        
        # Get track IDs from selected rows
        selected_track_ids = []
        for index in selected_indices:
            row = index.row()
            title_item = self.track_table.item(row, 0)  # Title column stores track ID
            if title_item:
                track_id = title_item.data(Qt.ItemDataRole.UserRole)
                if track_id is not None:
                    selected_track_ids.append(track_id)
        
        # Find tracks by ID from facade (ensure unique results)
        tracks = self.facade.get_tracks()
        selected_tracks = []
        found_ids = set()
        
        for track in tracks:
            if track.id in selected_track_ids and track.id not in found_ids:
                selected_tracks.append(track)
                found_ids.add(track.id)
        
        return selected_tracks
    
    def on_optimized_track_selected(self, track):
        """Handle track selection from optimized components"""
        print(f"🎵 Optimized track selected: {track.title} by {track.artist}")
        # Update UI state as needed
        self.update_button_states()
    
    def get_selected_track_count(self):
        """Get number of currently selected tracks"""
        # Handle optimized track view
        if self.use_optimized_ui and hasattr(self.track_table, 'get_selected_tracks'):
            selected_tracks = self.track_table.get_selected_tracks()
            return len(selected_tracks)
        
        # Standard table implementation
        selected_rows = set()
        for item in self.track_table.selectedItems():
            selected_rows.add(item.row())
        return len(selected_rows)
    
    def format_llm_value(self, value, value_type="string"):
        """Format LLM metadata values for display in table"""
        if value is None or value == "" or value == []:
            return "-"
        
        if value_type == "percentage":
            if isinstance(value, (int, float)):
                percentage = int(value * 100)
                return f"{percentage}%"
            return "-"
        elif value_type == "float":
            if isinstance(value, (int, float)):
                return f"{value:.1f}"
            return "-"
        elif value_type == "list":
            if isinstance(value, list) and value:
                # Clean and format list items
                clean_items = [str(v).strip() for v in value[:3] if v]
                return ", ".join(clean_items) if clean_items else "-"
            return "-"
        elif value_type == "time":
            if isinstance(value, (int, float)):
                return f"{value:.1f}s"
            return "-"
        else:
            # String normalization
            if isinstance(value, str):
                value = value.strip()
                if not value:
                    return "-"
                # Normalize common values
                value = self.normalize_string_value(value, value_type)
                return value
            return str(value) if value else "-"
    
    def normalize_string_value(self, value: str, context: str = "string") -> str:
        """Normalize string values for consistent display"""
        value = value.strip()
        
        # Capitalize first letter for better display
        if value and value[0].islower():
            value = value[0].upper() + value[1:]
        
        # Context-specific normalizations
        if context == "mood":
            # Common mood normalizations
            mood_mappings = {
                "uplifting": "Uplifting",
                "energetic": "Energetic", 
                "melancholic": "Melancholic",
                "happy": "Happy",
                "sad": "Sad",
                "aggressive": "Aggressive",
                "peaceful": "Peaceful",
                "romantic": "Romantic"
            }
            return mood_mappings.get(value.lower(), value)
        
        elif context == "era":
            # Era normalizations
            if value.lower().endswith("s") and value[:-1].isdigit():
                # "2020s", "90s" etc.
                return value.upper()
            elif value.isdigit() and len(value) == 4:
                # "2020" -> "2020s"
                return f"{value}s"
            return value
        
        elif context == "time_of_day":
            # Time of day normalizations
            time_mappings = {
                "morning": "Morning",
                "afternoon": "Afternoon", 
                "evening": "Evening",
                "night": "Night",
                "dawn": "Dawn",
                "dusk": "Dusk"
            }
            return time_mappings.get(value.lower(), value)
        
        elif context == "activity":
            # Activity normalizations  
            activity_mappings = {
                "workout": "Workout",
                "party": "Party",
                "chill": "Chill",
                "focus": "Focus",
                "study": "Study",
                "driving": "Driving",
                "dancing": "Dancing",
                "relaxing": "Relaxing"
            }
            return activity_mappings.get(value.lower(), value)
        
        elif context == "season":
            # Season normalizations
            season_mappings = {
                "spring": "Spring",
                "summer": "Summer",
                "fall": "Fall", 
                "autumn": "Autumn",
                "winter": "Winter"
            }
            return season_mappings.get(value.lower(), value)
        
        elif context == "language":
            # Language normalizations
            language_mappings = {
                "english": "English",
                "spanish": "Spanish",
                "french": "French",
                "german": "German",
                "italian": "Italian",
                "portuguese": "Portuguese",
                "instrumental": "Instrumental",
                "japanese": "Japanese",
                "korean": "Korean",
                "chinese": "Chinese"
            }
            return language_mappings.get(value.lower(), value)
        
        # Default: return with proper capitalization
        return value
    
    def get_enhanced_metadata_for_track(self, track):
        """Get enhanced metadata for a track via facade"""
        try:
            enhanced = self.facade.get_enhanced_metadata(track.id)
            return enhanced
        except Exception as e:
            print(f"Error getting enhanced metadata for {track.title}: {e}")
            return None
    
    def load_music_folder(self):
        # Get last folder from recent folders
        recent_folders = self.facade.get_recent_folders()
        start_dir = recent_folders[0] if recent_folders else ""
        
        folder = QFileDialog.getExistingDirectory(
            self, "Select Music Folder", start_dir
        )
        
        if folder:
            # Show progress (don't clear tracks - we're adding to library)
            # self.track_table.setRowCount(0)  # Commented out to preserve existing tracks
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.status_bar.show_progress("Loading music folder...")
            
            # Start async loading thread
            self.load_thread = AsyncLoadThread(self.facade, folder)
            self.load_thread.load_failed.connect(self.on_load_failed)
            self.load_thread.load_completed.connect(self.on_load_completed)
            self.load_thread.track_analyzed.connect(self.add_track_to_table)
            self.load_thread.progress_updated.connect(self.update_progress)
            self.load_thread.start()
    
    def on_load_failed(self):
        """Handle load failure on main thread"""
        self.progress_bar.setVisible(False)
        self.status_bar.show_error("Failed to load music from the selected folder")
        QMessageBox.warning(
            self, "Load Failed",
            "Failed to load music from the selected folder."
        )
    
    def on_load_completed(self):
        """Handle successful load completion"""
        # Hide progress bar and update status
        self.progress_bar.setVisible(False)
        self.update_button_states()
        tracks = self.facade.get_tracks()
        self.status_bar.show_success(f"Successfully loaded {len(tracks)} tracks!")
    
    def analyze_tracks(self, file_paths: List[str]):
        """Analyze tracks using the facade's async analyzer"""
        if not file_paths:
            return
        
        try:
            self.status_bar.show_message(f"Analyzing {len(file_paths)} tracks...")
            
            # Use facade to analyze tracks
            analyzed_tracks = self.facade.analyze_audio_files(file_paths)
            
            if analyzed_tracks:
                # Tracks are automatically added to facade via TRACK_ANALYZED events
                # No need to manually add them or call populate_table()
                self.status_bar.show_success(f"Successfully analyzed {len(analyzed_tracks)} tracks")
            else:
                self.status_bar.show_warning("No tracks were successfully analyzed")
                
        except Exception as e:
            self.status_bar.show_error(f"Error analyzing tracks: {str(e)}")
    
    def clear_library(self):
        """Clear the entire music library"""
        reply = QMessageBox.question(
            self, "Clear Library",
            "Are you sure you want to clear the entire music library?\n\nThis will remove all loaded tracks and cached data.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Clear facade and database
            self.facade.clear_library()
            # Clear UI
            self.clear_track_table()
            self.status_bar.show_info("Music library cleared")
    
    def add_track_to_table(self, track):
        # Use optimized track view if available
        if self.use_optimized_ui and hasattr(self.track_table, 'add_track'):
            self.track_table.add_track(track)
            return
        
        # Standard table implementation
        row = self.track_table.rowCount()
        self.track_table.insertRow(row)
        
        # Check if track is available
        is_available = getattr(track, 'is_available', True)
        
        # Get enhanced metadata
        enhanced = self.get_enhanced_metadata_for_track(track)
        
        # Determine item types based on track properties
        item_type = "default"
        if enhanced:
            item_type = "enhanced"
        elif not is_available:
            item_type = "unavailable"
        elif hasattr(track, 'energy') and track.energy:
            if track.energy > 8.0:
                item_type = "energy_high"
            elif track.energy < 4.0:
                item_type = "energy_low"
        
        # Create enhanced table items - Original columns (0-6)
        items = []
        items.append(EnhancedTableItem(track.title, item_type))  # 0: Title
        items.append(EnhancedTableItem(track.artist, item_type))  # 1: Artist
        items.append(EnhancedTableItem(track.key or "", item_type))  # 2: Key
        items.append(EnhancedTableItem(f"{track.bpm:.1f}" if track.bpm else "", item_type))  # 3: BPM
        items.append(EnhancedTableItem(f"{track.energy:.1f}" if track.energy else "", item_type))  # 4: Energy
        items.append(EnhancedTableItem(f"{track.emotional_intensity:.1f}" if track.emotional_intensity else "", item_type))  # 5: Emotion
        items.append(EnhancedTableItem(track.genre or "", item_type))  # 6: Genre
        
        # Enhanced metadata columns (7-18) with enhanced styling
        if enhanced:
            items.append(EnhancedTableItem(self.format_llm_value(enhanced.subgenre, "subgenre"), "enhanced"))  # 7: Subgenre
            items.append(EnhancedTableItem(self.format_llm_value(enhanced.mood, "mood"), "enhanced"))  # 8: Mood
            items.append(EnhancedTableItem(self.format_llm_value(enhanced.era, "era"), "enhanced"))  # 9: Era
            items.append(EnhancedTableItem(self.format_llm_value(enhanced.language, "language"), "enhanced"))  # 10: Language
            items.append(EnhancedTableItem(self.format_llm_value(enhanced.danceability, "percentage"), "enhanced"))  # 11: Danceability
            items.append(EnhancedTableItem(self.format_llm_value(enhanced.time_of_day, "time_of_day"), "enhanced"))  # 12: Time of Day
            items.append(EnhancedTableItem(self.format_llm_value(enhanced.activity, "activity"), "enhanced"))  # 13: Activity
            items.append(EnhancedTableItem(self.format_llm_value(enhanced.season, "season"), "enhanced"))  # 14: Season
            items.append(EnhancedTableItem(self.format_llm_value(enhanced.mixing_friendliness, "percentage"), "enhanced"))  # 15: Mix Friendly
            items.append(EnhancedTableItem(self.format_llm_value(enhanced.crowd_appeal, "percentage"), "enhanced"))  # 16: Crowd Appeal
            items.append(EnhancedTableItem(self.format_llm_value(enhanced.production_quality, "percentage"), "enhanced"))  # 17: Production
            items.append(EnhancedTableItem(self.format_llm_value(enhanced.confidence_score, "percentage"), "enhanced"))  # 18: Confidence
        else:
            # No enhanced metadata available - fill with placeholder
            for i in range(12):  # 12 LLM columns
                items.append(EnhancedTableItem("-", item_type))
        
        # Apply additional styling for unavailable tracks
        if not is_available:
            # Add indicator to title
            items[0].setText(f"⚠ {track.title}")
            items[0].setToolTip("File not available (external drive not mounted?)")
        
        # Enhanced visual indicators are handled by EnhancedTableItem styling
        # No need for manual color application here
        
        # Add all items to table and set tooltips
        for col, item in enumerate(items):
            self.track_table.setItem(row, col, item)
            # Store track ID in the first column for reliable mapping
            if col == 0:  # Title column
                item.setData(Qt.ItemDataRole.UserRole, track.id)
            # Add helpful tooltips for LLM columns
            if col >= 7 and hasattr(self, 'column_tooltips'):
                tooltip = self.column_tooltips.get(col, "")
                if tooltip:
                    item.setToolTip(f"{tooltip}\nValue: {item.text()}")
    
    def refresh_track_llm_data(self, track_id: str):
        """Refresh LLM data for a specific track in the table"""
        # Find the row with the matching track ID
        for row in range(self.track_table.rowCount()):
            title_item = self.track_table.item(row, 0)
            if title_item:
                stored_track_id = title_item.data(Qt.ItemDataRole.UserRole)
                if stored_track_id == track_id:
                    # Find the track in facade
                    tracks = self.facade.get_tracks()
                    track = None
                    for t in tracks:
                        if t.id == track_id:
                            track = t
                            break
                    
                    if track:
                        # Update only the LLM columns (7-18)
                        enhanced = self.get_enhanced_metadata_for_track(track)
                        if enhanced:
                            llm_values = [
                                self.format_llm_value(enhanced.subgenre, "subgenre"),  # 7
                                self.format_llm_value(enhanced.mood, "mood"),  # 8
                                self.format_llm_value(enhanced.era, "era"),  # 9
                                self.format_llm_value(enhanced.language, "language"),  # 10
                                self.format_llm_value(enhanced.danceability, "percentage"),  # 11
                                self.format_llm_value(enhanced.time_of_day, "time_of_day"),  # 12
                                self.format_llm_value(enhanced.activity, "activity"),  # 13
                                self.format_llm_value(enhanced.season, "season"),  # 14
                                self.format_llm_value(enhanced.mixing_friendliness, "percentage"),  # 15
                                self.format_llm_value(enhanced.crowd_appeal, "percentage"),  # 16
                                self.format_llm_value(enhanced.production_quality, "percentage"),  # 17
                                self.format_llm_value(enhanced.confidence_score, "percentage"),  # 18
                            ]
                            
                            # Update LLM columns
                            for i, value in enumerate(llm_values):
                                col = 7 + i
                                item = QTableWidgetItem(value)
                                # Add visual indicator for enhanced data
                                if enhanced.confidence_score > 0:
                                    item.setData(Qt.ItemDataRole.ForegroundRole, BlueLibraryTheme.ACCENT_PRIMARY)
                                # Add tooltip
                                if hasattr(self, 'column_tooltips'):
                                    tooltip = self.column_tooltips.get(col, "")
                                    if tooltip:
                                        item.setToolTip(f"{tooltip}\nValue: {value}")
                                self.track_table.setItem(row, col, item)
                    break
        
        # Update the table display
        self.track_table.viewport().update()
    
    def refresh_all_llm_data(self):
        """Refresh LLM data for all tracks in the table"""
        # Handle optimized track view
        if self.use_optimized_ui and hasattr(self.track_table, 'setTracks'):
            print("🔄 Refreshing LLM data in optimized track view by reloading tracks")
            tracks = self.facade.get_tracks()
            self.track_table.setTracks(tracks)
            return
        
        # Standard table implementation
        tracks = self.facade.get_tracks()
        for track in tracks:
            self.refresh_track_llm_data(track.id)
    
    def on_analysis_finished(self):
        self.progress_bar.setVisible(False)
        self.update_button_states()
    
    def on_track_selected(self):
        selected_tracks = self.get_selected_tracks()
        selected_count = len(selected_tracks)
        
        if selected_count == 1:
            # Single selection - set as current track for playback
            track = selected_tracks[0]
            self.facade.set_current_track(track.id)
            
            # Check track availability
            is_available = getattr(track, 'is_available', True)
            
            if is_available:
                self.current_track_label.setText(
                    f"{track.title}\n{track.artist}"
                )
                self.play_btn.setEnabled(True)
                self.stop_btn.setEnabled(True)
                # Set current audio file for playback
                self.current_audio_file = track.filepath
            else:
                self.current_track_label.setText(
                    f"⚠ {track.title}\n{track.artist}\n(File not available)"
                )
                self.play_btn.setEnabled(False)
                self.stop_btn.setEnabled(False)
                self.current_audio_file = None
                
        elif selected_count > 1:
            # Multiple selection - show selection info
            self.current_track_label.setText(
                f"Multiple tracks selected\n({selected_count} tracks)"
            )
            self.play_btn.setEnabled(False)
            self.stop_btn.setEnabled(False)
            self.current_audio_file = None
            
        else:
            # No selection
            self.current_track_label.setText("No track selected")
            self.play_btn.setEnabled(False)
            self.stop_btn.setEnabled(False)
            self.current_audio_file = None
        
        # Always update button states when selection changes
        self.update_llm_button_state()
    
    def play_pause_audio(self):
        """Toggle play/pause for the selected audio track"""
        if not self.current_audio_file:
            return
        
        if self.is_playing:
            # Pause audio
            self.media_player.pause()
            self.play_btn.setText("▶")
            self.is_playing = False
        else:
            # Play audio
            if self.media_player.source() != QUrl.fromLocalFile(self.current_audio_file):
                # Load new file
                self.media_player.setSource(QUrl.fromLocalFile(self.current_audio_file))
            
            self.media_player.play()
            self.play_btn.setText("⏸")
            self.is_playing = True
    
    def stop_audio(self):
        """Stop audio playback"""
        self.media_player.stop()
        self.play_btn.setText("▶")
        self.is_playing = False
    
    def set_volume(self, value):
        """Set audio volume (0-100)"""
        self.audio_output.setVolume(value / 100.0)
    
    def on_mode_changed(self, mode_text: str):
        self.facade.set_mix_mode(mode_text)
        self.update_weight_display()
    
    def update_weight_display(self):
        # Update sliders to reflect current engine weights
        weights = self.facade.get_algorithm_weights()
        for param, weight in weights.items():
            if param in self.weight_sliders:
                slider, label = self.weight_sliders[param]
                value = int(weight * 100)
                # Block signals during programmatic updates to prevent circular triggers
                slider.blockSignals(True)
                slider.setValue(value)
                slider.blockSignals(False)
                label.setText(f"{value}%")
    
    def on_weight_changed(self):
        # Update engine weights from sliders
        total = sum(slider.value() for slider, _ in self.weight_sliders.values())
        
        if total > 0:
            new_weights = {}
            for param, (slider, _) in self.weight_sliders.items():
                new_weights[param] = slider.value() / total
            self.facade.set_algorithm_weights(new_weights)
    
    def generate_playlist(self):
        """Open the enhanced playlist generator dialog"""
        try:
            from .playlist_generator_dialog import PlaylistGeneratorDialog, CompactPlaylistGenerator
            
            # Check screen size for appropriate dialog
            screen = QApplication.primaryScreen()
            screen_size = screen.size()
            
            if screen_size.width() < 400:  # Very small screen
                dialog = CompactPlaylistGenerator(self.facade, self)
            else:
                dialog = PlaylistGeneratorDialog(self.facade, self)
            
            # Connect to handle created playlist
            dialog.playlist_created.connect(self.on_playlist_created)
            
            # Show dialog
            dialog.exec()
            
        except ImportError:
            # Fallback to original implementation
            self.generate_playlist_classic()
    
    def generate_playlist_classic(self):
        """Classic playlist generation (fallback)"""
        tracks = self.facade.get_tracks()
        if not tracks:
            self.status_bar.show_error("No tracks available to generate playlist")
            return
        
        # Get settings
        curve = self.curve_combo.currentText().lower()
        length = self.length_slider.value()
        
        self.status_bar.show_progress(f"Generating {length}-track playlist with {curve} curve...")
        
        # Generate playlist using facade
        current_track = self.facade.get_current_track()
        start_track_id = current_track.id if current_track else None
        
        playlist = self.facade.generate_playlist(length, curve, start_track_id)
        
        if playlist:
            self.status_bar.show_success(f"Generated {len(playlist)}-track playlist successfully!")
            # Show playlist
            self.show_playlist(playlist)
        else:
            self.status_bar.show_error("Failed to generate playlist")
    
    def on_playlist_created(self, playlist: List[Track]):
        """Handle playlist creation from dialog"""
        self.current_playlist = playlist
        self.status_bar.show_success(f"Generated {len(playlist)}-track playlist successfully!")
        
        # Optionally show the playlist in the main UI
        # You could update a playlist view or enable export options
        
        # Ask if user wants to see the playlist
        reply = QMessageBox.question(
            self, "Playlist Generated",
            f"Successfully generated {len(playlist)} track playlist.\n\nWould you like to view it?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.show_playlist(playlist)
    
    def quick_generate_playlist(self, curve: str, length: int):
        """Quick playlist generation with preset parameters"""
        tracks = self.facade.get_tracks()
        if not tracks:
            self.status_bar.show_error("No tracks available to generate playlist")
            return
        
        self.status_bar.show_progress(f"Generating {length}-track playlist...")
        
        # Generate playlist with correct method signature
        current_track = self.facade.get_current_track()
        start_track_id = None
        if current_track and hasattr(current_track, 'id'):
            start_track_id = current_track.id
        
        playlist = self.facade.generate_playlist(
            target_length=length,
            progression_curve=curve,
            start_track_id=start_track_id
        )
        
        if playlist:
            self.current_playlist = playlist
            self.status_bar.show_success(f"Generated {len(playlist)}-track playlist!")
            
            # Show export option
            reply = QMessageBox.question(
                self, "Playlist Generated",
                f"Successfully generated {len(playlist)} track playlist.\n\n"
                "Would you like to export it?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.export_playlist_m3u()
        else:
            self.status_bar.show_error("Failed to generate playlist")
    
    def show_playlist(self, playlist: List[Track]):
        # Store current playlist for export functionality
        self.current_playlist = playlist
        
        message = "Generated Playlist:\n\n"
        for i, track in enumerate(playlist, 1):
            message += f"{i}. {track.title} - {track.artist} ({track.key}, {track.bpm} BPM)\n"
        
        message += f"\n\nPlaylist ready! You can now export it via:\nFile → Export Playlist → M3U Format"
        
        QMessageBox.information(self, "Generated Playlist", message)
    
    def show_llm_settings(self):
        """Show LLM configuration dialog"""
        try:
            from .llm_settings_dialog import LLMSettingsDialog
            dialog = LLMSettingsDialog(self.facade, self)
            # Connect signal to update button state when settings are saved
            dialog.llm_settings_saved.connect(self.update_llm_button_state)
            dialog.exec()
        except ImportError:
            QMessageBox.information(
                self, "LLM Settings", 
                "LLM integration is not available."
            )
        except Exception as e:
            QMessageBox.warning(
                self, "Error", 
                f"Failed to open LLM settings: {e}"
            )
    
    def show_about(self):
        QMessageBox.about(
            self, "About BlueLibrary",
            "BlueLibrary - Advanced Harmonic Mixer\n\n"
            "An intelligent DJ mixing tool that goes beyond\n"
            "traditional Camelot wheel mixing.\n\n"
            "Features AI-powered LLM integration for\n"
            "intelligent music analysis and mixing.\n\n"
            "Version 1.0.0"
        )
    
    # View menu methods
    def toggle_column(self, column_index: int, visible: bool):
        """Toggle column visibility in track table"""
        if visible:
            self.track_table.showColumn(column_index)
        else:
            self.track_table.hideColumn(column_index)
    
    def zoom_in(self):
        """Increase font size in track table"""
        font = self.track_table.font()
        current_size = font.pointSize()
        if current_size < 20:  # Max zoom
            font.setPointSize(current_size + 1)
            self.track_table.setFont(font)
    
    def zoom_out(self):
        """Decrease font size in track table"""
        font = self.track_table.font()
        current_size = font.pointSize()
        if current_size > 8:  # Min zoom
            font.setPointSize(current_size - 1)
            self.track_table.setFont(font)
    
    def reset_zoom(self):
        """Reset font size to default"""
        font = self.track_table.font()
        font.setPointSize(13)  # Default size
        self.track_table.setFont(font)
    
    def refresh_view(self):
        """Refresh the track view and reload data"""
        try:
            self.status_bar.show_message("Refreshing view...")
            self.facade.refresh_tracks()
            self.populate_table()
            self.status_bar.show_success("View refreshed")
        except Exception as e:
            self.status_bar.show_error(f"Error refreshing view: {str(e)}")
    
    def populate_table(self):
        """Populate the track table with current tracks and enhanced metadata"""
        try:
            # Get all tracks from facade
            tracks = self.facade.get_tracks()
            print(f"📊 Populating table with {len(tracks)} tracks")
            
            # Check if using optimized track view
            if self.use_optimized_ui and hasattr(self.track_table, 'setTracks'):
                # Use optimized track view
                print("📊 Using optimized track view for population")
                self.track_table.setTracks(tracks)
                self.update_button_states()
                self.status_bar.show_success(f"Loaded {len(tracks)} tracks into optimized view")
                return
            
            # Standard table widget implementation
            # Clear existing table
            self.track_table.setRowCount(0)
            
            if not tracks:
                self.status_bar.show_info("No tracks to display")
                return
            
            # Set table size
            self.track_table.setRowCount(len(tracks))
            
            # Populate each row
            for row, track in enumerate(tracks):
                # Basic track information
                self.track_table.setItem(row, 0, QTableWidgetItem(getattr(track, 'title', 'Unknown')))
                self.track_table.setItem(row, 1, QTableWidgetItem(getattr(track, 'artist', 'Unknown')))
                self.track_table.setItem(row, 2, QTableWidgetItem(str(getattr(track, 'key', 'N/A'))))
                self.track_table.setItem(row, 3, QTableWidgetItem(str(getattr(track, 'bpm', 0))))
                self.track_table.setItem(row, 4, QTableWidgetItem(f"{getattr(track, 'energy', 0):.1f}"))
                self.track_table.setItem(row, 5, QTableWidgetItem(str(getattr(track, 'emotion', 'N/A'))))
                self.track_table.setItem(row, 6, QTableWidgetItem(getattr(track, 'genre', 'Unknown')))
                self.track_table.setItem(row, 7, QTableWidgetItem(getattr(track, 'album', 'Unknown')))
                self.track_table.setItem(row, 8, QTableWidgetItem(str(getattr(track, 'year', 'N/A'))))
                self.track_table.setItem(row, 9, QTableWidgetItem(str(getattr(track, 'duration', 'N/A'))))
                
                # Compatibility (empty for now, can be calculated)
                self.track_table.setItem(row, 10, QTableWidgetItem('N/A'))
                
                # Usage statistics
                self.track_table.setItem(row, 11, QTableWidgetItem(str(getattr(track, 'last_played', 'Never'))))
                self.track_table.setItem(row, 12, QTableWidgetItem(str(getattr(track, 'play_count', 0))))
                self.track_table.setItem(row, 13, QTableWidgetItem(str(getattr(track, 'rating', 'N/A'))))
                
                # File status
                import os
                filepath = getattr(track, 'filepath', '') or getattr(track, 'file_path', '')
                status = "Available" if (filepath and os.path.exists(filepath)) else "Missing"
                self.track_table.setItem(row, 14, QTableWidgetItem(status))
                
                # Enhanced metadata status
                enhanced_metadata = self.facade.get_enhanced_metadata(track.id)
                if enhanced_metadata and enhanced_metadata.confidence_score > 0.1:
                    enhanced_text = f"✅ Enhanced ({enhanced_metadata.confidence_score:.2f})"
                    # Enhanced data columns
                    self.track_table.setItem(row, 16, QTableWidgetItem(enhanced_metadata.mood or 'N/A'))
                    self.track_table.setItem(row, 17, QTableWidgetItem(f"{enhanced_metadata.danceability:.2f}" if enhanced_metadata.danceability else 'N/A'))
                    self.track_table.setItem(row, 18, QTableWidgetItem(f"{enhanced_metadata.valence:.2f}" if enhanced_metadata.valence else 'N/A'))
                else:
                    enhanced_text = "❌ Not Enhanced"
                    self.track_table.setItem(row, 16, QTableWidgetItem('N/A'))
                    self.track_table.setItem(row, 17, QTableWidgetItem('N/A'))
                    self.track_table.setItem(row, 18, QTableWidgetItem('N/A'))
                
                self.track_table.setItem(row, 15, QTableWidgetItem(enhanced_text))
                
                # Store track reference for selection
                self.track_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, track)
            
            # Update button states and status
            self.update_button_states()
            self.status_bar.show_success(f"Loaded {len(tracks)} tracks into table")
            print(f"✅ Table populated successfully with {len(tracks)} tracks")
            
        except Exception as e:
            print(f"❌ Error populating table: {e}")
            self.status_bar.show_error(f"Error loading tracks: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def export_playlist_m3u(self):
        """Export current playlist to M3U format"""
        try:
            # Check if we have a current playlist
            if not hasattr(self, 'current_playlist') or not self.current_playlist:
                # Try to get tracks from selection or all tracks
                tracks = self.get_selected_tracks()
                if not tracks:
                    tracks = self.facade.get_tracks()
                    if not tracks:
                        self.status_bar.show_error("No tracks available to export")
                        return
                    
                    # Ask user if they want to export all tracks
                    reply = QMessageBox.question(
                        self, "Export All Tracks",
                        f"No playlist generated yet. Export all {len(tracks)} tracks as M3U playlist?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )
                    if reply != QMessageBox.StandardButton.Yes:
                        return
            else:
                tracks = self.current_playlist
            
            # Open file dialog to choose save location
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Playlist as M3U",
                "playlist.m3u",
                "M3U Playlist Files (*.m3u);;All Files (*)"
            )
            
            if not file_path:
                return  # User cancelled
            
            # Ensure .m3u extension
            if not file_path.lower().endswith('.m3u'):
                file_path += '.m3u'
            
            # Export using facade
            success = self.facade.export_playlist_with_plugin(
                "M3U Exporter",
                file_path,
                {
                    'playlist_name': os.path.basename(file_path).replace('.m3u', ''),
                    'serato_compatible': True
                }
            )
            
            if success:
                self.status_bar.show_success(f"Playlist exported to {os.path.basename(file_path)}")
                
                # Show confirmation with details
                QMessageBox.information(
                    self, "Export Successful",
                    f"Playlist exported successfully!\n\n"
                    f"File: {file_path}\n"
                    f"Tracks: {len(tracks)}\n"
                    f"Format: M3U (Serato DJ Pro compatible)\n\n"
                    f"You can now import this playlist into Serato DJ Pro:\n"
                    f"Files panel → Import → Import Playlist"
                )
            else:
                self.status_bar.show_error("Failed to export playlist")
                QMessageBox.warning(
                    self, "Export Failed",
                    "Failed to export playlist. Please check the file path and try again."
                )
                
        except Exception as e:
            self.status_bar.show_error(f"Export error: {str(e)}")
            QMessageBox.critical(
                self, "Export Error",
                f"An error occurred while exporting the playlist:\n\n{str(e)}"
            )
    
    def export_playlist_serato(self):
        """Export current playlist directly to Serato DJ Pro library"""
        try:
            # Get tracks to export
            tracks = getattr(self, 'current_playlist', None)
            if not tracks:
                # Try to get tracks from selection or all tracks
                tracks = self.get_selected_tracks()
                if not tracks:
                    tracks = self.facade.get_tracks()
                    if not tracks:
                        self.status_bar.show_error("No tracks available to export")
                        return
                    
                    # Ask user if they want to export all tracks
                    reply = QMessageBox.question(
                        self, "Export All Tracks to Serato",
                        f"No playlist generated yet. Export all {len(tracks)} tracks to Serato DJ Pro?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )
                    if reply != QMessageBox.StandardButton.Yes:
                        return
            
            # Check Serato status first
            serato_status = self.facade.get_serato_status()
            if not serato_status.get('plugin_available', False):
                QMessageBox.warning(
                    self, "Serato Not Available",
                    "Serato DJ Pro integration is not available.\n\n"
                    "Please ensure:\n"
                    "• Serato DJ Pro is installed\n"
                    "• pyserato library is installed\n"
                    "• Serato library is accessible"
                )
                return
            
            # Check if Serato is running
            if serato_status.get('serato_running', False):
                QMessageBox.warning(
                    self, "Serato DJ Running",
                    "Serato DJ Pro is currently running.\n\n"
                    "Please close Serato DJ Pro before exporting playlists.\n"
                    "This prevents database corruption."
                )
                return
            
            # Get playlist name from user
            from PyQt6.QtWidgets import QInputDialog
            playlist_name, ok = QInputDialog.getText(
                self, 
                "Export to Serato DJ Pro",
                "Enter playlist name for Serato DJ Pro:",
                text=f"BlueLibrary_Playlist_{len(tracks)}_tracks"
            )
            
            if not ok or not playlist_name.strip():
                return  # User cancelled or empty name
            
            playlist_name = playlist_name.strip()
            
            # Check for existing crate
            existing_crates = self.facade.list_serato_crates()
            if playlist_name in existing_crates:
                reply = QMessageBox.question(
                    self, "Overwrite Existing Crate",
                    f"A crate named '{playlist_name}' already exists in Serato DJ Pro.\n\n"
                    f"Do you want to overwrite it?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return
            
            # Show progress
            self.status_bar.show_progress(f"Exporting {len(tracks)} tracks to Serato DJ Pro...")
            
            # Export to Serato
            result = self.facade.export_playlist_to_serato(
                playlist_name=playlist_name,
                tracks=tracks,
                options={
                    'create_backup': True,
                    'overwrite_existing': True
                }
            )
            
            if result['success']:
                self.status_bar.show_success(f"Playlist exported to Serato DJ Pro!")
                
                # Show success dialog with details
                QMessageBox.information(
                    self, "Export Successful",
                    f"Playlist exported successfully to Serato DJ Pro!\n\n"
                    f"Crate Name: {playlist_name}\n"
                    f"Tracks: {result['tracks_exported']}\n"
                    f"Library: {result['library_path']}\n\n"
                    f"The playlist is now available in Serato DJ Pro.\n"
                    f"You can find it in the 'Crates' section."
                )
            else:
                self.status_bar.show_error(f"Serato export failed: {result['error']}")
                QMessageBox.warning(
                    self, "Export Failed",
                    f"Failed to export playlist to Serato DJ Pro:\n\n{result['error']}\n\n"
                    f"Please check:\n"
                    f"• Serato DJ Pro is not running\n"
                    f"• You have write access to Serato library\n"
                    f"• All track files exist and are accessible"
                )
                
        except Exception as e:
            self.status_bar.show_error(f"Serato export error: {str(e)}")
            QMessageBox.critical(
                self, "Serato Export Error",
                f"An error occurred while exporting to Serato DJ Pro:\n\n{str(e)}"
            )
    
    def load_settings(self):
        """Load saved settings from database"""
        # Load window geometry with better macOS defaults
        geometry = self.facade.load_window_geometry()
        if geometry:
            # Ensure window fits on screen with reasonable defaults
            width = max(1000, min(geometry.get('width', 1200), 1400))
            height = max(600, min(geometry.get('height', 700), 900))
            self.setGeometry(
                geometry.get('x', 100),
                geometry.get('y', 100),
                width,
                height
            )
        
        # Update weight display to reflect loaded weights
        self.update_weight_display()
        
        # Load last used mode
        last_mode = self.facade.get_mix_mode()
        index = self.mode_combo.findText(last_mode)
        if index >= 0:
            self.mode_combo.setCurrentIndex(index)
    
    def save_settings(self):
        """Save current settings to database"""
        # Save window geometry
        geometry = {
            'x': self.x(),
            'y': self.y(),
            'width': self.width(),
            'height': self.height()
        }
        self.facade.save_window_geometry(geometry)
    
    def enhance_all_tracks(self):
        """Enhance all tracks with LLM analysis"""
        self._enhance_tracks(all_tracks=True)
    
    def enhance_selected_track(self):
        """Enhance only the selected track(s) with LLM analysis"""
        selected_tracks = self.get_selected_tracks()
        if not selected_tracks:
            self.status_bar.show_error("No tracks selected")
            return
        
        # Show info about selection
        count = len(selected_tracks)
        if count == 1:
            self.status_bar.show_info(f"Enhancing 1 selected track", "ai")
        else:
            self.status_bar.show_info(f"Enhancing {count} selected tracks", "ai")
        
        self._enhance_tracks(all_tracks=False, selected_tracks=selected_tracks)
    
    def _enhance_tracks(self, all_tracks: bool = True, selected_tracks: list = None):
        """Common enhancement logic"""
        if not self.facade.is_llm_configured():
            # Get detailed configuration status
            if hasattr(self.facade.llm_config_manager, 'get_configuration_status'):
                status = self.facade.llm_config_manager.get_configuration_status()
                issues = status.get('issues', ['LLM not configured'])
                issue_text = '\n• '.join([''] + issues)
                
                QMessageBox.warning(
                    self, "LLM Not Configured",
                    f"LLM enhancement is not available:\n{issue_text}\n\n"
                    "Please configure LLM settings first.\n"
                    "Go to Settings → LLM Configuration"
                )
            else:
                QMessageBox.warning(
                    self, "LLM Not Configured",
                    "Please configure LLM settings first.\nGo to Settings → LLM Configuration"
                )
            return
        
        if all_tracks:
            tracks = self.facade.get_tracks()
            if not tracks:
                self.status_bar.show_error("No tracks loaded. Load your music library first.")
                return
        else:
            # Use provided selected tracks
            tracks = selected_tracks if selected_tracks else []
            if not tracks:
                self.status_bar.show_error("No tracks selected for enhancement.")
                return
        
        # Skip cost estimate dialog and proceed directly
        # Note: Cost estimate checking removed per user request
        
        # Start enhancement process
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_bar.show_progress(f"Enhancing {len(tracks)} track(s) with AI...")
        self.enhance_all_btn.setEnabled(False)
        self.enhance_selected_btn.setEnabled(False)
        self.enhance_all_btn.setText("🤖 Enhancing...")
        
        # Create enhancement thread
        self.enhancement_thread = EnhancementThread(self.facade, tracks)
        self.enhancement_thread.progress_updated.connect(self.on_enhancement_progress)
        self.enhancement_thread.enhancement_completed.connect(self.on_enhancement_completed)
        self.enhancement_thread.enhancement_failed.connect(self.on_enhancement_failed)
        self.enhancement_thread.start()
    
    def on_enhancement_progress(self, current: int, total: int):
        """Handle enhancement progress updates"""
        progress = int((current / total) * 100)
        self.progress_bar.setValue(progress)
        self.status_bar.show_progress(f"Enhancing tracks with AI... {current}/{total}")
    
    def on_enhancement_completed(self, enhanced_count: int):
        """Handle enhancement completion"""
        self.progress_bar.setVisible(False)
        self.enhance_all_btn.setEnabled(True)
        self.enhance_all_btn.setText("🤖 Enhance All Tracks")
        self.enhance_selected_btn.setEnabled(True)
        
        # Refresh the table to show new LLM data
        print(f"🔄 Refreshing LLM data after enhancement of {enhanced_count} tracks")
        self.refresh_all_llm_data()
        
        self.update_button_states()
        self.status_bar.show_success(f"Enhanced {enhanced_count} tracks successfully!")
        
        QMessageBox.information(
            self, "Enhancement Complete",
            f"Successfully enhanced {enhanced_count} tracks with AI!\n\n"
            f"Your tracks now have:\n"
            f"• Intelligent mood analysis\n"
            f"• Enhanced genre detection\n"
            f"• DJ mixing suggestions\n"
            f"• Improved compatibility scoring\n\n"
            f"Use 'LLM Intelligent Mixing' algorithm for best results."
        )
    
    def on_enhancement_failed(self, error_message: str):
        """Handle enhancement failure"""
        self.progress_bar.setVisible(False)
        self.enhance_all_btn.setEnabled(True)
        self.enhance_all_btn.setText("🤖 Enhance All Tracks")
        self.enhance_selected_btn.setEnabled(True)
        
        self.update_button_states()
        self.status_bar.show_error(f"Enhancement failed: {error_message}")
        
        QMessageBox.warning(
            self, "Enhancement Failed",
            f"Failed to enhance tracks with AI:\n{error_message}\n\n"
            f"Please check your LLM configuration and try again."
        )
    
    def update_button_states(self):
        """Update all button states based on current application state"""
        tracks = self.facade.get_tracks()
        has_tracks = len(tracks) > 0
        
        # Update Generate Playlist button
        self.generate_btn.setEnabled(has_tracks)
        generate_tooltip = "Generate an optimized playlist" if has_tracks else "Load tracks first to generate playlists"
        self.generate_btn.setToolTip(generate_tooltip)
        
        # Update LLM Enhancement button
        self.update_llm_button_state()
        
        # Update advanced buttons
        self.update_advanced_button_states()
        
        # Update status bar
        if has_tracks:
            self.status_bar.show_info(f"Loaded {len(tracks)} tracks", "music")
        else:
            self.status_bar.show_info("No tracks loaded", "folder")
        
        # Debug info
        print(f"Button States Updated: tracks={has_tracks}, generate_enabled={has_tracks}")
    
    def update_llm_button_state(self):
        """Update LLM enhancement button state and tooltip"""
        tracks = self.facade.get_tracks()
        has_tracks = len(tracks) > 0
        
        # Check LLM availability with better error handling
        llm_available = False
        llm_configured = False
        llm_error = None
        
        try:
            llm_available = self.facade.is_llm_available()
            llm_configured = self.facade.is_llm_configured()
        except Exception as e:
            llm_error = str(e)
            print(f"Error checking LLM status: {e}")
        
        selected_count = self.get_selected_track_count()
        
        # Determine if buttons should be enabled
        button_enabled = has_tracks and llm_available and llm_configured
        selected_button_enabled = button_enabled and selected_count > 0
        
        # Enable/disable both enhancement buttons
        self.enhance_all_btn.setEnabled(button_enabled)
        self.enhance_selected_btn.setEnabled(selected_button_enabled)
        
        # Update selected button text dynamically
        if selected_count == 0:
            self.enhance_selected_btn.setText("🎯 Enhance Selected")
        elif selected_count == 1:
            self.enhance_selected_btn.setText("🎯 Enhance Selected (1)")
        else:
            self.enhance_selected_btn.setText(f"🎯 Enhance Selected ({selected_count})")
        
        # Set appropriate tooltips
        if llm_error:
            tooltip = f"LLM integration error: {llm_error}"
        elif not llm_available:
            tooltip = "LLM integration not available (missing dependencies)"
        elif not has_tracks:
            tooltip = "Load your music library first to enhance tracks"
        elif not llm_configured:
            tooltip = "Configure LLM in Settings → LLM Configuration first"
        else:
            tooltip = "Enhance tracks with AI analysis for better mixing suggestions"
        
        # Dynamic tooltip for selected button
        if selected_count == 0:
            selected_tooltip = "Select one or more tracks to enhance with AI (Ctrl+Click for multiple, Shift+Click for range)"
        elif selected_count == 1:
            selected_tooltip = "Enhance the selected track with AI analysis"
        else:
            selected_tooltip = f"Enhance {selected_count} selected tracks with AI analysis"
        
        self.enhance_all_btn.setToolTip(tooltip)
        self.enhance_selected_btn.setToolTip(selected_tooltip if button_enabled else tooltip)
        
        # Update button states based on current conditions
    
    def update_advanced_button_states(self):
        """Update states of advanced feature buttons"""
        has_tracks = len(self.facade.get_tracks()) > 0
        
        # Update contextual generation button
        if hasattr(self, 'contextual_generate_btn'):
            self.contextual_generate_btn.setEnabled(has_tracks)
        
        # Update temporal generation button
        if hasattr(self, 'temporal_generate_btn'):
            self.temporal_generate_btn.setEnabled(has_tracks)
        
        # Update global optimization button
        if hasattr(self, 'global_optimize_btn'):
            self.global_optimize_btn.setEnabled(has_tracks)
    
    def on_policy_selected(self, policy_id: str):
        """Handle policy selection from quick selector"""
        print(f"Policy selected: {policy_id}")
        # You could apply the policy here or store it for playlist generation
    
    def test_selected_policy(self):
        """Test the currently selected policy"""
        if hasattr(self, 'policy_selector'):
            policy_id = self.policy_selector.get_selected_policy_id()
            if policy_id and hasattr(self, 'policy_manager'):
                try:
                    # Get a few tracks for testing
                    tracks = self.facade.get_tracks()[:5] if self.facade.get_tracks() else []
                    
                    if tracks:
                        # Apply policy to tracks
                        enhanced_metadata = {}
                        for track in tracks:
                            enhanced = self.get_enhanced_metadata_for_track(track)
                            if enhanced:
                                enhanced_metadata[track.id] = enhanced.__dict__
                        
                        results = self.policy_manager.apply_policy(policy_id, tracks, enhanced_metadata)
                        
                        # Show results
                        avg_score = sum(r.total_score for r in results) / len(results) if results else 0
                        critical_passed = all(r.satisfied_critical_rules for r in results) if results else False
                        
                        QMessageBox.information(
                            self, "Policy Test Results",
                            f"Policy: {policy_id}\\n"
                            f"Tracks tested: {len(results)}\\n"
                            f"Average score: {avg_score:.3f}\\n"
                            f"Critical rules passed: {'✅' if critical_passed else '❌'}"
                        )
                    else:
                        QMessageBox.warning(self, "No Tracks", "Load some tracks first to test the policy.")
                        
                except Exception as e:
                    QMessageBox.warning(self, "Policy Test Error", f"Error testing policy: {e}")
            else:
                QMessageBox.warning(self, "No Policy", "Please select a policy first.")
    
    def open_policy_editor(self):
        """Open the full policy editor dialog"""
        if hasattr(self, 'policy_manager'):
            from PyQt6.QtWidgets import QDialog
            
            dialog = QDialog(self)
            dialog.setWindowTitle("BlueLibrary Policy Editor - Block 6")
            dialog.setModal(True)
            dialog.resize(1200, 800)
            
            layout = QVBoxLayout(dialog)
            
            # Add header
            header_label = QLabel("🔧 Advanced Mixing Policies Configuration")
            header_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
            header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(header_label)
            
            # Add policy editor
            editor = PolicyEditorWidget(self.policy_manager)
            layout.addWidget(editor)
            
            # Add close button
            close_btn = ModernButton("Close", "secondary")
            close_btn.clicked.connect(dialog.accept)
            layout.addWidget(close_btn)
            
            dialog.exec()
            
            # Refresh policy selector after editing
            if hasattr(self, 'policy_selector'):
                self.policy_selector.refresh_policies()
        else:
            QMessageBox.warning(self, "Policies Not Available", "Policy system is not initialized.")
    
    def generate_contextual_playlist(self):
        """Generate playlist using contextual parameters (Block 3)"""
        tracks = self.facade.get_tracks()
        if not tracks:
            QMessageBox.warning(self, "No Tracks", "Load some tracks first.")
            return
        
        try:
            from ..analysis.contextual_playlist_generator import ContextualPlaylistGenerator, PlaylistGenerationRequest
            from ..core.harmonic_engine import HarmonicMixingEngine
            
            # Get contextual parameters
            time_of_day = self.time_combo.currentText() if self.time_combo.currentText() != "any" else None
            activity = self.activity_combo.currentText() if self.activity_combo.currentText() != "any" else None
            season = self.season_combo.currentText() if self.season_combo.currentText() != "any" else None
            
            # Get enhanced metadata
            enhanced_metadata = {}
            for track in tracks:
                enhanced = self.get_enhanced_metadata_for_track(track)
                if enhanced:
                    enhanced_metadata[track.id] = enhanced.__dict__
            
            # Create generator
            harmonic_engine = HarmonicMixingEngine()
            generator = ContextualPlaylistGenerator(harmonic_engine)
            
            # Create request
            request = PlaylistGenerationRequest(
                tracks=tracks,
                enhanced_metadata=enhanced_metadata,
                target_length=self.length_slider.value(),
                time_of_day=time_of_day,
                activity=activity,
                season=season
            )
            
            # Generate playlist
            result = generator.generate_contextual_playlist(request)
            
            # Show results
            self.show_playlist_results("Contextual Playlist", result.playlist, {
                "Score": f"{result.total_score:.3f}",
                "Curve": result.contextual_curve.name,
                "Time": time_of_day or "Any",
                "Activity": activity or "Any",
                "Season": season or "Any"
            })
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate contextual playlist: {e}")
    
    def generate_temporal_sequence(self):
        """Generate playlist using temporal/linguistic sequencing (Block 4)"""
        tracks = self.facade.get_tracks()
        if not tracks:
            QMessageBox.warning(self, "No Tracks", "Load some tracks first.")
            return
        
        try:
            from ..analysis.temporal_linguistic_sequencer import TemporalLinguisticSequencer, TemporalFlow, LinguisticFlow
            
            # Get parameters
            temporal_flow_name = self.temporal_flow_combo.currentText()
            linguistic_flow_name = self.linguistic_flow_combo.currentText()
            
            # Map to enums
            temporal_flow_map = {
                "none": None,
                "chronological": TemporalFlow.CHRONOLOGICAL,
                "reverse_chronological": TemporalFlow.REVERSE_CHRONOLOGICAL,
                "era_journey": TemporalFlow.ERA_JOURNEY
            }
            
            linguistic_flow_map = {
                "none": None,
                "monolingual": LinguisticFlow.MONOLINGUAL,
                "bilingual_bridge": LinguisticFlow.BILINGUAL_BRIDGE,
                "multilingual_journey": LinguisticFlow.MULTILINGUAL_JOURNEY
            }
            
            temporal_flow = temporal_flow_map.get(temporal_flow_name)
            linguistic_flow = linguistic_flow_map.get(linguistic_flow_name)
            
            # Get enhanced metadata
            enhanced_metadata = {}
            for track in tracks:
                enhanced = self.get_enhanced_metadata_for_track(track)
                if enhanced:
                    enhanced_metadata[track.id] = enhanced.__dict__
            
            # Create sequencer
            sequencer = TemporalLinguisticSequencer()
            
            # Generate sequence
            if temporal_flow and linguistic_flow:
                result = sequencer.create_combined_sequence(
                    tracks, enhanced_metadata, temporal_flow, linguistic_flow,
                    target_length=self.length_slider.value()
                )
            elif temporal_flow:
                result = sequencer.create_temporal_sequence(
                    tracks, enhanced_metadata, temporal_flow,
                    target_length=self.length_slider.value()
                )
            elif linguistic_flow:
                result = sequencer.create_linguistic_sequence(
                    tracks, enhanced_metadata, linguistic_flow,
                    target_length=self.length_slider.value()
                )
            else:
                QMessageBox.warning(self, "No Selection", "Please select a temporal or linguistic flow.")
                return
            
            # Show results
            info = {
                "Narrative Score": f"{result.narrative_score:.3f}",
                "Temporal Flow": temporal_flow_name if temporal_flow else "None",
                "Linguistic Flow": linguistic_flow_name if linguistic_flow else "None"
            }
            
            if hasattr(result, 'era_progression'):
                info["Era Progression"] = " → ".join(result.era_progression)
            if hasattr(result, 'language_progression'):
                info["Language Flow"] = " → ".join(result.language_progression)
            
            self.show_playlist_results("Temporal/Linguistic Sequence", result.tracks, info)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate temporal sequence: {e}")
    
    def generate_optimized_playlist(self):
        """Generate playlist using global optimization (Block 5)"""
        tracks = self.facade.get_tracks()
        if not tracks:
            QMessageBox.warning(self, "No Tracks", "Load some tracks first.")
            return
        
        try:
            from ..analysis.global_optimizer import GlobalPlaylistOptimizer, OptimizationObjective
            
            # Get parameters
            objective_name = self.optimization_combo.currentText()
            max_alternatives = self.alternatives_slider.value()
            
            # Map to enum
            objective_map = {
                "balanced": OptimizationObjective.BALANCED,
                "compatibility": OptimizationObjective.COMPATIBILITY,
                "energy_flow": OptimizationObjective.ENERGY_FLOW,
                "cultural_journey": OptimizationObjective.CULTURAL_JOURNEY,
                "narrative": OptimizationObjective.NARRATIVE
            }
            
            objective = objective_map.get(objective_name, OptimizationObjective.BALANCED)
            
            # Get enhanced metadata
            enhanced_metadata = {}
            for track in tracks:
                enhanced = self.get_enhanced_metadata_for_track(track)
                if enhanced:
                    enhanced_metadata[track.id] = enhanced.__dict__
            
            # Create optimizer
            optimizer = GlobalPlaylistOptimizer()
            
            # Generate optimized playlist
            result = optimizer.optimize_playlist(
                tracks=tracks,
                enhanced_metadata=enhanced_metadata,
                target_length=self.length_slider.value(),
                objective=objective,
                max_alternatives=max_alternatives
            )
            
            # Show results
            info = {
                "Total Score": f"{result.total_score:.3f}",
                "Objective": objective_name.title(),
                "Nodes Explored": str(result.nodes_explored),
                "Alternatives": str(max_alternatives)
            }
            
            if hasattr(result, 'constraint_violations'):
                info["Violations"] = str(len(result.constraint_violations))
            
            self.show_playlist_results("Globally Optimized Playlist", result.playlist, info)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate optimized playlist: {e}")
    
    def show_playlist_results(self, title: str, playlist: list, info: dict):
        """Show playlist generation results in a dialog"""
        from PyQt6.QtWidgets import QDialog, QTextEdit
        
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setModal(True)
        dialog.resize(600, 400)
        
        layout = QVBoxLayout(dialog)
        
        # Info section
        info_text = "\\n".join([f"{key}: {value}" for key, value in info.items()])
        info_label = QLabel(f"📊 **Results Summary**\\n{info_text}")
        info_label.setStyleSheet("font-weight: bold; padding: 10px; background-color: #2d3748; border-radius: 5px;")
        layout.addWidget(info_label)
        
        # Playlist section
        layout.addWidget(QLabel("🎵 **Generated Playlist:**"))
        
        playlist_text = QTextEdit()
        playlist_text.setReadOnly(True)
        
        playlist_content = ""
        for i, track in enumerate(playlist, 1):
            playlist_content += f"{i:2d}. {track.artist} - {track.title}\\n"
            if hasattr(track, 'key') and track.key:
                playlist_content += f"     Key: {track.key}"
            if hasattr(track, 'bpm') and track.bpm:
                playlist_content += f"  BPM: {track.bpm:.0f}"
            if hasattr(track, 'energy') and track.energy:
                playlist_content += f"  Energy: {track.energy:.1f}"
            playlist_content += "\\n\\n"
        
        playlist_text.setPlainText(playlist_content)
        layout.addWidget(playlist_text)
        
        # Close button
        close_btn = ModernButton("Close", "secondary")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec()
    
    def setup_toolbar_connections(self):
        """Setup connections for the compact toolbar"""
        # Connect toolbar signals to main window methods
        self.compact_toolbar.load_folder.connect(self.load_music_folder)
        self.compact_toolbar.clear_library.connect(self.clear_library)
        self.compact_toolbar.generate_playlist.connect(self.generate_playlist)
        self.compact_toolbar.enhance_tracks.connect(self.enhance_all_tracks)
        self.compact_toolbar.play_pause.connect(self.play_pause_audio)
        self.compact_toolbar.stop.connect(self.stop_audio)
        self.compact_toolbar.toggle_controls.connect(self.toggle_controls_panel)
    
    def setup_quick_action_connections(self):
        """Setup connections for the quick action panel"""
        # Connect quick action signals to main window methods
        self.quick_action_panel.analyze_folder.connect(self.analyze_folder)
        self.quick_action_panel.export_playlist.connect(self.export_playlist)
        self.quick_action_panel.settings.connect(self.show_settings)
        self.quick_action_panel.zoom_in.connect(self.zoom_in)
        self.quick_action_panel.zoom_out.connect(self.zoom_out)
        self.quick_action_panel.reset_zoom.connect(self.reset_zoom)
    
    def setup_tabbed_panel_connections(self):
        """Setup connections for the tabbed control panel"""
        # Get tabs
        mixing_tab = self.tabbed_control_panel.get_mixing_tab()
        advanced_tab = self.tabbed_control_panel.get_advanced_tab()
        player_tab = self.tabbed_control_panel.get_player_tab()
        
        # Connect mixing tab signals
        mixing_tab.mode_changed.connect(self.on_mode_changed)
        mixing_tab.weight_changed.connect(self.on_weight_changed)
        mixing_tab.generate_playlist.connect(self.generate_playlist)
        
        # Connect advanced tab signals
        advanced_tab.contextual_generate.connect(self.generate_contextual_playlist)
        advanced_tab.temporal_generate.connect(self.generate_temporal_sequence)
        advanced_tab.optimization_generate.connect(self.generate_optimized_playlist)
        
        # Connect player tab signals
        player_tab.play_pause.connect(self.play_pause_audio)
        player_tab.stop.connect(self.stop_audio)
        player_tab.volume_changed.connect(self.set_volume)
        
        # Keep references to tabs for easy access
        self.mixing_tab = mixing_tab
        self.advanced_tab = advanced_tab
        self.player_tab = player_tab
    
    def toggle_controls_panel(self):
        """Toggle visibility of the controls panel"""
        self.controls_visible = not self.controls_visible
        self.tabbed_control_panel.setVisible(self.controls_visible)
        self.compact_toolbar.set_controls_visible(self.controls_visible)
        
        # Update splitter proportions when hiding/showing controls
        if self.controls_visible:
            # Show controls: 82% table, 18% controls
            self.update_splitter_proportions([900, 200])
            status = "Controls visible"
        else:
            # Hide controls: 100% table, 0% controls
            self.update_splitter_proportions([1100, 0])
            status = "Controls hidden - More space for tracks"
        
        self.compact_toolbar.set_status(status)
    
    def update_splitter_proportions(self, sizes):
        """Update splitter proportions with animation-like effect"""
        # Find the splitter
        splitter = None
        for child in self.centralWidget().findChildren(QSplitter):
            if child.count() == 2:  # Table and controls
                splitter = child
                break
        
        if splitter:
            # Update stretch factors
            if sizes[1] == 0:  # Controls hidden
                splitter.setStretchFactor(0, 1)  # Table gets all space
                splitter.setStretchFactor(1, 0)  # Controls get no space
            else:  # Controls visible
                splitter.setStretchFactor(0, 6)  # Table gets 6/7 of space
                splitter.setStretchFactor(1, 1)  # Controls get 1/7 of space
            
            # Apply new sizes
            splitter.setSizes(sizes)
            
            # Force update
            splitter.update()
            QApplication.processEvents()
    
    def on_weight_changed(self, param: str, value: float):
        """Handle weight changes from tabbed panel"""
        if param == "key":
            self.facade.set_weight("key", value)
        elif param == "bpm":
            self.facade.set_weight("bpm", value)
        elif param == "energy":
            self.facade.set_weight("energy", value)
        elif param == "emotional":
            self.facade.set_weight("emotional", value)
    
    def analyze_folder(self):
        """Analyze current music folder"""
        if hasattr(self, 'folder_path') and self.folder_path:
            self.load_music_folder(self.folder_path)
        else:
            self.load_music_folder()
    
    def export_playlist(self):
        """Export current playlist"""
        # This would open an export dialog
        self.compact_toolbar.set_status("Export functionality coming soon...")
    
    def show_settings(self):
        """Show settings dialog"""
        # This would open a settings dialog
        self.compact_toolbar.set_status("Settings dialog coming soon...")
    
    def update_button_states(self):
        """Update button states based on current context"""
        has_tracks = len(self.facade.get_tracks()) > 0
        has_selected = self.get_selected_track_count() > 0
        
        # Update toolbar buttons
        self.compact_toolbar.set_generate_enabled(has_tracks)
        self.compact_toolbar.set_enhance_enabled(has_tracks)
        self.compact_toolbar.set_play_enabled(has_selected)
        
        # Update quick action buttons
        self.quick_action_panel.set_analyze_enabled(True)
        self.quick_action_panel.set_export_enabled(has_tracks)
        
        # Update tabbed panel buttons
        if hasattr(self, 'mixing_tab') and self.mixing_tab:
            self.mixing_tab.set_generate_enabled(has_tracks)
        
        if hasattr(self, 'advanced_tab') and self.advanced_tab:
            self.advanced_tab.set_buttons_enabled(has_tracks)
        
        if hasattr(self, 'player_tab') and self.player_tab:
            self.player_tab.set_play_enabled(has_selected)
    
    def update_progress(self, current: int, total: int):
        """Update progress in all components"""
        # Update compact toolbar progress
        self.compact_toolbar.update_progress(current, total)
        
        # Update legacy progress bar
        if hasattr(self, 'progress_bar'):
            self.progress_bar.setMaximum(total)
            self.progress_bar.setValue(current)
        
        # Throttle progress updates to avoid UI lag
        import time
        current_time = time.time()
        if current_time - self._last_progress_update > 0.1:  # Update every 100ms max
            self._last_progress_update = current_time
            QApplication.processEvents()
    
    def initialize_tabbed_references(self):
        """Initialize references to tabbed components for backward compatibility"""
        # Get references to tabs
        if hasattr(self, 'tabbed_control_panel') and self.tabbed_control_panel:
            mixing_tab = self.tabbed_control_panel.get_mixing_tab()
            advanced_tab = self.tabbed_control_panel.get_advanced_tab()
            player_tab = self.tabbed_control_panel.get_player_tab()
            
            # Set up references to maintain backward compatibility
            self.mode_combo = mixing_tab.mode_combo
            self.weight_sliders = {
                'key': (mixing_tab.key_slider, mixing_tab.key_label),
                'bpm': (mixing_tab.bpm_slider, mixing_tab.bpm_label),
                'energy': (mixing_tab.energy_slider, mixing_tab.energy_label),
                'emotional': (mixing_tab.emotional_slider, mixing_tab.emotional_label)
            }
            self.generate_btn = mixing_tab.generate_btn
            
            # Advanced tab references
            self.time_combo = advanced_tab.time_combo
            self.activity_combo = advanced_tab.activity_combo
            self.season_combo = advanced_tab.season_combo
            self.contextual_generate_btn = advanced_tab.contextual_generate_btn
            self.temporal_flow_combo = advanced_tab.temporal_flow_combo
            self.linguistic_flow_combo = advanced_tab.linguistic_flow_combo
            self.temporal_generate_btn = advanced_tab.temporal_generate_btn
            self.optimization_combo = advanced_tab.optimization_combo
            self.alternatives_slider = advanced_tab.alternatives_slider
            self.alternatives_label = advanced_tab.alternatives_label
            self.global_optimize_btn = advanced_tab.global_optimize_btn
            
            # Player tab references
            self.current_track_label = player_tab.current_track_label
            self.play_btn = player_tab.play_btn
            self.stop_btn = player_tab.stop_btn
            self.volume_slider = player_tab.volume_slider
            
            # Create fake curve and length controls for compatibility
            self.curve_combo = None
            self.length_slider = None
            self.length_label = None
        else:
            # Fallback if tabbed panel is not available
            self.mode_combo = None
            self.weight_sliders = {}
            self.curve_combo = None
            self.length_slider = None
            self.length_label = None
            self.generate_btn = None
            self.current_track_label = None
            self.play_btn = None
            self.stop_btn = None
            self.volume_slider = None
    
    def closeEvent(self, event):
        """Save settings when closing the application"""
        self.save_settings()
        self.facade.close()
        event.accept()
