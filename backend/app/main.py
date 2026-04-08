"""
Electronic Lab Notebook (ELN) — FastAPI application entry point.

21 CFR Part 11 compliant backend scaffold.
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import attachments, audit, auth, barcodes, comments, entries, experiments, materials, projects, reviews, users
from app.config import settings

app = FastAPI(
    title="Lab Notebook ELN API",
    description="Electronic Lab Notebook with 21 CFR Part 11 compliance scaffolding",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(projects.router)
app.include_router(experiments.router)
app.include_router(entries.router)
app.include_router(materials.router)
app.include_router(attachments.router)
app.include_router(comments.router)
app.include_router(reviews.router)
app.include_router(barcodes.router)
app.include_router(audit.router)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


@app.get("/health", tags=["health"])
def health_check() -> dict:
    return {"status": "ok", "service": "lab-notebook-eln"}
