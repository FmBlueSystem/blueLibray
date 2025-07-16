"""
Advanced Structural Analysis for Music Tracks
Implements onset detection, beat segmentation, and transition point identification
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict
from enum import Enum

# Make librosa optional
try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    librosa = None

# Make scipy optional for audio processing
try:
    from scipy import ndimage
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    ndimage = None


class StructuralElement(Enum):
    """Types of structural elements in a track"""
    INTRO = "intro"
    VERSE = "verse" 
    CHORUS = "chorus"
    BRIDGE = "bridge"
    OUTRO = "outro"
    BREAK = "break"
    BUILD_UP = "buildup"
    DROP = "drop"


@dataclass
class TransitionPoint:
    """Represents an optimal transition point in a track"""
    time_seconds: float
    confidence: float
    element_type: StructuralElement
    energy_level: float
    beat_strength: float
    mix_suitability: float  # 0-1, how suitable for mixing


@dataclass
class StructuralAnalysis:
    """Complete structural analysis of a track"""
    track_id: str
    duration: float
    intro_end: Optional[float] = None
    outro_start: Optional[float] = None
    transition_points: List[TransitionPoint] = None
    beat_grid: List[float] = None  # Beat positions in seconds
    tempo_changes: List[Tuple[float, float]] = None  # (time, new_tempo)
    energy_curve: List[Tuple[float, float]] = None  # (time, energy)
    
    def __post_init__(self):
        if self.transition_points is None:
            self.transition_points = []
        if self.beat_grid is None:
            self.beat_grid = []
        if self.tempo_changes is None:
            self.tempo_changes = []
        if self.energy_curve is None:
            self.energy_curve = []


class StructuralAnalyzer:
    """Analyzes the structural elements of music tracks"""
    
    def __init__(self):
        self.sr = 22050  # Sample rate for analysis
        self.hop_length = 512
        self.frame_length = 2048
        
    def analyze_track(self, filepath: str, track_id: str) -> Optional[StructuralAnalysis]:
        """
        Perform complete structural analysis of a track
        
        Args:
            filepath: Path to audio file
            track_id: Unique identifier for track
            
        Returns:
            StructuralAnalysis object or None if analysis fails
        """
        if not LIBROSA_AVAILABLE:
            print("Warning: librosa not available, returning basic analysis")
            return StructuralAnalysis(track_id=track_id, duration=180.0)  # Default duration
        
        try:
            # Load audio
            y, sr = librosa.load(filepath, sr=self.sr)
            duration = len(y) / sr
            
            # Initialize analysis result
            analysis = StructuralAnalysis(
                track_id=track_id,
                duration=duration
            )
            
            # Perform structural analysis
            analysis.beat_grid = self._detect_beats(y, sr)
            analysis.intro_end, analysis.outro_start = self._detect_intro_outro(y, sr)
            analysis.transition_points = self._find_transition_points(y, sr, analysis.beat_grid)
            analysis.tempo_changes = self._detect_tempo_changes(y, sr)
            analysis.energy_curve = self._compute_energy_curve(y, sr)
            
            return analysis
            
        except Exception as e:
            print(f"Structural analysis failed for {filepath}: {e}")
            return None
    
    def _detect_beats(self, y: np.ndarray, sr: int) -> List[float]:
        """Detect beat positions using onset detection"""
        try:
            # Track beats
            tempo, beats = librosa.beat.beat_track(y=y, sr=sr, hop_length=self.hop_length)
            
            # Convert beat frames to time
            beat_times = librosa.frames_to_time(beats, sr=sr, hop_length=self.hop_length)
            
            return beat_times.tolist()
            
        except Exception:
            return []
    
    def _detect_intro_outro(self, y: np.ndarray, sr: int) -> Tuple[Optional[float], Optional[float]]:
        """Detect intro and outro sections"""
        try:
            duration = len(y) / sr
            
            # Compute spectral centroid for energy analysis
            spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            times = librosa.frames_to_time(np.arange(len(spectral_centroid)), sr=sr)
            
            # Smooth the spectral centroid
            if SCIPY_AVAILABLE:
                smoothed = ndimage.gaussian_filter1d(spectral_centroid, sigma=2)
            else:
                # Simple smoothing fallback
                smoothed = spectral_centroid
            
            # Find where energy stabilizes (end of intro)
            intro_end = None
            if len(smoothed) > 100:  # Ensure enough data
                # Look for energy stabilization in first 30% of track
                search_end = min(int(len(smoothed) * 0.3), len(smoothed))
                energy_diff = np.diff(smoothed[:search_end])
                
                # Find first point where energy change becomes minimal
                stable_threshold = np.std(energy_diff) * 0.5
                for i, diff in enumerate(energy_diff):
                    if abs(diff) < stable_threshold and i > len(energy_diff) * 0.1:
                        intro_end = times[i]
                        break
            
            # Find outro start (where energy starts declining)
            outro_start = None
            if len(smoothed) > 100:
                # Look in last 30% of track
                search_start = max(int(len(smoothed) * 0.7), 0)
                energy_segment = smoothed[search_start:]
                
                # Find sustained decline
                decline_count = 0
                for i in range(1, len(energy_segment)):
                    if energy_segment[i] < energy_segment[i-1]:
                        decline_count += 1
                        if decline_count >= 5:  # Sustained decline
                            outro_start = times[search_start + i - 4]
                            break
                    else:
                        decline_count = 0
            
            return intro_end, outro_start
            
        except Exception:
            return None, None
    
    def _find_transition_points(self, y: np.ndarray, sr: int, beats: List[float]) -> List[TransitionPoint]:
        """Find optimal transition points for mixing"""
        if not beats:
            return []
        
        try:
            transition_points = []
            
            # Compute features for transition analysis
            spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            rms_energy = librosa.feature.rms(y=y, hop_length=self.hop_length)[0]
            
            # Convert to time domain
            feature_times = librosa.frames_to_time(np.arange(len(rms_energy)), sr=sr)
            
            # Find transitions at beat boundaries
            for beat_time in beats:
                # Skip beats too close to start/end
                if beat_time < 10 or beat_time > len(y)/sr - 10:
                    continue
                
                # Find closest feature frame
                frame_idx = np.argmin(np.abs(feature_times - beat_time))
                
                if frame_idx >= 5 and frame_idx < len(rms_energy) - 5:
                    # Analyze local stability (5 frames = ~0.5 seconds)
                    local_energy = rms_energy[frame_idx-5:frame_idx+5]
                    energy_stability = 1.0 - (np.std(local_energy) / (np.mean(local_energy) + 1e-8))
                    
                    # Compute beat strength
                    beat_strength = self._compute_beat_strength(y, sr, beat_time)
                    
                    # Determine structural element type
                    element_type = self._classify_structural_element(
                        beat_time, len(y)/sr, rms_energy[frame_idx]
                    )
                    
                    # Compute mix suitability
                    mix_suitability = self._compute_mix_suitability(
                        energy_stability, beat_strength, element_type
                    )
                    
                    if mix_suitability > 0.3:  # Only keep decent transition points
                        transition_point = TransitionPoint(
                            time_seconds=beat_time,
                            confidence=energy_stability,
                            element_type=element_type,
                            energy_level=float(rms_energy[frame_idx]),
                            beat_strength=beat_strength,
                            mix_suitability=mix_suitability
                        )
                        transition_points.append(transition_point)
            
            # Sort by mix suitability and keep top candidates
            transition_points.sort(key=lambda x: x.mix_suitability, reverse=True)
            return transition_points[:20]  # Keep top 20 transition points
            
        except Exception:
            return []
    
    def _compute_beat_strength(self, y: np.ndarray, sr: int, beat_time: float) -> float:
        """Compute the strength of a beat at given time"""
        try:
            # Convert time to sample
            sample_idx = int(beat_time * sr)
            
            # Extract small window around beat
            window_size = int(0.1 * sr)  # 100ms window
            start_idx = max(0, sample_idx - window_size // 2)
            end_idx = min(len(y), sample_idx + window_size // 2)
            
            if end_idx - start_idx < window_size // 2:
                return 0.0
            
            window = y[start_idx:end_idx]
            
            # Compute onset strength
            onset_envelope = librosa.onset.onset_strength(
                y=window, sr=sr, hop_length=self.hop_length//4
            )
            
            return float(np.max(onset_envelope)) if len(onset_envelope) > 0 else 0.0
            
        except Exception:
            return 0.0
    
    def _classify_structural_element(self, time: float, duration: float, energy: float) -> StructuralElement:
        """Classify what type of structural element this is"""
        position_ratio = time / duration
        
        if position_ratio < 0.15:
            return StructuralElement.INTRO
        elif position_ratio > 0.85:
            return StructuralElement.OUTRO
        elif energy > 0.5:  # High energy sections
            if 0.3 < position_ratio < 0.7:
                return StructuralElement.CHORUS
            else:
                return StructuralElement.BUILD_UP
        else:  # Lower energy sections
            return StructuralElement.VERSE
    
    def _compute_mix_suitability(self, stability: float, beat_strength: float, 
                                element_type: StructuralElement) -> float:
        """Compute how suitable this point is for mixing"""
        # Base score from stability and beat strength
        base_score = (stability * 0.6 + beat_strength * 0.4)
        
        # Modifier based on structural element
        element_modifiers = {
            StructuralElement.INTRO: 0.9,
            StructuralElement.VERSE: 0.8,
            StructuralElement.CHORUS: 0.7,  # Chorus can be tricky
            StructuralElement.BRIDGE: 0.6,
            StructuralElement.OUTRO: 0.9,
            StructuralElement.BREAK: 0.95,  # Breaks are great for mixing
            StructuralElement.BUILD_UP: 0.3,  # Build-ups are risky
            StructuralElement.DROP: 0.4      # Drops are tricky
        }
        
        modifier = element_modifiers.get(element_type, 0.5)
        return base_score * modifier
    
    def _detect_tempo_changes(self, y: np.ndarray, sr: int) -> List[Tuple[float, float]]:
        """Detect significant tempo changes throughout the track"""
        try:
            # Analyze tempo in overlapping windows
            window_duration = 10  # 10 second windows
            hop_duration = 5      # 5 second hops
            
            window_samples = int(window_duration * sr)
            hop_samples = int(hop_duration * sr)
            
            tempo_changes = []
            previous_tempo = None
            
            for start_sample in range(0, len(y) - window_samples, hop_samples):
                end_sample = start_sample + window_samples
                window = y[start_sample:end_sample]
                
                try:
                    tempo, _ = librosa.beat.beat_track(y=window, sr=sr)
                    current_time = start_sample / sr
                    
                    if previous_tempo is not None:
                        # Check for significant tempo change (>5 BPM)
                        if abs(tempo - previous_tempo) > 5:
                            tempo_changes.append((current_time, float(tempo)))
                    
                    previous_tempo = tempo
                    
                except Exception:
                    continue
            
            return tempo_changes
            
        except Exception:
            return []
    
    def _compute_energy_curve(self, y: np.ndarray, sr: int) -> List[Tuple[float, float]]:
        """Compute energy curve over time"""
        try:
            # Compute RMS energy with larger hop for smoother curve
            rms_energy = librosa.feature.rms(y=y, hop_length=self.hop_length*4)[0]
            times = librosa.frames_to_time(
                np.arange(len(rms_energy)), sr=sr, hop_length=self.hop_length*4
            )
            
            # Smooth the energy curve
            if SCIPY_AVAILABLE:
                smoothed_energy = ndimage.gaussian_filter1d(rms_energy, sigma=1)
            else:
                # Simple smoothing fallback
                smoothed_energy = rms_energy
            
            # Normalize to 0-1 range
            if np.max(smoothed_energy) > 0:
                smoothed_energy = smoothed_energy / np.max(smoothed_energy)
            
            # Return as list of (time, energy) tuples
            return [(float(t), float(e)) for t, e in zip(times, smoothed_energy)]
            
        except Exception:
            return []
    
    def get_best_mix_out_point(self, analysis: StructuralAnalysis, 
                              target_time: Optional[float] = None) -> Optional[TransitionPoint]:
        """Get the best point to mix out of this track"""
        if not analysis.transition_points:
            return None
        
        # If target time specified, find closest suitable point
        if target_time is not None:
            suitable_points = [
                tp for tp in analysis.transition_points 
                if tp.mix_suitability > 0.6 and abs(tp.time_seconds - target_time) < 30
            ]
            if suitable_points:
                return min(suitable_points, key=lambda x: abs(x.time_seconds - target_time))
        
        # Otherwise return highest scoring point
        return max(analysis.transition_points, key=lambda x: x.mix_suitability)
    
    def get_best_mix_in_point(self, analysis: StructuralAnalysis) -> Optional[TransitionPoint]:
        """Get the best point to mix into this track"""
        if not analysis.transition_points:
            return None
        
        # Prefer points after intro but before outro
        intro_end = analysis.intro_end or 0
        outro_start = analysis.outro_start or analysis.duration
        
        suitable_points = [
            tp for tp in analysis.transition_points
            if tp.time_seconds > intro_end and tp.time_seconds < outro_start - 30
            and tp.mix_suitability > 0.5
        ]
        
        if suitable_points:
            # Prefer earlier suitable points for mix-in
            return max(suitable_points, key=lambda x: x.mix_suitability)
        
        return max(analysis.transition_points, key=lambda x: x.mix_suitability)