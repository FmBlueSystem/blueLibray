"""
Serato DJ Backup System
Creates automatic backups before modifying Serato library files
"""

import os
import shutil
import datetime
from pathlib import Path
from typing import Optional, List, Dict
import json


class SeratoBackupManager:
    """Manages backups of Serato DJ library files"""
    
    def __init__(self, serato_library_path: Path):
        self.serato_path = serato_library_path
        self.backup_base_path = serato_library_path / "_BlueLibrary_Backups"
        self.max_backups = 10  # Keep only last 10 backups
        
        # Ensure backup directory exists
        self.backup_base_path.mkdir(exist_ok=True)
    
    def create_backup(self, backup_name: Optional[str] = None) -> Optional[Path]:
        """
        Create a complete backup of critical Serato files
        Returns: Path to backup folder or None if failed
        """
        if backup_name is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"bluelibrary_backup_{timestamp}"
        
        backup_path = self.backup_base_path / backup_name
        
        try:
            backup_path.mkdir(exist_ok=True)
            
            # Files/folders to backup
            items_to_backup = [
                "Subcrates",  # All playlist files
                "database V2",  # Main database
                "Smartcrates",  # Smart playlists
                "window.pref"  # Window preferences
            ]
            
            backup_manifest = {
                'created_at': datetime.datetime.now().isoformat(),
                'bluelibrary_version': '2.0',
                'backup_type': 'automatic',
                'files_backed_up': []
            }
            
            # Copy each item
            for item_name in items_to_backup:
                source_path = self.serato_path / item_name
                if source_path.exists():
                    dest_path = backup_path / item_name
                    
                    if source_path.is_file():
                        shutil.copy2(source_path, dest_path)
                        backup_manifest['files_backed_up'].append({
                            'name': item_name,
                            'type': 'file',
                            'size': source_path.stat().st_size
                        })
                    elif source_path.is_dir():
                        shutil.copytree(source_path, dest_path)
                        file_count = len(list(source_path.rglob('*')))
                        backup_manifest['files_backed_up'].append({
                            'name': item_name,
                            'type': 'directory',
                            'file_count': file_count
                        })
            
            # Save backup manifest
            manifest_path = backup_path / "backup_manifest.json"
            with open(manifest_path, 'w') as f:
                json.dump(backup_manifest, f, indent=2)
            
            print(f"Backup created successfully: {backup_path}")
            self._cleanup_old_backups()
            
            return backup_path
            
        except Exception as e:
            print(f"Error creating backup: {e}")
            # Cleanup failed backup attempt
            if backup_path.exists():
                shutil.rmtree(backup_path, ignore_errors=True)
            return None
    
    def create_crate_backup(self, crate_name: str) -> Optional[Path]:
        """
        Create a backup of a specific crate file before modification
        Returns: Path to backup file or None if failed
        """
        subcrates_path = self.serato_path / "Subcrates"
        crate_file_path = subcrates_path / f"{crate_name}.crate"
        
        if not crate_file_path.exists():
            print(f"Crate file not found: {crate_file_path}")
            return None
        
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{crate_name}_backup_{timestamp}.crate"
            backup_file_path = self.backup_base_path / backup_filename
            
            shutil.copy2(crate_file_path, backup_file_path)
            print(f"Crate backup created: {backup_file_path}")
            
            return backup_file_path
            
        except Exception as e:
            print(f"Error creating crate backup: {e}")
            return None
    
    def restore_backup(self, backup_path: Path) -> bool:
        """
        Restore a complete backup
        Returns: True if successful, False otherwise
        """
        if not backup_path.exists():
            print(f"Backup path does not exist: {backup_path}")
            return False
        
        try:
            # Read backup manifest
            manifest_path = backup_path / "backup_manifest.json"
            if manifest_path.exists():
                with open(manifest_path, 'r') as f:
                    manifest = json.load(f)
                    print(f"Restoring backup from: {manifest['created_at']}")
            
            # Restore each backed up item
            for item in backup_path.iterdir():
                if item.name == "backup_manifest.json":
                    continue
                
                dest_path = self.serato_path / item.name
                
                # Remove existing item
                if dest_path.exists():
                    if dest_path.is_file():
                        dest_path.unlink()
                    elif dest_path.is_dir():
                        shutil.rmtree(dest_path)
                
                # Restore from backup
                if item.is_file():
                    shutil.copy2(item, dest_path)
                elif item.is_dir():
                    shutil.copytree(item, dest_path)
            
            print(f"Backup restored successfully from: {backup_path}")
            return True
            
        except Exception as e:
            print(f"Error restoring backup: {e}")
            return False
    
    def restore_crate_backup(self, backup_file_path: Path, target_crate_name: Optional[str] = None) -> bool:
        """
        Restore a specific crate from backup
        Returns: True if successful, False otherwise
        """
        if not backup_file_path.exists():
            print(f"Backup file does not exist: {backup_file_path}")
            return False
        
        try:
            subcrates_path = self.serato_path / "Subcrates"
            
            if target_crate_name is None:
                # Extract original crate name from backup filename
                backup_name = backup_file_path.stem
                if "_backup_" in backup_name:
                    target_crate_name = backup_name.split("_backup_")[0]
                else:
                    target_crate_name = backup_name
            
            target_path = subcrates_path / f"{target_crate_name}.crate"
            shutil.copy2(backup_file_path, target_path)
            
            print(f"Crate restored: {target_crate_name}")
            return True
            
        except Exception as e:
            print(f"Error restoring crate backup: {e}")
            return False
    
    def list_backups(self) -> List[Dict[str, any]]:
        """
        List all available backups with their metadata
        Returns: List of backup information dicts
        """
        backups = []
        
        if not self.backup_base_path.exists():
            return backups
        
        for backup_dir in self.backup_base_path.iterdir():
            if backup_dir.is_dir():
                manifest_path = backup_dir / "backup_manifest.json"
                backup_info = {
                    'name': backup_dir.name,
                    'path': str(backup_dir),
                    'created_at': None,
                    'file_count': 0,
                    'size_mb': 0
                }
                
                # Read manifest if available
                if manifest_path.exists():
                    try:
                        with open(manifest_path, 'r') as f:
                            manifest = json.load(f)
                            backup_info['created_at'] = manifest.get('created_at')
                            backup_info['file_count'] = len(manifest.get('files_backed_up', []))
                    except Exception:
                        pass
                
                # Calculate backup size
                try:
                    total_size = sum(
                        f.stat().st_size 
                        for f in backup_dir.rglob('*') 
                        if f.is_file()
                    )
                    backup_info['size_mb'] = round(total_size / (1024 * 1024), 2)
                except Exception:
                    pass
                
                backups.append(backup_info)
        
        # Sort by creation time (newest first)
        backups.sort(key=lambda x: x['created_at'] or '', reverse=True)
        return backups
    
    def list_crate_backups(self) -> List[Dict[str, any]]:
        """
        List all available crate backup files
        Returns: List of crate backup information dicts
        """
        crate_backups = []
        
        if not self.backup_base_path.exists():
            return crate_backups
        
        for backup_file in self.backup_base_path.iterdir():
            if backup_file.is_file() and backup_file.suffix == '.crate':
                backup_info = {
                    'name': backup_file.name,
                    'path': str(backup_file),
                    'size_kb': round(backup_file.stat().st_size / 1024, 2),
                    'modified_at': datetime.datetime.fromtimestamp(
                        backup_file.stat().st_mtime
                    ).isoformat()
                }
                
                # Extract original crate name
                if "_backup_" in backup_file.stem:
                    backup_info['original_crate'] = backup_file.stem.split("_backup_")[0]
                
                crate_backups.append(backup_info)
        
        # Sort by modification time (newest first)
        crate_backups.sort(key=lambda x: x['modified_at'], reverse=True)
        return crate_backups
    
    def _cleanup_old_backups(self):
        """Remove old backups beyond the max_backups limit"""
        try:
            backups = self.list_backups()
            if len(backups) > self.max_backups:
                backups_to_remove = backups[self.max_backups:]
                for backup in backups_to_remove:
                    backup_path = Path(backup['path'])
                    if backup_path.exists():
                        shutil.rmtree(backup_path)
                        print(f"Removed old backup: {backup['name']}")
        except Exception as e:
            print(f"Error cleaning up old backups: {e}")
    
    def get_backup_stats(self) -> Dict[str, any]:
        """
        Get statistics about the backup system
        Returns: Dict with backup statistics
        """
        full_backups = self.list_backups()
        crate_backups = self.list_crate_backups()
        
        # Calculate total backup size
        total_size_mb = sum(backup['size_mb'] for backup in full_backups)
        total_size_mb += sum(backup['size_kb'] / 1024 for backup in crate_backups)
        
        return {
            'backup_directory': str(self.backup_base_path),
            'full_backups_count': len(full_backups),
            'crate_backups_count': len(crate_backups),
            'total_size_mb': round(total_size_mb, 2),
            'max_backups_limit': self.max_backups,
            'latest_backup': full_backups[0]['created_at'] if full_backups else None
        }


class SeratoBackupValidator:
    """Validates backup integrity and completeness"""
    
    @staticmethod
    def validate_backup(backup_path: Path) -> Dict[str, any]:
        """
        Validate a backup for completeness and integrity
        Returns: Dict with validation results
        """
        validation = {
            'valid': False,
            'has_manifest': False,
            'has_subcrates': False,
            'has_database': False,
            'file_count': 0,
            'errors': []
        }
        
        try:
            if not backup_path.exists():
                validation['errors'].append("Backup path does not exist")
                return validation
            
            # Check for manifest
            manifest_path = backup_path / "backup_manifest.json"
            validation['has_manifest'] = manifest_path.exists()
            
            # Check for critical folders
            subcrates_path = backup_path / "Subcrates"
            validation['has_subcrates'] = subcrates_path.exists()
            
            database_path = backup_path / "database V2"
            validation['has_database'] = database_path.exists()
            
            # Count files
            validation['file_count'] = len(list(backup_path.rglob('*')))
            
            # Overall validity
            validation['valid'] = (
                validation['has_manifest'] and 
                validation['has_subcrates'] and 
                validation['file_count'] > 0
            )
            
        except Exception as e:
            validation['errors'].append(f"Validation error: {str(e)}")
        
        return validation


if __name__ == "__main__":
    # Test the backup system
    from .serato_detector import SeratoDetector
    
    detector = SeratoDetector()
    library_path = detector.get_serato_library_path()
    
    if library_path:
        backup_manager = SeratoBackupManager(library_path)
        
        print("=== Serato Backup System Test ===")
        print(f"Library Path: {library_path}")
        print(f"Backup Path: {backup_manager.backup_base_path}")
        
        # Get backup stats
        stats = backup_manager.get_backup_stats()
        print(f"Backup Stats: {stats}")
        
        # List existing backups
        backups = backup_manager.list_backups()
        print(f"Existing Backups: {len(backups)}")
        for backup in backups[:3]:  # Show first 3
            print(f"  - {backup['name']} ({backup['size_mb']} MB)")
        
        # Create a test backup
        print("\\nCreating test backup...")
        backup_path = backup_manager.create_backup("test_backup")
        if backup_path:
            print(f"Test backup created: {backup_path}")
            
            # Validate the backup
            validator = SeratoBackupValidator()
            validation = validator.validate_backup(backup_path)
            print(f"Backup validation: {validation}")
    else:
        print("No Serato library found on this system")