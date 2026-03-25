"""Theme extraction and aggregation using Claude."""
from __future__ import annotations
import json
import logging

from src.analysis.llm_client import get_llm_client, get_model_id
from src.analysis.prompts import THEME_AGGREGATION_PROMPT

logger = logging.getLogger(__name__)


async def aggregate_themes(topic_frequencies: dict[str, int], total_reviews: int) -> list[dict]:
    """Use Claude to merge synonymous topics and rank top complaints."""
    client = get_llm_client()

    freq_text = "\n".join(f"- {topic}: {count}" for topic, count in sorted(topic_frequencies.items(), key=lambda x: -x[1])[:50])

    prompt = THEME_AGGREGATION_PROMPT.format(
        topic_frequencies=freq_text,
        total_reviews=total_reviews,
    )

    try:
        message = await client.messages.create(
            model=get_model_id("claude-sonnet-4-20250514"),
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        text = message.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        return json.loads(text)
    except Exception as e:
        logger.error(f"Theme aggregation failed: {e}")
        return []
