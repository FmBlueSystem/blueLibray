"""
LLM Integration System for BlueLibrary
Provides intelligent music analysis and mixing suggestions using Large Language Models
"""

import json
import asyncio
import hashlib
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
import os
from pathlib import Path

from ..core.harmonic_engine import Track
from ..core.plugin_system import PluginInterface, PluginMetadata, PluginType


class LLMProvider(Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"
    GROQ = "groq"


@dataclass
class LLMConfig:
    """Configuration for LLM integration"""
    provider: LLMProvider
    api_key: Optional[str] = None
    model: str = "gpt-3.5-turbo"
    base_url: Optional[str] = None
    max_tokens: int = 1000
    temperature: float = 0.1
    timeout: int = 30
    cache_enabled: bool = True


@dataclass
class MusicAnalysis:
    """Result of LLM music analysis"""
    track_id: str
    mood: str
    energy_description: str
    genre_details: str
    mixing_suggestions: List[str]
    compatibility_factors: Dict[str, float]
    emotional_profile: Dict[str, float]
    confidence_score: float


class LLMProvider_ABC(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    async def analyze_track(self, track: Track, context: str = "") -> MusicAnalysis:
        """Analyze a single track using LLM"""
        pass
    
    @abstractmethod
    async def suggest_compatibility(self, track1: Track, track2: Track) -> float:
        """Get LLM-based compatibility score between tracks"""
        pass
    
    @abstractmethod
    async def generate_playlist_description(self, tracks: List[Track], theme: str = "") -> str:
        """Generate description for a playlist"""
        pass


class OpenAIProvider(LLMProvider_ABC):
    """OpenAI GPT provider"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.base_url = "https://api.openai.com/v1/chat/completions"
        
    async def analyze_track(self, track: Track, context: str = "") -> MusicAnalysis:
        """Analyze track using OpenAI"""
        prompt = self._create_analysis_prompt(track, context)
        
        try:
            response = await self._make_request(prompt)
            return self._parse_analysis_response(track.id, response)
        except Exception as e:
            print(f"OpenAI analysis failed: {e}")
            return self._fallback_analysis(track.id)
    
    async def suggest_compatibility(self, track1: Track, track2: Track) -> float:
        """Get compatibility suggestion from OpenAI"""
        prompt = self._create_compatibility_prompt(track1, track2)
        
        try:
            response = await self._make_request(prompt)
            return self._parse_compatibility_response(response)
        except Exception as e:
            print(f"OpenAI compatibility failed: {e}")
            return 0.5  # Neutral score on error
    
    async def generate_playlist_description(self, tracks: List[Track], theme: str = "") -> str:
        """Generate playlist description"""
        prompt = self._create_playlist_prompt(tracks, theme)
        
        try:
            response = await self._make_request(prompt)
            return response.get('content', 'AI-generated playlist')
        except Exception as e:
            print(f"OpenAI playlist description failed: {e}")
            return f"Playlist with {len(tracks)} tracks"
    
    def _create_analysis_prompt(self, track: Track, context: str) -> str:
        """Create prompt for track analysis"""
        return f"""
        Analyze this music track for DJ mixing purposes:
        
        Track: "{track.title}" by {track.artist}
        Genre: {track.genre or 'Unknown'}
        Key: {track.key or 'Unknown'}
        BPM: {track.bpm or 'Unknown'}
        Energy: {track.energy or 'Unknown'}
        
        Context: {context}
        
        Provide analysis in JSON format:
        {{
            "mood": "description of overall mood",
            "energy_description": "detailed energy analysis",
            "genre_details": "specific subgenre and style notes",
            "mixing_suggestions": ["suggestion1", "suggestion2"],
            "compatibility_factors": {{
                "harmonic": 0.8,
                "rhythmic": 0.7,
                "energy": 0.9,
                "mood": 0.8
            }},
            "emotional_profile": {{
                "happiness": 0.7,
                "intensity": 0.8,
                "danceability": 0.9
            }},
            "confidence_score": 0.85
        }}
        
        Focus on practical DJ mixing advice and technical compatibility.
        """
    
    def _create_compatibility_prompt(self, track1: Track, track2: Track) -> str:
        """Create prompt for compatibility analysis"""
        return f"""
        Analyze the DJ mixing compatibility between these two tracks:
        
        Track 1: "{track1.title}" by {track1.artist}
        - Genre: {track1.genre}, Key: {track1.key}, BPM: {track1.bpm}
        
        Track 2: "{track2.title}" by {track2.artist}
        - Genre: {track2.genre}, Key: {track2.key}, BPM: {track2.bpm}
        
        Return a compatibility score from 0.0 to 1.0 considering:
        - Harmonic compatibility
        - BPM matching/transition potential
        - Genre and style compatibility
        - Energy flow
        - Emotional progression
        
        Respond with just a number between 0.0 and 1.0.
        """
    
    def _create_playlist_prompt(self, tracks: List[Track], theme: str) -> str:
        """Create prompt for playlist description"""
        track_list = "\\n".join([f"- {t.title} by {t.artist}" for t in tracks[:10]])
        
        return f"""
        Create a compelling description for this DJ playlist:
        
        Theme: {theme}
        Tracks ({len(tracks)} total):
        {track_list}
        {"..." if len(tracks) > 10 else ""}
        
        Write a 2-3 sentence description focusing on the musical journey,
        energy flow, and mixing potential. Make it engaging for DJs and music lovers.
        """
    
    async def _make_request(self, prompt: str) -> Dict[str, Any]:
        """Make API request to OpenAI"""
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.config.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature
        }
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(self.config.timeout)) as session:
            async with session.post(self.base_url, json=payload, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    return {"content": result["choices"][0]["message"]["content"]}
                else:
                    raise Exception(f"API request failed: {response.status}")
    
    def _parse_analysis_response(self, track_id: str, response: Dict) -> MusicAnalysis:
        """Parse analysis response from LLM"""
        try:
            content = response.get('content', '{}')
            data = json.loads(content)
            
            return MusicAnalysis(
                track_id=track_id,
                mood=data.get('mood', 'Unknown'),
                energy_description=data.get('energy_description', 'Unknown'),
                genre_details=data.get('genre_details', 'Unknown'),
                mixing_suggestions=data.get('mixing_suggestions', []),
                compatibility_factors=data.get('compatibility_factors', {}),
                emotional_profile=data.get('emotional_profile', {}),
                confidence_score=data.get('confidence_score', 0.5)
            )
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Failed to parse LLM response: {e}")
            return self._fallback_analysis(track_id)
    
    def _parse_compatibility_response(self, response: Dict) -> float:
        """Parse compatibility response"""
        try:
            content = response.get('content', '0.5')
            score = float(content.strip())
            return max(0.0, min(1.0, score))  # Clamp to 0-1 range
        except (ValueError, TypeError):
            return 0.5
    
    def _fallback_analysis(self, track_id: str) -> MusicAnalysis:
        """Fallback analysis when LLM fails"""
        return MusicAnalysis(
            track_id=track_id,
            mood="Unknown",
            energy_description="Unable to analyze",
            genre_details="Unable to analyze",
            mixing_suggestions=[],
            compatibility_factors={},
            emotional_profile={},
            confidence_score=0.0
        )


class AnthropicProvider(LLMProvider_ABC):
    """Anthropic Claude provider"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.base_url = "https://api.anthropic.com/v1/messages"
    
    async def analyze_track(self, track: Track, context: str = "") -> MusicAnalysis:
        """Analyze track using Claude"""
        # Similar implementation to OpenAI but with Anthropic API format
        # For now, delegate to fallback
        return self._fallback_analysis(track.id)
    
    async def suggest_compatibility(self, track1: Track, track2: Track) -> float:
        """Get compatibility from Claude"""
        return 0.5  # Placeholder
    
    async def generate_playlist_description(self, tracks: List[Track], theme: str = "") -> str:
        """Generate description with Claude"""
        return f"Claude-analyzed playlist with {len(tracks)} tracks"
    
    def _fallback_analysis(self, track_id: str) -> MusicAnalysis:
        """Fallback analysis"""
        return MusicAnalysis(
            track_id=track_id,
            mood="Unknown",
            energy_description="Claude analysis not implemented",
            genre_details="Claude analysis not implemented", 
            mixing_suggestions=[],
            compatibility_factors={},
            emotional_profile={},
            confidence_score=0.0
        )


class LLMCache:
    """Cache system for LLM responses"""
    
    def __init__(self, cache_dir: Optional[str] = None):
        if cache_dir is None:
            cache_dir = Path.home() / '.bluelibrary' / 'llm_cache'
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_key(self, prompt: str, config: LLMConfig) -> str:
        """Generate cache key from prompt and config"""
        content = f"{prompt}:{config.provider.value}:{config.model}:{config.temperature}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get_cached_response(self, prompt: str, config: LLMConfig) -> Optional[Dict]:
        """Get cached response if available"""
        try:
            cache_key = self._get_cache_key(prompt, config)
            cache_file = self.cache_dir / f"{cache_key}.json"
            
            if cache_file.exists():
                with open(cache_file, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        return None
    
    def cache_response(self, prompt: str, config: LLMConfig, response: Dict):
        """Cache LLM response"""
        try:
            cache_key = self._get_cache_key(prompt, config)
            cache_file = self.cache_dir / f"{cache_key}.json"
            
            with open(cache_file, 'w') as f:
                json.dump(response, f)
        except Exception as e:
            print(f"Failed to cache LLM response: {e}")


class LLMIntegration:
    """Main LLM integration manager"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.cache = LLMCache() if config.cache_enabled else None
        self.provider = self._create_provider()
    
    def _create_provider(self) -> LLMProvider_ABC:
        """Create appropriate LLM provider"""
        if self.config.provider == LLMProvider.OPENAI:
            return OpenAIProvider(self.config)
        elif self.config.provider == LLMProvider.ANTHROPIC:
            return AnthropicProvider(self.config)
        else:
            raise ValueError(f"Unsupported provider: {self.config.provider}")
    
    async def analyze_track(self, track: Track, context: str = "") -> MusicAnalysis:
        """Analyze track with caching"""
        if self.cache:
            prompt = f"analyze_track:{track.title}:{track.artist}:{context}"
            cached = self.cache.get_cached_response(prompt, self.config)
            if cached:
                return MusicAnalysis(**cached)
        
        analysis = await self.provider.analyze_track(track, context)
        
        if self.cache:
            self.cache.cache_response(prompt, self.config, asdict(analysis))
        
        return analysis
    
    async def suggest_compatibility(self, track1: Track, track2: Track) -> float:
        """Get compatibility score with caching"""
        if self.cache:
            prompt = f"compatibility:{track1.id}:{track2.id}"
            cached = self.cache.get_cached_response(prompt, self.config)
            if cached:
                return cached.get('score', 0.5)
        
        score = await self.provider.suggest_compatibility(track1, track2)
        
        if self.cache:
            self.cache.cache_response(prompt, self.config, {'score': score})
        
        return score
    
    async def batch_analyze_tracks(self, tracks: List[Track], context: str = "") -> List[MusicAnalysis]:
        """Analyze multiple tracks concurrently"""
        tasks = [self.analyze_track(track, context) for track in tracks]
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    def update_config(self, new_config: LLMConfig):
        """Update LLM configuration"""
        self.config = new_config
        self.provider = self._create_provider()