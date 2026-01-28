from __future__ import annotations
from datetime import datetime
from typing import Any, Dict


def _clean_md(text: str) -> str:
    '''
    Light cleanup for LLM output
    '''
    if not text:
        return ''
    t = text.strip()
    # common patter: model wraps secti9on in ** ... **
    if t.startswith('**'):
        t = t.lstrip('*').strip()
    if t.endswith('**'):
        t = t.rstrip('*').strip()
    return t

def render_markdown(payload: Dict[str, Any]) -> str:
    runner_name = payload.get('runner_name', "Runner")
    generated_at = payload.get('generated_at', '')
    metrics = payload.get('metrics', {})
    risk = payload.get('risk', {})
    narrative = payload.get('narrative', {})

    risk_level = risk.get('risk_level', 'unknown')
    risk_flags = risk.get('risk_flags', [])
    limitations = risk.get('limitations', [])
    flag_details = risk.get('flag_details', {})

    interpretation = _clean_md(narrative.get('interpretation', ''))
    recommendations = _clean_md(narrative.get('recommendations', ''))
    takeaways = _clean_md(narrative.get('takeaways', ''))

    def bullet_list(items):
        if not items:
            return "_None_"
        return '\n'.join([f'- {x}' for x in items])
    
    md = f"""# Running Coach Report — {runner_name}

**Generated:** {generated_at}

---

## Summary
- **Risk level:** **{risk_level}**
- **Runs in last {metrics.get("lookback_days", 28)} days:** {metrics.get("run_count")}
- **Total distance (km):** {metrics.get("total_distance_km")}
- **ACWR:** {metrics.get("acwr")}
- **Longest run share:** {metrics.get("longest_run_pct")}
- **Rest days (last 14):** {metrics.get("rest_days_last_14")}
- **Back-to-back run days (last 14):** {metrics.get("back_to_back_runs_last_14")}
- **Easy %:** {metrics.get("easy_pct")} | **Hard %:** {metrics.get("hard_pct")}

---

## Risk flags
{bullet_list(risk_flags)}

### Flag details
{bullet_list([f"**{k}** — {v}" for k, v in flag_details.items()])}

### Limitations
{bullet_list(limitations)}

---

## Interpretation
{interpretation}

---

## Recommendations
{recommendations}

---

## Key takeaways
{takeaways}
"""
    return md