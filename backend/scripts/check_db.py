"""Скрипт для проверки подключения к Supabase"""
import asyncio
import sys
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import engine, Base
from app.core.config import settings
from sqlalchemy import text


async def check_connection():
	"""Проверка подключения к БД"""
	print("🔍 Проверка подключения к Supabase...")
	print(f"📡 DATABASE_URL: {settings.DATABASE_URL[:50]}...")
	
	try:
		async with engine.begin() as conn:
			# Проверяем подключение
			result = await conn.execute(text("SELECT version();"))
			version = result.scalar()
			print(f"✅ Подключение успешно!")
			print(f"📊 Версия PostgreSQL: {version[:50]}...")
			
			# Проверяем существующие таблицы
			result = await conn.execute(
				text("""
					SELECT table_name 
					FROM information_schema.tables 
					WHERE table_schema = 'public'
					ORDER BY table_name;
				""")
			)
			tables = [row[0] for row in result.fetchall()]
			
			if tables:
				print(f"\n📋 Найдено таблиц: {len(tables)}")
				for table in tables:
					print(f"   - {table}")
			else:
				print("\n⚠️  Таблицы не найдены. Они будут созданы при первом запуске приложения.")
			
			return True
			
	except Exception as e:
		print(f"❌ Ошибка подключения: {e}")
		print("\n💡 Проверьте:")
		print("   1. Правильность строки подключения в .env")
		print("   2. Доступность Supabase проекта")
		print("   3. Правильность пароля БД")
		return False


async def create_tables():
	"""Создание таблиц"""
	print("\n🔨 Создание таблиц...")
	try:
		async with engine.begin() as conn:
			await conn.run_sync(Base.metadata.create_all)
		print("✅ Таблицы успешно созданы!")
		return True
	except Exception as e:
		print(f"❌ Ошибка создания таблиц: {e}")
		return False


async def main():
	"""Основная функция"""
	print("=" * 60)
	print("Supabase Connection Checker")
	print("=" * 60)
	
	connected = await check_connection()
	
	if not connected:
		sys.exit(1)
	
	# Спрашиваем, нужно ли создать таблицы
	print("\n" + "=" * 60)
	create = input("\nСоздать таблицы? (y/n): ").strip().lower()
	
	if create == 'y':
		created = await create_tables()
		if not created:
			sys.exit(1)
	
	print("\n✅ Проверка завершена!")
	print("=" * 60)


if __name__ == "__main__":
	asyncio.run(main())

