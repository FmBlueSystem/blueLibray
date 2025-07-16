"""
LLM-powered Metadata Enhancement System
Automatically enriches track metadata using AI analysis
"""

import asyncio
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from ..core.harmonic_engine import Track
from .llm_integration import LLMIntegration, LLMConfig, MusicAnalysis


@dataclass
class EnhancedMetadata:
    """Enhanced metadata from LLM analysis"""
    track_id: str
    # Original metadata
    original_genre: Optional[str] = None
    original_mood: Optional[str] = None
    
    # Genre validation results
    is_genre_correct: Optional[bool] = None
    corrected_genre: Optional[str] = None
    genre_correction_reason: Optional[str] = None
    
    # Enhanced metadata
    subgenre: Optional[str] = None
    mood: Optional[str] = None
    era: Optional[str] = None
    language: Optional[str] = None
    instruments: List[str] = None
    vocal_style: Optional[str] = None
    tempo_description: Optional[str] = None
    danceability: Optional[float] = None
    
    # Contextual information
    time_of_day: Optional[str] = None  # morning, afternoon, evening, night
    activity: Optional[str] = None  # workout, party, chill, focus
    season: Optional[str] = None  # spring, summer, fall, winter
    
    # DJ-specific metadata
    intro_length: Optional[float] = None
    outro_length: Optional[float] = None
    breakdown_sections: List[Dict[str, float]] = None
    build_up_sections: List[Dict[str, float]] = None
    best_mix_points: List[float] = None
    
    # Quality scores
    production_quality: Optional[float] = None
    mixing_friendliness: Optional[float] = None
    crowd_appeal: Optional[float] = None
    
    confidence_score: float = 0.0


class MetadataEnhancer:
    """Enhances track metadata using LLM analysis"""
    
    def __init__(self, llm_integration: LLMIntegration, database=None):
        self.llm_integration = llm_integration
        self.enhancement_cache: Dict[str, EnhancedMetadata] = {}
        self.database = database
        
        # Load existing enhanced metadata from database if available
        if self.database:
            try:
                self.enhancement_cache = self.database.load_all_enhanced_metadata()
                if len(self.enhancement_cache) > 0:
                    print(f"Loaded {len(self.enhancement_cache)} enhanced metadata entries from database")
            except Exception as e:
                print(f"Error loading enhanced metadata from database: {e}")
                self.enhancement_cache = {}
    
    async def enhance_track(self, track: Track) -> EnhancedMetadata:
        """Enhance a single track's metadata"""
        if track.id in self.enhancement_cache:
            return self.enhancement_cache[track.id]
        
        try:
            # Get analysis from LLM using public method
            context = "Enhance metadata with detailed music analysis including mood, danceability, and energy"
            analysis = await self.llm_integration.analyze_track(track, context)
            enhanced_metadata = self._create_enhanced_metadata_from_analysis(track.id, analysis)
            
            # Cache the result
            self.enhancement_cache[track.id] = enhanced_metadata
            
            # Save to database if available
            if self.database:
                try:
                    self.database.save_enhanced_metadata(enhanced_metadata)
                except Exception as e:
                    print(f"Error saving enhanced metadata to database: {e}")
            
            return enhanced_metadata
            
        except Exception as e:
            print(f"Failed to enhance metadata for {track.title}: {e}")
            return self._create_fallback_metadata(track.id)
    
    async def enhance_tracks_batch(self, tracks: List[Track]) -> Dict[str, EnhancedMetadata]:
        """Enhance multiple tracks in batch"""
        tasks = [self.enhance_track(track) for track in tracks]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        enhanced_metadata = {}
        for track, result in zip(tracks, results):
            if isinstance(result, EnhancedMetadata):
                enhanced_metadata[track.id] = result
            else:
                print(f"Failed to enhance {track.title}: {result}")
                enhanced_metadata[track.id] = self._create_fallback_metadata(track.id)
        
        return enhanced_metadata
    
    def _create_enhancement_prompt(self, track: Track) -> str:
        """Create LLM prompt for metadata enhancement"""
        return f"""
        Analyze this music track and provide enhanced metadata for DJ mixing:
        
        Track: "{track.title}" by {track.artist}
        Existing Genre: {track.genre or 'Unknown'}
        Key: {track.key or 'Unknown'}
        BPM: {track.bpm or 'Unknown'}
        Energy Level: {track.energy or 'Unknown'}
        
        IMPORTANT: First validate if the existing genre is correct based on the track title and artist.
        If the genre is wrong or could be more accurate, provide a corrected version.
        
        Provide detailed analysis in JSON format:
        {{
            "genre_validation": {{
                "is_original_correct": true,
                "original_genre": "{track.genre or 'Unknown'}",
                "corrected_genre": "correct genre if different, or same if correct",
                "correction_reason": "explanation if genre was corrected"
            }},
            "subgenre": "specific subgenre (e.g., 'Deep House', 'Latin Trap')",
            "mood": "overall mood (e.g., 'uplifting', 'melancholic', 'energetic')",
            "era": "time period (e.g., '2020s', '90s', 'classic')",
            "language": "primary language of vocals or 'instrumental'",
            "instruments": ["list", "of", "prominent", "instruments"],
            "vocal_style": "type of vocals (e.g., 'male lead', 'female harmonies', 'rap')",
            "tempo_description": "tempo feel (e.g., 'mid-tempo', 'driving', 'laid-back')",
            "danceability": 0.85,
            
            "time_of_day": "best time to play (morning/afternoon/evening/night)",
            "activity": "best activity context (workout/party/chill/focus)",
            "season": "seasonal feel (spring/summer/fall/winter)",
            
            "intro_length": 8.0,
            "outro_length": 16.0,
            "breakdown_sections": [{{"start": 60.0, "end": 80.0}}],
            "build_up_sections": [{{"start": 40.0, "end": 60.0}}],
            "best_mix_points": [32.0, 96.0, 160.0],
            
            "production_quality": 0.9,
            "mixing_friendliness": 0.8,
            "crowd_appeal": 0.85,
            
            "confidence_score": 0.9
        }}
        
        Focus on practical DJ information. Use your knowledge of music to infer details
        that would help a DJ choose appropriate tracks for different contexts.
        
        Genre Validation Guidelines:
        - Common mistakes: "Pop" for specific dance genres, "Rock" for Metal/Punk variants
        - Be specific: "House" → "Deep House", "Electronic" → "Techno/Trance/etc"
        - Consider artist context: Known for specific genres
        - Use recognized DJ/music industry categories
        """
    
    def _parse_enhancement_response(self, track_id: str, response: Dict) -> EnhancedMetadata:
        """Parse LLM response into enhanced metadata"""
        try:
            content = response.get('content', '{}')
            data = json.loads(content)
            
            # Parse genre validation
            genre_validation = data.get('genre_validation', {})
            
            return EnhancedMetadata(
                track_id=track_id,
                # Genre validation
                original_genre=genre_validation.get('original_genre'),
                is_genre_correct=genre_validation.get('is_original_correct'),
                corrected_genre=genre_validation.get('corrected_genre'),
                genre_correction_reason=genre_validation.get('correction_reason'),
                
                # Enhanced metadata
                subgenre=data.get('subgenre'),
                mood=data.get('mood'),
                era=data.get('era'),
                language=data.get('language'),
                instruments=data.get('instruments', []),
                vocal_style=data.get('vocal_style'),
                tempo_description=data.get('tempo_description'),
                danceability=data.get('danceability'),
                
                time_of_day=data.get('time_of_day'),
                activity=data.get('activity'),
                season=data.get('season'),
                
                intro_length=data.get('intro_length'),
                outro_length=data.get('outro_length'),
                breakdown_sections=data.get('breakdown_sections', []),
                build_up_sections=data.get('build_up_sections', []),
                best_mix_points=data.get('best_mix_points', []),
                
                production_quality=data.get('production_quality'),
                mixing_friendliness=data.get('mixing_friendliness'),
                crowd_appeal=data.get('crowd_appeal'),
                
                confidence_score=data.get('confidence_score', 0.5)
            )
            
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Failed to parse enhancement response: {e}")
            return self._create_fallback_metadata(track_id)
    
    def _create_enhanced_metadata_from_analysis(self, track_id: str, analysis) -> EnhancedMetadata:
        """Create enhanced metadata from MusicAnalysis"""
        try:
            # Extract data from MusicAnalysis object
            return EnhancedMetadata(
                track_id=track_id,
                # Basic metadata
                subgenre=getattr(analysis, 'subgenre', None),
                mood=getattr(analysis, 'mood', None),
                era=getattr(analysis, 'era', None),
                
                # Musical characteristics
                danceability=getattr(analysis, 'danceability', None),
                valence=getattr(analysis, 'valence', None),
                arousal=getattr(analysis, 'arousal', None),
                
                # Mix characteristics
                intro_length=getattr(analysis, 'intro_length', None),
                outro_length=getattr(analysis, 'outro_length', None),
                drop_sections=getattr(analysis, 'drop_sections', []),
                build_up_sections=getattr(analysis, 'build_up_sections', []),
                best_mix_points=getattr(analysis, 'best_mix_points', []),
                
                # Quality metrics
                production_quality=getattr(analysis, 'production_quality', None),
                mixing_friendliness=getattr(analysis, 'mixing_friendliness', None),
                crowd_appeal=getattr(analysis, 'crowd_appeal', None),
                
                confidence_score=getattr(analysis, 'confidence_score', 0.7)
            )
            
        except Exception as e:
            print(f"Error creating enhanced metadata from analysis: {e}")
            return self._create_fallback_metadata(track_id)
    
    def _create_fallback_metadata(self, track_id: str) -> EnhancedMetadata:
        """Create fallback metadata when LLM fails"""
        return EnhancedMetadata(
            track_id=track_id,
            confidence_score=0.0
        )
    
    def get_enhanced_metadata(self, track_id: str) -> Optional[EnhancedMetadata]:
        """Get cached enhanced metadata for a track"""
        return self.enhancement_cache.get(track_id)
    
    def clear_cache(self):
        """Clear the enhancement cache"""
        self.enhancement_cache.clear()
    
    def export_enhancements(self, track_ids: List[str] = None) -> Dict[str, Any]:
        """Export enhanced metadata to dict"""
        if track_ids is None:
            track_ids = list(self.enhancement_cache.keys())
        
        exported = {}
        for track_id in track_ids:
            if track_id in self.enhancement_cache:
                exported[track_id] = asdict(self.enhancement_cache[track_id])
        
        return exported
    
    def import_enhancements(self, data: Dict[str, Any]) -> bool:
        """Import enhanced metadata from dict"""
        try:
            for track_id, metadata_dict in data.items():
                metadata = EnhancedMetadata(**metadata_dict)
                self.enhancement_cache[track_id] = metadata
            return True
        except Exception as e:
            print(f"Failed to import enhancements: {e}")
            return False


class MetadataFilter:
    """Filter and search tracks based on enhanced metadata"""
    
    def __init__(self, enhancer: MetadataEnhancer):
        self.enhancer = enhancer
    
    def filter_by_mood(self, track_ids: List[str], mood: str) -> List[str]:
        """Filter tracks by mood"""
        filtered = []
        for track_id in track_ids:
            metadata = self.enhancer.get_enhanced_metadata(track_id)
            if metadata and metadata.mood and mood.lower() in metadata.mood.lower():
                filtered.append(track_id)
        return filtered
    
    def filter_by_activity(self, track_ids: List[str], activity: str) -> List[str]:
        """Filter tracks by activity context"""
        filtered = []
        for track_id in track_ids:
            metadata = self.enhancer.get_enhanced_metadata(track_id)
            if metadata and metadata.activity and activity.lower() in metadata.activity.lower():
                filtered.append(track_id)
        return filtered
    
    def filter_by_time_of_day(self, track_ids: List[str], time_of_day: str) -> List[str]:
        """Filter tracks by time of day"""
        filtered = []
        for track_id in track_ids:
            metadata = self.enhancer.get_enhanced_metadata(track_id)
            if metadata and metadata.time_of_day and time_of_day.lower() in metadata.time_of_day.lower():
                filtered.append(track_id)
        return filtered
    
    def filter_by_danceability(self, track_ids: List[str], min_danceability: float) -> List[str]:
        """Filter tracks by minimum danceability score"""
        filtered = []
        for track_id in track_ids:
            metadata = self.enhancer.get_enhanced_metadata(track_id)
            if metadata and metadata.danceability and metadata.danceability >= min_danceability:
                filtered.append(track_id)
        return filtered
    
    def filter_by_era(self, track_ids: List[str], era: str) -> List[str]:
        """Filter tracks by musical era"""
        filtered = []
        for track_id in track_ids:
            metadata = self.enhancer.get_enhanced_metadata(track_id)
            if metadata and metadata.era and era.lower() in metadata.era.lower():
                filtered.append(track_id)
        return filtered
    
    def search_by_instruments(self, track_ids: List[str], instrument: str) -> List[str]:
        """Search tracks that feature specific instruments"""
        filtered = []
        for track_id in track_ids:
            metadata = self.enhancer.get_enhanced_metadata(track_id)
            if metadata and metadata.instruments:
                for track_instrument in metadata.instruments:
                    if instrument.lower() in track_instrument.lower():
                        filtered.append(track_id)
                        break
        return filtered
    
    def get_mixing_friendly_tracks(self, track_ids: List[str], min_score: float = 0.7) -> List[str]:
        """Get tracks that are mixing-friendly"""
        filtered = []
        for track_id in track_ids:
            metadata = self.enhancer.get_enhanced_metadata(track_id)
            if metadata and metadata.mixing_friendliness and metadata.mixing_friendliness >= min_score:
                filtered.append(track_id)
        return filtered
    
    def get_crowd_pleasers(self, track_ids: List[str], min_appeal: float = 0.8) -> List[str]:
        """Get tracks with high crowd appeal"""
        filtered = []
        for track_id in track_ids:
            metadata = self.enhancer.get_enhanced_metadata(track_id)
            if metadata and metadata.crowd_appeal and metadata.crowd_appeal >= min_appeal:
                filtered.append(track_id)
        return filtered