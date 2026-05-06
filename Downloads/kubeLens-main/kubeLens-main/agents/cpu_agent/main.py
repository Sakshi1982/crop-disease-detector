from __future__ import annotations
from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any

app = FastAPI(title="CPU Agent", version="1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

CPU_THRESHOLD: float = 80.0
CONSECUTIVE_LIMIT: int = 3

class MetricsPayload(BaseModel):
    pods: list[dict[str, Any]] = []

@app.get("/health")
def health():
    return {"status": "ok", "agent": "cpu"}

@app.post("/agent/cpu")
def analyse_cpu(payload: MetricsPayload):
    history = [{"pods": payload.pods}]
    pod_series: dict[str, list[float]] = {}
    
    for snapshot in history:
        for pod in snapshot.get("pods", []):
            name = pod.get("name") or pod.get("pod_name", "unknown")
            pod_series.setdefault(name, []).append(
                float(pod.get("cpu_percent", 0))
            )

    for pod_name, readings in pod_series.items():
        consecutive = 0
        peak_cpu = 0.0
        for cpu in readings:
            if cpu > CPU_THRESHOLD:
                consecutive += 1
                peak_cpu = max(peak_cpu, cpu)
            else:
                consecutive = 0
                peak_cpu = 0.0
            if consecutive >= CONSECUTIVE_LIMIT:
                return {
                    "pod": pod_name,
                    "agent": "cpu",
                    "severity": "critical",
                    "reason": f"CPU at {peak_cpu:.1f}% for {consecutive} min",
                    "recommendation": (
                        "This pod is consuming too much processing power. "
                        "Allocate more resources immediately."
                    ),
                    "confidence": round(min(consecutive / 5, 1.0), 2),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

    return {
        "pod": "all",
        "agent": "cpu",
        "severity": "low",
        "reason": "All pods within normal CPU range",
        "recommendation": "No action needed",
        "confidence": 1.0,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }