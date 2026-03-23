"""Mock analysis fallback when no Claude API key is configured."""
from __future__ import annotations
import random

COMMON_TOPICS = [
    "delivery delay", "missing parts", "damaged goods", "poor packaging",
    "wrong item", "slow customer service", "refund issues", "quality issues",
    "assembly difficulty", "good value", "fast shipping", "great product",
    "poor communication", "website issues", "return process",
]

NEGATIVE_KEYWORDS = ["terrible", "worst", "horrible", "broken", "damaged", "never", "scam", "awful", "waste", "disappointed"]
POSITIVE_KEYWORDS = ["great", "excellent", "perfect", "love", "amazing", "fast", "good", "happy", "recommend", "fantastic"]


def mock_sentiment(text: str | None) -> tuple[str, float, list[str]]:
    """Assign sentiment based on keyword matching with random fallback."""
    text_lower = (text or "").lower()

    neg_count = sum(1 for kw in NEGATIVE_KEYWORDS if kw in text_lower)
    pos_count = sum(1 for kw in POSITIVE_KEYWORDS if kw in text_lower)

    if neg_count > pos_count:
        sentiment = "NEG"
        score = max(0.05, 0.3 - neg_count * 0.05)
    elif pos_count > neg_count:
        sentiment = "POS"
        score = min(0.95, 0.7 + pos_count * 0.05)
    else:
        roll = random.random()
        if roll < 0.4:
            sentiment, score = "POS", round(random.uniform(0.6, 0.95), 2)
        elif roll < 0.7:
            sentiment, score = "NEU", round(random.uniform(0.35, 0.65), 2)
        else:
            sentiment, score = "NEG", round(random.uniform(0.05, 0.35), 2)

    topics = random.sample(COMMON_TOPICS, k=random.randint(1, 3))
    return sentiment, score, topics


def mock_top_complaints() -> list[dict]:
    return [
        {"theme": "Delivery Delays", "frequency": 342, "severity": "high", "example_quote": "Waited 3 weeks for delivery, no updates provided.", "category": "delivery"},
        {"theme": "Damaged/Broken Items", "frequency": 287, "severity": "high", "example_quote": "Product arrived with broken legs, completely unusable.", "category": "product_quality"},
        {"theme": "Missing Parts", "frequency": 198, "severity": "high", "example_quote": "Half the screws were missing from the package.", "category": "product_quality"},
        {"theme": "Poor Customer Service", "frequency": 176, "severity": "medium", "example_quote": "Waited on hold for 45 minutes, then got disconnected.", "category": "customer_service"},
        {"theme": "Refund Difficulties", "frequency": 154, "severity": "medium", "example_quote": "Still waiting for my refund after 6 weeks.", "category": "returns"},
        {"theme": "Wrong Item Sent", "frequency": 98, "severity": "medium", "example_quote": "Ordered a desk, received a completely different table.", "category": "delivery"},
        {"theme": "Poor Packaging", "frequency": 87, "severity": "medium", "example_quote": "Box was completely crushed, no padding inside.", "category": "delivery"},
        {"theme": "Assembly Instructions", "frequency": 76, "severity": "low", "example_quote": "Instructions were in a language I couldn't read.", "category": "product_quality"},
        {"theme": "Website/Ordering Issues", "frequency": 65, "severity": "low", "example_quote": "Website showed item in stock but order was cancelled.", "category": "website"},
        {"theme": "Product Not As Described", "frequency": 54, "severity": "medium", "example_quote": "Color was completely different from the photos.", "category": "product_quality"},
    ]


def mock_trends() -> dict:
    return {
        "trends": [
            {"trend": "Delivery complaints increasing", "direction": "up", "evidence": "20% increase in delivery-related reviews over last 3 months"},
            {"trend": "Product quality sentiment improving", "direction": "up", "evidence": "Fewer reports of damaged goods in recent reviews"},
            {"trend": "Customer service response time", "direction": "stable", "evidence": "Consistent complaints about wait times"},
            {"trend": "Return process satisfaction", "direction": "down", "evidence": "Growing number of refund delay complaints"},
        ],
        "seasonal_patterns": "Spike in negative reviews after major sale events (Black Friday, summer sales) likely due to fulfillment strain.",
        "source_specific": "Trustpilot DE and NL show higher satisfaction than UK profiles. PissedConsumer skews heavily negative by platform nature.",
        "recommendations": [
            {"priority": "high", "recommendation": "Implement proactive delivery tracking notifications to reduce 'where is my order' complaints", "expected_impact": "Could reduce delivery complaints by 30-40%"},
            {"priority": "high", "recommendation": "Improve packaging standards for fragile items — add quality checks before dispatch", "expected_impact": "Reduce damaged goods reports by 25%"},
            {"priority": "medium", "recommendation": "Create video assembly guides for top 50 products to supplement written instructions", "expected_impact": "Reduce assembly complaints and improve product satisfaction"},
            {"priority": "medium", "recommendation": "Streamline refund process with automated status updates at each stage", "expected_impact": "Improve customer retention and reduce repeat contacts"},
            {"priority": "low", "recommendation": "Add a real-time inventory system to prevent overselling during peak periods", "expected_impact": "Eliminate 'order cancelled' complaints related to stock issues"},
        ],
    }


def mock_monthly_sentiment() -> list[dict]:
    """Generate mock monthly sentiment data for trend charts."""
    import datetime
    months = []
    base = datetime.date(2025, 1, 1)
    for i in range(12):
        month = base.month + i
        year = base.year + (month - 1) // 12
        month = ((month - 1) % 12) + 1
        months.append({
            "month": f"{year}-{month:02d}",
            "positive": random.randint(40, 120),
            "neutral": random.randint(20, 60),
            "negative": random.randint(30, 90),
            "avg_score": round(random.uniform(0.35, 0.55), 2),
        })
    return months
