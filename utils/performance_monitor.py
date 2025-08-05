#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Performance monitoring utility for RPA-ZAAS optimization.
Provides timing measurement and logging for identifying bottlenecks.
"""

import time
import logging
from functools import wraps
from contextlib import contextmanager

logger = logging.getLogger("nubox_rpa.performance")

class PerformanceMonitor:
    """
    Utility class for measuring and logging performance metrics.
    """
    
    def __init__(self):
        self.timings = {}
        self.total_time = 0
        self.start_time = None
    
    def start_session(self):
        """Start a new performance monitoring session."""
        self.start_time = time.time()
        self.timings.clear()
        self.total_time = 0
        logger.info("🚀 Performance monitoring session started")
    
    def end_session(self):
        """End the performance monitoring session and log summary."""
        if self.start_time:
            self.total_time = time.time() - self.start_time
            logger.info(f"⏱️ Total session time: {self.total_time:.2f} seconds")
            self._log_summary()
        return self.total_time
    
    @contextmanager
    def measure_step(self, step_name):
        """Context manager for measuring individual steps."""
        start_time = time.time()
        logger.info(f"⏳ Starting: {step_name}")
        try:
            yield
        finally:
            elapsed = time.time() - start_time
            self.timings[step_name] = elapsed
            logger.info(f"✅ Completed: {step_name} in {elapsed:.2f}s")
    
    def time_function(self, func_name=None):
        """Decorator for timing function execution."""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                name = func_name or f"{func.__module__}.{func.__name__}"
                with self.measure_step(name):
                    return func(*args, **kwargs)
            return wrapper
        return decorator
    
    def _log_summary(self):
        """Log a summary of all measured timings."""
        if not self.timings:
            return
        
        logger.info("📊 Performance Summary:")
        for step, duration in sorted(self.timings.items(), key=lambda x: x[1], reverse=True):
            percentage = (duration / self.total_time) * 100 if self.total_time > 0 else 0
            logger.info(f"  {step}: {duration:.2f}s ({percentage:.1f}%)")
    
    def get_step_time(self, step_name):
        """Get the timing for a specific step."""
        return self.timings.get(step_name, 0)
    
    def get_bottlenecks(self, threshold_seconds=1.0):
        """Identify steps that took longer than the threshold."""
        return {step: duration for step, duration in self.timings.items() 
                if duration >= threshold_seconds}

# Global performance monitor instance
perf_monitor = PerformanceMonitor()

def measure_performance(step_name):
    """Decorator for measuring performance of functions."""
    return perf_monitor.time_function(step_name)

@contextmanager
def measure_step(step_name):
    """Context manager for measuring performance of code blocks."""
    with perf_monitor.measure_step(step_name):
        yield