# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BlueLibrary is an advanced DJ harmonic mixing application built with PyQt6 that implements sophisticated algorithms for music track compatibility analysis. The application goes beyond traditional Camelot wheel mixing by incorporating multiple factors: harmonic key relationships, BPM matching, energy levels, and emotional intensity for superior track transitions.

## Architecture

### Core Design Patterns

The application follows a **Layered Architecture** with **Facade Pattern** at its center:

1. **Application Facade** (`harmonic_mixer/core/application_facade.py`)
   - `BlueLibraryFacade` is the primary interface for all business operations
   - Centralizes state management, event coordination, and plugin integration
   - UI components should interact primarily through the facade, not directly with core components

2. **Event-Driven Architecture** (`harmonic_mixer/core/event_system.py`)
   - Global `event_manager` handles all inter-component communication
   - Components publish events (track analysis, playlist generation, etc.)
   - Loose coupling via observer pattern with both sync and async handlers

3. **Plugin System** (`harmonic_mixer/core/plugin_system.py`)
   - Extensible architecture supporting mixing algorithms, export formats, and audio analyzers
   - Built-in plugins include ML-based mixing and M3U export
   - Plugins register with global `plugin_manager`

4. **Async Processing** (`harmonic_mixer/utils/async_analyzer.py`)
   - Non-blocking audio analysis with configurable worker pools
   - File-based caching with hash-based invalidation
   - Memory-efficient batch processing for large music collections

### Key Components

- **Harmonic Engine** (`harmonic_engine.py`): Core algorithm implementing multi-factor compatibility scoring
- **Security Layer** (`secure_database.py`): Encrypted settings storage with file validation
- **UI Layer** (`ui/main_window.py`): PyQt6 interface using facade pattern for business logic

## Development Commands

### Running the Application
```bash
python main.py
```

### Testing
```bash
# Run core algorithm tests
python test_engine.py

# Run enhanced architecture tests (includes async, events, plugins)
python test_enhanced.py

# Run with pytest (if pytest is installed)
pytest test_*.py
```

### Dependencies
```bash
# Install core requirements
pip install -r requirements.txt

# For full audio analysis (optional but recommended)
pip install librosa mutagen soundfile audioread

# For security features (recommended)
pip install cryptography
```

## Key Development Patterns

### Adding New Features

1. **Business Logic**: Implement in facade (`BlueLibraryFacade`)
2. **UI Updates**: Subscribe to events, don't directly call business logic
3. **State Management**: Use `ApplicationState` within facade
4. **Async Operations**: Use `AsyncAudioAnalyzer` for I/O-heavy tasks

### Event System Usage

Components communicate via events:
```python
# Publishing events
event_manager.track_analyzed(track)
event_manager.analysis_progress(current, total)

# Subscribing to events
event_manager.event_bus.subscribe(
    EventType.TRACK_ANALYZED,
    lambda event: update_ui(event.data)
)
```

### Plugin Development

New mixing algorithms extend `MixingAlgorithmPlugin`:
```python
class CustomAlgorithm(MixingAlgorithmPlugin):
    def calculate_compatibility(self, track1: Track, track2: Track) -> float:
        # Implementation
        return score

# Register with plugin manager
plugin_manager.register_plugin(CustomAlgorithm())
```

### Security Considerations

- All file paths are validated through `SecurityValidator`
- Sensitive settings are encrypted via `SecureSettingsDatabase`
- Input validation is performed at facade boundaries

## Algorithm Architecture

The harmonic mixing engine uses a **Strategy Pattern** with multiple mixing modes:

- **Intelligent Mode**: Balanced multi-factor approach (default weights: key 40%, BPM 30%, energy 20%, emotional 10%)
- **Classic Camelot**: Traditional harmonic mixing (key 90%, BPM 10%)
- **Energy Flow**: Focus on energy progression (energy 50%)
- **Emotional**: Prioritize emotional continuity (emotional 50%)

Weight calculations are in `harmonic_engine.py` methods:
- `_calculate_key_score()`: Camelot wheel compatibility
- `_calculate_bpm_score()`: Tempo matching with tolerance
- `_calculate_energy_score()`: Energy level transitions
- `_calculate_emotional_score()`: Emotional flow continuity

## Data Flow

1. **Audio Analysis**: `AsyncAudioAnalyzer` → Cache → Event publication
2. **Track Selection**: UI → Facade → State management → Event publication
3. **Playlist Generation**: Facade → `HarmonicMixingEngine` → Algorithm execution
4. **UI Updates**: Event subscription → Reactive UI updates

## Testing Strategy

- `test_engine.py`: Core algorithm validation (compatibility scoring, playlist generation)
- `test_enhanced.py`: Architecture validation (facade, events, plugins, async processing, security)
- Both test files are designed to run independently and validate different aspects of the system

## Performance Considerations

- Audio analysis uses async processing with configurable worker pools
- Results are cached based on file modification time and content hash
- Large collections use batch processing with memory management
- UI remains responsive through event-driven updates and async operations