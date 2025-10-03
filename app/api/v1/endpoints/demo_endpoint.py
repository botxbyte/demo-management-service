from __future__ import annotations
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_async_db
from app.config.constants import SuccessMessages, ApiErrorMessages
from app.helper.fastapi.get_header import get_list_params, get_user_id
from app.schema.response_schema import (
    ApiResponseSchema, 
    PaginatedResponseSchema, 
    PaginationMeta
)
from app.schema.demo_schema import (
    DemoCreateSchema, 
    DemoUpdateSchema, 
    DemoReadSchema,
    DemoStatusUpdateSchema,
    DemoIsActiveUpdateSchema,
    DemoListParamsSchema,
)
from app.service.demo_service import DemoService
from app.exception.demo_exception import (
    DemoNotFoundException,
    DemoCreationException,
    DemoUpdateException,
    DemoDeletionException,
    DemoInvalidDataException,
    DemoPermissionDeniedException
)
from app.exception.baseapp_exception import (

    InternalServerErrorException
)
import json

router = APIRouter()

# Create a new workspace
@router.post("/demo/create/", response_model=ApiResponseSchema[DemoReadSchema], status_code=status.HTTP_201_CREATED)
async def create_demo(
    name: str = Form(..., description="Demo name"),
    logo: Optional[UploadFile] = File(None, description="Logo image file"),
    db: AsyncSession = Depends(get_async_db),
    user_id: UUID = Depends(get_user_id),
):
    """
    Create a new workspace with optional logo upload.
    
    This endpoint allows creating a workspace and uploading a logo in a single request.
    """
    try:
        # Create workspace schema with form data
        payload = DemoCreateSchema(name=name)
        
        # Create workspace using the schema
        data = await DemoService(db).create(payload=payload, user_id=user_id, logo_file=logo)
            
        return ApiResponseSchema[DemoReadSchema](success=True, data=data, message=SuccessMessages.DEMO_CREATED)
        
    except (DemoCreationException, DemoInvalidDataException, InternalServerErrorException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{ApiErrorMessages.DEMO_CREATION_FAILED}: {str(e)}"
        ) from e

# Retrieve a demo by ID
@router.get("/demo/read/{demo_id}/", response_model=ApiResponseSchema[DemoReadSchema])
async def get_workspace(
    demo_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    user_id: UUID = Depends(get_user_id),
):
    """Retrieve a demo by ID."""
    try:
        data = await DemoService(db).read(demo_id=demo_id, user_id=user_id)
        return ApiResponseSchema[DemoReadSchema](success=True, data=data, message=SuccessMessages.DEMO_RETRIEVED)
    except (DemoNotFoundException, DemoPermissionDeniedException, InternalServerErrorException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{ApiErrorMessages.DEMO_RETRIEVAL_FAILED}: {str(e)}"
        ) from e

# List all workspaces
@router.get("/demos/", response_model=PaginatedResponseSchema[list[DemoReadSchema]])
async def list_workspaces(
    params: DemoListParamsSchema = Depends(get_list_params),
    db: AsyncSession = Depends(get_async_db),
    user_id: UUID = Depends(get_user_id),
):
    """List all demos."""
    try:
        # Parse filters if provided as JSON strings
        
        parsed_filters = []
        if params.filters:
            for f in params.filters:
                try:
                    parsed_filters.append(json.loads(f))
                except (json.JSONDecodeError, TypeError):
                    pass
        
        result = await DemoService(db).list_all(
            filters=parsed_filters if parsed_filters else None,
            search=params.search,
            order_by=params.order_by,
            skip=params.offset,
            limit=params.limit,
            user_id=user_id
        )
        
        # Extract data and pagination info
        if isinstance(result, dict):
            data = result.get("data", [])
            total_count = result.get("total_count", len(data))
        else:
            data = result
            total_count = len(data)
        
        # Calculate pagination metadata
        total_pages = (total_count + params.limit - 1) // params.limit if total_count > 0 else 0
        
        pagination = PaginationMeta(
            total_count=total_count,
            offset=params.offset,
            limit=params.limit,
            total_pages=total_pages
        )
        
        return PaginatedResponseSchema[list[DemoReadSchema]](
            success=True, 
            data=data, 
            pagination=pagination,
            message=SuccessMessages.DEMO_RETRIEVED
        )
    except (DemoPermissionDeniedException, InternalServerErrorException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e 
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{ApiErrorMessages.DEMOS_RETRIEVAL_FAILED}: {str(e)}" 
        ) from e

# Update an existing workspace
@router.patch("/demo/update/{demo_id}/", response_model=ApiResponseSchema[DemoReadSchema])
async def update_workspace(
    demo_id: UUID,
    name: Optional[str] = Form(None, description="Demo name"),
    logo: Optional[UploadFile] = File(None, description="Logo image file"),
    db: AsyncSession = Depends(get_async_db),
    user_id: UUID = Depends(get_user_id),
):
    """
    Update an existing demo with optional logo upload.
    
    This endpoint allows updating demo name and uploading a logo in a single request.
    """
    try:
        # Create workspace schema with form data
        payload = DemoUpdateSchema(
            name=name
        )
        
        # Update workspace using the schema
        data = await DemoService(db).update(demo_id=demo_id, payload=payload, user_id=user_id, logo_file=logo)
        
    
        return ApiResponseSchema[DemoReadSchema](success=True, data=data, message=SuccessMessages.DEMO_UPDATED)
        
    except (DemoNotFoundException, DemoUpdateException, DemoInvalidDataException, DemoPermissionDeniedException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{ApiErrorMessages.DEMO_UPDATE_FAILED}: {str(e)}"
        ) from e

# Delete a workspace
@router.delete("/demo/delete/{demo_id}/", response_model=ApiResponseSchema[dict])
async def delete_workspace(
    demo_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    user_id: UUID = Depends(get_user_id),
):
    """Delete a demo by ID."""
    try:
        await DemoService(db).delete(demo_id=demo_id, user_id=user_id)
        return ApiResponseSchema[dict](success=True, data={}, message=SuccessMessages.DEMO_DELETED)
    except (DemoNotFoundException, DemoDeletionException, DemoPermissionDeniedException,DemoInvalidDataException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e 
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{ApiErrorMessages.DEMO_DELETION_FAILED}: {str(e)}"
        ) from e




# Update workspace status
@router.patch("/demo/update/status/{demo_id}/", response_model=ApiResponseSchema[DemoReadSchema])
async def update_workspace_status(
    demo_id: UUID,
    payload: DemoStatusUpdateSchema,
    db: AsyncSession = Depends(get_async_db),
    user_id: UUID = Depends(get_user_id),
):
    """
    Update workspace status and error messages.
    
    Updates the workspace status, error_message, and error_user_message fields.
    """
    try:
        data = await DemoService(db).update_status(demo_id=demo_id, payload=payload, user_id=user_id)
        return ApiResponseSchema[DemoReadSchema](success=True, data=data, message=SuccessMessages.DEMO_STATUS_UPDATED)
    except (DemoNotFoundException, DemoUpdateException, DemoPermissionDeniedException, DemoInvalidDataException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{ApiErrorMessages.DEMO_STATUS_UPDATE_FAILED}: {str(e)}"
        ) from e
        


# Update workspace is_active status
@router.patch("/demo/update/is-active/{demo_id}/", response_model=ApiResponseSchema[DemoReadSchema])
async def update_workspace_is_active(
    demo_id: UUID,
    payload: DemoIsActiveUpdateSchema,
    db: AsyncSession = Depends(get_async_db),
    user_id: UUID = Depends(get_user_id),
):
    """
    Update workspace is_active status.
    
    Updates only the is_active field of the workspace.
    """
    try:
        data = await DemoService(db).update_is_active(demo_id=demo_id, payload=payload, user_id=user_id)
        return ApiResponseSchema[DemoReadSchema](success=True, data=data, message=SuccessMessages.DEMO_ACTIVE_STATUS_UPDATED)
    except (DemoNotFoundException, DemoUpdateException, DemoPermissionDeniedException, DemoInvalidDataException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail) from e 
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{ApiErrorMessages.DEMO_ACTIVE_STATUS_UPDATE_FAILED}: {str(e)}"
        ) from e

