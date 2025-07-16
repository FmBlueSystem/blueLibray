"""
LLM-powered Mixing Algorithm Plugin
Combines traditional harmonic mixing with AI-powered musical understanding
"""

import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from ..core.plugin_system import MixingAlgorithmPlugin, PluginMetadata, PluginType
from ..core.harmonic_engine import Track
from .llm_integration import LLMIntegration, LLMConfig, LLMProvider, MusicAnalysis


@dataclass
class LLMixingConfig:
    """Configuration for LLM mixing algorithm"""
    llm_weight: float = 0.3  # How much to weight LLM vs traditional algorithm
    traditional_weight: float = 0.7
    use_emotional_analysis: bool = True
    use_genre_intelligence: bool = True
    use_mixing_suggestions: bool = True
    fallback_to_traditional: bool = True
    context_awareness: bool = True


class LLMixingAlgorithmPlugin(MixingAlgorithmPlugin):
    """
    Intelligent mixing algorithm that combines traditional harmonic mixing
    with LLM-powered musical understanding and context awareness
    """
    
    def __init__(self, llm_config: LLMConfig = None, mixing_config: LLMixingConfig = None):
        self.llm_config = llm_config or self._get_default_llm_config()
        self.mixing_config = mixing_config or LLMixingConfig()
        self.llm_integration = None
        self.analysis_cache: Dict[str, MusicAnalysis] = {}
        
        # Traditional algorithm weights for fallback
        self.traditional_weights = {
            'key': 0.4,
            'bpm': 0.3,
            'energy': 0.2,
            'emotional': 0.1
        }
        
        self.is_initialized = False
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="LLM Intelligent Mixing",
            version="1.0.0",
            author="BlueLibrary AI Team",
            description="AI-powered mixing algorithm using Large Language Models for intelligent track compatibility analysis",
            plugin_type=PluginType.MIXING_ALGORITHM,
            dependencies=["aiohttp"]
        )
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the LLM mixing plugin"""
        try:
            # Update configurations from provided config
            if 'llm_provider' in config:
                self.llm_config.provider = LLMProvider(config['llm_provider'])
            if 'llm_api_key' in config:
                self.llm_config.api_key = config['llm_api_key']
            if 'llm_model' in config:
                self.llm_config.model = config['llm_model']
            if 'llm_weight' in config:
                self.mixing_config.llm_weight = config['llm_weight']
                self.mixing_config.traditional_weight = 1.0 - config['llm_weight']
            
            # Initialize LLM integration
            if self.llm_config.api_key:
                self.llm_integration = LLMIntegration(self.llm_config)
                print(f"LLM Mixing Algorithm initialized with {self.llm_config.provider.value}")
            else:
                print("LLM API key not provided, falling back to traditional algorithm")
            
            self.is_initialized = True
            return True
            
        except Exception as e:
            print(f"Failed to initialize LLM Mixing Algorithm: {e}")
            self.is_initialized = False
            return False
    
    def cleanup(self):
        """Cleanup plugin resources"""
        self.analysis_cache.clear()
        self.llm_integration = None
        self.is_initialized = False
    
    async def calculate_compatibility_async(self, track1: Track, track2: Track) -> float:
        """Async version of compatibility calculation"""
        if not self.is_initialized or not self.llm_integration:
            return self._calculate_traditional_compatibility(track1, track2)
        
        try:
            # Get LLM analyses for both tracks
            analysis1 = await self._get_track_analysis(track1)
            analysis2 = await self._get_track_analysis(track2)
            
            # Calculate LLM-based compatibility
            llm_score = await self._calculate_llm_compatibility(track1, track2, analysis1, analysis2)
            
            # Calculate traditional compatibility
            traditional_score = self._calculate_traditional_compatibility(track1, track2)
            
            # Combine scores
            final_score = (
                llm_score * self.mixing_config.llm_weight +
                traditional_score * self.mixing_config.traditional_weight
            )
            
            return max(0.0, min(1.0, final_score))
            
        except Exception as e:
            print(f"LLM compatibility calculation failed: {e}")
            if self.mixing_config.fallback_to_traditional:
                return self._calculate_traditional_compatibility(track1, track2)
            return 0.0
    
    def calculate_compatibility(self, track1: Track, track2: Track) -> float:
        """Sync wrapper for async compatibility calculation"""
        try:
            # Try to get existing event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Create a new task for async execution
                task = asyncio.create_task(self.calculate_compatibility_async(track1, track2))
                return 0.5  # Return neutral score, actual score will be available later
            else:
                # Run in the event loop
                return loop.run_until_complete(self.calculate_compatibility_async(track1, track2))
        except RuntimeError:
            # No event loop, create one
            return asyncio.run(self.calculate_compatibility_async(track1, track2))
        except Exception as e:
            print(f"Error in compatibility calculation: {e}")
            return self._calculate_traditional_compatibility(track1, track2)
    
    async def _get_track_analysis(self, track: Track) -> MusicAnalysis:
        """Get or generate LLM analysis for a track"""
        if track.id in self.analysis_cache:
            return self.analysis_cache[track.id]
        
        context = f"DJ mixing analysis for track in collection"
        analysis = await self.llm_integration.analyze_track(track, context)
        self.analysis_cache[track.id] = analysis
        return analysis
    
    async def _calculate_llm_compatibility(
        self, 
        track1: Track, 
        track2: Track, 
        analysis1: MusicAnalysis,
        analysis2: MusicAnalysis
    ) -> float:
        """Calculate compatibility using LLM analysis"""
        # Direct LLM compatibility query
        direct_score = await self.llm_integration.suggest_compatibility(track1, track2)
        
        # Analytical score based on LLM analysis
        analytical_score = self._calculate_analytical_llm_score(analysis1, analysis2)
        
        # Combine direct and analytical scores
        combined_score = (direct_score * 0.6 + analytical_score * 0.4)
        
        return combined_score
    
    def _calculate_analytical_llm_score(self, analysis1: MusicAnalysis, analysis2: MusicAnalysis) -> float:
        """Calculate compatibility from LLM analysis data"""
        score = 0.0
        weight_sum = 0.0
        
        # Emotional profile compatibility
        if analysis1.emotional_profile and analysis2.emotional_profile:
            emotional_score = self._calculate_emotional_compatibility(
                analysis1.emotional_profile, 
                analysis2.emotional_profile
            )
            score += emotional_score * 0.3
            weight_sum += 0.3
        
        # Compatibility factors
        if analysis1.compatibility_factors and analysis2.compatibility_factors:
            factors_score = self._calculate_factors_compatibility(
                analysis1.compatibility_factors,
                analysis2.compatibility_factors
            )
            score += factors_score * 0.4
            weight_sum += 0.4
        
        # Confidence weighting
        confidence = (analysis1.confidence_score + analysis2.confidence_score) / 2
        score += confidence * 0.3
        weight_sum += 0.3
        
        return score / weight_sum if weight_sum > 0 else 0.5
    
    def _calculate_emotional_compatibility(self, profile1: Dict[str, float], profile2: Dict[str, float]) -> float:
        """Calculate emotional profile compatibility"""
        common_emotions = set(profile1.keys()) & set(profile2.keys())
        if not common_emotions:
            return 0.5
        
        compatibility = 0.0
        for emotion in common_emotions:
            # High compatibility when emotions are similar
            diff = abs(profile1[emotion] - profile2[emotion])
            emotion_compat = 1.0 - diff
            compatibility += emotion_compat
        
        return compatibility / len(common_emotions)
    
    def _calculate_factors_compatibility(self, factors1: Dict[str, float], factors2: Dict[str, float]) -> float:
        """Calculate compatibility factors score"""
        common_factors = set(factors1.keys()) & set(factors2.keys())
        if not common_factors:
            return 0.5
        
        compatibility = 0.0
        for factor in common_factors:
            # Average the factor scores
            factor_compat = (factors1[factor] + factors2[factor]) / 2
            compatibility += factor_compat
        
        return compatibility / len(common_factors)
    
    def _calculate_traditional_compatibility(self, track1: Track, track2: Track) -> float:
        """Fallback traditional compatibility calculation"""
        score = 0.0
        
        # Key compatibility
        if track1.key and track2.key:
            key_score = self._calculate_key_compatibility(track1.key, track2.key)
            score += key_score * self.traditional_weights['key']
        
        # BPM compatibility  
        if track1.bpm and track2.bpm:
            bpm_score = self._calculate_bpm_compatibility(track1.bpm, track2.bpm)
            score += bpm_score * self.traditional_weights['bpm']
        
        # Energy compatibility
        if track1.energy and track2.energy:
            energy_score = self._calculate_energy_compatibility(track1.energy, track2.energy)
            score += energy_score * self.traditional_weights['energy']
        
        # Emotional compatibility
        if track1.emotional_intensity and track2.emotional_intensity:
            emotional_score = self._calculate_emotional_intensity_compatibility(
                track1.emotional_intensity, track2.emotional_intensity
            )
            score += emotional_score * self.traditional_weights['emotional']
        
        return max(0.0, min(1.0, score))
    
    def _calculate_key_compatibility(self, key1: str, key2: str) -> float:
        """Simple key compatibility"""
        if key1 == key2:
            return 1.0
        # Add basic Camelot wheel logic here
        return 0.5
    
    def _calculate_bpm_compatibility(self, bpm1: float, bpm2: float) -> float:
        """BPM compatibility calculation"""
        diff = abs(bpm1 - bpm2)
        if diff <= 5:
            return 1.0
        elif diff <= 15:
            return 0.8
        elif diff <= 30:
            return 0.5
        else:
            return 0.2
    
    def _calculate_energy_compatibility(self, energy1: float, energy2: float) -> float:
        """Energy level compatibility"""
        diff = abs(energy1 - energy2)
        return max(0.0, 1.0 - (diff / 10.0))
    
    def _calculate_emotional_intensity_compatibility(self, emotion1: float, emotion2: float) -> float:
        """Emotional intensity compatibility"""
        diff = abs(emotion1 - emotion2)
        return max(0.0, 1.0 - (diff / 10.0))
    
    def get_weight_parameters(self) -> Dict[str, Dict]:
        """Return available weight parameters"""
        return {
            'llm_weight': {
                'min': 0.0,
                'max': 1.0,
                'default': 0.3,
                'description': 'Weight of LLM analysis vs traditional algorithm'
            },
            'emotional_weight': {
                'min': 0.0,
                'max': 1.0,
                'default': 0.3,
                'description': 'Weight of emotional analysis in LLM scoring'
            },
            'confidence_weight': {
                'min': 0.0,
                'max': 1.0,
                'default': 0.3,
                'description': 'Weight of LLM confidence in final score'
            }
        }
    
    def set_weights(self, weights: Dict[str, float]):
        """Set algorithm weights"""
        if 'llm_weight' in weights:
            self.mixing_config.llm_weight = weights['llm_weight']
            self.mixing_config.traditional_weight = 1.0 - weights['llm_weight']
    
    def _get_default_llm_config(self) -> LLMConfig:
        """Get default LLM configuration"""
        return LLMConfig(
            provider=LLMProvider.OPENAI,
            model="gpt-3.5-turbo",
            max_tokens=500,
            temperature=0.1,
            cache_enabled=True
        )
    
    async def analyze_track_batch(self, tracks: List[Track]) -> Dict[str, MusicAnalysis]:
        """Batch analyze tracks for better performance"""
        if not self.llm_integration:
            return {}
        
        analyses = await self.llm_integration.batch_analyze_tracks(tracks)
        result = {}
        
        for track, analysis in zip(tracks, analyses):
            if isinstance(analysis, MusicAnalysis):
                result[track.id] = analysis
                self.analysis_cache[track.id] = analysis
        
        return result
    
    def get_analysis_for_track(self, track_id: str) -> Optional[MusicAnalysis]:
        """Get cached analysis for a track"""
        return self.analysis_cache.get(track_id)
    
    def clear_analysis_cache(self):
        """Clear the analysis cache"""
        self.analysis_cache.clear()