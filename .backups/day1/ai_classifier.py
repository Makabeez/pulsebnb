"""
AI classifier - routes contract metadata through Joe's local LiteLLM router.
Day 1: safe no-op stub (returns None tuple, won't break the indexer).
Day 2: full LLM-backed classification with reasoning + 0-100 score.
"""

import os
import logging

log = logging.getLogger("pulsebnb.ai")

LITELLM_URL = os.getenv("LITELLM_URL", "http://127.0.0.1:4000")
LITELLM_MODEL = os.getenv("LITELLM_MODEL", "enrichment")
LITELLM_API_KEY = os.getenv("LITELLM_API_KEY", "")


def classify_with_ai(contract: dict):
    """
    Returns (label, reason, score):
      label  : 'real' | 'fork' | 'honeypot' | 'scam' | 'unknown' | None
      reason : 1-sentence rationale
      score  : 0-100 confidence

    Day 1 stub: returns (None, None, 0) so indexer keeps running and
    ai_classified_at stays 0, meaning rows get re-tried once we ship day 2.
    """
    return (None, None, 0)
