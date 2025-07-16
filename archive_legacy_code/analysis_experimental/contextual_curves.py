"""
Contextual Mixing Curves
Smart playlist generation adapted to time of day, activity, and context
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass
from enum import Enum
from ..core.harmonic_engine import Track


class ContextType(Enum):
    """Types of contexts for mixing"""
    TIME_BASED = "time"
    ACTIVITY_BASED = "activity"  
    ENERGY_BASED = "energy"
    MOOD_BASED = "mood"
    SEASON_BASED = "season"


class CurveShape(Enum):
    """Different curve shapes for energy progression"""
    FLAT = "flat"              # Maintain consistent energy
    ASCENDING = "ascending"     # Gradual energy increase
    DESCENDING = "descending"   # Gradual energy decrease
    PEAK = "peak"              # Build up to peak then down
    VALLEY = "valley"          # Start high, dip, then recover
    WAVE = "wave"              # Multiple peaks and valleys
    BUILD_DROP = "build_drop"   # Build to climax then sharp drop


@dataclass
class ContextualCurve:
    """Defines a contextual mixing curve"""
    name: str
    context_type: ContextType
    context_value: str
    target_curve: CurveShape
    energy_range: Tuple[float, float]  # Min, max energy levels
    duration_minutes: int
    peak_position: float = 0.7  # Where peak occurs (0-1)
    transition_smoothness: float = 0.8  # How smooth transitions are (0-1)
    mood_preference: Optional[List[str]] = None
    activity_preference: Optional[List[str]] = None


class ContextualMixingEngine:
    """
    Advanced mixing engine that adapts to context using LLM metadata
    """
    
    def __init__(self):
        self._init_time_curves()
        self._init_activity_curves()
        self._init_energy_curves()
        self._init_mood_curves()
        self._init_season_curves()
        
        # Weights for contextual factors
        self.context_weights = {
            'time_match': 0.3,      # How well track fits time of day
            'activity_match': 0.25, # How well track fits activity
            'energy_progression': 0.2, # How well energy flows
            'mood_consistency': 0.15,  # Mood coherence
            'crowd_appeal': 0.1     # General crowd appeal
        }
    
    def _init_time_curves(self):
        """Initialize time-based mixing curves"""
        self.time_curves = {
            "morning": ContextualCurve(
                name="Morning Warm-up",
                context_type=ContextType.TIME_BASED,
                context_value="morning",
                target_curve=CurveShape.ASCENDING,
                energy_range=(0.3, 0.7),
                duration_minutes=45,
                peak_position=0.8,
                mood_preference=["uplifting", "energetic", "positive"]
            ),
            "afternoon": ContextualCurve(
                name="Afternoon Energy",
                context_type=ContextType.TIME_BASED, 
                context_value="afternoon",
                target_curve=CurveShape.FLAT,
                energy_range=(0.6, 0.8),
                duration_minutes=60,
                mood_preference=["energetic", "uplifting", "happy"]
            ),
            "evening": ContextualCurve(
                name="Evening Prime Time",
                context_type=ContextType.TIME_BASED,
                context_value="evening",
                target_curve=CurveShape.BUILD_DROP,
                energy_range=(0.7, 0.95),
                duration_minutes=90,
                peak_position=0.6,
                mood_preference=["energetic", "passionate", "festive"]
            ),
            "night": ContextualCurve(
                name="Night Peak Experience", 
                context_type=ContextType.TIME_BASED,
                context_value="night",
                target_curve=CurveShape.PEAK,
                energy_range=(0.8, 1.0),
                duration_minutes=120,
                peak_position=0.5,
                mood_preference=["energetic", "passionate", "intense"]
            ),
            "late_night": ContextualCurve(
                name="Late Night Wind Down",
                context_type=ContextType.TIME_BASED,
                context_value="late_night", 
                target_curve=CurveShape.DESCENDING,
                energy_range=(0.6, 0.3),
                duration_minutes=60,
                mood_preference=["romantic", "passionate", "chill"]
            )
        }
    
    def _init_activity_curves(self):
        """Initialize activity-based mixing curves"""
        self.activity_curves = {
            "party": ContextualCurve(
                name="Party Energy",
                context_type=ContextType.ACTIVITY_BASED,
                context_value="party",
                target_curve=CurveShape.WAVE,
                energy_range=(0.7, 0.95),
                duration_minutes=90,
                mood_preference=["energetic", "festive", "uplifting"],
                activity_preference=["party", "dance", "celebration"]
            ),
            "workout": ContextualCurve(
                name="Workout Motivation",
                context_type=ContextType.ACTIVITY_BASED,
                context_value="workout",
                target_curve=CurveShape.FLAT,
                energy_range=(0.8, 0.95),
                duration_minutes=45,
                mood_preference=["energetic", "motivational", "intense"],
                activity_preference=["workout", "fitness", "energy"]
            ),
            "chill": ContextualCurve(
                name="Chill Vibes",
                context_type=ContextType.ACTIVITY_BASED,
                context_value="chill",
                target_curve=CurveShape.FLAT,
                energy_range=(0.3, 0.6),
                duration_minutes=60,
                mood_preference=["chill", "relaxed", "smooth"],
                activity_preference=["chill", "relax", "background"]
            ),
            "social_dancing": ContextualCurve(
                name="Social Dance Flow",
                context_type=ContextType.ACTIVITY_BASED,
                context_value="social_dancing",
                target_curve=CurveShape.WAVE,
                energy_range=(0.6, 0.85),
                duration_minutes=120,
                mood_preference=["passionate", "romantic", "energetic"],
                activity_preference=["social dancing", "dance", "party"]
            ),
            "focus": ContextualCurve(
                name="Focus Background",
                context_type=ContextType.ACTIVITY_BASED,
                context_value="focus",
                target_curve=CurveShape.FLAT,
                energy_range=(0.2, 0.4),
                duration_minutes=90,
                mood_preference=["calm", "focused", "instrumental"],
                activity_preference=["focus", "work", "background"]
            )
        }
    
    def _init_energy_curves(self):
        """Initialize energy-based curves"""
        self.energy_curves = {
            "warm_up": ContextualCurve(
                name="Warm Up",
                context_type=ContextType.ENERGY_BASED,
                context_value="warm_up",
                target_curve=CurveShape.ASCENDING,
                energy_range=(0.3, 0.7),
                duration_minutes=30
            ),
            "peak_time": ContextualCurve(
                name="Peak Time",
                context_type=ContextType.ENERGY_BASED,
                context_value="peak_time",
                target_curve=CurveShape.FLAT,
                energy_range=(0.8, 0.95),
                duration_minutes=60
            ),
            "cool_down": ContextualCurve(
                name="Cool Down",
                context_type=ContextType.ENERGY_BASED,
                context_value="cool_down",
                target_curve=CurveShape.DESCENDING,
                energy_range=(0.7, 0.3),
                duration_minutes=30
            )
        }
    
    def _init_mood_curves(self):
        """Initialize mood-based curves"""
        self.mood_curves = {
            "romantic_journey": ContextualCurve(
                name="Romantic Journey",
                context_type=ContextType.MOOD_BASED,
                context_value="romantic",
                target_curve=CurveShape.WAVE,
                energy_range=(0.4, 0.8),
                duration_minutes=75,
                mood_preference=["romantic", "passionate", "sensual"]
            ),
            "energy_blast": ContextualCurve(
                name="Energy Blast",
                context_type=ContextType.MOOD_BASED,
                context_value="energetic",
                target_curve=CurveShape.ASCENDING,
                energy_range=(0.6, 1.0),
                duration_minutes=45,
                mood_preference=["energetic", "intense", "powerful"]
            )
        }
    
    def _init_season_curves(self):
        """Initialize season-based curves"""
        self.season_curves = {
            "summer": ContextualCurve(
                name="Summer Vibes",
                context_type=ContextType.SEASON_BASED,
                context_value="summer",
                target_curve=CurveShape.WAVE,
                energy_range=(0.6, 0.9),
                duration_minutes=90,
                mood_preference=["uplifting", "festive", "energetic"]
            ),
            "winter": ContextualCurve(
                name="Winter Warmth",
                context_type=ContextType.SEASON_BASED,
                context_value="winter",
                target_curve=CurveShape.ASCENDING,
                energy_range=(0.4, 0.8),
                duration_minutes=75,
                mood_preference=["warm", "cozy", "romantic"]
            )
        }
    
    def select_contextual_curve(
        self, 
        time_of_day: Optional[str] = None,
        activity: Optional[str] = None,
        target_energy: Optional[str] = None,
        mood_preference: Optional[str] = None,
        season: Optional[str] = None,
        duration_minutes: Optional[int] = None
    ) -> ContextualCurve:
        """
        Select the best contextual curve based on given parameters
        
        Args:
            time_of_day: Time context ("morning", "evening", etc.)
            activity: Activity context ("party", "workout", etc.)
            target_energy: Energy preference ("warm_up", "peak_time", etc.)
            mood_preference: Mood preference ("romantic", "energetic", etc.)
            season: Season context ("summer", "winter", etc.)
            duration_minutes: Target duration
            
        Returns:
            Best matching ContextualCurve
        """
        candidates = []
        
        # Add time-based curves
        if time_of_day and time_of_day.lower() in self.time_curves:
            candidates.append(self.time_curves[time_of_day.lower()])
        
        # Add activity-based curves
        if activity and activity.lower() in self.activity_curves:
            candidates.append(self.activity_curves[activity.lower()])
        
        # Add energy-based curves
        if target_energy and target_energy.lower() in self.energy_curves:
            candidates.append(self.energy_curves[target_energy.lower()])
        
        # Add mood-based curves
        if mood_preference and mood_preference.lower() in self.mood_curves:
            candidates.append(self.mood_curves[mood_preference.lower()])
        
        # Add season-based curves
        if season and season.lower() in self.season_curves:
            candidates.append(self.season_curves[season.lower()])
        
        if not candidates:
            # Default to evening prime time if no matches
            return self.time_curves["evening"]
        
        # Select best candidate based on multiple factors
        best_curve = candidates[0]
        
        # Prefer activity-based curves as they're most specific
        activity_curves = [c for c in candidates if c.context_type == ContextType.ACTIVITY_BASED]
        if activity_curves:
            best_curve = activity_curves[0]
        
        # Adjust duration if specified
        if duration_minutes:
            best_curve.duration_minutes = duration_minutes
        
        return best_curve
    
    def generate_energy_progression(
        self, 
        curve: ContextualCurve, 
        num_tracks: int
    ) -> List[float]:
        """
        Generate energy progression points for a given curve
        
        Args:
            curve: Contextual curve definition
            num_tracks: Number of tracks in playlist
            
        Returns:
            List of target energy levels (0-1) for each track position
        """
        if num_tracks <= 1:
            return [np.mean(curve.energy_range)]
        
        # Generate progression based on curve shape
        positions = np.linspace(0, 1, num_tracks)
        min_energy, max_energy = curve.energy_range
        
        if curve.target_curve == CurveShape.FLAT:
            # Consistent energy with small variations
            base_energy = np.mean(curve.energy_range)
            progression = [base_energy + np.random.normal(0, 0.05) for _ in positions]
            
        elif curve.target_curve == CurveShape.ASCENDING:
            # Gradual increase
            progression = [min_energy + (max_energy - min_energy) * pos for pos in positions]
            
        elif curve.target_curve == CurveShape.DESCENDING:
            # Gradual decrease
            progression = [max_energy - (max_energy - min_energy) * pos for pos in positions]
            
        elif curve.target_curve == CurveShape.PEAK:
            # Build to peak then decline
            peak_pos = curve.peak_position
            progression = []
            for pos in positions:
                if pos <= peak_pos:
                    # Build up
                    energy = min_energy + (max_energy - min_energy) * (pos / peak_pos)
                else:
                    # Come down
                    energy = max_energy - (max_energy - min_energy) * ((pos - peak_pos) / (1 - peak_pos)) * 0.5
                progression.append(energy)
                
        elif curve.target_curve == CurveShape.VALLEY:
            # Start high, dip, then recover
            valley_pos = 0.4
            progression = []
            for pos in positions:
                if pos <= valley_pos:
                    # Go down to valley
                    energy = max_energy - (max_energy - min_energy) * (pos / valley_pos) * 0.6
                else:
                    # Come back up
                    energy = min_energy + (max_energy - min_energy) * ((pos - valley_pos) / (1 - valley_pos))
                progression.append(energy)
                
        elif curve.target_curve == CurveShape.WAVE:
            # Multiple peaks and valleys
            progression = []
            for pos in positions:
                # Create wave pattern with 2-3 cycles
                wave = np.sin(pos * np.pi * 2.5) * 0.3 + 0.5
                energy = min_energy + (max_energy - min_energy) * wave
                progression.append(energy)
                
        elif curve.target_curve == CurveShape.BUILD_DROP:
            # Build to climax then sharp drop
            build_pos = 0.7
            progression = []
            for pos in positions:
                if pos <= build_pos:
                    # Gradual build
                    energy = min_energy + (max_energy - min_energy) * (pos / build_pos)
                else:
                    # Sharp drop then level
                    if pos <= build_pos + 0.1:
                        # Sharp drop
                        energy = max_energy * 0.6
                    else:
                        # Level out
                        energy = max_energy * 0.7
                progression.append(energy)
        
        # Clamp values to range and add smoothing
        progression = [max(min_energy, min(max_energy, e)) for e in progression]
        
        # Apply smoothing based on transition_smoothness
        if curve.transition_smoothness > 0.5 and len(progression) > 2:
            smoothed = []
            for i, energy in enumerate(progression):
                if 0 < i < len(progression) - 1:
                    # Smooth with neighbors
                    smooth_factor = curve.transition_smoothness
                    smoothed_energy = (
                        energy * (1 - smooth_factor) +
                        (progression[i-1] + progression[i+1]) / 2 * smooth_factor
                    )
                    smoothed.append(smoothed_energy)
                else:
                    smoothed.append(energy)
            progression = smoothed
        
        return progression
    
    def calculate_track_context_score(
        self, 
        track: Track, 
        enhanced_metadata: Dict,
        curve: ContextualCurve,
        target_energy: float,
        position_in_playlist: float
    ) -> float:
        """
        Calculate how well a track fits the contextual requirements
        
        Args:
            track: Track to evaluate
            enhanced_metadata: LLM metadata for track
            curve: Current contextual curve
            target_energy: Target energy level for this position
            position_in_playlist: Position in playlist (0-1)
            
        Returns:
            Context fit score (0-1)
        """
        score = 0.0
        total_weight = 0.0
        
        # Time of day match
        track_time = (enhanced_metadata.get('time_of_day', '') or '').lower()
        if track_time and curve.context_type == ContextType.TIME_BASED:
            if track_time == curve.context_value:
                score += self.context_weights['time_match'] * 1.0
            elif self._is_compatible_time(track_time, curve.context_value):
                score += self.context_weights['time_match'] * 0.7
            else:
                score += self.context_weights['time_match'] * 0.2
            total_weight += self.context_weights['time_match']
        elif track_time:
            # Penalize mismatched time contexts more heavily
            if curve.context_type == ContextType.TIME_BASED:
                if not self._is_compatible_time(track_time, curve.context_value):
                    score += self.context_weights['time_match'] * 0.1
                else:
                    score += self.context_weights['time_match'] * 0.4
                total_weight += self.context_weights['time_match']
        
        # Activity match
        track_activity = (enhanced_metadata.get('activity', '') or '').lower()
        if track_activity and curve.activity_preference:
            if track_activity in [a.lower() for a in curve.activity_preference]:
                score += self.context_weights['activity_match'] * 1.0
            elif self._is_compatible_activity(track_activity, curve.activity_preference):
                score += self.context_weights['activity_match'] * 0.6
            else:
                score += self.context_weights['activity_match'] * 0.1
            total_weight += self.context_weights['activity_match']
        elif track_activity and curve.activity_preference:
            # Heavy penalty for completely wrong activity
            score += self.context_weights['activity_match'] * 0.05
            total_weight += self.context_weights['activity_match']
        
        # Energy progression match
        track_danceability = self._normalize_percentage(enhanced_metadata.get('danceability'))
        if track_danceability is not None:
            energy_diff = abs(track_danceability - target_energy)
            energy_score = max(0, 1.0 - energy_diff)
            score += self.context_weights['energy_progression'] * energy_score
            total_weight += self.context_weights['energy_progression']
        
        # Mood consistency
        track_mood = (enhanced_metadata.get('mood', '') or '').lower()
        if track_mood and curve.mood_preference:
            if track_mood in [m.lower() for m in curve.mood_preference]:
                score += self.context_weights['mood_consistency'] * 1.0
            elif self._is_compatible_mood(track_mood, curve.mood_preference):
                score += self.context_weights['mood_consistency'] * 0.6
            else:
                score += self.context_weights['mood_consistency'] * 0.3
            total_weight += self.context_weights['mood_consistency']
        
        # Crowd appeal
        crowd_appeal = self._normalize_percentage(enhanced_metadata.get('crowd_appeal'))
        if crowd_appeal is not None:
            score += self.context_weights['crowd_appeal'] * crowd_appeal
            total_weight += self.context_weights['crowd_appeal']
        
        return score / total_weight if total_weight > 0 else 0.5
    
    def _is_compatible_time(self, track_time: str, curve_time: str) -> bool:
        """Check if times are compatible"""
        compatible_times = {
            'morning': ['afternoon'],
            'afternoon': ['morning', 'evening'],
            'evening': ['afternoon', 'night'],
            'night': ['evening', 'late_night'],
            'late_night': ['night']
        }
        return track_time in compatible_times.get(curve_time, [])
    
    def _is_compatible_activity(self, track_activity: str, curve_activities: List[str]) -> bool:
        """Check if activities are compatible"""
        compatible_activities = {
            'party': ['dance', 'celebration', 'social dancing'],
            'workout': ['fitness', 'energy', 'motivation'],
            'chill': ['relax', 'background', 'lounge'],
            'dance': ['party', 'social dancing', 'celebration'],
            'focus': ['work', 'study', 'background']
        }
        
        for curve_activity in curve_activities:
            if track_activity in compatible_activities.get(curve_activity.lower(), []):
                return True
        return False
    
    def _is_compatible_mood(self, track_mood: str, curve_moods: List[str]) -> bool:
        """Check if moods are compatible"""
        compatible_moods = {
            'energetic': ['uplifting', 'festive', 'powerful'],
            'romantic': ['passionate', 'sensual', 'emotional'],
            'uplifting': ['happy', 'positive', 'energetic'],
            'chill': ['relaxed', 'calm', 'smooth'],
            'passionate': ['romantic', 'intense', 'emotional']
        }
        
        for curve_mood in curve_moods:
            if track_mood in compatible_moods.get(curve_mood.lower(), []):
                return True
        return False
    
    def _normalize_percentage(self, value) -> Optional[float]:
        """Convert percentage strings to float values"""
        if not value or value == "-":
            return None
        
        if isinstance(value, str):
            if value.endswith('%'):
                try:
                    return float(value[:-1]) / 100.0
                except ValueError:
                    return None
            else:
                try:
                    return float(value)
                except ValueError:
                    return None
        elif isinstance(value, (int, float)):
            if value > 1.0:  # Assume it's a percentage (0-100)
                return value / 100.0
            return float(value)
        
        return None
    
    def get_available_curves(self) -> Dict[str, List[str]]:
        """Get all available contextual curves organized by type"""
        return {
            'time': list(self.time_curves.keys()),
            'activity': list(self.activity_curves.keys()),
            'energy': list(self.energy_curves.keys()),
            'mood': list(self.mood_curves.keys()),
            'season': list(self.season_curves.keys())
        }