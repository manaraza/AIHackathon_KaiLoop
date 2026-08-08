"""
ScrapSense — mocked plate-waste module.

There's no training dataset for plate waste (unlike SecondCrop's produce
grading), so instead of a trained classifier this uses a lightweight
heuristic instead. This is intentionally the "mocked" module per the
hackathon plan -- real, running code, just not ML-trained. Swap
estimate_waste_ratio() for a trained model later without touching
anything downstream (aggregation, flagging, API shape all stay the same).

Two signals combine to flag a pixel as "food":
  1. High color saturation -- catches sauced/colorful food, which is most
     food. This alone was the first version, and it worked well except
     for one systematic blind spot:
  2. Pale food (rice, mashed potato, plain pasta) has almost no color
     saturation, so signal 1 misses it. To catch it, pixels that are
     low-saturation but locally textured (grain-by-grain brightness
     variation, unlike a smooth ceramic plate) also count as food --
     as long as they're not too dark (shadow) or too bright (glare),
     which otherwise get misread as texture too.
Calibrated against real plate photos, including one of white rice that
signal 1 alone underestimated by roughly half.
"""

import cv2
import numpy as np

# (label, [low, high) bounds on waste_ratio)
WASTE_LEVELS = [
    ("clean_plate", 0.0, 0.15),
    ("partial_leftover", 0.15, 0.45),
    ("high_leftover", 0.45, 1.01),
]

SATURATION_THRESHOLD = 60  # 0-255; pixels above this count as "colorful food"
TEXTURE_THRESHOLD = 90     # local Laplacian energy; above this counts as "textured"
VALUE_LOW = 50             # exclude near-black shadow from the texture check
VALUE_HIGH = 235           # exclude blown-out glare/reflections from the texture check
WORKING_SIZE = (300, 300)

# A dish needs at least this many logged plates before it's eligible to
# be flagged — one bad photo shouldn't trigger a menu change.
MIN_SAMPLES_TO_FLAG = 3
FLAG_AVG_RATIO_THRESHOLD = 0.35


def estimate_waste_ratio(image_bytes: bytes) -> float:
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not decode image")
    img = cv2.resize(img, WORKING_SIZE)

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    saturation = hsv[:, :, 1]
    value = hsv[:, :, 2]

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    texture = cv2.blur(np.abs(cv2.Laplacian(gray, cv2.CV_64F, ksize=3)), (5, 5))

    is_colorful = saturation > SATURATION_THRESHOLD
    plausible_brightness = (value > VALUE_LOW) & (value < VALUE_HIGH)
    is_textured_pale = (saturation <= SATURATION_THRESHOLD) & (texture > TEXTURE_THRESHOLD) & plausible_brightness

    food_mask = is_colorful | is_textured_pale
    return round(float(food_mask.mean()), 4)


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
