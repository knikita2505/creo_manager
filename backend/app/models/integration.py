from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class Integration(Base):
	__tablename__ = "integrations"

	id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
	user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
	kind = Column(String, nullable=False)  # 'youtube', 'gdrive', 'gads', 'telegram'
	auth_data = Column(JSONB, nullable=False)
	is_valid = Column(Boolean, default=True, nullable=False)
	created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

