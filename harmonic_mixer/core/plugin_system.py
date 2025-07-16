"""
Plugin architecture for extensible mixing algorithms and features
"""

import importlib
import inspect
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Type, Callable
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

from .harmonic_engine import Track


class PluginType(Enum):
    """Types of plugins supported"""
    MIXING_ALGORITHM = "mixing_algorithm"
    AUDIO_ANALYZER = "audio_analyzer"
    EXPORT_FORMAT = "export_format"
    EXPORT = "export"  # For advanced export plugins like Serato
    UI_COMPONENT = "ui_component"
    PREPROCESSING = "preprocessing"


@dataclass
class PluginMetadata:
    """Plugin metadata information"""
    name: str
    version: str
    author: str
    description: str
    plugin_type: PluginType
    dependencies: List[str]
    config_schema: Optional[Dict] = None


class PluginInterface(ABC):
    """Base interface for all plugins"""
    
    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata"""
        pass
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize plugin with configuration"""
        pass
    
    @abstractmethod
    def cleanup(self):
        """Cleanup plugin resources"""
        pass


class MixingAlgorithmPlugin(PluginInterface):
    """Interface for mixing algorithm plugins"""
    
    @abstractmethod
    def calculate_compatibility(self, track1: Track, track2: Track) -> float:
        """Calculate compatibility score between tracks"""
        pass
    
    @abstractmethod
    def get_weight_parameters(self) -> Dict[str, Dict]:
        """Return available weight parameters and their ranges"""
        pass
    
    @abstractmethod
    def set_weights(self, weights: Dict[str, float]):
        """Set algorithm weights"""
        pass


class AudioAnalyzerPlugin(PluginInterface):
    """Interface for audio analyzer plugins"""
    
    @abstractmethod
    def extract_features(self, filepath: str) -> Dict[str, Any]:
        """Extract audio features from file"""
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """Return list of supported file formats"""
        pass


class ExportFormatPlugin(PluginInterface):
    """Interface for playlist export plugins"""
    
    @abstractmethod
    def export_playlist(self, tracks: List[Track], filepath: str, options: Dict = None) -> bool:
        """Export playlist to file"""
        pass
    
    @abstractmethod
    def get_file_extension(self) -> str:
        """Return file extension for this format"""
        pass


class ExportPlugin(PluginInterface):
    """Interface for advanced export plugins (like Serato integration)"""
    
    @abstractmethod
    def export_playlist(self, tracks: List[Track], playlist_name: str, options: Dict = None) -> Any:
        """Export playlist to external system"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if export target is available"""
        pass
    
    @abstractmethod
    def get_export_options(self) -> Dict[str, Any]:
        """Get available export options"""
        pass


# Built-in Plugin Implementations

class MLMixingAlgorithm(MixingAlgorithmPlugin):
    """Machine Learning-based mixing algorithm (placeholder)"""
    
    def __init__(self):
        self.weights = {'ml_score': 1.0}
        self.model = None  # Placeholder for ML model
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="ML Mixing Algorithm",
            version="1.0.0",
            author="BlueLibrary Team",
            description="Machine learning-based compatibility scoring",
            plugin_type=PluginType.MIXING_ALGORITHM,
            dependencies=["scikit-learn", "numpy"]
        )
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize ML model"""
        # In real implementation, load trained model
        print("ML Algorithm initialized")
        return True
    
    def cleanup(self):
        """Cleanup resources"""
        self.model = None
    
    def calculate_compatibility(self, track1: Track, track2: Track) -> float:
        """Calculate ML-based compatibility"""
        # Placeholder implementation
        # Real implementation would use trained model
        
        features = []
        
        # Extract features for ML model
        if track1.key and track2.key:
            features.extend([
                self._key_to_number(track1.key),
                self._key_to_number(track2.key)
            ])
        
        if track1.bpm and track2.bpm:
            features.extend([track1.bpm, track2.bpm])
        
        if track1.energy and track2.energy:
            features.extend([track1.energy, track2.energy])
        
        # Simple heuristic for demonstration
        # Real implementation would use ML model prediction
        if len(features) >= 6:
            key_diff = abs(features[0] - features[1])
            bpm_diff = abs(features[2] - features[3])
            energy_diff = abs(features[4] - features[5])
            
            score = max(0, 1.0 - (key_diff * 0.1 + bpm_diff * 0.01 + energy_diff * 0.05))
            return min(score, 1.0)
        
        return 0.5
    
    def _key_to_number(self, key: str) -> int:
        """Convert Camelot key to number for ML processing"""
        if not key or len(key) < 2:
            return 0
        
        try:
            number = int(key[:-1])
            letter = key[-1]
            return number + (12 if letter == 'B' else 0)
        except ValueError:
            return 0
    
    def get_weight_parameters(self) -> Dict[str, Dict]:
        """Return ML-specific parameters"""
        return {
            'ml_score': {
                'min': 0.0,
                'max': 1.0,
                'default': 1.0,
                'description': 'ML model prediction weight'
            }
        }
    
    def set_weights(self, weights: Dict[str, float]):
        """Set ML algorithm weights"""
        self.weights.update(weights)


class M3UExportPlugin(ExportFormatPlugin):
    """M3U playlist export plugin"""
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="M3U Exporter",
            version="1.0.0",
            author="BlueLibrary Team",
            description="Export playlists to M3U format",
            plugin_type=PluginType.EXPORT_FORMAT,
            dependencies=[]
        )
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        return True
    
    def cleanup(self):
        pass
    
    def export_playlist(self, tracks: List[Track], filepath: str, options: Dict = None) -> bool:
        """Export playlist to M3U format"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("#EXTM3U\n")
                
                for track in tracks:
                    # Write track info
                    duration = int(track.duration) if track.duration else -1
                    title = f"{track.artist} - {track.title}"
                    f.write(f"#EXTINF:{duration},{title}\n")
                    f.write(f"{track.filepath}\n")
            
            return True
        except Exception as e:
            print(f"Failed to export M3U playlist: {e}")
            return False
    
    def get_file_extension(self) -> str:
        return ".m3u"


class PluginManager:
    """Manages plugin lifecycle and registration"""
    
    def __init__(self):
        self.plugins: Dict[str, PluginInterface] = {}
        self.plugin_types: Dict[PluginType, List[str]] = {
            plugin_type: [] for plugin_type in PluginType
        }
        
        # Register built-in plugins
        self._register_builtin_plugins()
    
    def _register_builtin_plugins(self):
        """Register built-in plugins"""
        builtin_plugins = [
            MLMixingAlgorithm(),
            M3UExportPlugin()
        ]
        
        for plugin in builtin_plugins:
            self.register_plugin(plugin)
        
        # Register LLM plugin if available
        try:
            from ..llm.llm_mixing_plugin import LLMixingAlgorithmPlugin
            self.register_plugin(LLMixingAlgorithmPlugin())
        except ImportError as e:
            print(f"LLM plugin not available: {e}")
        
        # Register Serato export plugin if available
        try:
            from ..integrations.serato_export_plugin import create_serato_export_plugin
            self.register_plugin(create_serato_export_plugin())
        except ImportError as e:
            print(f"Serato export plugin not available: {e}")
    
    def register_plugin(self, plugin: PluginInterface) -> bool:
        """Register a plugin"""
        try:
            # Initialize plugin
            if not plugin.initialize({}):
                return False
            
            # Store plugin
            plugin_name = plugin.metadata.name
            self.plugins[plugin_name] = plugin
            self.plugin_types[plugin.metadata.plugin_type].append(plugin_name)
            
            print(f"Registered plugin: {plugin_name}")
            return True
            
        except Exception as e:
            print(f"Failed to register plugin {plugin.metadata.name}: {e}")
            return False
    
    def unregister_plugin(self, plugin_name: str):
        """Unregister a plugin"""
        if plugin_name in self.plugins:
            plugin = self.plugins[plugin_name]
            plugin.cleanup()
            
            # Remove from registry
            del self.plugins[plugin_name]
            self.plugin_types[plugin.metadata.plugin_type].remove(plugin_name)
            
            print(f"Unregistered plugin: {plugin_name}")
    
    def get_plugin(self, plugin_name: str) -> Optional[PluginInterface]:
        """Get plugin by name"""
        return self.plugins.get(plugin_name)
    
    def get_plugins_by_type(self, plugin_type: PluginType) -> List[PluginInterface]:
        """Get all plugins of specific type"""
        plugin_names = self.plugin_types[plugin_type]
        return [self.plugins[name] for name in plugin_names]
    
    def list_plugins(self) -> List[PluginMetadata]:
        """List all registered plugins"""
        return [plugin.metadata for plugin in self.plugins.values()]
    
    def load_plugin_from_file(self, filepath: str) -> bool:
        """Load plugin from Python file"""
        try:
            plugin_path = Path(filepath)
            if not plugin_path.exists():
                return False
            
            # Import module dynamically
            spec = importlib.util.spec_from_file_location("plugin_module", filepath)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find plugin classes in module
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, PluginInterface) and 
                    obj != PluginInterface):
                    
                    # Create and register plugin instance
                    plugin_instance = obj()
                    return self.register_plugin(plugin_instance)
            
            return False
            
        except Exception as e:
            print(f"Failed to load plugin from {filepath}: {e}")
            return False
    
    def cleanup_all(self):
        """Cleanup all plugins"""
        for plugin in self.plugins.values():
            try:
                plugin.cleanup()
            except Exception as e:
                print(f"Error cleaning up plugin {plugin.metadata.name}: {e}")
        
        self.plugins.clear()
        for plugin_type in self.plugin_types:
            self.plugin_types[plugin_type].clear()


class PluginConfigManager:
    """Manages plugin configurations"""
    
    def __init__(self, config_dir: str = None):
        if config_dir is None:
            config_dir = Path.home() / '.bluelibrary' / 'plugins'
        
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def save_plugin_config(self, plugin_name: str, config: Dict[str, Any]):
        """Save plugin configuration"""
        config_file = self.config_dir / f"{plugin_name}.json"
        
        try:
            import json
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Failed to save config for {plugin_name}: {e}")
    
    def load_plugin_config(self, plugin_name: str) -> Dict[str, Any]:
        """Load plugin configuration"""
        config_file = self.config_dir / f"{plugin_name}.json"
        
        if not config_file.exists():
            return {}
        
        try:
            import json
            with open(config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Failed to load config for {plugin_name}: {e}")
            return {}
    
    def delete_plugin_config(self, plugin_name: str):
        """Delete plugin configuration"""
        config_file = self.config_dir / f"{plugin_name}.json"
        
        if config_file.exists():
            config_file.unlink()


# Plugin Registry - Global instance
plugin_manager = PluginManager()
plugin_config_manager = PluginConfigManager()