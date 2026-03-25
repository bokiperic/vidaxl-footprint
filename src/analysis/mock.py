"""Mock analysis fallback when no Claude API key is configured."""
from __future__ import annotations
import random

COMMON_TOPICS = [
    "sizing issues", "fabric quality", "bra fit", "delivery delay",
    "wrong size", "slow customer service", "refund issues", "comfort",
    "color mismatch", "good value", "fast shipping", "great design",
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
        {"theme": "Sizing Inconsistency", "frequency": 342, "severity": "high", "example_quote": "Ordered my usual size but it was way too small, sizing is all over the place.", "category": "product_quality"},
        {"theme": "Fabric Quality Decline", "frequency": 287, "severity": "high", "example_quote": "Material feels cheap and started pilling after one wash.", "category": "product_quality"},
        {"theme": "Bra Fit Issues", "frequency": 198, "severity": "high", "example_quote": "The bra cups are shaped oddly and don't provide proper support.", "category": "product_quality"},
        {"theme": "Delivery Delays", "frequency": 176, "severity": "medium", "example_quote": "Waited 2 weeks for delivery, no tracking updates provided.", "category": "delivery"},
        {"theme": "Refund Difficulties", "frequency": 154, "severity": "medium", "example_quote": "Still waiting for my refund after 4 weeks of returning items.", "category": "returns"},
        {"theme": "Poor Customer Service", "frequency": 132, "severity": "medium", "example_quote": "Email support took 10 days to respond with a generic reply.", "category": "customer_service"},
        {"theme": "Return Process Complexity", "frequency": 98, "severity": "medium", "example_quote": "Return shipping costs are too high and the process is confusing.", "category": "returns"},
        {"theme": "Color Mismatch", "frequency": 87, "severity": "low", "example_quote": "The color looked completely different from the website photos.", "category": "product_quality"},
        {"theme": "Website/Ordering Issues", "frequency": 65, "severity": "low", "example_quote": "Website showed item in stock but order was cancelled next day.", "category": "website"},
        {"theme": "Comfort Issues", "frequency": 54, "severity": "medium", "example_quote": "The underwire digs in after just an hour of wearing.", "category": "product_quality"},
    ]


def mock_trends() -> dict:
    return {
        "trends": [
            {"trend": "Sizing complaints increasing", "direction": "up", "evidence": "25% increase in sizing-related reviews over last 3 months"},
            {"trend": "Fabric quality sentiment declining", "direction": "down", "evidence": "More reports of poor material quality in recent collections"},
            {"trend": "Customer service response time", "direction": "stable", "evidence": "Consistent complaints about slow email support"},
            {"trend": "Return process satisfaction", "direction": "down", "evidence": "Growing number of complaints about return shipping costs"},
        ],
        "seasonal_patterns": "Spike in negative reviews after major sale events (Black Friday, summer sales) likely due to fulfillment strain and sizing issues with sale items.",
        "source_specific": "Trustpilot DE and NL show higher satisfaction than COM profile. PissedConsumer skews heavily negative by platform nature.",
        "recommendations": [
            {"priority": "high", "recommendation": "Standardize sizing across all product lines and add detailed size guides with measurements", "expected_impact": "Could reduce sizing complaints by 30-40%"},
            {"priority": "high", "recommendation": "Improve fabric quality control — enforce minimum material standards for all collections", "expected_impact": "Reduce quality complaints by 25%"},
            {"priority": "medium", "recommendation": "Offer free returns or prepaid return labels to reduce friction in the return process", "expected_impact": "Improve customer retention and reduce negative reviews about returns"},
            {"priority": "medium", "recommendation": "Streamline refund process with automated status updates at each stage", "expected_impact": "Improve customer satisfaction and reduce repeat contacts"},
            {"priority": "low", "recommendation": "Add virtual try-on or fit recommendation tool to reduce sizing mismatches", "expected_impact": "Reduce return rates and improve purchase confidence"},
        ],
    }


def mock_best_products() -> list[dict]:
    return [
        {"product": "Luxe Lace Padded Bra", "avg_rating": 4.8, "review_count": 47},
        {"product": "Cotton Comfort Brief 3-Pack", "avg_rating": 4.7, "review_count": 63},
        {"product": "Silk Touch Nightdress", "avg_rating": 4.6, "review_count": 29},
        {"product": "Sport Seamless Leggings", "avg_rating": 4.6, "review_count": 38},
        {"product": "Modal Soft Pyjama Set", "avg_rating": 4.5, "review_count": 41},
        {"product": "Invisible T-Shirt Bra", "avg_rating": 4.5, "review_count": 55},
        {"product": "Ribbed Cotton Hipster", "avg_rating": 4.4, "review_count": 34},
        {"product": "Satin Kimono Robe", "avg_rating": 4.4, "review_count": 22},
        {"product": "Micro Mesh Thong 5-Pack", "avg_rating": 4.3, "review_count": 48},
        {"product": "Cozy Fleece Lounge Hoodie", "avg_rating": 4.3, "review_count": 31},
    ]


def mock_worst_products() -> list[dict]:
    return [
        {"product": "Strapless Push-Up Bra", "avg_rating": 2.1, "review_count": 36},
        {"product": "Shapewear High-Waist Brief", "avg_rating": 2.3, "review_count": 28},
        {"product": "Adhesive Nipple Covers", "avg_rating": 2.4, "review_count": 19},
        {"product": "Backless Body Suit", "avg_rating": 2.5, "review_count": 23},
        {"product": "Lace Suspender Belt", "avg_rating": 2.6, "review_count": 15},
        {"product": "Underwire Plunge Bra", "avg_rating": 2.7, "review_count": 42},
        {"product": "String Bikini Bottom", "avg_rating": 2.8, "review_count": 21},
        {"product": "Halterneck Swimsuit", "avg_rating": 2.9, "review_count": 17},
        {"product": "Corset Waist Trainer", "avg_rating": 3.0, "review_count": 26},
        {"product": "Lace-Up Bodysuit", "avg_rating": 3.0, "review_count": 20},
    ]


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
