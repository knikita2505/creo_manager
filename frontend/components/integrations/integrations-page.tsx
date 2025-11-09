'use client'

import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { getIntegrations } from '@/lib/api-integrations'
import { IntegrationCard } from './integration-card'

export function IntegrationsPage() {
	const queryClient = useQueryClient()

	const { data, isLoading, error } = useQuery({
		queryKey: ['integrations'],
		queryFn: getIntegrations,
	})

	const handleRefresh = () => {
		queryClient.invalidateQueries({ queryKey: ['integrations'] })
	}

	const integrations = data?.integrations || []

	return (
		<div className="min-h-screen bg-white">
			<div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
				<div className="mb-8">
					<h1 className="text-2xl font-semibold text-gray-900 mb-2">
						Настройка интеграций
					</h1>
					<p className="text-sm text-gray-500">
						Подключите необходимые сервисы для работы с видео и уведомлениями
					</p>
				</div>

				{isLoading && (
					<div className="space-y-4">
						<div className="animate-pulse bg-gray-200 h-32 rounded-xl"></div>
						<div className="animate-pulse bg-gray-200 h-32 rounded-xl"></div>
					</div>
				)}

				{error && (
					<div className="p-4 bg-red-50 border border-red-200 rounded-xl">
						<p className="text-sm text-red-600">
							Ошибка загрузки интеграций. Попробуйте обновить страницу.
						</p>
					</div>
				)}

				{!isLoading && !error && (
					<div className="grid grid-cols-1 md:grid-cols-2 gap-6">
						<IntegrationCard
							kind="youtube"
							integration={integrations.find((i) => i.kind === 'youtube')}
							onUpdate={handleRefresh}
						/>
						<IntegrationCard
							kind="gdrive"
							integration={integrations.find((i) => i.kind === 'gdrive')}
							onUpdate={handleRefresh}
						/>
						<IntegrationCard
							kind="gads"
							integration={integrations.find((i) => i.kind === 'gads')}
							onUpdate={handleRefresh}
						/>
						<IntegrationCard
							kind="telegram"
							integration={integrations.find((i) => i.kind === 'telegram')}
							onUpdate={handleRefresh}
						/>
					</div>
				)}
			</div>
		</div>
	)
}



