"""
Configurable Mixing Policies System
Advanced rule-based system for customizable playlist generation policies
Allows users to create, modify, and combine mixing rules
"""

import json
import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Callable, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from ..core.harmonic_engine import Track


class PolicyType(Enum):
    """Types of mixing policies"""
    HARMONIC = "harmonic"           # Key compatibility rules
    ENERGY = "energy"               # Energy flow rules
    STYLISTIC = "stylistic"         # Genre/style rules
    TEMPORAL = "temporal"           # Era/time-based rules
    LINGUISTIC = "linguistic"       # Language rules
    CONTEXTUAL = "contextual"       # Activity/mood rules
    QUALITY = "quality"             # Audio quality rules
    DIVERSITY = "diversity"         # Variety rules
    NARRATIVE = "narrative"         # Storytelling rules
    CUSTOM = "custom"               # User-defined rules


class OperatorType(Enum):
    """Types of rule operators"""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_EQUAL = "greater_equal"
    LESS_EQUAL = "less_equal"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    IN_LIST = "in_list"
    NOT_IN_LIST = "not_in_list"
    SIMILAR_TO = "similar_to"
    COMPATIBLE_WITH = "compatible_with"
    WITHIN_RANGE = "within_range"
    MATCHES_PATTERN = "matches_pattern"


class RulePriority(Enum):
    """Rule priority levels"""
    CRITICAL = "critical"       # Must be satisfied (hard constraint)
    HIGH = "high"              # Strongly preferred (high weight)
    MEDIUM = "medium"          # Moderately preferred (medium weight)
    LOW = "low"                # Weakly preferred (low weight)
    SUGGESTION = "suggestion"   # Optional hint (very low weight)


@dataclass
class PolicyRule:
    """Individual mixing rule"""
    id: str
    name: str
    description: str
    policy_type: PolicyType
    
    # Rule definition
    field: str                      # Track field to evaluate (e.g., 'key', 'bpm', 'subgenre')
    operator: OperatorType          # Comparison operator
    value: Any                      # Value to compare against
    context: str = "track"          # Context: 'track', 'transition', 'sequence', 'global'
    
    # Rule properties
    priority: RulePriority = RulePriority.MEDIUM
    weight: float = 1.0             # Rule weight for scoring
    enabled: bool = True            # Whether rule is active
    
    # Advanced properties
    tolerance: float = 0.0          # Tolerance for numeric comparisons
    adaptive: bool = False          # Whether rule adapts based on context
    time_sensitive: bool = False    # Whether rule changes by time of day
    
    # Metadata
    created_by: str = "system"
    tags: List[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class PolicyRuleSet:
    """Collection of related rules"""
    id: str
    name: str
    description: str
    rules: List[PolicyRule] = field(default_factory=list)
    
    # Combination logic
    combination_mode: str = "weighted_sum"  # "weighted_sum", "all_required", "any_satisfied", "majority"
    minimum_score: float = 0.6              # Minimum score to consider valid
    
    # Metadata
    version: str = "1.0"
    created_by: str = "system"
    tags: List[str] = field(default_factory=list)
    enabled: bool = True


@dataclass
class MixingPolicy:
    """Complete mixing policy with multiple rule sets"""
    id: str
    name: str
    description: str
    version: str = "1.0"
    
    # Rule sets
    rule_sets: List[PolicyRuleSet] = field(default_factory=list)
    
    # Global policy settings
    global_weights: Dict[PolicyType, float] = field(default_factory=dict)
    optimization_objective: str = "balanced"  # From OptimizationObjective
    fallback_strategy: str = "greedy"
    
    # Validation settings
    strict_mode: bool = False       # Whether to enforce all critical rules
    adaptive_weights: bool = True   # Whether to adapt weights based on context
    
    # Metadata
    created_by: str = "user"
    created_at: str = ""
    last_modified: str = ""
    usage_count: int = 0
    tags: List[str] = field(default_factory=list)


@dataclass
class PolicyEvaluationResult:
    """Result of policy evaluation"""
    rule_id: str
    rule_name: str
    satisfied: bool
    score: float
    expected_value: Any
    actual_value: Any
    message: str
    weight: float
    priority: RulePriority


@dataclass
class PolicyApplicationResult:
    """Result of applying a complete policy"""
    policy_id: str
    total_score: float
    rule_results: List[PolicyEvaluationResult]
    rule_set_scores: Dict[str, float]
    satisfied_critical_rules: bool
    recommendations: List[str]
    warnings: List[str]


class PolicyRuleEngine:
    """Engine for evaluating policy rules"""
    
    def __init__(self):
        self.operators = self._init_operators()
        self.field_extractors = self._init_field_extractors()
        
    def _init_operators(self) -> Dict[OperatorType, Callable]:
        """Initialize rule operators"""
        return {
            OperatorType.EQUALS: lambda a, b, t=0: abs(self._to_numeric(a) - self._to_numeric(b)) <= t if self._is_numeric(a) and self._is_numeric(b) else str(a).lower() == str(b).lower(),
            OperatorType.NOT_EQUALS: lambda a, b, t=0: not self.operators[OperatorType.EQUALS](a, b, t),
            OperatorType.GREATER_THAN: lambda a, b, t=0: self._to_numeric(a) > self._to_numeric(b) - t,
            OperatorType.LESS_THAN: lambda a, b, t=0: self._to_numeric(a) < self._to_numeric(b) + t,
            OperatorType.GREATER_EQUAL: lambda a, b, t=0: self._to_numeric(a) >= self._to_numeric(b) - t,
            OperatorType.LESS_EQUAL: lambda a, b, t=0: self._to_numeric(a) <= self._to_numeric(b) + t,
            OperatorType.CONTAINS: lambda a, b, t=0: str(b).lower() in str(a).lower(),
            OperatorType.NOT_CONTAINS: lambda a, b, t=0: str(b).lower() not in str(a).lower(),
            OperatorType.IN_LIST: lambda a, b, t=0: str(a).lower() in [str(x).lower() for x in (b if isinstance(b, list) else [b])],
            OperatorType.NOT_IN_LIST: lambda a, b, t=0: str(a).lower() not in [str(x).lower() for x in (b if isinstance(b, list) else [b])],
            OperatorType.SIMILAR_TO: lambda a, b, t=0.8: self._similarity_score(a, b) >= t,
            OperatorType.COMPATIBLE_WITH: lambda a, b, t=0.7: self._compatibility_score(a, b) >= t,
            OperatorType.WITHIN_RANGE: lambda a, b, t=0: self._in_range(a, b, t),
            OperatorType.MATCHES_PATTERN: lambda a, b, t=0: self._matches_pattern(a, b)
        }
    
    def _init_field_extractors(self) -> Dict[str, Callable]:
        """Initialize field extractors for different data sources"""
        return {
            # Track properties
            'id': lambda track, metadata=None: track.id,
            'title': lambda track, metadata=None: track.title,
            'artist': lambda track, metadata=None: track.artist,
            'key': lambda track, metadata=None: getattr(track, 'key', None),
            'bpm': lambda track, metadata=None: getattr(track, 'bpm', None),
            'energy': lambda track, metadata=None: getattr(track, 'energy', None),
            
            # LLM metadata fields
            'subgenre': lambda track, metadata=None: metadata.get('subgenre') if metadata else None,
            'mood': lambda track, metadata=None: metadata.get('mood') if metadata else None,
            'era': lambda track, metadata=None: metadata.get('era') if metadata else None,
            'language': lambda track, metadata=None: metadata.get('language') if metadata else None,
            'danceability': lambda track, metadata=None: self._normalize_percentage(metadata.get('danceability')) if metadata else None,
            'crowd_appeal': lambda track, metadata=None: self._normalize_percentage(metadata.get('crowd_appeal')) if metadata else None,
            'mix_friendly': lambda track, metadata=None: self._normalize_percentage(metadata.get('mix_friendly')) if metadata else None,
            'time_of_day': lambda track, metadata=None: metadata.get('time_of_day') if metadata else None,
            'activity': lambda track, metadata=None: metadata.get('activity') if metadata else None,
            'season': lambda track, metadata=None: metadata.get('season') if metadata else None,
        }
    
    def evaluate_rule(
        self, 
        rule: PolicyRule, 
        track: Track, 
        metadata: Optional[Dict] = None,
        context_data: Optional[Dict] = None
    ) -> PolicyEvaluationResult:
        """Evaluate a single rule against a track"""
        
        try:
            # Extract field value
            if rule.field in self.field_extractors:
                actual_value = self.field_extractors[rule.field](track, metadata)
            else:
                # Try to get from metadata directly
                actual_value = metadata.get(rule.field) if metadata else None
            
            # Handle missing values
            if actual_value is None:
                return PolicyEvaluationResult(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    satisfied=False,
                    score=0.0,
                    expected_value=rule.value,
                    actual_value=None,
                    message=f"Field '{rule.field}' not available",
                    weight=rule.weight,
                    priority=rule.priority
                )
            
            # Apply operator
            operator_func = self.operators.get(rule.operator)
            if not operator_func:
                raise ValueError(f"Unknown operator: {rule.operator}")
            
            # Evaluate rule
            satisfied = operator_func(actual_value, rule.value, rule.tolerance)
            
            # Calculate score
            if satisfied:
                score = 1.0
            else:
                # Partial credit for near misses
                score = self._calculate_partial_score(rule, actual_value)
            
            # Apply adaptive weighting if enabled
            if rule.adaptive and context_data:
                adaptive_multiplier = self._apply_adaptive_weighting(rule, context_data)
                score = min(1.0, score * adaptive_multiplier)  # Cap at 1.0
            
            message = "Satisfied" if satisfied else "Not satisfied"
            
            return PolicyEvaluationResult(
                rule_id=rule.id,
                rule_name=rule.name,
                satisfied=satisfied,
                score=score,
                expected_value=rule.value,
                actual_value=actual_value,
                message=message,
                weight=rule.weight,
                priority=rule.priority
            )
            
        except Exception as e:
            return PolicyEvaluationResult(
                rule_id=rule.id,
                rule_name=rule.name,
                satisfied=False,
                score=0.0,
                expected_value=rule.value,
                actual_value=actual_value if 'actual_value' in locals() else None,
                message=f"Error evaluating rule: {str(e)}",
                weight=rule.weight,
                priority=rule.priority
            )
    
    def _calculate_partial_score(self, rule: PolicyRule, actual_value: Any) -> float:
        """Calculate partial score for unsatisfied rules"""
        if not self._is_numeric(actual_value) or not self._is_numeric(rule.value):
            return 0.0
        
        actual_num = self._to_numeric(actual_value)
        expected_num = self._to_numeric(rule.value)
        
        if rule.operator in [OperatorType.EQUALS]:
            # Distance-based scoring
            if rule.tolerance > 0:
                distance = abs(actual_num - expected_num)
                max_distance = rule.tolerance * 2  # Allow some grace
                return max(0.0, 1.0 - (distance / max_distance))
        
        elif rule.operator in [OperatorType.GREATER_THAN, OperatorType.GREATER_EQUAL]:
            if actual_num < expected_num:
                # Proportional penalty
                deficit = expected_num - actual_num
                penalty_range = expected_num * 0.2  # 20% tolerance
                return max(0.0, 1.0 - (deficit / penalty_range))
        
        elif rule.operator in [OperatorType.LESS_THAN, OperatorType.LESS_EQUAL]:
            if actual_num > expected_num:
                # Proportional penalty
                excess = actual_num - expected_num
                penalty_range = expected_num * 0.2  # 20% tolerance
                return max(0.0, 1.0 - (excess / penalty_range))
        
        return 0.0
    
    def _apply_adaptive_weighting(self, rule: PolicyRule, context_data: Dict) -> float:
        """Apply adaptive weighting based on context"""
        multiplier = 1.0
        
        # Time-sensitive rules
        if rule.time_sensitive and 'time_of_day' in context_data:
            time_of_day = context_data['time_of_day']
            if rule.policy_type == PolicyType.ENERGY:
                if time_of_day in ['morning', 'evening'] and 'energy' in rule.field.lower():
                    multiplier *= 1.2  # Boost energy rules during active times
                elif time_of_day == 'night' and 'energy' in rule.field.lower():
                    multiplier *= 0.8  # Reduce energy importance at night
        
        # Activity-based adaptation
        if 'activity' in context_data:
            activity = context_data['activity']
            if activity == 'workout' and rule.policy_type == PolicyType.ENERGY:
                multiplier *= 1.3  # Boost energy rules for workouts
            elif activity == 'chill' and rule.policy_type == PolicyType.HARMONIC:
                multiplier *= 1.1  # Boost harmonic rules for chill sessions
        
        # Ensure multiplier stays within reasonable bounds
        return max(0.1, min(2.0, multiplier))
    
    # Utility methods
    def _is_numeric(self, value: Any) -> bool:
        """Check if value is numeric"""
        try:
            float(value)
            return True
        except (TypeError, ValueError):
            return False
    
    def _to_numeric(self, value: Any) -> float:
        """Convert value to numeric"""
        if isinstance(value, (int, float)):
            return float(value)
        elif isinstance(value, str):
            # Handle percentage strings
            if value.endswith('%'):
                return float(value[:-1]) / 100.0
            else:
                return float(value)
        else:
            raise ValueError(f"Cannot convert {value} to numeric")
    
    def _normalize_percentage(self, value: Any) -> Optional[float]:
        """Normalize percentage value to 0-1 range"""
        if not value or value == "-":
            return None
        
        if isinstance(value, str) and value.endswith('%'):
            try:
                return float(value[:-1]) / 100.0
            except ValueError:
                return None
        elif isinstance(value, (int, float)):
            if value > 1.0:
                return value / 100.0
            return float(value)
        
        return None
    
    def _similarity_score(self, a: Any, b: Any) -> float:
        """Calculate similarity score between two values"""
        str_a = str(a).lower()
        str_b = str(b).lower()
        
        if str_a == str_b:
            return 1.0
        
        # Simple Jaccard similarity for strings
        set_a = set(str_a.split())
        set_b = set(str_b.split())
        
        if not set_a and not set_b:
            return 1.0
        elif not set_a or not set_b:
            return 0.0
        
        intersection = len(set_a & set_b)
        union = len(set_a | set_b)
        
        return intersection / union if union > 0 else 0.0
    
    def _compatibility_score(self, a: Any, b: Any) -> float:
        """Calculate compatibility score (placeholder)"""
        # This would integrate with harmonic compatibility in real implementation
        return self._similarity_score(a, b)
    
    def _in_range(self, value: Any, range_spec: Any, tolerance: float) -> bool:
        """Check if value is within specified range"""
        if not self._is_numeric(value):
            return False
        
        num_value = self._to_numeric(value)
        
        if isinstance(range_spec, (list, tuple)) and len(range_spec) == 2:
            min_val, max_val = range_spec
            return min_val - tolerance <= num_value <= max_val + tolerance
        
        return False
    
    def _matches_pattern(self, value: Any, pattern: str) -> bool:
        """Check if value matches pattern (simple implementation)"""
        import re
        try:
            return bool(re.match(pattern, str(value)))
        except re.error:
            return False


class ConfigurablePolicyManager:
    """Manager for configurable mixing policies"""
    
    def __init__(self, config_dir: Optional[str] = None):
        self.config_dir = Path(config_dir) if config_dir else Path.home() / ".bluelibrary" / "policies"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.rule_engine = PolicyRuleEngine()
        self.policies: Dict[str, MixingPolicy] = {}
        self.rule_sets: Dict[str, PolicyRuleSet] = {}
        
        # Load built-in policies
        self._load_builtin_policies()
        
        # Load user policies
        self._load_user_policies()
    
    def _load_builtin_policies(self):
        """Load built-in default policies"""
        
        # Classic DJ Policy
        classic_harmonic_rules = PolicyRuleSet(
            id="classic_harmonic",
            name="Classic Harmonic Mixing",
            description="Traditional Camelot wheel harmonic mixing rules",
            rules=[
                PolicyRule(
                    id="key_compatibility",
                    name="Key Compatibility",
                    description="Tracks should be in compatible keys",
                    policy_type=PolicyType.HARMONIC,
                    field="key",
                    operator=OperatorType.COMPATIBLE_WITH,
                    value="adjacent_camelot",
                    priority=RulePriority.HIGH,
                    weight=2.0
                ),
                PolicyRule(
                    id="bpm_proximity",
                    name="BPM Proximity",
                    description="BPM should be within 10% range",
                    policy_type=PolicyType.ENERGY,
                    field="bpm",
                    operator=OperatorType.WITHIN_RANGE,
                    value=[0.9, 1.1],  # 90% to 110% of current BPM
                    priority=RulePriority.MEDIUM,
                    weight=1.5,
                    tolerance=5.0
                )
            ]
        )
        
        classic_policy = MixingPolicy(
            id="classic_dj",
            name="Classic DJ Mixing",
            description="Traditional harmonic mixing approach",
            rule_sets=[classic_harmonic_rules],
            global_weights={
                PolicyType.HARMONIC: 0.6,
                PolicyType.ENERGY: 0.3,
                PolicyType.STYLISTIC: 0.1
            }
        )
        
        # Modern AI Policy
        ai_stylistic_rules = PolicyRuleSet(
            id="ai_stylistic",
            name="AI-Enhanced Stylistic Matching",
            description="LLM-powered stylistic compatibility rules",
            rules=[
                PolicyRule(
                    id="subgenre_compatibility",
                    name="Subgenre Compatibility",
                    description="Subgenres should be compatible",
                    policy_type=PolicyType.STYLISTIC,
                    field="subgenre",
                    operator=OperatorType.SIMILAR_TO,
                    value="compatible_subgenres",
                    priority=RulePriority.HIGH,
                    weight=1.8
                ),
                PolicyRule(
                    id="mood_progression",
                    name="Mood Progression",
                    description="Moods should create good progression",
                    policy_type=PolicyType.STYLISTIC,
                    field="mood",
                    operator=OperatorType.COMPATIBLE_WITH,
                    value="mood_transitions",
                    priority=RulePriority.MEDIUM,
                    weight=1.3
                ),
                PolicyRule(
                    id="high_danceability",
                    name="High Danceability",
                    description="Maintain high danceability for parties",
                    policy_type=PolicyType.QUALITY,
                    field="danceability",
                    operator=OperatorType.GREATER_EQUAL,
                    value=0.7,
                    priority=RulePriority.MEDIUM,
                    weight=1.2,
                    adaptive=True
                )
            ]
        )
        
        ai_policy = MixingPolicy(
            id="modern_ai",
            name="Modern AI Mixing",
            description="AI-enhanced mixing with LLM metadata",
            rule_sets=[classic_harmonic_rules, ai_stylistic_rules],
            global_weights={
                PolicyType.HARMONIC: 0.3,
                PolicyType.STYLISTIC: 0.4,
                PolicyType.ENERGY: 0.2,
                PolicyType.QUALITY: 0.1
            },
            adaptive_weights=True
        )
        
        # Cultural Journey Policy
        cultural_rules = PolicyRuleSet(
            id="cultural_journey",
            name="Cultural Journey Rules",
            description="Rules for cross-cultural musical journeys",
            rules=[
                PolicyRule(
                    id="language_bridges",
                    name="Language Bridges",
                    description="Use instrumental tracks to bridge languages",
                    policy_type=PolicyType.LINGUISTIC,
                    field="language",
                    operator=OperatorType.IN_LIST,
                    value=["instrumental", "spanish", "english"],
                    priority=RulePriority.MEDIUM,
                    weight=1.0
                ),
                PolicyRule(
                    id="era_progression",
                    name="Era Progression",
                    description="Maintain reasonable era progression",
                    policy_type=PolicyType.TEMPORAL,
                    field="era",
                    operator=OperatorType.COMPATIBLE_WITH,
                    value="era_transitions",
                    priority=RulePriority.LOW,
                    weight=0.8
                )
            ]
        )
        
        cultural_policy = MixingPolicy(
            id="cultural_journey",
            name="Cultural Journey",
            description="Cross-cultural mixing with intelligent transitions",
            rule_sets=[cultural_rules],
            global_weights={
                PolicyType.LINGUISTIC: 0.4,
                PolicyType.TEMPORAL: 0.3,
                PolicyType.HARMONIC: 0.2,
                PolicyType.STYLISTIC: 0.1
            }
        )
        
        # Add built-in policies
        self.policies.update({
            classic_policy.id: classic_policy,
            ai_policy.id: ai_policy,
            cultural_policy.id: cultural_policy
        })
        
        # Add built-in rule sets
        self.rule_sets.update({
            classic_harmonic_rules.id: classic_harmonic_rules,
            ai_stylistic_rules.id: ai_stylistic_rules,
            cultural_rules.id: cultural_rules
        })
    
    def _load_user_policies(self):
        """Load user-defined policies from config directory"""
        policies_file = self.config_dir / "policies.json"
        
        if policies_file.exists():
            try:
                with open(policies_file, 'r') as f:
                    data = json.load(f)
                
                # Load policies
                for policy_data in data.get('policies', []):
                    policy = self._dict_to_policy(policy_data)
                    self.policies[policy.id] = policy
                
                # Load rule sets
                for ruleset_data in data.get('rule_sets', []):
                    ruleset = self._dict_to_ruleset(ruleset_data)
                    self.rule_sets[ruleset.id] = ruleset
                    
            except Exception as e:
                print(f"Warning: Could not load user policies: {e}")
    
    def save_user_policies(self):
        """Save user policies to config directory"""
        policies_file = self.config_dir / "policies.json"
        
        # Filter user-created policies
        user_policies = [p for p in self.policies.values() if p.created_by != "system"]
        user_rule_sets = [rs for rs in self.rule_sets.values() if rs.created_by != "system"]
        
        data = {
            'policies': [self._policy_to_dict(p) for p in user_policies],
            'rule_sets': [self._ruleset_to_dict(rs) for rs in user_rule_sets]
        }
        
        with open(policies_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def apply_policy(
        self,
        policy_id: str,
        tracks: List[Track],
        enhanced_metadata: Dict[str, Dict],
        context_data: Optional[Dict] = None
    ) -> List[PolicyApplicationResult]:
        """Apply policy to a list of tracks"""
        
        if policy_id not in self.policies:
            raise ValueError(f"Policy '{policy_id}' not found")
        
        policy = self.policies[policy_id]
        results = []
        
        for track in tracks:
            metadata = enhanced_metadata.get(track.id, {})
            result = self._apply_policy_to_track(policy, track, metadata, context_data)
            results.append(result)
        
        return results
    
    def _apply_policy_to_track(
        self,
        policy: MixingPolicy,
        track: Track,
        metadata: Dict,
        context_data: Optional[Dict] = None
    ) -> PolicyApplicationResult:
        """Apply policy to a single track"""
        
        all_rule_results = []
        rule_set_scores = {}
        total_weighted_score = 0.0
        total_weight = 0.0
        satisfied_critical_rules = True
        recommendations = []
        warnings = []
        
        # Evaluate each rule set
        for rule_set in policy.rule_sets:
            if not rule_set.enabled:
                continue
            
            rule_set_results = []
            rule_set_score = 0.0
            rule_set_weight = 0.0
            
            # Evaluate each rule in the set
            for rule in rule_set.rules:
                if not rule.enabled:
                    continue
                
                result = self.rule_engine.evaluate_rule(rule, track, metadata, context_data)
                rule_set_results.append(result)
                all_rule_results.append(result)
                
                # Check critical rules
                if rule.priority == RulePriority.CRITICAL and not result.satisfied:
                    satisfied_critical_rules = False
                    warnings.append(f"Critical rule '{rule.name}' not satisfied")
                
                # Calculate weighted score
                weight = result.weight * self._get_priority_multiplier(rule.priority)
                rule_set_score += result.score * weight
                rule_set_weight += weight
            
            # Calculate rule set score
            if rule_set_weight > 0:
                final_rule_set_score = rule_set_score / rule_set_weight
            else:
                final_rule_set_score = 0.0
            
            rule_set_scores[rule_set.id] = final_rule_set_score
            
            # Add to total score
            policy_type_weight = policy.global_weights.get(
                rule_set.rules[0].policy_type if rule_set.rules else PolicyType.CUSTOM, 
                1.0
            )
            total_weighted_score += final_rule_set_score * policy_type_weight * rule_set_weight
            total_weight += policy_type_weight * rule_set_weight
        
        # Calculate final score
        final_score = total_weighted_score / total_weight if total_weight > 0 else 0.0
        
        # Generate recommendations
        recommendations = self._generate_recommendations(all_rule_results, policy)
        
        return PolicyApplicationResult(
            policy_id=policy.id,
            total_score=final_score,
            rule_results=all_rule_results,
            rule_set_scores=rule_set_scores,
            satisfied_critical_rules=satisfied_critical_rules,
            recommendations=recommendations,
            warnings=warnings
        )
    
    def _get_priority_multiplier(self, priority: RulePriority) -> float:
        """Get weight multiplier for rule priority"""
        multipliers = {
            RulePriority.CRITICAL: 3.0,
            RulePriority.HIGH: 2.0,
            RulePriority.MEDIUM: 1.0,
            RulePriority.LOW: 0.5,
            RulePriority.SUGGESTION: 0.2
        }
        return multipliers.get(priority, 1.0)
    
    def _generate_recommendations(
        self, 
        rule_results: List[PolicyEvaluationResult], 
        policy: MixingPolicy
    ) -> List[str]:
        """Generate recommendations based on rule evaluation"""
        recommendations = []
        
        # Find unsatisfied high-priority rules
        unsatisfied_high = [r for r in rule_results 
                           if not r.satisfied and r.priority in [RulePriority.CRITICAL, RulePriority.HIGH]]
        
        for result in unsatisfied_high:
            if "key" in result.rule_id.lower():
                recommendations.append(f"Consider tracks in compatible keys (currently {result.actual_value})")
            elif "bpm" in result.rule_id.lower():
                recommendations.append(f"Look for tracks with BPM closer to {result.expected_value}")
            elif "energy" in result.rule_id.lower() or "danceability" in result.rule_id.lower():
                recommendations.append(f"Choose tracks with higher energy/danceability")
        
        return recommendations
    
    # CRUD operations for policies and rules
    def create_policy(self, policy: MixingPolicy) -> str:
        """Create a new mixing policy"""
        if policy.id in self.policies:
            raise ValueError(f"Policy '{policy.id}' already exists")
        
        policy.created_by = "user"
        self.policies[policy.id] = policy
        self.save_user_policies()
        return policy.id
    
    def update_policy(self, policy_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing policy"""
        if policy_id not in self.policies:
            return False
        
        policy = self.policies[policy_id]
        for key, value in updates.items():
            if hasattr(policy, key):
                setattr(policy, key, value)
        
        self.save_user_policies()
        return True
    
    def delete_policy(self, policy_id: str) -> bool:
        """Delete a policy"""
        if policy_id in self.policies and self.policies[policy_id].created_by == "user":
            del self.policies[policy_id]
            self.save_user_policies()
            return True
        return False
    
    def get_policy(self, policy_id: str) -> Optional[MixingPolicy]:
        """Get a policy by ID"""
        return self.policies.get(policy_id)
    
    def list_policies(self) -> List[MixingPolicy]:
        """List all available policies"""
        return list(self.policies.values())
    
    def export_policy(self, policy_id: str, filepath: str) -> bool:
        """Export a policy to a file"""
        if policy_id not in self.policies:
            return False
        
        policy = self.policies[policy_id]
        policy_dict = self._policy_to_dict(policy)
        
        with open(filepath, 'w') as f:
            json.dump(policy_dict, f, indent=2)
        
        return True
    
    def import_policy(self, filepath: str) -> Optional[str]:
        """Import a policy from a file"""
        try:
            with open(filepath, 'r') as f:
                policy_dict = json.load(f)
            
            policy = self._dict_to_policy(policy_dict)
            policy.created_by = "user"
            
            # Ensure unique ID
            base_id = policy.id
            counter = 1
            while policy.id in self.policies:
                policy.id = f"{base_id}_{counter}"
                counter += 1
            
            self.policies[policy.id] = policy
            self.save_user_policies()
            return policy.id
            
        except Exception as e:
            print(f"Error importing policy: {e}")
            return None
    
    # Utility methods for serialization
    def _policy_to_dict(self, policy: MixingPolicy) -> Dict:
        """Convert policy to dictionary"""
        policy_dict = asdict(policy)
        
        # Convert enums to strings for JSON serialization
        if 'global_weights' in policy_dict:
            global_weights = {}
            for k, v in policy_dict['global_weights'].items():
                key = k.value if hasattr(k, 'value') else str(k)
                global_weights[key] = v
            policy_dict['global_weights'] = global_weights
        
        # Convert rule sets
        for rule_set in policy_dict.get('rule_sets', []):
            # Convert rules in rule set
            for rule in rule_set.get('rules', []):
                if 'policy_type' in rule and hasattr(rule['policy_type'], 'value'):
                    rule['policy_type'] = rule['policy_type'].value
                if 'operator' in rule and hasattr(rule['operator'], 'value'):
                    rule['operator'] = rule['operator'].value
                if 'priority' in rule and hasattr(rule['priority'], 'value'):
                    rule['priority'] = rule['priority'].value
        
        return policy_dict
    
    def _dict_to_policy(self, data: Dict) -> MixingPolicy:
        """Convert dictionary to policy"""
        # Convert rule sets
        rule_sets = []
        for rs_data in data.get('rule_sets', []):
            rule_set = self._dict_to_ruleset(rs_data)
            rule_sets.append(rule_set)
        
        data['rule_sets'] = rule_sets
        
        # Convert enums
        if 'global_weights' in data:
            global_weights = {}
            for k, v in data['global_weights'].items():
                policy_type = PolicyType(k) if isinstance(k, str) else k
                global_weights[policy_type] = v
            data['global_weights'] = global_weights
        
        return MixingPolicy(**data)
    
    def _ruleset_to_dict(self, rule_set: PolicyRuleSet) -> Dict:
        """Convert rule set to dictionary"""
        return asdict(rule_set)
    
    def _dict_to_ruleset(self, data: Dict) -> PolicyRuleSet:
        """Convert dictionary to rule set"""
        # Convert rules
        rules = []
        for rule_data in data.get('rules', []):
            rule = self._dict_to_rule(rule_data)
            rules.append(rule)
        
        data['rules'] = rules
        return PolicyRuleSet(**data)
    
    def _dict_to_rule(self, data: Dict) -> PolicyRule:
        """Convert dictionary to rule"""
        # Convert enums
        if 'policy_type' in data and isinstance(data['policy_type'], str):
            data['policy_type'] = PolicyType(data['policy_type'])
        if 'operator' in data and isinstance(data['operator'], str):
            data['operator'] = OperatorType(data['operator'])
        if 'priority' in data and isinstance(data['priority'], str):
            data['priority'] = RulePriority(data['priority'])
        
        return PolicyRule(**data)