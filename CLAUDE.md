# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BlueLibrary is an advanced DJ harmonic mixing application built with PyQt6 that implements sophisticated algorithms for music track compatibility analysis beyond traditional Camelot wheel mixing.

## Commands

```bash
# Setup
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run application
python main.py

# Test suite (OBLIGATORIO antes de entregar cambios)
python test_engine.py || exit 1
python test_enhanced.py || exit 1
pytest -q || exit 1

# Optional
ruff check . || true
```

## Architecture

### Core Components

1. **Application Facade** (`harmonic_mixer/core/application_facade.py`)
   - `BlueLibraryFacade`: Central interface for all operations
   - UI must interact through facade, not directly with core

2. **Event System** (`harmonic_mixer/core/event_system.py`)
   - Global `event_manager` for inter-component communication
   - Loose coupling via observer pattern

3. **Plugin System** (`harmonic_mixer/core/plugin_system.py`)
   - Extensible for mixing algorithms, exports, analyzers
   - Register with `plugin_manager`

4. **Async Processing** (`harmonic_mixer/utils/async_analyzer.py`)
   - Non-blocking analysis with worker pools
   - File caching with hash validation

### Key Files
- `harmonic_engine.py`: Multi-factor compatibility scoring
- `secure_database.py`: Encrypted settings storage
- `ui/main_window.py`: PyQt6 interface using facade

## Flujo de Trabajo Obligatorio

**Claude: Validar SIEMPRE antes de entregar respuesta final**

1. **Analizar solicitud** (plan interno)
2. **Ejecutar pruebas actuales** (comandos arriba)
3. **Aplicar cambios mínimos** (~400 líneas máx/iteración)
4. **Re-ejecutar TODAS las pruebas**
5. **Si falla**: diagnosticar, reparar (máx 3 ciclos)
6. **Responder**: resumen cambios + estado tests ✅/❌

**Trigger "¿100% seguro?"**: Re-ejecutar TODO el flujo

## Development Patterns

### Events
```python
# Publish
event_manager.track_analyzed(track)

# Subscribe
event_manager.event_bus.subscribe(EventType.TRACK_ANALYZED, handler)
```

### Plugins
```python
class CustomAlgorithm(MixingAlgorithmPlugin):
    def calculate_compatibility(self, track1, track2):
        return score

plugin_manager.register_plugin(CustomAlgorithm())
```

### Adding Features
1. Logic → `BlueLibraryFacade`
2. UI → Subscribe to events
3. State → Use `ApplicationState`
4. Async → Use `AsyncAudioAnalyzer`

## Algorithm Modes

- **Intelligent**: Balanced (key 40%, BPM 30%, energy 20%, emotional 10%)
- **Classic Camelot**: Traditional (key 90%, BPM 10%, energy 0%, emotional 0%)
- **Energy Flow**: Energy focus (key 20%, BPM 20%, energy 50%, emotional 10%)
- **Emotional**: Emotional continuity (key 20%, BPM 10%, energy 20%, emotional 50%)
- **Structural**: Balanced analysis (key 25%, BPM 25%, energy 25%, emotional 25%)

**Note**: Structural mode is implemented but not exposed through the UI facade.

## Security
- Path validation via `SecurityValidator`
- Encrypted settings via `SecureSettingsDatabase`
- Input validation at facade boundaries

## Testing
- `test_engine.py`: Algorithm validation
- `test_enhanced.py`: Architecture validation

## Performance
- Async analysis with worker pools
- Cache based on file hash
- Batch processing for large collections
- Event-driven UI updates