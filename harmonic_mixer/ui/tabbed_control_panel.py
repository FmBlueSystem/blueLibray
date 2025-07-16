"""
Tabbed Control Panel for BlueLibrary
Organizes controls into thematic tabs to maximize space for track files
"""

from PyQt6.QtWidgets import (
    QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
    QLabel, QComboBox, QSlider, QPushButton, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal
from .enhanced_theme import ModernBlueLibraryTheme as BlueLibraryTheme
from .enhanced_components import ModernButton, EnhancedSlider
from .policy_editor import PolicyQuickSelector


class MixingControlsTab(QWidget):
    """Tab for core mixing controls and algorithm settings"""
    
    # Signals for main window communication
    mode_changed = pyqtSignal(str)
    weight_changed = pyqtSignal(str, float)
    generate_playlist = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the mixing controls UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Algorithm Settings Group
        settings_group = QGroupBox("Algorithm Settings")
        settings_layout = QVBoxLayout()
        
        # Mixing mode selector
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Mixing Mode:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            "intelligent", "classic_camelot", "energy_flow", "emotional"
        ])
        self.mode_combo.setObjectName("modeCombo")
        self.mode_combo.currentTextChanged.connect(self.mode_changed.emit)
        mode_layout.addWidget(self.mode_combo)
        settings_layout.addLayout(mode_layout)
        
        # Weight controls (compact layout)
        weights_group = QGroupBox("Algorithm Weights")
        weights_layout = QVBoxLayout()
        
        # Key weight
        key_layout = QHBoxLayout()
        key_layout.addWidget(QLabel("Key:"))
        self.key_slider = EnhancedSlider(Qt.Orientation.Horizontal)
        self.key_slider.setRange(0, 100)
        self.key_slider.setValue(40)
        self.key_label = QLabel("40%")
        self.key_slider.valueChanged.connect(
            lambda v: [self.key_label.setText(f"{v}%"), self.weight_changed.emit("key", v/100)]
        )
        key_layout.addWidget(self.key_slider)
        key_layout.addWidget(self.key_label)
        weights_layout.addLayout(key_layout)
        
        # BPM weight
        bpm_layout = QHBoxLayout()
        bpm_layout.addWidget(QLabel("BPM:"))
        self.bpm_slider = EnhancedSlider(Qt.Orientation.Horizontal)
        self.bpm_slider.setRange(0, 100)
        self.bpm_slider.setValue(30)
        self.bpm_label = QLabel("30%")
        self.bpm_slider.valueChanged.connect(
            lambda v: [self.bpm_label.setText(f"{v}%"), self.weight_changed.emit("bpm", v/100)]
        )
        bpm_layout.addWidget(self.bpm_slider)
        bpm_layout.addWidget(self.bpm_label)
        weights_layout.addLayout(bpm_layout)
        
        # Energy weight
        energy_layout = QHBoxLayout()
        energy_layout.addWidget(QLabel("Energy:"))
        self.energy_slider = EnhancedSlider(Qt.Orientation.Horizontal)
        self.energy_slider.setRange(0, 100)
        self.energy_slider.setValue(20)
        self.energy_label = QLabel("20%")
        self.energy_slider.valueChanged.connect(
            lambda v: [self.energy_label.setText(f"{v}%"), self.weight_changed.emit("energy", v/100)]
        )
        energy_layout.addWidget(self.energy_slider)
        energy_layout.addWidget(self.energy_label)
        weights_layout.addLayout(energy_layout)
        
        # Emotional weight
        emotional_layout = QHBoxLayout()
        emotional_layout.addWidget(QLabel("Emotional:"))
        self.emotional_slider = EnhancedSlider(Qt.Orientation.Horizontal)
        self.emotional_slider.setRange(0, 100)
        self.emotional_slider.setValue(10)
        self.emotional_label = QLabel("10%")
        self.emotional_slider.valueChanged.connect(
            lambda v: [self.emotional_label.setText(f"{v}%"), self.weight_changed.emit("emotional", v/100)]
        )
        emotional_layout.addWidget(self.emotional_slider)
        emotional_layout.addWidget(self.emotional_label)
        weights_layout.addLayout(emotional_layout)
        
        weights_group.setLayout(weights_layout)
        settings_layout.addWidget(weights_group)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # Mixing Policies Group
        policies_group = QGroupBox("Mixing Policies")
        policies_layout = QVBoxLayout()
        
        # Policy selector (compact version)
        try:
            from ..analysis.configurable_policies import ConfigurablePolicyManager
            import tempfile
            policy_manager = ConfigurablePolicyManager(config_dir=tempfile.gettempdir())
            self.policy_selector = PolicyQuickSelector(policy_manager)
            policies_layout.addWidget(self.policy_selector)
        except ImportError:
            # Fallback if policy manager is not available
            policies_layout.addWidget(QLabel("Policy management not available"))
        
        policies_group.setLayout(policies_layout)
        layout.addWidget(policies_group)
        
        # Playlist Generation Group
        playlist_group = QGroupBox("Playlist Generation")
        playlist_layout = QVBoxLayout()
        
        # Generate playlist button
        self.generate_btn = ModernButton("Generate Playlist", "primary")
        self.generate_btn.clicked.connect(self.generate_playlist.emit)
        self.generate_btn.setEnabled(False)
        playlist_layout.addWidget(self.generate_btn)
        
        playlist_group.setLayout(playlist_layout)
        layout.addWidget(playlist_group)
        
        # Add stretch to push everything to top
        layout.addStretch(1)
    
    def set_generate_enabled(self, enabled: bool):
        """Enable/disable generate button"""
        self.generate_btn.setEnabled(enabled)
    
    def get_current_mode(self) -> str:
        """Get current mixing mode"""
        return self.mode_combo.currentText()
    
    def get_weights(self) -> dict:
        """Get current weight values"""
        return {
            'key': self.key_slider.value() / 100,
            'bpm': self.bpm_slider.value() / 100,
            'energy': self.energy_slider.value() / 100,
            'emotional': self.emotional_slider.value() / 100
        }


class AdvancedControlsTab(QWidget):
    """Tab for advanced contextual and temporal controls"""
    
    # Signals for main window communication
    contextual_generate = pyqtSignal()
    temporal_generate = pyqtSignal()
    optimization_generate = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the advanced controls UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Contextual Generation Group
        contextual_group = QGroupBox("Contextual Generation")
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
        self.contextual_generate_btn = ModernButton("Generate Contextual", "primary")
        self.contextual_generate_btn.clicked.connect(self.contextual_generate.emit)
        self.contextual_generate_btn.setEnabled(False)
        contextual_layout.addWidget(self.contextual_generate_btn)
        
        contextual_group.setLayout(contextual_layout)
        layout.addWidget(contextual_group)
        
        # Temporal & Linguistic Group
        temporal_group = QGroupBox("Temporal & Linguistic")
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
        self.temporal_generate_btn = ModernButton("Generate Temporal", "secondary")
        self.temporal_generate_btn.clicked.connect(self.temporal_generate.emit)
        self.temporal_generate_btn.setEnabled(False)
        temporal_layout.addWidget(self.temporal_generate_btn)
        
        temporal_group.setLayout(temporal_layout)
        layout.addWidget(temporal_group)
        
        # Global Optimization Group
        optimization_group = QGroupBox("Global Optimization")
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
        self.global_optimize_btn.clicked.connect(self.optimization_generate.emit)
        self.global_optimize_btn.setEnabled(False)
        optimization_layout.addWidget(self.global_optimize_btn)
        
        optimization_group.setLayout(optimization_layout)
        layout.addWidget(optimization_group)
        
        # Add stretch to push everything to top
        layout.addStretch(1)
    
    def set_buttons_enabled(self, enabled: bool):
        """Enable/disable all generate buttons"""
        self.contextual_generate_btn.setEnabled(enabled)
        self.temporal_generate_btn.setEnabled(enabled)
        self.global_optimize_btn.setEnabled(enabled)
    
    def get_contextual_settings(self) -> dict:
        """Get contextual generation settings"""
        return {
            'time_of_day': self.time_combo.currentText(),
            'activity': self.activity_combo.currentText(),
            'season': self.season_combo.currentText()
        }
    
    def get_temporal_settings(self) -> dict:
        """Get temporal generation settings"""
        return {
            'temporal_flow': self.temporal_flow_combo.currentText(),
            'linguistic_flow': self.linguistic_flow_combo.currentText()
        }
    
    def get_optimization_settings(self) -> dict:
        """Get optimization settings"""
        return {
            'objective': self.optimization_combo.currentText(),
            'max_alternatives': self.alternatives_slider.value()
        }


class PlayerControlsTab(QWidget):
    """Tab for player controls and track information"""
    
    # Signals for main window communication
    play_pause = pyqtSignal()
    stop = pyqtSignal()
    volume_changed = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the player controls UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Current track info
        track_info_group = QGroupBox("Current Track")
        track_info_layout = QVBoxLayout()
        
        self.current_track_label = QLabel("No track selected")
        self.current_track_label.setWordWrap(True)
        self.current_track_label.setMinimumHeight(60)
        track_info_layout.addWidget(self.current_track_label)
        
        track_info_group.setLayout(track_info_layout)
        layout.addWidget(track_info_group)
        
        # Player controls
        player_group = QGroupBox("Player Controls")
        player_layout = QVBoxLayout()
        
        # Play/pause and stop buttons
        button_layout = QHBoxLayout()
        
        self.play_btn = ModernButton("▶", "primary")
        self.play_btn.setEnabled(False)
        self.play_btn.clicked.connect(self.play_pause.emit)
        self.play_btn.setMinimumWidth(60)
        button_layout.addWidget(self.play_btn)
        
        self.stop_btn = ModernButton("⏹", "secondary")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop.emit)
        self.stop_btn.setMinimumWidth(60)
        button_layout.addWidget(self.stop_btn)
        
        button_layout.addStretch()
        player_layout.addLayout(button_layout)
        
        # Volume control
        volume_layout = QHBoxLayout()
        volume_layout.addWidget(QLabel("Volume:"))
        
        self.volume_slider = EnhancedSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.valueChanged.connect(self.volume_changed.emit)
        volume_layout.addWidget(self.volume_slider)
        
        self.volume_label = QLabel("50%")
        self.volume_slider.valueChanged.connect(
            lambda v: self.volume_label.setText(f"{v}%")
        )
        volume_layout.addWidget(self.volume_label)
        
        player_layout.addLayout(volume_layout)
        
        player_group.setLayout(player_layout)
        layout.addWidget(player_group)
        
        # Add stretch to push everything to top
        layout.addStretch(1)
    
    def set_current_track(self, track_info: str):
        """Set current track information"""
        self.current_track_label.setText(track_info)
    
    def set_play_enabled(self, enabled: bool):
        """Enable/disable play button"""
        self.play_btn.setEnabled(enabled)
    
    def set_stop_enabled(self, enabled: bool):
        """Enable/disable stop button"""
        self.stop_btn.setEnabled(enabled)
    
    def set_play_text(self, text: str):
        """Set play button text (▶ or ⏸)"""
        self.play_btn.setText(text)


class TabbedControlPanel(QTabWidget):
    """Main tabbed control panel that organizes all controls"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.apply_styling()
    
    def setup_ui(self):
        """Setup the tabbed interface"""
        # Create tabs
        self.mixing_tab = MixingControlsTab()
        self.advanced_tab = AdvancedControlsTab()
        self.player_tab = PlayerControlsTab()
        
        # Add tabs to widget
        self.addTab(self.mixing_tab, "🎵 Mixing")
        self.addTab(self.advanced_tab, "⚙️ Advanced")
        self.addTab(self.player_tab, "▶️ Player")
        
        # Set default tab
        self.setCurrentIndex(0)
    
    def apply_styling(self):
        """Apply modern styling to the tab widget"""
        self.setStyleSheet(f"""
            QTabWidget::pane {{
                background-color: {BlueLibraryTheme.SURFACE_LOW};
                border: 2px solid {BlueLibraryTheme.ACCENT_PRIMARY};
                border-radius: 8px;
                padding: 5px;
            }}
            
            QTabBar::tab {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {BlueLibraryTheme.SURFACE_MEDIUM}, 
                    stop:1 {BlueLibraryTheme.SURFACE_LOW});
                border: 1px solid {BlueLibraryTheme.ACCENT_PRIMARY};
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                padding: 8px 12px;
                margin-right: 2px;
                color: {BlueLibraryTheme.TEXT_PRIMARY};
                font-weight: 600;
                min-width: 80px;
            }}
            
            QTabBar::tab:selected {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {BlueLibraryTheme.ACCENT_PRIMARY}, 
                    stop:1 {BlueLibraryTheme.SURFACE_LOW});
                color: {BlueLibraryTheme.TEXT_PRIMARY};
                font-weight: 700;
            }}
            
            QTabBar::tab:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {BlueLibraryTheme.SURFACE_HIGH}, 
                    stop:1 {BlueLibraryTheme.SURFACE_MEDIUM});
            }}
            
            QGroupBox {{
                font-weight: 600;
                color: {BlueLibraryTheme.TEXT_ACCENT};
                border: 1px solid {BlueLibraryTheme.ACCENT_PRIMARY};
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 6px;
            }}
            
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                background-color: {BlueLibraryTheme.SURFACE_LOW};
            }}
        """)
    
    def get_mixing_tab(self) -> MixingControlsTab:
        """Get the mixing controls tab"""
        return self.mixing_tab
    
    def get_advanced_tab(self) -> AdvancedControlsTab:
        """Get the advanced controls tab"""
        return self.advanced_tab
    
    def get_player_tab(self) -> PlayerControlsTab:
        """Get the player controls tab"""
        return self.player_tab