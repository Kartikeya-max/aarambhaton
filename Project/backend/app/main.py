"""HTTP API. Run with:  uvicorn app.main:app --reload --port 8000"""
from __future__ import annotations

from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from . import config
from .plans import PLANS
from .service import ParseError, get_engine, run_review

ALLOWED_EXTENSIONS = (".pdf", ".csv", ".png", ".jpg", ".jpeg", ".webp", ".heic", ".txt")
MAX_BYTES = config.MAX_FILE_SIZE_MB * 1024 * 1024

app = FastAPI(
    title="BillSatyapana API",
    version="0.1.0",
    description="Checks a hospital bill against CGHS reference rates and drug MRPs. "
    "Flags items for review; it is not a legal verdict.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def _read_upload(upload: UploadFile, label: str) -> bytes:
    name = (upload.filename or "").lower()
    if not name.endswith(ALLOWED_EXTENSIONS):
        raise HTTPException(422, f"The {label} file type is not supported.")
    data = upload.file.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise HTTPException(413, f"The {label} file is larger than {config.MAX_FILE_SIZE_MB} MB.")
    if not data:
        raise HTTPException(422, f"The {label} file is empty.")
    return data


@app.get("/health")
def health() -> dict:
    engine = get_engine()
    return {
        "status": "ok",
        "referenceItems": len(engine.ref.cghs),
        "drugItems": len(engine.ref.drugs),
        "demoData": engine.ref.is_demo,
    }


@app.get("/api/plans")
def plans() -> list[dict]:
    return PLANS


# Sync (not async) on purpose: parsing is CPU-bound, so FastAPI runs it in a worker thread.
@app.post("/api/review")
@app.post("/analyze")  # alias used in the project deck
def review(
    plan_id: str = Form(...),
    bill: UploadFile = File(...),
    visit_summary: Optional[UploadFile] = File(None),
    accreditation: Optional[str] = Form(None),
) -> dict:
    bill_bytes = _read_upload(bill, "bill")
    summary_bytes = _read_upload(visit_summary, "visit summary") if visit_summary and visit_summary.filename else None
    try:
        return run_review(
            plan_id=plan_id,
            bill_name=bill.filename or "",
            bill_bytes=bill_bytes,
            summary_name=visit_summary.filename if visit_summary else None,
            summary_bytes=summary_bytes,
            accreditation=accreditation,
        )
    except (ParseError, ValueError) as exc:
        raise HTTPException(422, str(exc)) from exc
