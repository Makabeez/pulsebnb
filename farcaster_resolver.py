"""
Farcaster identity resolver via Neynar bulk endpoint.

Ported from Base Builder Radar. Uses same API key (cross-chain identity).
Bulk-resolves up to 350 addresses per call to minimize API spend.
"""

import os
import logging
import httpx

log = logging.getLogger("pulsebnb.farcaster")

NEYNAR_API_KEY = os.getenv("NEYNAR_API_KEY", "")
NEYNAR_API = "https://api.neynar.com/v2/farcaster"

_client = httpx.Client(timeout=15.0)


def resolve_farcaster_bulk(addresses):
    """
    Bulk-resolve Farcaster users for a list of addresses.
    Returns dict: {lowercase_address: {fid, username, pfp}}
    """
    if not NEYNAR_API_KEY or not addresses:
        return {}
    try:
        r = _client.get(
            f"{NEYNAR_API}/user/bulk-by-address",
            headers={
                "x-api-key": NEYNAR_API_KEY,
                "x-neynar-experimental": "false",
            },
            params={"addresses": ",".join(addresses)},
        )
        if r.status_code != 200:
            log.warning("neynar bulk HTTP %d", r.status_code)
            return {}
        data = r.json()
        result = {}
        for addr, users in data.items():
            if users:
                u = users[0]
                result[addr.lower()] = {
                    "fid": u.get("fid"),
                    "username": u.get("username"),
                    "pfp": u.get("pfp_url"),
                }
        return result
    except Exception as e:
        log.warning("neynar bulk failed: %s", e)
        return {}
