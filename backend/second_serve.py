"""
Second Serve — near-expiry retail inventory module.

Unlike SecondCrop and ScrapSense, this one doesn't need a photo or a
trained model at all — the pitch's value prop for this module is "no new
hardware, no manual logging," working straight off inventory data a
retailer already has (SKU, expiry date, quantity on hand). That makes
this genuinely how a production version would work too, not a
hackathon stand-in for something fancier.

Rule: the closer an item is to its expiry date, the more urgent the
action needed. Watch = keep an eye on it. Near-expiry = mark it down to
move it while it's still sellable. Urgent/expired = it won't sell in
time, route it to rescue instead of letting it become landfill.
"""

from datetime import date

MARKDOWN_PCT = {
    "urgent": 50,
    "near_expiry": 30,
    "watch": 0,
    "ok": 0,
}


def classify_item(expiry_date: date, today: date | None = None) -> dict:
    today = today or date.today()
    days_left = (expiry_date - today).days

    if days_left < 0:
        urgency, route = "expired", "rescue"
    elif days_left <= 1:
        urgency, route = "urgent", "rescue"
    elif days_left <= 3:
        urgency, route = "near_expiry", "markdown"
    elif days_left <= 7:
        urgency, route = "watch", "monitor"
    else:
        urgency, route = "ok", "none"

    return {
        "days_left": days_left,
        "urgency": urgency,
        "route": route,
        "suggested_markdown_pct": MARKDOWN_PCT.get(urgency, 0),
    }
