#!/bin/bash

# Скрипт запуска Frontend
# Использование: ./start_frontend.sh

set -e  # Остановка при ошибке

echo "🚀 Запуск Creo Manager Frontend..."
echo ""

# Переходим в директорию frontend
cd "$(dirname "$0")/frontend"

# Проверяем наличие Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js не найден!"
    echo "   Установите Node.js: https://nodejs.org/"
    exit 1
fi

# Проверяем версию Node.js (требуется >= 18)
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo "⚠️  Требуется Node.js версии 18 или выше"
    echo "   Текущая версия: $(node -v)"
    exit 1
fi

echo "✅ Node.js версия: $(node -v)"
echo "✅ npm версия: $(npm -v)"
echo ""

# Проверяем наличие package.json
if [ ! -f "package.json" ]; then
    echo "❌ Файл package.json не найден!"
    exit 1
fi

# Проверяем наличие node_modules
if [ ! -d "node_modules" ]; then
    echo "📦 Установка зависимостей..."
    npm install
else
    echo "✅ Зависимости установлены"
fi

# Проверяем наличие .env.local (опционально)
if [ ! -f ".env.local" ]; then
    echo "ℹ️  Файл .env.local не найден (опционально)"
    echo "   Создайте .env.local для настройки API URL:"
    echo "   NEXT_PUBLIC_API_URL=http://localhost:8000"
    echo ""
fi

echo ""
echo "🌟 Запуск dev сервера..."
echo "   Frontend будет доступен на: http://localhost:3000"
echo "   Нажмите Ctrl+C для остановки"
echo ""

# Запускаем dev сервер
npm run dev

