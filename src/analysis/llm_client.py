"""Factory for LLM client — supports direct Anthropic API and Amazon Bedrock."""
from __future__ import annotations

import anthropic

from src.config import settings


def get_llm_client():
    """Return an async Anthropic client, using Bedrock if configured."""
    if settings.USE_BEDROCK:
        return anthropic.AsyncAnthropicBedrock(aws_region=settings.AWS_REGION)
    return anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)


def get_model_id(default: str) -> str:
    """Return the Bedrock model ID if using Bedrock, otherwise the default."""
    if settings.USE_BEDROCK:
        return settings.BEDROCK_MODEL_ID
    return default
