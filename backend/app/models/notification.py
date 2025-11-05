from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class Notification(Base):
	__tablename__ = "notifications"

	id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	type = Column(String, nullable=False)  # 'moderation_alert'
	payload = Column(JSONB, nullable=False)
	delivered_to = Column(String, nullable=False)  # 'telegram'
	delivered_at = Column(DateTime(timezone=True), nullable=True)

