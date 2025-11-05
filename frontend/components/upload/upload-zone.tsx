'use client'

import { useState, useCallback } from 'react'
import { Upload, FileVideo, X } from 'lucide-react'
import { uploadVideo } from '@/lib/api'
import { cn } from '@/lib/utils'

interface UploadZoneProps {
	onSuccess: () => void
}

export function UploadZone({ onSuccess }: UploadZoneProps) {
	const [isDragging, setIsDragging] = useState(false)
	const [isUploading, setIsUploading] = useState(false)
	const [generateOrientations, setGenerateOrientations] = useState(false)
	const [selectedOrientations, setSelectedOrientations] = useState<string[]>([])
	const [error, setError] = useState<string | null>(null)

	const handleUpload = useCallback(async (files: File[]) => {
		setIsUploading(true)
		setError(null)

		try {
			const orientations = generateOrientations ? selectedOrientations : []
			await uploadVideo(files, generateOrientations, orientations)
			onSuccess()
		} catch (err) {
			setError(err instanceof Error ? err.message : 'Ошибка загрузки')
		} finally {
			setIsUploading(false)
		}
	}, [generateOrientations, selectedOrientations, onSuccess])

	const handleDragOver = useCallback((e: React.DragEvent) => {
		e.preventDefault()
		setIsDragging(true)
	}, [])

	const handleDragLeave = useCallback((e: React.DragEvent) => {
		e.preventDefault()
		setIsDragging(false)
	}, [])

	const handleDrop = useCallback(
		async (e: React.DragEvent) => {
			e.preventDefault()
			setIsDragging(false)

			const files = Array.from(e.dataTransfer.files).filter((file) =>
				file.type.startsWith('video/')
			)

			if (files.length > 0) {
				await handleUpload(files)
			}
		},
		[handleUpload]
	)

	const handleFileSelect = useCallback(
		async (e: React.ChangeEvent<HTMLInputElement>) => {
			const files = e.target.files
			if (files && files.length > 0) {
				await handleUpload(Array.from(files))
			}
		},
		[handleUpload]
	)

	const toggleOrientation = (orientation: string) => {
		setSelectedOrientations((prev) =>
			prev.includes(orientation)
				? prev.filter((o) => o !== orientation)
				: [...prev, orientation]
		)
	}

	return (
		<div className="rounded-xl shadow-md bg-white px-5 py-4">
			<div
				className={cn(
					'border-2 border-dashed rounded-xl p-8 text-center transition-colors',
					isDragging
						? 'border-primary bg-primary/5'
						: 'border-gray-300 hover:border-gray-400',
					isUploading && 'opacity-50 pointer-events-none'
				)}
				onDragOver={handleDragOver}
				onDragLeave={handleDragLeave}
				onDrop={handleDrop}
			>
				<input
					type="file"
					multiple
					accept="video/*"
					onChange={handleFileSelect}
					className="hidden"
					id="video-upload"
					disabled={isUploading}
				/>
				<label htmlFor="video-upload" className="cursor-pointer">
					<Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
					<p className="text-base font-medium text-gray-900 mb-2">
						Перетащите сюда видео или выберите файл
					</p>
					<p className="text-sm text-gray-500">
						Поддерживаются форматы: MP4, MOV, AVI
					</p>
				</label>
			</div>

			<div className="mt-4 space-y-4">
				<label className="flex items-center space-x-2 cursor-pointer">
					<input
						type="checkbox"
						checked={generateOrientations}
						onChange={(e) => setGenerateOrientations(e.target.checked)}
						className="rounded border-gray-300 text-primary focus:ring-primary"
					/>
					<span className="text-sm text-gray-700">
						Генерировать недостающие ориентации
					</span>
				</label>

				{generateOrientations && (
					<div className="flex flex-wrap gap-2">
						{['square', 'portrait', 'landscape'].map((orientation) => (
							<button
								key={orientation}
								type="button"
								onClick={() => toggleOrientation(orientation)}
								className={cn(
									'px-3 py-1.5 rounded-lg text-sm font-medium transition-colors',
									selectedOrientations.includes(orientation)
										? 'bg-primary text-white'
										: 'bg-gray-100 text-gray-700 hover:bg-gray-200'
								)}
							>
								{orientation === 'square' && 'Квадрат (1:1)'}
								{orientation === 'portrait' && 'Вертикаль (9:16)'}
								{orientation === 'landscape' && 'Горизонталь (16:9)'}
							</button>
						))}
					</div>
				)}

				{error && (
					<div className="p-3 bg-red-50 border border-red-200 rounded-lg">
						<p className="text-sm text-red-600">{error}</p>
					</div>
				)}

				{isUploading && (
					<div className="flex items-center justify-center space-x-2 text-sm text-gray-600">
						<div className="animate-spin rounded-full h-4 w-4 border-2 border-primary border-t-transparent"></div>
						<span>Загрузка и обработка...</span>
					</div>
				)}
			</div>
		</div>
	)
}
