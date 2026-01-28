from __future__ import annotations
import os
from typing import Any, Dict, Tuple
from openai import OpenAI
from app.llm.prompt import SYSTEM_PROMPT, build_user_prompt


def _split_sections(text: str) -> Tuple[str, str, str]:
    def find(label: str) -> int:
        idx = text.find(label)
        if idx == -1:
            raise ValueError(f"Missing section header: {label}")
        return idx
    
    i1 = find('INTERPRETATION:')
    i2 = find('RECOMMENDATIONS:')
    i3 = find('TAKEAWAYS:')

    interpretation = text[i1 + len('INTERPRETATION:'):i2].strip()
    recommendations = text[i2 + len('RECOMMENDATIONS:'):i3].strip()
    takeaways = text[i3 + len('TAKEAWAYS:'):].strip()
    return interpretation, recommendations, takeaways

def generate_narrative(metrics: Dict[str, Any], risk: Dict[str, Any], model: str = "gpt-4o-mini") -> Dict[str, str]:
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise RuntimeError('OPENAI_API_KEY is not set.')
    
    client = OpenAI(api_key = api_key)

    resp = client.chat.completions.create(
        model = model,
        messages = [
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': build_user_prompt(metrics, risk)},
        ],
        temperature = 0.4,
    )

    text = resp.choices[0].message.content or ''
    interpretation, recommendations, takeaways = _split_sections(text)

    return {
        'interpretation': interpretation,
        'recommendations': recommendations,
        'takeaways': takeaways,
        'raw': text,
    }