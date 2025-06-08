from __future__ import annotations

import json
from typing import Any, Dict, List


async def generate_performance_report(data: List[Dict[str, Any]], path: str) -> None:
    """Write performance metrics to a JSON file."""
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
