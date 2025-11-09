"""Схемы для API интеграций"""
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class IntegrationResponse(BaseModel):
	id: UUID
	kind: str
	is_valid: bool
	created_at: datetime
	account_name: Optional[str] = None
	account_details: Optional[Dict[str, Any]] = None

	class Config:
		from_attributes = True


class IntegrationListResponse(BaseModel):
	integrations: list[IntegrationResponse]


class IntegrationConnectRequest(BaseModel):
	"""Запрос на подключение интеграции"""
	# Для Telegram: bot_token
	bot_token: Optional[str] = None
	# Для OAuth: будет обрабатываться через callback
	code: Optional[str] = None
	state: Optional[str] = None


class IntegrationConnectResponse(BaseModel):
	kind: str
	status: str
	created_at: datetime
	message: Optional[str] = None


class IntegrationDisconnectResponse(BaseModel):
	kind: str
	status: str


class IntegrationTestResponse(BaseModel):
	kind: str
	status: str
	message: Optional[str] = None


class OAuthAuthorizeResponse(BaseModel):
	authorization_url: str
	state: str


class OAuthConfigRequest(BaseModel):
	"""Запрос на сохранение OAuth конфигурации"""
	client_id: str
	client_secret: str
	redirect_uri: Optional[str] = None
	developer_token: Optional[str] = None
	login_customer_id: Optional[str] = None


class OAuthConfigResponse(BaseModel):
	"""Ответ с OAuth конфигурацией"""
	kind: str
	has_config: bool
	redirect_uri: Optional[str] = None
	has_developer_token: Optional[bool] = None
	login_customer_id: Optional[str] = None

