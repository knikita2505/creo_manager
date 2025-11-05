const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface UploadVersionResponse {
	id: string
	orientation: string
	status: string
	youtube_url: string | null
	error_text: string | null
	duration_sec: number
	width: number
	height: number
}

export interface UploadResponse {
	source_id: string
	original_filename: string
	versions: UploadVersionResponse[]
}

export interface UploadItemResponse {
	id: string
	source_id: string
	original_filename: string
	orientation: string
	duration_sec: number
	width: number
	height: number
	youtube_url: string | null
	status: string
	error_text: string | null
	uploaded_at: string | null
	created_at: string
}

export interface UploadListResponse {
	items: UploadItemResponse[]
	total: number
}

export interface UploadRequest {
	generate_orientations: boolean
	orientations: string[]
}

export async function uploadVideo(
	files: File[],
	generateOrientations: boolean = false,
	orientations: string[] = []
): Promise<UploadResponse> {
	const formData = new FormData()
	files.forEach((file) => {
		formData.append('files', file)
	})

	const params = new URLSearchParams()
	if (generateOrientations) {
		params.append('generate_orientations', 'true')
	}
	orientations.forEach((o) => {
		params.append('orientations', o)
	})

	const url = `${API_BASE_URL}/api/v1/uploads/${params.toString() ? '?' + params.toString() : ''}`

	const response = await fetch(url, {
		method: 'POST',
		body: formData,
	})

	if (!response.ok) {
		const error = await response.json()
		throw new Error(error.detail || 'Ошибка загрузки видео')
	}

	return response.json()
}

export async function getUploads(skip: number = 0, limit: number = 50): Promise<UploadListResponse> {
	const response = await fetch(
		`${API_BASE_URL}/api/v1/uploads/?skip=${skip}&limit=${limit}`
	)

	if (!response.ok) {
		throw new Error('Ошибка получения списка загрузок')
	}

	return response.json()
}

export async function retryUpload(uploadId: string): Promise<{ status: string; youtube_url: string }> {
	const response = await fetch(`${API_BASE_URL}/api/v1/uploads/${uploadId}/retry`, {
		method: 'POST',
	})

	if (!response.ok) {
		const error = await response.json()
		throw new Error(error.detail || 'Ошибка повторной загрузки')
	}

	return response.json()
}

