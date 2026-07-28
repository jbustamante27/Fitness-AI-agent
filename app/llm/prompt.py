from __future__ import annotations
import json
from dataclasses import asdict
from app.domain.schemas import ComputedMetrics, RiskAssessment

SYSTEM_PROMPT = '''
You are an experienced endurance training analyst specializing in recreational runners.
You interpret provided training metrics and deterministic risk flags.

You do NOT calculate metrics.
You do NOT invent missing data.
You ONLY analyze the metrics explicitly provided.

Tone: professional, calm, evidence-based, non-alarmist, plain English.
'''

def build_user_prompt(metrics: ComputedMetrics, risk: RiskAssessment) -> str:
    payload = {
        'metrics': asdict(metrics),
        'risk': asdict(risk),
    }

    return (
        "Analyze the following JSON (metrics + risk flags). Use established endurance training principles.\n"
        "Rules:\n"
        "- Use only provided metrics/flags\n"
        "- Respect the provided risk_flags\n"
        "- Keep recommendations conservative and actionable\n"
        "- If limitations exist, acknowledge briefly\n\n"
        "Return EXACTLY three sections with headers:\n"
        "INTERPRETATION:\n"
        "RECOMMENDATIONS:\n"
        "TAKEAWAYS:\n\n"
        f"JSON:\n{json.dumps(payload, indent=2)}\n"
    )