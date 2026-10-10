"""VYOM+ FastAPI Application Entrypoint."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api import api_router

app = FastAPI(
    title="VYOM+ Transaction Intelligence API",
    description="AI-powered financial transaction intelligence and voucher classification platform.",
    version="0.1.0",
)

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configurable in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount v1 REST API routes
app.include_router(api_router)


@app.get("/")
def root():
    """Root entrypoint returning basic system status."""
    return {
        "app": "VYOM+",
        "tagline": "Your books. Understood by AI.",
        "version": "0.1.0",
        "status": "online",
        "docs_url": "/docs",
    }


@app.get("/health")
@app.get("/api/health")
def health_check():
    """Health check endpoint for container probes and integration validation."""
    return {
        "status": "healthy",
        "app": "VYOM+",
        "version": "0.1.0",
        "environment": settings.environment,
        "gemini_configured": settings.is_gemini_configured,
        "gemini_model": settings.gemini_model,
    }
