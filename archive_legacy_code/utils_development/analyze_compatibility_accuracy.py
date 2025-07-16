#!/usr/bin/env python3
"""
BlueLibrary Compatibility Accuracy Analyzer

Analiza la precisión del algoritmo de compatibilidad armónica
comparando resultados esperados vs obtenidos.
"""

import sys
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Tuple, Any
import argparse
from dataclasses import dataclass

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from harmonic_mixer.core.application_facade import BlueLibraryFacade
    from harmonic_mixer.core.harmonic_engine import Track, CamelotKey
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

@dataclass
class CompatibilityTest:
    """Test de compatibilidad entre dos tracks"""
    track1_key: str
    track2_key: str
    expected_compatibility: str  # "high", "medium", "low" 
    actual_score: float
    expected_score_range: Tuple[float, float]
    passed: bool

class CompatibilityAnalyzer:
    """Analizador de precisión de compatibilidad"""
    
    def __init__(self):
        self.facade = BlueLibraryFacade()
        
        # Definir compatibilidades esperadas según teoría harmónica
        self.expected_compatibilities = {
            # Perfecta compatibilidad (misma clave)
            ("8A", "8A"): ("perfect", (0.95, 1.0)),
            ("8B", "8B"): ("perfect", (0.95, 1.0)),
            
            # Alta compatibilidad (claves adyacentes en Camelot wheel)
            ("8A", "7A"): ("high", (0.85, 0.95)),
            ("8A", "9A"): ("high", (0.85, 0.95)),
            ("8A", "8B"): ("high", (0.85, 0.95)),
            ("8B", "7B"): ("high", (0.85, 0.95)),
            ("8B", "9B"): ("high", (0.85, 0.95)),
            
            # Buena compatibilidad (2 pasos)
            ("8A", "6A"): ("good", (0.70, 0.85)),
            ("8A", "10A"): ("good", (0.70, 0.85)),
            ("8B", "6B"): ("good", (0.70, 0.85)),
            ("8B", "10B"): ("good", (0.70, 0.85)),
            
            # Baja compatibilidad (opuestas en el wheel)
            ("8A", "2A"): ("low", (0.30, 0.60)),
            ("8B", "2B"): ("low", (0.30, 0.60)),
            
            # Muy baja compatibilidad (claves incompatibles)
            ("8A", "3A"): ("very_low", (0.20, 0.50)),
            ("8A", "5A"): ("very_low", (0.20, 0.50)),
        }
        
        # Rangos de BPM para testing
        self.bpm_ranges = {
            "same": (125, 125),
            "close": (125, 128),
            "medium": (125, 135),
            "far": (125, 150),
            "very_far": (125, 180)
        }
    
    def create_test_track(self, key: str, bpm: float, energy: float = 5.0) -> Track:
        """Crea un track de prueba con parámetros específicos"""
        return Track(
            id=f"test_{key}_{bpm}_{energy}",
            filepath=f"/test/{key}_{bpm}.wav",
            title=f"Test Track {key}",
            artist="Test Artist",
            bpm=bpm,
            key=key,
            energy=energy,
            emotional_intensity=energy
        )
    
    def test_harmonic_compatibility(self) -> List[CompatibilityTest]:
        """Test de compatibilidad armónica"""
        results = []
        
        for (key1, key2), (expected_level, score_range) in self.expected_compatibilities.items():
            # Crear tracks con mismos BPM y energía para aislar factor harmónico
            track1 = self.create_test_track(key1, 125.0, 5.0)
            track2 = self.create_test_track(key2, 125.0, 5.0)
            
            # Calcular compatibilidad
            actual_score = self.facade.engine.calculate_compatibility(track1, track2)
            
            # Verificar si está en el rango esperado
            passed = score_range[0] <= actual_score <= score_range[1]
            
            test = CompatibilityTest(
                track1_key=key1,
                track2_key=key2,
                expected_compatibility=expected_level,
                actual_score=actual_score,
                expected_score_range=score_range,
                passed=passed
            )
            
            results.append(test)
        
        return results
    
    def test_bpm_impact(self) -> Dict[str, List[float]]:
        """Test del impacto del BPM en la compatibilidad"""
        base_track = self.create_test_track("8A", 125.0, 5.0)
        results = {}
        
        for bpm_category, (bpm1, bpm2) in self.bpm_ranges.items():
            track2 = self.create_test_track("8A", bpm2, 5.0)  # Misma clave, diferentes BPM
            score = self.facade.engine.calculate_compatibility(base_track, track2)
            
            if bpm_category not in results:
                results[bpm_category] = []
            results[bpm_category].append(score)
        
        return results
    
    def test_energy_impact(self) -> Dict[str, float]:
        """Test del impacto de la energía en la compatibilidad"""
        base_track = self.create_test_track("8A", 125.0, 5.0)
        results = {}
        
        energy_levels = [1.0, 3.0, 5.0, 7.0, 9.0]
        
        for energy in energy_levels:
            track2 = self.create_test_track("8A", 125.0, energy)  # Misma clave y BPM
            score = self.facade.engine.calculate_compatibility(base_track, track2)
            results[f"energy_{energy}"] = score
        
        return results
    
    def test_mix_mode_differences(self) -> Dict[str, Dict[str, float]]:
        """Test de diferencias entre modos de mezcla"""
        track1 = self.create_test_track("8A", 125.0, 5.0)
        track2 = self.create_test_track("8B", 125.0, 6.0)
        
        results = {}
        modes = ["classic", "intelligent", "energy", "emotional"]
        
        for mode in modes:
            self.facade.set_mix_mode(mode)
            score = self.facade.engine.calculate_compatibility(track1, track2)
            weights = self.facade.get_algorithm_weights()
            
            results[mode] = {
                "score": score,
                "weights": weights
            }
        
        return results
    
    def analyze_playlist_generation_quality(self, test_tracks: List[Track]) -> Dict[str, Any]:
        """Analiza la calidad de las playlists generadas"""
        if len(test_tracks) < 5:
            return {"error": "Not enough tracks for playlist analysis"}
        
        # Agregar tracks al facade
        for track in test_tracks:
            self.facade.state.add_track(track)
        
        # Generar playlist
        playlist = self.facade.generate_playlist(
            start_track=test_tracks[0],
            length=5,
            energy_curve="ascending"
        )
        
        if not playlist:
            return {"error": "Playlist generation failed"}
        
        # Analizar transiciones
        transition_scores = []
        energy_progression = []
        
        for i in range(len(playlist) - 1):
            current_track = playlist[i]
            next_track = playlist[i + 1]
            
            score = self.facade.engine.calculate_compatibility(current_track, next_track)
            transition_scores.append(score)
            energy_progression.append(next_track.energy - current_track.energy)
        
        return {
            "playlist_length": len(playlist),
            "transition_scores": transition_scores,
            "average_transition_score": sum(transition_scores) / len(transition_scores),
            "min_transition_score": min(transition_scores),
            "energy_progression": energy_progression,
            "energy_increases": sum(1 for x in energy_progression if x > 0),
            "energy_consistency": len([x for x in energy_progression if -1 <= x <= 2])
        }
    
    def run_comprehensive_analysis(self) -> Dict[str, Any]:
        """Ejecuta análisis completo de compatibilidad"""
        print("🔍 Running compatibility accuracy analysis...")
        
        # Test de compatibilidad armónica
        print("   Testing harmonic compatibility...")
        harmonic_tests = self.test_harmonic_compatibility()
        
        passed_harmonic = sum(1 for test in harmonic_tests if test.passed)
        harmonic_accuracy = passed_harmonic / len(harmonic_tests) * 100
        
        # Test de impacto de BPM
        print("   Testing BPM impact...")
        bpm_results = self.test_bpm_impact()
        
        # Test de impacto de energía
        print("   Testing energy impact...")
        energy_results = self.test_energy_impact()
        
        # Test de diferencias entre modos
        print("   Testing mix mode differences...")
        mode_results = self.test_mix_mode_differences()
        
        # Test de calidad de playlist
        print("   Testing playlist generation...")
        test_tracks = [
            self.create_test_track("8A", 125.0, 4.0),
            self.create_test_track("8B", 126.0, 5.0),
            self.create_test_track("9A", 127.0, 6.0),
            self.create_test_track("7A", 124.0, 5.5),
            self.create_test_track("8A", 125.0, 7.0),
        ]
        playlist_results = self.analyze_playlist_generation_quality(test_tracks)
        
        # Compilar reporte
        report = {
            "harmonic_compatibility": {
                "total_tests": len(harmonic_tests),
                "passed_tests": passed_harmonic,
                "accuracy_percentage": harmonic_accuracy,
                "detailed_results": [
                    {
                        "keys": f"{test.track1_key} -> {test.track2_key}",
                        "expected": test.expected_compatibility,
                        "expected_range": test.expected_score_range,
                        "actual_score": test.actual_score,
                        "passed": test.passed
                    }
                    for test in harmonic_tests
                ],
                "failed_tests": [
                    {
                        "keys": f"{test.track1_key} -> {test.track2_key}",
                        "expected_range": test.expected_score_range,
                        "actual_score": test.actual_score,
                        "difference": min(abs(test.actual_score - test.expected_score_range[0]),
                                        abs(test.actual_score - test.expected_score_range[1]))
                    }
                    for test in harmonic_tests if not test.passed
                ]
            },
            "bpm_impact_analysis": {
                "results": bpm_results,
                "observations": self._analyze_bpm_impact(bpm_results)
            },
            "energy_impact_analysis": {
                "results": energy_results,
                "observations": self._analyze_energy_impact(energy_results)
            },
            "mix_mode_analysis": {
                "results": mode_results,
                "observations": self._analyze_mode_differences(mode_results)
            },
            "playlist_quality": playlist_results,
            "recommendations": self._generate_recommendations(
                harmonic_accuracy, bpm_results, energy_results, mode_results, playlist_results
            )
        }
        
        return report
    
    def _analyze_bpm_impact(self, bpm_results: Dict[str, List[float]]) -> List[str]:
        """Analiza el impacto del BPM"""
        observations = []
        
        if "same" in bpm_results and "far" in bpm_results:
            same_score = bpm_results["same"][0] if bpm_results["same"] else 0
            far_score = bpm_results["far"][0] if bpm_results["far"] else 0
            
            if same_score - far_score > 0.2:
                observations.append("BPM difference significantly impacts compatibility")
            else:
                observations.append("BPM impact is minimal")
        
        return observations
    
    def _analyze_energy_impact(self, energy_results: Dict[str, float]) -> List[str]:
        """Analiza el impacto de la energía"""
        observations = []
        
        energy_values = list(energy_results.values())
        if energy_values:
            max_diff = max(energy_values) - min(energy_values)
            if max_diff > 0.1:
                observations.append("Energy levels significantly impact compatibility")
            else:
                observations.append("Energy impact is minimal")
        
        return observations
    
    def _analyze_mode_differences(self, mode_results: Dict[str, Dict[str, float]]) -> List[str]:
        """Analiza diferencias entre modos"""
        observations = []
        
        scores = [result["score"] for result in mode_results.values()]
        if scores:
            max_diff = max(scores) - min(scores)
            if max_diff > 0.2:
                observations.append("Significant differences between mix modes")
            else:
                observations.append("Mix modes produce similar results")
        
        return observations
    
    def _generate_recommendations(self, harmonic_accuracy: float, 
                                bpm_results: Dict, energy_results: Dict,
                                mode_results: Dict, playlist_results: Dict) -> List[str]:
        """Genera recomendaciones basadas en análisis"""
        recommendations = []
        
        if harmonic_accuracy < 80:
            recommendations.append(
                "Consider improving harmonic compatibility algorithm - accuracy below 80%"
            )
        
        if "error" in playlist_results:
            recommendations.append(
                "Fix playlist generation issues"
            )
        elif playlist_results.get("average_transition_score", 0) < 0.7:
            recommendations.append(
                "Improve playlist transition scoring - average score too low"
            )
        
        # Analizar consistencia de energía
        if (playlist_results.get("energy_consistency", 0) < 
            playlist_results.get("playlist_length", 1) - 1):
            recommendations.append(
                "Improve energy curve consistency in playlist generation"
            )
        
        return recommendations

def main():
    parser = argparse.ArgumentParser(description='Analyze BlueLibrary compatibility accuracy')
    parser.add_argument('--output', default='compatibility_analysis.json',
                       help='Output file for analysis results')
    
    args = parser.parse_args()
    
    analyzer = CompatibilityAnalyzer()
    
    try:
        report = analyzer.run_comprehensive_analysis()
        
        # Guardar reporte
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Mostrar resumen
        harmonic = report['harmonic_compatibility']
        print(f"\n📊 COMPATIBILITY ANALYSIS SUMMARY:")
        print(f"   Harmonic accuracy: {harmonic['accuracy_percentage']:.1f}% "
              f"({harmonic['passed_tests']}/{harmonic['total_tests']})")
        
        if report['recommendations']:
            print(f"\n💡 RECOMMENDATIONS:")
            for rec in report['recommendations']:
                print(f"   - {rec}")
        
        print(f"\n📄 Full analysis saved to: {args.output}")
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()