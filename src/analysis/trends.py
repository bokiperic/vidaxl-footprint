"""Trend detection and actionable insights using Claude."""
from __future__ import annotations
import json
import logging

import anthropic

from src.analysis.prompts import TREND_DETECTION_PROMPT
from src.config import settings

logger = logging.getLogger(__name__)


async def detect_trends(
    monthly_data: list[dict],
    top_complaints: list[dict],
    total_reviews: int,
    avg_rating: float,
    sources: list[str],
) -> dict:
    """Use Claude to detect trends and generate business insights."""
    client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    prompt = TREND_DETECTION_PROMPT.format(
        monthly_data=json.dumps(monthly_data, indent=2),
        top_complaints=json.dumps(top_complaints, indent=2),
        total_reviews=total_reviews,
        avg_rating=round(avg_rating, 2),
        sources=", ".join(sources),
    )

    try:
        message = await client.messages.create(
            model="claude-opus-4-20250514",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        text = message.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        return json.loads(text)
    except Exception as e:
        logger.error(f"Trend detection failed: {e}")
        return {}
