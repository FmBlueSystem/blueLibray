"""
Stylistic Compatibility Matrix
Advanced compatibility scoring using LLM-enhanced metadata (Subgenre, Mood, Era, Language, etc.)
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
from ..core.harmonic_engine import Track


class CompatibilityLevel(Enum):
    """Compatibility levels for stylistic matching"""
    PERFECT = 1.0      # Same style/perfect match
    EXCELLENT = 0.9    # Very compatible styles
    GOOD = 0.7         # Compatible with minor adjustments
    FAIR = 0.5         # Workable but noticeable difference
    POOR = 0.3         # Difficult transition
    INCOMPATIBLE = 0.1 # Should avoid


@dataclass
class StyleProfile:
    """Complete style profile for a track"""
    subgenre: Optional[str] = None
    mood: Optional[str] = None
    era: Optional[str] = None
    language: Optional[str] = None
    danceability: Optional[float] = None
    time_of_day: Optional[str] = None
    activity: Optional[str] = None
    season: Optional[str] = None
    crowd_appeal: Optional[float] = None
    mix_friendly: Optional[float] = None


class StylisticCompatibilityMatrix:
    """
    Advanced stylistic compatibility scoring based on LLM metadata
    """
    
    def __init__(self):
        # Initialize compatibility matrices for different style dimensions
        self._init_subgenre_matrix()
        self._init_mood_matrix()
        self._init_era_matrix()
        self._init_language_matrix()
        self._init_activity_matrix()
        self._init_time_of_day_matrix()
        self._init_season_matrix()
        
        # Weights for different style factors
        self.style_weights = {
            'subgenre': 0.25,     # Most important for style continuity
            'mood': 0.2,          # Critical for emotional flow
            'era': 0.15,          # Important for temporal coherence
            'language': 0.1,      # Moderate impact
            'activity': 0.1,      # Context-dependent
            'time_of_day': 0.1,   # Context-dependent
            'season': 0.05,       # Minor impact
            'danceability': 0.05  # Minor direct impact
        }
    
    def _init_subgenre_matrix(self):
        """Initialize subgenre compatibility matrix"""
        self.subgenre_compatibility = {
            # Salsa variations
            "salsa romantica": {
                "salsa romantica": CompatibilityLevel.PERFECT,
                "romantic salsa": CompatibilityLevel.PERFECT,
                "salsa dura": CompatibilityLevel.GOOD,
                "tropical salsa": CompatibilityLevel.GOOD,
                "classic salsa": CompatibilityLevel.EXCELLENT,
                "latin ballad": CompatibilityLevel.FAIR,
                "bachata": CompatibilityLevel.FAIR
            },
            "salsa dura": {
                "salsa dura": CompatibilityLevel.PERFECT,
                "salsa romantica": CompatibilityLevel.GOOD,
                "tropical salsa": CompatibilityLevel.EXCELLENT,
                "classic salsa": CompatibilityLevel.EXCELLENT,
                "afro-cuban jazz": CompatibilityLevel.GOOD,
                "merengue": CompatibilityLevel.FAIR
            },
            "tropical salsa": {
                "tropical salsa": CompatibilityLevel.PERFECT,
                "salsa dura": CompatibilityLevel.EXCELLENT,
                "salsa romantica": CompatibilityLevel.GOOD,
                "merengue": CompatibilityLevel.GOOD,
                "cumbia": CompatibilityLevel.FAIR
            },
            "classic salsa": {
                "classic salsa": CompatibilityLevel.PERFECT,
                "salsa dura": CompatibilityLevel.EXCELLENT,
                "salsa romantica": CompatibilityLevel.EXCELLENT,
                "afro-cuban jazz": CompatibilityLevel.GOOD,
                "son cubano": CompatibilityLevel.GOOD
            },
            # Other Latin genres
            "bachata": {
                "bachata": CompatibilityLevel.PERFECT,
                "salsa romantica": CompatibilityLevel.FAIR,
                "latin ballad": CompatibilityLevel.GOOD,
                "reggaeton": CompatibilityLevel.FAIR
            },
            "merengue": {
                "merengue": CompatibilityLevel.PERFECT,
                "tropical salsa": CompatibilityLevel.GOOD,
                "cumbia": CompatibilityLevel.GOOD,
                "reggaeton": CompatibilityLevel.FAIR
            },
            # Jazz variations
            "afro-cuban jazz": {
                "afro-cuban jazz": CompatibilityLevel.PERFECT,
                "classic salsa": CompatibilityLevel.GOOD,
                "salsa dura": CompatibilityLevel.GOOD,
                "latin jazz": CompatibilityLevel.EXCELLENT,
                "smooth jazz": CompatibilityLevel.FAIR
            }
        }
    
    def _init_mood_matrix(self):
        """Initialize mood compatibility matrix"""
        self.mood_compatibility = {
            "energetic": {
                "energetic": CompatibilityLevel.PERFECT,
                "uplifting": CompatibilityLevel.EXCELLENT,
                "happy": CompatibilityLevel.EXCELLENT,
                "passionate": CompatibilityLevel.GOOD,
                "festive": CompatibilityLevel.EXCELLENT,
                "romantic": CompatibilityLevel.FAIR,
                "melancholic": CompatibilityLevel.POOR,
                "chill": CompatibilityLevel.POOR
            },
            "passionate": {
                "passionate": CompatibilityLevel.PERFECT,
                "romantic": CompatibilityLevel.EXCELLENT,
                "energetic": CompatibilityLevel.GOOD,
                "sensual": CompatibilityLevel.EXCELLENT,
                "emotional": CompatibilityLevel.GOOD,
                "uplifting": CompatibilityLevel.FAIR,
                "chill": CompatibilityLevel.FAIR
            },
            "romantic": {
                "romantic": CompatibilityLevel.PERFECT,
                "passionate": CompatibilityLevel.EXCELLENT,
                "sensual": CompatibilityLevel.EXCELLENT,
                "emotional": CompatibilityLevel.GOOD,
                "nostalgic": CompatibilityLevel.GOOD,
                "energetic": CompatibilityLevel.FAIR,
                "uplifting": CompatibilityLevel.FAIR
            },
            "uplifting": {
                "uplifting": CompatibilityLevel.PERFECT,
                "happy": CompatibilityLevel.EXCELLENT,
                "energetic": CompatibilityLevel.EXCELLENT,
                "festive": CompatibilityLevel.EXCELLENT,
                "positive": CompatibilityLevel.EXCELLENT,
                "passionate": CompatibilityLevel.FAIR,
                "melancholic": CompatibilityLevel.POOR
            },
            "chill": {
                "chill": CompatibilityLevel.PERFECT,
                "relaxed": CompatibilityLevel.EXCELLENT,
                "smooth": CompatibilityLevel.EXCELLENT,
                "romantic": CompatibilityLevel.FAIR,
                "nostalgic": CompatibilityLevel.GOOD,
                "energetic": CompatibilityLevel.POOR
            }
        }
    
    def _init_era_matrix(self):
        """Initialize era compatibility matrix"""
        self.era_compatibility = {
            "70s": {
                "70s": CompatibilityLevel.PERFECT,
                "80s": CompatibilityLevel.EXCELLENT,
                "classic": CompatibilityLevel.EXCELLENT,
                "vintage": CompatibilityLevel.GOOD,
                "90s": CompatibilityLevel.GOOD,
                "2000s": CompatibilityLevel.FAIR,
                "2010s": CompatibilityLevel.POOR,
                "2020s": CompatibilityLevel.POOR
            },
            "80s": {
                "80s": CompatibilityLevel.PERFECT,
                "70s": CompatibilityLevel.EXCELLENT,
                "90s": CompatibilityLevel.EXCELLENT,
                "classic": CompatibilityLevel.EXCELLENT,
                "2000s": CompatibilityLevel.GOOD,
                "2010s": CompatibilityLevel.FAIR,
                "2020s": CompatibilityLevel.FAIR
            },
            "90s": {
                "90s": CompatibilityLevel.PERFECT,
                "80s": CompatibilityLevel.EXCELLENT,
                "2000s": CompatibilityLevel.EXCELLENT,
                "classic": CompatibilityLevel.GOOD,
                "2010s": CompatibilityLevel.GOOD,
                "70s": CompatibilityLevel.GOOD,
                "2020s": CompatibilityLevel.FAIR
            },
            "2000s": {
                "2000s": CompatibilityLevel.PERFECT,
                "90s": CompatibilityLevel.EXCELLENT,
                "2010s": CompatibilityLevel.EXCELLENT,
                "80s": CompatibilityLevel.GOOD,
                "2020s": CompatibilityLevel.GOOD,
                "classic": CompatibilityLevel.FAIR
            },
            "2010s": {
                "2010s": CompatibilityLevel.PERFECT,
                "2000s": CompatibilityLevel.EXCELLENT,
                "2020s": CompatibilityLevel.EXCELLENT,
                "90s": CompatibilityLevel.GOOD,
                "modern": CompatibilityLevel.GOOD,
                "80s": CompatibilityLevel.FAIR
            },
            "2020s": {
                "2020s": CompatibilityLevel.PERFECT,
                "2010s": CompatibilityLevel.EXCELLENT,
                "modern": CompatibilityLevel.EXCELLENT,
                "2000s": CompatibilityLevel.GOOD,
                "contemporary": CompatibilityLevel.EXCELLENT,
                "90s": CompatibilityLevel.FAIR
            },
            "classic": {
                "classic": CompatibilityLevel.PERFECT,
                "70s": CompatibilityLevel.EXCELLENT,
                "80s": CompatibilityLevel.EXCELLENT,
                "vintage": CompatibilityLevel.EXCELLENT,
                "90s": CompatibilityLevel.GOOD,
                "traditional": CompatibilityLevel.EXCELLENT
            }
        }
    
    def _init_language_matrix(self):
        """Initialize language compatibility matrix"""
        self.language_compatibility = {
            "spanish": {
                "spanish": CompatibilityLevel.PERFECT,
                "instrumental": CompatibilityLevel.GOOD,
                "portuguese": CompatibilityLevel.FAIR,
                "english": CompatibilityLevel.FAIR
            },
            "english": {
                "english": CompatibilityLevel.PERFECT,
                "instrumental": CompatibilityLevel.GOOD,
                "spanish": CompatibilityLevel.FAIR
            },
            "instrumental": {
                "instrumental": CompatibilityLevel.PERFECT,
                "spanish": CompatibilityLevel.GOOD,
                "english": CompatibilityLevel.GOOD,
                "portuguese": CompatibilityLevel.GOOD
            },
            "portuguese": {
                "portuguese": CompatibilityLevel.PERFECT,
                "spanish": CompatibilityLevel.FAIR,
                "instrumental": CompatibilityLevel.GOOD
            }
        }
    
    def _init_activity_matrix(self):
        """Initialize activity compatibility matrix"""
        self.activity_compatibility = {
            "party": {
                "party": CompatibilityLevel.PERFECT,
                "dance": CompatibilityLevel.EXCELLENT,
                "celebration": CompatibilityLevel.EXCELLENT,
                "social dancing": CompatibilityLevel.EXCELLENT,
                "club": CompatibilityLevel.GOOD,
                "workout": CompatibilityLevel.FAIR,
                "chill": CompatibilityLevel.POOR
            },
            "workout": {
                "workout": CompatibilityLevel.PERFECT,
                "fitness": CompatibilityLevel.EXCELLENT,
                "energy": CompatibilityLevel.EXCELLENT,
                "party": CompatibilityLevel.FAIR,
                "dance": CompatibilityLevel.FAIR,
                "chill": CompatibilityLevel.POOR
            },
            "chill": {
                "chill": CompatibilityLevel.PERFECT,
                "relax": CompatibilityLevel.EXCELLENT,
                "background": CompatibilityLevel.EXCELLENT,
                "lounge": CompatibilityLevel.EXCELLENT,
                "focus": CompatibilityLevel.GOOD,
                "party": CompatibilityLevel.POOR,
                "workout": CompatibilityLevel.POOR
            },
            "social dancing": {
                "social dancing": CompatibilityLevel.PERFECT,
                "dance": CompatibilityLevel.EXCELLENT,
                "party": CompatibilityLevel.EXCELLENT,
                "celebration": CompatibilityLevel.GOOD,
                "club": CompatibilityLevel.GOOD
            }
        }
    
    def _init_time_of_day_matrix(self):
        """Initialize time of day compatibility matrix"""
        self.time_of_day_compatibility = {
            "morning": {
                "morning": CompatibilityLevel.PERFECT,
                "afternoon": CompatibilityLevel.GOOD,
                "evening": CompatibilityLevel.FAIR,
                "night": CompatibilityLevel.POOR
            },
            "afternoon": {
                "afternoon": CompatibilityLevel.PERFECT,
                "morning": CompatibilityLevel.GOOD,
                "evening": CompatibilityLevel.EXCELLENT,
                "night": CompatibilityLevel.FAIR
            },
            "evening": {
                "evening": CompatibilityLevel.PERFECT,
                "afternoon": CompatibilityLevel.EXCELLENT,
                "night": CompatibilityLevel.EXCELLENT,
                "morning": CompatibilityLevel.FAIR
            },
            "night": {
                "night": CompatibilityLevel.PERFECT,
                "evening": CompatibilityLevel.EXCELLENT,
                "late night": CompatibilityLevel.EXCELLENT,
                "afternoon": CompatibilityLevel.FAIR,
                "morning": CompatibilityLevel.POOR
            }
        }
    
    def _init_season_matrix(self):
        """Initialize season compatibility matrix"""
        self.season_compatibility = {
            "summer": {
                "summer": CompatibilityLevel.PERFECT,
                "spring": CompatibilityLevel.GOOD,
                "fall": CompatibilityLevel.FAIR,
                "winter": CompatibilityLevel.POOR
            },
            "winter": {
                "winter": CompatibilityLevel.PERFECT,
                "fall": CompatibilityLevel.GOOD,
                "spring": CompatibilityLevel.FAIR,
                "summer": CompatibilityLevel.POOR
            },
            "spring": {
                "spring": CompatibilityLevel.PERFECT,
                "summer": CompatibilityLevel.GOOD,
                "fall": CompatibilityLevel.GOOD,
                "winter": CompatibilityLevel.FAIR
            },
            "fall": {
                "fall": CompatibilityLevel.PERFECT,
                "winter": CompatibilityLevel.GOOD,
                "spring": CompatibilityLevel.GOOD,
                "summer": CompatibilityLevel.FAIR
            }
        }
    
    def extract_style_profile(self, track: Track, enhanced_metadata: Optional[Dict] = None) -> StyleProfile:
        """
        Extract style profile from track and enhanced metadata
        
        Args:
            track: Track object
            enhanced_metadata: LLM enhanced metadata dictionary
            
        Returns:
            StyleProfile object with all available style information
        """
        profile = StyleProfile()
        
        if enhanced_metadata:
            profile.subgenre = self._normalize_string(enhanced_metadata.get('subgenre'))
            profile.mood = self._normalize_string(enhanced_metadata.get('mood'))
            profile.era = self._normalize_string(enhanced_metadata.get('era'))
            profile.language = self._normalize_string(enhanced_metadata.get('language'))
            profile.time_of_day = self._normalize_string(enhanced_metadata.get('time_of_day'))
            profile.activity = self._normalize_string(enhanced_metadata.get('activity'))
            profile.season = self._normalize_string(enhanced_metadata.get('season'))
            
            # Convert percentages to floats
            profile.danceability = self._normalize_percentage(enhanced_metadata.get('danceability'))
            profile.crowd_appeal = self._normalize_percentage(enhanced_metadata.get('crowd_appeal'))
            profile.mix_friendly = self._normalize_percentage(enhanced_metadata.get('mix_friendly'))
        
        return profile
    
    def _normalize_string(self, value) -> Optional[str]:
        """Normalize string values to lowercase for consistent matching"""
        if value and isinstance(value, str) and value != "-":
            return value.lower().strip()
        return None
    
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
    
    def calculate_stylistic_compatibility(self, profile1: StyleProfile, profile2: StyleProfile) -> float:
        """
        Calculate stylistic compatibility between two style profiles
        
        Args:
            profile1: Style profile of first track
            profile2: Style profile of second track
            
        Returns:
            Compatibility score (0-1)
        """
        total_score = 0.0
        total_weight = 0.0
        
        # Subgenre compatibility
        if profile1.subgenre and profile2.subgenre:
            score = self._get_compatibility_score(
                profile1.subgenre, profile2.subgenre, self.subgenre_compatibility
            )
            total_score += score * self.style_weights['subgenre']
            total_weight += self.style_weights['subgenre']
        
        # Mood compatibility
        if profile1.mood and profile2.mood:
            score = self._get_compatibility_score(
                profile1.mood, profile2.mood, self.mood_compatibility
            )
            total_score += score * self.style_weights['mood']
            total_weight += self.style_weights['mood']
        
        # Era compatibility
        if profile1.era and profile2.era:
            score = self._get_compatibility_score(
                profile1.era, profile2.era, self.era_compatibility
            )
            total_score += score * self.style_weights['era']
            total_weight += self.style_weights['era']
        
        # Language compatibility
        if profile1.language and profile2.language:
            score = self._get_compatibility_score(
                profile1.language, profile2.language, self.language_compatibility
            )
            total_score += score * self.style_weights['language']
            total_weight += self.style_weights['language']
        
        # Activity compatibility
        if profile1.activity and profile2.activity:
            score = self._get_compatibility_score(
                profile1.activity, profile2.activity, self.activity_compatibility
            )
            total_score += score * self.style_weights['activity']
            total_weight += self.style_weights['activity']
        
        # Time of day compatibility
        if profile1.time_of_day and profile2.time_of_day:
            score = self._get_compatibility_score(
                profile1.time_of_day, profile2.time_of_day, self.time_of_day_compatibility
            )
            total_score += score * self.style_weights['time_of_day']
            total_weight += self.style_weights['time_of_day']
        
        # Season compatibility
        if profile1.season and profile2.season:
            score = self._get_compatibility_score(
                profile1.season, profile2.season, self.season_compatibility
            )
            total_score += score * self.style_weights['season']
            total_weight += self.style_weights['season']
        
        # Danceability compatibility
        if profile1.danceability is not None and profile2.danceability is not None:
            dance_diff = abs(profile1.danceability - profile2.danceability)
            dance_score = max(0, 1.0 - dance_diff)
            total_score += dance_score * self.style_weights['danceability']
            total_weight += self.style_weights['danceability']
        
        # Return weighted average or neutral score if no data
        return total_score / total_weight if total_weight > 0 else 0.5
    
    def _get_compatibility_score(self, value1: str, value2: str, matrix: Dict) -> float:
        """Get compatibility score from matrix"""
        if value1 in matrix and value2 in matrix[value1]:
            return matrix[value1][value2].value
        elif value2 in matrix and value1 in matrix[value2]:
            return matrix[value2][value1].value
        else:
            # Default score for unknown combinations
            return CompatibilityLevel.FAIR.value
    
    def get_style_distance(self, profile1: StyleProfile, profile2: StyleProfile) -> Dict[str, float]:
        """
        Get detailed style distance breakdown
        
        Returns:
            Dictionary with individual compatibility scores for each style dimension
        """
        distances = {}
        
        if profile1.subgenre and profile2.subgenre:
            distances['subgenre'] = self._get_compatibility_score(
                profile1.subgenre, profile2.subgenre, self.subgenre_compatibility
            )
        
        if profile1.mood and profile2.mood:
            distances['mood'] = self._get_compatibility_score(
                profile1.mood, profile2.mood, self.mood_compatibility
            )
        
        if profile1.era and profile2.era:
            distances['era'] = self._get_compatibility_score(
                profile1.era, profile2.era, self.era_compatibility
            )
        
        if profile1.language and profile2.language:
            distances['language'] = self._get_compatibility_score(
                profile1.language, profile2.language, self.language_compatibility
            )
        
        if profile1.activity and profile2.activity:
            distances['activity'] = self._get_compatibility_score(
                profile1.activity, profile2.activity, self.activity_compatibility
            )
        
        if profile1.time_of_day and profile2.time_of_day:
            distances['time_of_day'] = self._get_compatibility_score(
                profile1.time_of_day, profile2.time_of_day, self.time_of_day_compatibility
            )
        
        if profile1.danceability is not None and profile2.danceability is not None:
            distances['danceability'] = max(0, 1.0 - abs(profile1.danceability - profile2.danceability))
        
        return distances
    
    def suggest_bridge_tracks(self, profile1: StyleProfile, profile2: StyleProfile, 
                             available_tracks: List[Tuple[Track, Dict]]) -> List[Tuple[Track, float]]:
        """
        Suggest bridge tracks that can help transition between incompatible styles
        
        Args:
            profile1: Source style profile
            profile2: Target style profile  
            available_tracks: List of (track, enhanced_metadata) tuples
            
        Returns:
            List of (track, bridge_score) tuples sorted by bridge effectiveness
        """
        bridges = []
        
        for track, metadata in available_tracks:
            bridge_profile = self.extract_style_profile(track, metadata)
            
            # Calculate how well this track bridges the gap
            to_bridge = self.calculate_stylistic_compatibility(profile1, bridge_profile)
            from_bridge = self.calculate_stylistic_compatibility(bridge_profile, profile2)
            
            # Bridge score is the harmonic mean of both compatibilities
            if to_bridge > 0 and from_bridge > 0:
                bridge_score = 2 * (to_bridge * from_bridge) / (to_bridge + from_bridge)
                
                # Bonus for tracks that are good at both ends
                if to_bridge > 0.7 and from_bridge > 0.7:
                    bridge_score *= 1.2
                
                bridges.append((track, min(bridge_score, 1.0)))
        
        # Sort by bridge effectiveness
        bridges.sort(key=lambda x: x[1], reverse=True)
        return bridges[:10]  # Return top 10 bridge candidates