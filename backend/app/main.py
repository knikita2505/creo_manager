from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
	"""Управление жизненным циклом приложения"""
	# Startup
	try:
		async with engine.begin() as conn:
			await conn.run_sync(Base.metadata.create_all)
		print("✅ Подключение к БД успешно, таблицы проверены/созданы")
	except Exception as e:
		error_msg = str(e)
		if "nodename nor servname provided" in error_msg or "gaierror" in error_msg:
			print("❌ ОШИБКА: Не удалось подключиться к базе данных")
			print("   Проверьте:")
			print("   1. Существует ли файл backend/.env")
			print("   2. Правильно ли указан DATABASE_URL в .env")
			print("   3. Формат строки: postgresql+asyncpg://postgres:[PASSWORD]@db.[REF].supabase.co:5432/postgres")
			print("   4. Доступен ли проект Supabase (не в паузе)")
			print("")
			print("   Получите правильную строку подключения в Supabase Dashboard:")
			print("   Settings → Database → Connection string → URI")
			print("")
			raise
		else:
			print(f"⚠️  Предупреждение при подключении к БД: {e}")
			print("   Приложение запущено, но некоторые функции могут быть недоступны")
	
	yield
	# Shutdown


app = FastAPI(
	title="Creo Manager API",
	description="API для управления креативами и загрузки видео на YouTube",
	version="0.1.0",
	lifespan=lifespan,
)

app.add_middleware(
	CORSMiddleware,
	allow_origins=settings.CORS_ORIGINS,
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
	return {"message": "Creo Manager API", "version": "0.1.0"}


@app.get("/health")
async def health():
	return {"status": "healthy"}

