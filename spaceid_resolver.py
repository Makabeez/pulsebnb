"""
Space ID .bnb name resolver for BNB Chain.

Uses Space ID's public REST endpoint for reverse lookup. Falls back gracefully
if the API is unreachable - identity resolution is enrichment, not critical path.
"""

import os
import logging
import httpx

log = logging.getLogger("pulsebnb.spaceid")

# Space ID public API - returns primary domain for an address
# Confirmed working April 2026 per Space ID docs
SPACEID_API = "https://api.prd.space.id/v1/getName"

_client = httpx.Client(timeout=8.0)


def resolve_spaceid(address: str):
    """
    Returns the primary .bnb domain for an address, or None.

    Examples of returned values: 'vitalik.bnb', 'cz.bnb', None
    """
    if not address:
        return None
    try:
        r = _client.get(
            SPACEID_API,
            params={"tld": "bnb", "address": address},
        )
        if r.status_code != 200:
            return None
        data = r.json()
        # Response shape: {"code": 0, "name": "foo.bnb"} on hit, name="" on miss
        name = (data.get("name") or "").strip()
        return name or None
    except Exception as e:
        log.debug("spaceid lookup failed for %s: %s", address[:10], e)
        return None
