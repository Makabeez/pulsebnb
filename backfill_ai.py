"""
Backfill AI classification on existing contracts.

Run once after upgrading to day 2 to classify the contracts that were
indexed before the AI pipeline was live.

Usage:
    cd /home/vps/pulsebnb
    source venv/bin/activate
    python backfill_ai.py [--max N] [--dry-run]
"""

import argparse
import os
import sqlite3
import sys
import time
import logging

from dotenv import load_dotenv

load_dotenv()

from ai_classifier import classify_with_ai

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("backfill")

DB_PATH = os.getenv("DB_PATH", "./data/pulsebnb.db")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max", type=int, default=300,
                    help="Max contracts to classify in this run (default 300)")
    ap.add_argument("--dry-run", action="store_true",
                    help="Print what would happen, don't write to DB")
    args = ap.parse_args()

    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=10000")
    rows = conn.execute(
        """SELECT address, contract_type, contract_name, verified
           FROM contracts
           WHERE ai_classified_at = 0
           ORDER BY deployed_at DESC LIMIT ?""",
        (args.max,),
    ).fetchall()

    if not rows:
        log.info("Nothing to backfill — all contracts already classified.")
        return

    log.info("Backfilling %d contracts at ~24 RPM (~%dmin total)",
             len(rows), max(1, len(rows) * 25 // 60 // 10))
    if args.dry_run:
        log.info("DRY RUN — no DB writes")

    real, noise, errors = 0, 0, 0
    start = time.time()

    for i, row in enumerate(rows, 1):
        addr = row["address"]
        label, reason, score = classify_with_ai({
            "address": addr,
            "contract_type": row["contract_type"],
            "contract_name": row["contract_name"],
            "verified": bool(row["verified"]),
        })
        if label is None:
            errors += 1
            log.warning("[%d/%d] ✗ %s — error, will retry next run",
                        i, len(rows), addr[:10])
        else:
            tag = "★" if label == "real" else " "
            log.info("[%d/%d] %s %s -> %s (%d) %s",
                     i, len(rows), tag, addr[:10], label, score,
                     (reason or "")[:50])
            if label == "real":
                real += 1
            else:
                noise += 1
            if not args.dry_run:
                conn.execute(
                    """UPDATE contracts
                       SET ai_label=?, ai_reason=?, ai_score=?, ai_classified_at=?
                       WHERE address=?""",
                    (label, reason, score, int(time.time()), addr),
                )
                if i % 10 == 0:
                    conn.commit()
        time.sleep(2.5)  # respect 30 RPM Cerebras free tier

    conn.commit()
    conn.close()
    elapsed = int(time.time() - start)
    log.info("=" * 60)
    log.info("DONE in %ds — real: %d, noise: %d, errors: %d",
             elapsed, real, noise, errors)
    log.info("Real ratio: %.1f%%",
             100 * real / (real + noise) if (real + noise) else 0)


if __name__ == "__main__":
    main()
