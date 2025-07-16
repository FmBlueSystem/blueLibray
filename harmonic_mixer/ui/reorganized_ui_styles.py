"""
Enhanced Styles for Reorganized UI
Provides additional styling for the new tabbed interface and compact toolbar
"""

from .enhanced_theme import ModernBlueLibraryTheme as BlueLibraryTheme


class ReorganizedUIStyles:
    """Styles for the reorganized UI components"""
    
    @staticmethod
    def get_main_window_enhancements():
        """Get enhanced styles for the main window with new layout"""
        return f"""
            /* Main Window Enhancements */
            QMainWindow {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {BlueLibraryTheme.BACKGROUND_PRIMARY}, 
                    stop:1 {BlueLibraryTheme.BACKGROUND_SECONDARY});
                border: none;
            }}
            
            QMainWindow::separator {{
                width: 2px;
                background: {BlueLibraryTheme.ACCENT_PRIMARY};
                border: none;
            }}
            
            QMainWindow::separator:hover {{
                background: {BlueLibraryTheme.ACCENT_SECONDARY};
            }}
            
            /* Central Widget Enhancements */
            QWidget#centralWidget {{
                background: transparent;
                border: none;
                padding: 5px;
            }}
            
            /* Splitter Enhancements */
            QSplitter::handle {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {BlueLibraryTheme.ACCENT_PRIMARY}, 
                    stop:1 {BlueLibraryTheme.ACCENT_SECONDARY});
                border: 1px solid {BlueLibraryTheme.ACCENT_PRIMARY};
                border-radius: 2px;
                margin: 2px;
            }}
            
            QSplitter::handle:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {BlueLibraryTheme.ACCENT_SECONDARY}, 
                    stop:1 {BlueLibraryTheme.ACCENT_PRIMARY});
            }}
            
            QSplitter::handle:horizontal {{
                width: 6px;
                min-width: 6px;
                max-width: 6px;
            }}
            
            QSplitter::handle:vertical {{
                height: 6px;
                min-height: 6px;
                max-height: 6px;
            }}
        """
    
    @staticmethod
    def get_compact_toolbar_styles():
        """Get styles for the compact toolbar"""
        return f"""
            /* Compact Toolbar Styles */
            CompactToolbar {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {BlueLibraryTheme.SURFACE_HIGH}, 
                    stop:1 {BlueLibraryTheme.SURFACE_MEDIUM});
                border: 2px solid {BlueLibraryTheme.ACCENT_PRIMARY};
                border-radius: 10px;
                padding: 8px;
                margin: 2px;
            }}
            
            CompactToolbar QFrame[frameShape="5"] {{
                color: {BlueLibraryTheme.ACCENT_PRIMARY};
                background: {BlueLibraryTheme.ACCENT_PRIMARY};
                max-width: 2px;
                min-width: 2px;
                margin: 8px 5px;
                border-radius: 1px;
            }}
            
            CompactToolbar QLabel {{
                color: {BlueLibraryTheme.TEXT_PRIMARY};
                font-size: 12px;
                font-weight: 600;
                padding: 2px 4px;
                background: transparent;
                border: none;
            }}
            
            CompactToolbar QWidget[id^="section_"] {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {BlueLibraryTheme.SURFACE_MEDIUM}, 
                    stop:1 {BlueLibraryTheme.SURFACE_LOW});
                border: 1px solid {BlueLibraryTheme.ACCENT_PRIMARY};
                border-radius: 6px;
                padding: 4px;
                margin: 0px 2px;
            }}
            
            /* Quick Action Panel Styles */
            QuickActionPanel {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {BlueLibraryTheme.SURFACE_MEDIUM}, 
                    stop:1 {BlueLibraryTheme.SURFACE_LOW});
                border: 1px solid {BlueLibraryTheme.ACCENT_PRIMARY};
                border-radius: 8px;
                padding: 4px;
                margin: 2px;
            }}
            
            QuickActionPanel QFrame[frameShape="5"] {{
                color: {BlueLibraryTheme.ACCENT_PRIMARY};
                background: {BlueLibraryTheme.ACCENT_PRIMARY};
                max-width: 1px;
                min-width: 1px;
                margin: 4px 3px;
                border-radius: 1px;
            }}
        """
    
    @staticmethod
    def get_tabbed_panel_styles():
        """Get styles for the tabbed control panel"""
        return f"""
            /* Tabbed Control Panel Styles */
            TabbedControlPanel {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {BlueLibraryTheme.SURFACE_MEDIUM}, 
                    stop:1 {BlueLibraryTheme.SURFACE_LOW});
                border: 2px solid {BlueLibraryTheme.ACCENT_PRIMARY};
                border-radius: 10px;
                padding: 5px;
                margin: 2px;
            }}
            
            TabbedControlPanel QTabWidget::pane {{
                background: {BlueLibraryTheme.SURFACE_LOW};
                border: 1px solid {BlueLibraryTheme.ACCENT_PRIMARY};
                border-radius: 8px;
                padding: 8px;
                margin: 2px;
            }}
            
            TabbedControlPanel QTabBar::tab {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {BlueLibraryTheme.SURFACE_MEDIUM}, 
                    stop:1 {BlueLibraryTheme.SURFACE_LOW});
                border: 1px solid {BlueLibraryTheme.ACCENT_PRIMARY};
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                padding: 10px 15px;
                margin-right: 2px;
                color: {BlueLibraryTheme.TEXT_PRIMARY};
                font-weight: 600;
                font-size: 13px;
                min-width: 80px;
            }}
            
            TabbedControlPanel QTabBar::tab:selected {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {BlueLibraryTheme.ACCENT_PRIMARY}, 
                    stop:1 {BlueLibraryTheme.SURFACE_LOW});
                color: {BlueLibraryTheme.TEXT_PRIMARY};
                font-weight: 700;
                border-bottom: 2px solid {BlueLibraryTheme.SURFACE_LOW};
            }}
            
            TabbedControlPanel QTabBar::tab:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {BlueLibraryTheme.SURFACE_HIGH}, 
                    stop:1 {BlueLibraryTheme.SURFACE_MEDIUM});
            }}
            
            TabbedControlPanel QTabBar::tab:!selected {{
                margin-top: 2px;
            }}
            
            /* Tab Content Styles */
            TabbedControlPanel QWidget {{
                background: transparent;
                border: none;
            }}
            
            TabbedControlPanel QGroupBox {{
                font-weight: 600;
                font-size: 12px;
                color: {BlueLibraryTheme.TEXT_ACCENT};
                border: 1px solid {BlueLibraryTheme.ACCENT_PRIMARY};
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 6px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {BlueLibraryTheme.SURFACE_MEDIUM}, 
                    stop:1 {BlueLibraryTheme.SURFACE_LOW});
            }}
            
            TabbedControlPanel QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                background: {BlueLibraryTheme.SURFACE_LOW};
                border: 1px solid {BlueLibraryTheme.ACCENT_PRIMARY};
                border-radius: 4px;
                font-weight: 700;
                color: {BlueLibraryTheme.TEXT_ACCENT};
            }}
        """
    
    @staticmethod
    def get_enhanced_table_styles():
        """Get enhanced styles for the track table with more space"""
        return f"""
            /* Enhanced Track Table Styles */
            QTableWidget, VirtualTableWidget, OptimizedTrackView {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {BlueLibraryTheme.SURFACE_LOW}, 
                    stop:1 {BlueLibraryTheme.SURFACE_MEDIUM});
                border: 2px solid {BlueLibraryTheme.ACCENT_PRIMARY};
                border-radius: 12px;
                gridline-color: {BlueLibraryTheme.BACKGROUND_TERTIARY};
                selection-background-color: {BlueLibraryTheme.ACCENT_PRIMARY};
                font-size: 13px;
                padding: 5px;
            }}
            
            QTableWidget::item, VirtualTableWidget::item {{
                padding: 12px 10px;
                border: none;
                color: {BlueLibraryTheme.TEXT_PRIMARY};
                background: transparent;
            }}
            
            QTableWidget::item:selected, VirtualTableWidget::item:selected {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {BlueLibraryTheme.ACCENT_PRIMARY}, 
                    stop:1 {BlueLibraryTheme.ACCENT_SECONDARY});
                color: {BlueLibraryTheme.TEXT_PRIMARY};
                border-radius: 8px;
                font-weight: 600;
                padding: 12px 10px;
            }}
            
            QTableWidget::item:hover, VirtualTableWidget::item:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {BlueLibraryTheme.SURFACE_HIGH}, 
                    stop:1 {BlueLibraryTheme.SURFACE_MEDIUM});
                border-radius: 6px;
            }}
            
            QTableWidget::item:alternate, VirtualTableWidget::item:alternate {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {BlueLibraryTheme.SURFACE_MEDIUM}, 
                    stop:1 {BlueLibraryTheme.SURFACE_LOW});
            }}
            
            /* Header Styles */
            QHeaderView::section {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {BlueLibraryTheme.SURFACE_HIGH}, 
                    stop:1 {BlueLibraryTheme.SURFACE_MEDIUM});
                border: 1px solid {BlueLibraryTheme.ACCENT_PRIMARY};
                border-left: none;
                border-top: none;
                padding: 12px 8px;
                font-weight: 700;
                font-size: 13px;
                color: {BlueLibraryTheme.TEXT_ACCENT};
            }}
            
            QHeaderView::section:first {{
                border-left: 1px solid {BlueLibraryTheme.ACCENT_PRIMARY};
                border-top-left-radius: 8px;
            }}
            
            QHeaderView::section:last {{
                border-top-right-radius: 8px;
            }}
            
            QHeaderView::section:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {BlueLibraryTheme.ACCENT_SECONDARY}, 
                    stop:1 {BlueLibraryTheme.SURFACE_HIGH});
            }}
            
            /* Scrollbar Styles */
            QScrollBar:vertical {{
                background: {BlueLibraryTheme.SURFACE_LOW};
                border: 1px solid {BlueLibraryTheme.ACCENT_PRIMARY};
                border-radius: 6px;
                width: 12px;
                margin: 0px;
            }}
            
            QScrollBar::handle:vertical {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {BlueLibraryTheme.ACCENT_PRIMARY}, 
                    stop:1 {BlueLibraryTheme.ACCENT_SECONDARY});
                border: 1px solid {BlueLibraryTheme.ACCENT_PRIMARY};
                border-radius: 5px;
                min-height: 20px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {BlueLibraryTheme.ACCENT_SECONDARY}, 
                    stop:1 {BlueLibraryTheme.ACCENT_PRIMARY});
            }}
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                background: {BlueLibraryTheme.SURFACE_MEDIUM};
                border: 1px solid {BlueLibraryTheme.ACCENT_PRIMARY};
                border-radius: 3px;
                height: 12px;
            }}
            
            QScrollBar::add-line:vertical:hover, QScrollBar::sub-line:vertical:hover {{
                background: {BlueLibraryTheme.SURFACE_HIGH};
            }}
            
            QScrollBar:horizontal {{
                background: {BlueLibraryTheme.SURFACE_LOW};
                border: 1px solid {BlueLibraryTheme.ACCENT_PRIMARY};
                border-radius: 6px;
                height: 12px;
                margin: 0px;
            }}
            
            QScrollBar::handle:horizontal {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {BlueLibraryTheme.ACCENT_PRIMARY}, 
                    stop:1 {BlueLibraryTheme.ACCENT_SECONDARY});
                border: 1px solid {BlueLibraryTheme.ACCENT_PRIMARY};
                border-radius: 5px;
                min-width: 20px;
            }}
            
            QScrollBar::handle:horizontal:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {BlueLibraryTheme.ACCENT_SECONDARY}, 
                    stop:1 {BlueLibraryTheme.ACCENT_PRIMARY});
            }}
        """
    
    @staticmethod
    def get_combined_styles():
        """Get all combined styles for the reorganized UI"""
        return (
            ReorganizedUIStyles.get_main_window_enhancements() +
            ReorganizedUIStyles.get_compact_toolbar_styles() +
            ReorganizedUIStyles.get_tabbed_panel_styles() +
            ReorganizedUIStyles.get_enhanced_table_styles()
        )