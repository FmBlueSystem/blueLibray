#!/usr/bin/env python3
"""
Test script for the harmonic mixing engine
"""

from harmonic_mixer.core import HarmonicMixingEngine, Track, MixMode, CamelotKey


def create_test_tracks():
    """Create some test tracks with various properties"""
    tracks = [
        Track("1", "Track A", "Artist 1", "path1.mp3", key="8A", bpm=128.0, energy=7.0, emotional_intensity=6.0),
        Track("2", "Track B", "Artist 2", "path2.mp3", key="9A", bpm=126.0, energy=7.5, emotional_intensity=7.0),
        Track("3", "Track C", "Artist 3", "path3.mp3", key="8B", bpm=130.0, energy=8.0, emotional_intensity=7.5),
        Track("4", "Track D", "Artist 4", "path4.mp3", key="7A", bpm=125.0, energy=6.5, emotional_intensity=5.5),
        Track("5", "Track E", "Artist 5", "path5.mp3", key="10A", bpm=132.0, energy=8.5, emotional_intensity=8.0),
        Track("6", "Track F", "Artist 6", "path6.mp3", key="8A", bpm=128.5, energy=7.2, emotional_intensity=6.5),
    ]
    return tracks


def test_compatibility_scoring():
    """Test the compatibility scoring between tracks"""
    print("=== Testing Compatibility Scoring ===\n")
    
    engine = HarmonicMixingEngine()
    tracks = create_test_tracks()
    
    # Test compatibility between first track and all others
    base_track = tracks[0]
    print(f"Base track: {base_track.title} ({base_track.key}, {base_track.bpm} BPM)")
    print("\nCompatibility scores:")
    
    for track in tracks[1:]:
        score = engine.calculate_compatibility(base_track, track)
        print(f"  → {track.title} ({track.key}, {track.bpm} BPM): {score:.3f}")


def test_camelot_keys():
    """Test Camelot key compatibility"""
    print("\n=== Testing Camelot Key System ===\n")
    
    test_keys = ["8A", "9B", "1A", "12B"]
    
    for key in test_keys:
        compatible = CamelotKey.get_compatible_keys(key)
        print(f"{key} ({CamelotKey.KEYS[key]}) is compatible with: {', '.join(compatible)}")


def test_mixing_modes():
    """Test different mixing modes"""
    print("\n=== Testing Mixing Modes ===\n")
    
    engine = HarmonicMixingEngine()
    tracks = create_test_tracks()
    base_track = tracks[0]
    test_track = tracks[1]
    
    for mode in MixMode:
        engine.set_mode(mode)
        score = engine.calculate_compatibility(base_track, test_track)
        print(f"{mode.value} mode - Weights: {engine.weights}")
        print(f"  Compatibility score: {score:.3f}")


def test_playlist_generation():
    """Test playlist generation"""
    print("\n=== Testing Playlist Generation ===\n")
    
    engine = HarmonicMixingEngine()
    tracks = create_test_tracks()
    
    # Generate playlist starting from first track
    playlist = engine.generate_playlist(tracks, tracks[0], target_length=5)
    
    print("Generated playlist:")
    for i, track in enumerate(playlist, 1):
        print(f"{i}. {track.title} ({track.key}, {track.bpm} BPM, Energy: {track.energy})")
    
    # Test with energy progression
    print("\nWith ascending energy curve:")
    playlist = engine.generate_playlist(tracks, tracks[0], target_length=5, progression_curve="ascending")
    
    for i, track in enumerate(playlist, 1):
        print(f"{i}. {track.title} ({track.key}, {track.bpm} BPM, Energy: {track.energy})")


def test_compatibility_matrix():
    """Test compatibility matrix generation"""
    print("\n=== Testing Compatibility Matrix ===\n")
    
    engine = HarmonicMixingEngine()
    tracks = create_test_tracks()[:4]  # Use fewer tracks for readability
    
    matrix = engine.build_compatibility_matrix(tracks)
    
    print("Compatibility Matrix:")
    print("     ", end="")
    for track in tracks:
        print(f"{track.title:>10}", end="")
    print()
    
    for i, track1 in enumerate(tracks):
        print(f"{track1.title:<5}", end="")
        for j, track2 in enumerate(tracks):
            print(f"{matrix[i][j]:>10.3f}", end="")
        print()


if __name__ == "__main__":
    test_camelot_keys()
    test_compatibility_scoring()
    test_mixing_modes()
    test_playlist_generation()
    test_compatibility_matrix()
    
    print("\n✓ All tests completed!")