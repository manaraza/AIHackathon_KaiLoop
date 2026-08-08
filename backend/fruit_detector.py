"""
Classical CV fruit detector for batch grading.

The trained SecondCrop model was trained on single-fruit, centered photos
(the Kaggle dataset). Fed a photo of a crate of 24 apples, it would just
return one score for the whole image -- not what anyone doing real
grading needs. This module finds individual round fruit-shaped regions
in a photo (Hough circle detection) so each one can be cropped and run
through the existing trained classifier separately.

This is genuinely a hard, unsolved-in-general computer vision problem
without labeled training data (a proper answer is a trained object
detector). What's here is a reasonable classical-CV approximation:
- Works well on well-separated, evenly-lit produce (a single layer laid
  out on a tray/box/table) -- tested at 24/24 correct count on a sample
  photo of apples in a box.
- Produces some false positives on cluttered/textured backgrounds
  (grass, woven baskets) since it has no training data to learn what
  "fruit" looks like vs. "background clutter."
- Undercounts heavily on densely packed bins where fruit overlaps with
  no visible boundary between pieces.
These are documented, known limitations, not silent failures -- the
caller decides what to do when detection finds 0 or 1 region (falls
back to treating the whole photo as one fruit).
"""

import cv2
import numpy as np

WORKING_MAX_DIM = 900
MIN_RADIUS_FRAC = 0.045
MAX_RADIUS_FRAC = 0.09
HOUGH_PARAM1 = 100
HOUGH_PARAM2 = 55
CROP_PADDING_FRAC = 0.15  # extra margin around each detected circle


def _decode(image_bytes: bytes) -> np.ndarray:
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not decode image")
    return img


def detect_fruit_boxes(image_bytes: bytes) -> list[dict]:
    """Returns a list of {x, y, w, h} bounding boxes in ORIGINAL image
    pixel coordinates (not the internal working-resolution coordinates)."""
    img = _decode(image_bytes)
    orig_h, orig_w = img.shape[:2]

    scale = WORKING_MAX_DIM / max(orig_h, orig_w)
    scale = min(scale, 1.0)  # never upscale
    work = cv2.resize(img, (int(orig_w * scale), int(orig_h * scale)))
    wh, ww = work.shape[:2]

    gray = cv2.cvtColor(work, cv2.COLOR_BGR2GRAY)
    blurred = cv2.medianBlur(gray, 9)

    min_r = int(MIN_RADIUS_FRAC * max(wh, ww))
    max_r = int(MAX_RADIUS_FRAC * max(wh, ww))
    min_dist = int(min_r * 1.5)

    circles = cv2.HoughCircles(
        blurred,
        cv2.HOUGH_GRADIENT,
        dp=1.5,
        minDist=min_dist,
        param1=HOUGH_PARAM1,
        param2=HOUGH_PARAM2,
        minRadius=min_r,
        maxRadius=max_r,
    )

    boxes = []
    if circles is not None:
        for x, y, r in circles[0]:
            pad_r = r * (1 + CROP_PADDING_FRAC)
            # map back to original image coordinates
            cx, cy, cr = x / scale, y / scale, pad_r / scale
            x0 = max(0, int(cx - cr))
            y0 = max(0, int(cy - cr))
            x1 = min(orig_w, int(cx + cr))
            y1 = min(orig_h, int(cy + cr))
            if x1 - x0 < 10 or y1 - y0 < 10:
                continue
            boxes.append({"x": x0, "y": y0, "w": x1 - x0, "h": y1 - y0})

    return boxes


def crop(image_bytes: bytes, box: dict) -> bytes:
    img = _decode(image_bytes)
    x, y, w, h = box["x"], box["y"], box["w"], box["h"]
    region = img[y : y + h, x : x + w]
    ok, encoded = cv2.imencode(".jpg", region)
    if not ok:
        raise ValueError("Could not encode cropped region")
    return encoded.tobytes()
