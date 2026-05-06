from __future__ import annotations
from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any

try:
    import numpy as np
    _NUMPY = True
except ImportError:
    _NUMPY = False

app = FastAPI(title="Memory Agent", version="1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

SLOPE_THRESHOLD_BYTES: float = 5_000_000
MIN_READINGS: int = 3

class MetricsPayload(BaseModel):
    pods: list[dict[str, Any]] = []

def _slope(values):
    n = len(values)
    x = list(range(n))
    if _NUMPY:
        return float(np.polyfit(x, values, 1)[0])
    x_mean = sum(x) / n
    y_mean = sum(values) / n
    num = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, values))
    den = sum((xi - x_mean) ** 2 for xi in x)
    return num / den if den != 0 else 0.0

@app.get("/health")
def health():
    return {"status": "ok", "agent": "memory"}

@app.post("/agent/memory")
def analyse_memory(payload: MetricsPayload):
    pod_series: dict[str, list[float]] = {}
    for pod in payload.pods:
        name = pod.get("name") or pod.get("pod_name", "unknown")
        pod_series.setdefault(name, []).append(
            float(pod.get("memory_bytes", 0))
        )

    for pod_name, readings in pod_series.items():
        if len(readings) < MIN_READINGS:
            continue
        slope = _slope(readings)
        if slope > SLOPE_THRESHOLD_BYTES:
            current_mb = readings[-1] / 1_048_576
            slope_mb = slope / 1_048_576
            return {
                "pod": pod_name,
                "agent": "memory",
                "severity": "warning",
                "reason": (
                    f"Memory growing at {slope_mb:.1f} MB/step, "
                    f"currently at {current_mb:.1f} MB"
                ),
                "recommendation": (
                    "This pod is continuously consuming more memory and "
                    "may crash soon. Restart it and investigate the cause."
                ),
                "confidence": round(min(slope / (SLOPE_THRESHOLD_BYTES * 2), 1.0), 2),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    return {
        "pod": "all",
        "agent": "memory",
        "severity": "low",
        "reason": "Memory usage stable across all pods",
        "recommendation": "No action needed",
        "confidence": 1.0,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }