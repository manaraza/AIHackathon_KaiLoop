"""
Kai Loop — SecondCrop backend.

Endpoints:
    POST /grade   — upload a produce photo, get back grade + route + score
    GET  /impact  — aggregate stats across everything graded so far
    GET  /health  — quick liveness check
"""

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from db import get_impact_summary, init_db, log_grading
from model_loader import grade_image

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
