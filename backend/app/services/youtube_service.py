import os
from typing import Optional
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

from app.core.config import settings


class YouTubeService:
	"""Сервис для работы с YouTube API"""

	@staticmethod
	def get_oauth_flow() -> Flow:
		"""Создать OAuth flow для авторизации"""
		return Flow.from_client_config(
			{
				"web": {
					"client_id": settings.YOUTUBE_CLIENT_ID,
					"client_secret": settings.YOUTUBE_CLIENT_SECRET,
					"auth_uri": "https://accounts.google.com/o/oauth2/auth",
					"token_uri": "https://oauth2.googleapis.com/token",
					"redirect_uris": [settings.YOUTUBE_REDIRECT_URI],
				}
			},
			scopes=["https://www.googleapis.com/auth/youtube.upload"],
		)

	@staticmethod
	def get_client(credentials: dict) -> any:
		"""Получить клиент YouTube API с credentials"""
		creds = Credentials.from_authorized_user_info(credentials)
		return build("youtube", "v3", credentials=creds)

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

