from fastapi import APIRouter

from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.demo_endpoint import router as demo_router


api_router: APIRouter = APIRouter()

api_router.include_router(router=health_router, prefix="/demo-management", tags=["Health"])  # /health/
api_router.include_router(router=demo_router, prefix="/demo-management", tags=["Demo"])  # /demo/
