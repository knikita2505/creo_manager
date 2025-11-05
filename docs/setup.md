# Инструкция по настройке проекта

## Требования

- Python 3.11+
- Node.js 18+
- Supabase проект (см. [supabase-setup.md](supabase-setup.md))
- FFmpeg

## Установка FFmpeg

### macOS
```bash
brew install ffmpeg
```

### Linux
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

### Windows
Скачайте с [ffmpeg.org](https://ffmpeg.org/download.html) и добавьте в PATH

## Настройка Backend

1. Создайте виртуальное окружение:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Создайте файл `.env` на основе `.env.example`:
```bash
cp .env.example .env
```

4. Настройте Supabase:
   - Создайте проект на [supabase.com](https://supabase.com)
   - Получите строку подключения (см. [supabase-setup.md](supabase-setup.md))
   - Добавьте в `.env` как `DATABASE_URL`

5. Настройте переменные окружения в `.env`:
   - `DATABASE_URL` - строка подключения к Supabase (формат: `postgresql+asyncpg://...`)
   - `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET` - OAuth credentials для YouTube API

6. Запустите сервер:
```bash
python run.py
# или
uvicorn app.main:app --reload
```

## Настройка Frontend

1. Установите зависимости:
```bash
cd frontend
npm install
```

2. Создайте файл `.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

3. Запустите dev сервер:
```bash
npm run dev
```

## Получение YouTube API Credentials

1. Перейдите в [Google Cloud Console](https://console.cloud.google.com/)
2. Создайте новый проект или выберите существующий
3. Включите YouTube Data API v3
4. Создайте OAuth 2.0 Client ID:
   - Credentials → Create Credentials → OAuth client ID
   - Application type: Web application
   - Authorized redirect URIs: `http://localhost:8000/api/auth/youtube/callback`
5. Скопируйте Client ID и Client Secret в `.env`

## Первый запуск

1. Запустите backend (порт 8000)
2. Запустите frontend (порт 3000)
3. Откройте http://localhost:3000
4. Для работы с загрузкой видео необходимо сначала подключить YouTube интеграцию (будет реализовано в следующем этапе)

## Примечания

- В текущей версии используется временная функция аутентификации (заглушка)
- Для полноценной работы необходимо настроить интеграции с YouTube
- Убедитесь, что FFmpeg доступен в PATH

