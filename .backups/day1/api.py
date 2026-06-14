"""
PulseBNB - Read API
FastAPI endpoints exposing the indexed BNB Chain data.
"""

import os
import math
import sqlite3
import time
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DB_PATH", "./data/pulsebnb.db")
WATCHLIST_CONTRACT = os.getenv("WATCHLIST_CONTRACT", "")

app = FastAPI(title="PulseBNB API", version="0.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def deployer_dict(row):
    return {
        "address": row["address"],
        "spaceid": row["spaceid"],
        "farcaster_username": row["farcaster_username"],
        "farcaster_fid": row["farcaster_fid"],
        "farcaster_pfp": row["farcaster_pfp"],
    }


def contract_dict(r):
    return {
        "address": r["address"],
        "deployer": {
            "address": r["deployer"],
            "spaceid": r["spaceid"],
            "farcaster_username": r["farcaster_username"],
            "farcaster_fid": r["farcaster_fid"],
            "farcaster_pfp": r["farcaster_pfp"],
        },
        "block_number": r["block_number"],
        "tx_hash": r["tx_hash"],
        "deployed_at": r["deployed_at"],
        "contract_type": r["contract_type"],
        "verified": bool(r["verified"]),
        "contract_name": r["contract_name"],
        "tx_count": r["tx_count"],
        "ai_label": r["ai_label"],
        "ai_reason": r["ai_reason"],
        "ai_score": r["ai_score"],
    }


@app.get("/health")
def health():
    return {"ok": True, "chain": "bnb", "ts": int(time.time())}


@app.get("/feed")
def feed(
    limit: int = Query(50, ge=1, le=200),
    label: str = Query(None, description="Filter by ai_label: real|fork|honeypot|scam"),
):
    conn = db()
    if label:
        rows = conn.execute(
            """SELECT c.*, d.spaceid, d.farcaster_username, d.farcaster_fid, d.farcaster_pfp
               FROM contracts c
               LEFT JOIN deployers d ON d.address = c.deployer
               WHERE c.ai_label = ?
               ORDER BY c.deployed_at DESC LIMIT ?""",
            (label, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            """SELECT c.*, d.spaceid, d.farcaster_username, d.farcaster_fid, d.farcaster_pfp
               FROM contracts c
               LEFT JOIN deployers d ON d.address = c.deployer
               ORDER BY c.deployed_at DESC LIMIT ?""",
            (limit,),
        ).fetchall()
    conn.close()
    return {"items": [contract_dict(r) for r in rows]}


@app.get("/leaderboard")
def leaderboard(window: str = "7d", limit: int = Query(50, ge=1, le=200)):
    """Top builders ranked by transparent score (0.4*deploys + 0.4*log(tx) + 0.2*verified_ratio)."""
    days = {"1d": 1, "7d": 7, "30d": 30, "all": 36500}.get(window, 7)
    cutoff = int(time.time()) - days * 86400

    conn = db()
    rows = conn.execute(
        """SELECT c.deployer,
                  COUNT(*) AS n_contracts,
                  SUM(c.verified) AS n_verified,
                  SUM(c.tx_count) AS total_tx,
                  MAX(c.deployed_at) AS last_deploy,
                  d.spaceid, d.farcaster_username, d.farcaster_fid, d.farcaster_pfp
           FROM contracts c
           LEFT JOIN deployers d ON d.address = c.deployer
           WHERE c.deployed_at >= ?
           GROUP BY c.deployer
           ORDER BY n_contracts DESC, total_tx DESC
           LIMIT ?""",
        (cutoff, limit),
    ).fetchall()
    conn.close()

    items = []
    for r in rows:
        n = r["n_contracts"] or 0
        v = r["n_verified"] or 0
        tx = r["total_tx"] or 0
        verified_ratio = (v / n) if n else 0
        score = round(0.4 * n + 0.4 * math.log1p(tx) + 0.2 * (verified_ratio * 10), 2)
        items.append({
            "address": r["deployer"],
            "spaceid": r["spaceid"],
            "farcaster_username": r["farcaster_username"],
            "farcaster_fid": r["farcaster_fid"],
            "farcaster_pfp": r["farcaster_pfp"],
            "n_contracts": n,
            "n_verified": v,
            "total_tx": tx,
            "verified_ratio": round(verified_ratio, 3),
            "last_deploy": r["last_deploy"],
            "score": score,
        })
    items.sort(key=lambda x: x["score"], reverse=True)
    return {"window": window, "items": items}


@app.get("/hot")
def hot(limit: int = Query(20, ge=1, le=100)):
    cutoff = int(time.time()) - 7 * 86400
    conn = db()
    rows = conn.execute(
        """SELECT c.*, d.spaceid, d.farcaster_username, d.farcaster_fid, d.farcaster_pfp
           FROM contracts c
           LEFT JOIN deployers d ON d.address = c.deployer
           WHERE c.deployed_at >= ?
           ORDER BY c.tx_count DESC, c.deployed_at DESC
           LIMIT ?""",
        (cutoff, limit),
    ).fetchall()
    conn.close()
    return {"items": [contract_dict(r) for r in rows]}


@app.get("/builder/{address}")
def builder(address: str):
    address = address.lower()
    conn = db()
    d = conn.execute("SELECT * FROM deployers WHERE address=?", (address,)).fetchone()
    if not d:
        conn.close()
        return {"error": "not found"}
    contracts = conn.execute(
        "SELECT * FROM contracts WHERE deployer=? ORDER BY deployed_at DESC LIMIT 200",
        (address,),
    ).fetchall()
    conn.close()
    return {
        "deployer": deployer_dict(d) | {"address": address},
        "contracts": [dict(r) for r in contracts],
        "stats": {
            "total_contracts": len(contracts),
            "verified": sum(1 for c in contracts if c["verified"]),
        },
    }


@app.get("/stats")
def stats():
    conn = db()
    total = conn.execute("SELECT COUNT(*) AS n FROM contracts").fetchone()["n"]
    last_24h = conn.execute(
        "SELECT COUNT(*) AS n FROM contracts WHERE deployed_at >= ?",
        (int(time.time()) - 86400,),
    ).fetchone()["n"]
    last_7d = conn.execute(
        "SELECT COUNT(*) AS n FROM contracts WHERE deployed_at >= ?",
        (int(time.time()) - 7 * 86400,),
    ).fetchone()["n"]
    builders_7d = conn.execute(
        "SELECT COUNT(DISTINCT deployer) AS n FROM contracts WHERE deployed_at >= ?",
        (int(time.time()) - 7 * 86400,),
    ).fetchone()["n"]
    ai_classified = conn.execute(
        "SELECT COUNT(*) AS n FROM contracts WHERE ai_classified_at > 0"
    ).fetchone()["n"]
    last_block = conn.execute("SELECT value FROM meta WHERE key='last_block'").fetchone()
    conn.close()
    return {
        "chain": "bnb",
        "total_contracts": total,
        "contracts_24h": last_24h,
        "contracts_7d": last_7d,
        "active_builders_7d": builders_7d,
        "ai_classified": ai_classified,
        "last_indexed_block": int(last_block["value"]) if last_block else None,
        "watchlist_contract": WATCHLIST_CONTRACT or None,
    }


@app.get("/watchlist/{address}")
def watchlist(address: str):
    """Who is watching this contract/builder? Day 5+ feature."""
    return {
        "address": address.lower(),
        "watchers": [],
        "note": "Watchlist contract not yet deployed (day 5-6).",
    }
