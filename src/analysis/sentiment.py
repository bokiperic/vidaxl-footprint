"""Claude-powered sentiment classification."""
from __future__ import annotations
import json
import logging

from src.analysis.llm_client import get_llm_client, get_model_id
from src.analysis.prompts import SENTIMENT_BATCH_PROMPT

logger = logging.getLogger(__name__)

BATCH_SIZE = 30


async def classify_sentiment_batch(reviews: list[dict]) -> list[dict]:
    """Classify sentiment for a batch of reviews using Claude.

    Each review dict should have: id, title, body, rating
    Returns list of: {id, sentiment, sentiment_score, topics}
    """
    client = get_llm_client()

    results = []
    for i in range(0, len(reviews), BATCH_SIZE):
        batch = reviews[i : i + BATCH_SIZE]
        reviews_json = json.dumps(
            [{"id": r["id"], "title": r.get("title", ""), "body": r.get("body", ""), "rating": r.get("rating")} for r in batch],
            indent=2,
        )

        prompt = SENTIMENT_BATCH_PROMPT.format(reviews_json=reviews_json)

        try:
            message = await client.messages.create(
                model=get_model_id("claude-sonnet-4-20250514"),
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
            )
            text = message.content[0].text.strip()
            # Strip markdown code fences if present
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            batch_results = json.loads(text)
            results.extend(batch_results)
        except Exception as e:
            logger.error(f"Sentiment classification failed for batch {i}: {e}")
            # Skip failed batch rather than crashing
            continue

    return results
