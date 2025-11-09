'use client'

import { useState } from 'react'
import { CheckCircle2, XCircle, AlertCircle, Link2, Trash2, RefreshCw, Loader2 } from 'lucide-react'
import { IntegrationResponse, OAuthConfigRequest } from '@/lib/api-integrations'
import {
	getOAuthUrl,
	connectTelegram,
	disconnectIntegration,
	testIntegration,
	getOAuthConfig,
	saveOAuthConfig,
} from '@/lib/api-integrations'
import { cn } from '@/lib/utils'

interface IntegrationCardProps {
	kind: string
	integration?: IntegrationResponse
	onUpdate: () => void
}

const INTEGRATION_INFO = {
	youtube: {
		name: 'YouTube',
		description: 'Загрузка видео на YouTube',
		icon: '🎥',
		oauth: true,
	},
	gdrive: {
		name: 'Google Drive',
		description: 'Импорт видео из Google Drive',
		icon: '📁',
		oauth: true,
	},
	gads: {
		name: 'Google Ads',
		description: 'Мониторинг банов в Google Ads',
		icon: '📊',
		oauth: true,
	},
	telegram: {
		name: 'Telegram',
		description: 'Уведомления о банах и статусах',
		icon: '📱',
		oauth: false,
	},
}

export function IntegrationCard({ kind, integration, onUpdate }: IntegrationCardProps) {
	const [isConnecting, setIsConnecting] = useState(false)
	const [isTesting, setIsTesting] = useState(false)
	const [isDisconnecting, setIsDisconnecting] = useState(false)
	const [telegramToken, setTelegramToken] = useState('')
	const [error, setError] = useState<string | null>(null)
	
	// OAuth credentials state
	const [showOAuthConfig, setShowOAuthConfig] = useState(false)
	const [oauthClientId, setOAuthClientId] = useState('')
	const [oauthClientSecret, setOAuthClientSecret] = useState('')
	const [oauthRedirectUri, setOAuthRedirectUri] = useState('')
	const [isSavingConfig, setIsSavingConfig] = useState(false)
	const [isLoadingConfig, setIsLoadingConfig] = useState(false)
	const [oauthDeveloperToken, setOAuthDeveloperToken] = useState('')
	const [hasDeveloperToken, setHasDeveloperToken] = useState(false)
	const [oauthLoginCustomerId, setOAuthLoginCustomerId] = useState('')

	const info = INTEGRATION_INFO[kind as keyof typeof INTEGRATION_INFO] || {
		name: kind,
		description: '',
		icon: '🔌',
		oauth: false,
	}

	const status = integration
		? integration.is_valid
			? 'active'
			: 'error'
		: 'disconnected'
	
	const formatCustomerId = (value: string) => {
		const digits = value.replace(/\D/g, '')
		if (digits.length === 10) {
			return `${digits.slice(0, 3)}-${digits.slice(3, 6)}-${digits.slice(6)}`
		}
		return value
	}

	const accountDetails = integration?.account_details as Record<string, unknown> | undefined | null
	const accountLabel = (() => {
		if (!integration) return null
		if (typeof integration.account_name === 'string' && integration.account_name.trim()) {
			return integration.account_name
		}
		if (!accountDetails) return null
		const candidates = ['display_name', 'email', 'username', 'customer_id', 'login_customer_id']
		for (const key of candidates) {
			const value = accountDetails[key]
			if (typeof value === 'string' && value.trim()) {
				if (kind === 'gads' && (key === 'customer_id' || key === 'login_customer_id')) {
					return formatCustomerId(value)
				}
				return value
			}
		}
		return null
	})()
	const accountSecondary = (() => {
		if (!accountDetails) return null
		if (kind === 'gads') {
			const loginId = accountDetails['login_customer_id']
			if (typeof loginId === 'string' && loginId.trim()) {
				return `Login customer ID: ${formatCustomerId(loginId)}`
			}
			const customerId = accountDetails['customer_id']
			if (typeof customerId === 'string' && customerId.trim()) {
				return `Customer ID: ${formatCustomerId(customerId)}`
			}
		}
		if (kind === 'youtube') {
			const channelId = accountDetails['id']
			if (typeof channelId === 'string' && channelId.trim()) {
				return `ID: ${channelId}`
			}
		}
		if (kind === 'gdrive') {
			const email = accountDetails['email']
			if (typeof email === 'string' && email.trim() && email !== accountLabel) {
				return email
			}
		}
		if (kind === 'telegram') {
			const username = accountDetails['username']
			if (typeof username === 'string' && username.trim() && username !== accountLabel) {
				return `@${username.replace(/^@/, '')}`
			}
		}
		return null
	})()

	// Загружаем OAuth config при открытии формы
	const loadOAuthConfig = async () => {
		if (!info.oauth) return
		setIsLoadingConfig(true)
		try {
			const config = await getOAuthConfig(kind)
			if (config.has_config) {
				// Показываем только redirect_uri, client_id и client_secret не возвращаем из соображений безопасности
				// Но пользователь может их ввести заново
				setOAuthRedirectUri(config.redirect_uri || '')
			}
			setHasDeveloperToken(Boolean(config.has_developer_token))
			setOAuthLoginCustomerId(config.login_customer_id || '')
			setOAuthDeveloperToken('')
		} catch (err) {
			// Игнорируем ошибку, если config не существует
		} finally {
			setIsLoadingConfig(false)
		}
	}

	const handleSaveOAuthConfig = async () => {
		const clientId = oauthClientId.trim()
		const clientSecret = oauthClientSecret.trim()
		const redirectUri = oauthRedirectUri.trim()
		
		if (!clientId || !clientSecret) {
			setError('Укажите Client ID и Client Secret')
			return
		}
		
		let developerToken = ''
		let loginCustomerId = ''
		if (kind === 'gads') {
			developerToken = oauthDeveloperToken.trim()
			loginCustomerId = oauthLoginCustomerId.trim()
			if (!developerToken && !hasDeveloperToken) {
				setError('Укажите developer token для Google Ads')
				return
			}
		}
		
		setIsSavingConfig(true)
		setError(null)
		try {
			const payload: OAuthConfigRequest = {
				client_id: clientId,
				client_secret: clientSecret,
				redirect_uri: redirectUri || undefined,
			}
			if (kind === 'gads') {
				if (developerToken) {
					payload.developer_token = developerToken
				}
				if (loginCustomerId) {
					payload.login_customer_id = loginCustomerId
				}
			}
			
			await saveOAuthConfig(kind, payload)
			setShowOAuthConfig(false)
			setOAuthClientId('')
			setOAuthClientSecret('')
			setOAuthRedirectUri('')
			setOAuthDeveloperToken('')
			setOAuthLoginCustomerId('')
			if (kind === 'gads') {
				setHasDeveloperToken(Boolean(developerToken || hasDeveloperToken))
			}
			onUpdate()
			
			// Автоматически открываем окно авторизации после сохранения ключей
			if (info.oauth) {
				setTimeout(() => {
					handleConnect()
				}, 500) // Небольшая задержка для обновления UI
			}
		} catch (err) {
			setError(err instanceof Error ? err.message : 'Ошибка сохранения конфигурации')
		} finally {
			setIsSavingConfig(false)
		}
	}

	const handleConnect = async () => {
		if (kind === 'telegram') {
			if (!telegramToken.trim()) {
				setError('Введите bot token')
				return
			}
			setIsConnecting(true)
			setError(null)
			try {
				await connectTelegram(telegramToken.trim())
				setTelegramToken('')
				onUpdate()
			} catch (err) {
				setError(err instanceof Error ? err.message : 'Ошибка подключения')
			} finally {
				setIsConnecting(false)
			}
		} else {
			// OAuth интеграции
			setIsConnecting(true)
			setError(null)
			try {
				const { authorization_url } = await getOAuthUrl(kind)
				window.location.href = authorization_url
			} catch (err) {
				setError(err instanceof Error ? err.message : 'Ошибка получения OAuth URL')
				setIsConnecting(false)
			}
		}
	}

	const handleDisconnect = async () => {
		if (!confirm(`Отключить интеграцию ${info.name}?`)) {
			return
		}

		setIsDisconnecting(true)
		setError(null)
		try {
			await disconnectIntegration(kind)
			onUpdate()
		} catch (err) {
			setError(err instanceof Error ? err.message : 'Ошибка отключения')
		} finally {
			setIsDisconnecting(false)
		}
	}

	const handleTest = async () => {
		setIsTesting(true)
		setError(null)
		try {
			const result = await testIntegration(kind)
			if (result.status === 'ok') {
				alert(`✅ ${result.message || 'Подключение успешно'}`)
			} else {
				setError(result.message || 'Ошибка подключения')
			}
			onUpdate()
		} catch (err) {
			setError(err instanceof Error ? err.message : 'Ошибка проверки')
		} finally {
			setIsTesting(false)
		}
	}

	return (
		<div className="rounded-xl shadow-md bg-white px-5 py-4">
			<div className="flex items-start justify-between mb-4">
				<div className="flex items-center space-x-3">
					<span className="text-2xl">{info.icon}</span>
					<div>
						<h3 className="text-lg font-medium text-gray-900">{info.name}</h3>
						<p className="text-sm text-gray-500">{info.description}</p>
					</div>
				</div>
				{status === 'active' && (
					<CheckCircle2 className="h-5 w-5 text-success flex-shrink-0" />
				)}
				{status === 'error' && (
					<XCircle className="h-5 w-5 text-destructive flex-shrink-0" />
				)}
				{status === 'disconnected' && (
					<AlertCircle className="h-5 w-5 text-gray-400 flex-shrink-0" />
				)}
			</div>

			<div className="mb-4">
				<div className="flex items-center space-x-2 mb-2">
					<span
						className={cn(
							'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
							status === 'active' && 'bg-green-100 text-green-800',
							status === 'error' && 'bg-red-100 text-red-800',
							status === 'disconnected' && 'bg-gray-100 text-gray-800'
						)}
					>
						{status === 'active' && 'Активно'}
						{status === 'error' && 'Ошибка'}
						{status === 'disconnected' && 'Не подключено'}
					</span>
					{integration && (
						<span className="text-xs text-gray-500">
							Подключено {new Date(integration.created_at).toLocaleDateString('ru-RU')}
						</span>
					)}
				</div>

				{integration && (accountLabel || accountSecondary) && (
					<div className="mt-2 text-sm text-gray-600 space-y-1">
						{accountLabel && (
							<div>
								<span className="font-medium">Аккаунт:</span> {accountLabel}
							</div>
						)}
						{accountSecondary && (
							<div className="text-xs text-gray-500">{accountSecondary}</div>
						)}
					</div>
				)}

				{kind === 'telegram' && !integration && (
					<div className="mt-3">
						<label className="block text-sm font-medium text-gray-700 mb-1">
							Bot Token
						</label>
						<input
							type="password"
							value={telegramToken}
							onChange={(e) => setTelegramToken(e.target.value)}
							placeholder="Введите токен бота"
							className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
						/>
						<p className="mt-1 text-xs text-gray-500">
							Получите токен у @BotFather в Telegram
						</p>
					</div>
				)}

				{info.oauth && !integration && (
					<div className="mt-3">
						{!showOAuthConfig ? (
							<button
								type="button"
								onClick={() => {
									setShowOAuthConfig(true)
									loadOAuthConfig()
								}}
								className="text-sm text-primary hover:text-primary/80 underline"
							>
								Настроить OAuth credentials
							</button>
						) : (
							<div className="space-y-3 p-3 bg-gray-50 rounded-lg border border-gray-200">
								<div>
									<label className="block text-sm font-medium text-gray-700 mb-1">
										Client ID <span className="text-red-500">*</span>
									</label>
									<input
										type="text"
										value={oauthClientId}
										onChange={(e) => setOAuthClientId(e.target.value)}
										placeholder="Введите Client ID"
										className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
									/>
								</div>
								<div>
									<label className="block text-sm font-medium text-gray-700 mb-1">
										Client Secret <span className="text-red-500">*</span>
									</label>
									<input
										type="password"
										value={oauthClientSecret}
										onChange={(e) => setOAuthClientSecret(e.target.value)}
										placeholder="Введите Client Secret"
										className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
									/>
								</div>
								<div>
									<label className="block text-sm font-medium text-gray-700 mb-1">
										Redirect URI (опционально)
									</label>
									<input
										type="text"
										value={oauthRedirectUri}
										onChange={(e) => setOAuthRedirectUri(e.target.value)}
										placeholder="Автоматически сформируется, если не указан"
										className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
									/>
									<p className="mt-1 text-xs text-gray-500">
										Если не указан, будет использован: http://localhost:8000/api/v1/integrations/{kind}/oauth/callback
									</p>
								</div>
								{kind === 'gads' && (
									<>
										{hasDeveloperToken && !oauthDeveloperToken && (
											<div className="flex items-center text-xs text-green-600">
												<CheckCircle2 className="h-4 w-4 mr-1" />
												Developer token сохранён
											</div>
										)}
										<div>
											<label className="block text-sm font-medium text-gray-700 mb-1">
												Developer Token <span className="text-red-500">*</span>
											</label>
											<input
												type="password"
												value={oauthDeveloperToken}
												onChange={(e) => setOAuthDeveloperToken(e.target.value)}
												placeholder={
													hasDeveloperToken
														? 'Оставьте пустым, чтобы сохранить текущий токен'
														: 'Введите developer token'
												}
												className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
											/>
											<p className="mt-1 text-xs text-gray-500">
												Developer token доступен в Google Ads → Tools & Settings → Setup → API Center.
											</p>
										</div>
										<div>
											<label className="block text-sm font-medium text-gray-700 mb-1">
												Login Customer ID (опционально)
											</label>
											<input
												type="text"
												value={oauthLoginCustomerId}
												onChange={(e) => setOAuthLoginCustomerId(e.target.value)}
												placeholder="Например, 123-456-7890"
												className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
											/>
											<p className="mt-1 text-xs text-gray-500">
												Укажите, если используете управляющий аккаунт Google Ads.
											</p>
										</div>
									</>
								)}
								<div className="flex gap-2">
									<button
										type="button"
										onClick={handleSaveOAuthConfig}
										disabled={isSavingConfig || isLoadingConfig}
										className={cn(
											'inline-flex items-center px-3 py-1.5 rounded-lg text-sm font-medium transition-colors',
											'bg-primary text-white hover:bg-primary/90 disabled:opacity-50'
										)}
									>
										{isSavingConfig ? 'Сохранение...' : 'Сохранить'}
									</button>
									<button
										type="button"
										onClick={() => {
											setShowOAuthConfig(false)
											setOAuthClientId('')
											setOAuthClientSecret('')
											setOAuthRedirectUri('')
										}}
										className="px-3 py-1.5 text-sm text-gray-600 hover:text-gray-800"
									>
										Отмена
									</button>
								</div>
							</div>
						)}
					</div>
				)}
			</div>

			{error && (
				<div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
					<p className="text-sm text-red-600">{error}</p>
				</div>
			)}

			<div className="flex flex-wrap gap-2">
				{!integration && (
					<button
						onClick={handleConnect}
						disabled={isConnecting}
						className={cn(
							'inline-flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-colors',
							'bg-primary text-white hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed'
						)}
					>
						{isConnecting ? (
							<>
								<Loader2 className="h-4 w-4 mr-2 animate-spin" />
								Подключение...
							</>
						) : (
							<>
								<Link2 className="h-4 w-4 mr-2" />
								Подключить
							</>
						)}
					</button>
				)}

				{integration && (
					<>
						<button
							onClick={handleTest}
							disabled={isTesting}
							className={cn(
								'inline-flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-colors',
								'bg-gray-100 text-gray-700 hover:bg-gray-200 disabled:opacity-50'
							)}
						>
							{isTesting ? (
								<>
									<Loader2 className="h-4 w-4 mr-2 animate-spin" />
									Проверка...
								</>
							) : (
								<>
									<RefreshCw className="h-4 w-4 mr-2" />
									Проверить
								</>
							)}
						</button>

						{status === 'error' && (
							<button
								onClick={handleConnect}
								disabled={isConnecting}
								className={cn(
									'inline-flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-colors',
									'bg-primary text-white hover:bg-primary/90 disabled:opacity-50'
								)}
							>
								{isConnecting ? (
									<>
										<Loader2 className="h-4 w-4 mr-2 animate-spin" />
										Переподключение...
									</>
								) : (
									<>
										<Link2 className="h-4 w-4 mr-2" />
										Переподключить
									</>
								)}
							</button>
						)}

						<button
							onClick={handleDisconnect}
							disabled={isDisconnecting}
							className={cn(
								'inline-flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-colors',
								'bg-red-50 text-red-600 hover:bg-red-100 disabled:opacity-50'
							)}
						>
							{isDisconnecting ? (
								<>
									<Loader2 className="h-4 w-4 mr-2 animate-spin" />
									Отключение...
								</>
							) : (
								<>
									<Trash2 className="h-4 w-4 mr-2" />
									Отключить
								</>
							)}
						</button>
					</>
				)}
			</div>
		</div>
	)
}

