"""
LLM Configuration Manager
Handles LLM settings, API keys, and plugin configuration
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict

from .llm_integration import LLMProvider, LLMConfig
from ..data.secure_database import SecureSettingsDatabase


@dataclass
class LLMSettings:
    """Complete LLM settings configuration"""
    enabled: bool = False
    provider: str = "openai"  # Store as string for JSON serialization
    api_key: str = ""
    model: str = "gpt-3.5-turbo"
    max_tokens: int = 500
    temperature: float = 0.1
    cache_enabled: bool = True
    mixing_weight: float = 0.3
    use_emotional_analysis: bool = True
    use_genre_intelligence: bool = True
    fallback_to_traditional: bool = True


class LLMConfigManager:
    """Manages LLM configuration and settings"""
    
    def __init__(self, db: SecureSettingsDatabase):
        self.db = db
        self._settings: Optional[LLMSettings] = None
    
    def get_settings(self) -> LLMSettings:
        """Get current LLM settings"""
        if self._settings is None:
            self._load_settings()
        return self._settings
    
    def update_settings(self, settings: LLMSettings) -> bool:
        """Update LLM settings"""
        try:
            self._settings = settings
            self._save_settings()
            return True
        except Exception as e:
            print(f"Failed to update LLM settings: {e}")
            return False
    
    def get_llm_config(self) -> Optional[LLMConfig]:
        """Convert settings to LLMConfig object"""
        settings = self.get_settings()
        
        if not settings.enabled or not settings.api_key:
            return None
        
        try:
            provider = LLMProvider(settings.provider)
            return LLMConfig(
                provider=provider,
                api_key=settings.api_key,
                model=settings.model,
                max_tokens=settings.max_tokens,
                temperature=settings.temperature,
                cache_enabled=settings.cache_enabled
            )
        except ValueError as e:
            print(f"Invalid LLM provider: {settings.provider}")
            return None
    
    def is_configured(self) -> bool:
        """Check if LLM is properly configured"""
        settings = self.get_settings()
        
        if not settings.enabled:
            print("🔍 LLM Config: Disabled in settings")
            return False
            
        if not settings.api_key:
            print("🔍 LLM Config: No API key provided")
            return False
            
        if not self.validate_api_key(settings.provider, settings.api_key):
            print(f"🔍 LLM Config: Invalid API key format for {settings.provider}")
            return False
            
        print(f"🔍 LLM Config: ✅ Valid configuration for {settings.provider}")
        return True
    
    def get_configuration_status(self) -> Dict[str, Any]:
        """Get detailed configuration status for diagnostics"""
        settings = self.get_settings()
        
        status = {
            "configured": False,
            "enabled": settings.enabled,
            "provider": settings.provider,
            "has_api_key": bool(settings.api_key),
            "api_key_valid": False,
            "config_stored_in_db": bool(self.db),
            "issues": []
        }
        
        if not settings.enabled:
            status["issues"].append("LLM integration is disabled")
        
        if not settings.api_key:
            status["issues"].append("No API key provided")
        else:
            status["api_key_valid"] = self.validate_api_key(settings.provider, settings.api_key)
            if not status["api_key_valid"]:
                status["issues"].append(f"Invalid API key format for {settings.provider}")
        
        if not settings.provider:
            status["issues"].append("No provider selected")
        
        status["configured"] = len(status["issues"]) == 0
        
        return status
    
    def test_configuration(self) -> bool:
        """Test if LLM configuration is working"""
        config = self.get_llm_config()
        if not config:
            return False
        
        try:
            # Test API call based on provider
            provider = config.get('provider', '').lower()
            api_key = config.get('api_key', '')
            
            if not api_key:
                return False
                
            if provider == 'openai':
                return self._test_openai_api(config)
            elif provider == 'anthropic':
                return self._test_anthropic_api(config)
            elif provider == 'google':
                return self._test_google_api(config)
            else:
                # Unknown provider, assume valid for now
                return True
                
        except Exception as e:
            print(f"LLM API test failed: {e}")
            return False
    
    def _test_openai_api(self, config: Dict[str, Any]) -> bool:
        """Test OpenAI API connection"""
        try:
            import openai
            
            client = openai.OpenAI(
                api_key=config.get('api_key'),
                base_url=config.get('base_url')
            )
            
            # Simple test request
            response = client.chat.completions.create(
                model=config.get('model', 'gpt-3.5-turbo'),
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=1,
                timeout=10
            )
            
            return bool(response.choices)
            
        except ImportError:
            # OpenAI library not available
            return False
        except Exception as e:
            print(f"OpenAI API test failed: {e}")
            return False
    
    def _test_anthropic_api(self, config: Dict[str, Any]) -> bool:
        """Test Anthropic API connection"""
        try:
            import anthropic
            
            client = anthropic.Anthropic(
                api_key=config.get('api_key'),
                base_url=config.get('base_url')
            )
            
            # Simple test request
            response = client.messages.create(
                model=config.get('model', 'claude-3-sonnet-20240229'),
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=1,
                timeout=10
            )
            
            return bool(response.content)
            
        except ImportError:
            # Anthropic library not available
            return False
        except Exception as e:
            print(f"Anthropic API test failed: {e}")
            return False
    
    def _test_google_api(self, config: Dict[str, Any]) -> bool:
        """Test Google API connection"""
        try:
            import google.generativeai as genai
            
            genai.configure(api_key=config.get('api_key'))
            
            model = genai.GenerativeModel(config.get('model', 'gemini-pro'))
            response = model.generate_content(
                "Test",
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=1,
                    timeout=10
                )
            )
            
            return bool(response.text)
            
        except ImportError:
            # Google library not available
            return False
        except Exception as e:
            print(f"Google API test failed: {e}")
            return False
    
    def get_available_providers(self) -> Dict[str, Dict[str, Any]]:
        """Get list of available LLM providers"""
        return {
            "openai": {
                "name": "OpenAI GPT",
                "models": ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo-preview"],
                "requires_api_key": True,
                "description": "OpenAI's GPT models for music analysis"
            },
            "anthropic": {
                "name": "Anthropic Claude",
                "models": ["claude-3-haiku", "claude-3-sonnet", "claude-3-opus"],
                "requires_api_key": True,
                "description": "Anthropic's Claude models for music analysis"
            },
            "groq": {
                "name": "Groq",
                "models": ["mixtral-8x7b-32768", "llama2-70b-4096"],
                "requires_api_key": True,
                "description": "Fast inference with Groq"
            }
        }
    
    def get_model_suggestions(self, provider: str) -> List[str]:
        """Get model suggestions for a provider"""
        providers = self.get_available_providers()
        if provider in providers:
            return providers[provider]["models"]
        return []
    
    def _load_settings(self):
        """Load settings from database"""
        try:
            settings_data = self.db.get_setting('llm_settings', {})
            if settings_data:
                # Convert dict back to LLMSettings
                self._settings = LLMSettings(**settings_data)
            else:
                self._settings = LLMSettings()  # Default settings
        except Exception as e:
            print(f"Failed to load LLM settings: {e}")
            self._settings = LLMSettings()  # Fallback to defaults
    
    def _save_settings(self):
        """Save settings to database"""
        try:
            settings_data = asdict(self._settings)
            self.db.set_setting('llm_settings', settings_data)
        except Exception as e:
            print(f"Failed to save LLM settings: {e}")
    
    def reset_to_defaults(self):
        """Reset settings to defaults"""
        self._settings = LLMSettings()
        self._save_settings()
    
    def export_settings(self) -> str:
        """Export settings as JSON (without API key)"""
        settings = self.get_settings()
        export_data = asdict(settings)
        export_data['api_key'] = ""  # Don't export API key
        return json.dumps(export_data, indent=2)
    
    def import_settings(self, json_data: str) -> bool:
        """Import settings from JSON"""
        try:
            data = json.loads(json_data)
            # Keep existing API key if not provided
            current_api_key = self.get_settings().api_key
            if 'api_key' not in data or not data['api_key']:
                data['api_key'] = current_api_key
            
            settings = LLMSettings(**data)
            return self.update_settings(settings)
        except Exception as e:
            print(f"Failed to import LLM settings: {e}")
            return False
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get LLM usage statistics"""
        try:
            # Try to load existing usage stats
            stats_file = self.config_dir / "usage_stats.json"
            if stats_file.exists():
                with open(stats_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading usage stats: {e}")
        
        # Default empty stats
        return {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "average_response_time": 0.0,
            "estimated_cost": 0.0,
            "last_request": None,
            "tokens_used": 0,
            "requests_by_day": {}
        }
    
    def track_api_usage(self, provider: str, model: str, input_tokens: int, 
                       output_tokens: int, response_time: float):
        """Track API usage for cost and performance monitoring"""
        try:
            stats = self.get_usage_stats()
            
            # Update basic stats
            stats["total_requests"] += 1
            stats["tokens_used"] += input_tokens + output_tokens
            stats["last_request"] = datetime.now().isoformat()
            
            # Update average response time
            current_avg = stats.get("average_response_time", 0.0)
            total_requests = stats["total_requests"]
            stats["average_response_time"] = (
                (current_avg * (total_requests - 1) + response_time) / total_requests
            )
            
            # Track requests by day
            today = datetime.now().strftime("%Y-%m-%d")
            if today not in stats["requests_by_day"]:
                stats["requests_by_day"][today] = 0
            stats["requests_by_day"][today] += 1
            
            # Estimate cost (rough approximation)
            cost_per_token = self._get_cost_per_token(provider, model)
            request_cost = (input_tokens + output_tokens) * cost_per_token
            stats["estimated_cost"] += request_cost
            
            # Save updated stats
            self._save_usage_stats(stats)
            
        except Exception as e:
            print(f"Error tracking API usage: {e}")
    
    def track_cache_hit(self):
        """Track cache hit for performance monitoring"""
        try:
            stats = self.get_usage_stats()
            stats["cache_hits"] += 1
            self._save_usage_stats(stats)
        except Exception as e:
            print(f"Error tracking cache hit: {e}")
    
    def track_cache_miss(self):
        """Track cache miss for performance monitoring"""
        try:
            stats = self.get_usage_stats()
            stats["cache_misses"] += 1
            self._save_usage_stats(stats)
        except Exception as e:
            print(f"Error tracking cache miss: {e}")
    
    def _get_cost_per_token(self, provider: str, model: str) -> float:
        """Get approximate cost per token for provider/model"""
        # Rough cost estimates (as of 2024)
        cost_map = {
            "openai": {
                "gpt-3.5-turbo": 0.000002,  # $0.002/1K tokens
                "gpt-4": 0.00003,           # $0.03/1K tokens
                "gpt-4-turbo": 0.00001,     # $0.01/1K tokens
            },
            "anthropic": {
                "claude-3-sonnet": 0.000003,    # $0.003/1K tokens
                "claude-3-haiku": 0.000001,     # $0.001/1K tokens
                "claude-3-opus": 0.000015,      # $0.015/1K tokens
            },
            "google": {
                "gemini-pro": 0.000001,     # $0.001/1K tokens
                "gemini-ultra": 0.000005,   # $0.005/1K tokens
            }
        }
        
        return cost_map.get(provider, {}).get(model, 0.000001)  # Default fallback
    
    def _save_usage_stats(self, stats: Dict[str, Any]):
        """Save usage statistics to file"""
        try:
            stats_file = self.config_dir / "usage_stats.json"
            with open(stats_file, 'w') as f:
                json.dump(stats, f, indent=2)
        except Exception as e:
            print(f"Error saving usage stats: {e}")
    
    def reset_usage_stats(self):
        """Reset usage statistics"""
        try:
            stats_file = self.config_dir / "usage_stats.json"
            if stats_file.exists():
                stats_file.unlink()
        except Exception as e:
            print(f"Error resetting usage stats: {e}")
    
    def create_default_config(self):
        """Create a default configuration file for testing"""
        try:
            default_settings = LLMSettings(
                enabled=False,  # Disabled by default
                provider="openai",
                api_key="",  # Empty - user needs to fill
                model="gpt-3.5-turbo",
                base_url=None,
                temperature=0.7,
                max_tokens=1000,
                cache_enabled=True
            )
            
            self.save_settings(default_settings)
            print(f"✅ Created default LLM configuration in database")
            print("💡 Edit the configuration file to add your API key and enable LLM features")
            
            return True
        except Exception as e:
            print(f"❌ Failed to create default config: {e}")
            return False
    
    def validate_api_key(self, provider: str, api_key: str) -> bool:
        """Validate an API key format"""
        if not api_key:
            return False
        
        # Basic validation based on provider
        if provider == "openai":
            return api_key.startswith("sk-") and len(api_key) > 20
        elif provider == "anthropic":
            return api_key.startswith("sk-ant-") and len(api_key) > 20
        elif provider == "groq":
            return len(api_key) > 20
        
        return True  # Allow other providers
    
    def get_cost_estimate(self, num_tracks: int) -> Dict[str, Any]:
        """Estimate cost for analyzing tracks"""
        settings = self.get_settings()
        
        # Rough cost estimates (tokens per track analysis)
        tokens_per_track = 800  # Input + output tokens
        
        cost_per_1k_tokens = {
            "gpt-3.5-turbo": 0.002,
            "gpt-4": 0.06,
            "claude-3-haiku": 0.0015,
            "claude-3-sonnet": 0.018
        }
        
        model = settings.model
        cost_rate = cost_per_1k_tokens.get(model, 0.002)
        
        total_tokens = num_tracks * tokens_per_track
        estimated_cost = (total_tokens / 1000) * cost_rate
        
        return {
            "num_tracks": num_tracks,
            "tokens_per_track": tokens_per_track,
            "total_tokens": total_tokens,
            "cost_per_1k_tokens": cost_rate,
            "estimated_cost_usd": round(estimated_cost, 4),
            "model": model
        }