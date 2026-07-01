from __future__ import annotations

import json
from typing import Any, Dict


class GrafanaDashboardGenerator:
    """Generates standard JSON model definitions for RedForge Grafana monitoring dashboards."""

    @staticmethod
    def generate(title: str = "RedForge Operational Telemetry Dashboard") -> str:
        """Return a stringified JSON schema model configuration importable into Grafana."""
        dashboard_model = {
            "annotations": {
                "list": [
                    {
                        "builtIn": 1,
                        "datasource": "-- Grafana --",
                        "enable": True,
                        "hide": True,
                        "name": "Annotations & Alerts",
                        "type": "dashboard"
                    }
                ]
            },
            "editable": True,
            "fiscalYearStartMonth": 0,
            "graphTooltip": 0,
            "id": 1,
            "links": [],
            "liveNow": True,
            "panels": [
                {
                    "collapsed": False,
                    "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
                    "id": 101,
                    "title": "API Request Volume & Latency",
                    "type": "timeseries",
                    "targets": [
                        {
                            "datasource": {"type": "prometheus", "uid": "prometheus"},
                            "editorMode": "code",
                            "expr": "rate(redforge_api_requests_total[1m])",
                            "legendFormat": "{{method}} {{path}}",
                            "range": True,
                            "refId": "A"
                        }
                    ]
                },
                {
                    "collapsed": False,
                    "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
                    "id": 102,
                    "title": "Worker Pool Load & Queue size",
                    "type": "timeseries",
                    "targets": [
                        {
                            "datasource": {"type": "prometheus", "uid": "prometheus"},
                            "editorMode": "code",
                            "expr": "redforge_queue_size_pending",
                            "legendFormat": "Pending Tasks Queue",
                            "range": True,
                            "refId": "A"
                        },
                        {
                            "datasource": {"type": "prometheus", "uid": "prometheus"},
                            "editorMode": "code",
                            "expr": "redforge_workers_active_load",
                            "legendFormat": "Active Workers Load",
                            "range": True,
                            "refId": "B"
                        }
                    ]
                },
                {
                    "collapsed": False,
                    "gridPos": {"h": 6, "w": 8, "x": 0, "y": 8},
                    "id": 103,
                    "title": "Host CPU Usage (%)",
                    "type": "gauge",
                    "targets": [
                        {
                            "datasource": {"type": "prometheus", "uid": "prometheus"},
                            "editorMode": "code",
                            "expr": "redforge_system_cpu_usage_percent",
                            "range": True,
                            "refId": "A"
                        }
                    ]
                },
                {
                    "collapsed": False,
                    "gridPos": {"h": 6, "w": 8, "x": 8, "y": 8},
                    "id": 104,
                    "title": "Host Memory Usage (%)",
                    "type": "gauge",
                    "targets": [
                        {
                            "datasource": {"type": "prometheus", "uid": "prometheus"},
                            "editorMode": "code",
                            "expr": "redforge_system_memory_usage_percent",
                            "range": True,
                            "refId": "A"
                        }
                    ]
                },
                {
                    "collapsed": False,
                    "gridPos": {"h": 6, "w": 8, "x": 16, "y": 8},
                    "id": 105,
                    "title": "Triggered System Alerts Count",
                    "type": "stat",
                    "targets": [
                        {
                            "datasource": {"type": "prometheus", "uid": "prometheus"},
                            "editorMode": "code",
                            "expr": "sum(redforge_alerts_total)",
                            "range": True,
                            "refId": "A"
                        }
                    ]
                }
            ],
            "schemaVersion": 36,
            "style": "dark",
            "tags": ["redforge", "observability", "metrics"],
            "templating": {"list": []},
            "time": {"from": "now-1h", "to": "now"},
            "timepicker": {},
            "timezone": "",
            "title": title,
            "version": 1
        }
        return json.dumps(dashboard_model, indent=2)
