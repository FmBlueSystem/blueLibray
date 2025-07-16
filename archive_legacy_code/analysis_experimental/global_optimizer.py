"""
Global Playlist Optimization using Graph Pathfinding
Advanced A* algorithm for globally optimal playlist generation
"""

import heapq
import numpy as np
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from ..core.harmonic_engine import Track


class OptimizationObjective(Enum):
    """Different optimization objectives"""
    COMPATIBILITY = "compatibility"      # Maximize track compatibility
    NARRATIVE = "narrative"              # Optimize for storytelling
    ENERGY_FLOW = "energy_flow"          # Optimize energy progression
    CULTURAL_JOURNEY = "cultural"        # Optimize cultural coherence
    BALANCED = "balanced"                # Balance multiple objectives
    CUSTOM = "custom"                    # Custom weights


@dataclass
class TrackNode:
    """Node representing a track in the playlist graph"""
    track: Track
    metadata: Dict
    position: int  # Position in playlist
    
    # Graph properties
    predecessors: List['TrackNode'] = field(default_factory=list)
    successors: List['TrackNode'] = field(default_factory=list)
    
    # A* properties
    g_score: float = float('inf')  # Cost from start
    h_score: float = 0.0           # Heuristic to goal
    f_score: float = float('inf')  # Total score
    parent: Optional['TrackNode'] = None
    
    # Optimization properties
    compatibility_scores: Dict[str, float] = field(default_factory=dict)
    constraint_violations: int = 0
    local_optimality: float = 0.0
    
    def __hash__(self):
        return hash((self.track.id, self.position))
    
    def __eq__(self, other):
        return isinstance(other, TrackNode) and self.track.id == other.track.id and self.position == other.position


@dataclass
class OptimizationConstraint:
    """Constraint for playlist optimization"""
    name: str
    constraint_type: str  # "hard", "soft", "preference"
    weight: float
    check_function: callable
    violation_penalty: float = 1.0


@dataclass 
class OptimizationResult:
    """Result of global optimization"""
    playlist: List[Track]
    total_score: float
    objective_scores: Dict[str, float]
    path_cost: float
    nodes_explored: int
    optimization_time: float
    constraint_violations: List[Dict]
    alternative_paths: List[List[Track]] = field(default_factory=list)


class GlobalPlaylistOptimizer:
    """
    Advanced playlist optimizer using graph pathfinding and multi-objective optimization
    """
    
    def __init__(self):
        # Import compatibility engines with fallbacks
        self._init_compatibility_engines()
        
        # Optimization objectives and weights
        self.objective_weights = {
            OptimizationObjective.COMPATIBILITY: {
                'harmonic': 0.3,
                'stylistic': 0.25,
                'contextual': 0.2,
                'structural': 0.15,
                'temporal': 0.1
            },
            OptimizationObjective.NARRATIVE: {
                'temporal_coherence': 0.4,
                'cultural_coherence': 0.3,
                'emotional_arc': 0.2,
                'diversity': 0.1
            },
            OptimizationObjective.ENERGY_FLOW: {
                'energy_progression': 0.5,
                'danceability_flow': 0.3,
                'crowd_appeal': 0.2
            },
            OptimizationObjective.CULTURAL_JOURNEY: {
                'linguistic_coherence': 0.4,
                'era_progression': 0.35,
                'cultural_bridges': 0.25
            },
            OptimizationObjective.BALANCED: {
                'compatibility': 0.25,
                'narrative': 0.25,
                'energy': 0.25,
                'cultural': 0.25
            }
        }
        
        # Default constraints
        self.default_constraints = self._init_default_constraints()
        
        # Performance settings
        self.max_nodes_to_explore = 10000
        self.beam_search_width = 50
        self.early_termination_threshold = 0.95
    
    def _init_compatibility_engines(self):
        """Initialize compatibility engines with fallbacks"""
        try:
            from .enhanced_compatibility import EnhancedCompatibilityEngine
            from ..core.harmonic_engine import HarmonicMixingEngine
            self.harmonic_engine = HarmonicMixingEngine()
            self.enhanced_engine = EnhancedCompatibilityEngine(self.harmonic_engine)
        except ImportError:
            self.harmonic_engine = None
            self.enhanced_engine = None
        
        try:
            from .stylistic_compatibility import StylisticCompatibilityMatrix
            self.stylistic_matrix = StylisticCompatibilityMatrix()
        except ImportError:
            self.stylistic_matrix = None
        
        try:
            from .contextual_curves import ContextualMixingEngine
            self.contextual_engine = ContextualMixingEngine()
        except ImportError:
            self.contextual_engine = None
        
        try:
            from .temporal_linguistic_sequencer import TemporalLinguisticSequencer
            self.temporal_sequencer = TemporalLinguisticSequencer()
        except ImportError:
            self.temporal_sequencer = None
    
    def _init_default_constraints(self) -> List[OptimizationConstraint]:
        """Initialize default constraints"""
        constraints = []
        
        # Hard constraint: No duplicate tracks
        constraints.append(OptimizationConstraint(
            name="no_duplicates",
            constraint_type="hard",
            weight=1.0,
            check_function=self._check_no_duplicates,
            violation_penalty=10.0
        ))
        
        # Soft constraint: Minimum compatibility
        constraints.append(OptimizationConstraint(
            name="min_compatibility",
            constraint_type="soft", 
            weight=0.8,
            check_function=lambda path: self._check_min_compatibility(path, 0.3),
            violation_penalty=2.0
        ))
        
        # Soft constraint: Energy flow consistency
        constraints.append(OptimizationConstraint(
            name="energy_flow",
            constraint_type="soft",
            weight=0.6,
            check_function=self._check_energy_flow,
            violation_penalty=1.5
        ))
        
        # Preference: Cultural coherence
        constraints.append(OptimizationConstraint(
            name="cultural_coherence",
            constraint_type="preference",
            weight=0.4,
            check_function=self._check_cultural_coherence,
            violation_penalty=0.5
        ))
        
        return constraints
    
    def optimize_playlist(
        self,
        tracks: List[Track],
        enhanced_metadata: Dict[str, Dict],
        target_length: int = 10,
        start_track: Optional[Track] = None,
        objective: OptimizationObjective = OptimizationObjective.BALANCED,
        custom_weights: Optional[Dict[str, float]] = None,
        constraints: Optional[List[OptimizationConstraint]] = None,
        max_alternatives: int = 3
    ) -> OptimizationResult:
        """
        Optimize playlist using global graph pathfinding
        
        Args:
            tracks: Available tracks
            enhanced_metadata: LLM metadata for tracks
            target_length: Target playlist length
            start_track: Starting track (optional)
            objective: Optimization objective
            custom_weights: Custom objective weights
            constraints: Custom constraints
            max_alternatives: Number of alternative paths to find
            
        Returns:
            OptimizationResult with optimal playlist and metrics
        """
        import time
        start_time = time.time()
        
        # Prepare optimization
        active_constraints = constraints or self.default_constraints
        objective_weights = custom_weights or self.objective_weights.get(objective, self.objective_weights[OptimizationObjective.BALANCED])
        
        # Build graph
        graph = self._build_playlist_graph(tracks, enhanced_metadata, target_length)
        
        # Find optimal path using A*
        optimal_path, nodes_explored = self._find_optimal_path(
            graph, start_track, target_length, objective_weights, active_constraints
        )
        
        # Find alternative paths
        alternative_paths = self._find_alternative_paths(
            graph, optimal_path, target_length, objective_weights, active_constraints, max_alternatives
        )
        
        optimization_time = time.time() - start_time
        
        # Calculate final scores
        if optimal_path:
            total_score = self._calculate_path_score(optimal_path, objective_weights)
            objective_scores = self._calculate_objective_breakdown(optimal_path, enhanced_metadata)
            path_cost = self._calculate_path_cost(optimal_path, active_constraints)
            constraint_violations = self._analyze_constraint_violations(optimal_path, active_constraints)
            playlist = [node.track for node in optimal_path]
            alternative_playlists = [[node.track for node in path] for path in alternative_paths]
        else:
            # Fallback to greedy if A* fails
            playlist = self._greedy_fallback(tracks, enhanced_metadata, target_length, start_track)
            total_score = 0.5
            objective_scores = {}
            path_cost = float('inf')
            constraint_violations = []
            alternative_playlists = []
        
        return OptimizationResult(
            playlist=playlist,
            total_score=total_score,
            objective_scores=objective_scores,
            path_cost=path_cost,
            nodes_explored=nodes_explored,
            optimization_time=optimization_time,
            constraint_violations=constraint_violations,
            alternative_paths=alternative_playlists
        )
    
    def _build_playlist_graph(
        self,
        tracks: List[Track],
        enhanced_metadata: Dict[str, Dict],
        target_length: int
    ) -> Dict[int, List[TrackNode]]:
        """
        Build graph where nodes are (track, position) pairs
        
        Returns:
            Graph as dict[position] -> List[TrackNode]
        """
        graph = {}
        
        # Create nodes for each position
        for position in range(target_length):
            graph[position] = []
            
            for track in tracks:
                metadata = enhanced_metadata.get(track.id, {})
                node = TrackNode(
                    track=track,
                    metadata=metadata,
                    position=position
                )
                
                # Calculate compatibility scores with other tracks
                node.compatibility_scores = self._calculate_node_compatibility_scores(
                    track, tracks, enhanced_metadata
                )
                
                graph[position].append(node)
        
        # Connect nodes (create edges)
        self._connect_graph_nodes(graph, target_length)
        
        return graph
    
    def _connect_graph_nodes(self, graph: Dict[int, List[TrackNode]], target_length: int):
        """Connect nodes to create graph edges"""
        for position in range(target_length - 1):
            current_nodes = graph[position]
            next_nodes = graph[position + 1]
            
            for current_node in current_nodes:
                for next_node in next_nodes:
                    # Don't connect same track to itself
                    if current_node.track.id != next_node.track.id:
                        current_node.successors.append(next_node)
                        next_node.predecessors.append(current_node)
    
    def _calculate_node_compatibility_scores(
        self,
        track: Track,
        all_tracks: List[Track],
        enhanced_metadata: Dict[str, Dict]
    ) -> Dict[str, float]:
        """Calculate compatibility scores between this track and all others"""
        scores = {}
        track_metadata = enhanced_metadata.get(track.id, {})
        
        for other_track in all_tracks:
            if other_track.id == track.id:
                continue
            
            other_metadata = enhanced_metadata.get(other_track.id, {})
            
            # Calculate different types of compatibility
            compatibility_score = 0.0
            
            # Harmonic compatibility
            if self.harmonic_engine:
                harmonic_score = self.harmonic_engine.calculate_compatibility(track, other_track)
                compatibility_score += harmonic_score * 0.3
            
            # Stylistic compatibility
            if self.stylistic_matrix:
                profile1 = self.stylistic_matrix.extract_style_profile(track, track_metadata)
                profile2 = self.stylistic_matrix.extract_style_profile(other_track, other_metadata)
                stylistic_score = self.stylistic_matrix.calculate_stylistic_compatibility(profile1, profile2)
                compatibility_score += stylistic_score * 0.25
            
            # Temporal compatibility (era/language)
            if self.temporal_sequencer:
                era1 = self.temporal_sequencer._normalize_era(track_metadata.get('era', ''))
                era2 = self.temporal_sequencer._normalize_era(other_metadata.get('era', ''))
                lang1 = self.temporal_sequencer._normalize_language(track_metadata.get('language', ''))
                lang2 = self.temporal_sequencer._normalize_language(other_metadata.get('language', ''))
                
                temporal_score = 0.5
                if era1 and era2:
                    temporal_score = self.temporal_sequencer.era_transitions.get(era1, {}).get(era2, 0.5)
                if lang1 and lang2:
                    lang_score = self.temporal_sequencer.language_transitions.get(lang1, {}).get(lang2, 0.5)
                    temporal_score = (temporal_score + lang_score) / 2
                
                compatibility_score += temporal_score * 0.2
            
            # Energy compatibility
            energy1 = self._normalize_percentage(track_metadata.get('danceability'))
            energy2 = self._normalize_percentage(other_metadata.get('danceability'))
            if energy1 is not None and energy2 is not None:
                energy_diff = abs(energy1 - energy2)
                energy_score = max(0, 1.0 - energy_diff)
                compatibility_score += energy_score * 0.15
            
            # Crowd appeal compatibility
            appeal1 = self._normalize_percentage(track_metadata.get('crowd_appeal'))
            appeal2 = self._normalize_percentage(other_metadata.get('crowd_appeal'))
            if appeal1 is not None and appeal2 is not None:
                appeal_score = min(appeal1, appeal2)  # Limited by weakest track
                compatibility_score += appeal_score * 0.1
            
            scores[other_track.id] = compatibility_score
        
        return scores
    
    def _find_optimal_path(
        self,
        graph: Dict[int, List[TrackNode]],
        start_track: Optional[Track],
        target_length: int,
        objective_weights: Dict[str, float],
        constraints: List[OptimizationConstraint]
    ) -> Tuple[List[TrackNode], int]:
        """
        Find optimal path using A* algorithm
        
        Returns:
            (optimal_path, nodes_explored)
        """
        if not graph or target_length == 0:
            return [], 0
        
        # Initialize start nodes
        start_nodes = []
        if start_track:
            start_nodes = [node for node in graph[0] if node.track.id == start_track.id]
        else:
            start_nodes = graph[0]  # All possible starting nodes
        
        # A* algorithm with beam search optimization
        open_set = []
        closed_set = set()
        nodes_explored = 0
        
        # Initialize start nodes
        for start_node in start_nodes:
            start_node.g_score = 0
            start_node.h_score = self._calculate_heuristic(start_node, target_length, objective_weights)
            start_node.f_score = start_node.g_score + start_node.h_score
            heapq.heappush(open_set, (start_node.f_score, id(start_node), start_node, [start_node]))
        
        best_complete_path = None
        best_complete_score = float('inf')
        
        while open_set and nodes_explored < self.max_nodes_to_explore:
            current_f, _, current_node, current_path = heapq.heappop(open_set)
            nodes_explored += 1
            
            # Check if we've reached target length
            if len(current_path) == target_length:
                path_score = self._calculate_path_score_with_constraints(current_path, objective_weights, constraints)
                if path_score < best_complete_score:
                    best_complete_score = path_score
                    best_complete_path = current_path
                
                # Early termination if score is very good
                if path_score <= self.early_termination_threshold:
                    break
                
                continue
            
            # Skip if already processed this state
            state_key = (current_node.track.id, len(current_path), tuple(node.track.id for node in current_path))
            if state_key in closed_set:
                continue
            closed_set.add(state_key)
            
            # Explore successors
            next_position = len(current_path)
            if next_position < target_length:
                successors = self._get_valid_successors(current_node, current_path, graph, constraints)
                
                # Beam search: limit number of successors
                if len(successors) > self.beam_search_width:
                    successors = self._select_best_successors(successors, current_path, objective_weights, self.beam_search_width)
                
                for successor in successors:
                    new_path = current_path + [successor]
                    
                    # Calculate cost to reach this successor
                    g_score = current_node.g_score + self._calculate_edge_cost(current_node, successor, new_path, objective_weights)
                    
                    # Skip if we've found a better path to this node
                    if g_score >= successor.g_score:
                        continue
                    
                    # Update scores
                    successor.g_score = g_score
                    successor.h_score = self._calculate_heuristic(successor, target_length - len(new_path), objective_weights)
                    successor.f_score = successor.g_score + successor.h_score
                    successor.parent = current_node
                    
                    heapq.heappush(open_set, (successor.f_score, id(successor), successor, new_path))
        
        return best_complete_path or [], nodes_explored
    
    def _get_valid_successors(
        self,
        current_node: TrackNode,
        current_path: List[TrackNode],
        graph: Dict[int, List[TrackNode]],
        constraints: List[OptimizationConstraint]
    ) -> List[TrackNode]:
        """Get valid successor nodes considering constraints"""
        next_position = len(current_path)
        if next_position >= len(graph):
            return []
        
        all_successors = graph[next_position]
        valid_successors = []
        
        for successor in all_successors:
            # Check hard constraints
            is_valid = True
            test_path = current_path + [successor]
            
            for constraint in constraints:
                if constraint.constraint_type == "hard":
                    if not constraint.check_function(test_path):
                        is_valid = False
                        break
            
            if is_valid:
                valid_successors.append(successor)
        
        return valid_successors
    
    def _select_best_successors(
        self,
        successors: List[TrackNode],
        current_path: List[TrackNode],
        objective_weights: Dict[str, float],
        beam_width: int
    ) -> List[TrackNode]:
        """Select best successors for beam search"""
        if len(successors) <= beam_width:
            return successors
        
        # Score successors based on local optimality
        scored_successors = []
        current_node = current_path[-1]
        
        for successor in successors:
            score = self._calculate_edge_cost(current_node, successor, current_path + [successor], objective_weights)
            scored_successors.append((score, successor))
        
        # Sort by score (lower is better) and take top beam_width
        scored_successors.sort(key=lambda x: x[0])
        return [successor for _, successor in scored_successors[:beam_width]]
    
    def _calculate_edge_cost(
        self,
        from_node: TrackNode,
        to_node: TrackNode,
        path: List[TrackNode],
        objective_weights: Dict[str, float]
    ) -> float:
        """Calculate cost of edge between two nodes"""
        # Base compatibility cost (lower compatibility = higher cost)
        compatibility = from_node.compatibility_scores.get(to_node.track.id, 0.5)
        compatibility_cost = 1.0 - compatibility
        
        # Position-based cost (prefer tracks in appropriate positions)
        position_cost = self._calculate_position_cost(to_node, len(path) - 1)
        
        # Diversity cost (penalize too much repetition)
        diversity_cost = self._calculate_diversity_cost(to_node, path[:-1])
        
        # Combine costs based on objective weights
        total_cost = (
            compatibility_cost * objective_weights.get('compatibility', 0.4) +
            position_cost * objective_weights.get('position_optimality', 0.3) +
            diversity_cost * objective_weights.get('diversity', 0.3)
        )
        
        return total_cost
    
    def _calculate_heuristic(
        self,
        node: TrackNode,
        remaining_positions: int,
        objective_weights: Dict[str, float]
    ) -> float:
        """Calculate heuristic estimate of cost to complete path"""
        if remaining_positions <= 0:
            return 0.0
        
        # Estimate based on average compatibility and remaining length
        avg_compatibility = np.mean(list(node.compatibility_scores.values())) if node.compatibility_scores else 0.5
        
        # Optimistic estimate: assume we can maintain current compatibility level
        estimated_cost = (1.0 - avg_compatibility) * remaining_positions * 0.5
        
        return estimated_cost
    
    def _calculate_position_cost(self, node: TrackNode, position: int) -> float:
        """Calculate cost based on track appropriateness for position"""
        # This could be enhanced with more sophisticated position-based scoring
        # For now, use a simple energy progression model
        
        metadata = node.metadata
        energy = self._normalize_percentage(metadata.get('danceability'))
        crowd_appeal = self._normalize_percentage(metadata.get('crowd_appeal'))
        
        if energy is None:
            return 0.0
        
        # Simple model: want higher energy in middle positions
        total_positions = 10  # Approximate
        optimal_position_ratio = position / max(1, total_positions - 1)
        
        # Energy should peak around 60-70% through playlist
        optimal_energy_peak = 0.7
        if optimal_position_ratio <= optimal_energy_peak:
            target_energy = 0.3 + (optimal_position_ratio / optimal_energy_peak) * 0.6
        else:
            remaining_ratio = (optimal_position_ratio - optimal_energy_peak) / (1.0 - optimal_energy_peak)
            target_energy = 0.9 - remaining_ratio * 0.4
        
        energy_diff = abs(energy - target_energy)
        position_cost = energy_diff * 0.5
        
        # Bonus for high crowd appeal
        if crowd_appeal:
            position_cost *= (1.0 - crowd_appeal * 0.2)
        
        return position_cost
    
    def _calculate_diversity_cost(self, node: TrackNode, previous_path: List[TrackNode]) -> float:
        """Calculate cost to encourage diversity"""
        if not previous_path:
            return 0.0
        
        metadata = node.metadata
        
        # Check for repetition in recent tracks
        recent_tracks = previous_path[-3:]  # Last 3 tracks
        repetition_penalty = 0.0
        
        for prev_node in recent_tracks:
            prev_metadata = prev_node.metadata
            
            # Same subgenre penalty
            if ((metadata.get('subgenre', '') or '').lower() == (prev_metadata.get('subgenre', '') or '').lower() and
                metadata.get('subgenre')):
                repetition_penalty += 0.1
            
            # Same artist penalty
            if node.track.artist.lower() == prev_node.track.artist.lower():
                repetition_penalty += 0.2
            
            # Same era penalty
            if ((metadata.get('era', '') or '').lower() == (prev_metadata.get('era', '') or '').lower() and
                metadata.get('era')):
                repetition_penalty += 0.05
        
        return min(repetition_penalty, 0.5)  # Cap penalty
    
    def _calculate_path_score(self, path: List[TrackNode], objective_weights: Dict[str, float]) -> float:
        """Calculate total score for a complete path"""
        if not path:
            return float('inf')
        
        total_score = 0.0
        
        # Calculate transition scores
        for i in range(len(path) - 1):
            current_node = path[i]
            next_node = path[i + 1]
            
            transition_score = current_node.compatibility_scores.get(next_node.track.id, 0.5)
            total_score += (1.0 - transition_score)  # Convert to cost
        
        # Add position costs
        for i, node in enumerate(path):
            position_cost = self._calculate_position_cost(node, i)
            total_score += position_cost
        
        # Add diversity costs
        for i, node in enumerate(path):
            if i > 0:
                diversity_cost = self._calculate_diversity_cost(node, path[:i])
                total_score += diversity_cost
        
        return total_score
    
    def _calculate_path_score_with_constraints(
        self,
        path: List[TrackNode],
        objective_weights: Dict[str, float],
        constraints: List[OptimizationConstraint]
    ) -> float:
        """Calculate path score including constraint violations"""
        base_score = self._calculate_path_score(path, objective_weights)
        
        # Add constraint violation penalties
        for constraint in constraints:
            if not constraint.check_function(path):
                base_score += constraint.violation_penalty
        
        return base_score
    
    def _find_alternative_paths(
        self,
        graph: Dict[int, List[TrackNode]],
        optimal_path: List[TrackNode],
        target_length: int,
        objective_weights: Dict[str, float],
        constraints: List[OptimizationConstraint],
        max_alternatives: int
    ) -> List[List[TrackNode]]:
        """Find alternative paths that are different from optimal"""
        if not optimal_path or max_alternatives <= 0:
            return []
        
        # For now, return empty list - full implementation would use
        # techniques like k-shortest paths or path diversification
        return []
    
    def _greedy_fallback(
        self,
        tracks: List[Track],
        enhanced_metadata: Dict[str, Dict],
        target_length: int,
        start_track: Optional[Track]
    ) -> List[Track]:
        """Fallback to greedy algorithm if A* fails"""
        if not tracks:
            return []
        
        playlist = []
        available_tracks = tracks.copy()
        
        # Start with specified track or best track
        if start_track and start_track in available_tracks:
            current_track = start_track
            available_tracks.remove(start_track)
        else:
            current_track = available_tracks.pop(0)
        
        playlist.append(current_track)
        
        # Greedy selection
        while len(playlist) < target_length and available_tracks:
            best_track = None
            best_score = -1
            
            current_metadata = enhanced_metadata.get(current_track.id, {})
            
            for track in available_tracks:
                track_metadata = enhanced_metadata.get(track.id, {})
                
                # Simple compatibility calculation
                score = 0.5  # Default
                
                if self.harmonic_engine:
                    score = self.harmonic_engine.calculate_compatibility(current_track, track)
                
                if score > best_score:
                    best_score = score
                    best_track = track
            
            if best_track:
                playlist.append(best_track)
                available_tracks.remove(best_track)
                current_track = best_track
            else:
                break
        
        return playlist
    
    def _calculate_objective_breakdown(self, path: List[TrackNode], enhanced_metadata: Dict[str, Dict]) -> Dict[str, float]:
        """Calculate breakdown of objective scores"""
        if not path:
            return {}
        
        scores = {}
        
        # Compatibility score
        compatibility_scores = []
        for i in range(len(path) - 1):
            current_node = path[i]
            next_node = path[i + 1]
            score = current_node.compatibility_scores.get(next_node.track.id, 0.5)
            compatibility_scores.append(score)
        scores['compatibility'] = np.mean(compatibility_scores) if compatibility_scores else 0.5
        
        # Energy flow score
        energy_scores = []
        for i in range(len(path) - 1):
            current_energy = self._normalize_percentage(path[i].metadata.get('danceability'))
            next_energy = self._normalize_percentage(path[i + 1].metadata.get('danceability'))
            if current_energy is not None and next_energy is not None:
                energy_diff = abs(current_energy - next_energy)
                energy_scores.append(1.0 - energy_diff)
        scores['energy_flow'] = np.mean(energy_scores) if energy_scores else 0.5
        
        # Cultural coherence score
        if self.temporal_sequencer:
            languages = []
            eras = []
            for node in path:
                lang = self.temporal_sequencer._normalize_language(node.metadata.get('language', ''))
                era = self.temporal_sequencer._normalize_era(node.metadata.get('era', ''))
                if lang:
                    languages.append(lang)
                if era:
                    eras.append(era)
            
            # Calculate coherence based on diversity
            unique_languages = set(languages)
            unique_eras = set(eras)
            
            lang_coherence = 1.0 if len(unique_languages) <= 2 else max(0.3, 1.0 - (len(unique_languages) - 2) * 0.2)
            era_coherence = 1.0 if len(unique_eras) <= 3 else max(0.3, 1.0 - (len(unique_eras) - 3) * 0.15)
            
            scores['cultural_coherence'] = (lang_coherence + era_coherence) / 2
        else:
            scores['cultural_coherence'] = 0.5
        
        # Crowd appeal score
        crowd_appeals = []
        for node in path:
            appeal = self._normalize_percentage(node.metadata.get('crowd_appeal'))
            if appeal is not None:
                crowd_appeals.append(appeal)
        scores['crowd_appeal'] = np.mean(crowd_appeals) if crowd_appeals else 0.5
        
        return scores
    
    def _calculate_path_cost(self, path: List[TrackNode], constraints: List[OptimizationConstraint]) -> float:
        """Calculate total path cost including constraints"""
        if not path:
            return float('inf')
        
        cost = 0.0
        
        # Transition costs
        for i in range(len(path) - 1):
            compatibility = path[i].compatibility_scores.get(path[i + 1].track.id, 0.5)
            cost += (1.0 - compatibility)
        
        # Constraint violation costs
        for constraint in constraints:
            if not constraint.check_function(path):
                cost += constraint.violation_penalty
        
        return cost
    
    def _analyze_constraint_violations(self, path: List[TrackNode], constraints: List[OptimizationConstraint]) -> List[Dict]:
        """Analyze which constraints are violated"""
        violations = []
        
        for constraint in constraints:
            if not constraint.check_function(path):
                violations.append({
                    'constraint': constraint.name,
                    'type': constraint.constraint_type,
                    'penalty': constraint.violation_penalty,
                    'description': f"Constraint '{constraint.name}' violated"
                })
        
        return violations
    
    # Constraint check functions
    def _check_no_duplicates(self, path: List[TrackNode]) -> bool:
        """Check that no track appears twice"""
        track_ids = [node.track.id for node in path]
        return len(track_ids) == len(set(track_ids))
    
    def _check_min_compatibility(self, path: List[TrackNode], min_threshold: float) -> bool:
        """Check minimum compatibility between adjacent tracks"""
        if len(path) < 2:
            return True
        
        for i in range(len(path) - 1):
            compatibility = path[i].compatibility_scores.get(path[i + 1].track.id, 0.5)
            if compatibility < min_threshold:
                return False
        
        return True
    
    def _check_energy_flow(self, path: List[TrackNode]) -> bool:
        """Check that energy flow is reasonable"""
        if len(path) < 3:
            return True
        
        # Check for too many abrupt energy changes
        abrupt_changes = 0
        for i in range(len(path) - 1):
            current_energy = self._normalize_percentage(path[i].metadata.get('danceability'))
            next_energy = self._normalize_percentage(path[i + 1].metadata.get('danceability'))
            
            if current_energy is not None and next_energy is not None:
                energy_diff = abs(current_energy - next_energy)
                if energy_diff > 0.3:  # Large energy jump
                    abrupt_changes += 1
        
        # Allow some energy changes but not too many
        return abrupt_changes <= len(path) // 3
    
    def _check_cultural_coherence(self, path: List[TrackNode]) -> bool:
        """Check cultural coherence of the path"""
        if len(path) < 2:
            return True
        
        # Allow reasonable diversity but not too much chaos
        languages = set()
        eras = set()
        
        for node in path:
            lang = (node.metadata.get('language', '') or '').lower()
            era = (node.metadata.get('era', '') or '').lower()
            if lang:
                languages.add(lang)
            if era:
                eras.add(era)
        
        # Reasonable limits for coherence
        return len(languages) <= 3 and len(eras) <= 4
    
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