from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List


class Settings(BaseSettings):
	# Database
	DATABASE_URL: str
	
	@field_validator('DATABASE_URL')
	@classmethod
	def validate_database_url(cls, v: str) -> str:
		"""Проверка формата DATABASE_URL"""
		if not v or v.strip() == "":
			raise ValueError("DATABASE_URL не может быть пустым")
		
		# Проверяем, что это PostgreSQL URL
		if not v.startswith(("postgresql://", "postgresql+asyncpg://")):
			raise ValueError(
				"DATABASE_URL должен начинаться с 'postgresql://' или 'postgresql+asyncpg://'\n"
				"Для Supabase используйте формат:\n"
				"postgresql+asyncpg://postgres:[PASSWORD]@db.[REF].supabase.co:5432/postgres"
			)
		
		# Автоматически исправляем формат postgresql:// на postgresql+asyncpg://
		if v.startswith("postgresql://") and not v.startswith("postgresql+asyncpg://"):
			v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
			print(f"⚠️  Автоматически исправлен формат DATABASE_URL: добавлен +asyncpg")
		
		# Проверяем наличие обязательных частей
		if "[YOUR-PASSWORD]" in v or "[YOUR-PROJECT-REF]" in v or "[PASSWORD]" in v or "[REF]" in v:
			raise ValueError(
				"Замените плейсхолдеры в DATABASE_URL на реальные значения:\n"
				"- [PASSWORD] или [YOUR-PASSWORD] → ваш пароль БД\n"
				"- [REF] или [YOUR-PROJECT-REF] → идентификатор проекта Supabase"
			)
		
		return v

	# Security
	SECRET_KEY: str
	ALGORITHM: str = "HS256"
	ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

	# CORS
	CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001"]
	
	# Frontend
	FRONTEND_URL: str = "http://localhost:3000"
	
	# Backend
	BACKEND_URL: str = "http://localhost:8000"

	# YouTube API
	YOUTUBE_CLIENT_ID: str = ""
	YOUTUBE_CLIENT_SECRET: str = ""
	YOUTUBE_REDIRECT_URI: str = ""

	# Google Drive API
	GDRIVE_CLIENT_ID: str = ""
	GDRIVE_CLIENT_SECRET: str = ""
	GDRIVE_REDIRECT_URI: str = ""

	# Google Ads API
	GADS_CLIENT_ID: str = ""
	GADS_CLIENT_SECRET: str = ""
	GADS_REDIRECT_URI: str = ""
	GADS_DEVELOPER_TOKEN: str = ""

	# Telegram
	TELEGRAM_BOT_TOKEN: str = ""

	# Storage
	STORAGE_PATH: str = "./storage"
	MAX_UPLOAD_SIZE: int = 10737418240  # 10GB

	# Video Processing
	FFMPEG_PATH: str = "ffmpeg"
	FFPROBE_PATH: str = "ffprobe"
	MAX_PARALLEL_UPLOADS: int = 3

	class Config:
		env_file = ".env"
		case_sensitive = True


settings = Settings()

