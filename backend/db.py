"""
Tiny SQLite log of every grading call, used to power /impact.
"""

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "secondcrop.db"

# Rough average weight per produce item, used only to turn "N items graded"
# into a friendlier "kg diverted from landfill" figure for the impact
# dashboard. Placeholder until real per-item weights are available.
AVG_ITEM_WEIGHT_KG = 0.15


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS gradings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                filename TEXT,
                score REAL NOT NULL,
                grade TEXT NOT NULL,
                route TEXT NOT NULL
            )
            """
        )
        conn.commit()


def log_grading(filename: str, score: float, grade: str, route: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO gradings (timestamp, filename, score, grade, route) "
            "VALUES (?, ?, ?, ?, ?)",
            (datetime.now(timezone.utc).isoformat(), filename, score, grade, route),
        )
        conn.commit()


def get_impact_summary() -> dict:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT grade, COUNT(*) FROM gradings GROUP BY grade"
        ).fetchall()
        total = conn.execute("SELECT COUNT(*) FROM gradings").fetchone()[0]

    counts = {"A": 0, "B": 0, "C": 0}
    for grade, count in rows:
        counts[grade] = count

    total_kg = round(total * AVG_ITEM_WEIGHT_KG, 2)
    retail_kg = round(counts["A"] * AVG_ITEM_WEIGHT_KG, 2)
    review_kg = round(counts["B"] * AVG_ITEM_WEIGHT_KG, 2)
    rescue_kg = round(counts["C"] * AVG_ITEM_WEIGHT_KG, 2)

    return {
        "total_items_graded": total,
        "counts_by_grade": counts,
        "estimated_kg_diverted_from_landfill": total_kg,
        "breakdown_kg": {
            "retail": retail_kg,
            "processing_review": review_kg,
            "rescue": rescue_kg,
        },
    }
