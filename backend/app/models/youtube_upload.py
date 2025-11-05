from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class YouTubeUpload(Base):
	__tablename__ = "youtube_uploads"

	id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	version_id = Column(UUID(as_uuid=True), ForeignKey("video_versions.id"), nullable=False, index=True)
	youtube_video_id = Column(String, nullable=True, index=True)
	youtube_url = Column(String, nullable=True)
	title = Column(String, nullable=True)
	privacy = Column(String, default="unlisted", nullable=False)
	thumbnail_set = Column(Boolean, default=False, nullable=False)
	status = Column(String, nullable=False)  # 'queued', 'processing', 'success', 'error'
	error_text = Column(String, nullable=True)
	uploaded_at = Column(DateTime(timezone=True), nullable=True)

