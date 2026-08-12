from __future__ import annotations
from typing import Any, Dict


def _clean_md(text: str) -> str:
    '''
    Light cleanup for LLM output
    '''
    if not text:
        return ''
    t = text.strip()
    # common pattern: model wraps section in ** ... **
    if t.startswith('**'):
        t = t.lstrip('*').strip()
    if t.endswith('**'):
        t = t.rstrip('*').strip()
    return t


def render_markdown(payload: Dict[str, Any]) -> str:
    runner_name = payload.get('runner_name', "Runner")
    generated_at = payload.get('generated_at', '')
    metrics = payload.get('metrics', {}) or {}
    risk = payload.get('risk', {}) or {}
    narrative = payload.get('narrative', {}) or {}

    risk_level = risk.get('risk_level', 'unknown')
    flags = risk.get('flags', []) or []
    explanations = risk.get('explanations', []) or []
    limitations = risk.get('limitations', []) or []

    # flags and explanations are parallel lists produced together by assess_risk
    flag_details = [
        f"**{flag}** — {explanation}"
        for flag, explanation in zip(flags, explanations)
    ]

    interpretation = _clean_md(narrative.get('interpretation', ''))
    recommendations = _clean_md(narrative.get('recommendations', ''))
    takeaways = _clean_md(narrative.get('takeaways', ''))

    def bullet_list(items):
        if not items:
            return "_None_"
        return '\n'.join([f'- {x}' for x in items])

    def num(value, digits=1, suffix=''):
        if value is None:
            return 'n/a'
        return f"{value:.{digits}f}{suffix}"

    acwr_note = (
        "" if metrics.get("acwr_distance") is None or metrics.get("acwr_is_reliable")
        else "  _(provisional)_"
    )

    md = f"""# Running Coach Report — {runner_name}

**Generated:** {generated_at}

---

## Summary
- **Risk level:** **{risk_level}**
- **Runs in last {metrics.get("lookback_days", 35)} days:** {metrics.get("run_count", 0)}
- **Total distance:** {num(metrics.get("total_distance_km"), 1, " km")}
- **Total time:** {num(metrics.get("total_duration_min"), 0, " min")}
- **ACWR (distance):** {num(metrics.get("acwr_distance"), 2)}{acwr_note}
- **ACWR (duration):** {num(metrics.get("acwr_duration"), 2)}
- **Weekly distance trend:** {metrics.get("weekly_distance_trend", "unknown")}
- **Longest run share (last 7d):** {num((metrics.get("longest_run_pct") or 0) * 100, 0, "%")}
- **Rest days (last 14):** {metrics.get("rest_days_last_14", 0)}
- **Back-to-back run days (last 14):** {metrics.get("back_to_back_runs_last_14", 0)}
- **Easy / Moderate / Hard:** {num(metrics.get("easy_pct"), 1, "%")} / {num(metrics.get("moderate_pct"), 1, "%")} / {num(metrics.get("hard_pct"), 1, "%")}
- **Monotony:** {num(metrics.get("monotony_last_7"), 2)} | **Strain:** {num(metrics.get("strain_last_7"), 1)}

---

## Risk flags
{bullet_list(flags)}

### Flag details
{bullet_list(flag_details)}

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