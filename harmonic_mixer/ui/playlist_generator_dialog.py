"""
Mobile-optimized Playlist Generator Dialog
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QDialogButtonBox,
    QMessageBox, QFileDialog, QApplication, QPushButton
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QKeySequence, QShortcut

from .playlist_generator_widget import PlaylistGeneratorWidget
from ..core.harmonic_engine import Track
from typing import List, Optional


class PlaylistGeneratorDialog(QDialog):
    """Mobile-friendly dialog for playlist generation"""
    playlist_created = pyqtSignal(list)  # Emitted when playlist is created
    
    def __init__(self, facade, parent=None):
        super().__init__(parent)
        self.facade = facade
        self.current_playlist = []
        self.init_ui()
        self.setup_shortcuts()
        
    def init_ui(self):
        self.setWindowTitle("Generate Playlist")
        self.setModal(True)
        
        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Add the playlist generator widget
        self.generator_widget = PlaylistGeneratorWidget(self.facade)
        self.generator_widget.playlist_generated.connect(self.on_playlist_generated)
        self.generator_widget.generation_started.connect(self.on_generation_started)
        self.generator_widget.generation_completed.connect(self.on_generation_completed)
        layout.addWidget(self.generator_widget)
        
        # Dialog buttons
        self.button_box = QDialogButtonBox()
        self.button_box.setStandardButtons(
            QDialogButtonBox.StandardButton.Close
        )
        
        # Add custom buttons
        self.apply_btn = self.button_box.addButton(
            "Apply Playlist", QDialogButtonBox.ButtonRole.ApplyRole
        )
        self.apply_btn.setEnabled(False)
        self.apply_btn.clicked.connect(self.apply_playlist)
        
        self.export_btn = self.button_box.addButton(
            "Export...", QDialogButtonBox.ButtonRole.ActionRole
        )
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self.export_playlist)
        
        self.button_box.rejected.connect(self.reject)
        
        # Style the button box
        self.button_box.setStyleSheet("""
            QDialogButtonBox {
                background-color: #f8f9fa;
                border-top: 1px solid #ddd;
                padding: 10px;
            }
        """)
        
        layout.addWidget(self.button_box)
        self.setLayout(layout)
        
        # Set dialog size based on screen
        self.setup_responsive_size()
        
        # Enable/disable generate button based on track availability
        tracks = self.facade.get_tracks()
        self.generator_widget.set_tracks_available(len(tracks) > 0)
    
    def setup_responsive_size(self):
        """Set dialog size based on screen dimensions"""
        screen = QApplication.primaryScreen()
        screen_size = screen.size()
        
        # Mobile screens (width < 768px)
        if screen_size.width() < 768:
            # Full screen on mobile
            self.setWindowState(Qt.WindowState.WindowMaximized)
            self.setStyleSheet("""
                QDialog {
                    background-color: white;
                }
            """)
        
        # Tablet screens (768px <= width < 1200px)
        elif screen_size.width() < 1200:
            # 90% of screen size on tablets
            width = int(screen_size.width() * 0.9)
            height = int(screen_size.height() * 0.85)
            self.resize(width, height)
            
            # Center on screen
            self.move(
                (screen_size.width() - width) // 2,
                (screen_size.height() - height) // 2
            )
        
        # Desktop screens (width >= 1200px)
        else:
            # Fixed size on desktop
            self.resize(900, 700)
            
            # Center on parent or screen
            if self.parent():
                parent_rect = self.parent().geometry()
                self.move(
                    parent_rect.center().x() - self.width() // 2,
                    parent_rect.center().y() - self.height() // 2
                )
    
    def setup_shortcuts(self):
        """Setup keyboard shortcuts for accessibility"""
        # Escape to close
        QShortcut(QKeySequence.StandardKey.Cancel, self, self.reject)
        
        # Ctrl+G to generate
        generate_shortcut = QShortcut(QKeySequence("Ctrl+G"), self)
        generate_shortcut.activated.connect(
            self.generator_widget.generate_playlist
        )
        
        # Ctrl+E to export
        export_shortcut = QShortcut(QKeySequence("Ctrl+E"), self)
        export_shortcut.activated.connect(self.export_playlist)
        
        # Ctrl+Return to apply
        apply_shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        apply_shortcut.activated.connect(self.apply_playlist)
    
    def on_playlist_generated(self, playlist: List[Track]):
        """Handle playlist generation completion"""
        self.current_playlist = playlist
        self.apply_btn.setEnabled(True)
        self.export_btn.setEnabled(True)
        
        # Show notification
        self.show_notification(
            f"Successfully generated {len(playlist)} track playlist!"
        )
    
    def on_generation_started(self):
        """Handle generation start"""
        self.apply_btn.setEnabled(False)
        self.button_box.button(
            QDialogButtonBox.StandardButton.Close
        ).setEnabled(False)
    
    def on_generation_completed(self):
        """Handle generation completion"""
        self.button_box.button(
            QDialogButtonBox.StandardButton.Close
        ).setEnabled(True)
    
    def apply_playlist(self):
        """Apply the generated playlist and close"""
        if self.current_playlist:
            self.playlist_created.emit(self.current_playlist)
            self.accept()
    
    def export_playlist(self):
        """Export the current playlist"""
        if not self.current_playlist:
            return
        
        # Get export format
        file_filter = "M3U Playlist (*.m3u);;CSV File (*.csv);;Text File (*.txt)"
        filename, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Export Playlist",
            "playlist.m3u",
            file_filter
        )
        
        if filename:
            try:
                if selected_filter.startswith("M3U"):
                    self.export_m3u(filename)
                elif selected_filter.startswith("CSV"):
                    self.export_csv(filename)
                else:
                    self.export_text(filename)
                
                self.show_notification(f"Playlist exported to {filename}")
                
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Export Error",
                    f"Failed to export playlist: {str(e)}"
                )
    
    def export_m3u(self, filename: str):
        """Export playlist as M3U file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("#EXTM3U\n")
                for track in self.current_playlist:
                    # Write extended info
                    duration = int(track.duration) if hasattr(track, 'duration') and track.duration else -1
                    artist = getattr(track, 'artist', 'Unknown Artist')
                    title = getattr(track, 'title', 'Unknown Title')
                    file_path = getattr(track, 'file_path', '') or getattr(track, 'filepath', '')
                    
                    f.write(f"#EXTINF:{duration},{artist} - {title}\n")
                    f.write(f"{file_path}\n")
        except PermissionError:
            raise Exception(f"Permission denied writing to {filename}")
        except Exception as e:
            raise Exception(f"Failed to write M3U file: {str(e)}")
    
    def export_csv(self, filename: str):
        """Export playlist as CSV file"""
        import csv
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                # Write header
                writer.writerow([
                    "Position", "Title", "Artist", "Key", "BPM", 
                    "Energy", "File Path"
                ])
                
                # Write tracks
                for i, track in enumerate(self.current_playlist, 1):
                    writer.writerow([
                        i,
                        getattr(track, 'title', 'Unknown Title'),
                        getattr(track, 'artist', 'Unknown Artist'),
                        getattr(track, 'key', ''),
                        getattr(track, 'bpm', ''),
                        getattr(track, 'energy', ''),
                        getattr(track, 'file_path', '') or getattr(track, 'filepath', '')
                    ])
        except PermissionError:
            raise Exception(f"Permission denied writing to {filename}")
        except Exception as e:
            raise Exception(f"Failed to write CSV file: {str(e)}")
    
    def export_text(self, filename: str):
        """Export playlist as text file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("Generated Playlist\n")
                f.write("=" * 50 + "\n\n")
                
                for i, track in enumerate(self.current_playlist, 1):
                    title = getattr(track, 'title', 'Unknown Title')
                    artist = getattr(track, 'artist', 'Unknown Artist')
                    key = getattr(track, 'key', 'Unknown')
                    bpm = getattr(track, 'bpm', 'Unknown')
                    energy = getattr(track, 'energy', 'Unknown')
                    file_path = getattr(track, 'file_path', '') or getattr(track, 'filepath', 'Unknown')
                    
                    f.write(f"{i}. {title} - {artist}\n")
                    f.write(f"   Key: {key}, BPM: {bpm}\n")
                    f.write(f"   Energy: {energy}/10\n")
                    f.write(f"   File: {file_path}\n\n")
        except PermissionError:
            raise Exception(f"Permission denied writing to {filename}")
        except Exception as e:
            raise Exception(f"Failed to write text file: {str(e)}")
    
    def show_notification(self, message: str):
        """Show a temporary notification"""
        # You could implement a toast-style notification here
        # For now, using the status message in the parent window
        if self.parent() and hasattr(self.parent(), 'status_bar'):
            self.parent().status_bar.show_success(message)
    
    def keyPressEvent(self, event):
        """Handle key press events for better mobile navigation"""
        # On mobile, hardware back button often sends Escape
        if event.key() == Qt.Key.Key_Escape:
            # If generation is in progress, confirm before closing
            if hasattr(self.generator_widget, 'is_generating') and \
               self.generator_widget.is_generating:
                reply = QMessageBox.question(
                    self,
                    "Generation in Progress",
                    "Playlist generation is still in progress. Cancel?",
                    QMessageBox.StandardButton.Yes | 
                    QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    super().keyPressEvent(event)
            else:
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)


class CompactPlaylistGenerator(QDialog):
    """Ultra-compact version for small screens"""
    playlist_created = pyqtSignal(list)
    
    def __init__(self, facade, parent=None):
        super().__init__(parent)
        self.facade = facade
        self.setWindowTitle("Quick Playlist")
        self.setModal(True)
        
        # For very small screens, provide a simplified interface
        layout = QVBoxLayout()
        
        # Simple preset buttons
        presets = [
            ("Party Mix (20 tracks)", "ascending", 20),
            ("Chill Session (15 tracks)", "neutral", 15),
            ("Workout Mix (25 tracks)", "peak", 25),
            ("Quick Mix (10 tracks)", "neutral", 10)
        ]
        
        for name, curve, length in presets:
            btn = QPushButton(name)
            btn.setMinimumHeight(50)
            btn.clicked.connect(
                lambda checked, c=curve, l=length: self.quick_generate(c, l)
            )
            layout.addWidget(btn)
        
        # Close button
        close_btn = QPushButton("Cancel")
        close_btn.clicked.connect(self.reject)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)
        self.resize(300, 400)
    
    def quick_generate(self, curve: str, length: int):
        """Quick playlist generation with preset"""
        try:
            playlist = self.facade.generate_playlist(length, curve)
            if playlist:
                self.playlist_created.emit(playlist)
                self.accept()
            else:
                QMessageBox.warning(
                    self,
                    "Generation Failed",
                    "Could not generate playlist. Please try again."
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"An error occurred: {str(e)}"
            )