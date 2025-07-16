"""
Centralized UI Theme and Color Definitions
Ensures consistent styling across all BlueLibrary components
"""

from typing import Dict


class BlueLibraryTheme:
    """Central theme configuration for BlueLibrary"""
    
    # Core Colors
    BACKGROUND_PRIMARY = "#1e1e1e"      # Main window background
    BACKGROUND_SECONDARY = "#2d2d2d"    # Widget backgrounds
    BACKGROUND_TERTIARY = "#3d3d3d"     # Borders, separators
    
    # Text Colors
    TEXT_PRIMARY = "#ffffff"            # Main text
    TEXT_SECONDARY = "#cccccc"          # Secondary text
    TEXT_DISABLED = "#666666"           # Disabled text
    
    # Accent Colors
    ACCENT_PRIMARY = "#4a90e2"          # Main blue accent
    ACCENT_HOVER = "#5ba0f2"           # Hover state
    ACCENT_PRESSED = "#3a80d2"         # Pressed state
    
    # Status Colors
    SUCCESS = "#4a9d4a"                # Success green
    WARNING = "#d4a853"                # Warning yellow
    ERROR = "#d9534f"                  # Error red
    INFO = "#5bc0de"                   # Info cyan
    
    # Info Section Colors (Dark Theme Variants)
    INFO_BACKGROUND_BLUE = "#2a3a4a"   # Dark blue info sections
    INFO_BACKGROUND_GREEN = "#2a4a2a"  # Dark green info sections  
    INFO_BACKGROUND_YELLOW = "#4a4a2a" # Dark yellow info sections
    INFO_BACKGROUND_NEUTRAL = "#3a3a3a" # Neutral dark info sections
    
    @classmethod
    def get_main_window_stylesheet(cls) -> str:
        """Get stylesheet for main window"""
        return f"""
            QMainWindow {{
                background-color: {cls.BACKGROUND_PRIMARY};
            }}
            QWidget {{
                background-color: {cls.BACKGROUND_SECONDARY};
                color: {cls.TEXT_PRIMARY};
            }}
            QTableWidget {{
                background-color: {cls.BACKGROUND_PRIMARY};
                alternate-background-color: {cls.BACKGROUND_SECONDARY};
                gridline-color: {cls.BACKGROUND_TERTIARY};
            }}
            QTableWidget::item:selected {{
                background-color: {cls.ACCENT_PRIMARY};
            }}
            QPushButton {{
                background-color: {cls.ACCENT_PRIMARY};
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
                color: {cls.TEXT_PRIMARY};
            }}
            QPushButton:hover {{
                background-color: {cls.ACCENT_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {cls.ACCENT_PRESSED};
            }}
            QPushButton:disabled {{
                background-color: {cls.BACKGROUND_TERTIARY};
                color: {cls.TEXT_DISABLED};
            }}
            QGroupBox {{
                border: 1px solid {cls.BACKGROUND_TERTIARY};
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
                color: {cls.TEXT_PRIMARY};
            }}
            QGroupBox::title {{
                padding: 0 5px;
                left: 10px;
                top: -5px;
                color: {cls.TEXT_PRIMARY};
            }}
            QSlider::groove:horizontal {{
                height: 6px;
                background: {cls.BACKGROUND_TERTIARY};
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {cls.ACCENT_PRIMARY};
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {cls.ACCENT_HOVER};
            }}
            QProgressBar {{
                border: 1px solid {cls.BACKGROUND_TERTIARY};
                border-radius: 4px;
                text-align: center;
                color: {cls.TEXT_PRIMARY};
            }}
            QProgressBar::chunk {{
                background-color: {cls.ACCENT_PRIMARY};
                border-radius: 3px;
            }}
        """
    
    @classmethod
    def get_dialog_stylesheet(cls) -> str:
        """Get stylesheet for dialogs"""
        return f"""
            QDialog {{
                background-color: {cls.BACKGROUND_PRIMARY};
                color: {cls.TEXT_PRIMARY};
            }}
            QWidget {{
                background-color: {cls.BACKGROUND_SECONDARY};
                color: {cls.TEXT_PRIMARY};
            }}
            
            /* Tab Widget Styling */
            QTabWidget::pane {{
                border: 1px solid {cls.BACKGROUND_TERTIARY};
                background-color: {cls.BACKGROUND_SECONDARY};
            }}
            QTabBar::tab {{
                background-color: {cls.BACKGROUND_TERTIARY};
                color: {cls.TEXT_SECONDARY};
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }}
            QTabBar::tab:selected {{
                background-color: {cls.ACCENT_PRIMARY};
                color: {cls.TEXT_PRIMARY};
                font-weight: bold;
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {cls.ACCENT_HOVER};
                color: {cls.TEXT_PRIMARY};
            }}
            
            /* Form Controls */
            QLabel {{
                color: {cls.TEXT_PRIMARY};
                background-color: transparent;
            }}
            
            QLineEdit {{
                background-color: {cls.BACKGROUND_PRIMARY};
                border: 1px solid {cls.BACKGROUND_TERTIARY};
                border-radius: 4px;
                padding: 6px;
                color: {cls.TEXT_PRIMARY};
            }}
            QLineEdit:focus {{
                border: 2px solid {cls.ACCENT_PRIMARY};
            }}
            QLineEdit:disabled {{
                background-color: {cls.BACKGROUND_TERTIARY};
                color: {cls.TEXT_DISABLED};
            }}
            
            QComboBox {{
                background-color: {cls.BACKGROUND_PRIMARY};
                border: 1px solid {cls.BACKGROUND_TERTIARY};
                border-radius: 4px;
                padding: 6px;
                color: {cls.TEXT_PRIMARY};
            }}
            QComboBox:hover {{
                border: 1px solid {cls.ACCENT_PRIMARY};
            }}
            QComboBox:disabled {{
                background-color: {cls.BACKGROUND_TERTIARY};
                color: {cls.TEXT_DISABLED};
            }}
            QComboBox::drop-down {{
                border: none;
                background-color: {cls.ACCENT_PRIMARY};
                border-top-right-radius: 4px;
                border-bottom-right-radius: 4px;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid {cls.TEXT_PRIMARY};
                margin-left: 5px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {cls.BACKGROUND_SECONDARY};
                border: 1px solid {cls.BACKGROUND_TERTIARY};
                selection-background-color: {cls.ACCENT_PRIMARY};
                color: {cls.TEXT_PRIMARY};
            }}
            
            QSpinBox, QDoubleSpinBox {{
                background-color: {cls.BACKGROUND_PRIMARY};
                border: 1px solid {cls.BACKGROUND_TERTIARY};
                border-radius: 4px;
                padding: 6px;
                color: {cls.TEXT_PRIMARY};
            }}
            QSpinBox:focus, QDoubleSpinBox:focus {{
                border: 2px solid {cls.ACCENT_PRIMARY};
            }}
            QSpinBox:disabled, QDoubleSpinBox:disabled {{
                background-color: {cls.BACKGROUND_TERTIARY};
                color: {cls.TEXT_DISABLED};
            }}
            
            QCheckBox {{
                color: {cls.TEXT_PRIMARY};
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 1px solid {cls.BACKGROUND_TERTIARY};
                border-radius: 3px;
                background-color: {cls.BACKGROUND_PRIMARY};
            }}
            QCheckBox::indicator:checked {{
                background-color: {cls.ACCENT_PRIMARY};
                border: 1px solid {cls.ACCENT_PRIMARY};
            }}
            QCheckBox::indicator:hover {{
                border: 1px solid {cls.ACCENT_PRIMARY};
            }}
            QCheckBox:disabled {{
                color: {cls.TEXT_DISABLED};
            }}
            
            /* Buttons */
            QPushButton {{
                background-color: {cls.ACCENT_PRIMARY};
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                color: {cls.TEXT_PRIMARY};
            }}
            QPushButton:hover {{
                background-color: {cls.ACCENT_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {cls.ACCENT_PRESSED};
            }}
            QPushButton:disabled {{
                background-color: {cls.BACKGROUND_TERTIARY};
                color: {cls.TEXT_DISABLED};
            }}
            
            /* Group Boxes */
            QGroupBox {{
                border: 1px solid {cls.BACKGROUND_TERTIARY};
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
                color: {cls.TEXT_PRIMARY};
            }}
            QGroupBox::title {{
                padding: 0 5px;
                left: 10px;
                top: -5px;
                color: {cls.TEXT_PRIMARY};
            }}
            
            /* Sliders */
            QSlider::groove:horizontal {{
                height: 6px;
                background: {cls.BACKGROUND_TERTIARY};
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {cls.ACCENT_PRIMARY};
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {cls.ACCENT_HOVER};
            }}
            QSlider:disabled {{
                opacity: 0.5;
            }}
            
            /* Text Areas */
            QTextEdit {{
                background-color: {cls.BACKGROUND_PRIMARY};
                border: 1px solid {cls.BACKGROUND_TERTIARY};
                border-radius: 4px;
                color: {cls.TEXT_PRIMARY};
                padding: 8px;
            }}
            QTextEdit:focus {{
                border: 2px solid {cls.ACCENT_PRIMARY};
            }}
        """
    
    @classmethod
    def get_info_section_style(cls, section_type: str = "neutral") -> str:
        """Get style for information sections"""
        color_map = {
            "neutral": cls.INFO_BACKGROUND_NEUTRAL,
            "blue": cls.INFO_BACKGROUND_BLUE,
            "green": cls.INFO_BACKGROUND_GREEN,
            "yellow": cls.INFO_BACKGROUND_YELLOW,
            "success": cls.INFO_BACKGROUND_GREEN,
            "warning": cls.INFO_BACKGROUND_YELLOW,
            "info": cls.INFO_BACKGROUND_BLUE
        }
        
        background_color = color_map.get(section_type, cls.INFO_BACKGROUND_NEUTRAL)
        
        return f"""
            padding: 15px;
            background-color: {background_color};
            border: 1px solid {cls.BACKGROUND_TERTIARY};
            border-radius: 6px;
            color: {cls.TEXT_PRIMARY};
            font-weight: normal;
        """
    
    @classmethod
    def get_status_colors(cls) -> Dict[str, str]:
        """Get status color mapping"""
        return {
            "success": cls.SUCCESS,
            "warning": cls.WARNING,
            "error": cls.ERROR,
            "info": cls.INFO,
            "primary": cls.ACCENT_PRIMARY
        }