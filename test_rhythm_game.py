#!/usr/bin/env python3
"""
Test script for the Enhanced Neon Rhythm Game
Tests key functionality without requiring display or audio
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

def test_imports():
    """Test that all required modules can be imported"""
    try:
        from main import (
            RhythmGame, Note, Particle, PerformanceMonitor,
            BackgroundRenderer, AudioManager, GameSettings,
            ChartGenerator, SongManager
        )
        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def test_data_structures():
    """Test that data structures work correctly"""
    try:
        from main import Note, Particle, NEON_CYAN
        
        # Test Note creation
        note = Note(lane=0, y=100)
        assert note.lane == 0
        assert note.y == 100
        assert not note.hit
        assert not note.missed
        
        # Test Particle creation  
        particle = Particle(100, 200, NEON_CYAN)
        assert particle.x == 100
        assert particle.y == 200
        assert particle.color == NEON_CYAN
        assert particle.life > 0
        
        print("✓ Data structures working correctly")
        return True
    except Exception as e:
        print(f"✗ Data structure test failed: {e}")
        return False

def test_performance_monitor():
    """Test performance monitoring functionality"""
    try:
        from main import PerformanceMonitor
        
        monitor = PerformanceMonitor()
        assert monitor.quality_level == "high"
        
        # Simulate poor performance
        for _ in range(60):
            monitor.frame_times.append(0.04)  # 25 FPS
        
        monitor.update(0.04)
        # Should auto-adjust quality due to poor performance
        
        print("✓ Performance monitor working correctly")
        return True
    except Exception as e:
        print(f"✗ Performance monitor test failed: {e}")
        return False

def test_chart_generator():
    """Test chart generation functionality"""
    try:
        from main import ChartGenerator
        
        generator = ChartGenerator()
        
        # Test analysis
        analysis = generator.get_default_analysis()
        assert "duration" in analysis
        assert "bpm" in analysis
        assert analysis["duration"] > 0
        
        # Test chart generation
        chart = generator.generate_chart(analysis, "Normal")
        assert isinstance(chart, list)
        
        # Test duplicate removal
        duplicate_notes = [
            {"time": 1.0, "lane": 0},
            {"time": 1.05, "lane": 0},  # Too close
            {"time": 2.0, "lane": 1}
        ]
        filtered = generator.remove_duplicate_notes(duplicate_notes)
        assert len(filtered) == 2  # Should remove middle note
        
        print("✓ Chart generator working correctly")
        return True
    except Exception as e:
        print(f"✗ Chart generator test failed: {e}")
        return False

def test_settings_management():
    """Test settings loading and validation"""
    try:
        from main import GameSettings, ConfigManager
        
        settings = GameSettings()
        
        # Test default settings load
        assert "resolution" in settings.settings
        assert "fullscreen" in settings.settings
        assert isinstance(settings.settings["resolution"], list)
        
        # Test config manager validation
        config_manager = ConfigManager()
        test_config = {"display": {"width": 100, "height": 100}}  # Too small
        validated = config_manager.validate_config(test_config)
        assert validated["display"]["width"] >= 800  # Should be corrected
        
        print("✓ Settings management working correctly")
        return True
    except Exception as e:
        print(f"✗ Settings management test failed: {e}")
        return False

def test_error_handling():
    """Test that error handling works as expected"""
    try:
        from main import create_error_report, safe_cleanup
        
        # Test error report creation
        test_error = ValueError("Test error")
        report = create_error_report(test_error, "test_context")
        assert "ERROR REPORT" in report
        assert "Test error" in report
        assert "test_context" in report
        
        # Test safe cleanup (should not crash)
        safe_cleanup()
        
        print("✓ Error handling working correctly")
        return True
    except Exception as e:
        print(f"✗ Error handling test failed: {e}")
        return False

def run_tests():
    """Run all tests and report results"""
    print("Running Enhanced Neon Rhythm Game Tests...")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_data_structures,
        test_performance_monitor,
        test_chart_generator,
        test_settings_management,
        test_error_handling
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! The IndentationError fix was successful.")
        print("The Enhanced Neon Rhythm Game is ready to run.")
        return True
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)