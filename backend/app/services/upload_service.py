import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import aiofiles

from app.models import SourceAsset, VideoVersion, YouTubeUpload, Integration
from app.services.video_processor import VideoProcessor
from app.services.youtube_service import YouTubeService
from app.services.integration_service import IntegrationService
from app.core.config import settings


class UploadService:
	"""Сервис для управления загрузкой видео"""

	@staticmethod
	async def process_and_upload(
		session: AsyncSession,
		user_id: uuid.UUID,
		file_path: str,
		original_filename: str,
		generate_orientations: bool,
		requested_orientations: List[str],
	) -> dict:
		"""Обработать видео и загрузить на YouTube"""

		# Получаем расшифрованные credentials для YouTube
		credentials = await IntegrationService.get_decrypted_auth_data(session, user_id, "youtube")
		
		if not credentials:
			raise ValueError("YouTube интеграция не найдена или не активна. Пожалуйста, подключите YouTube в настройках интеграций.")

		# Создаём директории для хранения
		storage_base = Path(settings.STORAGE_PATH)
		source_dir = storage_base / "sources" / str(user_id)
		versions_dir = storage_base / "versions" / str(user_id)
		source_dir.mkdir(parents=True, exist_ok=True)
		versions_dir.mkdir(parents=True, exist_ok=True)

		# Получаем информацию о видео
		video_info = await VideoProcessor.get_video_info(file_path)

		# Сохраняем исходный файл
		source_id = uuid.uuid4()
		source_storage_path = source_dir / f"{source_id}.mp4"
		async with aiofiles.open(file_path, "rb") as src, aiofiles.open(
			str(source_storage_path), "wb"
		) as dst:
			content = await src.read()
			await dst.write(content)

		# Создаём запись об исходнике
		source_asset = SourceAsset(
			id=source_id,
			user_id=user_id,
			original_filename=original_filename,
			storage_path=str(source_storage_path),
			duration_sec=video_info["duration"],
			width=video_info["width"],
			height=video_info["height"],
			fps=video_info["fps"],
		)
		session.add(source_asset)

		# Определяем какие ориентации нужно создать
		original_orientation = UploadService._detect_orientation(
			video_info["width"], video_info["height"]
		)
		orientations_to_create = [original_orientation]

		if generate_orientations:
			all_orientations = ["square", "portrait", "landscape"]
			if requested_orientations:
				orientations_to_create.extend([o for o in requested_orientations if o != original_orientation])
			else:
				orientations_to_create.extend([o for o in all_orientations if o != original_orientation])

		versions = []

		for orientation in orientations_to_create:
			version_id = uuid.uuid4()

			# Обрабатываем видео
			temp_path = str(versions_dir / f"{version_id}_temp.mp4")
			clean_path = str(versions_dir / f"{version_id}_clean.mp4")
			final_path = str(versions_dir / f"{version_id}_final.mp4")

			try:
				# Очистка метаданных
				await VideoProcessor.clean_metadata(str(source_storage_path), clean_path)

				# Уникализация
				transform_profile = None
				version_info = video_info.copy()
				if orientation == original_orientation:
					_, transform_profile = await VideoProcessor.uniquify_video(
						clean_path, final_path, version_info
					)
				else:
					# Генерация ориентации
					new_info = await VideoProcessor.generate_orientation(
						clean_path, final_path, orientation, video_info
					)
					# Уникализация после генерации ориентации
					uniquified_path = str(versions_dir / f"{version_id}_uniq.mp4")
					_, transform_profile = await VideoProcessor.uniquify_video(
						final_path, uniquified_path, new_info
					)
					os.rename(uniquified_path, final_path)
					version_info = new_info

				# Создаём запись о версии
				video_version = VideoVersion(
					id=version_id,
					source_id=source_id,
					orientation=orientation,
					transform_profile=transform_profile,
					storage_path_render=final_path,
					duration_sec=version_info["duration"],
					width=version_info["width"],
					height=version_info["height"],
					fps=version_info["fps"],
				)
				session.add(video_version)

				# Создаём запись о загрузке
				upload = YouTubeUpload(
					id=uuid.uuid4(),
					version_id=version_id,
					status="queued",
					privacy="unlisted",
				)
				session.add(upload)

				await session.commit()

				# Загружаем на YouTube
				upload.status = "processing"
				await session.commit()

				try:
					video_id, youtube_url = await YouTubeService.upload_video(
						final_path,
						f"{original_filename} ({orientation})",
						credentials,
						"unlisted",
					)

					upload.youtube_video_id = video_id
					upload.youtube_url = youtube_url
					upload.status = "success"
					upload.uploaded_at = datetime.now()

					versions.append(
						{
							"id": version_id,
							"orientation": orientation,
							"status": "success",
							"youtube_url": youtube_url,
							"duration_sec": version_info["duration"],
							"width": version_info["width"],
							"height": version_info["height"],
						}
					)

				except Exception as e:
					upload.status = "error"
					upload.error_text = str(e)
					versions.append(
						{
							"id": version_id,
							"orientation": orientation,
							"status": "error",
							"error_text": str(e),
							"duration_sec": version_info.get("duration", 0),
							"width": version_info.get("width", 0),
							"height": version_info.get("height", 0),
						}
					)

				await session.commit()

				# Удаляем временные файлы
				for temp_file in [temp_path, clean_path]:
					if os.path.exists(temp_file):
						os.remove(temp_file)

			except Exception as e:
				# Создаём запись об ошибке
				upload = YouTubeUpload(
					id=uuid.uuid4(),
					version_id=version_id,
					status="error",
					error_text=str(e),
				)
				session.add(upload)
				await session.commit()

				versions.append(
					{
						"id": version_id,
						"orientation": orientation,
						"status": "error",
						"error_text": str(e),
					}
				)

		return {
			"source_id": source_id,
			"original_filename": original_filename,
			"versions": versions,
		}

	@staticmethod
	def _detect_orientation(width: int, height: int) -> str:
		"""Определить ориентацию видео"""
		ratio = width / height
		if abs(ratio - 1.0) < 0.1:
			return "square"
		elif ratio > 1.0:
			return "landscape"
		else:
			return "portrait"

	@staticmethod
	async def retry_upload(
		session: AsyncSession, user_id: uuid.UUID, upload_id: uuid.UUID
	) -> dict:
		"""Повторная попытка загрузки"""
		upload_query = select(YouTubeUpload).where(YouTubeUpload.id == upload_id)
		result = await session.execute(upload_query)
		upload = result.scalar_one_or_none()

		if not upload:
			raise ValueError("Загрузка не найдена")

		version_query = select(VideoVersion).where(VideoVersion.id == upload.version_id)
		result = await session.execute(version_query)
		version = result.scalar_one_or_none()

		if not version:
			raise ValueError("Версия видео не найдена")

		integration_query = select(Integration).where(
			Integration.user_id == user_id, Integration.kind == "youtube", Integration.is_valid == True
		)
		result = await session.execute(integration_query)
		integration = result.scalar_one_or_none()

		if not integration:
			raise ValueError("YouTube интеграция не найдена")

		upload.status = "processing"
		await session.commit()

		try:
			video_id, youtube_url = await YouTubeService.upload_video(
				version.storage_path_render,
				version.orientation,
				integration.auth_data,
				upload.privacy,
			)

			upload.youtube_video_id = video_id
			upload.youtube_url = youtube_url
			upload.status = "success"
			upload.uploaded_at = datetime.now()
			upload.error_text = None

			await session.commit()

			return {
				"id": upload.id,
				"status": "success",
				"youtube_url": youtube_url,
			}

		except Exception as e:
			upload.status = "error"
			upload.error_text = str(e)
			await session.commit()

			raise

