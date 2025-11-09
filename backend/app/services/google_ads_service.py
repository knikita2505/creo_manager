"""Сервис для работы с Google Ads API"""
from typing import Dict, Any, Optional
import httpx
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

from app.core.config import settings


class GoogleAdsService:
	"""Сервис для работы с Google Ads API"""

	API_VERSION = "v22"

	@staticmethod
	def get_oauth_flow(
		client_id: Optional[str] = None,
		client_secret: Optional[str] = None,
		redirect_uri: Optional[str] = None,
		scopes: Optional[list[str]] = None,
	) -> Flow:
		"""Создать OAuth flow для авторизации"""
		# Используем переданные параметры или значения из settings
		client_id = client_id or settings.GADS_CLIENT_ID
		client_secret = client_secret or settings.GADS_CLIENT_SECRET
		
		# Если redirect_uri не указан, формируем его динамически
		if not redirect_uri:
			redirect_uri = settings.GADS_REDIRECT_URI
			if not redirect_uri:
				# Формируем redirect_uri на основе FRONTEND_URL
				redirect_uri = f"{settings.FRONTEND_URL}/api/v1/integrations/gads/oauth/callback"

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
			scopes=scopes or ["https://www.googleapis.com/auth/adwords"],
			redirect_uri=redirect_uri,
		)

	@staticmethod
	async def test_connection(credentials: dict) -> Dict[str, Any]:
		"""Проверить соединение с Google Ads"""
		developer_token = credentials.get("developer_token")
		if not developer_token:
			return {
				"status": "error",
				"message": "Developer token не настроен. Укажите его в настройках интеграции.",
			}
		
		try:
			creds = Credentials.from_authorized_user_info(credentials)
			if not creds.valid:
				return {"status": "error", "message": "Токен невалиден или истёк"}
			
			account_info = await GoogleAdsService.get_account_info(
				access_token=credentials.get("token"),
				developer_token=developer_token,
				login_customer_id=credentials.get("login_customer_id"),
			)
			
			if account_info.get("display_name"):
				return {
					"status": "ok",
					"message": f"Подключено к аккаунту Google Ads {account_info['display_name']}",
					"account_info": account_info,
				}
			
			return {"status": "ok", "message": "Подключение успешно"}
		except Exception as e:
			return {"status": "error", "message": str(e)}

	@staticmethod
	async def get_account_info(
		access_token: str,
		developer_token: str,
		login_customer_id: Optional[str] = None,
	) -> Dict[str, Any]:
		"""Получить информацию об аккаунте Google Ads"""
		if not access_token or not developer_token:
			return {}
		
		headers = {
			"Authorization": f"Bearer {access_token}",
			"developer-token": developer_token,
		}
		if login_customer_id:
			headers["login-customer-id"] = login_customer_id.replace("-", "")
		
		base_url = f"https://googleads.googleapis.com/{GoogleAdsService.API_VERSION}"
		
		async with httpx.AsyncClient(timeout=10) as client:
			url_list_customers = f"{base_url}/customers:listAccessibleCustomers"
			print(f"ℹ️ Запрос списка аккаунтов Google Ads: {url_list_customers}")
			list_response = await client.get(
				url_list_customers, headers=headers
			)
			if list_response.status_code != 200:
				print(
					f"⚠️ Не удалось получить список аккаунтов Google Ads "
					f"(status={list_response.status_code}): {list_response.text}"
				)
				return {}
			
			data = list_response.json()
			resource_names = data.get("resourceNames") or []
			if not resource_names:
				return {}
			
			resource_name = resource_names[0]
			customer_id = resource_name.split("/")[-1]
			
			details_url = f"{base_url}/{resource_name}"
			print(f"ℹ️ Запрос данных аккаунта Google Ads: {details_url}")
			details_response = await client.get(details_url, headers=headers)
			display_name = None
			if details_response.status_code == 200:
				customer_payload = details_response.json()
				display_name = customer_payload.get("descriptiveName") or customer_payload.get("resourceName")
			else:
				print(
					f"⚠️ Не удалось получить данные аккаунта {resource_name} "
					f"(status={details_response.status_code}): {details_response.text}"
				)
				display_name = resource_name
			
			return {
				"display_name": display_name,
				"resource_name": resource_name,
				"customer_id": customer_id,
				"login_customer_id": login_customer_id,
			}

