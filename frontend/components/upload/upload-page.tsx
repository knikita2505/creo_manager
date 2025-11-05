'use client'

import { useState } from 'react'
import { UploadZone } from './upload-zone'
import { UploadsTable } from './uploads-table'
import { useQuery } from '@tanstack/react-query'
import { getUploads } from '@/lib/api'

export function UploadPage() {
	const [uploadKey, setUploadKey] = useState(0)

	const { data, isLoading, refetch } = useQuery({
		queryKey: ['uploads'],
		queryFn: () => getUploads(),
	})

	const handleUploadSuccess = () => {
		setUploadKey((prev) => prev + 1)
		refetch()
	}

	return (
		<div className="min-h-screen bg-white">
			<div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
				<div className="mb-8">
					<h1 className="text-2xl font-semibold text-gray-900 mb-2">
						Загрузка видео на YouTube
					</h1>
					<p className="text-sm text-gray-500">
						Загрузите видео для автоматической обработки и публикации
					</p>
				</div>

				<div className="mb-8">
					<UploadZone key={uploadKey} onSuccess={handleUploadSuccess} />
				</div>

				<div>
					<h2 className="text-xl font-medium text-gray-900 mb-4">История загрузок</h2>
					<UploadsTable data={data} isLoading={isLoading} onRetry={refetch} />
				</div>
			</div>
		</div>
	)
}

