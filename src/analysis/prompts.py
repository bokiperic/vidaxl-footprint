SENTIMENT_BATCH_PROMPT = """Analyze the following customer reviews and for each one provide:
1. sentiment: "POS", "NEU", or "NEG"
2. sentiment_score: float 0.0 (most negative) to 1.0 (most positive)
3. topics: list of 1-5 topic tags (e.g. "delivery delay", "missing parts", "good quality", "poor packaging")

Return a JSON array where each element has: {"id": <review_id>, "sentiment": "...", "sentiment_score": ..., "topics": [...]}

Reviews:
{reviews_json}

Return ONLY the JSON array, no other text."""

THEME_AGGREGATION_PROMPT = """Given these topic tags extracted from {total_reviews} customer reviews of Hunkemoller (European lingerie & underwear retailer), merge synonymous topics and rank the top 10 complaint themes.

Topic frequencies:
{topic_frequencies}

For each theme provide:
- theme: merged theme name
- frequency: total count
- severity: "high", "medium", or "low"
- example_quote: a representative example (use one from the provided data if available)
- category: one of "delivery", "product_quality", "customer_service", "pricing", "website", "returns", "other"

Return a JSON array of the top 10 themes, sorted by frequency descending. Return ONLY the JSON array."""

TREND_DETECTION_PROMPT = """Analyze the following monthly sentiment and topic data from Hunkemoller customer reviews to detect trends and generate actionable business insights.

Monthly data:
{monthly_data}

Top complaint themes:
{top_complaints}

Total reviews analyzed: {total_reviews}
Average rating: {avg_rating}
Sources covered: {sources}

Provide:
1. trends: array of 3-5 notable trends (each with "trend", "direction" up/down/stable, "evidence")
2. seasonal_patterns: any seasonal observations
3. source_specific: notable differences between review sources
4. recommendations: exactly 5 actionable business recommendations (each with "priority" high/medium/low, "recommendation", "expected_impact")

Return as a JSON object with these 4 keys. Return ONLY JSON."""

ARTICLE_SUMMARY_PROMPT = """Summarize this article about Hunkemoller. Extract:
- summary: 2-3 sentence summary
- sentiment: "POS", "NEU", or "NEG"
- key_topics: list of topic tags

Article title: {title}
Article body: {body}

Return as a JSON object. Return ONLY JSON."""
