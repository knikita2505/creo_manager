import os
from typing import Optional, Dict, Any
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

from app.core.config import settings


class YouTubeService:
	"""Сервис для работы с YouTube API"""

	@staticmethod
	def get_oauth_flow(
		client_id: Optional[str] = None,
		client_secret: Optional[str] = None,
		redirect_uri: Optional[str] = None,
	) -> Flow:
		"""Создать OAuth flow для авторизации"""
		# Используем переданные параметры или значения из settings
		client_id = client_id or settings.YOUTUBE_CLIENT_ID
		client_secret = client_secret or settings.YOUTUBE_CLIENT_SECRET
		
		# Проверяем, что client_id и client_secret заданы
		if not client_id or not client_secret:
			raise ValueError("client_id и client_secret обязательны для создания OAuth flow")
		
		# Если redirect_uri не указан, формируем его динамически
		if not redirect_uri:
			redirect_uri = settings.YOUTUBE_REDIRECT_URI
			if not redirect_uri:
				# Формируем redirect_uri на основе BACKEND_URL (так как callback обрабатывается на backend)
				redirect_uri = f"{settings.BACKEND_URL}/api/v1/integrations/youtube/oauth/callback"
		
		if not redirect_uri:
			raise ValueError("redirect_uri обязателен для создания OAuth flow")

		return Flow.from_client_config(
			{
				"web": {
					"client_id": client_id,
					"client_secret": client_secret,
					"auth_uri": "https://accounts.google.com/o/oauth2/auth",
					"token_uri": "https://oauth2.googleapis.com/token",
					"redirect_uris": [redirect_uri],
				}
			},
			scopes=[
				"https://www.googleapis.com/auth/youtube.upload",
				"https://www.googleapis.com/auth/youtube.readonly",  # Для проверки соединения
			],
			redirect_uri=redirect_uri,
		)

	@staticmethod
	def get_client(credentials: dict) -> any:
		"""Получить клиент YouTube API с credentials"""
		# Проверяем наличие обязательных полей
		required_fields = ["token", "refresh_token", "client_id", "client_secret"]
		missing_fields = [field for field in required_fields if not credentials.get(field)]
		
		if missing_fields:
			raise ValueError(
				f"Отсутствуют обязательные поля в credentials: {', '.join(missing_fields)}. "
				"Пожалуйста, переподключите YouTube интеграцию."
			)
		
		# Убеждаемся, что есть token_uri
		if "token_uri" not in credentials:
			credentials["token_uri"] = "https://oauth2.googleapis.com/token"
		
		try:
			creds = Credentials.from_authorized_user_info(credentials)
			return build("youtube", "v3", credentials=creds)
		except Exception as e:
			raise ValueError(
				f"Ошибка создания YouTube клиента: {str(e)}. "
				"Проверьте, что credentials содержат все необходимые поля."
			) from e
	
	@staticmethod
	def get_account_info(credentials: dict) -> Dict[str, Any]:
		"""Получить информацию об аккаунте YouTube"""
		try:
			youtube = YouTubeService.get_client(credentials)
			response = youtube.channels().list(part="snippet", mine=True).execute()
			items = response.get("items") or []
			if not items:
				return {}
			channel = items[0]
			snippet = channel.get("snippet", {})
			return {
				"display_name": snippet.get("title"),
				"id": channel.get("id"),
				"thumbnail_url": (snippet.get("thumbnails", {}) or {}).get("default", {}).get("url"),
			}
		except Exception as error:
			print(f"⚠️ Не удалось получить данные YouTube аккаунта: {error}")
			return {}

	@staticmethod
	async def upload_video(
		file_path: str,
		title: Optional[str],
		credentials: dict,
		privacy: str = "unlisted",
	) -> tuple[str, str]:
		"""Загрузить видео на YouTube"""
		try:
			youtube = YouTubeService.get_client(credentials)

			body = {
				"snippet": {
					"title": title or os.path.basename(file_path),
					"description": "",
					"tags": [],
					"categoryId": "22",  # People & Blogs
				},
				"status": {
					"privacyStatus": privacy,
					"selfDeclaredMadeForKids": False,
				},
			}

			media = MediaFileUpload(file_path, chunksize=-1, resumable=True, mimetype="video/*")

			insert_request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

			response = None
			while response is None:
				status, response = insert_request.next_chunk()
				if status:
					pass  # Можно добавить прогресс-бар

			video_id = response["id"]
			youtube_url = f"https://www.youtube.com/watch?v={video_id}"

			return video_id, youtube_url

		except HttpError as e:
			error_message = f"YouTube API error: {e.resp.status} - {e.content.decode()}"
			raise Exception(error_message) from e

	@staticmethod
	async def set_thumbnail(video_id: str, thumbnail_path: str, credentials: dict) -> None:
		"""Установить миниатюру для видео"""
		try:
			youtube = YouTubeService.get_client(credentials)
			youtube.thumbnails().set(
				videoId=video_id, media_body=MediaFileUpload(thumbnail_path)
			).execute()
		except HttpError as e:
			error_message = f"YouTube API error при установке thumbnail: {e.resp.status} - {e.content.decode()}"
			raise Exception(error_message) from e

