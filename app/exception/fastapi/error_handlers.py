from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi import status
from app.exception.baseapp_exception import BaseAppException
from app.config.logger_config import log_central


def setup_error_handlers(app):
    """
    Set up custom error handlers for the FastAPI app.
    This is the standard way to organize error handling in enterprise applications.
    """
    
    @app.exception_handler(BaseAppException)
    async def app_exception_handler(_: Request, exc: BaseAppException) -> JSONResponse:
        """Handle custom application exceptions."""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "data": {},
                "error_message": exc.detail,
                "errors": []
            },
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
        """Handle HTTP exceptions (400, 401, 403, 404, etc.)."""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "data": {},
                "error_message": exc.detail,
                "errors": []
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        """Handle Pydantic validation errors."""
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "data": {},
                "error_message": "Validation failed",
                "errors": exc.errors()
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
        """Handle unexpected exceptions with proper logging."""
        # Log the unexpected exception
        log_central(
            message=f"Unhandled exception: {exc}",
            level="error",
            exc_info=True
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "data": {},
                "error_message": "Internal Server Error",
                "errors": []
            },
        )