"""API routes package."""

from app.api.routes.datasets import router as datasets_router
from app.api.routes.classification import router as classification_router
from app.api.routes.predictions import router as predictions_router
from app.api.routes.analytics import router as analytics_router
from app.api.routes.export import router as export_router
from app.api.routes.taxonomy import router as taxonomy_router

__all__ = [
    "datasets_router",
    "classification_router",
    "predictions_router",
    "analytics_router",
    "export_router",
    "taxonomy_router",
]
