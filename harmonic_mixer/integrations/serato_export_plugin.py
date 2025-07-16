"""
Serato DJ Pro Export Plugin
Creates playlists directly in Serato DJ library using pyserato
"""

import os
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

try:
    from pyserato.model.crate import Crate
    from pyserato.model.track import Track as SeratoTrack
    from pyserato.builder import Builder
    PYSERATO_AVAILABLE = True
except ImportError:
    PYSERATO_AVAILABLE = False
    # Define dummy classes for type hints
    class Crate:
        pass
    class SeratoTrack:
        pass

# Lazy imports to avoid circular dependencies
# from ..core.harmonic_engine import Track  
# from ..core.plugin_system import ExportPlugin, PluginType, PluginMetadata
from .serato_detector import SeratoDetector, quick_serato_check
from .serato_backup import SeratoBackupManager


@dataclass
class SeratoExportResult:
    """Result of Serato export operation"""
    success: bool
    crate_path: Optional[Path] = None
    backup_path: Optional[Path] = None
    error_message: Optional[str] = None
    tracks_exported: int = 0
    library_path: Optional[Path] = None


class SeratoExportPlugin:
    """Plugin for exporting playlists directly to Serato DJ Pro library"""
    
    def __init__(self):
        # Import here to avoid circular dependencies
        from ..core.plugin_system import PluginType, PluginMetadata
        
        self.detector = SeratoDetector()
        self.backup_manager = None
        self._metadata = PluginMetadata(
            name="Serato DJ Pro Export",
            version="1.0.0", 
            author="BlueLibrary Team",
            description="Export playlists directly to Serato DJ Pro library",
            plugin_type=PluginType.EXPORT,
            dependencies=["pyserato", "psutil"]
        )
    
    @property
    def metadata(self):
        """Return plugin metadata"""
        return self._metadata
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize plugin with configuration"""
        return PYSERATO_AVAILABLE and self.detector.is_installation_detected()
    
    def cleanup(self):
        """Cleanup plugin resources"""
        self.backup_manager = None
        
    def is_available(self) -> bool:
        """Check if Serato export is available on this system"""
        if not PYSERATO_AVAILABLE:
            return False
        
        return self.detector.is_installation_detected()
    
    def get_requirements(self) -> Dict[str, str]:
        """Get requirements for this plugin"""
        return {
            'pyserato': 'Required for creating Serato crate files',
            'serato_dj_pro': 'Serato DJ Pro must be installed',
            'library_access': 'Write access to Serato library folder'
        }
    
    def pre_export_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive pre-export checks
        Returns: Dict with status and any issues found
        """
        status = quick_serato_check()
        
        detailed_status = {
            'can_export': False,
            'issues': [],
            'warnings': [],
            'library_path': status.get('library_path'),
            'serato_running': status.get('serato_running', False),
            'running_processes': status.get('running_processes', [])
        }
        
        # Check dependencies
        if not PYSERATO_AVAILABLE:
            detailed_status['issues'].append("pyserato library not installed")
        
        # Check Serato installation
        if not status.get('library_found', False):
            detailed_status['issues'].append("Serato DJ library not found")
        
        # Check if Serato is running
        if status.get('serato_running', False):
            detailed_status['issues'].append(
                f"Serato DJ is currently running: {', '.join(status.get('running_processes', []))}"
            )
        
        # Check write permissions
        if not status.get('safe_to_modify', False):
            detailed_status['issues'].append("Cannot write to Serato library folder")
        
        # Set overall status
        detailed_status['can_export'] = len(detailed_status['issues']) == 0
        
        return detailed_status
    
    def export_playlist(
        self, 
        tracks, 
        playlist_name: str,
        options: Optional[Dict[str, Any]] = None
    ) -> SeratoExportResult:
        """
        Export playlist directly to Serato DJ Pro library
        
        Args:
            tracks: List of Track objects to export
            playlist_name: Name for the playlist/crate
            options: Additional export options
                - library_path: Override auto-detected library path
                - create_backup: Whether to create backup (default: True)
                - overwrite_existing: Whether to overwrite existing crate
        
        Returns:
            SeratoExportResult with export details
        """
        if options is None:
            options = {}
        
        # Pre-export validation
        pre_check = self.pre_export_check()
        if not pre_check['can_export']:
            return SeratoExportResult(
                success=False,
                error_message=f"Cannot export: {'; '.join(pre_check['issues'])}"
            )
        
        # Get library path
        library_path = options.get('library_path')
        if library_path:
            library_path = Path(library_path)
        else:
            library_path = self.detector.get_serato_library_path()
        
        if not library_path:
            return SeratoExportResult(
                success=False,
                error_message="No Serato library path found"
            )
        
        try:
            # Initialize backup manager
            self.backup_manager = SeratoBackupManager(library_path)
            backup_path = None
            
            # Create backup if requested
            if options.get('create_backup', True):
                backup_path = self.backup_manager.create_crate_backup(playlist_name)
                if backup_path:
                    print(f"Created backup: {backup_path}")
            
            # Prepare Serato crate
            crate = self._create_serato_crate(tracks, playlist_name)
            
            # Get subcrates path
            subcrates_path = self.detector.get_subcrates_path(library_path)
            if not subcrates_path:
                return SeratoExportResult(
                    success=False,
                    error_message="Cannot access Subcrates folder"
                )
            
            # Check for existing crate
            crate_file_path = subcrates_path / f"{playlist_name}.crate"
            if crate_file_path.exists() and not options.get('overwrite_existing', True):
                return SeratoExportResult(
                    success=False,
                    error_message=f"Crate '{playlist_name}' already exists"
                )
            
            # Save the crate using pyserato
            builder = Builder()
            # Save the crate to the subcrates directory (not the file path)
            try:
                builder.save(crate, subcrates_path, overwrite=True)
            except Exception as e:
                print(f"Error saving crate with pyserato: {e}")
                import traceback
                traceback.print_exc()
                raise
            
            # Verify the crate was created (pyserato puts it in SubCrates subdirectory)
            actual_crate_path = subcrates_path / "SubCrates" / f"{playlist_name}.crate"
            if not actual_crate_path.exists():
                # Check original location too
                if not crate_file_path.exists():
                    return SeratoExportResult(
                        success=False,
                        error_message="Crate file was not created successfully"
                    )
                actual_crate_path = crate_file_path
            
            return SeratoExportResult(
                success=True,
                crate_path=actual_crate_path,
                backup_path=backup_path,
                tracks_exported=len(tracks),
                library_path=library_path
            )
            
        except Exception as e:
            return SeratoExportResult(
                success=False,
                error_message=f"Export failed: {str(e)}"
            )
    
    def _create_serato_crate(self, tracks, crate_name: str) -> Crate:
        """
        Create a Serato crate object from tracks
        
        Args:
            tracks: List of Track objects
            crate_name: Name for the crate
            
        Returns:
            Pyserato Crate object
        """
        crate = Crate(crate_name)
        
        for i, track in enumerate(tracks):
            try:
                # Check if track is actually a Track object
                if not hasattr(track, 'filepath'):
                    print(f"Error: Track {i+1} does not have filepath attribute. Type: {type(track)}")
                    continue
                
                # Convert BlueLibrary track path to format expected by Serato
                track_path = self._format_track_path_for_serato(track.filepath)
                
                if track_path:
                    try:
                        # Create a Serato Track object using from_path for better metadata
                        serato_track = SeratoTrack.from_path(track_path)
                        crate.add_track(serato_track)
                    except Exception as e:
                        # Fallback to basic Track creation
                        try:
                            serato_track = SeratoTrack(track_path)
                            crate.add_track(serato_track)
                        except Exception as e2:
                            print(f"Warning: Could not add track {getattr(track, 'title', 'Unknown')}: {e}, {e2}")
                            continue
            except Exception as e:
                print(f"Error processing track {i+1}: {e}")
                continue
        
        return crate
    
    def _format_track_path_for_serato(self, file_path: str) -> Optional[str]:
        """
        Format a file path for Serato compatibility
        
        Args:
            file_path: Original file path
            
        Returns:
            Formatted path string or None if invalid
        """
        if not file_path:
            return None
        
        try:
            # Convert to Path object for better handling
            path_obj = Path(file_path)
            
            # Check if file exists
            if not path_obj.exists():
                print(f"Warning: File does not exist: {file_path}")
                return None
            
            # Get resolved absolute path - this is what works with Serato!
            resolved_path = path_obj.resolve()
            
            # Return absolute path (this is what Working_Test_Abs proved works)
            return str(resolved_path)
            
        except Exception as e:
            print(f"Error formatting path {file_path}: {e}")
            return None
    
    def list_existing_crates(self, library_path: Optional[Path] = None) -> List[str]:
        """
        List all existing crates in Serato library
        
        Args:
            library_path: Override library path
            
        Returns:
            List of crate names
        """
        if library_path is None:
            library_path = self.detector.get_serato_library_path()
        
        if library_path:
            return self.detector.list_existing_crates(library_path)
        
        return []
    
    def delete_crate(self, crate_name: str, library_path: Optional[Path] = None) -> bool:
        """
        Delete a crate from Serato library
        
        Args:
            crate_name: Name of crate to delete
            library_path: Override library path
            
        Returns:
            True if deleted successfully
        """
        if library_path is None:
            library_path = self.detector.get_serato_library_path()
        
        if not library_path:
            return False
        
        try:
            subcrates_path = self.detector.get_subcrates_path(library_path)
            if subcrates_path:
                crate_file_path = subcrates_path / f"{crate_name}.crate"
                if crate_file_path.exists():
                    # Create backup before deletion
                    if self.backup_manager:
                        self.backup_manager.create_crate_backup(crate_name)
                    
                    crate_file_path.unlink()
                    return True
        except Exception as e:
            print(f"Error deleting crate {crate_name}: {e}")
        
        return False
    
    def get_export_options(self) -> Dict[str, Any]:
        """
        Get available export options for UI
        
        Returns:
            Dict with option definitions
        """
        return {
            'create_backup': {
                'type': 'boolean',
                'default': True,
                'description': 'Create backup before export'
            },
            'overwrite_existing': {
                'type': 'boolean', 
                'default': True,
                'description': 'Overwrite existing crate with same name'
            },
            'library_path': {
                'type': 'path',
                'default': None,
                'description': 'Custom Serato library path (auto-detected if empty)'
            }
        }
    
    def get_status_info(self) -> Dict[str, Any]:
        """
        Get current status information for UI display
        
        Returns:
            Dict with status information
        """
        status = quick_serato_check()
        
        return {
            'plugin_available': self.is_available(),
            'serato_detected': status.get('library_found', False),
            'serato_running': status.get('serato_running', False),
            'library_path': status.get('library_path'),
            'can_export_now': status.get('safe_to_modify', False),
            'existing_crates_count': len(self.list_existing_crates()),
            'pyserato_available': PYSERATO_AVAILABLE
        }


def create_serato_export_plugin():
    """Factory function to create Serato export plugin"""
    # Import the base classes here to avoid circular imports
    from ..core.plugin_system import ExportPlugin
    
    # Create a dynamic class that inherits from ExportPlugin
    class SeratoExportPluginInstance(SeratoExportPlugin, ExportPlugin):
        pass
    
    return SeratoExportPluginInstance()


if __name__ == "__main__":
    # Test the plugin
    plugin = SeratoExportPlugin()
    
    print("=== Serato Export Plugin Test ===")
    print(f"Plugin Available: {plugin.is_available()}")
    
    # Get status
    status = plugin.get_status_info()
    print(f"Status: {status}")
    
    # Pre-export check
    pre_check = plugin.pre_export_check()
    print(f"Pre-export Check: {pre_check}")
    
    # List existing crates
    crates = plugin.list_existing_crates()
    print(f"Existing Crates: {len(crates)}")
    if crates:
        print(f"  Examples: {', '.join(crates[:5])}")
    
    # Get export options
    options = plugin.get_export_options()
    print(f"Export Options: {list(options.keys())}")