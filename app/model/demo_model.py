import uuid
from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
from app.model.baseapp_model import BaseAppModel

class DemoModel(BaseAppModel):
    """Demo model."""
    __tablename__ = 'demos'
    demo_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False, info={"search": True},index=True)
    logo = Column(String(255), nullable=True)