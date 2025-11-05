'use client'

import { useState } from 'react'
import { CheckCircle2, XCircle, Clock, RefreshCw, ExternalLink } from 'lucide-react'
import { UploadItemResponse, retryUpload } from '@/lib/api'
import { cn } from '@/lib/utils'

interface UploadsTableProps {
	data?: { items: UploadItemResponse[]; total: number }
	isLoading: boolean
	onRetry: () => void
}

export function UploadsTable({ data, isLoading, onRetry }: UploadsTableProps) {
	const [retryingIds, setRetryingIds] = useState<Set<string>>(new Set())

	const handleRetry = async (uploadId: string) => {
		setRetryingIds((prev) => new Set(prev).add(uploadId))
		try {
			await retryUpload(uploadId)
			onRetry()
		} catch (error) {
			console.error('Ошибка повторной загрузки:', error)
		} finally {
			setRetryingIds((prev) => {
				const next = new Set(prev)
				next.delete(uploadId)
				return next
			})
		}
	}

	const getStatusIcon = (status: string) => {
		switch (status) {
			case 'success':
				return <CheckCircle2 className="h-5 w-5 text-success" />
			case 'error':
				return <XCircle className="h-5 w-5 text-destructive" />
			case 'processing':
			case 'queued':
				return <Clock className="h-5 w-5 text-gray-400" />
			default:
				return null
		}
	}

	const getStatusText = (status: string) => {
		switch (status) {
			case 'success':
				return 'Успешно'
			case 'error':
				return 'Ошибка'
			case 'processing':
				return 'Обработка'
			case 'queued':
				return 'В очереди'
			default:
				return status
		}
	}

	const getOrientationText = (orientation: string) => {
		switch (orientation) {
			case 'square':
				return 'Квадрат (1:1)'
			case 'portrait':
				return 'Вертикаль (9:16)'
			case 'landscape':
				return 'Горизонталь (16:9)'
			default:
				return orientation
		}
	}

	const formatDuration = (seconds: number) => {
		const mins = Math.floor(seconds / 60)
		const secs = Math.floor(seconds % 60)
		return `${mins}:${secs.toString().padStart(2, '0')}`
	}

	if (isLoading) {
		return (
			<div className="rounded-xl shadow-md bg-white px-5 py-4">
				<div className="animate-pulse space-y-4">
					<div className="h-4 bg-gray-200 rounded w-3/4"></div>
					<div className="h-4 bg-gray-200 rounded w-1/2"></div>
					<div className="h-4 bg-gray-200 rounded w-5/6"></div>
				</div>
			</div>
		)
	}

	if (!data || data.items.length === 0) {
		return (
			<div className="rounded-xl shadow-md bg-white px-5 py-4 text-center py-12">
				<p className="text-gray-500">Вы пока не загрузили ни одного видео</p>
			</div>
		)
	}

	return (
		<div className="rounded-xl shadow-md bg-white overflow-hidden">
			<div className="overflow-x-auto">
				<table className="w-full">
					<thead className="bg-gray-50">
						<tr>
							<th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
								Название
							</th>
							<th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
								Ориентация
							</th>
							<th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
								Длительность
							</th>
							<th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
								Размер
							</th>
							<th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
								Статус
							</th>
							<th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
								Действия
							</th>
						</tr>
					</thead>
					<tbody className="bg-white divide-y divide-gray-200">
						{data.items.map((item) => (
							<tr key={item.id} className="hover:bg-gray-50">
								<td className="px-6 py-4 whitespace-nowrap">
									<div className="text-sm font-medium text-gray-900">
										{item.original_filename}
									</div>
									<div className="text-xs text-gray-500">
										{new Date(item.created_at).toLocaleString('ru-RU')}
									</div>
								</td>
								<td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
									{getOrientationText(item.orientation)}
								</td>
								<td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
									{formatDuration(item.duration_sec)}
								</td>
								<td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
									{item.width} × {item.height}
								</td>
								<td className="px-6 py-4 whitespace-nowrap">
									<div className="flex items-center space-x-2">
										{getStatusIcon(item.status)}
										<span className="text-sm text-gray-700">
											{getStatusText(item.status)}
										</span>
									</div>
									{item.error_text && (
										<div className="text-xs text-red-600 mt-1">
											{item.error_text}
										</div>
									)}
								</td>
								<td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
									<div className="flex items-center space-x-2">
										{item.youtube_url && (
											<a
												href={item.youtube_url}
												target="_blank"
												rel="noopener noreferrer"
												className="text-primary hover:text-primary/80"
											>
												<ExternalLink className="h-4 w-4" />
											</a>
										)}
										{item.status === 'error' && (
											<button
												onClick={() => handleRetry(item.id)}
												disabled={retryingIds.has(item.id)}
												className={cn(
													'text-primary hover:text-primary/80 disabled:opacity-50',
													retryingIds.has(item.id) && 'animate-spin'
												)}
											>
												<RefreshCw className="h-4 w-4" />
											</button>
										)}
									</div>
								</td>
							</tr>
						))}
					</tbody>
				</table>
			</div>
		</div>
	)
}
