"""
SQLite database for storing user preferences and settings
"""

import sqlite3
import json
import os
import threading
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
from dataclasses import asdict


class SettingsDatabase:
    """Manages application settings and preferences in SQLite"""
    
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            # Use default path in user's home directory
            config_dir = Path.home() / '.bluelibrary'
            config_dir.mkdir(exist_ok=True)
            db_path = str(config_dir / 'settings.db')
        
        self.db_path = db_path
        self._thread_local = threading.local()
        self._lock = threading.Lock()
        self._initialize_database()
    
    def _get_connection(self):
        """Get thread-local database connection"""
        if not hasattr(self._thread_local, 'conn') or self._thread_local.conn is None:
            self._thread_local.conn = sqlite3.connect(self.db_path)
            self._thread_local.conn.row_factory = sqlite3.Row
        return self._thread_local.conn
    
    def _initialize_database(self):
        """Create database tables if they don't exist"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Settings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Playlists table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS playlists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                tracks TEXT NOT NULL,  -- JSON array of track data
                settings TEXT,  -- JSON object with generation settings
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Recent folders table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recent_folders (
                path TEXT PRIMARY KEY,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tracks table for persistent storage
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tracks (
                id TEXT PRIMARY KEY,
                filepath TEXT NOT NULL,
                folder_path TEXT NOT NULL,
                file_modified_time TIMESTAMP,
                metadata TEXT NOT NULL,  -- JSON serialized Track object
                last_analyzed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(filepath)
            )
        """)
        
        # Enhanced metadata table for LLM-generated data
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS enhanced_metadata (
                track_id TEXT PRIMARY KEY,
                enhanced_data TEXT NOT NULL,  -- JSON serialized EnhancedMetadata object
                last_enhanced TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (track_id) REFERENCES tracks (id) ON DELETE CASCADE
            )
        """)
        
        conn.commit()
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a setting value"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        
        if row:
            try:
                return json.loads(row['value'])
            except json.JSONDecodeError:
                return row['value']
        return default
    
    def set_setting(self, key: str, value: Any):
        """Set a setting value"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Convert value to JSON string if it's not already a string
        if not isinstance(value, str):
            value = json.dumps(value)
        
        cursor.execute("""
            INSERT OR REPLACE INTO settings (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        """, (key, value))
        
        conn.commit()
    
    def get_all_settings(self) -> Dict[str, Any]:
        """Get all settings as a dictionary"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM settings")
        
        settings = {}
        for row in cursor.fetchall():
            try:
                settings[row['key']] = json.loads(row['value'])
            except json.JSONDecodeError:
                settings[row['key']] = row['value']
        
        return settings
    
    def save_algorithm_weights(self, weights: Dict[str, float]):
        """Save algorithm weight settings"""
        self.set_setting('algorithm_weights', weights)
    
    def load_algorithm_weights(self) -> Optional[Dict[str, float]]:
        """Load algorithm weight settings"""
        return self.get_setting('algorithm_weights')
    
    def save_window_geometry(self, geometry: Dict[str, int]):
        """Save window position and size"""
        self.set_setting('window_geometry', geometry)
    
    def load_window_geometry(self) -> Optional[Dict[str, int]]:
        """Load window position and size"""
        return self.get_setting('window_geometry')
    
    def add_recent_folder(self, path: str):
        """Add a folder to recent folders list"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO recent_folders (path, last_accessed)
            VALUES (?, CURRENT_TIMESTAMP)
        """, (path,))
        
        # Keep only the 10 most recent folders
        cursor.execute("""
            DELETE FROM recent_folders
            WHERE path NOT IN (
                SELECT path FROM recent_folders
                ORDER BY last_accessed DESC
                LIMIT 10
            )
        """)
        
        conn.commit()
    
    def get_recent_folders(self) -> List[str]:
        """Get list of recently accessed folders"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT path FROM recent_folders
            ORDER BY last_accessed DESC
            LIMIT 10
        """)
        
        return [row['path'] for row in cursor.fetchall()]
    
    def save_playlist(self, name: str, tracks: List[Dict], settings: Dict):
        """Save a generated playlist"""
        cursor = self.conn.cursor()
        
        tracks_json = json.dumps(tracks)
        settings_json = json.dumps(settings)
        
        cursor.execute("""
            INSERT INTO playlists (name, tracks, settings, created_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """, (name, tracks_json, settings_json))
        
        conn.commit()
        return cursor.lastrowid
    
    def get_playlists(self) -> List[Dict]:
        """Get all saved playlists"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, created_at
            FROM playlists
            ORDER BY created_at DESC
        """)
        
        playlists = []
        for row in cursor.fetchall():
            playlists.append({
                'id': row['id'],
                'name': row['name'],
                'created_at': row['created_at']
            })
        
        return playlists
    
    def get_playlist(self, playlist_id: int) -> Optional[Dict]:
        """Get a specific playlist with all data"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM playlists WHERE id = ?
        """, (playlist_id,))
        
        row = cursor.fetchone()
        if row:
            return {
                'id': row['id'],
                'name': row['name'],
                'tracks': json.loads(row['tracks']),
                'settings': json.loads(row['settings']) if row['settings'] else {},
                'created_at': row['created_at']
            }
        
        return None
    
    def delete_playlist(self, playlist_id: int):
        """Delete a playlist"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM playlists WHERE id = ?", (playlist_id,))
        conn.commit()
    
    # === Track Persistence Methods ===
    
    def save_track(self, track, folder_path: str):
        """Save a track to the database"""
        from ..core.harmonic_engine import Track  # Import here to avoid circular imports
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Get file modification time
        file_mod_time = None
        if os.path.exists(track.filepath):
            file_mod_time = datetime.fromtimestamp(os.path.getmtime(track.filepath))
        
        # Serialize track data (convert numpy types to Python types)
        track_data = asdict(track)
        
        # Convert numpy types to native Python types for JSON serialization
        for key, value in track_data.items():
            if hasattr(value, 'item'):  # numpy scalar
                track_data[key] = value.item()
            elif isinstance(value, (float, int)) and str(type(value)).startswith('<class \'numpy'):
                track_data[key] = float(value) if 'float' in str(type(value)) else int(value)
        
        metadata_json = json.dumps(track_data)
        
        cursor.execute("""
            INSERT OR REPLACE INTO tracks 
            (id, filepath, folder_path, file_modified_time, metadata, last_analyzed)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (track.id, track.filepath, folder_path, file_mod_time, metadata_json))
        
        conn.commit()
    
    def save_tracks_batch(self, tracks: List, folder_path: str):
        """Save multiple tracks efficiently"""
        from ..core.harmonic_engine import Track  # Import here to avoid circular imports
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        track_records = []
        for track in tracks:
            # Get file modification time
            file_mod_time = None
            if os.path.exists(track.filepath):
                file_mod_time = datetime.fromtimestamp(os.path.getmtime(track.filepath))
            
            # Serialize track data (convert numpy types to Python types)
            track_data = asdict(track)
            
            # Convert numpy types to native Python types for JSON serialization
            for key, value in track_data.items():
                if hasattr(value, 'item'):  # numpy scalar
                    track_data[key] = value.item()
                elif isinstance(value, (float, int)) and str(type(value)).startswith('<class \'numpy'):
                    track_data[key] = float(value) if 'float' in str(type(value)) else int(value)
            
            metadata_json = json.dumps(track_data)
            
            track_records.append((
                track.id, track.filepath, folder_path, 
                file_mod_time, metadata_json
            ))
        
        cursor.executemany("""
            INSERT OR REPLACE INTO tracks 
            (id, filepath, folder_path, file_modified_time, metadata, last_analyzed)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, track_records)
        
        conn.commit()
    
    def load_tracks_by_folder(self, folder_path: str) -> List:
        """Load all tracks from a specific folder"""
        from ..core.harmonic_engine import Track  # Import here to avoid circular imports
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT metadata, filepath, file_modified_time 
            FROM tracks 
            WHERE folder_path = ?
            ORDER BY last_analyzed DESC
        """, (folder_path,))
        
        tracks = []
        for row in cursor.fetchall():
            try:
                # Check if file still exists and hasn't been modified
                if os.path.exists(row['filepath']):
                    current_mod_time = datetime.fromtimestamp(os.path.getmtime(row['filepath']))
                    cached_mod_time = datetime.fromisoformat(row['file_modified_time']) if row['file_modified_time'] else None
                    
                    # Only load if file hasn't been modified since caching
                    if cached_mod_time and current_mod_time <= cached_mod_time:
                        track_data = json.loads(row['metadata'])
                        track = Track(**track_data)
                        tracks.append(track)
                    else:
                        # File has been modified, remove from cache
                        self._remove_track_by_filepath(row['filepath'])
            except (json.JSONDecodeError, OSError, ValueError):
                # Invalid data or file issues, remove from cache
                self._remove_track_by_filepath(row['filepath'])
                continue
        
        return tracks
    
    def get_cached_tracks(self) -> List:
        """Get all cached tracks with validation"""
        from ..core.harmonic_engine import Track  # Import here to avoid circular imports
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT metadata, filepath, file_modified_time 
            FROM tracks 
            ORDER BY last_analyzed DESC
        """)
        
        tracks = []
        for row in cursor.fetchall():
            try:
                # Check if file still exists and hasn't been modified
                if os.path.exists(row['filepath']):
                    current_mod_time = datetime.fromtimestamp(os.path.getmtime(row['filepath']))
                    cached_mod_time = datetime.fromisoformat(row['file_modified_time']) if row['file_modified_time'] else None
                    
                    # Only load if file hasn't been modified since caching
                    if cached_mod_time and current_mod_time <= cached_mod_time:
                        track_data = json.loads(row['metadata'])
                        track = Track(**track_data)
                        tracks.append(track)
                    else:
                        # File has been modified, remove from cache
                        self._remove_track_by_filepath(row['filepath'])
                else:
                    # File no longer exists, remove from cache
                    self._remove_track_by_filepath(row['filepath'])
            except (json.JSONDecodeError, OSError, ValueError):
                # Invalid data, remove from cache
                self._remove_track_by_filepath(row['filepath'])
                continue
        
        return tracks
    
    def _remove_track_by_filepath(self, filepath: str):
        """Remove a track from cache by filepath"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tracks WHERE filepath = ?", (filepath,))
        conn.commit()
    
    def clear_track_cache(self):
        """Clear all cached tracks"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tracks")
        conn.commit()
    
    def get_last_folder_path(self) -> Optional[str]:
        """Get the most recently analyzed folder path"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT folder_path, COUNT(*) as track_count
            FROM tracks 
            GROUP BY folder_path 
            ORDER BY MAX(last_analyzed) DESC 
            LIMIT 1
        """)
        
        row = cursor.fetchone()
        return row['folder_path'] if row and row['track_count'] > 0 else None
    
    def save_enhanced_metadata(self, enhanced_metadata):
        """Save enhanced metadata for a track"""
        from ..llm.metadata_enhancer import EnhancedMetadata  # Import here to avoid circular imports
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Serialize enhanced metadata
        enhanced_data = asdict(enhanced_metadata)
        enhanced_json = json.dumps(enhanced_data)
        
        cursor.execute("""
            INSERT OR REPLACE INTO enhanced_metadata (track_id, enhanced_data, last_enhanced)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        """, (enhanced_metadata.track_id, enhanced_json))
        
        conn.commit()
    
    def load_enhanced_metadata(self, track_id: str):
        """Load enhanced metadata for a track"""
        from ..llm.metadata_enhancer import EnhancedMetadata  # Import here to avoid circular imports
        
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT enhanced_data FROM enhanced_metadata 
            WHERE track_id = ?
        """, (track_id,))
        
        row = cursor.fetchone()
        if row:
            try:
                enhanced_data = json.loads(row['enhanced_data'])
                return EnhancedMetadata(**enhanced_data)
            except (json.JSONDecodeError, TypeError) as e:
                print(f"Error loading enhanced metadata for track {track_id}: {e}")
                return None
        return None
    
    def load_all_enhanced_metadata(self) -> Dict[str, Any]:
        """Load all enhanced metadata as a dictionary"""
        from ..llm.metadata_enhancer import EnhancedMetadata  # Import here to avoid circular imports
        
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT track_id, enhanced_data FROM enhanced_metadata")
        
        enhanced_cache = {}
        for row in cursor.fetchall():
            try:
                enhanced_data = json.loads(row['enhanced_data'])
                enhanced_cache[row['track_id']] = EnhancedMetadata(**enhanced_data)
            except (json.JSONDecodeError, TypeError) as e:
                print(f"Error loading enhanced metadata for track {row['track_id']}: {e}")
                continue
        
        return enhanced_cache
    
    def delete_enhanced_metadata(self, track_id: str):
        """Delete enhanced metadata for a track"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM enhanced_metadata WHERE track_id = ?", (track_id,))
        conn.commit()
    
    def close(self):
        """Close database connections"""
        # Close thread-local connections
        if hasattr(self._thread_local, 'conn') and self._thread_local.conn:
            self._thread_local.conn.close()
            self._thread_local.conn = None