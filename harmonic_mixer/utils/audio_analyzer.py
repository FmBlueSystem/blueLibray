"""
Audio file analysis and metadata extraction
"""

import os
from typing import Optional, Dict, Any
import numpy as np

# Optional imports with fallback
try:
    import mutagen
    from mutagen.mp3 import MP3
    from mutagen.flac import FLAC
    from mutagen.mp4 import MP4
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False

try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False

from ..core.harmonic_engine import Track


class AudioAnalyzer:
    """Analyzes audio files to extract metadata and musical features"""
    
    # Mapping of musical keys to Camelot notation
    KEY_TO_CAMELOT = {
        'C': '8B', 'Am': '8A',
        'G': '9B', 'Em': '9A',
        'D': '10B', 'Bm': '10A',
        'A': '11B', 'F#m': '11A',
        'E': '12B', 'C#m': '12A',
        'B': '1B', 'G#m': '1A',
        'F#': '2B', 'D#m': '2A',
        'Db': '3B', 'Bbm': '3A',
        'Ab': '4B', 'Fm': '4A',
        'Eb': '5B', 'Cm': '5A',
        'Bb': '6B', 'Gm': '6A',
        'F': '7B', 'Dm': '7A'
    }
    
    def __init__(self):
        self.sample_rate = 22050  # Default sample rate for analysis
        
    def analyze_file(self, filepath: str, track_id: str) -> Optional[Track]:
        """Analyze an audio file and return a Track object with metadata"""
        if not os.path.exists(filepath):
            return None
        
        # Extract basic metadata
        metadata = self._extract_metadata(filepath)
        
        # Create track object
        track = Track(
            id=track_id,
            title=metadata.get('title', os.path.basename(filepath).rsplit('.', 1)[0]),
            artist=metadata.get('artist', 'Unknown Artist'),
            filepath=filepath,
            duration=metadata.get('duration', 0),
            genre=metadata.get('genre')
        )
        
        # Extract musical features if librosa is available
        if LIBROSA_AVAILABLE and metadata.get('duration', 0) > 0:
            features = self._extract_musical_features(filepath)
            if features:
                track.bpm = features.get('bpm')
                track.key = features.get('key')
                track.energy = features.get('energy')
                track.emotional_intensity = features.get('emotional_intensity')
        else:
            # Use placeholder values
            track.bpm = 120.0
            track.key = "8A"
            track.energy = 5.0
            track.emotional_intensity = 5.0
        
        return track
    
    def _extract_metadata(self, filepath: str) -> Dict[str, Any]:
        """Extract metadata from audio file using mutagen"""
        metadata = {
            'title': os.path.basename(filepath).rsplit('.', 1)[0],
            'artist': 'Unknown Artist',
            'duration': 0,
            'genre': None
        }
        
        if not MUTAGEN_AVAILABLE:
            return metadata
        
        try:
            audio = mutagen.File(filepath)
            if audio is None:
                return metadata
            
            # Extract common tags
            if 'title' in audio and audio['title']:
                metadata['title'] = str(audio['title'][0])
            elif 'TIT2' in audio:  # ID3 tag
                metadata['title'] = str(audio['TIT2'][0])
            
            if 'artist' in audio and audio['artist']:
                metadata['artist'] = str(audio['artist'][0])
            elif 'TPE1' in audio:  # ID3 tag
                metadata['artist'] = str(audio['TPE1'][0])
            
            # Get duration
            if hasattr(audio.info, 'length'):
                metadata['duration'] = audio.info.length
            
            # Extract genre information
            genre = self._extract_genre(audio)
            if genre:
                metadata['genre'] = genre
            
        except Exception as e:
            print(f"Error reading metadata from {filepath}: {e}")
        
        return metadata
    
    def _extract_genre(self, audio) -> Optional[str]:
        """Extract genre from audio metadata tags"""
        if not audio:
            return None
        
        try:
            # MP3 files (ID3 tags) - TCON frame
            if 'TCON' in audio:
                genre_value = audio['TCON']
                if hasattr(genre_value, 'text') and genre_value.text:
                    return str(genre_value.text[0])
                elif isinstance(genre_value, list) and genre_value:
                    return str(genre_value[0])
                else:
                    return str(genre_value)
            
            # FLAC files (Vorbis Comments) - GENRE field
            elif 'GENRE' in audio:
                genre_value = audio['GENRE']
                if isinstance(genre_value, list) and genre_value:
                    return str(genre_value[0])
                return str(genre_value)
            
            # Alternative case for FLAC
            elif 'genre' in audio:
                genre_value = audio['genre']
                if isinstance(genre_value, list) and genre_value:
                    return str(genre_value[0])
                return str(genre_value)
            
            # MP4/M4A files (iTunes atoms) - ©gen atom
            elif '©gen' in audio:
                genre_value = audio['©gen']
                if isinstance(genre_value, list) and genre_value:
                    return str(genre_value[0])
                return str(genre_value)
            
            # Alternative MP4 atom
            elif 'gnre' in audio:
                genre_value = audio['gnre']
                if isinstance(genre_value, list) and genre_value:
                    return str(genre_value[0])
                return str(genre_value)
            
            # Generic fallback - check common variations
            genre_tags = ['Genre', 'GENRE', 'genre']
            for tag in genre_tags:
                if tag in audio:
                    genre_value = audio[tag]
                    if isinstance(genre_value, list) and genre_value:
                        return str(genre_value[0])
                    elif genre_value:
                        return str(genre_value)
        
        except Exception as e:
            print(f"Error extracting genre: {e}")
        
        return None
    
    def _extract_musical_features(self, filepath: str) -> Optional[Dict[str, Any]]:
        """Extract musical features using librosa"""
        if not LIBROSA_AVAILABLE:
            return None
        
        try:
            # Load audio with a shorter duration for faster analysis
            y, sr = librosa.load(filepath, sr=self.sample_rate, duration=30)
            
            features = {}
            
            # Estimate tempo (BPM)
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            features['bpm'] = float(tempo)
            
            # Estimate key (simplified - in real implementation would use more sophisticated methods)
            chroma = librosa.feature.chroma_stft(y=y, sr=sr)
            key_strengths = np.mean(chroma, axis=1)
            estimated_key_idx = np.argmax(key_strengths)
            
            # Map to key names (simplified)
            key_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            estimated_key = key_names[estimated_key_idx]
            
            # For now, assume major keys (in real implementation would detect major/minor)
            features['key'] = self.KEY_TO_CAMELOT.get(estimated_key, '8A')
            
            # Estimate energy (RMS energy)
            rms = librosa.feature.rms(y=y)
            energy_mean = np.mean(rms)
            # Normalize to 1-10 scale
            features['energy'] = min(10, max(1, energy_mean * 50))
            
            # Estimate emotional intensity (based on spectral features)
            spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)
            intensity = np.mean(spectral_centroids) / sr
            # Normalize to 1-10 scale
            features['emotional_intensity'] = min(10, max(1, intensity * 20))
            
            return features
            
        except Exception as e:
            print(f"Error analyzing {filepath}: {e}")
            return None
    
    def batch_analyze(self, filepaths: list, progress_callback=None) -> list:
        """Analyze multiple files with optional progress callback"""
        tracks = []
        
        for i, filepath in enumerate(filepaths):
            track = self.analyze_file(filepath, str(i))
            if track:
                tracks.append(track)
            
            if progress_callback:
                progress_callback(i + 1, len(filepaths))
        
        return tracks