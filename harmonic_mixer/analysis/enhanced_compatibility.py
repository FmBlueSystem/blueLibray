"""
Enhanced Compatibility Scoring with Structural Analysis
Integrates structural analysis with harmonic mixing for precise transitions
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from ..core.harmonic_engine import Track, HarmonicMixingEngine

# Import structural components with fallback
try:
    from .structural_analyzer import StructuralAnalysis, TransitionPoint, StructuralElement
    STRUCTURAL_ANALYSIS_AVAILABLE = True
except ImportError:
    # Define minimal classes for type hints when not available
    class StructuralElement:
        pass
    class TransitionPoint:
        pass
    class StructuralAnalysis:
        pass
    STRUCTURAL_ANALYSIS_AVAILABLE = False

# Import stylistic compatibility
try:
    from .stylistic_compatibility import StylisticCompatibilityMatrix, StyleProfile
    STYLISTIC_ANALYSIS_AVAILABLE = True
except ImportError:
    STYLISTIC_ANALYSIS_AVAILABLE = False


@dataclass
class MixTransition:
    """Represents a potential transition between two tracks"""
    track_from: Track
    track_to: Track
    mix_out_point: TransitionPoint
    mix_in_point: TransitionPoint
    compatibility_score: float
    transition_quality: float
    estimated_mix_duration: float


class EnhancedCompatibilityEngine:
    """Enhanced compatibility engine with structural and stylistic analysis"""
    
    def __init__(self, base_engine: HarmonicMixingEngine):
        self.base_engine = base_engine
        self.structural_cache: Dict[str, StructuralAnalysis] = {}
        
        # Initialize stylistic compatibility matrix
        if STYLISTIC_ANALYSIS_AVAILABLE:
            self.stylistic_matrix = StylisticCompatibilityMatrix()
        else:
            self.stylistic_matrix = None
        
        # Weights for enhanced scoring (updated for stylistic analysis)
        self.enhanced_weights = {
            'harmonic': 0.25,     # Traditional harmonic compatibility  
            'stylistic': 0.25,    # Stylistic compatibility (NEW)
            'structural': 0.2,    # Structural compatibility
            'transition': 0.2,    # Transition point quality
            'temporal': 0.1       # Timing and flow
        }
    
    def calculate_enhanced_compatibility(
        self, 
        track1: Track, 
        track2: Track,
        structural1: Optional[StructuralAnalysis] = None,
        structural2: Optional[StructuralAnalysis] = None,
        enhanced_metadata1: Optional[Dict] = None,
        enhanced_metadata2: Optional[Dict] = None
    ) -> float:
        """
        Calculate enhanced compatibility with structural and stylistic analysis
        
        Args:
            track1: Source track
            track2: Target track
            structural1: Structural analysis of track1 (optional)
            structural2: Structural analysis of track2 (optional)
            enhanced_metadata1: LLM metadata for track1 (optional)
            enhanced_metadata2: LLM metadata for track2 (optional)
            
        Returns:
            Enhanced compatibility score (0-1)
        """
        # Base harmonic compatibility
        harmonic_score = self.base_engine.calculate_compatibility(track1, track2)
        
        # Initialize component scores
        stylistic_score = 0.5  # Default neutral score
        structural_score = 0.5
        transition_score = 0.5  
        temporal_score = 0.5
        
        # Calculate stylistic compatibility (NEW)
        if self.stylistic_matrix and enhanced_metadata1 and enhanced_metadata2:
            profile1 = self.stylistic_matrix.extract_style_profile(track1, enhanced_metadata1)
            profile2 = self.stylistic_matrix.extract_style_profile(track2, enhanced_metadata2)
            stylistic_score = self.stylistic_matrix.calculate_stylistic_compatibility(profile1, profile2)
        
        # Calculate structural compatibility if data available
        if structural1 and structural2:
            structural_score = self._calculate_structural_compatibility(
                track1, track2, structural1, structural2
            )
            
            transition_score = self._calculate_transition_quality(
                structural1, structural2
            )
            
            temporal_score = self._calculate_temporal_compatibility(
                track1, track2, structural1, structural2
            )
        
        # Weighted combination with all factors
        enhanced_score = (
            self.enhanced_weights['harmonic'] * harmonic_score +
            self.enhanced_weights['stylistic'] * stylistic_score +
            self.enhanced_weights['structural'] * structural_score +
            self.enhanced_weights['transition'] * transition_score +
            self.enhanced_weights['temporal'] * temporal_score
        )
        
        return min(enhanced_score, 1.0)
    
    def _calculate_structural_compatibility(
        self, 
        track1: Track, 
        track2: Track,
        structural1: StructuralAnalysis,
        structural2: StructuralAnalysis
    ) -> float:
        """Calculate compatibility based on structural elements"""
        score = 0.0
        
        # Duration compatibility
        duration_ratio = min(structural1.duration, structural2.duration) / \
                        max(structural1.duration, structural2.duration)
        duration_score = duration_ratio * 0.3
        
        # Beat grid compatibility
        beat_score = self._calculate_beat_compatibility(structural1, structural2) * 0.4
        
        # Energy curve compatibility  
        energy_score = self._calculate_energy_compatibility(structural1, structural2) * 0.3
        
        return duration_score + beat_score + energy_score
    
    def _calculate_beat_compatibility(
        self, 
        structural1: StructuralAnalysis,
        structural2: StructuralAnalysis
    ) -> float:
        """Calculate beat grid compatibility"""
        if not structural1.beat_grid or not structural2.beat_grid:
            return 0.5  # Neutral score if no beat data
        
        # Calculate average beat intervals
        def avg_beat_interval(beats):
            if len(beats) < 2:
                return 0
            intervals = np.diff(beats)
            return np.mean(intervals)
        
        interval1 = avg_beat_interval(structural1.beat_grid)
        interval2 = avg_beat_interval(structural2.beat_grid)
        
        if interval1 == 0 or interval2 == 0:
            return 0.5
        
        # Calculate BPM from intervals
        bpm1 = 60 / interval1 if interval1 > 0 else 0
        bpm2 = 60 / interval2 if interval2 > 0 else 0
        
        # Use base engine's BPM scoring logic
        return self.base_engine._calculate_bpm_score(bpm1, bpm2)
    
    def _calculate_energy_compatibility(
        self,
        structural1: StructuralAnalysis,
        structural2: StructuralAnalysis
    ) -> float:
        """Calculate energy curve compatibility"""
        if not structural1.energy_curve or not structural2.energy_curve:
            return 0.5
        
        # Get energy levels at transition points
        # For mix-out: energy in last 30 seconds of track1
        # For mix-in: energy in first 30 seconds of track2
        
        def get_energy_in_range(energy_curve, start_time, end_time):
            relevant_points = [
                energy for time, energy in energy_curve
                if start_time <= time <= end_time
            ]
            return np.mean(relevant_points) if relevant_points else 0.5
        
        # Track1 outro energy
        outro_start = max(0, structural1.duration - 30)
        track1_outro_energy = get_energy_in_range(
            structural1.energy_curve, outro_start, structural1.duration
        )
        
        # Track2 intro energy
        track2_intro_energy = get_energy_in_range(
            structural2.energy_curve, 0, min(30, structural2.duration)
        )
        
        # Energy transition should be smooth
        energy_diff = abs(track1_outro_energy - track2_intro_energy)
        return max(0, 1.0 - energy_diff)
    
    def _calculate_transition_quality(
        self,
        structural1: StructuralAnalysis,
        structural2: StructuralAnalysis
    ) -> float:
        """Calculate quality of transition points"""
        if not structural1.transition_points or not structural2.transition_points:
            return 0.5
        
        # Get best transition points
        best_out = max(structural1.transition_points, key=lambda x: x.mix_suitability)
        best_in = max(structural2.transition_points, key=lambda x: x.mix_suitability)
        
        # Combine their suitability scores
        return (best_out.mix_suitability + best_in.mix_suitability) / 2
    
    def _calculate_temporal_compatibility(
        self,
        track1: Track,
        track2: Track,
        structural1: StructuralAnalysis,
        structural2: StructuralAnalysis
    ) -> float:
        """Calculate temporal flow compatibility"""
        score = 0.0
        
        # Tempo stability
        tempo_score = self._calculate_tempo_stability(structural1, structural2) * 0.4
        
        # Structural element matching
        element_score = self._calculate_element_matching(structural1, structural2) * 0.3
        
        # Mix timing feasibility
        timing_score = self._calculate_timing_feasibility(structural1, structural2) * 0.3
        
        return tempo_score + element_score + timing_score
    
    def _calculate_tempo_stability(
        self,
        structural1: StructuralAnalysis,
        structural2: StructuralAnalysis
    ) -> float:
        """Calculate tempo stability for mixing"""
        # Fewer tempo changes = more stable = better for mixing
        changes1 = len(structural1.tempo_changes)
        changes2 = len(structural2.tempo_changes)
        
        # Normalize by track duration
        stability1 = 1.0 - min(changes1 / (structural1.duration / 60), 1.0)
        stability2 = 1.0 - min(changes2 / (structural2.duration / 60), 1.0)
        
        return (stability1 + stability2) / 2
    
    def _calculate_element_matching(
        self,
        structural1: StructuralAnalysis,
        structural2: StructuralAnalysis
    ) -> float:
        """Calculate structural element type matching"""
        if not structural1.transition_points or not structural2.transition_points:
            return 0.5
        
        # Get transition element types
        out_elements = [tp.element_type for tp in structural1.transition_points]
        in_elements = [tp.element_type for tp in structural2.transition_points]
        
        # Define compatibility matrix between structural elements
        compatibility_matrix = {
            StructuralElement.OUTRO: {
                StructuralElement.INTRO: 1.0,
                StructuralElement.VERSE: 0.8,
                StructuralElement.BREAK: 0.9
            },
            StructuralElement.BREAK: {
                StructuralElement.VERSE: 0.9,
                StructuralElement.CHORUS: 0.7,
                StructuralElement.BUILD_UP: 0.8
            },
            StructuralElement.VERSE: {
                StructuralElement.VERSE: 0.8,
                StructuralElement.CHORUS: 0.6,
                StructuralElement.INTRO: 0.7
            }
        }
        
        # Find best element compatibility
        best_compatibility = 0.0
        for out_elem in out_elements:
            for in_elem in in_elements:
                compatibility = compatibility_matrix.get(out_elem, {}).get(in_elem, 0.5)
                best_compatibility = max(best_compatibility, compatibility)
        
        return best_compatibility
    
    def _calculate_timing_feasibility(
        self,
        structural1: StructuralAnalysis,
        structural2: StructuralAnalysis
    ) -> float:
        """Calculate if timing allows for good mixing"""
        # Check if there's enough time for a proper mix
        # Typical mix duration: 8-32 seconds
        
        if not structural1.transition_points or not structural2.transition_points:
            return 0.5
        
        # Get best transition points
        best_out = max(structural1.transition_points, key=lambda x: x.mix_suitability)
        best_in = max(structural2.transition_points, key=lambda x: x.mix_suitability)
        
        # Check if mix-out point leaves enough time
        time_remaining = structural1.duration - best_out.time_seconds
        
        # Check if mix-in point allows enough intro
        intro_time = best_in.time_seconds
        
        # Optimal: 15-45 seconds for mix-out, 10+ seconds for mix-in
        out_score = 1.0 if 15 <= time_remaining <= 45 else max(0, 1.0 - abs(time_remaining - 30) / 30)
        in_score = 1.0 if intro_time >= 10 else intro_time / 10
        
        return (out_score + in_score) / 2
    
    def find_optimal_transition(
        self,
        track1: Track,
        track2: Track,
        structural1: StructuralAnalysis,
        structural2: StructuralAnalysis
    ) -> Optional[MixTransition]:
        """Find the optimal transition between two tracks"""
        if not structural1.transition_points or not structural2.transition_points:
            return None
        
        best_transition = None
        best_score = 0.0
        
        # Try different combinations of transition points
        for out_point in structural1.transition_points[:5]:  # Top 5 out points
            for in_point in structural2.transition_points[:5]:  # Top 5 in points
                
                # Calculate transition quality for this combination
                transition_quality = self._evaluate_transition_pair(
                    out_point, in_point, structural1, structural2
                )
                
                if transition_quality > best_score:
                    best_score = transition_quality
                    
                    # Estimate mix duration
                    mix_duration = self._estimate_mix_duration(out_point, in_point)
                    
                    best_transition = MixTransition(
                        track_from=track1,
                        track_to=track2,
                        mix_out_point=out_point,
                        mix_in_point=in_point,
                        compatibility_score=self.calculate_enhanced_compatibility(
                            track1, track2, structural1, structural2
                        ),
                        transition_quality=transition_quality,
                        estimated_mix_duration=mix_duration
                    )
        
        return best_transition
    
    def _evaluate_transition_pair(
        self,
        out_point: TransitionPoint,
        in_point: TransitionPoint,
        structural1: StructuralAnalysis,
        structural2: StructuralAnalysis
    ) -> float:
        """Evaluate quality of a specific transition point pair"""
        # Combine individual point qualities
        point_quality = (out_point.mix_suitability + in_point.mix_suitability) / 2
        
        # Timing feasibility
        time_remaining = structural1.duration - out_point.time_seconds
        timing_score = 1.0 if 15 <= time_remaining <= 45 else max(0, 1.0 - abs(time_remaining - 30) / 30)
        
        # Energy matching
        energy_diff = abs(out_point.energy_level - in_point.energy_level)
        energy_score = max(0, 1.0 - energy_diff)
        
        # Beat strength compatibility
        beat_score = min(out_point.beat_strength, in_point.beat_strength)
        
        return (point_quality * 0.4 + timing_score * 0.3 + energy_score * 0.2 + beat_score * 0.1)
    
    def _estimate_mix_duration(self, out_point: TransitionPoint, in_point: TransitionPoint) -> float:
        """Estimate optimal mix duration between transition points"""
        # Base duration on energy levels and beat strengths
        base_duration = 16.0  # 16 seconds default
        
        # Adjust for energy compatibility
        energy_diff = abs(out_point.energy_level - in_point.energy_level)
        if energy_diff > 0.3:
            base_duration += 8.0  # Longer mix for energy transitions
        
        # Adjust for beat strength
        min_beat_strength = min(out_point.beat_strength, in_point.beat_strength)
        if min_beat_strength > 0.7:
            base_duration -= 4.0  # Shorter mix for strong beats
        elif min_beat_strength < 0.3:
            base_duration += 8.0  # Longer mix for weak beats
        
        return max(8.0, min(32.0, base_duration))  # Clamp to 8-32 seconds
    
    def calculate_stylistic_compatibility_detailed(
        self, 
        track1: Track, 
        track2: Track,
        enhanced_metadata1: Dict,
        enhanced_metadata2: Dict
    ) -> Dict[str, float]:
        """
        Calculate detailed stylistic compatibility breakdown
        
        Returns:
            Dictionary with scores for each stylistic dimension
        """
        if not self.stylistic_matrix:
            return {}
        
        profile1 = self.stylistic_matrix.extract_style_profile(track1, enhanced_metadata1)
        profile2 = self.stylistic_matrix.extract_style_profile(track2, enhanced_metadata2)
        
        return self.stylistic_matrix.get_style_distance(profile1, profile2)
    
    def find_style_bridge_tracks(
        self,
        track1: Track,
        track2: Track, 
        enhanced_metadata1: Dict,
        enhanced_metadata2: Dict,
        available_tracks: List[Tuple[Track, Dict]]
    ) -> List[Tuple[Track, float]]:
        """
        Find tracks that can bridge stylistic gaps between incompatible tracks
        
        Args:
            track1: Source track
            track2: Target track
            enhanced_metadata1: LLM metadata for track1
            enhanced_metadata2: LLM metadata for track2
            available_tracks: List of (track, metadata) tuples to consider as bridges
            
        Returns:
            List of (bridge_track, bridge_score) sorted by effectiveness
        """
        if not self.stylistic_matrix:
            return []
        
        profile1 = self.stylistic_matrix.extract_style_profile(track1, enhanced_metadata1)
        profile2 = self.stylistic_matrix.extract_style_profile(track2, enhanced_metadata2)
        
        return self.stylistic_matrix.suggest_bridge_tracks(profile1, profile2, available_tracks)
    
    def get_compatibility_explanation(
        self,
        track1: Track,
        track2: Track,
        enhanced_metadata1: Optional[Dict] = None,
        enhanced_metadata2: Optional[Dict] = None
    ) -> Dict[str, any]:
        """
        Get detailed explanation of why tracks are or aren't compatible
        
        Returns:
            Dictionary with compatibility breakdown and human-readable explanations
        """
        explanation = {
            'overall_score': 0.0,
            'harmonic': {},
            'stylistic': {},
            'recommendations': []
        }
        
        # Harmonic analysis
        harmonic_score = self.base_engine.calculate_compatibility(track1, track2)
        explanation['harmonic'] = {
            'score': harmonic_score,
            'key_match': f"{track1.key} → {track2.key}" if track1.key and track2.key else "No key data",
            'bpm_match': f"{track1.bpm} → {track2.bpm} BPM" if track1.bpm and track2.bpm else "No BPM data",
            'energy_match': f"{track1.energy} → {track2.energy}" if track1.energy and track2.energy else "No energy data"
        }
        
        # Stylistic analysis
        if self.stylistic_matrix and enhanced_metadata1 and enhanced_metadata2:
            profile1 = self.stylistic_matrix.extract_style_profile(track1, enhanced_metadata1)
            profile2 = self.stylistic_matrix.extract_style_profile(track2, enhanced_metadata2)
            
            stylistic_score = self.stylistic_matrix.calculate_stylistic_compatibility(profile1, profile2)
            style_breakdown = self.stylistic_matrix.get_style_distance(profile1, profile2)
            
            explanation['stylistic'] = {
                'score': stylistic_score,
                'subgenre_match': f"{profile1.subgenre} → {profile2.subgenre}",
                'mood_match': f"{profile1.mood} → {profile2.mood}", 
                'era_match': f"{profile1.era} → {profile2.era}",
                'language_match': f"{profile1.language} → {profile2.language}",
                'breakdown': style_breakdown
            }
            
            # Generate recommendations
            if stylistic_score < 0.5:
                explanation['recommendations'].append("Consider using a bridge track for smoother transition")
            if style_breakdown.get('mood', 0) < 0.5:
                explanation['recommendations'].append("Mood mismatch - consider gradual energy transition")
            if style_breakdown.get('era', 0) < 0.5:
                explanation['recommendations'].append("Era mismatch - may create temporal disconnect")
        
        # Calculate overall enhanced score
        explanation['overall_score'] = self.calculate_enhanced_compatibility(
            track1, track2, None, None, enhanced_metadata1, enhanced_metadata2
        )
        
        return explanation
    
    def supports_stylistic_analysis(self) -> bool:
        """Check if stylistic analysis is available"""
        return self.stylistic_matrix is not None