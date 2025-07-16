#!/usr/bin/env python3
"""
BlueLibrary - Advanced Harmonic Mixer
Main entry point for the application
"""

import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QLoggingCategory, Qt
from harmonic_mixer.ui import MainWindow

# Suppress Qt multimedia info messages
QLoggingCategory.setFilterRules("qt.multimedia.ffmpeg=false")


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("BlueLibrary")
    app.setOrganizationName("BlueLibrary")
    
    # Optimize rendering to reduce repaint warnings
    app.setAttribute(Qt.ApplicationAttribute.AA_DontCreateNativeWidgetSiblings, True)
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()