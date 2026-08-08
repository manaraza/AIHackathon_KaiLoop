"""
Kai Loop backend — SecondCrop, ScrapSense, and Second Serve.

Endpoints:
    POST /grade               — produce photo -> grade + route + score
    POST /grade-batch          — photo with multiple fruits -> per-fruit grades
    GET  /impact                — SecondCrop aggregate stats
    POST /scrapsense/log          — plate photo -> waste level
    GET  /scrapsense/report        — per-dish flagging report
    POST /secondserve/scan          — inventory item -> urgency + route
    GET  /secondserve/report         — near-expiry inventory report
    GET  /health                      — quick liveness check
"""

from datetime import date, datetime
from io import BytesIO

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image

from db import (
    get_impact_summary,
    get_scrapsense_report,
    get_secondserve_report,
    init_db,
    log_grading,
    log_scrapsense,
    log_secondserve,
)
from fruit_detector import crop, detect_fruit_boxes
from model_loader import grade_image
from scrapsense import analyze_plate
from second_serve import classify_item

app = FastAPI(title="Kai Loop — SecondCrop API")

# Wide open for hackathon dev; tighten before anything resembling prod.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/grade")
async def grade(file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. "
                   f"Use JPEG, PNG, or WebP.",
        )

    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Empty file")

    try:
        result = grade_image(image_bytes)
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))

    log_grading(
        filename=file.filename,
        score=result["score"],
        grade=result["grade"],
        route=result["route"],
    )
    return result


@app.get("/impact")
def impact():
    return get_impact_summary()


@app.post("/grade-batch")
async def grade_batch(file: UploadFile = File(...)):
    """Grades every fruit detected in a photo, not just one. Falls back to
    single-fruit grading if detection finds 0 or 1 region (e.g. the photo
    already is a single close-up fruit -- same behavior as /grade)."""
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. "
                   f"Use JPEG, PNG, or WebP.",
        )

    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Empty file")

    try:
        img = Image.open(BytesIO(image_bytes))
        img_w, img_h = img.size
    except Exception:
        raise HTTPException(status_code=400, detail="Could not read image")

    try:
        boxes = detect_fruit_boxes(image_bytes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if len(boxes) <= 1:
        # Not enough distinct regions found -- treat the whole photo as
        # one fruit, same as /grade.
        try:
            result = grade_image(image_bytes)
        except FileNotFoundError as e:
            raise HTTPException(status_code=503, detail=str(e))
        log_grading(filename=file.filename, score=result["score"],
                    grade=result["grade"], route=result["route"])
        items = [{"box": {"x": 0, "y": 0, "w": img_w, "h": img_h}, **result}]
    else:
        items = []
        for box in boxes:
            try:
                crop_bytes = crop(image_bytes, box)
                result = grade_image(crop_bytes)
            except (FileNotFoundError, ValueError) as e:
                raise HTTPException(status_code=503 if isinstance(e, FileNotFoundError) else 400, detail=str(e))
            log_grading(filename=file.filename, score=result["score"],
                        grade=result["grade"], route=result["route"])
            items.append({"box": box, **result})

    counts = {"A": 0, "B": 0, "C": 0}
    for item in items:
        counts[item["grade"]] += 1

    return {
        "image_width": img_w,
        "image_height": img_h,
        "detection_mode": "single_fallback" if len(boxes) <= 1 else "multi",
        "items": items,
        "counts_by_grade": counts,
    }


@app.post("/scrapsense/log")
async def scrapsense_log(dish_id: str = Form(...), file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. "
                   f"Use JPEG, PNG, or WebP.",
        )

    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Empty file")

    result = analyze_plate(image_bytes)
    log_scrapsense(
        dish_id=dish_id,
        filename=file.filename,
        waste_ratio=result["waste_ratio"],
        waste_level=result["waste_level"],
    )
    return {"dish_id": dish_id, **result}


@app.get("/scrapsense/report")
def scrapsense_report():
    return {"dishes": get_scrapsense_report()}


@app.post("/secondserve/scan")
def secondserve_scan(
    name: str = Form(...),
    expiry_date: str = Form(...),  # YYYY-MM-DD
    quantity: int = Form(...),
    unit_price: float = Form(...),
    sku: str = Form(""),
):
    try:
        expiry = datetime.strptime(expiry_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="expiry_date must be YYYY-MM-DD")

    if quantity < 0 or unit_price < 0:
        raise HTTPException(status_code=400, detail="quantity and unit_price must be >= 0")

    result = classify_item(expiry, today=date.today())
    log_secondserve(
        sku=sku,
        name=name,
        expiry_date=expiry_date,
        quantity=quantity,
        unit_price=unit_price,
        days_left=result["days_left"],
        urgency=result["urgency"],
        route=result["route"],
        suggested_markdown_pct=result["suggested_markdown_pct"],
    )
    return {"sku": sku, "name": name, **result}


@app.get("/secondserve/report")
def secondserve_report():
    return get_secondserve_report()
