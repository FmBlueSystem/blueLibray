"""
Contextual Playlist Generator
Advanced playlist generation using contextual curves and LLM metadata
"""

import random
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from ..core.harmonic_engine import Track, HarmonicMixingEngine
# Contextual curves module archived - using basic implementation
# from .contextual_curves import ContextualMixingEngine, ContextualCurve

# Stylistic compatibility module archived - using basic fallback
# try:
#     from .stylistic_compatibility import StylisticCompatibilityMatrix
#     STYLISTIC_AVAILABLE = True
# except ImportError:
STYLISTIC_AVAILABLE = False


@dataclass
class PlaylistGenerationRequest:
    """Request specification for playlist generation"""
    tracks: List[Track]
    enhanced_metadata: Dict[str, Dict]  # track_id -> metadata
    target_length: int = 10
    time_of_day: Optional[str] = None
    activity: Optional[str] = None
    mood_preference: Optional[str] = None
    season: Optional[str] = None
    duration_minutes: Optional[int] = None
    start_track: Optional[Track] = None
    energy_preference: Optional[str] = None  # "warm_up", "peak_time", "cool_down"
    allow_repeats: bool = False
    min_compatibility: float = 0.3


@dataclass
class PlaylistGenerationResult:
    """Result of playlist generation"""
    playlist: List[Track]
    contextual_curve: ContextualCurve
    energy_progression: List[float]
    track_scores: List[float]
    generation_info: Dict
    total_score: float


class ContextualPlaylistGenerator:
    """
    Advanced playlist generator using contextual curves and multi-factor analysis
    """
    
    def __init__(self, harmonic_engine: HarmonicMixingEngine):
        self.harmonic_engine = harmonic_engine
        self.contextual_engine = ContextualMixingEngine()
        
        # Initialize stylistic matrix if available
        if STYLISTIC_AVAILABLE:
            self.stylistic_matrix = StylisticCompatibilityMatrix()
        else:
            self.stylistic_matrix = None
        
        # Weights for playlist generation factors
        self.generation_weights = {
            'harmonic_compatibility': 0.25,    # Traditional harmonic matching
            'stylistic_compatibility': 0.25,   # Style matching
            'contextual_fit': 0.25,            # Context appropriateness  
            'energy_progression': 0.15,        # Energy flow
            'variety': 0.1                     # Diversity to avoid monotony
        }
    
    def generate_contextual_playlist(self, request: PlaylistGenerationRequest) -> PlaylistGenerationResult:
        """
        Generate a contextual playlist based on the request
        
        Args:
            request: Playlist generation specifications
            
        Returns:
            PlaylistGenerationResult with generated playlist and metadata
        """
        # Select appropriate contextual curve
        curve = self.contextual_engine.select_contextual_curve(
            time_of_day=request.time_of_day,
            activity=request.activity,
            mood_preference=request.mood_preference,
            season=request.season,
            duration_minutes=request.duration_minutes
        )
        
        # Generate energy progression
        energy_progression = self.contextual_engine.generate_energy_progression(
            curve, request.target_length
        )
        
        # Generate playlist using advanced algorithm
        playlist, track_scores, generation_info = self._generate_playlist_with_context(
            request, curve, energy_progression
        )
        
        # Calculate total score
        total_score = sum(track_scores) / len(track_scores) if track_scores else 0.0
        
        return PlaylistGenerationResult(
            playlist=playlist,
            contextual_curve=curve,
            energy_progression=energy_progression,
            track_scores=track_scores,
            generation_info=generation_info,
            total_score=total_score
        )
    
    def _generate_playlist_with_context(
        self, 
        request: PlaylistGenerationRequest,
        curve: ContextualCurve,
        energy_progression: List[float]
    ) -> Tuple[List[Track], List[float], Dict]:
        """
        Generate playlist using contextual and compatibility analysis
        """
        playlist = []
        track_scores = []
        used_tracks = set()
        available_tracks = list(request.tracks)
        generation_info = {
            'algorithm': 'contextual_multi_factor',
            'curve_used': curve.name,
            'iterations': 0,
            'fallback_selections': 0,
            'perfect_matches': 0,
            'context_mismatches': 0
        }
        
        # Start with specified track or select best starting track
        if request.start_track and request.start_track in available_tracks:
            current_track = request.start_track
            playlist.append(current_track)
            used_tracks.add(current_track.id)
            available_tracks.remove(current_track)
            
            # Score starting track
            start_score = self.contextual_engine.calculate_track_context_score(
                current_track, request.enhanced_metadata.get(current_track.id, {}),
                curve, energy_progression[0], 0.0
            )
            track_scores.append(start_score)
        else:
            # Select best starting track for context
            current_track = self._select_best_starting_track(
                available_tracks, request.enhanced_metadata, curve, energy_progression[0]
            )
            if current_track:
                playlist.append(current_track)
                used_tracks.add(current_track.id)
                available_tracks.remove(current_track)
                
                start_score = self.contextual_engine.calculate_track_context_score(
                    current_track, request.enhanced_metadata.get(current_track.id, {}),
                    curve, energy_progression[0], 0.0
                )
                track_scores.append(start_score)
            else:
                return [], [], generation_info
        
        # Generate remaining tracks
        for position in range(1, min(request.target_length, len(request.tracks))):
            generation_info['iterations'] += 1
            
            if not available_tracks:
                break
            
            # Calculate target energy for this position
            target_energy = energy_progression[position] if position < len(energy_progression) else 0.5
            position_ratio = position / (request.target_length - 1) if request.target_length > 1 else 0.5
            
            # Find best next track
            next_track, score = self._select_next_track(
                current_track,
                available_tracks,
                request.enhanced_metadata,
                curve,
                target_energy,
                position_ratio,
                generation_info
            )
            
            if next_track and score >= request.min_compatibility:
                playlist.append(next_track)
                track_scores.append(score)
                used_tracks.add(next_track.id)
                available_tracks.remove(next_track)
                current_track = next_track
                
                if score > 0.8:
                    generation_info['perfect_matches'] += 1
            else:
                # Fallback: select best available track even if below threshold
                if available_tracks:
                    fallback_track, fallback_score = self._select_fallback_track(
                        available_tracks, request.enhanced_metadata, curve, target_energy, position_ratio
                    )
                    if fallback_track:
                        playlist.append(fallback_track)
                        track_scores.append(fallback_score)
                        used_tracks.add(fallback_track.id)
                        available_tracks.remove(fallback_track)
                        current_track = fallback_track
                        generation_info['fallback_selections'] += 1
                
                if not playlist or len(playlist) <= position:
                    break
        
        return playlist, track_scores, generation_info
    
    def _select_best_starting_track(
        self,
        available_tracks: List[Track],
        enhanced_metadata: Dict[str, Dict],
        curve: ContextualCurve,
        target_energy: float
    ) -> Optional[Track]:
        """Select the best track to start the playlist"""
        
        best_track = None
        best_score = 0.0
        
        for track in available_tracks:
            metadata = enhanced_metadata.get(track.id, {})
            
            # Calculate contextual fit
            context_score = self.contextual_engine.calculate_track_context_score(
                track, metadata, curve, target_energy, 0.0
            )
            
            # Prefer tracks with good intro characteristics
            intro_bonus = 0.0
            if curve.context_type.value == "time" and curve.context_value in ["morning", "evening"]:
                # Prefer tracks good for opening
                mix_friendly = self._normalize_percentage(metadata.get('mix_friendly'))
                if mix_friendly and mix_friendly > 0.7:
                    intro_bonus = 0.1
            
            total_score = context_score + intro_bonus
            
            if total_score > best_score:
                best_score = total_score
                best_track = track
        
        return best_track
    
    def _select_next_track(
        self,
        current_track: Track,
        available_tracks: List[Track],
        enhanced_metadata: Dict[str, Dict],
        curve: ContextualCurve,
        target_energy: float,
        position_ratio: float,
        generation_info: Dict
    ) -> Tuple[Optional[Track], float]:
        """Select the best next track considering all factors"""
        
        candidates = []
        current_metadata = enhanced_metadata.get(current_track.id, {})
        
        for track in available_tracks:
            track_metadata = enhanced_metadata.get(track.id, {})
            
            # Calculate multi-factor score
            total_score = self._calculate_comprehensive_score(
                current_track, track, current_metadata, track_metadata,
                curve, target_energy, position_ratio
            )
            
            candidates.append((track, total_score))
        
        # Sort by score
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        if candidates:
            best_track, best_score = candidates[0]
            
            # Check if this is a context mismatch
            context_score = self.contextual_engine.calculate_track_context_score(
                best_track, enhanced_metadata.get(best_track.id, {}),
                curve, target_energy, position_ratio
            )
            
            if context_score < 0.4:
                generation_info['context_mismatches'] += 1
            
            return best_track, best_score
        
        return None, 0.0
    
    def _calculate_comprehensive_score(
        self,
        current_track: Track,
        candidate_track: Track,
        current_metadata: Dict,
        candidate_metadata: Dict,
        curve: ContextualCurve,
        target_energy: float,
        position_ratio: float
    ) -> float:
        """Calculate comprehensive score considering all factors"""
        
        total_score = 0.0
        
        # 1. Harmonic compatibility
        harmonic_score = self.harmonic_engine.calculate_compatibility(current_track, candidate_track)
        total_score += self.generation_weights['harmonic_compatibility'] * harmonic_score
        
        # 2. Stylistic compatibility
        if self.stylistic_matrix:
            stylistic_score = self._calculate_stylistic_score(
                current_track, candidate_track, current_metadata, candidate_metadata
            )
            total_score += self.generation_weights['stylistic_compatibility'] * stylistic_score
        
        # 3. Contextual fit
        contextual_score = self.contextual_engine.calculate_track_context_score(
            candidate_track, candidate_metadata, curve, target_energy, position_ratio
        )
        total_score += self.generation_weights['contextual_fit'] * contextual_score
        
        # 4. Energy progression
        energy_score = self._calculate_energy_progression_score(
            current_metadata, candidate_metadata, target_energy
        )
        total_score += self.generation_weights['energy_progression'] * energy_score
        
        # 5. Variety bonus (avoid too much similarity)
        variety_score = self._calculate_variety_score(
            current_metadata, candidate_metadata
        )
        total_score += self.generation_weights['variety'] * variety_score
        
        return total_score
    
    def _calculate_stylistic_score(
        self, 
        current_track: Track,
        candidate_track: Track,
        current_metadata: Dict,
        candidate_metadata: Dict
    ) -> float:
        """Calculate stylistic compatibility score"""
        if not self.stylistic_matrix:
            return 0.5
        
        current_profile = self.stylistic_matrix.extract_style_profile(current_track, current_metadata)
        candidate_profile = self.stylistic_matrix.extract_style_profile(candidate_track, candidate_metadata)
        
        return self.stylistic_matrix.calculate_stylistic_compatibility(current_profile, candidate_profile)
    
    def _calculate_energy_progression_score(
        self,
        current_metadata: Dict,
        candidate_metadata: Dict,
        target_energy: float
    ) -> float:
        """Calculate how well the energy progression flows"""
        
        current_energy = self._normalize_percentage(current_metadata.get('danceability', 0.5))
        candidate_energy = self._normalize_percentage(candidate_metadata.get('danceability', 0.5))
        
        if current_energy is None or candidate_energy is None:
            return 0.5
        
        # Check if candidate energy is close to target
        target_match = 1.0 - abs(candidate_energy - target_energy)
        
        # Check if energy transition is smooth
        energy_transition = 1.0 - min(abs(candidate_energy - current_energy), 0.3) / 0.3
        
        return (target_match * 0.7 + energy_transition * 0.3)
    
    def _calculate_variety_score(self, current_metadata: Dict, candidate_metadata: Dict) -> float:
        """Calculate variety score to avoid monotony"""
        
        variety_score = 1.0
        
        # Penalize exact same subgenre
        current_subgenre = current_metadata.get('subgenre', '') or ''
        candidate_subgenre = candidate_metadata.get('subgenre', '') or ''
        if (current_subgenre.lower() == candidate_subgenre.lower() and current_subgenre):
            variety_score -= 0.2
        
        # Penalize exact same mood
        current_mood = current_metadata.get('mood', '') or ''
        candidate_mood = candidate_metadata.get('mood', '') or ''
        if (current_mood.lower() == candidate_mood.lower() and current_mood):
            variety_score -= 0.1
        
        # Penalize exact same era
        current_era = current_metadata.get('era', '') or ''
        candidate_era = candidate_metadata.get('era', '') or ''
        if (current_era.lower() == candidate_era.lower() and current_era):
            variety_score -= 0.1
        
        return max(0.0, variety_score)
    
    def _select_fallback_track(
        self,
        available_tracks: List[Track],
        enhanced_metadata: Dict[str, Dict],
        curve: ContextualCurve,
        target_energy: float,
        position_ratio: float
    ) -> Tuple[Optional[Track], float]:
        """Select fallback track when no good matches are found"""
        
        # Relax requirements and find best available
        best_track = None
        best_score = 0.0
        
        for track in available_tracks:
            metadata = enhanced_metadata.get(track.id, {})
            
            # Simple contextual score
            score = self.contextual_engine.calculate_track_context_score(
                track, metadata, curve, target_energy, position_ratio
            )
            
            if score > best_score:
                best_score = score
                best_track = track
        
        return best_track, best_score
    
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
    
    def generate_multiple_playlists(
        self, 
        request: PlaylistGenerationRequest,
        num_playlists: int = 3
    ) -> List[PlaylistGenerationResult]:
        """
        Generate multiple playlist variations for comparison
        
        Args:
            request: Base playlist request
            num_playlists: Number of playlists to generate
            
        Returns:
            List of playlist results sorted by total score
        """
        results = []
        
        # Generate with different starting tracks and slight variations
        for i in range(num_playlists):
            # Create variation of request
            varied_request = PlaylistGenerationRequest(
                tracks=request.tracks.copy(),
                enhanced_metadata=request.enhanced_metadata,
                target_length=request.target_length,
                time_of_day=request.time_of_day,
                activity=request.activity,
                mood_preference=request.mood_preference,
                season=request.season,
                duration_minutes=request.duration_minutes,
                start_track=None,  # Let algorithm choose
                energy_preference=request.energy_preference,
                allow_repeats=request.allow_repeats,
                min_compatibility=max(0.2, request.min_compatibility - 0.1 * i)  # Relax threshold
            )
            
            # Add some randomness to track order for variety
            if i > 0:
                random.shuffle(varied_request.tracks)
            
            result = self.generate_contextual_playlist(varied_request)
            if result.playlist:
                results.append(result)
        
        # Sort by total score
        results.sort(key=lambda x: x.total_score, reverse=True)
        
        return results
    
    def explain_playlist_generation(self, result: PlaylistGenerationResult) -> Dict:
        """
        Generate explanation of how the playlist was created
        
        Args:
            result: Playlist generation result
            
        Returns:
            Dictionary with detailed explanation
        """
        explanation = {
            'curve_info': {
                'name': result.contextual_curve.name,
                'type': result.contextual_curve.context_type.value,
                'shape': result.contextual_curve.target_curve.value,
                'energy_range': result.contextual_curve.energy_range,
                'duration': result.contextual_curve.duration_minutes
            },
            'generation_stats': result.generation_info,
            'energy_flow': {
                'progression': result.energy_progression,
                'track_scores': result.track_scores,
                'average_score': result.total_score
            },
            'recommendations': []
        }
        
        # Add recommendations based on generation stats
        if result.generation_info.get('context_mismatches', 0) > len(result.playlist) * 0.3:
            explanation['recommendations'].append(
                "Consider adjusting context parameters - some tracks don't fit the selected context well"
            )
        
        if result.generation_info.get('fallback_selections', 0) > len(result.playlist) * 0.2:
            explanation['recommendations'].append(
                "Some tracks were selected as fallbacks - consider expanding your music library for this context"
            )
        
        if result.total_score < 0.6:
            explanation['recommendations'].append(
                "Overall compatibility could be improved - consider using different starting track or context"
            )
        
        return explanation