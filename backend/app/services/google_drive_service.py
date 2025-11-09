"""Сервис для работы с Google Drive API"""
from typing import Dict, Any, Optional
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.core.config import settings


class GoogleDriveService:
	"""Сервис для работы с Google Drive API"""

	@staticmethod
	def get_oauth_flow(
		client_id: Optional[str] = None,
		client_secret: Optional[str] = None,
		redirect_uri: Optional[str] = None,
	) -> Flow:
		"""Создать OAuth flow для авторизации"""
		# Используем переданные параметры или значения из settings
		client_id = client_id or settings.GDRIVE_CLIENT_ID
		client_secret = client_secret or settings.GDRIVE_CLIENT_SECRET
		
		# Если redirect_uri не указан, формируем его динамически
		if not redirect_uri:
			redirect_uri = settings.GDRIVE_REDIRECT_URI
			if not redirect_uri:
				# Формируем redirect_uri на основе FRONTEND_URL
				redirect_uri = f"{settings.FRONTEND_URL}/api/v1/integrations/gdrive/oauth/callback"

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
			scopes=["https://www.googleapis.com/auth/drive.readonly"],
			redirect_uri=redirect_uri,
		)

	@staticmethod
	def get_client(credentials: dict) -> any:
		"""Получить клиент Google Drive API с credentials"""
		creds = Credentials.from_authorized_user_info(credentials)
		return build("drive", "v3", credentials=creds)

	@staticmethod
	async def test_connection(credentials: dict) -> Dict[str, Any]:
		"""Проверить соединение с Google Drive"""
		try:
			drive = GoogleDriveService.get_client(credentials)
			# Тестовый запрос - получить информацию о пользователе
			about = drive.about().get(fields="user").execute()
			return {"status": "ok", "message": f"Подключено как {about.get('user', {}).get('emailAddress', 'Unknown')}"}
		except HttpError as e:
			return {"status": "error", "message": f"Ошибка подключения: {e.resp.status}"}
		except Exception as e:
			return {"status": "error", "message": str(e)}
	
	@staticmethod
	async def get_account_info(credentials: dict) -> Dict[str, Any]:
		"""Получить информацию об аккаунте Google Drive"""
		try:
			drive = GoogleDriveService.get_client(credentials)
			about = drive.about().get(fields="user").execute()
			user_info = about.get("user", {}) if about else {}
			return {
				"display_name": user_info.get("displayName"),
				"email": user_info.get("emailAddress"),
				"id": user_info.get("permissionId"),
			}
		except Exception as error:
			print(f"⚠️ Не удалось получить данные Google Drive аккаунта: {error}")
			return {}

