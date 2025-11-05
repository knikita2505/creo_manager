import os
import tempfile
import uuid
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.database import get_db
from app.api.v1.schemas.upload import (
	UploadResponse,
	UploadRequest,
	UploadListResponse,
	UploadItemResponse,
)
from app.models import SourceAsset, VideoVersion, YouTubeUpload
from app.services.upload_service import UploadService

router = APIRouter()


async def get_current_user_id() -> uuid.UUID:
	"""Временная функция для получения user_id. В будущем заменить на реальную аутентификацию"""
	# TODO: Реализовать реальную аутентификацию
	return uuid.UUID("00000000-0000-0000-0000-000000000001")


@router.post("/", response_model=UploadResponse)
async def upload_video(
	background_tasks: BackgroundTasks,
	files: List[UploadFile] = File(...),
	generate_orientations: bool = Query(False, description="Генерировать недостающие ориентации"),
	orientations: Optional[List[str]] = Query(None, description="Список ориентаций для генерации"),
	current_user_id: uuid.UUID = Depends(get_current_user_id),
	db: AsyncSession = Depends(get_db),
):
	"""Загрузить одно или несколько видео"""
	if not files:
		raise HTTPException(status_code=400, detail="Не предоставлены файлы")

	# Обрабатываем первое видео (для MVP)
	# В будущем можно обработать все файлы параллельно
	file = files[0]

	# Сохраняем файл во временную директорию
	with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_file:
		content = await file.read()
		tmp_file.write(content)
		tmp_path = tmp_file.name

	try:
		result = await UploadService.process_and_upload(
			session=db,
			user_id=current_user_id,
			file_path=tmp_path,
			original_filename=file.filename or "video.mp4",
			generate_orientations=generate_orientations,
			requested_orientations=orientations or [],
		)

		return UploadResponse(
			source_id=result["source_id"],
			original_filename=result["original_filename"],
			versions=[
				{
					"id": v["id"],
					"orientation": v["orientation"],
					"status": v["status"],
					"youtube_url": v.get("youtube_url"),
					"error_text": v.get("error_text"),
					"duration_sec": v.get("duration_sec", 0),
					"width": v.get("width", 0),
					"height": v.get("height", 0),
				}
				for v in result["versions"]
			],
		)

	finally:
		# Удаляем временный файл
		if os.path.exists(tmp_path):
			os.remove(tmp_path)


@router.get("/", response_model=UploadListResponse)
async def list_uploads(
	current_user_id: uuid.UUID = Depends(get_current_user_id),
	db: AsyncSession = Depends(get_db),
	skip: int = 0,
	limit: int = 50,
):
	"""Получить список всех загрузок пользователя"""
	# Получаем все исходники пользователя
	source_query = select(SourceAsset).where(SourceAsset.user_id == current_user_id)
	source_result = await db.execute(source_query)
	sources = source_result.scalars().all()

	source_ids = [s.id for s in sources]

	if not source_ids:
		return UploadListResponse(items=[], total=0)

	# Получаем все версии и загрузки
	version_query = select(VideoVersion, YouTubeUpload, SourceAsset).join(
		YouTubeUpload, VideoVersion.id == YouTubeUpload.version_id
	).join(SourceAsset, VideoVersion.source_id == SourceAsset.id).where(
		SourceAsset.id.in_(source_ids)
	).offset(skip).limit(limit)

	result = await db.execute(version_query)
	rows = result.all()

	items = []
	for version, upload, source in rows:
		items.append(
			UploadItemResponse(
				id=upload.id,
				source_id=source.id,
				original_filename=source.original_filename,
				orientation=version.orientation,
				duration_sec=version.duration_sec,
				width=version.width,
				height=version.height,
				youtube_url=upload.youtube_url,
				status=upload.status,
				error_text=upload.error_text,
				uploaded_at=upload.uploaded_at,
				created_at=version.created_at,
			)
		)

	# Подсчитываем общее количество
	count_query = select(VideoVersion).join(
		SourceAsset, VideoVersion.source_id == SourceAsset.id
	).where(SourceAsset.id.in_(source_ids))
	count_result = await db.execute(count_query)
	total = len(count_result.scalars().all())

	return UploadListResponse(items=items, total=total)


@router.post("/{upload_id}/retry")
async def retry_upload(
	upload_id: uuid.UUID,
	current_user_id: uuid.UUID = Depends(get_current_user_id),
	db: AsyncSession = Depends(get_db),
):
	"""Повторить попытку загрузки"""
	try:
		result = await UploadService.retry_upload(db, current_user_id, upload_id)
		return result
	except ValueError as e:
		raise HTTPException(status_code=404, detail=str(e))
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))

