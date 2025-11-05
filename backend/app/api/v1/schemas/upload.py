from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from uuid import UUID


class UploadVersionResponse(BaseModel):
	id: UUID
	orientation: str
	status: str
	youtube_url: Optional[str] = None
	error_text: Optional[str] = None
	duration_sec: float
	width: int
	height: int


class UploadResponse(BaseModel):
	source_id: UUID
	original_filename: str
	versions: List[UploadVersionResponse]


class UploadRequest(BaseModel):
	generate_orientations: bool = False
	orientations: List[str] = []  # ['square', 'portrait', 'landscape']


class UploadItemResponse(BaseModel):
	id: UUID
	source_id: UUID
	original_filename: str
	orientation: str
	duration_sec: float
	width: int
	height: int
	youtube_url: Optional[str] = None
	status: str
	error_text: Optional[str] = None
	uploaded_at: Optional[datetime] = None
	created_at: datetime


class UploadListResponse(BaseModel):
	items: List[UploadItemResponse]
	total: int

