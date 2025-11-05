from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class SourceAsset(Base):
	__tablename__ = "source_assets"

	id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
	original_filename = Column(String, nullable=False)
	storage_path = Column(String, nullable=False)
	duration_sec = Column(Float, nullable=False)
	width = Column(Integer, nullable=False)
	height = Column(Integer, nullable=False)
	fps = Column(Float, nullable=False)
	created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

