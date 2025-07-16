"""
Temporal and Linguistic Sequencing
Intelligent sequencing based on era progression and language flow
Creates cohesive musical narratives across time periods and cultures
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from enum import Enum
from ..core.harmonic_engine import Track


class TemporalFlow(Enum):
    """Types of temporal progression"""
    CHRONOLOGICAL = "chronological"      # 70s → 80s → 90s → 2000s
    REVERSE_CHRONO = "reverse_chrono"     # 2020s → 2010s → 2000s → 90s
    ERA_CLUSTERING = "era_clustering"     # Group by decades, then jump
    NOSTALGIC_WAVES = "nostalgic_waves"   # Mix periods in waves
    GOLDEN_AGE_FOCUS = "golden_age"      # Focus on specific era
    CROSS_GENERATIONAL = "cross_gen"     # Bridge generations


class LinguisticFlow(Enum):
    """Types of language progression"""
    MONOLINGUAL = "monolingual"          # Single language throughout
    BILINGUAL_BRIDGE = "bilingual"       # Two languages with bridges
    MULTILINGUAL_JOURNEY = "multilingual" # Multiple languages
    CULTURAL_FUSION = "cultural_fusion"   # Blend cultures gradually
    INSTRUMENTAL_BRIDGE = "instrumental"  # Use instrumental as bridges
    LANGUAGE_WAVES = "language_waves"     # Alternate between languages


@dataclass
class TemporalCluster:
    """Represents a temporal cluster of tracks"""
    era: str
    tracks: List[Track]
    start_year: int
    end_year: int
    cultural_weight: float  # How culturally significant this era is
    transition_score: float  # How well it transitions to/from other eras


@dataclass
class LinguisticCluster:
    """Represents a linguistic cluster of tracks"""
    language: str
    tracks: List[Track]
    cultural_context: str  # e.g., "Latin American", "Caribbean"
    bridge_potential: float  # How well it bridges to other languages


@dataclass
class TemporalLinguisticSequence:
    """A sequence with temporal and linguistic coherence"""
    tracks: List[Track]
    temporal_flow: TemporalFlow
    linguistic_flow: LinguisticFlow
    era_progression: List[str]
    language_progression: List[str]
    narrative_score: float
    cultural_coherence: float
    transition_quality: float


class TemporalLinguisticSequencer:
    """
    Advanced sequencer for temporal and linguistic coherence
    """
    
    def __init__(self):
        self._init_era_mappings()
        self._init_language_mappings()
        self._init_cultural_bridges()
        
        # Weights for sequencing factors
        self.sequencing_weights = {
            'temporal_coherence': 0.3,    # Era flow quality
            'linguistic_coherence': 0.25, # Language flow quality
            'cultural_bridges': 0.2,      # Cross-cultural transitions
            'narrative_flow': 0.15,       # Overall story progression
            'diversity_bonus': 0.1        # Bonus for interesting variety
        }
    
    def _init_era_mappings(self):
        """Initialize era mappings and relationships"""
        self.era_mappings = {
            # Normalize different era formats
            "70s": {"canonical": "1970s", "start": 1970, "end": 1979, "weight": 0.9},
            "1970s": {"canonical": "1970s", "start": 1970, "end": 1979, "weight": 0.9},
            "seventies": {"canonical": "1970s", "start": 1970, "end": 1979, "weight": 0.9},
            
            "80s": {"canonical": "1980s", "start": 1980, "end": 1989, "weight": 1.0},
            "1980s": {"canonical": "1980s", "start": 1980, "end": 1989, "weight": 1.0},
            "eighties": {"canonical": "1980s", "start": 1980, "end": 1989, "weight": 1.0},
            
            "90s": {"canonical": "1990s", "start": 1990, "end": 1999, "weight": 0.95},
            "1990s": {"canonical": "1990s", "start": 1990, "end": 1999, "weight": 0.95},
            "nineties": {"canonical": "1990s", "start": 1990, "end": 1999, "weight": 0.95},
            
            "2000s": {"canonical": "2000s", "start": 2000, "end": 2009, "weight": 0.8},
            "2010s": {"canonical": "2010s", "start": 2010, "end": 2019, "weight": 0.7},
            "2020s": {"canonical": "2020s", "start": 2020, "end": 2029, "weight": 0.6},
            
            "classic": {"canonical": "Classic", "start": 1960, "end": 1985, "weight": 1.0},
            "vintage": {"canonical": "Vintage", "start": 1960, "end": 1980, "weight": 0.9},
            "golden": {"canonical": "Golden Age", "start": 1970, "end": 1990, "weight": 1.0},
            "modern": {"canonical": "Modern", "start": 2010, "end": 2025, "weight": 0.7},
            "contemporary": {"canonical": "Contemporary", "start": 2015, "end": 2025, "weight": 0.6}
        }
        
        # Era transition compatibility (how well eras flow together)
        self.era_transitions = {
            "1970s": {"1980s": 0.9, "1990s": 0.6, "Classic": 0.8, "Vintage": 0.9},
            "1980s": {"1970s": 0.9, "1990s": 0.9, "2000s": 0.7, "Classic": 0.8, "Golden Age": 0.9},
            "1990s": {"1980s": 0.9, "2000s": 0.9, "2010s": 0.7, "Golden Age": 0.8},
            "2000s": {"1990s": 0.9, "2010s": 0.9, "Modern": 0.8},
            "2010s": {"2000s": 0.9, "2020s": 0.9, "Modern": 0.9, "Contemporary": 0.8},
            "2020s": {"2010s": 0.9, "Contemporary": 0.9, "Modern": 0.8},
            "Classic": {"1970s": 0.8, "1980s": 0.8, "Vintage": 0.9, "Golden Age": 0.9},
            "Vintage": {"1970s": 0.9, "Classic": 0.9},
            "Golden Age": {"1980s": 0.9, "1990s": 0.8, "Classic": 0.9},
            "Modern": {"2010s": 0.9, "2020s": 0.8, "Contemporary": 0.9},
            "Contemporary": {"2020s": 0.9, "Modern": 0.9}
        }
    
    def _init_language_mappings(self):
        """Initialize language mappings and cultural contexts"""
        self.language_mappings = {
            "spanish": {
                "canonical": "Spanish",
                "cultural_context": "Latin American",
                "bridge_potential": 0.9,
                "compatible_with": ["portuguese", "instrumental"]
            },
            "english": {
                "canonical": "English", 
                "cultural_context": "Anglo-American",
                "bridge_potential": 0.8,
                "compatible_with": ["instrumental"]
            },
            "portuguese": {
                "canonical": "Portuguese",
                "cultural_context": "Brazilian",
                "bridge_potential": 0.7,
                "compatible_with": ["spanish", "instrumental"]
            },
            "instrumental": {
                "canonical": "Instrumental",
                "cultural_context": "Universal",
                "bridge_potential": 1.0,
                "compatible_with": ["spanish", "english", "portuguese", "french", "italian"]
            },
            "french": {
                "canonical": "French",
                "cultural_context": "European",
                "bridge_potential": 0.6,
                "compatible_with": ["instrumental", "spanish"]
            },
            "italian": {
                "canonical": "Italian",
                "cultural_context": "European",
                "bridge_potential": 0.6,
                "compatible_with": ["instrumental", "spanish"]
            }
        }
        
        # Language transition scores
        self.language_transitions = {
            "Spanish": {
                "Spanish": 1.0,
                "Portuguese": 0.8,
                "Instrumental": 0.9,
                "English": 0.4,
                "French": 0.5,
                "Italian": 0.6
            },
            "English": {
                "English": 1.0,
                "Instrumental": 0.9,
                "Spanish": 0.4,
                "Portuguese": 0.3,
                "French": 0.5
            },
            "Portuguese": {
                "Portuguese": 1.0,
                "Spanish": 0.8,
                "Instrumental": 0.9,
                "English": 0.3
            },
            "Instrumental": {
                "Instrumental": 1.0,
                "Spanish": 0.9,
                "English": 0.9,
                "Portuguese": 0.9,
                "French": 0.9,
                "Italian": 0.9
            },
            "French": {
                "French": 1.0,
                "Instrumental": 0.9,
                "Italian": 0.7,
                "Spanish": 0.5,
                "English": 0.5
            },
            "Italian": {
                "Italian": 1.0,
                "Instrumental": 0.9,
                "French": 0.7,
                "Spanish": 0.6
            }
        }
    
    def _init_cultural_bridges(self):
        """Initialize cultural bridge patterns"""
        self.cultural_bridges = {
            # Patterns that work well for cultural transitions
            "latin_to_anglo": {
                "bridge_subgenres": ["latin jazz", "fusion", "world music"],
                "bridge_moods": ["uplifting", "energetic"],
                "transition_score": 0.7
            },
            "traditional_to_modern": {
                "bridge_subgenres": ["neo-traditional", "contemporary", "fusion"],
                "bridge_eras": ["1990s", "2000s"],
                "transition_score": 0.6
            },
            "instrumental_universal": {
                "bridge_potential": 1.0,
                "works_with": "all"
            }
        }
    
    def analyze_temporal_clusters(self, tracks: List[Track], enhanced_metadata: Dict[str, Dict]) -> List[TemporalCluster]:
        """
        Analyze tracks and group them into temporal clusters
        
        Args:
            tracks: List of tracks to analyze
            enhanced_metadata: LLM metadata for each track
            
        Returns:
            List of temporal clusters sorted by era
        """
        era_groups = {}
        
        for track in tracks:
            metadata = enhanced_metadata.get(track.id, {})
            era = (metadata.get('era', '') or '').lower().strip()
            
            if era and era in self.era_mappings:
                canonical_era = self.era_mappings[era]["canonical"]
                
                if canonical_era not in era_groups:
                    era_groups[canonical_era] = {
                        'tracks': [],
                        'era_info': self.era_mappings[era]
                    }
                
                era_groups[canonical_era]['tracks'].append(track)
        
        # Create temporal clusters
        clusters = []
        for era, group in era_groups.items():
            cluster = TemporalCluster(
                era=era,
                tracks=group['tracks'],
                start_year=group['era_info']['start'],
                end_year=group['era_info']['end'],
                cultural_weight=group['era_info']['weight'],
                transition_score=self._calculate_era_transition_score(era)
            )
            clusters.append(cluster)
        
        # Sort by start year
        clusters.sort(key=lambda x: x.start_year)
        
        return clusters
    
    def analyze_linguistic_clusters(self, tracks: List[Track], enhanced_metadata: Dict[str, Dict]) -> List[LinguisticCluster]:
        """
        Analyze tracks and group them into linguistic clusters
        
        Args:
            tracks: List of tracks to analyze
            enhanced_metadata: LLM metadata for each track
            
        Returns:
            List of linguistic clusters
        """
        language_groups = {}
        
        for track in tracks:
            metadata = enhanced_metadata.get(track.id, {})
            language = (metadata.get('language', '') or '').lower().strip()
            
            if language and language in self.language_mappings:
                canonical_lang = self.language_mappings[language]["canonical"]
                
                if canonical_lang not in language_groups:
                    language_groups[canonical_lang] = {
                        'tracks': [],
                        'lang_info': self.language_mappings[language]
                    }
                
                language_groups[canonical_lang]['tracks'].append(track)
        
        # Create linguistic clusters
        clusters = []
        for language, group in language_groups.items():
            cluster = LinguisticCluster(
                language=language,
                tracks=group['tracks'],
                cultural_context=group['lang_info']['cultural_context'],
                bridge_potential=group['lang_info']['bridge_potential']
            )
            clusters.append(cluster)
        
        # Sort by bridge potential (most versatile first)
        clusters.sort(key=lambda x: x.bridge_potential, reverse=True)
        
        return clusters
    
    def create_temporal_sequence(
        self,
        tracks: List[Track],
        enhanced_metadata: Dict[str, Dict],
        temporal_flow: TemporalFlow = TemporalFlow.CHRONOLOGICAL,
        target_length: int = 10
    ) -> TemporalLinguisticSequence:
        """
        Create a temporally coherent sequence
        
        Args:
            tracks: Available tracks
            enhanced_metadata: LLM metadata
            temporal_flow: Type of temporal progression
            target_length: Target sequence length
            
        Returns:
            Temporal linguistic sequence
        """
        temporal_clusters = self.analyze_temporal_clusters(tracks, enhanced_metadata)
        
        if not temporal_clusters:
            # Fallback: return tracks in original order
            return TemporalLinguisticSequence(
                tracks=tracks[:target_length],
                temporal_flow=temporal_flow,
                linguistic_flow=LinguisticFlow.MONOLINGUAL,
                era_progression=[],
                language_progression=[],
                narrative_score=0.5,
                cultural_coherence=0.5,
                transition_quality=0.5
            )
        
        if temporal_flow == TemporalFlow.CHRONOLOGICAL:
            sequence = self._create_chronological_sequence(temporal_clusters, target_length)
        elif temporal_flow == TemporalFlow.REVERSE_CHRONO:
            sequence = self._create_reverse_chronological_sequence(temporal_clusters, target_length)
        elif temporal_flow == TemporalFlow.ERA_CLUSTERING:
            sequence = self._create_era_clustering_sequence(temporal_clusters, target_length)
        elif temporal_flow == TemporalFlow.NOSTALGIC_WAVES:
            sequence = self._create_nostalgic_waves_sequence(temporal_clusters, target_length)
        elif temporal_flow == TemporalFlow.GOLDEN_AGE_FOCUS:
            sequence = self._create_golden_age_sequence(temporal_clusters, target_length)
        else:  # CROSS_GENERATIONAL
            sequence = self._create_cross_generational_sequence(temporal_clusters, target_length)
        
        # Calculate quality metrics
        sequence.narrative_score = self._calculate_narrative_score(sequence, enhanced_metadata)
        sequence.cultural_coherence = self._calculate_cultural_coherence(sequence, enhanced_metadata)
        sequence.transition_quality = self._calculate_transition_quality(sequence, enhanced_metadata)
        
        return sequence
    
    def create_linguistic_sequence(
        self,
        tracks: List[Track],
        enhanced_metadata: Dict[str, Dict],
        linguistic_flow: LinguisticFlow = LinguisticFlow.BILINGUAL_BRIDGE,
        target_length: int = 10
    ) -> TemporalLinguisticSequence:
        """
        Create a linguistically coherent sequence
        
        Args:
            tracks: Available tracks
            enhanced_metadata: LLM metadata
            linguistic_flow: Type of linguistic progression
            target_length: Target sequence length
            
        Returns:
            Temporal linguistic sequence
        """
        linguistic_clusters = self.analyze_linguistic_clusters(tracks, enhanced_metadata)
        
        if not linguistic_clusters:
            return TemporalLinguisticSequence(
                tracks=tracks[:target_length],
                temporal_flow=TemporalFlow.CHRONOLOGICAL,
                linguistic_flow=linguistic_flow,
                era_progression=[],
                language_progression=[],
                narrative_score=0.5,
                cultural_coherence=0.5,
                transition_quality=0.5
            )
        
        if linguistic_flow == LinguisticFlow.MONOLINGUAL:
            sequence = self._create_monolingual_sequence(linguistic_clusters, target_length)
        elif linguistic_flow == LinguisticFlow.BILINGUAL_BRIDGE:
            sequence = self._create_bilingual_sequence(linguistic_clusters, target_length)
        elif linguistic_flow == LinguisticFlow.MULTILINGUAL_JOURNEY:
            sequence = self._create_multilingual_sequence(linguistic_clusters, target_length)
        elif linguistic_flow == LinguisticFlow.CULTURAL_FUSION:
            sequence = self._create_cultural_fusion_sequence(linguistic_clusters, target_length)
        elif linguistic_flow == LinguisticFlow.INSTRUMENTAL_BRIDGE:
            sequence = self._create_instrumental_bridge_sequence(linguistic_clusters, target_length)
        else:  # LANGUAGE_WAVES
            sequence = self._create_language_waves_sequence(linguistic_clusters, target_length)
        
        # Calculate quality metrics
        sequence.narrative_score = self._calculate_narrative_score(sequence, enhanced_metadata)
        sequence.cultural_coherence = self._calculate_cultural_coherence(sequence, enhanced_metadata)
        sequence.transition_quality = self._calculate_transition_quality(sequence, enhanced_metadata)
        
        return sequence
    
    def create_combined_sequence(
        self,
        tracks: List[Track],
        enhanced_metadata: Dict[str, Dict],
        temporal_flow: TemporalFlow = TemporalFlow.CHRONOLOGICAL,
        linguistic_flow: LinguisticFlow = LinguisticFlow.BILINGUAL_BRIDGE,
        target_length: int = 10
    ) -> TemporalLinguisticSequence:
        """
        Create a sequence optimized for both temporal and linguistic coherence
        
        Args:
            tracks: Available tracks
            enhanced_metadata: LLM metadata
            temporal_flow: Type of temporal progression
            linguistic_flow: Type of linguistic progression
            target_length: Target sequence length
            
        Returns:
            Optimized temporal linguistic sequence
        """
        temporal_clusters = self.analyze_temporal_clusters(tracks, enhanced_metadata)
        linguistic_clusters = self.analyze_linguistic_clusters(tracks, enhanced_metadata)
        
        # Create combined optimization
        sequence_tracks = []
        era_progression = []
        language_progression = []
        
        # Use sophisticated algorithm to balance both temporal and linguistic factors
        sequence_tracks = self._optimize_combined_sequence(
            temporal_clusters, linguistic_clusters, enhanced_metadata, target_length
        )
        
        # Track progressions
        for track in sequence_tracks:
            metadata = enhanced_metadata.get(track.id, {})
            era = self._normalize_era(metadata.get('era', ''))
            language = self._normalize_language(metadata.get('language', ''))
            
            if era:
                era_progression.append(era)
            if language:
                language_progression.append(language)
        
        sequence = TemporalLinguisticSequence(
            tracks=sequence_tracks,
            temporal_flow=temporal_flow,
            linguistic_flow=linguistic_flow,
            era_progression=era_progression,
            language_progression=language_progression,
            narrative_score=0.0,
            cultural_coherence=0.0,
            transition_quality=0.0
        )
        
        # Calculate quality metrics
        sequence.narrative_score = self._calculate_narrative_score(sequence, enhanced_metadata)
        sequence.cultural_coherence = self._calculate_cultural_coherence(sequence, enhanced_metadata)
        sequence.transition_quality = self._calculate_transition_quality(sequence, enhanced_metadata)
        
        return sequence
    
    def _create_chronological_sequence(self, clusters: List[TemporalCluster], target_length: int) -> TemporalLinguisticSequence:
        """Create chronological sequence from earliest to latest"""
        tracks = []
        era_progression = []
        
        for cluster in clusters:
            tracks_to_add = min(len(cluster.tracks), max(1, target_length // len(clusters)))
            selected_tracks = cluster.tracks[:tracks_to_add]
            tracks.extend(selected_tracks)
            era_progression.extend([cluster.era] * len(selected_tracks))
            
            if len(tracks) >= target_length:
                break
        
        return TemporalLinguisticSequence(
            tracks=tracks[:target_length],
            temporal_flow=TemporalFlow.CHRONOLOGICAL,
            linguistic_flow=LinguisticFlow.MONOLINGUAL,
            era_progression=era_progression[:target_length],
            language_progression=[],
            narrative_score=0.0,
            cultural_coherence=0.0,
            transition_quality=0.0
        )
    
    def _create_reverse_chronological_sequence(self, clusters: List[TemporalCluster], target_length: int) -> TemporalLinguisticSequence:
        """Create reverse chronological sequence from latest to earliest"""
        reversed_clusters = list(reversed(clusters))
        sequence = self._create_chronological_sequence(reversed_clusters, target_length)
        sequence.temporal_flow = TemporalFlow.REVERSE_CHRONO
        return sequence
    
    def _create_era_clustering_sequence(self, clusters: List[TemporalCluster], target_length: int) -> TemporalLinguisticSequence:
        """Group tracks by era, then transition between eras"""
        tracks = []
        era_progression = []
        
        # Sort clusters by cultural weight
        sorted_clusters = sorted(clusters, key=lambda x: x.cultural_weight, reverse=True)
        
        for cluster in sorted_clusters:
            tracks_per_era = min(len(cluster.tracks), max(2, target_length // len(clusters)))
            selected_tracks = cluster.tracks[:tracks_per_era]
            tracks.extend(selected_tracks)
            era_progression.extend([cluster.era] * len(selected_tracks))
            
            if len(tracks) >= target_length:
                break
        
        sequence = TemporalLinguisticSequence(
            tracks=tracks[:target_length],
            temporal_flow=TemporalFlow.ERA_CLUSTERING,
            linguistic_flow=LinguisticFlow.MONOLINGUAL,
            era_progression=era_progression[:target_length],
            language_progression=[],
            narrative_score=0.0,
            cultural_coherence=0.0,
            transition_quality=0.0
        )
        return sequence
    
    def _create_nostalgic_waves_sequence(self, clusters: List[TemporalCluster], target_length: int) -> TemporalLinguisticSequence:
        """Create waves between different eras"""
        tracks = []
        era_progression = []
        
        # Alternate between clusters
        cluster_index = 0
        tracks_per_wave = 2
        
        while len(tracks) < target_length and clusters:
            cluster = clusters[cluster_index % len(clusters)]
            wave_tracks = cluster.tracks[:tracks_per_wave]
            tracks.extend(wave_tracks)
            era_progression.extend([cluster.era] * len(wave_tracks))
            
            # Remove used tracks
            cluster.tracks = cluster.tracks[tracks_per_wave:]
            if not cluster.tracks:
                clusters.remove(cluster)
            else:
                cluster_index += 1
        
        sequence = TemporalLinguisticSequence(
            tracks=tracks[:target_length],
            temporal_flow=TemporalFlow.NOSTALGIC_WAVES,
            linguistic_flow=LinguisticFlow.MONOLINGUAL,
            era_progression=era_progression[:target_length],
            language_progression=[],
            narrative_score=0.0,
            cultural_coherence=0.0,
            transition_quality=0.0
        )
        return sequence
    
    def _create_golden_age_sequence(self, clusters: List[TemporalCluster], target_length: int) -> TemporalLinguisticSequence:
        """Focus on golden age tracks (highest cultural weight)"""
        # Find golden age clusters
        golden_clusters = [c for c in clusters if c.cultural_weight >= 0.9]
        
        if not golden_clusters:
            golden_clusters = [max(clusters, key=lambda x: x.cultural_weight)]
        
        sequence = self._create_era_clustering_sequence(golden_clusters, target_length)
        sequence.temporal_flow = TemporalFlow.GOLDEN_AGE_FOCUS
        return sequence
    
    def _create_cross_generational_sequence(self, clusters: List[TemporalCluster], target_length: int) -> TemporalLinguisticSequence:
        """Bridge different generations"""
        if len(clusters) < 2:
            return self._create_chronological_sequence(clusters, target_length)
        
        tracks = []
        era_progression = []
        
        # Alternate between oldest and newest, working inward
        start_idx = 0
        end_idx = len(clusters) - 1
        
        while start_idx <= end_idx and len(tracks) < target_length:
            # Add from oldest
            if start_idx <= end_idx:
                cluster = clusters[start_idx]
                track = cluster.tracks.pop(0) if cluster.tracks else None
                if track:
                    tracks.append(track)
                    era_progression.append(cluster.era)
                start_idx += 1
            
            # Add from newest
            if start_idx <= end_idx and len(tracks) < target_length:
                cluster = clusters[end_idx]
                track = cluster.tracks.pop(0) if cluster.tracks else None
                if track:
                    tracks.append(track)
                    era_progression.append(cluster.era)
                end_idx -= 1
        
        sequence = TemporalLinguisticSequence(
            tracks=tracks[:target_length],
            temporal_flow=TemporalFlow.CROSS_GENERATIONAL,
            linguistic_flow=LinguisticFlow.MONOLINGUAL,
            era_progression=era_progression[:target_length],
            language_progression=[],
            narrative_score=0.0,
            cultural_coherence=0.0,
            transition_quality=0.0
        )
        return sequence
    
    def _create_monolingual_sequence(self, clusters: List[LinguisticCluster], target_length: int) -> TemporalLinguisticSequence:
        """Create sequence in single language"""
        # Choose largest cluster
        main_cluster = max(clusters, key=lambda x: len(x.tracks))
        
        tracks = main_cluster.tracks[:target_length]
        language_progression = [main_cluster.language] * len(tracks)
        
        return TemporalLinguisticSequence(
            tracks=tracks,
            temporal_flow=TemporalFlow.CHRONOLOGICAL,
            linguistic_flow=LinguisticFlow.MONOLINGUAL,
            era_progression=[],
            language_progression=language_progression,
            narrative_score=0.0,
            cultural_coherence=0.0,
            transition_quality=0.0
        )
    
    def _create_bilingual_sequence(self, clusters: List[LinguisticCluster], target_length: int) -> TemporalLinguisticSequence:
        """Create bilingual sequence with bridges"""
        if len(clusters) < 2:
            return self._create_monolingual_sequence(clusters, target_length)
        
        # Choose two main languages
        main_clusters = sorted(clusters, key=lambda x: len(x.tracks), reverse=True)[:2]
        
        tracks = []
        language_progression = []
        
        # Alternate between languages
        cluster_index = 0
        tracks_per_segment = 2
        
        while len(tracks) < target_length and any(c.tracks for c in main_clusters):
            cluster = main_clusters[cluster_index % 2]
            
            if cluster.tracks:
                segment_tracks = cluster.tracks[:tracks_per_segment]
                tracks.extend(segment_tracks)
                language_progression.extend([cluster.language] * len(segment_tracks))
                cluster.tracks = cluster.tracks[tracks_per_segment:]
            
            cluster_index += 1
        
        return TemporalLinguisticSequence(
            tracks=tracks[:target_length],
            temporal_flow=TemporalFlow.CHRONOLOGICAL,
            linguistic_flow=LinguisticFlow.BILINGUAL_BRIDGE,
            era_progression=[],
            language_progression=language_progression[:target_length],
            narrative_score=0.0,
            cultural_coherence=0.0,
            transition_quality=0.0
        )
    
    def _create_multilingual_sequence(self, clusters: List[LinguisticCluster], target_length: int) -> TemporalLinguisticSequence:
        """Create multilingual journey"""
        tracks = []
        language_progression = []
        
        # Sort by bridge potential
        sorted_clusters = sorted(clusters, key=lambda x: x.bridge_potential, reverse=True)
        
        cluster_index = 0
        while len(tracks) < target_length and sorted_clusters:
            cluster = sorted_clusters[cluster_index % len(sorted_clusters)]
            
            if cluster.tracks:
                track = cluster.tracks.pop(0)
                tracks.append(track)
                language_progression.append(cluster.language)
            else:
                sorted_clusters.remove(cluster)
                continue
            
            cluster_index += 1
        
        return TemporalLinguisticSequence(
            tracks=tracks,
            temporal_flow=TemporalFlow.CHRONOLOGICAL,
            linguistic_flow=LinguisticFlow.MULTILINGUAL_JOURNEY,
            era_progression=[],
            language_progression=language_progression,
            narrative_score=0.0,
            cultural_coherence=0.0,
            transition_quality=0.0
        )
    
    def _create_cultural_fusion_sequence(self, clusters: List[LinguisticCluster], target_length: int) -> TemporalLinguisticSequence:
        """Create gradual cultural fusion"""
        # Start with most compatible languages
        compatible_clusters = [c for c in clusters if c.bridge_potential > 0.7]
        
        if not compatible_clusters:
            compatible_clusters = clusters
        
        return self._create_multilingual_sequence(compatible_clusters, target_length)
    
    def _create_instrumental_bridge_sequence(self, clusters: List[LinguisticCluster], target_length: int) -> TemporalLinguisticSequence:
        """Use instrumental tracks as bridges between languages"""
        # Find instrumental cluster
        instrumental_cluster = None
        vocal_clusters = []
        
        for cluster in clusters:
            if cluster.language.lower() == "instrumental":
                instrumental_cluster = cluster
            else:
                vocal_clusters.append(cluster)
        
        tracks = []
        language_progression = []
        
        if instrumental_cluster and vocal_clusters:
            # Alternate: vocal → instrumental → vocal
            cluster_index = 0
            
            while len(tracks) < target_length:
                # Add vocal track
                if vocal_clusters and cluster_index < len(vocal_clusters):
                    vocal_cluster = vocal_clusters[cluster_index % len(vocal_clusters)]
                    if vocal_cluster.tracks:
                        track = vocal_cluster.tracks.pop(0)
                        tracks.append(track)
                        language_progression.append(vocal_cluster.language)
                
                # Add instrumental bridge
                if instrumental_cluster.tracks and len(tracks) < target_length:
                    track = instrumental_cluster.tracks.pop(0)
                    tracks.append(track)
                    language_progression.append(instrumental_cluster.language)
                
                cluster_index += 1
                
                # Stop if we've used all tracks
                if not any(c.tracks for c in vocal_clusters) and not instrumental_cluster.tracks:
                    break
        else:
            # Fallback to multilingual
            return self._create_multilingual_sequence(clusters, target_length)
        
        return TemporalLinguisticSequence(
            tracks=tracks[:target_length],
            temporal_flow=TemporalFlow.CHRONOLOGICAL,
            linguistic_flow=LinguisticFlow.INSTRUMENTAL_BRIDGE,
            era_progression=[],
            language_progression=language_progression[:target_length],
            narrative_score=0.0,
            cultural_coherence=0.0,
            transition_quality=0.0
        )
    
    def _create_language_waves_sequence(self, clusters: List[LinguisticCluster], target_length: int) -> TemporalLinguisticSequence:
        """Create waves alternating between languages"""
        if len(clusters) < 2:
            return self._create_monolingual_sequence(clusters, target_length)
        
        tracks = []
        language_progression = []
        
        # Sort by track count
        sorted_clusters = sorted(clusters, key=lambda x: len(x.tracks), reverse=True)
        
        cluster_index = 0
        wave_size = 1
        current_wave = 0
        
        while len(tracks) < target_length and sorted_clusters:
            cluster = sorted_clusters[cluster_index % len(sorted_clusters)]
            
            if cluster.tracks:
                track = cluster.tracks.pop(0)
                tracks.append(track)
                language_progression.append(cluster.language)
                current_wave += 1
                
                if current_wave >= wave_size:
                    cluster_index += 1
                    current_wave = 0
                    wave_size = min(3, wave_size + 1)  # Gradually increase wave size
            else:
                sorted_clusters.remove(cluster)
        
        return TemporalLinguisticSequence(
            tracks=tracks,
            temporal_flow=TemporalFlow.CHRONOLOGICAL,
            linguistic_flow=LinguisticFlow.LANGUAGE_WAVES,
            era_progression=[],
            language_progression=language_progression,
            narrative_score=0.0,
            cultural_coherence=0.0,
            transition_quality=0.0
        )
    
    def _optimize_combined_sequence(
        self,
        temporal_clusters: List[TemporalCluster],
        linguistic_clusters: List[LinguisticCluster],
        enhanced_metadata: Dict[str, Dict],
        target_length: int
    ) -> List[Track]:
        """Optimize sequence for both temporal and linguistic coherence"""
        # Create unified track pool with scores
        scored_tracks = []
        
        for t_cluster in temporal_clusters:
            for l_cluster in linguistic_clusters:
                # Find tracks that belong to both clusters
                common_tracks = set(t_cluster.tracks) & set(l_cluster.tracks)
                
                for track in common_tracks:
                    temporal_score = t_cluster.cultural_weight * t_cluster.transition_score
                    linguistic_score = l_cluster.bridge_potential
                    combined_score = (temporal_score + linguistic_score) / 2
                    
                    scored_tracks.append((track, combined_score, t_cluster.era, l_cluster.language))
        
        # Sort by combined score
        scored_tracks.sort(key=lambda x: x[1], reverse=True)
        
        # Select tracks ensuring diversity
        selected_tracks = []
        used_eras = set()
        used_languages = set()
        
        for track, score, era, language in scored_tracks:
            if len(selected_tracks) >= target_length:
                break
            
            # Prefer diversity in early selections
            diversity_bonus = 0
            if len(selected_tracks) < target_length // 2:
                if era not in used_eras:
                    diversity_bonus += 0.1
                if language not in used_languages:
                    diversity_bonus += 0.1
            
            final_score = score + diversity_bonus
            
            selected_tracks.append(track)
            used_eras.add(era)
            used_languages.add(language)
        
        return selected_tracks
    
    def _calculate_era_transition_score(self, era: str) -> float:
        """Calculate how well an era transitions to other eras"""
        if era not in self.era_transitions:
            return 0.5
        
        transitions = self.era_transitions[era]
        return sum(transitions.values()) / len(transitions) if transitions else 0.5
    
    def _normalize_era(self, era: str) -> str:
        """Normalize era string to canonical form"""
        era_lower = era.lower().strip()
        if era_lower in self.era_mappings:
            return self.era_mappings[era_lower]["canonical"]
        return era
    
    def _normalize_language(self, language: str) -> str:
        """Normalize language string to canonical form"""
        lang_lower = language.lower().strip()
        if lang_lower in self.language_mappings:
            return self.language_mappings[lang_lower]["canonical"]
        return language
    
    def _calculate_narrative_score(self, sequence: TemporalLinguisticSequence, enhanced_metadata: Dict[str, Dict]) -> float:
        """Calculate how well the sequence tells a story"""
        if len(sequence.tracks) < 2:
            return 0.5
        
        score = 0.0
        transitions = 0
        
        for i in range(len(sequence.tracks) - 1):
            current_track = sequence.tracks[i]
            next_track = sequence.tracks[i + 1]
            
            current_meta = enhanced_metadata.get(current_track.id, {})
            next_meta = enhanced_metadata.get(next_track.id, {})
            
            # Check era transition
            current_era = self._normalize_era(current_meta.get('era', ''))
            next_era = self._normalize_era(next_meta.get('era', ''))
            
            if current_era and next_era:
                era_score = self.era_transitions.get(current_era, {}).get(next_era, 0.5)
                score += era_score
                transitions += 1
        
        return score / transitions if transitions > 0 else 0.5
    
    def _calculate_cultural_coherence(self, sequence: TemporalLinguisticSequence, enhanced_metadata: Dict[str, Dict]) -> float:
        """Calculate cultural coherence of the sequence"""
        if not sequence.tracks:
            return 0.5
        
        languages = []
        for track in sequence.tracks:
            metadata = enhanced_metadata.get(track.id, {})
            language = self._normalize_language(metadata.get('language', ''))
            if language:
                languages.append(language)
        
        if not languages:
            return 0.5
        
        # Calculate diversity vs coherence balance
        unique_languages = set(languages)
        
        if len(unique_languages) == 1:
            return 1.0  # Perfect coherence
        elif len(unique_languages) <= 3:
            return 0.8  # Good diversity with coherence
        else:
            return 0.6  # High diversity, lower coherence
    
    def _calculate_transition_quality(self, sequence: TemporalLinguisticSequence, enhanced_metadata: Dict[str, Dict]) -> float:
        """Calculate quality of transitions between tracks"""
        if len(sequence.tracks) < 2:
            return 0.5
        
        total_score = 0.0
        transitions = 0
        
        for i in range(len(sequence.tracks) - 1):
            current_track = sequence.tracks[i]
            next_track = sequence.tracks[i + 1]
            
            current_meta = enhanced_metadata.get(current_track.id, {})
            next_meta = enhanced_metadata.get(next_track.id, {})
            
            # Language transition
            current_lang = self._normalize_language(current_meta.get('language', ''))
            next_lang = self._normalize_language(next_meta.get('language', ''))
            
            if current_lang and next_lang:
                lang_score = self.language_transitions.get(current_lang, {}).get(next_lang, 0.5)
                total_score += lang_score
                transitions += 1
        
        return total_score / transitions if transitions > 0 else 0.5