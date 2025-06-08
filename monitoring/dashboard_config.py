from __future__ import annotations

from typing import Any, Dict

GRAFANA_DASHBOARD: Dict[str, Any] = {
    "title": "AI Video Pipeline",
    "panels": [
        {"type": "graph", "title": "API Response Time", "metrics": "service_response_seconds"},
        {"type": "graph", "title": "Error Rate", "metrics": "service_errors_total"},
        {"type": "graph", "title": "Cost per Video", "metrics": "video_cost_usd"},
    ],
}

__all__ = ["GRAFANA_DASHBOARD"]
