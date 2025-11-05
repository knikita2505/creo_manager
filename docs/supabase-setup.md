# Настройка Supabase

## Создание проекта в Supabase

1. Перейдите на [supabase.com](https://supabase.com) и войдите в аккаунт
2. Создайте новый проект или используйте существующий
3. Дождитесь завершения инициализации проекта (обычно 1-2 минуты)

## Получение строки подключения

1. В Dashboard проекта перейдите в **Settings** → **Database**
2. Найдите секцию **Connection string**
3. Выберите **URI** формат
4. Скопируйте строку подключения

### Формат строки подключения

Supabase предоставляет несколько вариантов подключения:

#### Вариант 1: Connection Pooler (рекомендуется для production)
```
postgresql+asyncpg://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
```

#### Вариант 2: Прямое подключение (для разработки)
```
postgresql+asyncpg://postgres.[PROJECT-REF]:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
```

Где:
- `[PROJECT-REF]` - уникальный идентификатор вашего проекта (находится в URL проекта)
- `[PASSWORD]` - пароль базы данных (можно сбросить в Settings → Database)
- `[REGION]` - регион размещения (например, us-east-1)

### Пример

Если ваш проект имеет REF `abcdefghijklmnop`, пароль `mySecurePassword123`, и находится в регионе `us-east-1`:

**Connection Pooler:**
```
postgresql+asyncpg://postgres.abcdefghijklmnop:mySecurePassword123@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

**Прямое подключение:**
```
postgresql+asyncpg://postgres.abcdefghijklmnop:mySecurePassword123@db.abcdefghijklmnop.supabase.co:5432/postgres
```

## Настройка в проекте

1. Откройте файл `backend/.env`
2. Вставьте строку подключения в переменную `DATABASE_URL`:

```env
DATABASE_URL=postgresql+asyncpg://postgres.[YOUR-REF]:[YOUR-PASSWORD]@db.[YOUR-REF].supabase.co:5432/postgres
```

## Создание таблиц

Таблицы создаются автоматически при первом запуске приложения через SQLAlchemy.

Если нужно создать таблицы вручную через SQL редактор Supabase:

1. Перейдите в **SQL Editor** в Dashboard
2. Используйте схему из `Project description/db_structure.md`

Или запустите приложение - таблицы создадутся автоматически:

```bash
cd backend
python run.py
```

## Проверка подключения

После запуска приложения проверьте:

1. В Supabase Dashboard → **Database** → **Tables** должны появиться таблицы:
   - users
   - integrations
   - source_assets
   - video_versions
   - youtube_uploads
   - ads_video_links
   - moderation_checks
   - notifications

2. В логах приложения не должно быть ошибок подключения к БД

## Безопасность

⚠️ **Важно:**
- Никогда не коммитьте `.env` файл в git
- Храните пароль БД в безопасном месте
- Используйте Connection Pooler для production окружений
- Рекомендуется использовать переменные окружения на сервере

## Дополнительные возможности Supabase

Supabase предоставляет дополнительные возможности, которые можно использовать в будущем:

- **Storage** - для хранения видео файлов (вместо локального storage)
- **Auth** - для аутентификации пользователей
- **Realtime** - для real-time обновлений статусов загрузок
- **Edge Functions** - для серверной логики

На текущем этапе MVP мы используем только PostgreSQL базу данных.

