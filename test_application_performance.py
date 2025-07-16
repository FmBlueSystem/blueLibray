#!/usr/bin/env python3
"""
BlueLibrary Application Performance Tester

Script para probar la aplicación con diferentes tipos de archivos y medir rendimiento.
Identifica oportunidades de mejora y problemas potenciales.
"""

import sys
import time
import json
import asyncio
import traceback
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import argparse

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from harmonic_mixer.core.application_facade import BlueLibraryFacade
    from harmonic_mixer.core.harmonic_engine import Track
    from harmonic_mixer.utils.audio_analyzer import AudioAnalyzer
    from harmonic_mixer.utils.async_analyzer import AsyncAudioAnalyzer
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the BlueLibrary directory")
    sys.exit(1)

@dataclass
class TestResult:
    """Resultado de un test individual"""
    test_name: str
    success: bool
    duration: float
    error_message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

@dataclass 
class PerformanceMetrics:
    """Métricas de rendimiento"""
    total_files: int
    successful_analyses: int
    failed_analyses: int
    average_analysis_time: float
    min_analysis_time: float
    max_analysis_time: float
    total_duration: float
    errors: List[str]

class ApplicationTester:
    """Tester integral de la aplicación BlueLibrary"""
    
    def __init__(self, test_data_path: str = "test_data"):
        self.test_data_path = Path(test_data_path)
        self.facade = BlueLibraryFacade()
        self.results: List[TestResult] = []
        
    def log(self, message: str, level: str = "INFO"):
        """Log con timestamp"""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    def run_test(self, test_name: str, test_func, *args, **kwargs) -> TestResult:
        """Ejecuta un test y mide tiempo"""
        self.log(f"Running test: {test_name}")
        start_time = time.time()
        
        try:
            result = test_func(*args, **kwargs)
            duration = time.time() - start_time
            
            if asyncio.iscoroutine(result):
                result = asyncio.run(result)
            
            test_result = TestResult(
                test_name=test_name,
                success=True,
                duration=duration,
                details=result if isinstance(result, dict) else None
            )
            self.log(f"✅ {test_name} completed in {duration:.2f}s")
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = str(e)
            self.log(f"❌ {test_name} failed after {duration:.2f}s: {error_msg}", "ERROR")
            
            test_result = TestResult(
                test_name=test_name,
                success=False,
                duration=duration,
                error_message=error_msg
            )
        
        self.results.append(test_result)
        return test_result
    
    def test_facade_initialization(self) -> Dict[str, Any]:
        """Test de inicialización del facade"""
        facade = BlueLibraryFacade()
        
        # Verificar que los componentes están inicializados
        checks = {
            "harmonic_engine_initialized": facade.engine is not None,
            "database_initialized": facade.db is not None,
            "state_initialized": facade.state is not None,
            "analysis_manager_initialized": facade.analysis_manager is not None,
            "current_mix_mode": facade.get_mix_mode(),
            "algorithm_weights": facade.get_algorithm_weights(),
            "tracks_count": len(facade.get_tracks())
        }
        
        return checks
    
    def test_audio_file_loading(self, file_path: Path) -> Dict[str, Any]:
        """Test de carga de un archivo individual"""
        if not file_path.exists():
            raise FileNotFoundError(f"Test file not found: {file_path}")
        
        analyzer = AudioAnalyzer()
        
        # Test básico de análisis
        start_time = time.time()
        try:
            metadata = analyzer.analyze_file(str(file_path))
            analysis_time = time.time() - start_time
            
            return {
                "file_path": str(file_path),
                "file_size_mb": file_path.stat().st_size / (1024 * 1024),
                "analysis_time": analysis_time,
                "metadata_extracted": metadata is not None,
                "has_bpm": metadata and hasattr(metadata, 'bpm') and metadata.bpm is not None,
                "has_key": metadata and hasattr(metadata, 'key') and metadata.key is not None,
                "has_energy": metadata and hasattr(metadata, 'energy') and metadata.energy is not None,
                "metadata": metadata.__dict__ if metadata else None
            }
            
        except Exception as e:
            return {
                "file_path": str(file_path),
                "file_size_mb": file_path.stat().st_size / (1024 * 1024),
                "analysis_time": time.time() - start_time,
                "error": str(e)
            }
    
    async def test_folder_loading_async(self, folder_path: Path) -> Dict[str, Any]:
        """Test de carga asíncrona de carpeta"""
        if not folder_path.exists():
            raise FileNotFoundError(f"Test folder not found: {folder_path}")
        
        # Progress tracking
        progress_updates = []
        
        def progress_callback(current, total):
            progress_updates.append({
                "current": current,
                "total": total,
                "percentage": (current / total * 100) if total > 0 else 0,
                "timestamp": time.time()
            })
        
        start_time = time.time()
        success = await self.facade.load_music_folder(
            str(folder_path), 
            progress_callback
        )
        duration = time.time() - start_time
        
        tracks = self.facade.get_tracks()
        
        return {
            "folder_path": str(folder_path),
            "success": success,
            "duration": duration,
            "tracks_loaded": len(tracks),
            "progress_updates": len(progress_updates),
            "tracks_per_second": len(tracks) / duration if duration > 0 else 0
        }
    
    def test_harmonic_compatibility(self) -> Dict[str, Any]:
        """Test del motor de compatibilidad armónica"""
        # Crear tracks de prueba con claves conocidas
        test_tracks = [
            Track(
                id="test_8A",
                filepath="/test/8A.wav",
                title="Test 8A",
                artist="Test",
                bpm=125.0,
                key="8A",
                energy=5.0,
                emotional_intensity=5.0
            ),
            Track(
                id="test_8B", 
                filepath="/test/8B.wav",
                title="Test 8B",
                artist="Test",
                bpm=125.0,
                key="8B",
                energy=5.0,
                emotional_intensity=5.0
            ),
            Track(
                id="test_9A",
                filepath="/test/9A.wav", 
                title="Test 9A",
                artist="Test",
                bpm=125.0,
                key="9A",
                energy=5.0,
                emotional_intensity=5.0
            )
        ]
        
        # Test compatibilidad
        engine = self.facade.engine
        
        # 8A debería ser compatible con 8A, 7A, 9A, 8B
        compat_8A_8A = engine.calculate_compatibility(test_tracks[0], test_tracks[0])
        compat_8A_8B = engine.calculate_compatibility(test_tracks[0], test_tracks[1])
        compat_8A_9A = engine.calculate_compatibility(test_tracks[0], test_tracks[2])
        
        return {
            "self_compatibility_8A": compat_8A_8A,
            "compatibility_8A_8B": compat_8A_8B,
            "compatibility_8A_9A": compat_8A_9A,
            "expected_high_compatibility": compat_8A_8A > 0.9,
            "expected_good_compatibility_8B": compat_8A_8B > 0.8,
            "expected_good_compatibility_9A": compat_8A_9A > 0.8
        }
    
    def test_mix_modes(self) -> Dict[str, Any]:
        """Test de diferentes modos de mezcla"""
        results = {}
        
        # Test todos los modos disponibles
        modes = ["classic", "intelligent", "energy", "emotional", "structural"]
        
        for mode in modes:
            try:
                old_mode = self.facade.get_mix_mode()
                self.facade.set_mix_mode(mode)
                new_mode = self.facade.get_mix_mode()
                weights = self.facade.get_algorithm_weights()
                
                results[mode] = {
                    "mode_set_successfully": new_mode == mode,
                    "weights": weights,
                    "weights_sum": sum(weights.values())
                }
                
            except Exception as e:
                results[mode] = {"error": str(e)}
        
        return results
    
    def test_performance_with_file_count(self, max_files: int = 20) -> PerformanceMetrics:
        """Test de rendimiento con diferentes cantidades de archivos"""
        test_files = []
        
        # Recopilar archivos de prueba
        for subdir in ["keys", "tempos", "energy_levels", "genres"]:
            subdir_path = self.test_data_path / subdir
            if subdir_path.exists():
                test_files.extend(list(subdir_path.glob("*.wav"))[:max_files//4])
        
        test_files = test_files[:max_files]
        
        if not test_files:
            raise FileNotFoundError("No test files found for performance testing")
        
        analysis_times = []
        errors = []
        successful = 0
        
        start_time = time.time()
        
        for file_path in test_files:
            try:
                file_start = time.time()
                result = self.test_audio_file_loading(file_path)
                file_duration = time.time() - file_start
                
                analysis_times.append(file_duration)
                if result.get("metadata_extracted", False):
                    successful += 1
                    
            except Exception as e:
                errors.append(f"{file_path.name}: {str(e)}")
        
        total_duration = time.time() - start_time
        
        return PerformanceMetrics(
            total_files=len(test_files),
            successful_analyses=successful,
            failed_analyses=len(test_files) - successful,
            average_analysis_time=sum(analysis_times) / len(analysis_times) if analysis_times else 0,
            min_analysis_time=min(analysis_times) if analysis_times else 0,
            max_analysis_time=max(analysis_times) if analysis_times else 0,
            total_duration=total_duration,
            errors=errors
        )
    
    def test_edge_cases(self) -> Dict[str, Any]:
        """Test de casos límite"""
        edge_cases_dir = self.test_data_path / "edge_cases"
        results = {}
        
        if not edge_cases_dir.exists():
            return {"error": "Edge cases directory not found"}
        
        for file_path in edge_cases_dir.glob("*.wav"):
            try:
                result = self.test_audio_file_loading(file_path)
                results[file_path.stem] = {
                    "success": "error" not in result,
                    "analysis_time": result.get("analysis_time", 0),
                    "metadata_found": result.get("metadata_extracted", False)
                }
                
            except Exception as e:
                results[file_path.stem] = {
                    "success": False,
                    "error": str(e)
                }
        
        return results
    
    def test_memory_usage(self) -> Dict[str, Any]:
        """Test básico de uso de memoria (requiere psutil)"""
        try:
            import psutil
            process = psutil.Process()
            
            # Memoria antes
            memory_before = process.memory_info().rss / 1024 / 1024  # MB
            
            # Cargar algunos archivos
            test_dir = self.test_data_path / "keys"
            if test_dir.exists():
                asyncio.run(self.test_folder_loading_async(test_dir))
            
            # Memoria después  
            memory_after = process.memory_info().rss / 1024 / 1024  # MB
            
            return {
                "memory_before_mb": memory_before,
                "memory_after_mb": memory_after,
                "memory_increase_mb": memory_after - memory_before,
                "tracks_loaded": len(self.facade.get_tracks())
            }
            
        except ImportError:
            return {"error": "psutil not available for memory testing"}
    
    def run_comprehensive_test_suite(self) -> Dict[str, Any]:
        """Ejecuta la suite completa de tests"""
        self.log("🚀 Starting comprehensive test suite")
        
        # Test básicos
        self.run_test("facade_initialization", self.test_facade_initialization)
        self.run_test("harmonic_compatibility", self.test_harmonic_compatibility)
        self.run_test("mix_modes", self.test_mix_modes)
        
        # Test de archivos individuales
        test_files = []
        for subdir in ["keys", "tempos", "energy_levels"]:
            subdir_path = self.test_data_path / subdir
            if subdir_path.exists():
                test_files.extend(list(subdir_path.glob("*.wav"))[:2])
        
        for file_path in test_files[:5]:  # Test solo algunos archivos
            self.run_test(f"file_loading_{file_path.stem}", 
                         self.test_audio_file_loading, file_path)
        
        # Test de carga de carpeta
        keys_dir = self.test_data_path / "keys"
        if keys_dir.exists():
            self.run_test("folder_loading_async", 
                         self.test_folder_loading_async, keys_dir)
        
        # Test de rendimiento
        self.run_test("performance_test", self.test_performance_with_file_count, 10)
        
        # Test de casos límite
        self.run_test("edge_cases", self.test_edge_cases)
        
        # Test de memoria
        self.run_test("memory_usage", self.test_memory_usage)
        
        return self.generate_report()
    
    def generate_report(self) -> Dict[str, Any]:
        """Genera reporte final de resultados"""
        successful_tests = [r for r in self.results if r.success]
        failed_tests = [r for r in self.results if not r.success]
        
        total_duration = sum(r.duration for r in self.results)
        avg_duration = total_duration / len(self.results) if self.results else 0
        
        report = {
            "summary": {
                "total_tests": len(self.results),
                "successful_tests": len(successful_tests),
                "failed_tests": len(failed_tests),
                "success_rate": len(successful_tests) / len(self.results) * 100 if self.results else 0,
                "total_duration": total_duration,
                "average_test_duration": avg_duration
            },
            "test_results": [
                {
                    "name": r.test_name,
                    "success": r.success,
                    "duration": r.duration,
                    "error": r.error_message,
                    "details": r.details
                }
                for r in self.results
            ],
            "failed_tests": [
                {
                    "name": r.test_name,
                    "error": r.error_message,
                    "duration": r.duration
                }
                for r in failed_tests
            ]
        }
        
        return report

def main():
    parser = argparse.ArgumentParser(description='Test BlueLibrary application performance')
    parser.add_argument('--test-data', default='test_data', 
                       help='Path to test data directory')
    parser.add_argument('--output', default='test_results.json',
                       help='Output file for results')
    parser.add_argument('--quick', action='store_true',
                       help='Run only quick tests')
    
    args = parser.parse_args()
    
    tester = ApplicationTester(args.test_data)
    
    if not Path(args.test_data).exists():
        print(f"❌ Test data directory not found: {args.test_data}")
        print("Run 'python generate_test_audio.py' first to create test files")
        sys.exit(1)
    
    try:
        report = tester.run_comprehensive_test_suite()
        
        # Guardar reporte
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Mostrar resumen
        summary = report['summary']
        print(f"\n📊 TEST SUMMARY:")
        print(f"   Tests run: {summary['total_tests']}")
        print(f"   Successful: {summary['successful_tests']} ({summary['success_rate']:.1f}%)")
        print(f"   Failed: {summary['failed_tests']}")
        print(f"   Total duration: {summary['total_duration']:.2f}s")
        print(f"   Average per test: {summary['average_test_duration']:.2f}s")
        
        if report['failed_tests']:
            print(f"\n❌ FAILED TESTS:")
            for test in report['failed_tests']:
                print(f"   - {test['name']}: {test['error']}")
        
        print(f"\n📄 Full report saved to: {args.output}")
        
        # Exit code basado en resultados
        sys.exit(0 if summary['failed_tests'] == 0 else 1)
        
    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()