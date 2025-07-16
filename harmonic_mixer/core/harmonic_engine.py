"""
Advanced Harmonic Mixing Engine
Implements an intelligent mixing algorithm that goes beyond Camelot wheel
Enhanced with structural analysis and multi-factor compatibility scoring
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
from enum import Enum


class CamelotKey:
    """Represents a key in Camelot notation"""
    KEYS = {
        '1A': 'Ab minor', '1B': 'B major',
        '2A': 'Eb minor', '2B': 'F# major',
        '3A': 'Bb minor', '3B': 'Db major',
        '4A': 'F minor', '4B': 'Ab major',
        '5A': 'C minor', '5B': 'Eb major',
        '6A': 'G minor', '6B': 'Bb major',
        '7A': 'D minor', '7B': 'F major',
        '8A': 'A minor', '8B': 'C major',
        '9A': 'E minor', '9B': 'G major',
        '10A': 'B minor', '10B': 'D major',
        '11A': 'F# minor', '11B': 'A major',
        '12A': 'C# minor', '12B': 'E major'
    }
    
    @staticmethod
    def get_compatible_keys(key: str) -> List[str]:
        """Get harmonically compatible keys"""
        if not key or key not in CamelotKey.KEYS:
            return []
        
        number = int(key[:-1])
        letter = key[-1]
        
        compatible = [key]  # Same key
        
        # Adjacent keys on the wheel
        prev_num = 12 if number == 1 else number - 1
        next_num = 1 if number == 12 else number + 1
        
        compatible.extend([
            f"{prev_num}{letter}",
            f"{next_num}{letter}",
            f"{number}{'A' if letter == 'B' else 'B'}"
        ])
        
        return compatible


class MixMode(Enum):
    """Different mixing modes for various contexts"""
    CLASSIC_CAMELOT = "classic"
    INTELLIGENT = "intelligent" 
    ENERGY_FLOW = "energy"
    EMOTIONAL = "emotional"
    STRUCTURAL = "structural"  # New mode with enhanced structural analysis


@dataclass
class Track:
    """Represents a music track with all metadata"""
    id: str
    title: str
    artist: str
    filepath: str
    key: Optional[str] = None
    bpm: Optional[float] = None
    energy: Optional[float] = None  # 1-10 scale
    emotional_intensity: Optional[float] = None  # 1-10 scale
    genre: Optional[str] = None
    duration: Optional[float] = None  # seconds
    is_available: bool = True  # Whether the file is currently accessible
    
    def __hash__(self):
        return hash(self.id)


class HarmonicMixingEngine:
    """Advanced harmonic mixing algorithm implementation"""
    
    def __init__(self):
        self.weights = {
            'key': 0.4,
            'bpm': 0.3,
            'energy': 0.2,
            'emotional': 0.1
        }
        self.mode = MixMode.INTELLIGENT
        self.bpm_tolerance = 6.0  # ±3 BPM acceptable
        self.energy_tolerance = 2.0  # ±2 energy levels
        
        # Enhanced compatibility engine (lazy loaded)
        self._enhanced_engine = None
        
    def set_mode(self, mode: MixMode):
        """Set the mixing mode and adjust weights accordingly"""
        self.mode = mode
        
        if mode == MixMode.CLASSIC_CAMELOT:
            self.weights = {'key': 0.9, 'bpm': 0.1, 'energy': 0, 'emotional': 0}
        elif mode == MixMode.ENERGY_FLOW:
            self.weights = {'key': 0.2, 'bpm': 0.2, 'energy': 0.5, 'emotional': 0.1}
        elif mode == MixMode.EMOTIONAL:
            self.weights = {'key': 0.2, 'bpm': 0.1, 'energy': 0.2, 'emotional': 0.5}
        elif mode == MixMode.STRUCTURAL:
            # Balanced weights optimized for structural analysis
            self.weights = {'key': 0.25, 'bpm': 0.25, 'energy': 0.25, 'emotional': 0.25}
        else:  # INTELLIGENT
            self.weights = {'key': 0.4, 'bpm': 0.3, 'energy': 0.2, 'emotional': 0.1}
    
    def calculate_compatibility(self, track1: Track, track2: Track) -> float:
        """Calculate compatibility score between two tracks (0-1)"""
        score = 0.0
        
        # Key compatibility
        if track1.key and track2.key:
            key_score = self._calculate_key_score(track1.key, track2.key)
            score += self.weights['key'] * key_score
        
        # BPM compatibility
        if track1.bpm and track2.bpm:
            bpm_score = self._calculate_bpm_score(track1.bpm, track2.bpm)
            score += self.weights['bpm'] * bpm_score
        
        # Energy compatibility
        if track1.energy and track2.energy:
            energy_score = self._calculate_energy_score(track1.energy, track2.energy)
            score += self.weights['energy'] * energy_score
        
        # Emotional compatibility
        if track1.emotional_intensity and track2.emotional_intensity:
            emotional_score = self._calculate_emotional_score(
                track1.emotional_intensity, track2.emotional_intensity
            )
            score += self.weights['emotional'] * emotional_score
        
        return min(score, 1.0)
    
    def _calculate_key_score(self, key1: str, key2: str) -> float:
        """Calculate key compatibility score"""
        if key1 == key2:
            return 1.0
        
        compatible_keys = CamelotKey.get_compatible_keys(key1)
        if key2 in compatible_keys:
            return 0.8
        
        # Check for relative major/minor
        num1, letter1 = int(key1[:-1]), key1[-1]
        num2, letter2 = int(key2[:-1]), key2[-1]
        
        if num1 == num2 and letter1 != letter2:
            return 0.7
        
        # Penalize distant keys
        distance = min(abs(num1 - num2), 12 - abs(num1 - num2))
        return max(0, 0.5 - (distance * 0.1))
    
    def _calculate_bpm_score(self, bpm1: float, bpm2: float) -> float:
        """Calculate BPM compatibility score"""
        diff = abs(bpm1 - bpm2)
        
        if diff <= 2:
            return 1.0
        elif diff <= self.bpm_tolerance:
            return 1.0 - (diff / self.bpm_tolerance) * 0.5
        else:
            # Check for half/double time compatibility
            if abs(bpm1 * 2 - bpm2) <= 4 or abs(bpm1 - bpm2 * 2) <= 4:
                return 0.6
            return max(0, 0.3 - (diff - self.bpm_tolerance) * 0.02)
    
    def _calculate_energy_score(self, energy1: float, energy2: float) -> float:
        """Calculate energy compatibility score"""
        diff = abs(energy1 - energy2)
        
        if diff <= 1:
            return 1.0
        elif diff <= self.energy_tolerance:
            return 0.8
        else:
            return max(0, 0.5 - (diff - self.energy_tolerance) * 0.1)
    
    def _calculate_emotional_score(self, emotion1: float, emotion2: float) -> float:
        """Calculate emotional compatibility score"""
        diff = abs(emotion1 - emotion2)
        return max(0, 1.0 - (diff / 10.0))
    
    def generate_playlist(
        self, 
        tracks: List[Track], 
        start_track: Optional[Track] = None,
        target_length: int = 10,
        progression_curve: str = "neutral"
    ) -> List[Track]:
        """Generate an optimal playlist using the mixing algorithm"""
        if not tracks:
            return []
        
        if start_track is None:
            start_track = tracks[0]
        elif start_track not in tracks:
            return []
        
        playlist = [start_track]
        remaining_tracks = [t for t in tracks if t != start_track]
        
        while len(playlist) < target_length and remaining_tracks:
            current_track = playlist[-1]
            
            # Calculate compatibility scores for all remaining tracks
            scores = []
            for track in remaining_tracks:
                score = self.calculate_compatibility(current_track, track)
                
                # Apply progression curve modifiers
                if progression_curve == "ascending" and track.energy:
                    if track.energy > current_track.energy:
                        score *= 1.2
                elif progression_curve == "descending" and track.energy:
                    if track.energy < current_track.energy:
                        score *= 1.2
                
                scores.append((track, score))
            
            # Sort by score and select best match
            scores.sort(key=lambda x: x[1], reverse=True)
            
            if scores and scores[0][1] > 0.3:  # Minimum threshold
                next_track = scores[0][0]
                playlist.append(next_track)
                remaining_tracks.remove(next_track)
            else:
                break
        
        return playlist
    
    def build_compatibility_matrix(self, tracks: List[Track]) -> np.ndarray:
        """Build a compatibility matrix for all tracks"""
        n = len(tracks)
        matrix = np.zeros((n, n))
        
        for i in range(n):
            for j in range(n):
                if i != j:
                    matrix[i][j] = self.calculate_compatibility(tracks[i], tracks[j])
        
        return matrix
    
    def get_enhanced_engine(self):
        """Get or create enhanced compatibility engine"""
        if self._enhanced_engine is None:
            try:
                from ..analysis.enhanced_compatibility import EnhancedCompatibilityEngine
                self._enhanced_engine = EnhancedCompatibilityEngine(self)
            except ImportError:
                # Fallback if enhanced engine not available
                self._enhanced_engine = None
        return self._enhanced_engine
    
    def calculate_enhanced_compatibility(
        self, 
        track1: Track, 
        track2: Track, 
        structural_data: Optional[Dict] = None,
        enhanced_metadata: Optional[Dict] = None
    ) -> float:
        """
        Calculate compatibility using enhanced structural and stylistic analysis if available
        
        Args:
            track1: Source track
            track2: Target track
            structural_data: Dict with 'track1' and 'track2' structural analysis
            enhanced_metadata: Dict with 'track1' and 'track2' LLM metadata
            
        Returns:
            Enhanced compatibility score (0-1)
        """
        enhanced_engine = self.get_enhanced_engine()
        
        if enhanced_engine:
            structural1 = structural_data.get('track1') if structural_data else None
            structural2 = structural_data.get('track2') if structural_data else None
            
            metadata1 = enhanced_metadata.get('track1') if enhanced_metadata else None
            metadata2 = enhanced_metadata.get('track2') if enhanced_metadata else None
            
            return enhanced_engine.calculate_enhanced_compatibility(
                track1, track2, structural1, structural2, metadata1, metadata2
            )
        
        # Fallback to standard compatibility
        return self.calculate_compatibility(track1, track2)
    
    def supports_structural_analysis(self) -> bool:
        """Check if structural analysis is available"""
        try:
            from ..analysis.structural_analyzer import StructuralAnalyzer
            return True
        except ImportError:
            return False
    
    def supports_stylistic_analysis(self) -> bool:
        """Check if stylistic analysis is available"""
        enhanced_engine = self.get_enhanced_engine()
        return enhanced_engine and enhanced_engine.supports_stylistic_analysis() if enhanced_engine else False