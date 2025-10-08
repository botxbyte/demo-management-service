from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config.config import config
from app.config.logger_config import configure_logging, shutdown_logging
from app.api.v1.router import api_router
from app.middleware.correlation import CorrelationIdMiddleware
from app.exception.fastapi.error_handlers import setup_error_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):  # pylint: disable=unused-argument
    """Manage application lifespan events."""
    # Startup
    configure_logging()
    yield
    # Shutdown
    await shutdown_logging()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=config.APP_NAME,
        version=config.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        default_response_class=JSONResponse,
        lifespan=lifespan,
    )

    # Add middleware
    app.add_middleware(CorrelationIdMiddleware, header_name="X-Correlation-ID")
    
    # Setup custom error handlers
    setup_error_handlers(app)

    # Include API routes
    app.include_router(router=api_router, prefix="/demo-management/api/v1")
    
    # Mount static files for media
    app.mount("/media", StaticFiles(directory="app/media"), name="media")

    return app