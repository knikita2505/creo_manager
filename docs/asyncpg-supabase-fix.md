# Решение проблемы: asyncpg + Supabase

## Проблема

Если при использовании `postgresql+asyncpg://` возникает ошибка подключения, а без `+asyncpg` подключение работает, но появляется ошибка `ModuleNotFoundError: No module named 'psycopg2'`, это означает, что нужно использовать **Connection Pooler** вместо прямого подключения.

## Решение

### Вариант 1: Использовать Connection Pooler (рекомендуется)

Для `asyncpg` с Supabase нужно использовать **Connection Pooler** на порту **6543**, а не прямое подключение на порту 5432.

1. Откройте Supabase Dashboard
2. Перейдите в **Settings** → **Database**
3. Найдите секцию **Connection string**
4. Выберите вкладку **URI**
5. **Важно:** Выберите **"Session mode"** (Connection Pooler) вместо **"Transaction mode"** (Direct connection)
6. Скопируйте строку подключения

Формат Connection Pooler URL:
```
postgresql+asyncpg://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
```

Пример:
```
postgresql+asyncpg://postgres.blnoiaxjswehjulocafl:yourpassword@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

### Вариант 2: Использовать psycopg (синхронный драйвер)

Если Connection Pooler не подходит, можно использовать синхронный драйвер `psycopg`:

1. Установите psycopg:
```bash
cd backend
source venv/bin/activate
pip install psycopg2-binary
```

2. Используйте формат без `+asyncpg`:
```
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[REF].supabase.co:5432/postgres
```

**Но это не рекомендуется**, так как мы используем async SQLAlchemy и asyncpg работает лучше с async кодом.

## Рекомендация

**Используйте Connection Pooler (Вариант 1)** - это оптимальный вариант для production и разработки с asyncpg.

## Как получить правильный Connection Pooler URL

1. Supabase Dashboard → Settings → Database
2. Connection string → URI
3. **Session mode** (это Connection Pooler)
4. Скопируйте URL - он будет содержать `pooler.supabase.com:6543`
5. Если нужно, добавьте `+asyncpg` после `postgresql`:
   ```
   postgresql://... → postgresql+asyncpg://...
   ```

## Проверка

После обновления `.env` файла проверьте подключение:

```bash
cd backend
source venv/bin/activate
python scripts/check_db.py
```

Если всё правильно, вы увидите:
```
✅ Подключение успешно!
```

