"""
Serato DJ Pro Detection and Validation System
Detects installation, running processes, and library locations
"""

import os
import psutil
from pathlib import Path
from typing import Optional, List, Dict, Tuple
import platform


class SeratoDetector:
    """Detects Serato DJ Pro installation and status"""
    
    def __init__(self):
        self.platform = platform.system()
        self.serato_processes = [
            "Serato DJ Pro",
            "Serato DJ Lite", 
            "Serato DJ",
            "ScratchLive",
            "serato_dj_pro",
            "serato_dj_lite"
        ]
    
    def is_serato_running(self) -> Tuple[bool, List[str]]:
        """
        Check if any Serato process is currently running
        Returns: (is_running, list_of_running_processes)
        """
        running_processes = []
        
        try:
            for process in psutil.process_iter(['pid', 'name']):
                try:
                    process_name = process.info['name']
                    if any(serato_name.lower() in process_name.lower() 
                          for serato_name in self.serato_processes):
                        running_processes.append(process_name)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            print(f"Error checking processes: {e}")
            return False, []
        
        return len(running_processes) > 0, running_processes
    
    def get_serato_library_path(self) -> Optional[Path]:
        """
        Find the main Serato library path based on platform
        Returns: Path to _Serato_ folder or None if not found
        """
        if self.platform == "Darwin":  # macOS
            music_path = Path.home() / "Music" / "_Serato_"
            if music_path.exists():
                return music_path
        elif self.platform == "Windows":
            # Windows typical paths
            possible_paths = [
                Path.home() / "Music" / "_Serato_",
                Path("C:/Users") / os.getenv("USERNAME", "") / "Music" / "_Serato_",
                Path("C:/Music/_Serato_")
            ]
            for path in possible_paths:
                if path.exists():
                    return path
        elif self.platform == "Linux":
            # Linux typical paths  
            possible_paths = [
                Path.home() / "Music" / "_Serato_",
                Path.home() / ".serato"
            ]
            for path in possible_paths:
                if path.exists():
                    return path
        
        return None
    
    def find_all_serato_libraries(self) -> List[Path]:
        """
        Find all _Serato_ folders across all mounted drives
        Returns: List of Path objects to _Serato_ folders
        """
        serato_folders = []
        
        # Add main library
        main_lib = self.get_serato_library_path()
        if main_lib:
            serato_folders.append(main_lib)
        
        # Search external drives
        if self.platform == "Darwin":  # macOS
            volumes_path = Path("/Volumes")
            if volumes_path.exists():
                for volume in volumes_path.iterdir():
                    if volume.is_dir() and not volume.is_symlink():
                        serato_path = volume / "_Serato_"
                        if serato_path.exists():
                            serato_folders.append(serato_path)
        
        elif self.platform == "Windows":
            # Windows drive letters
            for drive_letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
                drive_path = Path(f"{drive_letter}:/_Serato_")
                if drive_path.exists():
                    serato_folders.append(drive_path)
        
        # Remove duplicates while preserving order
        unique_folders = []
        seen = set()
        for folder in serato_folders:
            if folder not in seen:
                unique_folders.append(folder)
                seen.add(folder)
        
        return unique_folders
    
    def validate_serato_library(self, serato_path: Path) -> Dict[str, bool]:
        """
        Validate that a Serato library folder has the expected structure
        Returns: Dict with validation results
        """
        validation = {
            'exists': False,
            'has_database': False,
            'has_subcrates_folder': False,
            'is_writable': False,
            'has_backup_folder': False
        }
        
        try:
            if not serato_path.exists():
                return validation
            
            validation['exists'] = True
            
            # Check for database V2
            database_path = serato_path / "database V2"
            validation['has_database'] = database_path.exists()
            
            # Check for Subcrates folder
            subcrates_path = serato_path / "Subcrates"
            validation['has_subcrates_folder'] = subcrates_path.exists()
            
            # Check if we can write to the folder
            validation['is_writable'] = os.access(serato_path, os.W_OK)
            
            # Check for backup folder
            backup_path = serato_path / "_Serato_Backup"
            validation['has_backup_folder'] = backup_path.exists()
            
        except Exception as e:
            print(f"Error validating Serato library at {serato_path}: {e}")
        
        return validation
    
    def get_subcrates_path(self, serato_path: Path) -> Optional[Path]:
        """
        Get the Subcrates folder path for a given Serato library
        Returns: Path to Subcrates folder or None
        """
        if not serato_path.exists():
            return None
        
        subcrates_path = serato_path / "Subcrates"
        if subcrates_path.exists():
            return subcrates_path
        
        # Create if it doesn't exist
        try:
            subcrates_path.mkdir(exist_ok=True)
            return subcrates_path
        except Exception as e:
            print(f"Could not create Subcrates folder: {e}")
            return None
    
    def list_existing_crates(self, serato_path: Path) -> List[str]:
        """
        List all existing crate files in a Serato library
        Returns: List of crate names (without .crate extension)
        """
        crates = []
        subcrates_path = self.get_subcrates_path(serato_path)
        
        if subcrates_path and subcrates_path.exists():
            try:
                for file_path in subcrates_path.iterdir():
                    if file_path.is_file() and file_path.suffix == '.crate':
                        crates.append(file_path.stem)
            except Exception as e:
                print(f"Error listing crates: {e}")
        
        return sorted(crates)
    
    def is_installation_detected(self) -> bool:
        """
        Check if Serato DJ Pro appears to be installed on the system
        Returns: True if installation detected
        """
        # Check for library existence
        library_path = self.get_serato_library_path()
        if library_path:
            return True
        
        # Could also check for application installation paths
        if self.platform == "Darwin":  # macOS
            app_paths = [
                Path("/Applications/Serato DJ Pro.app"),
                Path("/Applications/Serato DJ Lite.app"),
                Path.home() / "Applications" / "Serato DJ Pro.app"
            ]
            return any(path.exists() for path in app_paths)
        
        return False
    
    def get_system_info(self) -> Dict[str, str]:
        """
        Get system information relevant to Serato integration
        Returns: Dict with system details
        """
        return {
            'platform': self.platform,
            'python_version': platform.python_version(),
            'architecture': platform.architecture()[0],
            'home_directory': str(Path.home()),
            'serato_installed': str(self.is_installation_detected()),
            'main_library_path': str(self.get_serato_library_path()) if self.get_serato_library_path() else "Not found"
        }


def quick_serato_check() -> Dict[str, any]:
    """
    Quick utility function to check Serato status
    Returns: Dict with basic status information
    """
    detector = SeratoDetector()
    
    is_running, processes = detector.is_serato_running()
    library_path = detector.get_serato_library_path()
    validation = detector.validate_serato_library(library_path) if library_path else {}
    
    return {
        'serato_running': is_running,
        'running_processes': processes,
        'library_found': library_path is not None,
        'library_path': str(library_path) if library_path else None,
        'library_valid': validation.get('exists', False) and validation.get('has_subcrates_folder', False),
        'safe_to_modify': not is_running and validation.get('is_writable', False)
    }


if __name__ == "__main__":
    # Test the detector
    detector = SeratoDetector()
    
    print("=== Serato DJ Detection Report ===")
    print(f"Platform: {detector.platform}")
    
    is_running, processes = detector.is_serato_running()
    print(f"Serato Running: {is_running}")
    if processes:
        print(f"Running Processes: {', '.join(processes)}")
    
    library_path = detector.get_serato_library_path()
    print(f"Main Library: {library_path}")
    
    if library_path:
        validation = detector.validate_serato_library(library_path)
        print(f"Library Validation: {validation}")
        
        crates = detector.list_existing_crates(library_path)
        print(f"Existing Crates: {len(crates)} found")
        if crates:
            print(f"  Examples: {', '.join(crates[:5])}")
    
    all_libraries = detector.find_all_serato_libraries()
    print(f"All Libraries Found: {len(all_libraries)}")
    for lib in all_libraries:
        print(f"  - {lib}")