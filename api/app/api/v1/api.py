from fastapi import APIRouter

from app.api.v1.auth import auth_router
from app.api.v1.metrics import metrics_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(metrics_router)