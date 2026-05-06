from __future__ import annotations
import os
from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any

app = FastAPI(title="NLP Agent", version="1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

_TEMPLATES = {
    "critical": (
        "This is a critical issue requiring immediate attention. "
        "The affected pod is degrading system performance and may "
        "cause service disruption if not addressed now."
    ),
    "warning": (
        "This issue is not critical yet but is trending in a dangerous "
        "direction. The team should investigate within the next hour "
        "to prevent escalation."
    ),
    "low": (
        "All systems are operating within normal parameters. "
        "No action is required at this time."
    ),
}

class AlertSummary(BaseModel):
    alerts: list[dict[str, Any]] = []

@app.get("/health")
def health():
    return {"status": "ok", "agent": "nlp"}

@app.post("/agent/nlp")
def analyse_nlp(payload: AlertSummary):
    if not payload.alerts:
        return {
            "pod": "all",
            "agent": "nlp",
            "severity": "low",
            "reason": "No alerts to analyse",
            "recommendation": _TEMPLATES["low"],
            "confidence": 1.0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    critical = [a for a in payload.alerts if a.get("severity") == "critical"]
    warnings = [a for a in payload.alerts if a.get("severity") == "warning"]

    if critical:
        top = critical[0]
        severity = "critical"
    elif warnings:
        top = warnings[0]
        severity = "warning"
    else:
        top = payload.alerts[0]
        severity = "low"

    # Try LLM enrichment if OpenAI key present
    recommendation = _try_llm(top) or _TEMPLATES.get(severity, _TEMPLATES["low"])

    return {
        "pod": top.get("pod", "unknown"),
        "agent": "nlp",
        "severity": severity,
        "reason": f"Analysed {len(payload.alerts)} alert(s)",
        "recommendation": recommendation,
        "confidence": 0.9,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

def _try_llm(alert: dict) -> str | None:
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return None
    try:
        import openai
        client = openai.OpenAI(api_key=key)
        prompt = (
            f"Kubernetes pod '{alert.get('pod')}' has a '{alert.get('severity')}' alert. "
            f"Details: {alert.get('reason')}. "
            f"In 2 plain-English sentences, what is wrong and what should "
            f"the engineer do right now? No jargon."
        )
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=80
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return None