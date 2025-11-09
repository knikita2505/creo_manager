const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface IntegrationResponse {
	id: string
	kind: string
	is_valid: boolean
	created_at: string
	account_name?: string | null
	account_details?: Record<string, unknown> | null
}

export interface IntegrationListResponse {
	integrations: IntegrationResponse[]
}

export interface IntegrationConnectRequest {
	bot_token?: string
	code?: string
	state?: string
}

export interface IntegrationConnectResponse {
	kind: string
	status: string
	created_at: string
	message?: string
}

export interface IntegrationDisconnectResponse {
	kind: string
	status: string
}

export interface IntegrationTestResponse {
	kind: string
	status: string
	message?: string
}

export interface OAuthAuthorizeResponse {
	authorization_url: string
	state: string
}

export interface OAuthConfigRequest {
	client_id: string
	client_secret: string
	redirect_uri?: string
	developer_token?: string
	login_customer_id?: string
}

export interface OAuthConfigResponse {
	kind: string
	has_config: boolean
	redirect_uri?: string
	has_developer_token?: boolean | null
	login_customer_id?: string | null
}

export async function getIntegrations(): Promise<IntegrationListResponse> {
	const response = await fetch(`${API_BASE_URL}/api/v1/integrations/`)
	
	if (!response.ok) {
		throw new Error('Ошибка получения списка интеграций')
	}
	
	return response.json()
}

export async function getIntegration(kind: string): Promise<IntegrationResponse> {
	const response = await fetch(`${API_BASE_URL}/api/v1/integrations/${kind}`)
	
	if (!response.ok) {
		if (response.status === 404) {
			return null as any
		}
		throw new Error('Ошибка получения интеграции')
	}
	
	return response.json()
}

export async function getOAuthUrl(kind: string): Promise<OAuthAuthorizeResponse> {
	const response = await fetch(`${API_BASE_URL}/api/v1/integrations/${kind}/oauth/authorize`)
	
	if (!response.ok) {
		const error = await response.json()
		throw new Error(error.detail || 'Ошибка получения OAuth URL')
	}
	
	return response.json()
}

export async function connectTelegram(botToken: string): Promise<IntegrationConnectResponse> {
	const response = await fetch(`${API_BASE_URL}/api/v1/integrations/telegram/connect`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
		},
		body: JSON.stringify({ bot_token: botToken }),
	})
	
	if (!response.ok) {
		const error = await response.json()
		throw new Error(error.detail || 'Ошибка подключения Telegram')
	}
	
	return response.json()
}

export async function disconnectIntegration(kind: string): Promise<IntegrationDisconnectResponse> {
	const response = await fetch(`${API_BASE_URL}/api/v1/integrations/${kind}`, {
		method: 'DELETE',
	})
	
	if (!response.ok) {
		const error = await response.json()
		throw new Error(error.detail || 'Ошибка отключения интеграции')
	}
	
	return response.json()
}

export async function testIntegration(kind: string): Promise<IntegrationTestResponse> {
	const response = await fetch(`${API_BASE_URL}/api/v1/integrations/${kind}/test`, {
		method: 'POST',
	})
	
	if (!response.ok) {
		const error = await response.json()
		throw new Error(error.detail || 'Ошибка проверки соединения')
	}
	
	return response.json()
}

export async function getOAuthConfig(kind: string): Promise<OAuthConfigResponse> {
	const response = await fetch(`${API_BASE_URL}/api/v1/integrations/${kind}/oauth/config`)
	
	if (!response.ok) {
		const error = await response.json()
		throw new Error(error.detail || 'Ошибка получения OAuth конфигурации')
	}
	
	return response.json()
}

export async function saveOAuthConfig(
	kind: string,
	config: OAuthConfigRequest
): Promise<OAuthConfigResponse> {
	const response = await fetch(`${API_BASE_URL}/api/v1/integrations/${kind}/oauth/config`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
		},
		body: JSON.stringify(config),
	})
	
	if (!response.ok) {
		const error = await response.json()
		throw new Error(error.detail || 'Ошибка сохранения OAuth конфигурации')
	}
	
	return response.json()
}

