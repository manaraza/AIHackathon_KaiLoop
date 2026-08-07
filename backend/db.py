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
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS scrapsense_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                dish_id TEXT NOT NULL,
                filename TEXT,
                waste_ratio REAL NOT NULL,
                waste_level TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS secondserve_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                sku TEXT,
                name TEXT NOT NULL,
                expiry_date TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                days_left INTEGER NOT NULL,
                urgency TEXT NOT NULL,
                route TEXT NOT NULL,
                suggested_markdown_pct INTEGER NOT NULL
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


def log_scrapsense(dish_id: str, filename: str, waste_ratio: float, waste_level: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO scrapsense_logs (timestamp, dish_id, filename, waste_ratio, waste_level) "
            "VALUES (?, ?, ?, ?, ?)",
            (datetime.now(timezone.utc).isoformat(), dish_id, filename, waste_ratio, waste_level),
        )
        conn.commit()


def get_scrapsense_report() -> list[dict]:
    from scrapsense import (
        FLAG_AVG_RATIO_THRESHOLD,
        MIN_SAMPLES_TO_FLAG,
        suggested_portion_cut_pct,
    )

    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT dish_id, COUNT(*), AVG(waste_ratio),
                   SUM(CASE WHEN waste_level = 'high_leftover' THEN 1 ELSE 0 END)
            FROM scrapsense_logs
            GROUP BY dish_id
            ORDER BY AVG(waste_ratio) DESC
            """
        ).fetchall()

    report = []
    for dish_id, count, avg_ratio, high_count in rows:
        avg_ratio = round(avg_ratio, 4)
        flagged = count >= MIN_SAMPLES_TO_FLAG and avg_ratio >= FLAG_AVG_RATIO_THRESHOLD
        report.append(
            {
                "dish_id": dish_id,
                "plates_logged": count,
                "avg_waste_ratio": avg_ratio,
                "high_leftover_count": high_count,
                "flagged_over_portioned": flagged,
                "suggested_portion_cut_pct": suggested_portion_cut_pct(avg_ratio) if flagged else 0,
            }
        )
    return report


def log_secondserve(
    sku: str,
    name: str,
    expiry_date: str,
    quantity: int,
    unit_price: float,
    days_left: int,
    urgency: str,
    route: str,
    suggested_markdown_pct: int,
) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO secondserve_logs
                (timestamp, sku, name, expiry_date, quantity, unit_price,
                 days_left, urgency, route, suggested_markdown_pct)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now(timezone.utc).isoformat(),
                sku,
                name,
                expiry_date,
                quantity,
                unit_price,
                days_left,
                urgency,
                route,
                suggested_markdown_pct,
            ),
        )
        conn.commit()


def get_secondserve_report() -> dict:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT id, sku, name, expiry_date, quantity, unit_price,
                   days_left, urgency, route, suggested_markdown_pct
            FROM secondserve_logs
            ORDER BY days_left ASC
            """
        ).fetchall()

    items = []
    value_at_risk = 0.0
    counts = {"expired": 0, "urgent": 0, "near_expiry": 0, "watch": 0, "ok": 0}
    for row in rows:
        (_id, sku, name, expiry_date, quantity, unit_price,
         days_left, urgency, route, markdown_pct) = row
        items.append(
            {
                "sku": sku,
                "name": name,
                "expiry_date": expiry_date,
                "quantity": quantity,
                "unit_price": unit_price,
                "days_left": days_left,
                "urgency": urgency,
                "route": route,
                "suggested_markdown_pct": markdown_pct,
            }
        )
        counts[urgency] = counts.get(urgency, 0) + 1
        if urgency in ("expired", "urgent", "near_expiry"):
            value_at_risk += quantity * unit_price

    return {
        "items": items,
        "counts_by_urgency": counts,
        "estimated_value_at_risk": round(value_at_risk, 2),
    }
