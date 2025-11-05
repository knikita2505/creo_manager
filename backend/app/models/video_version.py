from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class VideoVersion(Base):
	__tablename__ = "video_versions"

	id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	source_id = Column(UUID(as_uuid=True), ForeignKey("source_assets.id"), nullable=False, index=True)
	orientation = Column(String, nullable=False)  # 'square', 'portrait', 'landscape'
	transform_profile = Column(JSONB, nullable=True)
	storage_path_render = Column(String, nullable=False)
	duration_sec = Column(Float, nullable=False)
	width = Column(Integer, nullable=False)
	height = Column(Integer, nullable=False)
	fps = Column(Float, nullable=False)
	created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

