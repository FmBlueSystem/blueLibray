# BlueLibrary - Advanced Harmonic Mixer

An intelligent DJ mixing tool that goes beyond traditional Camelot wheel mixing by incorporating BPM, energy levels, and emotional intensity for superior track transitions.

## Features

- **Advanced Harmonic Algorithm**: Multi-factor compatibility scoring beyond simple key matching
- **Multiple Mixing Modes**:
  - Intelligent Mode: Balanced approach using all factors
  - Classic Camelot: Traditional harmonic mixing
  - Energy Flow: Focus on energy progression
  - Emotional: Prioritize emotional continuity
- **Real-time Audio Analysis**: Automatic extraction of key, BPM, energy, and emotional intensity
- **Customizable Weights**: Fine-tune the importance of each mixing factor
- **Playlist Generation**: Create optimal playlists with customizable progression curves
- **Settings Persistence**: Saves your preferences and recent folders
- **Dark Theme UI**: Professional interface optimized for low-light environments

## Installation

### Prerequisites

- Python 3.8 or higher
- macOS, Linux, or Windows

### Install Dependencies

```bash
# Clone or download the project
cd BlueLibrary

# Install required packages
pip install -r requirements.txt
```

### Optional Dependencies

For full audio analysis capabilities, install the optional dependencies:

```bash
# For better audio format support
pip install librosa mutagen

# On macOS, you might need:
brew install ffmpeg
```

## Usage

### Running the Application

```bash
python main.py
```

### Quick Start

1. **Load Music**: Click "Load Music Folder" and select a directory containing your audio files
2. **Wait for Analysis**: The application will analyze each track's musical properties
3. **Select Starting Track**: Click on any track in the table to set it as the starting point
4. **Configure Algorithm**:
   - Choose a mixing mode (Intelligent, Classic Camelot, etc.)
   - Adjust weight sliders if desired
   - Select energy progression curve
5. **Generate Playlist**: Click "Generate Playlist" to create an optimized track sequence

### Understanding the Algorithm

The harmonic mixing engine evaluates track compatibility based on:

- **Key Compatibility** (40% default): Harmonic relationship between tracks
- **BPM Compatibility** (30% default): Tempo matching within tolerance
- **Energy Level** (20% default): Smooth energy transitions
- **Emotional Intensity** (10% default): Maintaining emotional flow

### Camelot Wheel Reference

The application uses Camelot notation for keys:
- **A** = Minor keys (1A-12A)
- **B** = Major keys (1B-12B)

Compatible transitions:
- Same number (different letter): Relative major/minor
- ±1 number (same letter): Adjacent keys on the wheel
- Same key: Perfect match

## Project Structure

```
BlueLibrary/
├── harmonic_mixer/
│   ├── core/          # Harmonic mixing algorithm
│   ├── ui/            # PyQt6 user interface
│   ├── utils/         # Audio analysis utilities
│   └── data/          # Database and persistence
├── main.py            # Application entry point
├── requirements.txt   # Python dependencies
└── README.md         # This file
```

## Development

### Adding New Features

The modular architecture makes it easy to extend:

1. **New Analysis Methods**: Add to `utils/audio_analyzer.py`
2. **New Mixing Modes**: Extend `MixMode` enum and add weight presets
3. **UI Enhancements**: Modify `ui/main_window.py`

### Algorithm Customization

Edit weight calculations in `core/harmonic_engine.py`:
- `_calculate_key_score()`: Key compatibility logic
- `_calculate_bpm_score()`: Tempo matching logic
- `_calculate_energy_score()`: Energy transition logic
- `_calculate_emotional_score()`: Emotional flow logic

## Troubleshooting

### Audio files not loading
- Ensure files are in supported formats: MP3, FLAC, MP4, M4A, WAV
- Check file permissions

### Slow analysis
- Initial analysis extracts multiple features from audio
- Consider analyzing smaller folders first
- Analysis results are not cached (future enhancement)

### Missing metadata
- Install `mutagen` for better metadata extraction
- Install `librosa` for musical feature analysis

## Future Enhancements

- [ ] Real-time audio playback
- [ ] Waveform visualization
- [ ] Export playlists to various formats
- [ ] Integration with DJ software
- [ ] Cloud synchronization
- [ ] Machine learning for personalized recommendations

## License

This project is provided as-is for educational and personal use.

## Credits

Based on research in harmonic mixing algorithms and DJ performance optimization.# blueLibray
