"""
Policy Editor UI Components
Graphical interface for creating and editing mixing policies
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QLabel, QPushButton, QLineEdit, QTextEdit, QComboBox, QSpinBox,
    QDoubleSpinBox, QCheckBox, QListWidget, QListWidgetItem, QTabWidget,
    QGroupBox, QSplitter, QTreeWidget, QTreeWidgetItem, QMessageBox,
    QFileDialog, QProgressBar, QSlider, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QIcon
from typing import Dict, List, Optional, Any

from ..analysis.configurable_policies import (
    ConfigurablePolicyManager, MixingPolicy, PolicyRuleSet, PolicyRule,
    PolicyType, OperatorType, RulePriority, PolicyApplicationResult
)


class PolicyEditorWidget(QWidget):
    """Main policy editor widget"""
    
    policy_changed = pyqtSignal(str)  # policy_id
    
    def __init__(self, policy_manager: ConfigurablePolicyManager, parent=None):
        super().__init__(parent)
        self.policy_manager = policy_manager
        self.current_policy_id = None
        self.current_rule_set_id = None
        self.current_rule_id = None
        
        self.init_ui()
        self.refresh_policy_list()
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QHBoxLayout(self)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        # Left panel - Policy list and basic controls
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - Detailed editor
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter proportions
        splitter.setSizes([300, 700])
    
    def create_left_panel(self) -> QWidget:
        """Create left panel with policy list"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Policy list
        layout.addWidget(QLabel("Mixing Policies:"))
        
        self.policy_list = QListWidget()
        self.policy_list.itemClicked.connect(self.on_policy_selected)
        layout.addWidget(self.policy_list)
        
        # Policy controls
        controls_layout = QHBoxLayout()
        
        self.new_policy_btn = QPushButton("New Policy")
        self.new_policy_btn.clicked.connect(self.create_new_policy)
        controls_layout.addWidget(self.new_policy_btn)
        
        self.delete_policy_btn = QPushButton("Delete")
        self.delete_policy_btn.clicked.connect(self.delete_current_policy)
        self.delete_policy_btn.setEnabled(False)
        controls_layout.addWidget(self.delete_policy_btn)
        
        layout.addLayout(controls_layout)
        
        # Import/Export
        import_export_layout = QHBoxLayout()
        
        self.import_btn = QPushButton("Import")
        self.import_btn.clicked.connect(self.import_policy)
        import_export_layout.addWidget(self.import_btn)
        
        self.export_btn = QPushButton("Export")
        self.export_btn.clicked.connect(self.export_policy)
        self.export_btn.setEnabled(False)
        import_export_layout.addWidget(self.export_btn)
        
        layout.addLayout(import_export_layout)
        
        # Preview section
        layout.addWidget(QLabel("Policy Preview:"))
        
        self.preview_text = QTextEdit()
        self.preview_text.setMaximumHeight(150)
        self.preview_text.setReadOnly(True)
        layout.addWidget(self.preview_text)
        
        return panel
    
    def create_right_panel(self) -> QWidget:
        """Create right panel with detailed editor"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Policy info tab
        self.policy_info_tab = self.create_policy_info_tab()
        self.tab_widget.addTab(self.policy_info_tab, "Policy Info")
        
        # Rule sets tab
        self.rule_sets_tab = self.create_rule_sets_tab()
        self.tab_widget.addTab(self.rule_sets_tab, "Rule Sets")
        
        # Rules editor tab
        self.rules_editor_tab = self.create_rules_editor_tab()
        self.tab_widget.addTab(self.rules_editor_tab, "Rules Editor")
        
        # Test tab
        self.test_tab = self.create_test_tab()
        self.tab_widget.addTab(self.test_tab, "Test Policy")
        
        # Save/Cancel buttons
        buttons_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("Save Policy")
        self.save_btn.clicked.connect(self.save_current_policy)
        self.save_btn.setEnabled(False)
        buttons_layout.addWidget(self.save_btn)
        
        self.cancel_btn = QPushButton("Cancel Changes")
        self.cancel_btn.clicked.connect(self.cancel_changes)
        self.cancel_btn.setEnabled(False)
        buttons_layout.addWidget(self.cancel_btn)
        
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)
        
        return panel
    
    def create_policy_info_tab(self) -> QWidget:
        """Create policy information tab"""
        tab = QWidget()
        layout = QFormLayout(tab)
        
        # Basic info
        self.policy_name_edit = QLineEdit()
        self.policy_name_edit.textChanged.connect(self.on_policy_modified)
        layout.addRow("Name:", self.policy_name_edit)
        
        self.policy_description_edit = QTextEdit()
        self.policy_description_edit.setMaximumHeight(80)
        self.policy_description_edit.textChanged.connect(self.on_policy_modified)
        layout.addRow("Description:", self.policy_description_edit)
        
        self.policy_version_edit = QLineEdit()
        self.policy_version_edit.textChanged.connect(self.on_policy_modified)
        layout.addRow("Version:", self.policy_version_edit)
        
        # Global settings
        layout.addRow(QLabel(""))  # Spacer
        layout.addRow(QLabel("Global Settings:"))
        
        self.optimization_objective_combo = QComboBox()
        self.optimization_objective_combo.addItems([
            "balanced", "compatibility", "narrative", "energy_flow", "cultural"
        ])
        self.optimization_objective_combo.currentTextChanged.connect(self.on_policy_modified)
        layout.addRow("Optimization Objective:", self.optimization_objective_combo)
        
        self.strict_mode_check = QCheckBox()
        self.strict_mode_check.stateChanged.connect(self.on_policy_modified)
        layout.addRow("Strict Mode:", self.strict_mode_check)
        
        self.adaptive_weights_check = QCheckBox()
        self.adaptive_weights_check.stateChanged.connect(self.on_policy_modified)
        layout.addRow("Adaptive Weights:", self.adaptive_weights_check)
        
        # Global weights
        layout.addRow(QLabel(""))  # Spacer
        layout.addRow(QLabel("Global Type Weights:"))
        
        self.weight_sliders = {}
        for policy_type in PolicyType:
            slider_layout = QHBoxLayout()
            
            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setRange(0, 100)
            slider.setValue(50)
            slider.valueChanged.connect(self.on_weight_changed)
            
            value_label = QLabel("0.50")
            value_label.setMinimumWidth(40)
            
            slider_layout.addWidget(slider)
            slider_layout.addWidget(value_label)
            
            self.weight_sliders[policy_type] = (slider, value_label)
            layout.addRow(f"{policy_type.value.title()}:", slider_layout)
        
        return tab
    
    def create_rule_sets_tab(self) -> QWidget:
        """Create rule sets management tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Rule sets list
        layout.addWidget(QLabel("Rule Sets:"))
        
        self.rule_sets_list = QListWidget()
        self.rule_sets_list.itemClicked.connect(self.on_rule_set_selected)
        layout.addWidget(self.rule_sets_list)
        
        # Rule set controls
        controls_layout = QHBoxLayout()
        
        self.new_rule_set_btn = QPushButton("New Rule Set")
        self.new_rule_set_btn.clicked.connect(self.create_new_rule_set)
        controls_layout.addWidget(self.new_rule_set_btn)
        
        self.edit_rule_set_btn = QPushButton("Edit")
        self.edit_rule_set_btn.clicked.connect(self.edit_current_rule_set)
        self.edit_rule_set_btn.setEnabled(False)
        controls_layout.addWidget(self.edit_rule_set_btn)
        
        self.delete_rule_set_btn = QPushButton("Delete")
        self.delete_rule_set_btn.clicked.connect(self.delete_current_rule_set)
        self.delete_rule_set_btn.setEnabled(False)
        controls_layout.addWidget(self.delete_rule_set_btn)
        
        layout.addLayout(controls_layout)
        
        # Rule set details
        details_group = QGroupBox("Rule Set Details")
        details_layout = QFormLayout(details_group)
        
        self.rule_set_name_edit = QLineEdit()
        self.rule_set_name_edit.textChanged.connect(self.on_policy_modified)
        details_layout.addRow("Name:", self.rule_set_name_edit)
        
        self.rule_set_description_edit = QTextEdit()
        self.rule_set_description_edit.setMaximumHeight(60)
        self.rule_set_description_edit.textChanged.connect(self.on_policy_modified)
        details_layout.addRow("Description:", self.rule_set_description_edit)
        
        self.rule_set_enabled_check = QCheckBox()
        self.rule_set_enabled_check.stateChanged.connect(self.on_policy_modified)
        details_layout.addRow("Enabled:", self.rule_set_enabled_check)
        
        self.combination_mode_combo = QComboBox()
        self.combination_mode_combo.addItems([
            "weighted_sum", "all_required", "any_satisfied", "majority"
        ])
        self.combination_mode_combo.currentTextChanged.connect(self.on_policy_modified)
        details_layout.addRow("Combination Mode:", self.combination_mode_combo)
        
        self.minimum_score_spin = QDoubleSpinBox()
        self.minimum_score_spin.setRange(0.0, 1.0)
        self.minimum_score_spin.setSingleStep(0.1)
        self.minimum_score_spin.setValue(0.6)
        self.minimum_score_spin.valueChanged.connect(self.on_policy_modified)
        details_layout.addRow("Minimum Score:", self.minimum_score_spin)
        
        layout.addWidget(details_group)
        
        return tab
    
    def create_rules_editor_tab(self) -> QWidget:
        """Create rules editor tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Rules list
        layout.addWidget(QLabel("Rules:"))
        
        self.rules_list = QListWidget()
        self.rules_list.itemClicked.connect(self.on_rule_selected)
        layout.addWidget(self.rules_list)
        
        # Rule controls
        controls_layout = QHBoxLayout()
        
        self.new_rule_btn = QPushButton("New Rule")
        self.new_rule_btn.clicked.connect(self.create_new_rule)
        controls_layout.addWidget(self.new_rule_btn)
        
        self.edit_rule_btn = QPushButton("Edit")
        self.edit_rule_btn.clicked.connect(self.edit_current_rule)
        self.edit_rule_btn.setEnabled(False)
        controls_layout.addWidget(self.edit_rule_btn)
        
        self.delete_rule_btn = QPushButton("Delete")
        self.delete_rule_btn.clicked.connect(self.delete_current_rule)
        self.delete_rule_btn.setEnabled(False)
        controls_layout.addWidget(self.delete_rule_btn)
        
        layout.addLayout(controls_layout)
        
        # Rule details in scrollable area
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QFormLayout(scroll_widget)
        
        # Basic rule info
        self.rule_name_edit = QLineEdit()
        self.rule_name_edit.textChanged.connect(self.on_policy_modified)
        scroll_layout.addRow("Name:", self.rule_name_edit)
        
        self.rule_description_edit = QTextEdit()
        self.rule_description_edit.setMaximumHeight(60)
        self.rule_description_edit.textChanged.connect(self.on_policy_modified)
        scroll_layout.addRow("Description:", self.rule_description_edit)
        
        # Rule definition
        self.policy_type_combo = QComboBox()
        self.policy_type_combo.addItems([pt.value for pt in PolicyType])
        self.policy_type_combo.currentTextChanged.connect(self.on_policy_modified)
        scroll_layout.addRow("Policy Type:", self.policy_type_combo)
        
        self.field_combo = QComboBox()
        self.field_combo.addItems([
            "key", "bpm", "energy", "subgenre", "mood", "era", "language",
            "danceability", "crowd_appeal", "mix_friendly", "time_of_day", "activity"
        ])
        self.field_combo.currentTextChanged.connect(self.on_policy_modified)
        scroll_layout.addRow("Field:", self.field_combo)
        
        self.operator_combo = QComboBox()
        self.operator_combo.addItems([op.value for op in OperatorType])
        self.operator_combo.currentTextChanged.connect(self.on_policy_modified)
        scroll_layout.addRow("Operator:", self.operator_combo)
        
        self.value_edit = QLineEdit()
        self.value_edit.textChanged.connect(self.on_policy_modified)
        scroll_layout.addRow("Value:", self.value_edit)
        
        self.context_combo = QComboBox()
        self.context_combo.addItems(["track", "transition", "sequence", "global"])
        self.context_combo.currentTextChanged.connect(self.on_policy_modified)
        scroll_layout.addRow("Context:", self.context_combo)
        
        # Rule properties
        scroll_layout.addRow(QLabel(""))  # Spacer
        scroll_layout.addRow(QLabel("Rule Properties:"))
        
        self.priority_combo = QComboBox()
        self.priority_combo.addItems([rp.value for rp in RulePriority])
        self.priority_combo.currentTextChanged.connect(self.on_policy_modified)
        scroll_layout.addRow("Priority:", self.priority_combo)
        
        self.weight_spin = QDoubleSpinBox()
        self.weight_spin.setRange(0.0, 10.0)
        self.weight_spin.setSingleStep(0.1)
        self.weight_spin.setValue(1.0)
        self.weight_spin.valueChanged.connect(self.on_policy_modified)
        scroll_layout.addRow("Weight:", self.weight_spin)
        
        self.enabled_check = QCheckBox()
        self.enabled_check.stateChanged.connect(self.on_policy_modified)
        scroll_layout.addRow("Enabled:", self.enabled_check)
        
        self.tolerance_spin = QDoubleSpinBox()
        self.tolerance_spin.setRange(0.0, 100.0)
        self.tolerance_spin.setSingleStep(0.1)
        self.tolerance_spin.setValue(0.0)
        self.tolerance_spin.valueChanged.connect(self.on_policy_modified)
        scroll_layout.addRow("Tolerance:", self.tolerance_spin)
        
        self.adaptive_check = QCheckBox()
        self.adaptive_check.stateChanged.connect(self.on_policy_modified)
        scroll_layout.addRow("Adaptive:", self.adaptive_check)
        
        self.time_sensitive_check = QCheckBox()
        self.time_sensitive_check.stateChanged.connect(self.on_policy_modified)
        scroll_layout.addRow("Time Sensitive:", self.time_sensitive_check)
        
        self.rule_notes_edit = QTextEdit()
        self.rule_notes_edit.setMaximumHeight(60)
        self.rule_notes_edit.textChanged.connect(self.on_policy_modified)
        scroll_layout.addRow("Notes:", self.rule_notes_edit)
        
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)
        
        return tab
    
    def create_test_tab(self) -> QWidget:
        """Create policy testing tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Test controls
        test_controls = QHBoxLayout()
        
        self.test_policy_btn = QPushButton("Test Current Policy")
        self.test_policy_btn.clicked.connect(self.test_current_policy)
        test_controls.addWidget(self.test_policy_btn)
        
        self.test_progress = QProgressBar()
        self.test_progress.setVisible(False)
        test_controls.addWidget(self.test_progress)
        
        test_controls.addStretch()
        layout.addLayout(test_controls)
        
        # Test results
        layout.addWidget(QLabel("Test Results:"))
        
        self.test_results = QTextEdit()
        self.test_results.setReadOnly(True)
        layout.addWidget(self.test_results)
        
        return tab
    
    def refresh_policy_list(self):
        """Refresh the policy list"""
        self.policy_list.clear()
        
        for policy in self.policy_manager.list_policies():
            item = QListWidgetItem(f"{policy.name} (v{policy.version})")
            item.setData(Qt.ItemDataRole.UserRole, policy.id)
            
            # Color-code by creator
            if policy.created_by == "system":
                item.setForeground(Qt.GlobalColor.blue)
            else:
                item.setForeground(Qt.GlobalColor.black)
            
            self.policy_list.addItem(item)
    
    def on_policy_selected(self, item: QListWidgetItem):
        """Handle policy selection"""
        policy_id = item.data(Qt.ItemDataRole.UserRole)
        self.current_policy_id = policy_id
        
        policy = self.policy_manager.get_policy(policy_id)
        if policy:
            self.load_policy_to_ui(policy)
            self.delete_policy_btn.setEnabled(policy.created_by == "user")
            self.export_btn.setEnabled(True)
    
    def load_policy_to_ui(self, policy: MixingPolicy):
        """Load policy data into UI components"""
        # Policy info
        self.policy_name_edit.setText(policy.name)
        self.policy_description_edit.setPlainText(policy.description)
        self.policy_version_edit.setText(policy.version)
        
        # Global settings
        self.optimization_objective_combo.setCurrentText(policy.optimization_objective)
        self.strict_mode_check.setChecked(policy.strict_mode)
        self.adaptive_weights_check.setChecked(policy.adaptive_weights)
        
        # Global weights
        for policy_type, (slider, label) in self.weight_sliders.items():
            weight = policy.global_weights.get(policy_type, 0.5)
            slider.setValue(int(weight * 100))
            label.setText(f"{weight:.2f}")
        
        # Rule sets
        self.refresh_rule_sets_list(policy)
        
        # Update preview
        self.update_policy_preview(policy)
    
    def refresh_rule_sets_list(self, policy: MixingPolicy):
        """Refresh rule sets list"""
        self.rule_sets_list.clear()
        
        for rule_set in policy.rule_sets:
            item = QListWidgetItem(f"{rule_set.name} ({len(rule_set.rules)} rules)")
            item.setData(Qt.ItemDataRole.UserRole, rule_set.id)
            
            if not rule_set.enabled:
                item.setForeground(Qt.GlobalColor.gray)
            
            self.rule_sets_list.addItem(item)
    
    def update_policy_preview(self, policy: MixingPolicy):
        """Update policy preview text"""
        preview = f"Policy: {policy.name}\n"
        preview += f"Objective: {policy.optimization_objective}\n"
        preview += f"Rule Sets: {len(policy.rule_sets)}\n"
        
        total_rules = sum(len(rs.rules) for rs in policy.rule_sets)
        preview += f"Total Rules: {total_rules}\n\n"
        
        for rule_set in policy.rule_sets:
            preview += f"• {rule_set.name}: {len(rule_set.rules)} rules\n"
        
        self.preview_text.setPlainText(preview)
    
    def on_weight_changed(self):
        """Handle weight slider changes"""
        sender = self.sender()
        
        for policy_type, (slider, label) in self.weight_sliders.items():
            if slider == sender:
                value = slider.value() / 100.0
                label.setText(f"{value:.2f}")
                break
        
        self.on_policy_modified()
    
    def on_policy_modified(self):
        """Handle policy modification"""
        self.save_btn.setEnabled(True)
        self.cancel_btn.setEnabled(True)
    
    def create_new_policy(self):
        """Create a new policy"""
        # Implementation would open a dialog to create new policy
        pass
    
    def delete_current_policy(self):
        """Delete the current policy"""
        if self.current_policy_id:
            reply = QMessageBox.question(
                self, "Delete Policy",
                f"Are you sure you want to delete this policy?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                if self.policy_manager.delete_policy(self.current_policy_id):
                    self.refresh_policy_list()
                    self.current_policy_id = None
    
    def save_current_policy(self):
        """Save the current policy"""
        if self.current_policy_id:
            # Collect data from UI and update policy
            # Implementation would gather all form data and update policy
            self.save_btn.setEnabled(False)
            self.cancel_btn.setEnabled(False)
            
            QMessageBox.information(self, "Saved", "Policy saved successfully!")
    
    def cancel_changes(self):
        """Cancel changes and reload"""
        if self.current_policy_id:
            policy = self.policy_manager.get_policy(self.current_policy_id)
            if policy:
                self.load_policy_to_ui(policy)
            
            self.save_btn.setEnabled(False)
            self.cancel_btn.setEnabled(False)
    
    def import_policy(self):
        """Import a policy from file"""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Import Policy", "", "JSON files (*.json)"
        )
        
        if filepath:
            policy_id = self.policy_manager.import_policy(filepath)
            if policy_id:
                self.refresh_policy_list()
                QMessageBox.information(self, "Success", f"Policy imported as '{policy_id}'")
            else:
                QMessageBox.warning(self, "Error", "Failed to import policy")
    
    def export_policy(self):
        """Export current policy to file"""
        if self.current_policy_id:
            filepath, _ = QFileDialog.getSaveFileName(
                self, "Export Policy", f"{self.current_policy_id}.json", "JSON files (*.json)"
            )
            
            if filepath:
                if self.policy_manager.export_policy(self.current_policy_id, filepath):
                    QMessageBox.information(self, "Success", "Policy exported successfully!")
                else:
                    QMessageBox.warning(self, "Error", "Failed to export policy")
    
    def test_current_policy(self):
        """Test the current policy"""
        if not self.current_policy_id:
            return
        
        self.test_results.setPlainText("Testing policy...\n")
        self.test_progress.setVisible(True)
        self.test_progress.setValue(0)
        
        # Simulate testing with timer
        self.test_timer = QTimer()
        self.test_timer.timeout.connect(self.update_test_progress)
        self.test_timer.start(100)
        
        self.test_step = 0
    
    def update_test_progress(self):
        """Update test progress"""
        self.test_step += 1
        progress = min(self.test_step * 10, 100)
        self.test_progress.setValue(progress)
        
        if progress >= 100:
            self.test_timer.stop()
            self.test_progress.setVisible(False)
            
            # Show mock test results
            results = """Policy Test Results:
            
✅ Harmonic Rules: 8/10 tracks passed
✅ Energy Rules: 9/10 tracks passed  
⚠️  Stylistic Rules: 6/10 tracks passed
✅ Quality Rules: 10/10 tracks passed

Overall Score: 82.5%

Recommendations:
• Consider loosening stylistic compatibility requirements
• Add more variety in subgenre matching
• Policy performs well for harmonic mixing
"""
            self.test_results.setPlainText(results)
    
    # Placeholder methods for rule set and rule management
    def on_rule_set_selected(self, item):
        """Handle rule set selection"""
        pass
    
    def create_new_rule_set(self):
        """Create new rule set"""
        pass
    
    def edit_current_rule_set(self):
        """Edit current rule set"""
        pass
    
    def delete_current_rule_set(self):
        """Delete current rule set"""
        pass
    
    def on_rule_selected(self, item):
        """Handle rule selection"""
        pass
    
    def create_new_rule(self):
        """Create new rule"""
        pass
    
    def edit_current_rule(self):
        """Edit current rule"""
        pass
    
    def delete_current_rule(self):
        """Delete current rule"""
        pass


class PolicyQuickSelector(QWidget):
    """Quick policy selector widget for main UI"""
    
    policy_selected = pyqtSignal(str)  # policy_id
    
    def __init__(self, policy_manager: ConfigurablePolicyManager, parent=None):
        super().__init__(parent)
        self.policy_manager = policy_manager
        
        self.init_ui()
        self.refresh_policies()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        layout.addWidget(QLabel("Mixing Policy:"))
        
        self.policy_combo = QComboBox()
        self.policy_combo.currentTextChanged.connect(self.on_policy_changed)
        layout.addWidget(self.policy_combo)
        
        self.edit_btn = QPushButton("Edit")
        self.edit_btn.clicked.connect(self.open_policy_editor)
        layout.addWidget(self.edit_btn)
    
    def refresh_policies(self):
        """Refresh policy list"""
        self.policy_combo.clear()
        
        for policy in self.policy_manager.list_policies():
            self.policy_combo.addItem(policy.name, policy.id)
    
    def on_policy_changed(self):
        """Handle policy selection change"""
        policy_id = self.policy_combo.currentData()
        if policy_id:
            self.policy_selected.emit(policy_id)
    
    def open_policy_editor(self):
        """Open policy editor dialog"""
        from PyQt6.QtWidgets import QDialog
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Policy Editor")
        dialog.setModal(True)
        dialog.resize(1000, 700)
        
        layout = QVBoxLayout(dialog)
        
        editor = PolicyEditorWidget(self.policy_manager)
        layout.addWidget(editor)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec()
        
        # Refresh after editing
        self.refresh_policies()
    
    def get_selected_policy_id(self) -> Optional[str]:
        """Get currently selected policy ID"""
        return self.policy_combo.currentData()
    
    def set_selected_policy(self, policy_id: str):
        """Set selected policy"""
        for i in range(self.policy_combo.count()):
            if self.policy_combo.itemData(i) == policy_id:
                self.policy_combo.setCurrentIndex(i)
                break