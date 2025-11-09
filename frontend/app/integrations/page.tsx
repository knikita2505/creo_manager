'use client'

import { useEffect } from 'react'
import { useSearchParams } from 'next/navigation'
import { IntegrationsPage } from '@/components/integrations/integrations-page'
import { useQueryClient } from '@tanstack/react-query'

export default function IntegrationsRoute() {
	const searchParams = useSearchParams()
	const queryClient = useQueryClient()

	useEffect(() => {
		const connected = searchParams.get('connected')
		if (connected) {
			// Обновляем список интеграций после успешного подключения
			queryClient.invalidateQueries({ queryKey: ['integrations'] })
			// Убираем параметр из URL
			window.history.replaceState({}, '', '/integrations')
		}
	}, [searchParams, queryClient])

	return <IntegrationsPage />
}
