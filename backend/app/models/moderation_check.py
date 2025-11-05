from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class ModerationCheck(Base):
	__tablename__ = "moderation_checks"

	id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	youtube_video_id = Column(String, nullable=False, index=True)
	gads_customer_id = Column(String, nullable=False)
	campaign_id = Column(String, nullable=False)
	ad_group_id = Column(String, nullable=False)
	status = Column(String, nullable=False)  # 'approved', 'limited', 'not_eligible', 'unknown'
	checked_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
	raw_payload = Column(JSONB, nullable=True)

