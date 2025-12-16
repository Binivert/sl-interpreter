"""Performance monitoring utilities."""

import logging
import time
from collections import deque
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Monitors system performance metrics."""
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self._timings: Dict[str, deque] = {}
        self._counters: Dict[str, int] = {}
        self._start_times: Dict[str, float] = {}
    
    def start_timer(self, name: str):
        """Start a named timer."""
        self._start_times[name] = time.perf_counter()
    
    def stop_timer(self, name: str) -> Optional[float]:
        """Stop a named timer and record the duration."""
        
        if name not in self._start_times:
            return None
        
        duration = time.perf_counter() - self._start_times[name]
        del self._start_times[name]
        
        if name not in self._timings:
            self._timings[name] = deque(maxlen=self.window_size)
        
        self._timings[name].append(duration)
        
        return duration
    
    def increment_counter(self, name: str, amount: int = 1):
        """Increment a counter."""
        
        if name not in self._counters:
            self._counters[name] = 0
        
        self._counters[name] += amount
    
    def get_average(self, name: str) -> Optional[float]:
        """Get average timing for a metric."""
        
        if name not in self._timings or len(self._timings[name]) == 0:
            return None
        
        return sum(self._timings[name]) / len(self._timings[name])
    
    def get_fps(self, name: str) -> Optional[float]:
        """Get FPS based on timing metric."""
        
        avg = self.get_average(name)
        if avg is None or avg == 0:
            return None
        
        return 1.0 / avg
    
    def get_counter(self, name: str) -> int:
        """Get counter value."""
        
        return self._counters.get(name, 0)
    
    def get_stats(self) -> Dict:
        """Get all performance statistics."""
        
        stats = {
            "timings": {},
            "counters": dict(self._counters)
        }
        
        for name, timings in self._timings.items():
            if len(timings) > 0:
                stats["timings"][name] = {
                    "average_ms": sum(timings) / len(timings) * 1000,
                    "min_ms": min(timings) * 1000,
                    "max_ms": max(timings) * 1000,
                    "samples": len(timings)
                }
        
        return stats
    
    def reset(self):
        """Reset all metrics."""
        
        self._timings.clear()
        self._counters.clear()
        self._start_times.clear()
