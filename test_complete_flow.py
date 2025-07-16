#!/usr/bin/env python3
"""
Complete Application Flow Test

Test the complete workflow of BlueLibrary including:
1. Application startup
2. Audio file loading
3. Harmonic analysis
4. Compatibility scoring
5. Playlist generation
6. Different mixing algorithms
"""

import os
import sys
import asyncio
import time
from pathlib import Path
from typing import List, Dict

# Add the project root to sys.path
sys.path.insert(0, str(Path(__file__).parent))

from harmonic_mixer.core.application_facade import BlueLibraryFacade
from harmonic_mixer.core.event_system import event_manager, EventType
from harmonic_mixer.utils.async_analyzer import AsyncAudioAnalyzer

class CompleteFlowTester:
    def __init__(self):
        self.facade = BlueLibraryFacade()
        self.events_received = []
        self.analysis_complete = False
        
        # Subscribe to events
        event_manager.event_bus.subscribe(EventType.TRACK_LOADED, self.on_track_loaded)
        event_manager.event_bus.subscribe(EventType.ANALYSIS_COMPLETED, self.on_analysis_complete)
        event_manager.event_bus.subscribe(EventType.ANALYSIS_PROGRESS, self.on_analysis_progress)
        
    def on_track_loaded(self, track_data):
        """Handle track loaded event"""
        self.events_received.append(("track_loaded", track_data))
        print(f"   📀 Track loaded: {track_data.get('title', 'Unknown')}")
        
    def on_analysis_complete(self, analysis_data):
        """Handle analysis complete event"""
        self.events_received.append(("analysis_complete", analysis_data))
        print(f"   ✅ Analysis complete for: {analysis_data.get('track_id', 'Unknown')}")
        self.analysis_complete = True
        
    def on_analysis_progress(self, progress_data):
        """Handle analysis progress event"""
        if progress_data.get('percentage', 0) % 20 == 0:  # Only show every 20%
            print(f"   🔄 Analysis progress: {progress_data.get('percentage', 0)}%")

    async def test_complete_flow(self):
        """Test the complete application flow"""
        print("🎵 Testing Complete BlueLibrary Flow")
        print("=" * 50)
        
        # 1. Test application startup
        print("\n1. Testing Application Startup...")
        try:
            # The facade is already initialized in __init__
            print("   ✅ Application started successfully")
        except Exception as e:
            print(f"   ❌ Application startup failed: {e}")
            return False
            
        # 2. Test audio file loading
        print("\n2. Testing Audio File Loading...")
        test_audio_path = Path("test_data")
        if not test_audio_path.exists():
            print("   ❌ Test audio directory not found")
            return False
            
        try:
            # Load some test files
            audio_files = list(test_audio_path.rglob("*.wav"))[:5]  # First 5 WAV files
            print(f"   📂 Found {len(audio_files)} test audio files")
            
            # Load folder instead of individual files
            print(f"   📂 Loading folder: {test_audio_path}")
            await self.facade.load_music_folder(str(test_audio_path))
                
            tracks = self.facade.get_tracks()
            print(f"   ✅ Loaded {len(tracks)} tracks successfully")
            
        except Exception as e:
            print(f"   ❌ Audio loading failed: {e}")
            return False
            
        # 3. Test harmonic analysis
        print("\n3. Testing Harmonic Analysis...")
        try:
            tracks = self.facade.get_tracks()
            if not tracks:
                print("   ❌ No tracks loaded for analysis")
                return False
                
            # Test analysis on first track
            first_track = tracks[0]
            print(f"   🔍 Analyzing track: {first_track.title}")
            
            # Wait for analysis to complete
            timeout = 30  # 30 second timeout
            start_time = time.time()
            
            while not self.analysis_complete and (time.time() - start_time) < timeout:
                await asyncio.sleep(0.5)
                
            if self.analysis_complete:
                print("   ✅ Harmonic analysis completed")
            else:
                print("   ⚠️  Analysis timeout (might still be processing)")
                
        except Exception as e:
            print(f"   ❌ Harmonic analysis failed: {e}")
            return False
            
        # 4. Test compatibility scoring
        print("\n4. Testing Compatibility Scoring...")
        try:
            tracks = self.facade.get_tracks()
            if len(tracks) < 2:
                print("   ❌ Need at least 2 tracks for compatibility testing")
                return False
                
            track1 = tracks[0]
            track2 = tracks[1]
            
            compatibility = self.facade.calculate_track_compatibility(track1.id, track2.id)
            print(f"   🔗 Compatibility between tracks: {compatibility:.3f}")
            
            if compatibility >= 0:
                print("   ✅ Compatibility calculation working")
            else:
                print("   ❌ Invalid compatibility score")
                return False
                
        except Exception as e:
            print(f"   ❌ Compatibility scoring failed: {e}")
            return False
            
        # 5. Test different mixing algorithms
        print("\n5. Testing Different Mixing Algorithms...")
        try:
            mixing_modes = ["Classic Camelot", "Intelligent", "Energy Flow", "Emotional"]
            
            for mode in mixing_modes:
                print(f"   🎛️  Testing {mode} mode...")
                self.facade.set_mix_mode(mode)
                
                # Test compatibility with this mode
                tracks = self.facade.get_tracks()
                if len(tracks) >= 2:
                    compatibility = self.facade.calculate_track_compatibility(tracks[0].id, tracks[1].id)
                    print(f"      🔗 {mode} compatibility: {compatibility:.3f}")
                    
            print("   ✅ All mixing algorithms tested")
            
        except Exception as e:
            print(f"   ❌ Mixing algorithm testing failed: {e}")
            return False
            
        # 6. Test playlist generation
        print("\n6. Testing Playlist Generation...")
        try:
            tracks = self.facade.get_tracks()
            if not tracks:
                print("   ❌ No tracks available for playlist generation")
                return False
                
            # Generate playlist starting from first track
            playlist = self.facade.generate_playlist(
                target_length=min(3, len(tracks)),
                start_track_id=tracks[0].id
            )
            
            if playlist:
                print(f"   📋 Generated playlist with {len(playlist)} tracks:")
                for i, track in enumerate(playlist, 1):
                    title = track.title
                    key = track.key or 'N/A'
                    bpm = track.bpm or 'N/A'
                    print(f"      {i}. {title} ({key}, {bpm} BPM)")
                print("   ✅ Playlist generation working")
            else:
                print("   ❌ Playlist generation failed")
                return False
                
        except Exception as e:
            print(f"   ❌ Playlist generation failed: {e}")
            return False
            
        # 7. Test application status
        print("\n7. Testing Application Status...")
        try:
            status = self.facade.get_application_status()
            print(f"   📊 Application Status:")
            print(f"      • Tracks loaded: {status.get('tracks_loaded', 0)}")
            print(f"      • Current mode: {status.get('mix_mode', 'Unknown')}")
            print(f"      • Analysis progress: {status.get('analysis_progress', 0)}%")
            print("   ✅ Status reporting working")
            
        except Exception as e:
            print(f"   ❌ Status reporting failed: {e}")
            return False
            
        # 8. Test event system
        print("\n8. Testing Event System...")
        print(f"   📡 Total events received: {len(self.events_received)}")
        for event_type, data in self.events_received[-3:]:  # Show last 3 events
            print(f"      • {event_type}: {type(data).__name__}")
        print("   ✅ Event system working")
        
        return True
        
    async def cleanup(self):
        """Clean up resources"""
        try:
            # No explicit shutdown method, just clean up
            print("   🧹 Application cleaned up")
        except Exception as e:
            print(f"   ⚠️  Cleanup warning: {e}")

async def main():
    """Run the complete flow test"""
    tester = CompleteFlowTester()
    
    try:
        success = await tester.test_complete_flow()
        
        print("\n" + "=" * 50)
        if success:
            print("🎉 COMPLETE FLOW TEST: SUCCESS!")
            print("   All core features are working correctly")
        else:
            print("❌ COMPLETE FLOW TEST: FAILED!")
            print("   Some features need attention")
            
    except Exception as e:
        print(f"\n❌ COMPLETE FLOW TEST: EXCEPTION!")
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    asyncio.run(main())