"""API endpoints для управления интеграциями"""
import uuid
import secrets
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.config import settings
from app.api.v1.schemas.integration import (
	IntegrationResponse,
	IntegrationListResponse,
	IntegrationConnectRequest,
	IntegrationConnectResponse,
	IntegrationDisconnectResponse,
	IntegrationTestResponse,
	OAuthAuthorizeResponse,
	OAuthConfigRequest,
	OAuthConfigResponse,
)
from app.models import Integration, User
from app.services.integration_service import IntegrationService, INTEGRATION_DEFAULT_SCOPES
from app.services.youtube_service import YouTubeService
from app.services.google_drive_service import GoogleDriveService
from app.services.telegram_service import TelegramService

# Google Ads Service импортируется лениво, так как требует дополнительных зависимостей

router = APIRouter()

# Временное хранилище для OAuth state (в production использовать Redis)
oauth_states: dict[str, uuid.UUID] = {}

# Тестовый пользователь ID (для MVP)
TEST_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


async def get_or_create_test_user(db: AsyncSession) -> User:
	"""Получить или создать тестового пользователя (для MVP)"""
	from sqlalchemy import select
	
	# Пытаемся найти существующего пользователя
	query = select(User).where(User.id == TEST_USER_ID)
	result = await db.execute(query)
	user = result.scalar_one_or_none()
	
	if user:
		return user
	
	# Создаём нового тестового пользователя
	user = User(
		id=TEST_USER_ID,
		email="test@example.com",
		name="Test User",
	)
	db.add(user)
	await db.commit()
	await db.refresh(user)
	return user


async def get_current_user_id(db: AsyncSession = Depends(get_db)) -> uuid.UUID:
	"""Временная функция для получения user_id. В будущем заменить на реальную аутентификацию"""
	# TODO: Реализовать реальную аутентификацию
	# Для MVP создаём/получаем тестового пользователя
	user = await get_or_create_test_user(db)
	return user.id


@router.get("/", response_model=IntegrationListResponse)
async def list_integrations(
	db: AsyncSession = Depends(get_db),
	current_user_id: uuid.UUID = Depends(get_current_user_id),
):
	"""Получить список всех интеграций пользователя"""
	integrations = await IntegrationService.get_all_integrations(db, current_user_id)
	return IntegrationListResponse(
		integrations=[
			IntegrationResponse(
				id=integration.id,
				kind=integration.kind,
				is_valid=integration.is_valid,
				created_at=integration.created_at,
				account_name=IntegrationService.get_account_name(integration),
				account_details=IntegrationService.get_account_info(integration) or None,
			)
			for integration in integrations
		]
	)


@router.get("/{kind}", response_model=IntegrationResponse)
async def get_integration(
	kind: str,
	db: AsyncSession = Depends(get_db),
	current_user_id: uuid.UUID = Depends(get_current_user_id),
):
	"""Получить конкретную интеграцию"""
	integration = await IntegrationService.get_integration(db, current_user_id, kind)
	if not integration:
		raise HTTPException(status_code=404, detail="Интеграция не найдена")

	return IntegrationResponse(
		id=integration.id,
		kind=integration.kind,
		is_valid=integration.is_valid,
		created_at=integration.created_at,
		account_name=IntegrationService.get_account_name(integration),
		account_details=IntegrationService.get_account_info(integration) or None,
	)


@router.get("/{kind}/oauth/authorize", response_model=OAuthAuthorizeResponse)
async def oauth_authorize(
	kind: str,
	db: AsyncSession = Depends(get_db),
	current_user_id: uuid.UUID = Depends(get_current_user_id),
):
	"""Получить URL для OAuth авторизации"""
	# Получаем OAuth config из базы, если есть
	oauth_config = await IntegrationService.get_oauth_config(db, current_user_id, kind)
	
	# Логируем для отладки (в production убрать)
	if oauth_config:
		print(f"✅ OAuth config найден для {kind}: client_id={oauth_config.get('client_id', '')[:20]}...")
	else:
		print(f"⚠️ OAuth config не найден в базе для {kind}, используем settings")
	
	# Извлекаем параметры из config или используем settings
	client_id = oauth_config.get("client_id") if oauth_config else None
	client_secret = oauth_config.get("client_secret") if oauth_config else None
	redirect_uri = oauth_config.get("redirect_uri") if oauth_config else None
	
	# Если config не найден в базе, используем settings (для обратной совместимости)
	if not client_id:
		if kind == "youtube":
			client_id = settings.YOUTUBE_CLIENT_ID
			client_secret = settings.YOUTUBE_CLIENT_SECRET
		elif kind == "gdrive":
			client_id = settings.GDRIVE_CLIENT_ID
			client_secret = settings.GDRIVE_CLIENT_SECRET
		elif kind == "gads":
			client_id = settings.GADS_CLIENT_ID
			client_secret = settings.GADS_CLIENT_SECRET
	
	# Проверяем, что credentials заданы
	if not client_id or not client_secret:
		raise HTTPException(
			status_code=400,
			detail="OAuth credentials не настроены. Пожалуйста, укажите Client ID и Client Secret в настройках интеграции."
		)
	
	if kind == "gads":
		developer_token = oauth_config.get("developer_token") if oauth_config else None
		if not developer_token and not settings.GADS_DEVELOPER_TOKEN:
			raise HTTPException(
				status_code=400,
				detail="Для интеграции Google Ads укажите developer token в настройках интеграции.",
			)
	
	# Формируем redirect_uri - должен указывать на backend
	if not redirect_uri:
		redirect_uri = f"{settings.BACKEND_URL}/api/v1/integrations/{kind}/oauth/callback"
	
	requested_scopes: Optional[list[str]] = None
	if kind == "gads":
		existing_auth = await IntegrationService.get_decrypted_auth_data(db, current_user_id, kind)
		existing_scopes = []
		if existing_auth:
			scopes = existing_auth.get("scopes")
			if isinstance(scopes, list):
				existing_scopes = scopes
		default_scopes = INTEGRATION_DEFAULT_SCOPES.get("gads", [])
		requested_scopes = sorted(set(default_scopes + existing_scopes))

	try:
		if kind == "youtube":
			flow = YouTubeService.get_oauth_flow(client_id, client_secret, redirect_uri)
		elif kind == "gdrive":
			flow = GoogleDriveService.get_oauth_flow(client_id, client_secret, redirect_uri)
		elif kind == "gads":
			from app.services.google_ads_service import GoogleAdsService
			flow = GoogleAdsService.get_oauth_flow(
				client_id, client_secret, redirect_uri, scopes=requested_scopes
			)
		else:
			raise HTTPException(status_code=400, detail=f"OAuth не поддерживается для {kind}")
	except ValueError as e:
		# Ошибки валидации
		raise HTTPException(
			status_code=400,
			detail=f"Ошибка валидации OAuth credentials: {str(e)}"
		)
	except Exception as e:
		# Другие ошибки
		import traceback
		error_detail = f"Ошибка создания OAuth flow: {str(e)}"
		print(f"Ошибка в oauth_authorize для {kind}:")
		print(traceback.format_exc())
		raise HTTPException(
			status_code=400,
			detail=error_detail
		)

	# Генерируем state для безопасности
	state = secrets.token_urlsafe(32)
	oauth_states[state] = current_user_id

	# Генерируем authorization URL
	authorization_url, _ = flow.authorization_url(
		access_type="offline",
		include_granted_scopes="true",
		prompt="consent",
		state=state,
	)

	return OAuthAuthorizeResponse(authorization_url=authorization_url, state=state)


@router.get("/{kind}/oauth/callback")
async def oauth_callback(
	kind: str,
	code: str = Query(...),
	state: str = Query(...),
	scope: Optional[str] = Query(None),
	db: AsyncSession = Depends(get_db),
):
	"""Обработка OAuth callback"""
	# Проверяем state
	if state not in oauth_states:
		raise HTTPException(status_code=400, detail="Неверный state параметр")

	user_id = oauth_states.pop(state)

	# Получаем OAuth config из базы, если есть
	oauth_config = await IntegrationService.get_oauth_config(db, user_id, kind)
	
	# Извлекаем параметры из config или используем settings
	client_id = oauth_config.get("client_id") if oauth_config else None
	client_secret = oauth_config.get("client_secret") if oauth_config else None
	redirect_uri = oauth_config.get("redirect_uri") if oauth_config else None
	
	# Формируем redirect_uri - должен указывать на backend
	if not redirect_uri:
		redirect_uri = f"{settings.BACKEND_URL}/api/v1/integrations/{kind}/oauth/callback"
	
	# Получаем flow для нужного сервиса
	requested_scopes: Optional[list[str]] = None
	scope_param_scopes: list[str] = []
	if scope:
		scope_param_scopes = sorted(set(scope.split(" ")))

	if kind == "gads":
		existing_auth = await IntegrationService.get_decrypted_auth_data(db, user_id, kind)
		existing_scopes: list[str] = []
		if existing_auth:
			scopes = existing_auth.get("scopes")
			if isinstance(scopes, list):
				existing_scopes = scopes
		default_scopes = INTEGRATION_DEFAULT_SCOPES.get("gads", [])
		requested_scopes = sorted(set(default_scopes + existing_scopes))

	final_scopes = scope_param_scopes or requested_scopes

	if kind == "youtube":
		flow = YouTubeService.get_oauth_flow(client_id, client_secret, redirect_uri)
	elif kind == "gdrive":
		flow = GoogleDriveService.get_oauth_flow(client_id, client_secret, redirect_uri)
	elif kind == "gads":
		from app.services.google_ads_service import GoogleAdsService
		flow = GoogleAdsService.get_oauth_flow(
			client_id, client_secret, redirect_uri, scopes=final_scopes
		)
	else:
		raise HTTPException(status_code=400, detail=f"OAuth не поддерживается для {kind}")

	try:
		# Обмениваем код на токены
		flow.fetch_token(code=code)
		credentials = flow.credentials

		# Сохраняем credentials
		# Используем client_id и client_secret из oauth_config, если они есть
		# Иначе используем из credentials
		saved_client_id = client_id or credentials.client_id
		saved_client_secret = client_secret or credentials.client_secret
		
		# Проверяем, что все обязательные поля есть
		if not credentials.token:
			raise ValueError("Token не получен от Google OAuth")
		if not credentials.refresh_token:
			print("⚠️ Предупреждение: refresh_token не получен. Токен может истечь.")
		
		token_scopes: list[str] = []
		if scope_param_scopes:
			token_scopes = scope_param_scopes
		elif credentials.scopes:
			token_scopes = list(credentials.scopes)
		elif requested_scopes:
			token_scopes = requested_scopes

		auth_data = {
			"token": credentials.token,
			"refresh_token": credentials.refresh_token,
			"token_uri": credentials.token_uri or "https://oauth2.googleapis.com/token",
			"client_id": saved_client_id,
			"client_secret": saved_client_secret,
			"scopes": token_scopes,
		}
		
		# Логируем для отладки
		print(f"✅ Сохранение credentials для {kind}:")
		print(f"   - token: {'есть' if auth_data['token'] else 'отсутствует'}")
		print(f"   - refresh_token: {'есть' if auth_data['refresh_token'] else 'отсутствует'}")
		print(f"   - client_id: {'есть' if auth_data['client_id'] else 'отсутствует'}")
		print(f"   - client_secret: {'есть' if auth_data['client_secret'] else 'отсутствует'}")

		account_info = None
		try:
			if kind == "youtube":
				account_info = YouTubeService.get_account_info(auth_data)
			elif kind == "gdrive":
				account_info = await GoogleDriveService.get_account_info(auth_data)
			elif kind == "gads":
				from app.services.google_ads_service import GoogleAdsService
				developer_token = None
				if oauth_config and oauth_config.get("developer_token"):
					developer_token = oauth_config["developer_token"]
				elif settings.GADS_DEVELOPER_TOKEN:
					developer_token = settings.GADS_DEVELOPER_TOKEN
				if not developer_token:
					raise HTTPException(
						status_code=400,
						detail="Для интеграции Google Ads укажите developer token в настройках и повторите авторизацию.",
					)
				login_customer_id = oauth_config.get("login_customer_id") if oauth_config else None
				account_info = await GoogleAdsService.get_account_info(
					access_token=auth_data["token"],
					developer_token=developer_token,
					login_customer_id=login_customer_id,
				)
			# Для других интеграций account_info не требуется
		except HTTPException:
			raise
		except Exception as info_error:
			print(f"⚠️ Не удалось получить информацию об аккаунте для {kind}: {info_error}")

		await IntegrationService.create_or_update_integration(
			db, user_id, kind, auth_data, is_valid=True, account_info=account_info
		)

		# Перенаправляем на страницу интеграций
		return RedirectResponse(url=f"{settings.FRONTEND_URL}/integrations?connected={kind}")

	except Exception as e:
		raise HTTPException(status_code=400, detail=f"Ошибка авторизации: {str(e)}")


@router.post("/telegram/connect", response_model=IntegrationConnectResponse)
async def connect_telegram(
	request: IntegrationConnectRequest,
	db: AsyncSession = Depends(get_db),
	current_user_id: uuid.UUID = Depends(get_current_user_id),
):
	"""Подключить Telegram бота"""
	if not request.bot_token:
		raise HTTPException(status_code=400, detail="bot_token обязателен")

	# Проверяем токен
	test_result = await TelegramService.test_connection({"bot_token": request.bot_token})
	if test_result["status"] != "ok":
		raise HTTPException(status_code=400, detail=test_result.get("message", "Неверный токен"))

	# Сохраняем интеграцию
	auth_data = {"bot_token": request.bot_token}
	account_info = test_result.get("meta")
	integration = await IntegrationService.create_or_update_integration(
		db, current_user_id, "telegram", auth_data, is_valid=True, account_info=account_info
	)

	return IntegrationConnectResponse(
		kind="telegram",
		status="connected",
		created_at=integration.created_at,
		message=test_result.get("message"),
	)


@router.delete("/{kind}", response_model=IntegrationDisconnectResponse)
async def disconnect_integration(
	kind: str,
	db: AsyncSession = Depends(get_db),
	current_user_id: uuid.UUID = Depends(get_current_user_id),
):
	"""Отключить интеграцию"""
	success = await IntegrationService.delete_integration(db, current_user_id, kind)
	if not success:
		raise HTTPException(status_code=404, detail="Интеграция не найдена")

	return IntegrationDisconnectResponse(kind=kind, status="disconnected")


@router.post("/{kind}/test", response_model=IntegrationTestResponse)
async def test_integration(
	kind: str,
	db: AsyncSession = Depends(get_db),
	current_user_id: uuid.UUID = Depends(get_current_user_id),
):
	"""Проверить соединение с интеграцией"""
	result = await IntegrationService.test_connection(db, current_user_id, kind)
	return IntegrationTestResponse(
		kind=kind, status=result["status"], message=result.get("message")
	)


@router.get("/{kind}/oauth/config", response_model=OAuthConfigResponse)
async def get_oauth_config(
	kind: str,
	db: AsyncSession = Depends(get_db),
	current_user_id: uuid.UUID = Depends(get_current_user_id),
):
	"""Получить OAuth конфигурацию"""
	if kind not in ["youtube", "gdrive", "gads"]:
		raise HTTPException(status_code=400, detail=f"OAuth не поддерживается для {kind}")
	
	oauth_config = await IntegrationService.get_oauth_config(db, current_user_id, kind)
	
	return OAuthConfigResponse(
		kind=kind,
		has_config=oauth_config is not None and oauth_config.get("client_id") is not None,
		redirect_uri=oauth_config.get("redirect_uri") if oauth_config else None,
		has_developer_token=oauth_config.get("developer_token") is not None if oauth_config else None,
		login_customer_id=oauth_config.get("login_customer_id") if oauth_config else None,
	)


@router.post("/{kind}/oauth/config", response_model=OAuthConfigResponse)
async def save_oauth_config(
	kind: str,
	request: OAuthConfigRequest,
	db: AsyncSession = Depends(get_db),
	current_user_id: uuid.UUID = Depends(get_current_user_id),
):
	"""Сохранить OAuth конфигурацию"""
	if kind not in ["youtube", "gdrive", "gads"]:
		raise HTTPException(status_code=400, detail=f"OAuth не поддерживается для {kind}")
	
	if not request.client_id or not request.client_secret:
		raise HTTPException(status_code=400, detail="client_id и client_secret обязательны")
	
	# Формируем redirect_uri, если не указан
	redirect_uri = request.redirect_uri
	if not redirect_uri:
		redirect_uri = f"{settings.BACKEND_URL}/api/v1/integrations/{kind}/oauth/callback"
	
	# Сохраняем конфигурацию
	try:
		integration = await IntegrationService.save_oauth_config(
			db,
			current_user_id,
			kind,
			request.client_id,
			request.client_secret,
			redirect_uri,
			request.developer_token,
			request.login_customer_id,
		)
	except ValueError as e:
		raise HTTPException(status_code=400, detail=str(e))
	
	oauth_config = integration.auth_data.get("oauth_config") if integration else None
	
	return OAuthConfigResponse(
		kind=kind,
		has_config=True,
		redirect_uri=redirect_uri,
		has_developer_token=oauth_config.get("developer_token") is not None if oauth_config else None,
		login_customer_id=oauth_config.get("login_customer_id") if oauth_config else None,
	)

