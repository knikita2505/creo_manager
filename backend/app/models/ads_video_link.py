from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class AdsVideoLink(Base):
	__tablename__ = "ads_video_links"

	id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	youtube_video_id = Column(String, nullable=False, index=True)
	gads_customer_id = Column(String, nullable=False)
	campaign_id = Column(String, nullable=False)
	ad_group_id = Column(String, nullable=False)
	asset_id = Column(String, nullable=True)
	created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

