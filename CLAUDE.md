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

## Reglas de Contribución + Validación Automática (CRÍTICO)

**Claude: estas reglas son OBLIGATORIAS cuando trabaje en este repositorio. No entregue respuesta final hasta validarlas.**

### Objetivo
Entregar cambios **funcionales, probados y mínimos**. Toda respuesta debe estar respaldada por ejecución de pruebas.

---

### Flujo de Trabajo Obligatorio

1. **Plan Interno**
   - Analice la solicitud.
   - Genere un plan *interno* (no lo imprima completo a menos que se le solicite).  

2. **Estado Actual: Ejecutar Pruebas**
   - Corra la suite de validación:
     ```bash
     python test_engine.py || exit 1
     python test_enhanced.py || exit 1
     pytest -q || exit 1
     ```
   - Si no puede ejecutar un comando, explique por qué y pida instrucciones.

3. **Aplicar Cambios Mínimos**
   - Modifique solo los archivos necesarios.
   - Límite por iteración: ~400 líneas totales modificadas. Si excede, pida aprobación.

4. **Re-Ejecutar Pruebas (Obligatorio)**
   - Vuelva a correr **todos** los comandos de prueba.
   - Si falla algo: diagnostique, repare, repita (máx. 3 ciclos; luego pida ayuda).

5. **Verificación Final**
   - Opcional: lint si está disponible (`ruff`, `flake8`, `black --check`, etc.).
   - Confirme: "Todos los tests en verde."

6. **Respuesta al Usuario**
   - Resumen breve de cambios.
   - Estado de pruebas: ✅ verde / ❌ fallos (con breve lista).
   - *No pegue archivos completos.* Presente diff compacto o lista de rutas.

---

### Disparador de Revalidación: "¿Está seguro al 100%?"
Si el usuario pregunta "¿está seguro al 100%?" (o detecta "100% seguro", "fully sure", "completely verified"):
1. Re-ejecute **todo el flujo** (Pasos 2–5).
2. Compare checksums o timestamps si es posible.
3. Responda solo tras confirmar resultados actualizados.

---

### Política de Uso de Tokens
- No imprima archivos completos >200 líneas. Use diffs (`@@ ... @@`).
- Para errores extensos, resuma: *"Fallaron 12 pruebas; muestro 3 más representativas, pídame el resto."*
- No muestre binarios ni JSON gigantes; diga dónde están.

---

### Manejo de UI / PyQt6
Cuando cambie componentes de UI con señales/slots (ej. `OptimizedTrackView`):
- Verifique que el objeto no sea destruido antes de conectar señales.
- Ejecute prueba rápida de creación/mostrar/descartar ventana si hay script (`python tools/smoke_ui.py` si existe).
- Si no hay prueba, sugiera crear una.

---

### Comandos Útiles (Claude puede pedir permiso para usarlos)
```bash
# Configurar entorno (ajuste según proyecto)
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Suite rápida
python test_engine.py
python test_enhanced.py
pytest -q

# Lint opcional
ruff check . || true
```

### Qué Hacer si Faltan Pruebas

Si no existen pruebas para el componente que modificará:
- Pregunte al usuario si debe crear tests mínimos.
- Sugiera un smoke test (importar módulo + crear objeto principal + salida limpia).

---

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
```

```bash
# For full audio analysis (optional but recommended)
pip install librosa mutagen soundfile audioread
```

```bash
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