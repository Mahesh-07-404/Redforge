from __future__ import annotations

import os
import time
from typing import Any

from .logger import StructuredLogger


class Profiler:
    """Measures code block CPU, memory usage, and execution latency."""

    def __init__(self, logger: StructuredLogger | None = None) -> None:
        self.logger = logger or StructuredLogger("profiler")
        self.slow_threshold_seconds = 2.0
        self._profiles: list[dict[str, Any]] = []

    def profile(self, name: str, threshold: float | None = None) -> ProfileContext:
        """Create a profile measurement context manager."""
        return ProfileContext(self, name, threshold or self.slow_threshold_seconds)

    def record_profile(self, measurement: dict[str, Any]) -> None:
        self._profiles.append(measurement)
        duration = measurement["duration_seconds"]
        if duration > measurement["threshold"]:
            self.logger.warning(
                f"Slow execution detected: {measurement['name']} took {duration:.2f}s",
                duration=duration,
                metric_name=measurement["name"],
                cpu_delta=measurement["cpu_delta_percent"],
                memory_delta_mb=measurement["memory_delta_mb"],
            )

    def get_profiles(self) -> list[dict[str, Any]]:
        return self._profiles

    def clear(self) -> None:
        self._profiles.clear()


class ProfileContext:
    """Context manager measuring execution metrics during its lifecycle."""

    def __init__(self, profiler: Profiler, name: str, threshold: float) -> None:
        self.profiler = profiler
        self.name = name
        self.threshold = threshold

        self.start_time = 0.0
        self.start_memory = 0.0

    def __enter__(self) -> ProfileContext:
        self.start_time = time.time()
        self.start_memory = self._get_memory_usage()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        end_time = time.time()
        end_memory = self._get_memory_usage()

        duration = end_time - self.start_time
        memory_delta = end_memory - self.start_memory

        measurement = {
            "name": self.name,
            "duration_seconds": duration,
            "threshold": self.threshold,
            "memory_delta_mb": memory_delta,
            "cpu_delta_percent": 0.0,  # Fallback
            "timestamp": end_time,
        }
        self.profiler.record_profile(measurement)

    def _get_memory_usage(self) -> float:
        """Return RSS memory usage of current process in MB."""
        try:
            import psutil

            process = psutil.Process(os.getpid())
            return float(process.memory_info().rss) / (1024 * 1024)
        except ImportError:
            # Fallback using resource library on Unix
            try:
                import resource

                # resource.getrusage returns in kilobytes on Linux
                return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
            except Exception:
                return 0.0
