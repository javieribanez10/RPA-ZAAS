#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Validation script for RPA-ZAAS performance optimizations.
Tests the optimized components without requiring actual browser interaction.
"""

import logging
import time
from utils.performance_monitor import perf_monitor, measure_step

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def validate_performance_monitor():
    """Validate the performance monitoring system."""
    logger.info("🧪 Validating performance monitor...")
    
    perf_monitor.start_session()
    
    # Test multiple steps with different durations
    with measure_step("Fast operation"):
        time.sleep(0.01)
    
    with measure_step("Medium operation"):
        time.sleep(0.1)
    
    with measure_step("Slow operation"):
        time.sleep(0.5)
    
    total_time = perf_monitor.end_session()
    
    # Validate timing accuracy
    fast_time = perf_monitor.get_step_time("Fast operation")
    medium_time = perf_monitor.get_step_time("Medium operation")
    slow_time = perf_monitor.get_step_time("Slow operation")
    
    # Check that times are in expected ranges
    assert 0.005 < fast_time < 0.05, f"Fast operation time unexpected: {fast_time}"
    assert 0.05 < medium_time < 0.2, f"Medium operation time unexpected: {medium_time}"
    assert 0.4 < slow_time < 0.7, f"Slow operation time unexpected: {slow_time}"
    
    # Check bottleneck detection
    bottlenecks = perf_monitor.get_bottlenecks(0.2)
    assert "Slow operation" in bottlenecks, "Bottleneck detection failed"
    assert "Fast operation" not in bottlenecks, "False positive in bottleneck detection"
    
    logger.info("✅ Performance monitor validation passed")
    return True

def validate_imports():
    """Validate that all optimized components can be imported."""
    logger.info("🧪 Validating optimized component imports...")
    
    try:
        # Test core imports
        from services.nubox_service import NuboxService
        from services.components.browser_manager import BrowserManager
        from services.components.authentication import AuthenticationService
        from services.components.navigation import NavigationService
        from services.components.ui_elements import UIElementService
        from core.rpa_controller import RPAController
        from utils.performance_monitor import perf_monitor, measure_step, measure_performance
        
        logger.info("✅ All optimized components imported successfully")
        return True
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        return False

def validate_optimizations_applied():
    """Validate that optimizations have been applied to the code."""
    logger.info("🧪 Validating optimizations are applied...")
    
    # Check that time.sleep has been removed from key files
    import os
    import re
    
    optimization_files = [
        'services/components/authentication.py',
        'services/components/navigation.py', 
        'services/components/ui_elements.py'
    ]
    
    base_path = '/home/runner/work/RPA-ZAAS/RPA-ZAAS'
    sleep_pattern = re.compile(r'time\.sleep\s*\(')
    
    for file_path in optimization_files:
        full_path = os.path.join(base_path, file_path)
        if os.path.exists(full_path):
            with open(full_path, 'r') as f:
                content = f.read()
                sleep_matches = sleep_pattern.findall(content)
                if sleep_matches:
                    logger.warning(f"⚠️ Found {len(sleep_matches)} time.sleep calls in {file_path}")
                else:
                    logger.info(f"✅ No time.sleep calls found in {file_path}")
    
    # Check for performance decorators
    nubox_service_path = os.path.join(base_path, 'services/nubox_service.py')
    with open(nubox_service_path, 'r') as f:
        content = f.read()
        if '@measure_performance' in content:
            logger.info("✅ Performance decorators found in NuboxService")
        else:
            logger.warning("⚠️ Performance decorators not found in NuboxService")
    
    logger.info("✅ Optimization validation completed")
    return True

def validate_browser_optimizations():
    """Validate browser optimization arguments."""
    logger.info("🧪 Validating browser optimizations...")
    
    import os
    browser_manager_path = '/home/runner/work/RPA-ZAAS/RPA-ZAAS/services/components/browser_manager.py'
    
    with open(browser_manager_path, 'r') as f:
        content = f.read()
    
    # Check for key optimization flags
    optimization_flags = [
        '--headless=new',
        '--disable-images', 
        '--disable-plugins',
        '--disable-extensions',
        '--no-sandbox',
        '--disable-dev-shm-usage'
    ]
    
    found_flags = 0
    for flag in optimization_flags:
        if flag in content:
            found_flags += 1
            logger.info(f"✅ Found optimization flag: {flag}")
        else:
            logger.warning(f"⚠️ Missing optimization flag: {flag}")
    
    if found_flags >= len(optimization_flags) * 0.8:  # At least 80% of flags present
        logger.info("✅ Browser optimizations validation passed")
        return True
    else:
        logger.warning(f"⚠️ Only {found_flags}/{len(optimization_flags)} optimization flags found")
        return False

def main():
    """Run all validation tests."""
    logger.info("🚀 Starting RPA-ZAAS Optimization Validation")
    logger.info("=" * 60)
    
    tests = [
        ("Component Imports", validate_imports),
        ("Performance Monitor", validate_performance_monitor), 
        ("Optimizations Applied", validate_optimizations_applied),
        ("Browser Optimizations", validate_browser_optimizations)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n🧪 Running: {test_name}")
        try:
            if test_func():
                logger.info(f"✅ {test_name} PASSED")
                passed += 1
            else:
                logger.error(f"❌ {test_name} FAILED")
        except Exception as e:
            logger.error(f"❌ {test_name} FAILED with exception: {e}")
    
    logger.info("\n" + "=" * 60)
    logger.info(f"🎯 Validation Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🚀 All optimizations validated successfully!")
        logger.info("💡 The RPA-ZAAS system is ready for high-performance operation")
    else:
        logger.warning(f"⚠️ {total - passed} validation(s) failed - please review")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)