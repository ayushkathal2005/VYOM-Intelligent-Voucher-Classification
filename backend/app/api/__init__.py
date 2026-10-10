"""Main API router combining all v1 endpoints."""

from fastapi import APIRouter
from app.api.routes.datasets import router as datasets_router
from app.api.routes.classification import router as classification_router
from app.api.routes.predictions import router as predictions_router
from app.api.routes.analytics import router as analytics_router
from app.api.routes.export import router as export_router
from app.api.routes.taxonomy import router as taxonomy_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(datasets_router)
api_router.include_router(classification_router)
api_router.include_router(predictions_router)
api_router.include_router(analytics_router)
api_router.include_router(export_router)
api_router.include_router(taxonomy_router)

__all__ = ["api_router"]
