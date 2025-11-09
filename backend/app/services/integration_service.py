"""Сервис для управления интеграциями"""
import uuid
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from googleapiclient.errors import HttpError

from app.models import Integration
from app.core.config import settings

INTEGRATION_DEFAULT_SCOPES: Dict[str, list[str]] = {
	"youtube": [
		"https://www.googleapis.com/auth/youtube.upload",
		"https://www.googleapis.com/auth/youtube.readonly",
	],
	"gdrive": ["https://www.googleapis.com/auth/drive.readonly"],
	"gads": ["https://www.googleapis.com/auth/adwords"],
}
from app.services.encryption import EncryptionService


class IntegrationService:
	"""Сервис для управления интеграциями"""

	@staticmethod
	async def get_integration(
		session: AsyncSession, user_id: uuid.UUID, kind: str
	) -> Optional[Integration]:
		"""Получить интеграцию пользователя"""
		query = select(Integration).where(
			and_(Integration.user_id == user_id, Integration.kind == kind)
		)
		result = await session.execute(query)
		return result.scalar_one_or_none()

	@staticmethod
	async def get_all_integrations(
		session: AsyncSession, user_id: uuid.UUID
	) -> list[Integration]:
		"""Получить все интеграции пользователя"""
		query = select(Integration).where(Integration.user_id == user_id)
		result = await session.execute(query)
		return list(result.scalars().all())

	@staticmethod
	async def create_or_update_integration(
		session: AsyncSession,
		user_id: uuid.UUID,
		kind: str,
		auth_data: Dict[str, Any],
		is_valid: bool = True,
		account_info: Optional[Dict[str, Any]] = None,
	) -> Integration:
		"""Создать или обновить интеграцию"""
		# Шифруем токены (но не oauth_config, если он есть)
		# Разделяем oauth_config и токены
		auth_payload = dict(auth_data)
		oauth_config = auth_payload.pop("oauth_config", None)
		account_info = account_info or auth_payload.pop("account_info", None)
		tokens_data = auth_payload  # Остальное - это токены
		
		encrypted_auth = EncryptionService.encrypt(tokens_data)

		# Проверяем, существует ли уже интеграция
		existing = await IntegrationService.get_integration(session, user_id, kind)
		existing_tokens: Dict[str, Any] = {}
		if existing and existing.auth_data.get("encrypted"):
			try:
				existing_tokens = EncryptionService.decrypt(existing.auth_data["encrypted"])
			except Exception:
				existing_tokens = {}

		# Сохраняем refresh_token и другие данные из предыдущей интеграции, если Google не вернул их
		if (not tokens_data.get("refresh_token")) and existing_tokens.get("refresh_token"):
			tokens_data["refresh_token"] = existing_tokens["refresh_token"]
		if not tokens_data.get("scopes"):
			if kind in INTEGRATION_DEFAULT_SCOPES:
				tokens_data["scopes"] = INTEGRATION_DEFAULT_SCOPES[kind]
			elif existing_tokens.get("scopes"):
				tokens_data["scopes"] = existing_tokens["scopes"]
		if not tokens_data.get("token_uri") and existing_tokens.get("token_uri"):
			tokens_data["token_uri"] = existing_tokens["token_uri"]

		# Перешифровываем с обновлёнными данными
		encrypted_auth = EncryptionService.encrypt(tokens_data)

		# Формируем auth_data с сохранением oauth_config
		new_auth_data = {"encrypted": encrypted_auth}
		if oauth_config:
			new_auth_data["oauth_config"] = oauth_config
		elif existing and existing.auth_data.get("oauth_config"):
			# Сохраняем существующий oauth_config при обновлении токенов
			new_auth_data["oauth_config"] = existing.auth_data["oauth_config"]
		
		if account_info:
			new_auth_data["account_info"] = account_info
		elif existing and existing.auth_data.get("account_info"):
			new_auth_data["account_info"] = existing.auth_data["account_info"]

		if existing:
			# Обновляем существующую
			existing.auth_data = new_auth_data
			existing.is_valid = is_valid
			await session.commit()
			await session.refresh(existing)
			return existing
		else:
			# Создаём новую
			integration = Integration(
				user_id=user_id,
				kind=kind,
				auth_data=new_auth_data,
				is_valid=is_valid,
			)
			session.add(integration)
			await session.commit()
			await session.refresh(integration)
			return integration

	@staticmethod
	async def delete_integration(
		session: AsyncSession, user_id: uuid.UUID, kind: str
	) -> bool:
		"""Удалить интеграцию"""
		integration = await IntegrationService.get_integration(session, user_id, kind)
		if integration:
			await session.delete(integration)
			await session.commit()
			return True
		return False

	@staticmethod
	async def get_decrypted_auth_data(
		session: AsyncSession, user_id: uuid.UUID, kind: str
	) -> Optional[Dict[str, Any]]:
		"""Получить расшифрованные данные авторизации"""
		integration = await IntegrationService.get_integration(session, user_id, kind)
		if not integration:
			return None

		try:
			encrypted_data = integration.auth_data.get("encrypted")
			if not encrypted_data:
				return None
			
			# Расшифровываем токены
			tokens_data = EncryptionService.decrypt(encrypted_data)
			
			# Добавляем client_id и client_secret из oauth_config, если их нет в токенах
			# Это нужно для правильного формата Credentials.from_authorized_user_info()
			oauth_config = integration.auth_data.get("oauth_config")
			if oauth_config:
				if "client_id" not in tokens_data and oauth_config.get("client_id"):
					tokens_data["client_id"] = oauth_config["client_id"]
				if "client_secret" not in tokens_data and oauth_config.get("client_secret"):
					tokens_data["client_secret"] = oauth_config["client_secret"]
				if kind == "gads" and oauth_config.get("developer_token"):
					tokens_data["developer_token"] = oauth_config["developer_token"]
					if oauth_config.get("login_customer_id"):
						tokens_data["login_customer_id"] = oauth_config["login_customer_id"]
			elif kind == "gads" and settings.GADS_DEVELOPER_TOKEN:
				tokens_data["developer_token"] = settings.GADS_DEVELOPER_TOKEN
			
			# Убеждаемся, что token_uri установлен
			if "token_uri" not in tokens_data:
				tokens_data["token_uri"] = "https://oauth2.googleapis.com/token"
			
			# Логируем для отладки (в production можно убрать)
			has_required = all(
				field in tokens_data and tokens_data[field]
				for field in ["token", "refresh_token", "client_id", "client_secret"]
			)
			if not has_required:
				missing = [f for f in ["token", "refresh_token", "client_id", "client_secret"] if not tokens_data.get(f)]
				print(f"⚠️ Предупреждение: отсутствуют поля в credentials для {kind}: {missing}")
			
			account_info = integration.auth_data.get("account_info")
			if account_info:
				tokens_data["account_info"] = account_info
			
			return tokens_data
		except Exception:
			# Если не удалось расшифровать, помечаем как невалидную
			if integration:
				integration.is_valid = False
				await session.commit()
			return None

	@staticmethod
	async def get_oauth_config(
		session: AsyncSession, user_id: uuid.UUID, kind: str
	) -> Optional[Dict[str, Any]]:
		"""Получить OAuth конфигурацию (не зашифрованную)"""
		integration = await IntegrationService.get_integration(session, user_id, kind)
		if not integration:
			return None
		
		# OAuth config хранится отдельно, не зашифрован
		return integration.auth_data.get("oauth_config")

	@staticmethod
	async def save_oauth_config(
		session: AsyncSession,
		user_id: uuid.UUID,
		kind: str,
		client_id: str,
		client_secret: str,
		redirect_uri: Optional[str] = None,
		developer_token: Optional[str] = None,
		login_customer_id: Optional[str] = None,
	) -> Integration:
		"""Сохранить OAuth конфигурацию"""
		integration = await IntegrationService.get_integration(session, user_id, kind)
		existing_oauth_config = integration.auth_data.get("oauth_config") if integration else {}
		existing_account_info = integration.auth_data.get("account_info") if integration else None
		
		token_to_store = developer_token or (existing_oauth_config.get("developer_token") if existing_oauth_config else None)
		login_customer_to_store = login_customer_id
		if login_customer_to_store is None and existing_oauth_config:
			login_customer_to_store = existing_oauth_config.get("login_customer_id")
		
		oauth_config = {
			"client_id": client_id,
			"client_secret": client_secret,
			"redirect_uri": redirect_uri,
		}
		
		if kind == "gads":
			if not token_to_store:
				raise ValueError("Для интеграции Google Ads требуется developer token")
			oauth_config["developer_token"] = token_to_store
			if login_customer_to_store:
				oauth_config["login_customer_id"] = login_customer_to_store

		if integration:
			# Обновляем существующую интеграцию
			# Сохраняем oauth_config отдельно от зашифрованных токенов
			if "encrypted" in integration.auth_data:
				# Сохраняем существующие токены
				integration.auth_data = {
					"oauth_config": oauth_config,
					"encrypted": integration.auth_data["encrypted"],
				}
			else:
				integration.auth_data = {"oauth_config": oauth_config}
			if existing_account_info:
				integration.auth_data["account_info"] = existing_account_info
			await session.commit()
			await session.refresh(integration)
			return integration
		else:
			# Создаём новую интеграцию только с OAuth config (без токенов)
			integration = Integration(
				user_id=user_id,
				kind=kind,
				auth_data={"oauth_config": oauth_config},
				is_valid=False,  # Токены ещё не получены
			)
			session.add(integration)
			await session.commit()
			await session.refresh(integration)
			return integration
	
	@staticmethod
	def get_account_info(integration: Integration) -> Dict[str, Any]:
		"""Извлечь сохранённую информацию об аккаунте"""
		if not integration or not integration.auth_data:
			return {}
		account_info = integration.auth_data.get("account_info")
		if isinstance(account_info, dict):
			return account_info
		return {}
	
	@staticmethod
	def get_account_name(integration: Integration) -> Optional[str]:
		"""Получить человекочитаемое имя аккаунта"""
		account_info = IntegrationService.get_account_info(integration)
		if not account_info:
			return None
		
		for key in ["display_name", "name", "email", "username", "customer_id", "login_customer_id"]:
			value = account_info.get(key)
			if value:
				return value
		return account_info.get("id")

	@staticmethod
	async def test_connection(
		session: AsyncSession, user_id: uuid.UUID, kind: str
	) -> Dict[str, Any]:
		"""Проверить соединение с сервисом"""
		auth_data = await IntegrationService.get_decrypted_auth_data(
			session, user_id, kind
		)

		if not auth_data:
			return {"status": "error", "message": "Интеграция не найдена или невалидна"}

		try:
			if kind == "youtube":
				# Тестовый запрос к YouTube API
				from app.services.youtube_service import YouTubeService
				client = YouTubeService.get_client(auth_data)
				# Используем channels().list() с scope youtube.readonly
				# Если scope нет, пробуем просто проверить валидность credentials
				try:
					request = client.channels().list(part="snippet", mine=True)
					response = request.execute()
					channel_title = response.get("items", [{}])[0].get("snippet", {}).get("title", "Unknown")
					return {"status": "ok", "message": f"Подключено как: {channel_title}"}
				except HttpError as e:
					if e.resp.status == 403:
						# Проверяем, что credentials валидны хотя бы
						from google.oauth2.credentials import Credentials
						creds = Credentials.from_authorized_user_info(auth_data)
						if creds.valid:
							return {
								"status": "ok",
								"message": "Подключение успешно (требуется повторная авторизация для полного доступа)"
							}
						else:
							return {"status": "error", "message": "Токен невалиден или истёк"}
					raise

			elif kind == "gdrive":
				# Тестовый запрос к Google Drive API
				from app.services.google_drive_service import GoogleDriveService
				result = await GoogleDriveService.test_connection(auth_data)
				return result

			elif kind == "gads":
				# Тестовый запрос к Google Ads API
				from app.services.google_ads_service import GoogleAdsService
				result = await GoogleAdsService.test_connection(auth_data)
				if result.get("account_info"):
					integration = await IntegrationService.get_integration(session, user_id, kind)
					if integration:
						integration.auth_data = {
							**integration.auth_data,
							"account_info": result["account_info"],
						}
						await session.commit()
				return result

			elif kind == "telegram":
				# Тестовое сообщение через Telegram
				from app.services.telegram_service import TelegramService
				result = await TelegramService.test_connection(auth_data)
				if result.get("meta"):
					integration = await IntegrationService.get_integration(session, user_id, kind)
					if integration:
						integration.auth_data = {
							**integration.auth_data,
							"account_info": result["meta"],
						}
						await session.commit()
				return result

			else:
				return {"status": "error", "message": f"Неизвестный тип интеграции: {kind}"}

		except Exception as e:
			# Помечаем интеграцию как невалидную
			integration = await IntegrationService.get_integration(session, user_id, kind)
			if integration:
				integration.is_valid = False
				await session.commit()

			return {"status": "error", "message": str(e)}

