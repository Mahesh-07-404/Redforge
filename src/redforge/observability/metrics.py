from __future__ import annotations

import time

from .contracts import MetricRecord


class MetricsCollector:
    """Manages system metrics collection, updates, and Prometheus scrapers output format."""

    def __init__(self) -> None:
        self._metrics: list[MetricRecord] = []
        # Key: (name, label_key_values_tuple) -> value
        self._counters: dict[tuple, float] = {}
        self._gauges: dict[tuple, float] = {}
        self._histograms: dict[tuple, list[float]] = {}

    def increment(
        self, name: str, value: float = 1.0, labels: dict[str, str] | None = None
    ) -> None:
        """Increment counter metric."""
        lbls = labels or {}
        key = (name, tuple(sorted(lbls.items())))
        self._counters[key] = self._counters.get(key, 0.0) + value
        self._record(name, self._counters[key], lbls)

    def set_gauge(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        """Set gauge metric."""
        lbls = labels or {}
        key = (name, tuple(sorted(lbls.items())))
        self._gauges[key] = value
        self._record(name, value, lbls)

    def record_histogram(
        self, name: str, value: float, labels: dict[str, str] | None = None
    ) -> None:
        """Record value in a histogram."""
        lbls = labels or {}
        key = (name, tuple(sorted(lbls.items())))
        if key not in self._histograms:
            self._histograms[key] = []
        self._histograms[key].append(value)
        self._record(name, value, lbls)

    def _record(self, name: str, value: float, labels: dict[str, str]) -> None:
        self._metrics.append(
            MetricRecord(name=name, value=value, labels=labels, timestamp=time.time())
        )

    def get_metrics(self) -> list[MetricRecord]:
        """Get all raw metric records."""
        return self._metrics

    def export_prometheus(self) -> str:
        """Generate a Prometheus scrape response payload."""
        lines = []

        # Export Counters
        for (name, labels_tuple), value in self._counters.items():
            labels_str = ",".join(f'{k}="{v}"' for k, v in labels_tuple)
            labels_block = f"{{{labels_str}}}" if labels_str else ""
            lines.append(f"# TYPE {name} counter")
            lines.append(f"{name}{labels_block} {value}")

        # Export Gauges
        for (name, labels_tuple), value in self._gauges.items():
            labels_str = ",".join(f'{k}="{v}"' for k, v in labels_tuple)
            labels_block = f"{{{labels_str}}}" if labels_str else ""
            lines.append(f"# TYPE {name} gauge")
            lines.append(f"{name}{labels_block} {value}")

        # Export Histograms (simplified as _sum, _count, and avg)
        for (name, labels_tuple), values in self._histograms.items():
            labels_str = ",".join(f'{k}="{v}"' for k, v in labels_tuple)
            labels_block = f"{{{labels_str}}}" if labels_str else ""

            h_sum = sum(values)
            h_count = len(values)
            lines.append(f"# TYPE {name} histogram")
            lines.append(f"{name}_sum{labels_block} {h_sum}")
            lines.append(f"{name}_count{labels_block} {h_count}")

        return "\n".join(lines) + "\n"

    def clear(self) -> None:
        """Reset metrics records."""
        self._metrics.clear()
        self._counters.clear()
        self._gauges.clear()
        self._histograms.clear()
