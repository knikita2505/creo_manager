#!/usr/bin/env python3
"""Скрипт для проверки конфигурации .env файла"""
import os
import sys
from pathlib import Path

def check_env_file():
	"""Проверка существования и содержимого .env файла"""
	env_path = Path(__file__).parent.parent / ".env"
	
	print("🔍 Проверка конфигурации...")
	print("")
	
	if not env_path.exists():
		print("❌ Файл .env не найден!")
		print(f"   Путь: {env_path}")
		print("")
		print("📝 Создайте файл .env:")
		print("   1. Скопируйте .env.example: cp .env.example .env")
		print("   2. Заполните DATABASE_URL строкой подключения из Supabase")
		print("")
		return False
	
	print(f"✅ Файл .env найден: {env_path}")
	print("")
	
	# Проверяем содержимое
	with open(env_path, 'r') as f:
		content = f.read()
	
	# Проверяем наличие DATABASE_URL
	if "DATABASE_URL=" not in content:
		print("❌ DATABASE_URL не найден в .env файле")
		return False
	
	# Извлекаем DATABASE_URL
	lines = content.split('\n')
	db_url = None
	for line in lines:
		if line.strip().startswith("DATABASE_URL="):
			db_url = line.split("=", 1)[1].strip()
			break
	
	if not db_url:
		print("❌ DATABASE_URL пустой или не найден")
		return False
	
	print(f"📡 DATABASE_URL: {db_url[:50]}...")
	print("")
	
	# Проверяем формат
	issues = []
	
	if "[YOUR-PASSWORD]" in db_url or "[PASSWORD]" in db_url:
		issues.append("❌ Замените [PASSWORD] или [YOUR-PASSWORD] на реальный пароль")
	
	if "[YOUR-PROJECT-REF]" in db_url or "[REF]" in db_url:
		issues.append("❌ Замените [REF] или [YOUR-PROJECT-REF] на идентификатор проекта")
	
	if not db_url.startswith(("postgresql://", "postgresql+asyncpg://")):
		issues.append("❌ DATABASE_URL должен начинаться с 'postgresql://' или 'postgresql+asyncpg://'")
	elif db_url.startswith("postgresql://") and not db_url.startswith("postgresql+asyncpg://"):
		issues.append("⚠️  DATABASE_URL использует формат 'postgresql://', рекомендуется 'postgresql+asyncpg://'")
		issues.append("   Исправление: замените 'postgresql://' на 'postgresql+asyncpg://'")
	
	if "supabase" not in db_url.lower():
		issues.append("⚠️  URL не содержит 'supabase' - убедитесь, что используете правильную строку подключения")
	
	if issues:
		print("⚠️  Обнаружены проблемы:")
		for issue in issues:
			print(f"   {issue}")
		print("")
		print("📖 Получите правильную строку подключения:")
		print("   Supabase Dashboard → Settings → Database → Connection string → URI")
		print("")
		print("   Формат для прямого подключения:")
		print("   postgresql+asyncpg://postgres:[PASSWORD]@db.[REF].supabase.co:5432/postgres")
		print("")
		return False
	
	print("✅ Формат DATABASE_URL выглядит правильно")
	print("")
	print("💡 Для проверки подключения запустите:")
	print("   python scripts/check_db.py")
	print("")
	
	return True

if __name__ == "__main__":
	success = check_env_file()
	sys.exit(0 if success else 1)

