#!/usr/bin/env python3
"""
BlueLibrary Test Audio Generator

Genera archivos de audio sintéticos para testear la aplicación con diferentes:
- Formatos de archivo (MP3, FLAC, WAV, etc.)
- Claves harmónicas (sistema Camelot)
- Tempos/BPM
- Niveles de energía
- Géneros musicales
- Casos límite y edge cases
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Tuple
import argparse

# Try to import audio libraries
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    import soundfile as sf
    SOUNDFILE_AVAILABLE = True
except ImportError:
    SOUNDFILE_AVAILABLE = False

try:
    import mutagen
    from mutagen.id3 import ID3, TIT2, TPE1, TALB, TCON, TBPM, TKEY
    from mutagen.mp3 import MP3
    from mutagen.flac import FLAC
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False

class TestAudioGenerator:
    """Generador de archivos de audio sintéticos para testing"""
    
    def __init__(self, base_path: str = "test_data"):
        self.base_path = Path(base_path)
        self.sample_rate = 44100
        self.duration = 30  # 30 segundos por track
        
        # Camelot wheel mapping
        self.camelot_keys = {
            # Minor keys (A)
            "1A": ("Ab minor", "Ab", "minor"),
            "2A": ("Eb minor", "Eb", "minor"), 
            "3A": ("Bb minor", "Bb", "minor"),
            "4A": ("F minor", "F", "minor"),
            "5A": ("C minor", "C", "minor"),
            "6A": ("G minor", "G", "minor"),
            "7A": ("D minor", "D", "minor"),
            "8A": ("A minor", "A", "minor"),
            "9A": ("E minor", "E", "minor"),
            "10A": ("B minor", "B", "minor"),
            "11A": ("F# minor", "F#", "minor"),
            "12A": ("Db minor", "Db", "minor"),
            
            # Major keys (B)
            "1B": ("B major", "B", "major"),
            "2B": ("F# major", "F#", "major"),
            "3B": ("Db major", "Db", "major"),
            "4B": ("Ab major", "Ab", "major"),
            "5B": ("Eb major", "Eb", "major"),
            "6B": ("Bb major", "Bb", "major"),
            "7B": ("F major", "F", "major"),
            "8B": ("C major", "C", "major"),
            "9B": ("G major", "G", "major"),
            "10B": ("D major", "D", "major"),
            "11B": ("A major", "A", "major"),
            "12B": ("E major", "E", "major")
        }
        
        # BPM ranges por género
        self.genre_bpm_ranges = {
            "house": (120, 130),
            "techno": (125, 135),
            "trance": (130, 140),
            "dubstep": (140, 150),
            "drum_and_bass": (160, 180),
            "ambient": (60, 90),
            "hip_hop": (70, 100),
            "funk": (100, 120),
            "disco": (110, 130),
            "breakbeat": (130, 150)
        }
        
        # Niveles de energía
        self.energy_levels = {
            "low": (1, 3),
            "medium_low": (3, 5),
            "medium": (5, 7),
            "medium_high": (7, 8),
            "high": (8, 10)
        }
    
    def generate_sine_wave(self, frequency: float, duration: float, 
                          amplitude: float = 0.5):
        """Genera una onda seno"""
        if not NUMPY_AVAILABLE:
            return []
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        return amplitude * np.sin(2 * np.pi * frequency * t)
    
    def generate_chord_progression(self, root_freq: float, 
                                 progression: List[float]):
        """Genera una progresión de acordes"""
        if not NUMPY_AVAILABLE:
            return []
        audio = np.zeros(int(self.sample_rate * self.duration))
        chord_duration = self.duration / len(progression)
        
        for i, interval_ratio in enumerate(progression):
            start_sample = int(i * chord_duration * self.sample_rate)
            end_sample = int((i + 1) * chord_duration * self.sample_rate)
            
            # Crear acorde con fundamental, tercera y quinta
            fundamental = self.generate_sine_wave(
                root_freq * interval_ratio, chord_duration, 0.3
            )
            third = self.generate_sine_wave(
                root_freq * interval_ratio * 1.25, chord_duration, 0.2
            )
            fifth = self.generate_sine_wave(
                root_freq * interval_ratio * 1.5, chord_duration, 0.2
            )
            
            chord = fundamental + third + fifth
            audio[start_sample:end_sample] = chord[:end_sample-start_sample]
        
        return audio
    
    def generate_rhythmic_pattern(self, bpm: int, energy: float):
        """Genera un patrón rítmico basado en BPM y energía"""
        if not NUMPY_AVAILABLE:
            return []
        beat_duration = 60.0 / bpm
        beats_per_bar = 4
        total_beats = int(self.duration / beat_duration)
        
        audio = np.zeros(int(self.sample_rate * self.duration))
        
        for beat in range(total_beats):
            if beat % beats_per_bar == 0:  # Kick en el tiempo 1
                kick_freq = 60  # Hz para kick
                kick_env = self.generate_sine_wave(kick_freq, 0.1, energy * 0.5)
                
                start_sample = int(beat * beat_duration * self.sample_rate)
                end_sample = start_sample + len(kick_env)
                
                if end_sample <= len(audio):
                    audio[start_sample:end_sample] += kick_env
            
            elif beat % 2 == 1:  # Hi-hat en contratiempos
                hihat_freq = 8000  # Hz para hi-hat
                hihat_env = self.generate_sine_wave(hihat_freq, 0.05, energy * 0.2)
                
                start_sample = int(beat * beat_duration * self.sample_rate)
                end_sample = start_sample + len(hihat_env)
                
                if end_sample <= len(audio):
                    audio[start_sample:end_sample] += hihat_env
        
        return audio
    
    def get_root_frequency(self, key_note: str) -> float:
        """Obtiene la frecuencia fundamental de una nota"""
        note_frequencies = {
            "C": 261.63, "C#": 277.18, "Db": 277.18,
            "D": 293.66, "D#": 311.13, "Eb": 311.13,
            "E": 329.63, "F": 349.23, "F#": 369.99,
            "Gb": 369.99, "G": 392.00, "G#": 415.30,
            "Ab": 415.30, "A": 440.00, "A#": 466.16,
            "Bb": 466.16, "B": 493.88
        }
        return note_frequencies.get(key_note, 440.0)
    
    def generate_track_audio(self, camelot_key: str, bpm: int, 
                           energy: float, genre: str):
        """Genera el audio de una pista con características específicas"""
        if not NUMPY_AVAILABLE:
            return []
        key_info = self.camelot_keys[camelot_key]
        root_freq = self.get_root_frequency(key_info[1])
        
        # Progresión de acordes típica
        if key_info[2] == "minor":
            progression = [1.0, 1.125, 1.33, 1.0]  # i - III - VI - i
        else:
            progression = [1.0, 1.25, 1.5, 1.0]   # I - V - IV - I
        
        # Generar componentes de audio
        harmonic = self.generate_chord_progression(root_freq, progression)
        rhythmic = self.generate_rhythmic_pattern(bpm, energy)
        
        # Mezclar componentes
        audio = harmonic * 0.6 + rhythmic * 0.4
        
        # Normalizar
        max_val = np.max(np.abs(audio))
        if max_val > 0:
            audio = audio / max_val * 0.8
        
        return audio.astype(np.float32)
    
    def add_metadata(self, filepath: str, track_info: Dict):
        """Agrega metadata ID3 a un archivo de audio"""
        if not MUTAGEN_AVAILABLE:
            return
        
        try:
            if filepath.endswith('.mp3'):
                audio_file = MP3(filepath)
                if audio_file.tags is None:
                    audio_file.add_tags()
                
                audio_file.tags.add(TIT2(encoding=3, text=track_info['title']))
                audio_file.tags.add(TPE1(encoding=3, text=track_info['artist']))
                audio_file.tags.add(TALB(encoding=3, text=track_info['album']))
                audio_file.tags.add(TCON(encoding=3, text=track_info['genre']))
                audio_file.tags.add(TBPM(encoding=3, text=str(track_info['bpm'])))
                audio_file.tags.add(TKEY(encoding=3, text=track_info['key']))
                
                audio_file.save()
                
            elif filepath.endswith('.flac'):
                audio_file = FLAC(filepath)
                audio_file['TITLE'] = track_info['title']
                audio_file['ARTIST'] = track_info['artist']
                audio_file['ALBUM'] = track_info['album']
                audio_file['GENRE'] = track_info['genre']
                audio_file['BPM'] = str(track_info['bpm'])
                audio_file['KEY'] = track_info['key']
                audio_file.save()
                
        except Exception as e:
            print(f"Warning: Could not add metadata to {filepath}: {e}")
    
    def create_test_track(self, output_dir: Path, filename: str, 
                         camelot_key: str, bpm: int, energy: float, 
                         genre: str, format: str = "wav"):
        """Crea un archivo de audio de prueba"""
        if not SOUNDFILE_AVAILABLE or not NUMPY_AVAILABLE:
            print("Warning: audio libraries not available, creating placeholder files")
            # Crear archivo placeholder con metadata JSON
            metadata = {
                "camelot_key": camelot_key,
                "bpm": bpm,
                "energy": energy,
                "genre": genre,
                "format": format,
                "key_info": self.camelot_keys[camelot_key]
            }
            
            # Crear directorio si no existe
            output_dir.mkdir(parents=True, exist_ok=True)
            
            json_path = output_dir / f"{filename}.json"
            with open(json_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"Created placeholder: {json_path}")
            return
        
        # Generar audio
        audio = self.generate_track_audio(camelot_key, bpm, energy, genre)
        
        # Crear directorio si no existe
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Guardar archivo
        filepath = output_dir / f"{filename}.{format}"
        
        try:
            sf.write(str(filepath), audio, self.sample_rate)
            
            # Agregar metadata
            key_info = self.camelot_keys[camelot_key]
            track_info = {
                'title': filename.replace('_', ' ').title(),
                'artist': f"Test Artist {genre.title()}",
                'album': f"BlueLibrary Test {genre.title()}",
                'genre': genre.title(),
                'bpm': bpm,
                'key': f"{key_info[0]} ({camelot_key})",
                'camelot_key': camelot_key,
                'energy': energy
            }
            
            self.add_metadata(str(filepath), track_info)
            
            # Crear archivo de metadata JSON para referencia
            json_path = output_dir / f"{filename}.json"
            with open(json_path, 'w') as f:
                json.dump(track_info, f, indent=2)
                
            print(f"Created: {filepath}")
            
        except Exception as e:
            print(f"Error creating {filepath}: {e}")

def main():
    parser = argparse.ArgumentParser(description='Generate test audio files for BlueLibrary')
    parser.add_argument('--output', default='test_data', help='Output directory')
    parser.add_argument('--formats', nargs='+', default=['wav'], 
                       help='Audio formats to generate')
    parser.add_argument('--quick', action='store_true', 
                       help='Generate only essential test files')
    
    args = parser.parse_args()
    
    generator = TestAudioGenerator(args.output)
    
    if not SOUNDFILE_AVAILABLE:
        print("⚠️  soundfile not available - will create metadata-only files")
        print("   Install with: pip install soundfile")
    
    if not MUTAGEN_AVAILABLE:
        print("⚠️  mutagen not available - metadata will be limited")
        print("   Install with: pip install mutagen")
    
    print("🎵 Generating test audio files...")
    
    # 1. Camelot wheel testing - una pista por clave
    print("\n📀 Generating Camelot wheel test files...")
    keys_dir = Path(args.output) / "keys"
    for camelot_key in generator.camelot_keys.keys():
        if args.quick and camelot_key not in ["8A", "8B", "9A", "9B"]:
            continue
            
        filename = f"key_{camelot_key}_{generator.camelot_keys[camelot_key][0].replace(' ', '_').replace('#', 'sharp')}"
        generator.create_test_track(
            keys_dir, filename, camelot_key, 125, 5.0, "house", "wav"
        )
    
    # 2. BPM testing - diferentes tempos
    print("\n🥁 Generating BPM test files...")
    tempos_dir = Path(args.output) / "tempos"
    test_bpms = [90, 110, 125, 140, 160, 175] if args.quick else range(80, 180, 10)
    
    for bpm in test_bpms:
        filename = f"bpm_{bpm}_8A_house"
        generator.create_test_track(
            tempos_dir, filename, "8A", bpm, 5.0, "house", "wav"
        )
    
    # 3. Energy levels testing
    print("\n⚡ Generating energy level test files...")
    energy_dir = Path(args.output) / "energy_levels"
    energy_levels = [1, 3, 5, 7, 9] if args.quick else range(1, 11)
    
    for energy in energy_levels:
        filename = f"energy_{energy}_8A_125bpm"
        generator.create_test_track(
            energy_dir, filename, "8A", 125, float(energy), "house", "wav"
        )
    
    # 4. Géneros testing
    print("\n🎼 Generating genre test files...")
    genres_dir = Path(args.output) / "genres"
    genres_to_test = ["house", "techno", "trance"] if args.quick else generator.genre_bpm_ranges.keys()
    
    for genre in genres_to_test:
        bpm_range = generator.genre_bpm_ranges[genre]
        bpm = (bpm_range[0] + bpm_range[1]) // 2
        filename = f"genre_{genre}_8A_{bpm}bpm"
        generator.create_test_track(
            genres_dir, filename, "8A", bpm, 6.0, genre, "wav"
        )
    
    # 5. Formatos testing
    print("\n📁 Generating format test files...")
    formats_dir = Path(args.output) / "formats"
    for format in args.formats:
        if format == "mp3" and not MUTAGEN_AVAILABLE:
            print(f"Skipping {format} - mutagen not available")
            continue
            
        filename = f"format_test_8A_125bpm"
        generator.create_test_track(
            formats_dir, filename, "8A", 125, 5.0, "house", format
        )
    
    # 6. Edge cases
    print("\n🚨 Generating edge case test files...")
    edge_dir = Path(args.output) / "edge_cases"
    
    # Casos extremos
    edge_cases = [
        ("very_slow", "8A", 40, 1.0, "ambient"),
        ("very_fast", "8A", 200, 9.0, "drum_and_bass"),
        ("zero_energy", "8A", 120, 0.1, "ambient"),
        ("max_energy", "8A", 130, 10.0, "techno")
    ]
    
    for name, key, bpm, energy, genre in edge_cases:
        generator.create_test_track(
            edge_dir, name, key, bpm, energy, genre, "wav"
        )
    
    # 7. Compatibility testing sets
    print("\n🔗 Generating compatibility test sets...")
    compat_dir = Path(args.output) / "compatibility_sets"
    
    # Set harmónicamente compatible
    compatible_set = [
        ("compatible_1_8A", "8A", 125, 5.0),
        ("compatible_2_8B", "8B", 125, 5.5),
        ("compatible_3_9A", "9A", 125, 6.0),
        ("compatible_4_7A", "7A", 125, 5.5)
    ]
    
    for name, key, bpm, energy in compatible_set:
        generator.create_test_track(
            compat_dir, name, key, bpm, energy, "house", "wav"
        )
    
    print(f"\n✅ Test audio generation complete!")
    print(f"📂 Files created in: {args.output}")
    print(f"🔍 Check the generated JSON files for metadata details")

if __name__ == "__main__":
    main()