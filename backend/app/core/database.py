from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
from app.core.config import settings

# Для Supabase рекомендуется использовать:
# - Connection Pooler (порт 6543) - для production, использует встроенный pooler Supabase
# - Прямое подключение (порт 5432) - для разработки, используем NullPool
# Connection Pooler URL: postgresql+asyncpg://postgres.[REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
# Direct connection URL: postgresql+asyncpg://postgres.[REF]:[PASSWORD]@db.[REF].supabase.co:5432/postgres

# Убеждаемся, что используем asyncpg драйвер
database_url = settings.DATABASE_URL

# Для asyncpg с Supabase нужно использовать Connection Pooler (порт 6543) или правильный формат
if database_url.startswith("postgresql://") and not database_url.startswith("postgresql+asyncpg://"):
	# Преобразуем postgresql:// в postgresql+asyncpg://
	database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
	
	# Если это прямое подключение (порт 5432), пробуем использовать Connection Pooler
	if ":5432" in database_url and "pooler" not in database_url:
		# Пытаемся найти REF и REGION для создания pooler URL
		import re
		match = re.search(r'@db\.([^.]+)\.supabase\.co', database_url)
		if match:
			ref = match.group(1)
			# Пробуем определить регион (по умолчанию us-east-1)
			# Пользователь может вручную указать pooler URL
			print(f"⚠️  Обнаружено прямое подключение (порт 5432)")
			print(f"   Для asyncpg рекомендуется использовать Connection Pooler (порт 6543)")
			print(f"   Connection Pooler URL: postgresql+asyncpg://postgres.[REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres")
			print(f"   Получите правильный URL в Supabase Dashboard → Settings → Database → Connection string")
			print(f"   Выберите 'Session mode' для Connection Pooler")
	
	print(f"⚠️  Автоматически исправлен формат DATABASE_URL для использования asyncpg")
elif not database_url.startswith("postgresql+asyncpg://"):
	raise ValueError(
		f"DATABASE_URL должен использовать asyncpg драйвер.\n"
		f"Используйте формат: postgresql+asyncpg://...\n"
		f"Текущий формат: {database_url[:50]}..."
	)

engine = create_async_engine(
	database_url,
	echo=False,
	future=True,
	# Используем NullPool для прямого подключения или если используем Supabase pooler
	poolclass=NullPool,
	pool_pre_ping=True,  # Проверка соединений перед использованием
)

AsyncSessionLocal = async_sessionmaker(
	engine,
	class_=AsyncSession,
	expire_on_commit=False,
	autocommit=False,
	autoflush=False,
)

Base = declarative_base()


async def get_db() -> AsyncSession:
	async with AsyncSessionLocal() as session:
		try:
			yield session
		finally:
			await session.close()

