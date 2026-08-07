"""
ScrapSense — mocked plate-waste module.

There's no training dataset for plate waste (unlike SecondCrop's produce
grading), so instead of a trained classifier this uses a lightweight
heuristic: food tends to be more saturated/colorful than a plate, so the
fraction of high-saturation pixels in the photo is a rough proxy for how
much food is still sitting on it. This is intentionally the "mocked"
module per the hackathon plan — real, running code, just not ML-trained.
Swap estimate_waste_ratio() for a trained model later without touching
anything downstream (aggregation, flagging, API shape all stay the same).
"""

from io import BytesIO

import numpy as np
from PIL import Image

# (label, [low, high) bounds on waste_ratio)
WASTE_LEVELS = [
    ("clean_plate", 0.0, 0.15),
    ("partial_leftover", 0.15, 0.45),
    ("high_leftover", 0.45, 1.01),
]

SATURATION_THRESHOLD = 60  # 0-255; pixels above this count as "food"

# A dish needs at least this many logged plates before it's eligible to
# be flagged — one bad photo shouldn't trigger a menu change.
MIN_SAMPLES_TO_FLAG = 3
FLAG_AVG_RATIO_THRESHOLD = 0.35


def estimate_waste_ratio(image_bytes: bytes) -> float:
    img = Image.open(BytesIO(image_bytes)).convert("RGB").resize((300, 300))
    hsv = np.array(img.convert("HSV"))
    saturation = hsv[:, :, 1]
    food_pixel_fraction = float((saturation > SATURATION_THRESHOLD).mean())
    return round(food_pixel_fraction, 4)


def waste_level_for(ratio: float) -> str:
    for label, low, high in WASTE_LEVELS:
        if low <= ratio < high:
            return label
    return "high_leftover"


def analyze_plate(image_bytes: bytes) -> dict:
    ratio = estimate_waste_ratio(image_bytes)
    return {"waste_ratio": ratio, "waste_level": waste_level_for(ratio)}


def suggested_portion_cut_pct(avg_ratio: float) -> int:
    """Rough, conservative suggestion: don't cut the full observed waste
    ratio, cut ~80% of it, so portions shrink without risking under-serving."""
    return round(avg_ratio * 100 * 0.8)
