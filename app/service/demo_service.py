from __future__ import annotations

from typing import Optional, Dict, Any, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.config.logger_config import  log_user_activity, log_central
from app.config.constants import  LogMessages
from app.schema.demo_schema import (
    DemoCreateSchema, 
    DemoUpdateSchema, 
    DemoReadSchema,
    DemoStatusUpdateSchema,
    DemoIsActiveUpdateSchema
)
from app.exception.demo_exception import (
    DemoNotFoundException,
    DemoFileUploadException,
    DemoFileValidationException,
    DemoFileSizeExceededException,
    DemoUnsupportedFileTypeException,
    DemoStorageException,
    DemoFileNotFoundException,
)

from app.service.baseapp_service import BaseAppService
from app.repository.demo_repository import DemoRepository
from app.helper.file_helper import FileHelper
from app.config.config import config

class DemoService(BaseAppService):
    """Demo service."""
    def __init__(self, db: AsyncSession):
        super().__init__(db=db)
        self.demo_repo = DemoRepository(db=db)
        self.file_helper = FileHelper(
            base_media_path=config.MEDIA_PATH,
            logo_subdir=config.LOGO_SUBDIR
        )

    async def create(self, payload: DemoCreateSchema, user_id: UUID, logo_file=None) -> DemoReadSchema:        
        """Create a new demo."""
        demo = await self.demo_repo.insert(demo_data=payload.model_dump(), user_id=user_id)
        log_user_activity(f"{LogMessages.DEMO_CREATED}: {demo.name}", action_type="demo_create", level="info")
        
        # Set initial status
        demo.status = "created"
        
        # Upload logo if provided
        if logo_file:
            try:
                logo_url = await self.file_helper.upload_logo(file=logo_file, demo_id=str(demo.demo_id))
                # Update demo with logo URL
                updated_demo = await self.demo_repo.update(
                    demo_id=demo.demo_id, 
                    demo_data={"logo": logo_url}, 
                    user_id=user_id
                )
                if updated_demo:
                    demo = updated_demo
            except (DemoFileUploadException, DemoFileValidationException, DemoFileSizeExceededException, 
                    DemoUnsupportedFileTypeException, DemoStorageException) as e:
                log_central(
                    message=f"{LogMessages.LOGO_UPLOAD_FAILED} {demo.demo_id}: {str(e)}", 
                    level="warning"
                )
                # Continue without logo if upload fails
        
        return DemoReadSchema.model_validate(demo)

    async def read(self, demo_id: UUID, user_id: UUID) -> DemoReadSchema:
        """Read a demo."""
        demo = await self.demo_repo.get_by_id(demo_id=demo_id)
        if not demo:
            raise DemoNotFoundException(demo_id=demo_id)
        return DemoReadSchema.model_validate(demo)
    
    async def list_all(
        self,
        filters: Optional[List[Dict[str, Any]]] = None,
        search: Optional[str] = None,
        order_by: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
        user_id: Optional[UUID] = None,
    ) -> List[DemoReadSchema]:
        """List all demos."""
        
        result = await self.demo_repo.get_all(
            filters=filters,
            search=search,
            order_by=order_by,
            skip=skip, 
            limit=limit,
            user_id=user_id,
        )
        data = result.get("data", []) if isinstance(result, dict) else result
        return [DemoReadSchema.model_validate(ws) for ws in data]

    
    async def update(self, demo_id: UUID, payload: DemoUpdateSchema, user_id: UUID, logo_file=None) -> DemoReadSchema:
        """Update a demo."""
        existing_demo = await self.demo_repo.get_by_id(demo_id=demo_id)
        if not existing_demo:
            raise DemoNotFoundException(demo_id=demo_id)
        
        # Handle logo upload if provided
        if logo_file:
            try:
                # Delete old logo if exists
                if existing_demo.logo:
                    try:
                        await self.file_helper.delete_logo(existing_demo.logo)
                    except DemoFileNotFoundException:
                        # Old logo file doesn't exist, continue
                        log_central(
                            message=f"{LogMessages.OLD_LOGO_NOT_FOUND} {demo_id}, continuing with upload",  
                            level="info"
                        )
                
                # Upload new logo
                logo_url = await self.file_helper.upload_logo(file=logo_file, demo_id=str(demo_id))
                
                # Add logo URL to payload
                payload_dict = payload.model_dump(exclude_unset=True)
                payload_dict["logo"] = logo_url
            except (DemoFileUploadException, DemoFileValidationException, DemoFileSizeExceededException, 
                    DemoUnsupportedFileTypeException, DemoStorageException) as e:
                log_central(
                    message=f"{LogMessages.LOGO_UPLOAD_FAILED} {demo_id}: {str(e)}",  
                    level="warning"
                )
                # Continue without logo if upload fails
                payload_dict = payload.model_dump(exclude_unset=True)
        else:
            payload_dict = payload.model_dump(exclude_unset=True)
        
        payload_dict["status"] = "updated"
        demo = await self.demo_repo.update(demo_id=demo_id, demo_data=payload_dict, user_id=user_id)

        log_user_activity(f"{LogMessages.DEMO_UPDATED}: {demo.name}", action_type="demo_update")
        return DemoReadSchema.model_validate(demo)

    async def delete(self, demo_id: UUID, user_id: UUID) -> None:
        """Delete a demo."""
        deleted = await self.demo_repo.delete(demo_id=demo_id, user_id=user_id)
        
        if not deleted:
            raise DemoNotFoundException(demo_id=demo_id)
        
        log_user_activity(f"{LogMessages.DEMO_DELETED} {demo_id}", action_type="demo_delete")

    
    async def update_status(self, demo_id: UUID, payload: DemoStatusUpdateSchema, user_id: UUID) -> DemoReadSchema:
        """
        Update demo status and error messages.
        """
        log_central(message=f"{LogMessages.DEMO_STATUS_UPDATED} {demo_id} status to {payload.status}", level="info")
        
        # Update status via repository
        demo = await self.demo_repo.update_status(
            demo_id=demo_id, 
            status=payload.status, 
            user_id=user_id
        )

        # Update error messages if provided
        update_data = {}
        if payload.error_message is not None:
            update_data["error_message"] = payload.error_message
        if payload.error_user_message is not None:
            update_data["error_user_message"] = payload.error_user_message

        if update_data:
            demo = await self.demo_repo.update(
                demo_id=demo_id, 
                demo_data=update_data, 
                user_id=user_id
            )

        return DemoReadSchema.model_validate(demo)

    async def update_is_active(self, demo_id: UUID, payload: DemoIsActiveUpdateSchema, user_id: UUID) -> DemoReadSchema:
        """
        Update demo is_active status.
        
        Args:
            demo_id: UUID of the demo to update
            payload: Is active update data
            user_id: ID of the user making the update
            
        Returns:
            Updated demo data
            
        Raises:
            DemoNotFoundException: If demo is not found
            DemoUpdateException: If update fails
        """
        # Update is_active via repository
        demo = await self.demo_repo.update_is_active(
            demo_id=demo_id, 
            is_active=payload.is_active, 
            user_id=user_id
        )

        return DemoReadSchema.model_validate(demo)