"""
Space ID resolver - reverse-resolves a .bnb name for an address.
Day 1: safe no-op stub.
Day 2: real implementation calling Space ID API or on-chain via web3.
"""

import logging

log = logging.getLogger("pulsebnb.spaceid")


def resolve_spaceid(address: str):
    """
    Returns a .bnb name string or None.

    Day 1 stub: returns None. Indexer keeps working without identity
    resolution; we'll just see raw 0x... addresses in the feed for day 1.
    """
    return None
