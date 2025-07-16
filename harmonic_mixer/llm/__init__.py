"""
LLM Integration package for BlueLibrary
"""

from .llm_integration import (
    LLMProvider,
    LLMConfig,
    MusicAnalysis,
    LLMIntegration,
    OpenAIProvider,
    AnthropicProvider
)

__all__ = [
    'LLMProvider',
    'LLMConfig', 
    'MusicAnalysis',
    'LLMIntegration',
    'OpenAIProvider',
    'AnthropicProvider'
]