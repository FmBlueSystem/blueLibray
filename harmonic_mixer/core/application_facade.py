"""
Application Facade - Simplified interface for UI layer
Reduces coupling and provides clean API for all operations
"""

import asyncio
import os
from typing import List, Optional, Dict, Any, Callable
from pathlib import Path
from dataclasses import asdict

from .harmonic_engine import HarmonicMixingEngine, Track, MixMode
from ..utils.async_analyzer import AsyncAudioAnalyzer, SecurityValidator
from ..data.secure_database import SecureSettingsDatabase
from ..data.database import SettingsDatabase
from .event_system import event_manager, EventType
from .plugin_system import plugin_manager, PluginType

# LLM integration (optional)
try:
    from ..llm.llm_config_manager import LLMConfigManager
    from ..llm.llm_integration import LLMIntegration
    from ..llm.metadata_enhancer import MetadataEnhancer
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False


class ApplicationState:
    """Centralized application state management"""
    
    def __init__(self):
        self.tracks: List[Track] = []
        self.current_track: Optional[Track] = None
        self.current_playlist: List[Track] = []
        self.is_analyzing = False
        self.analysis_progress = 0
        
    def clear_tracks(self):
        """Clear all loaded tracks"""
        self.tracks.clear()
        self.current_track = None
        self.current_playlist.clear()
    
    def add_track(self, track: Track):
        """Add a track to the collection (avoid duplicates)"""
        # Check if track already exists by filepath
        if hasattr(track, 'filepath') and track.filepath:
            existing = next((t for t in self.tracks if hasattr(t, 'filepath') and t.filepath == track.filepath), None)
            if existing:
                return  # Don't add duplicate
        
        self.tracks.append(track)
    
    def get_track_by_id(self, track_id: str) -> Optional[Track]:
        """Get track by ID"""
        return next((t for t in self.tracks if t.id == track_id), None)
    
    def set_current_track(self, track: Track):
        """Set the currently selected track"""
        self.current_track = track


class PlaylistManager:
    """Manages playlist operations and history"""
    
    def __init__(self, db: SettingsDatabase):
        self.db = db
        self.playlist_history: List[Dict] = []
    
    def generate_playlist(
        self, 
        engine: HarmonicMixingEngine,
        tracks: List[Track],
        start_track: Optional[Track] = None,
        target_length: int = 10,
        progression_curve: str = "neutral"
    ) -> List[Track]:
        """Generate playlist with settings tracking"""
        playlist = engine.generate_playlist(
            tracks, start_track, target_length, progression_curve
        )
        
        # Save to history
        playlist_data = {
            'tracks': [asdict(track) for track in playlist],
            'settings': {
                'mode': engine.mode.value,
                'weights': engine.weights.copy(),
                'progression_curve': progression_curve,
                'target_length': target_length,
                'start_track': asdict(start_track) if start_track else None
            }
        }
        
        self.playlist_history.append(playlist_data)
        
        return playlist
    
    def save_playlist(self, name: str, playlist: List[Track], settings: Dict):
        """Save playlist to database"""
        tracks_data = [asdict(track) for track in playlist]
        return self.db.save_playlist(name, tracks_data, settings)
    
    def get_saved_playlists(self) -> List[Dict]:
        """Get all saved playlists"""
        return self.db.get_playlists()


class AnalysisManager:
    """Manages audio analysis operations"""
    
    def __init__(self):
        self.analyzer = AsyncAudioAnalyzer()
        self.current_task: Optional[asyncio.Task] = None
        
        # Setup event publishing
        def publish_progress(current, total):
            event_manager.analysis_progress(current, total)
        
        self.progress_callback = publish_progress
    
    async def analyze_folder(
        self, 
        folder_path: str,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[Track]:
        """Analyze all audio files in a folder"""
        # Find audio files
        audio_files = self._find_audio_files(folder_path)
        
        if not audio_files:
            return []
        
        # Analyze files
        tracks = await self.analyzer.batch_analyze_async(
            audio_files, 
            progress_callback
        )
        
        return tracks
    
    def _find_audio_files(self, folder_path: str) -> List[str]:
        """Find all valid audio files in folder"""
        audio_files = []
        folder = Path(folder_path)
        
        if not folder.exists() or not folder.is_dir():
            return audio_files
        
        for file_path in folder.rglob("*"):
            if file_path.is_file() and SecurityValidator.validate_audio_file(str(file_path)):
                audio_files.append(str(file_path))
        
        return audio_files
    
    def cancel_analysis(self):
        """Cancel current analysis task"""
        if self.current_task and not self.current_task.done():
            self.current_task.cancel()


class BlueLibraryFacade:
    """
    Main application facade providing simplified interface for UI layer
    Centralizes all business logic and reduces UI coupling
    """
    
    def __init__(self):
        # Core components
        self.engine = HarmonicMixingEngine()
        self.db = SecureSettingsDatabase()
        self.state = ApplicationState()
        self.playlist_manager = PlaylistManager(self.db)
        self.analysis_manager = AnalysisManager()
        
        # LLM components (optional)
        self.llm_config_manager = None
        self.llm_integration = None
        self.metadata_enhancer = None
        
        if LLM_AVAILABLE:
            self.llm_config_manager = LLMConfigManager(self.db)
            self._initialize_llm_integration()
        
        # Initialize event system
        event_manager.application_started()
        
        # Setup event handlers
        self._setup_event_handlers()
        
        # Load saved settings
        self._load_settings()
    
    def _initialize_llm_integration(self):
        """Initialize LLM integration if configured"""
        print("🔍 Checking LLM configuration...")
        
        # Check if LLM config manager exists
        if not self.llm_config_manager:
            print("❌ LLM config manager not initialized")
            return
        
        # Check if LLM is configured
        if not self.llm_config_manager.is_configured():
            print("⚠️  LLM not configured - API key or provider missing")
            return
        
        # Get LLM configuration
        llm_config = self.llm_config_manager.get_llm_config()
        if not llm_config:
            print("❌ Failed to get LLM configuration")
            return
        
        print(f"✅ LLM configuration found: {llm_config.provider} provider")
        
        try:
            # Initialize LLM integration
            self.llm_integration = LLMIntegration(llm_config)
            print("✅ LLM integration created successfully")
            
            # Initialize metadata enhancer
            self.metadata_enhancer = MetadataEnhancer(self.llm_integration, self.db)
            cache_size = len(self.metadata_enhancer.enhancement_cache)
            print(f"✅ LLM metadata enhancer initialized with cache size: {cache_size}")
            
        except Exception as e:
            print(f"❌ Failed to initialize LLM integration: {e}")
            self.llm_integration = None
            self.metadata_enhancer = None
            import traceback
            traceback.print_exc()
    
    def _setup_event_handlers(self):
        """Setup event handlers for the facade"""
        # Track analysis events
        event_manager.event_bus.subscribe(
            EventType.TRACK_ANALYZED,
            lambda event: self.state.add_track(event.data)
        )
        
        # Mix mode change events
        event_manager.event_bus.subscribe(
            EventType.MIX_MODE_CHANGED,
            lambda event: self._on_mix_mode_changed(event.data)
        )
        
        # Error handling
        event_manager.event_bus.subscribe(
            EventType.ERROR_OCCURRED,
            lambda event: self._on_error(event.data)
        )
    
    def _on_mix_mode_changed(self, data):
        """Handle mix mode change"""
        # Save new mode to settings
        self.db.set_setting('last_mode', data['new_mode'])
    
    def _on_error(self, data):
        """Handle application errors"""
        print(f"Application error: {data['error']}")
        if data.get('context'):
            print(f"Context: {data['context']}")
    
    # === Track Management ===
    
    def get_tracks(self) -> List[Track]:
        """Get all loaded tracks"""
        return self.state.tracks.copy()
    
    def get_current_track(self) -> Optional[Track]:
        """Get currently selected track"""
        return self.state.current_track
    
    def set_current_track(self, track_id: str) -> bool:
        """Set current track by ID"""
        track = self.state.get_track_by_id(track_id)
        if track:
            old_track = self.state.current_track
            self.state.set_current_track(track)
            event_manager.event_bus.publish(
                EventType.TRACK_SELECTED,
                {'old_track': old_track, 'new_track': track},
                "facade"
            )
            return True
        return False
    
    def clear_tracks(self):
        """Clear all loaded tracks"""
        self.state.clear_tracks()
        event_manager.event_bus.publish(EventType.TRACKS_CLEARED, None, "facade")
    
    def clear_library(self):
        """Clear entire music library (manual action)"""
        self.state.clear_tracks()
        self.db.clear_track_cache()  # Also clear database cache
        event_manager.event_bus.publish(EventType.TRACKS_CLEARED, None, "facade")
    
    # === Audio Analysis ===
    
    async def load_music_folder(
        self, 
        folder_path: str,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> bool:
        """Load and analyze music from folder"""
        try:
            self.state.is_analyzing = True
            # Don't clear existing tracks - we want to add to the library
            
            # Save to recent folders
            self.db.add_recent_folder(folder_path)
            
            # Analyze tracks
            tracks = await self.analysis_manager.analyze_folder(
                folder_path, progress_callback
            )
            
            # Update state and dispatch events
            for track in tracks:
                self.state.add_track(track)
                # Dispatch event for UI update
                from harmonic_mixer.core.event_system import event_manager
                event_manager.track_analyzed(track)
            
            # Save tracks to database for persistence
            if tracks:
                self.db.save_tracks_batch(tracks, folder_path)
            
            self.state.is_analyzing = False
            return True
            
        except Exception as e:
            self.state.is_analyzing = False
            print(f"Error loading music folder: {e}")
            return False
    
    def analyze_audio_files(self, file_paths: List[str]) -> List[Track]:
        """Analyze specific audio files and return tracks"""
        from harmonic_mixer.core.event_system import event_manager
        import uuid
        
        try:
            analyzed_tracks = []
            
            for file_path in file_paths:
                try:
                    # Generate unique track ID
                    track_id = str(uuid.uuid4())
                    
                    # Analyze individual file
                    track = self.analysis_manager.analyzer.analyze_file(file_path, track_id)
                    if track:
                        analyzed_tracks.append(track)
                        # Dispatch event for UI update
                        event_manager.track_analyzed(track)
                except Exception as e:
                    print(f"Error analyzing {file_path}: {e}")
                    continue
            
            return analyzed_tracks
            
        except Exception as e:
            print(f"Error in analyze_audio_files: {e}")
            return []
    
    def cancel_analysis(self):
        """Cancel current analysis operation"""
        self.analysis_manager.cancel_analysis()
        self.state.is_analyzing = False
    
    def clear_analysis_cache(self):
        """Clear analysis cache"""
        self.analysis_manager.analyzer.clear_cache()
    
    def clear_track_cache(self):
        """Clear track cache from database"""
        self.db.clear_track_cache()
    
    def load_cached_tracks(self) -> bool:
        """Load previously cached tracks from database"""
        try:
            cached_tracks = self.db.get_cached_tracks()
            
            if cached_tracks:
                # Clear current state
                self.state.clear_tracks()
                
                # Add cached tracks to state
                for track in cached_tracks:
                    self.state.add_track(track)
                
                return True
            return False
            
        except Exception as e:
            print(f"Error loading cached tracks: {e}")
            return False
    
    def should_auto_restore(self) -> bool:
        """Check if auto-restore is enabled"""
        return self.db.get_setting('auto_restore_last_session', True)
    
    def restore_last_session(self) -> bool:
        """Restore tracks from the most recently analyzed folder"""
        try:
            last_folder = self.db.get_last_folder_path()
            if last_folder:
                cached_tracks = self.db.load_tracks_by_folder(last_folder)
                
                if cached_tracks:
                    # Clear current state
                    self.state.clear_tracks()
                    
                    # Check folder availability and update track status
                    folder_available = os.path.exists(last_folder)
                    unavailable_count = 0
                    
                    # Add cached tracks to state with availability check
                    for track in cached_tracks:
                        # Check if individual file exists
                        if hasattr(track, 'filepath') and track.filepath:
                            track.is_available = os.path.exists(track.filepath)
                            if not track.is_available:
                                unavailable_count += 1
                        else:
                            track.is_available = folder_available
                            
                        self.state.add_track(track)
                        # Publish event so UI shows the restored track
                        event_manager.track_analyzed(track)
                    
                    # Update recent folders if available
                    if folder_available:
                        self.db.add_recent_folder(last_folder)
                    
                    # Log status
                    total_tracks = len(cached_tracks)
                    available_tracks = total_tracks - unavailable_count
                    print(f"Restored {total_tracks} tracks ({available_tracks} available, {unavailable_count} unavailable)")
                    
                    if unavailable_count > 0:
                        print(f"Note: {unavailable_count} tracks are on unavailable storage (external drive not mounted?)")
                    
                    return True
            return False
            
        except Exception as e:
            print(f"Error restoring last session: {e}")
            return False
    
    # === Mixing Engine ===
    
    def set_mix_mode(self, mode: str):
        """Set mixing mode"""
        mode_map = {
            "Intelligent": MixMode.INTELLIGENT,
            "Classic Camelot": MixMode.CLASSIC_CAMELOT,
            "Energy Flow": MixMode.ENERGY_FLOW,
            "Emotional": MixMode.EMOTIONAL
        }
        
        if mode in mode_map:
            old_mode = self.get_mix_mode()
            self.engine.set_mode(mode_map[mode])
            event_manager.mix_mode_changed(old_mode, mode)
    
    def get_mix_mode(self) -> str:
        """Get current mixing mode"""
        mode_names = {
            MixMode.INTELLIGENT: "Intelligent",
            MixMode.CLASSIC_CAMELOT: "Classic Camelot",
            MixMode.ENERGY_FLOW: "Energy Flow",
            MixMode.EMOTIONAL: "Emotional"
        }
        return mode_names.get(self.engine.mode, "Intelligent")
    
    def set_algorithm_weights(self, weights: Dict[str, float]):
        """Set algorithm weights"""
        # Normalize weights
        total = sum(weights.values())
        if total > 0:
            normalized_weights = {k: v / total for k, v in weights.items()}
            self.engine.weights.update(normalized_weights)
    
    def get_algorithm_weights(self) -> Dict[str, float]:
        """Get current algorithm weights"""
        return self.engine.weights.copy()
    
    def calculate_track_compatibility(self, track1_id: str, track2_id: str) -> float:
        """Calculate compatibility between two tracks"""
        track1 = self.state.get_track_by_id(track1_id)
        track2 = self.state.get_track_by_id(track2_id)
        
        if track1 and track2:
            return self.engine.calculate_compatibility(track1, track2)
        return 0.0
    
    # === Playlist Management ===
    
    def generate_playlist(
        self,
        target_length: int = 15,
        progression_curve: str = "neutral",
        start_track_id: Optional[str] = None
    ) -> List[Track]:
        """Generate optimized playlist"""
        if not self.state.tracks:
            return []
        
        start_track = None
        if start_track_id:
            start_track = self.state.get_track_by_id(start_track_id)
        elif self.state.current_track:
            start_track = self.state.current_track
        
        playlist = self.playlist_manager.generate_playlist(
            self.engine,
            self.state.tracks,
            start_track,
            target_length,
            progression_curve
        )
        
        self.state.current_playlist = playlist
        return playlist
    
    def get_current_playlist(self) -> List[Track]:
        """Get current playlist"""
        return self.state.current_playlist.copy()
    
    def save_playlist(self, name: str) -> Optional[int]:
        """Save current playlist"""
        if not self.state.current_playlist:
            return None
        
        settings = {
            'mode': self.get_mix_mode(),
            'weights': self.get_algorithm_weights()
        }
        
        return self.playlist_manager.save_playlist(
            name, 
            self.state.current_playlist, 
            settings
        )
    
    def get_saved_playlists(self) -> List[Dict]:
        """Get all saved playlists"""
        return self.playlist_manager.get_saved_playlists()
    
    # === Settings Management ===
    
    def get_recent_folders(self) -> List[str]:
        """Get recently accessed folders"""
        return self.db.get_recent_folders()
    
    def save_window_geometry(self, geometry: Dict[str, int]):
        """Save window position and size"""
        self.db.save_window_geometry(geometry)
    
    def load_window_geometry(self) -> Optional[Dict[str, int]]:
        """Load window position and size"""
        return self.db.load_window_geometry()
    
    def _load_settings(self):
        """Load saved settings"""
        # Load algorithm weights
        weights = self.db.load_algorithm_weights()
        if weights:
            self.engine.weights = weights
        
        # Load last used mode
        last_mode = self.db.get_setting('last_mode', 'Intelligent')
        self.set_mix_mode(last_mode)
        
        # Note: Auto-restore is now handled by UI after initialization
    
    def save_current_settings(self):
        """Save current application settings"""
        # Save algorithm weights
        self.db.save_algorithm_weights(self.engine.weights)
        
        # Save current mode
        self.db.set_setting('last_mode', self.get_mix_mode())
    
    def close(self):
        """Cleanup and close application"""
        event_manager.application_closing()
        self.save_current_settings()
        self.cancel_analysis()
        plugin_manager.cleanup_all()
        self.db.close()
    
    # === Status and Information ===
    
    def get_application_status(self) -> Dict[str, Any]:
        """Get current application status"""
        return {
            'tracks_loaded': len(self.state.tracks),
            'current_track': self.state.current_track.title if self.state.current_track else None,
            'playlist_length': len(self.state.current_playlist),
            'is_analyzing': self.state.is_analyzing,
            'analysis_progress': self.state.analysis_progress,
            'mix_mode': self.get_mix_mode(),
            'weights': self.get_algorithm_weights()
        }
    
    def get_track_statistics(self) -> Dict[str, Any]:
        """Get statistics about loaded tracks"""
        if not self.state.tracks:
            return {}
        
        keys = [t.key for t in self.state.tracks if t.key]
        bpms = [t.bpm for t in self.state.tracks if t.bpm]
        energies = [t.energy for t in self.state.tracks if t.energy]
        
        return {
            'total_tracks': len(self.state.tracks),
            'unique_keys': len(set(keys)) if keys else 0,
            'avg_bpm': sum(bpms) / len(bpms) if bpms else 0,
            'avg_energy': sum(energies) / len(energies) if energies else 0,
            'bpm_range': (min(bpms), max(bpms)) if bpms else (0, 0),
            'energy_range': (min(energies), max(energies)) if energies else (0, 0)
        }
    
    # === Plugin Management ===
    
    def get_available_plugins(self) -> List[Dict]:
        """Get list of available plugins"""
        return [
            {
                'name': plugin.name,
                'version': plugin.version,
                'author': plugin.author,
                'description': plugin.description,
                'type': plugin.plugin_type.value
            }
            for plugin in plugin_manager.list_plugins()
        ]
    
    def get_mixing_algorithms(self) -> List[str]:
        """Get available mixing algorithm plugins"""
        plugins = plugin_manager.get_plugins_by_type(PluginType.MIXING_ALGORITHM)
        return [plugin.metadata.name for plugin in plugins]
    
    def get_export_formats(self) -> List[str]:
        """Get available export format plugins"""
        plugins = plugin_manager.get_plugins_by_type(PluginType.EXPORT_FORMAT)
        return [plugin.metadata.name for plugin in plugins]
    
    # === LLM Integration ===
    
    def is_llm_available(self) -> bool:
        """Check if LLM integration is available"""
        return LLM_AVAILABLE
    
    def is_llm_configured(self) -> bool:
        """Check if LLM is configured and ready"""
        if not self.llm_config_manager:
            print("🔍 LLM check: No config manager")
            return False
        
        if not self.llm_config_manager.is_configured():
            print("🔍 LLM check: Not configured (missing API key or provider)")
            return False
        
        if self.llm_integration is None:
            print("🔍 LLM check: Integration not initialized, attempting to initialize...")
            # Try to reinitialize
            self._initialize_llm_integration()
            return self.llm_integration is not None
        
        if self.metadata_enhancer is None:
            print("🔍 LLM check: Metadata enhancer not initialized")
            return False
        
        print("🔍 LLM check: ✅ Fully configured and ready")
        return True
    
    def get_llm_settings(self):
        """Get LLM settings"""
        if self.llm_config_manager:
            return self.llm_config_manager.get_settings()
        return None
    
    def update_llm_settings(self, settings) -> bool:
        """Update LLM settings and reinitialize if needed"""
        if not self.llm_config_manager:
            return False
        
        success = self.llm_config_manager.update_settings(settings)
        if success:
            self._initialize_llm_integration()
        return success
    
    def get_llm_providers(self):
        """Get available LLM providers"""
        if self.llm_config_manager:
            return self.llm_config_manager.get_available_providers()
        return {}
    
    async def enhance_track_metadata(self, track_id: str):
        """Enhance metadata for a specific track"""
        if not self.metadata_enhancer:
            return None
        
        track = self.state.get_track_by_id(track_id)
        if track:
            return await self.metadata_enhancer.enhance_track(track)
        return None
    
    async def enhance_all_tracks_metadata(self):
        """Enhance metadata for all loaded tracks"""
        if not self.metadata_enhancer or not self.state.tracks:
            return {}
        
        return await self.metadata_enhancer.enhance_tracks_batch(self.state.tracks)
    
    def get_enhanced_metadata(self, track_id: str):
        """Get enhanced metadata for a track"""
        if self.metadata_enhancer:
            return self.metadata_enhancer.get_enhanced_metadata(track_id)
        return None
    
    def get_llm_cost_estimate(self, num_tracks: int = None):
        """Get cost estimate for LLM analysis"""
        if not self.llm_config_manager:
            return None
        
        if num_tracks is None:
            num_tracks = len(self.state.tracks)
        
        return self.llm_config_manager.get_cost_estimate(num_tracks)
    
    def get_genre_corrections(self) -> List[Dict]:
        """Get all tracks where LLM detected incorrect genres"""
        if not self.metadata_enhancer:
            return []
        
        corrections = []
        for track in self.state.tracks:
            enhanced = self.metadata_enhancer.get_enhanced_metadata(track.id)
            if enhanced and enhanced.is_genre_correct is False:
                corrections.append({
                    'track_id': track.id,
                    'title': track.title,
                    'artist': track.artist,
                    'original_genre': enhanced.original_genre or track.genre,
                    'corrected_genre': enhanced.corrected_genre,
                    'reason': enhanced.genre_correction_reason
                })
        return corrections
    
    def apply_genre_correction(self, track_id: str) -> bool:
        """Apply LLM-suggested genre correction to a track"""
        if not self.metadata_enhancer:
            return False
        
        track = self.state.get_track_by_id(track_id)
        enhanced = self.metadata_enhancer.get_enhanced_metadata(track_id)
        
        if track and enhanced and enhanced.corrected_genre and not enhanced.is_genre_correct:
            # Update the track's genre
            track.genre = enhanced.corrected_genre
            
            # Save to database
            try:
                self.db.save_track(track, track.filepath.split('/')[:-1])  # folder path
                print(f"Updated genre for '{track.title}': {enhanced.original_genre} → {enhanced.corrected_genre}")
                return True
            except Exception as e:
                print(f"Failed to save genre correction: {e}")
                return False
        
        return False
    
    def apply_all_genre_corrections(self) -> int:
        """Apply all LLM-suggested genre corrections"""
        corrections = self.get_genre_corrections()
        applied = 0
        
        for correction in corrections:
            if self.apply_genre_correction(correction['track_id']):
                applied += 1
        
        if applied > 0:
            event_manager.event_bus.publish(
                EventType.TRACKS_UPDATED,
                {'corrected_genres': applied},
                "facade"
            )
        
        return applied
    
    def export_playlist_with_plugin(self, plugin_name: str, filepath: str, options: Dict = None) -> bool:
        """Export playlist using specific plugin"""
        if not self.state.current_playlist:
            return False
        
        plugin = plugin_manager.get_plugin(plugin_name)
        if plugin and hasattr(plugin, 'export_playlist'):
            try:
                result = plugin.export_playlist(self.state.current_playlist, filepath, options)
                if result:
                    event_manager.event_bus.publish(
                        EventType.PLAYLIST_EXPORTED,
                        {'plugin': plugin_name, 'filepath': filepath},
                        "facade"
                    )
                return result
            except Exception as e:
                event_manager.error_occurred(e, f"export_with_{plugin_name}")
                return False
        
        return False
    
    def export_playlist_to_serato(self, playlist_name: str, tracks: Optional[List[Track]] = None, options: Dict = None) -> Dict[str, Any]:
        """
        Export playlist directly to Serato DJ Pro library
        
        Args:
            playlist_name: Name for the playlist/crate in Serato
            tracks: List of tracks to export (uses current playlist if None)
            options: Export options (backup, overwrite, etc.)
        
        Returns:
            Dict with export result details
        """
        from ..integrations.serato_export_plugin import SeratoExportResult
        
        # Use provided tracks or current playlist
        tracks_to_export = tracks or self.state.current_playlist
        if not tracks_to_export:
            return {
                'success': False,
                'error': 'No tracks to export'
            }
        
        # Get Serato export plugin
        serato_plugin = plugin_manager.get_plugin("Serato DJ Pro Export")
        if not serato_plugin:
            return {
                'success': False,
                'error': 'Serato export plugin not available'
            }
        
        # Pre-export check
        pre_check = serato_plugin.pre_export_check()
        if not pre_check.get('can_export', False):
            return {
                'success': False,
                'error': f"Cannot export to Serato: {'; '.join(pre_check.get('issues', []))}"
            }
        
        try:
            # Perform export
            result: SeratoExportResult = serato_plugin.export_playlist(
                tracks_to_export, 
                playlist_name, 
                options or {}
            )
            
            # Publish event if successful
            if result.success:
                event_manager.event_bus.publish(
                    EventType.PLAYLIST_EXPORTED,
                    {
                        'plugin': 'Serato DJ Pro Export',
                        'playlist_name': playlist_name,
                        'crate_path': str(result.crate_path) if result.crate_path else None,
                        'tracks_count': result.tracks_exported
                    },
                    "facade"
                )
            
            return {
                'success': result.success,
                'crate_path': str(result.crate_path) if result.crate_path else None,
                'backup_path': str(result.backup_path) if result.backup_path else None,
                'tracks_exported': result.tracks_exported,
                'library_path': str(result.library_path) if result.library_path else None,
                'error': result.error_message
            }
            
        except Exception as e:
            event_manager.error_occurred(e, "export_to_serato")
            return {
                'success': False,
                'error': f"Export failed: {str(e)}"
            }
    
    def get_serato_status(self) -> Dict[str, Any]:
        """
        Get current Serato DJ integration status
        
        Returns:
            Dict with Serato status information
        """
        serato_plugin = plugin_manager.get_plugin("Serato DJ Pro Export")
        if serato_plugin:
            return serato_plugin.get_status_info()
        
        return {
            'plugin_available': False,
            'error': 'Serato plugin not found'
        }
    
    def list_serato_crates(self) -> List[str]:
        """
        List existing crates in Serato DJ library
        
        Returns:
            List of crate names
        """
        serato_plugin = plugin_manager.get_plugin("Serato DJ Pro Export")
        if serato_plugin:
            return serato_plugin.list_existing_crates()
        
        return []
    
    def load_plugin_from_file(self, filepath: str) -> bool:
        """Load plugin from file"""
        try:
            success = plugin_manager.load_plugin_from_file(filepath)
            if success:
                event_manager.event_bus.publish(
                    EventType.PLUGIN_LOADED,
                    {'filepath': filepath},
                    "facade"
                )
            return success
        except Exception as e:
            event_manager.error_occurred(e, "load_plugin")
            return False