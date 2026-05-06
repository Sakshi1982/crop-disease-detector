from __future__ import annotations
from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any

app = FastAPI(title="Anomaly Agent", version="1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

SPIKE_MULTIPLIER: float = 2.0
MIN_AVG_BYTES: float = 1.0

class MetricsPayload(BaseModel):
    pods: list[dict[str, Any]] = []

@app.get("/health")
def health():
    return {"status": "ok", "agent": "anomaly"}

@app.post("/agent/anomaly")
def analyse_anomaly(payload: MetricsPayload):
    for pod in payload.pods:
        name = pod.get("name") or pod.get("pod_name", "unknown")
        io = float(pod.get("io_bytes", 0))
        avg = float(pod.get("io_avg_bytes", io))

        if avg < MIN_AVG_BYTES:
            continue

        if io > SPIKE_MULTIPLIER * avg:
            ratio = io / avg
            return {
                "pod": name,
                "agent": "anomaly",
                "severity": "warning",
                "reason": (
                    f"I/O spike detected: {io/1_048_576:.1f} MB "
                    f"({ratio:.1f}x above normal)"
                ),
                "recommendation": (
                    "This pod is reading or writing far more data than "
                    "normal. Check if a scheduled job triggered this."
                ),
                "confidence": round(min(ratio / 5, 1.0), 2),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    return {
        "pod": "all",
        "agent": "anomaly",
        "severity": "low",
        "reason": "No storage anomalies detected",
        "recommendation": "No action needed",
        "confidence": 1.0,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }