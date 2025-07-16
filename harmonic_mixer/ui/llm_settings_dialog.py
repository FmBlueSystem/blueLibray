"""
LLM Settings Dialog
Configuration interface for LLM integration
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QTabWidget,
    QGroupBox, QLabel, QLineEdit, QComboBox, QCheckBox, QSlider,
    QPushButton, QTextEdit, QSpinBox, QDoubleSpinBox, QProgressBar,
    QMessageBox, QWidget, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
from typing import Optional

from ..llm.llm_config_manager import LLMSettings
from ..core.application_facade import BlueLibraryFacade
from .theme import BlueLibraryTheme


class LLMTestThread(QThread):
    """Thread for testing LLM configuration"""
    test_completed = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, facade, settings):
        super().__init__()
        self.facade = facade
        self.settings = settings
    
    def run(self):
        try:
            # Test the configuration
            success = self.facade.update_llm_settings(self.settings)
            if success and self.facade.is_llm_configured():
                self.test_completed.emit(True, "LLM configuration successful!")
            else:
                self.test_completed.emit(False, "Failed to initialize LLM with these settings")
        except Exception as e:
            self.test_completed.emit(False, f"Error: {str(e)}")


class LLMSettingsDialog(QDialog):
    """Dialog for configuring LLM settings"""
    
    # Signal emitted when LLM settings are successfully saved
    llm_settings_saved = pyqtSignal()
    
    def __init__(self, facade: BlueLibraryFacade, parent=None):
        super().__init__(parent)
        self.facade = facade
        self.test_thread = None
        
        self.setWindowTitle("LLM Configuration")
        self.setFixedSize(600, 700)
        
        # Apply dark theme
        self.setStyleSheet(BlueLibraryTheme.get_dialog_stylesheet())
        
        # Load current settings
        self.current_settings = facade.get_llm_settings()
        if not self.current_settings:
            self.current_settings = LLMSettings()
        
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Create tab widget
        tab_widget = QTabWidget()
        
        # Basic settings tab
        basic_tab = self.create_basic_tab()
        tab_widget.addTab(basic_tab, "Basic Configuration")
        
        # Advanced settings tab
        advanced_tab = self.create_advanced_tab()
        tab_widget.addTab(advanced_tab, "Advanced Settings")
        
        # Cost & Usage tab
        cost_tab = self.create_cost_tab()
        tab_widget.addTab(cost_tab, "Cost & Usage")
        
        layout.addWidget(tab_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.test_btn = QPushButton("Test Configuration")
        self.test_btn.clicked.connect(self.test_configuration)
        button_layout.addWidget(self.test_btn)
        
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_settings)
        button_layout.addWidget(self.save_btn)
        
        layout.addLayout(button_layout)
    
    def create_basic_tab(self) -> QWidget:
        """Create basic configuration tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Enable LLM
        self.enabled_cb = QCheckBox("Enable LLM Integration")
        self.enabled_cb.toggled.connect(self.on_enabled_changed)
        layout.addWidget(self.enabled_cb)
        
        # Provider selection
        provider_group = QGroupBox("LLM Provider")
        provider_layout = QFormLayout(provider_group)
        
        self.provider_combo = QComboBox()
        providers = self.facade.get_llm_providers()
        for provider_id, provider_info in providers.items():
            self.provider_combo.addItem(provider_info['name'], provider_id)
        self.provider_combo.currentTextChanged.connect(self.on_provider_changed)
        provider_layout.addRow("Provider:", self.provider_combo)
        
        self.model_combo = QComboBox()
        provider_layout.addRow("Model:", self.model_combo)
        
        layout.addWidget(provider_group)
        
        # API Configuration
        api_group = QGroupBox("API Configuration")
        api_layout = QFormLayout(api_group)
        
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_edit.setPlaceholderText("Enter your API key...")
        api_layout.addRow("API Key:", self.api_key_edit)
        
        # Show API key button
        show_key_btn = QPushButton("Show/Hide Key")
        show_key_btn.clicked.connect(self.toggle_api_key_visibility)
        api_layout.addRow("", show_key_btn)
        
        layout.addWidget(api_group)
        
        # Mixing Configuration
        mixing_group = QGroupBox("Mixing Algorithm")
        mixing_layout = QFormLayout(mixing_group)
        
        # LLM weight slider
        weight_layout = QHBoxLayout()
        self.weight_slider = QSlider(Qt.Orientation.Horizontal)
        self.weight_slider.setRange(0, 100)
        self.weight_slider.setValue(30)
        self.weight_slider.valueChanged.connect(self.on_weight_changed)
        self.weight_label = QLabel("30%")
        weight_layout.addWidget(self.weight_slider)
        weight_layout.addWidget(self.weight_label)
        mixing_layout.addRow("LLM Weight:", weight_layout)
        
        self.emotional_cb = QCheckBox("Use Emotional Analysis")
        self.emotional_cb.setChecked(True)
        mixing_layout.addRow("", self.emotional_cb)
        
        self.genre_cb = QCheckBox("Use Genre Intelligence")
        self.genre_cb.setChecked(True)
        mixing_layout.addRow("", self.genre_cb)
        
        self.fallback_cb = QCheckBox("Fallback to Traditional Algorithm")
        self.fallback_cb.setChecked(True)
        mixing_layout.addRow("", self.fallback_cb)
        
        layout.addWidget(mixing_group)
        
        layout.addStretch()
        return widget
    
    def create_advanced_tab(self) -> QWidget:
        """Create advanced settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Model Parameters
        model_group = QGroupBox("Model Parameters")
        model_layout = QFormLayout(model_group)
        
        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setRange(100, 4000)
        self.max_tokens_spin.setValue(500)
        model_layout.addRow("Max Tokens:", self.max_tokens_spin)
        
        self.temperature_spin = QDoubleSpinBox()
        self.temperature_spin.setRange(0.0, 2.0)
        self.temperature_spin.setSingleStep(0.1)
        self.temperature_spin.setValue(0.1)
        model_layout.addRow("Temperature:", self.temperature_spin)
        
        layout.addWidget(model_group)
        
        # Performance Settings
        perf_group = QGroupBox("Performance")
        perf_layout = QFormLayout(perf_group)
        
        self.cache_cb = QCheckBox("Enable Response Caching")
        self.cache_cb.setChecked(True)
        perf_layout.addRow("", self.cache_cb)
        
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(10, 120)
        self.timeout_spin.setValue(30)
        self.timeout_spin.setSuffix(" seconds")
        perf_layout.addRow("Request Timeout:", self.timeout_spin)
        
        layout.addWidget(perf_group)
        
        # Provider Info
        info_group = QGroupBox("Provider Information")
        info_layout = QVBoxLayout(info_group)
        
        self.provider_info_label = QLabel()
        self.provider_info_label.setWordWrap(True)
        self.provider_info_label.setStyleSheet(BlueLibraryTheme.get_info_section_style("info"))
        info_layout.addWidget(self.provider_info_label)
        
        layout.addWidget(info_group)
        
        layout.addStretch()
        return widget
    
    def create_cost_tab(self) -> QWidget:
        """Create cost estimation tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Cost Estimation
        cost_group = QGroupBox("Cost Estimation")
        cost_layout = QVBoxLayout(cost_group)
        
        tracks_count = len(self.facade.get_tracks())
        cost_info = self.facade.get_llm_cost_estimate(tracks_count) if tracks_count > 0 else None
        
        if cost_info:
            cost_text = f"""
            Current Library: {cost_info['num_tracks']} tracks
            Estimated Tokens: {cost_info['total_tokens']:,}
            Model: {cost_info['model']}
            Estimated Cost: ${cost_info['estimated_cost_usd']}
            
            This is an estimate for analyzing all tracks once.
            Caching reduces repeat analysis costs.
            """
        else:
            cost_text = "No tracks loaded. Load your music library to see cost estimates."
        
        cost_label = QLabel(cost_text)
        cost_label.setStyleSheet(BlueLibraryTheme.get_info_section_style("blue"))
        cost_layout.addWidget(cost_label)
        
        layout.addWidget(cost_group)
        
        # Usage Tips
        tips_group = QGroupBox("Cost Optimization Tips")
        tips_layout = QVBoxLayout(tips_group)
        
        tips_text = """
        💡 Tips to minimize costs:
        
        • Enable caching to avoid re-analyzing the same tracks
        • Use gpt-3.5-turbo instead of gpt-4 for lower costs
        • Consider Groq for faster, cheaper inference
        • Set lower max_tokens if you don't need detailed analysis
        • Use lower LLM weight (more traditional algorithm)
        
        🔒 Your API key is stored securely and never shared.
        """
        
        tips_label = QLabel(tips_text)
        tips_label.setWordWrap(True)
        tips_label.setStyleSheet(BlueLibraryTheme.get_info_section_style("yellow"))
        tips_layout.addWidget(tips_label)
        
        layout.addWidget(tips_group)
        
        layout.addStretch()
        return widget
    
    def load_settings(self):
        """Load settings into UI"""
        settings = self.current_settings
        
        self.enabled_cb.setChecked(settings.enabled)
        
        # Set provider
        provider_index = self.provider_combo.findData(settings.provider)
        if provider_index >= 0:
            self.provider_combo.setCurrentIndex(provider_index)
        
        self.api_key_edit.setText(settings.api_key)
        self.weight_slider.setValue(int(settings.mixing_weight * 100))
        self.emotional_cb.setChecked(settings.use_emotional_analysis)
        self.genre_cb.setChecked(settings.use_genre_intelligence)
        self.fallback_cb.setChecked(settings.fallback_to_traditional)
        self.max_tokens_spin.setValue(settings.max_tokens)
        self.temperature_spin.setValue(settings.temperature)
        self.cache_cb.setChecked(settings.cache_enabled)
        
        # Update model combo and provider info
        self.on_provider_changed()
        self.on_enabled_changed()
    
    def on_enabled_changed(self):
        """Handle enable/disable toggle"""
        enabled = self.enabled_cb.isChecked()
        # Enable/disable all other controls based on enabled state
        widgets_to_toggle = [
            self.provider_combo, self.model_combo, self.api_key_edit,
            self.weight_slider, self.emotional_cb, self.genre_cb,
            self.fallback_cb, self.max_tokens_spin, self.temperature_spin,
            self.cache_cb, self.test_btn
        ]
        for widget in widgets_to_toggle:
            widget.setEnabled(enabled)
    
    def on_provider_changed(self):
        """Handle provider selection change"""
        provider_id = self.provider_combo.currentData()
        providers = self.facade.get_llm_providers()
        
        if provider_id in providers:
            provider_info = providers[provider_id]
            
            # Update model combo
            self.model_combo.clear()
            for model in provider_info['models']:
                self.model_combo.addItem(model)
            
            # Set current model if it exists in new provider
            current_model = self.current_settings.model
            model_index = self.model_combo.findText(current_model)
            if model_index >= 0:
                self.model_combo.setCurrentIndex(model_index)
            
            # Update provider info
            self.provider_info_label.setText(
                f"<b>{provider_info['name']}</b><br>"
                f"{provider_info['description']}<br><br>"
                f"API Key Required: {'Yes' if provider_info['requires_api_key'] else 'No'}"
            )
    
    def on_weight_changed(self):
        """Handle LLM weight slider change"""
        value = self.weight_slider.value()
        self.weight_label.setText(f"{value}%")
    
    def toggle_api_key_visibility(self):
        """Toggle API key visibility"""
        if self.api_key_edit.echoMode() == QLineEdit.EchoMode.Password:
            self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
    
    def get_settings_from_ui(self) -> LLMSettings:
        """Get settings from UI controls"""
        return LLMSettings(
            enabled=self.enabled_cb.isChecked(),
            provider=self.provider_combo.currentData(),
            api_key=self.api_key_edit.text().strip(),
            model=self.model_combo.currentText(),
            max_tokens=self.max_tokens_spin.value(),
            temperature=self.temperature_spin.value(),
            cache_enabled=self.cache_cb.isChecked(),
            mixing_weight=self.weight_slider.value() / 100.0,
            use_emotional_analysis=self.emotional_cb.isChecked(),
            use_genre_intelligence=self.genre_cb.isChecked(),
            fallback_to_traditional=self.fallback_cb.isChecked()
        )
    
    def test_configuration(self):
        """Test the LLM configuration"""
        settings = self.get_settings_from_ui()
        
        if not settings.enabled:
            QMessageBox.information(self, "Test", "LLM integration is disabled.")
            return
        
        if not settings.api_key:
            QMessageBox.warning(self, "Test", "Please enter an API key.")
            return
        
        # Disable test button and show progress
        self.test_btn.setEnabled(False)
        self.test_btn.setText("Testing...")
        
        # Start test in background thread
        self.test_thread = LLMTestThread(self.facade, settings)
        self.test_thread.test_completed.connect(self.on_test_completed)
        self.test_thread.start()
    
    def on_test_completed(self, success: bool, message: str):
        """Handle test completion"""
        self.test_btn.setEnabled(True)
        self.test_btn.setText("Test Configuration")
        
        if success:
            QMessageBox.information(self, "Test Result", message)
        else:
            QMessageBox.warning(self, "Test Failed", message)
    
    def save_settings(self):
        """Save settings and close dialog"""
        settings = self.get_settings_from_ui()
        
        if settings.enabled and not settings.api_key:
            reply = QMessageBox.question(
                self, "No API Key",
                "LLM is enabled but no API key is set. Continue anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
        
        # Save settings
        success = self.facade.update_llm_settings(settings)
        if success:
            QMessageBox.information(self, "Success", "LLM settings saved successfully!")
            # Emit signal to notify parent window
            self.llm_settings_saved.emit()
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Failed to save LLM settings.")
    
    def closeEvent(self, event):
        """Handle dialog close"""
        if self.test_thread and self.test_thread.isRunning():
            self.test_thread.terminate()
            self.test_thread.wait()
        event.accept()
