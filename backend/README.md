# Backend - Creo Manager

## Установка зависимостей

1. Создайте виртуальное окружение (если еще не создано):
```bash
python3 -m venv venv
```

2. Активируйте виртуальное окружение:
```bash
source venv/bin/activate
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

## Настройка

1. Создайте файл `.env` из шаблона:
```bash
cp .env.example .env
```

2. Заполните необходимые параметры в `.env` (см. [CREATE_ENV.md](CREATE_ENV.md))

## Запуск

### Важно: Всегда активируйте виртуальное окружение перед запуском!

```bash
source venv/bin/activate
```

### Проверка подключения к БД

```bash
python scripts/check_db.py
```

### Запуск сервера

```bash
python run.py
# или
uvicorn app.main:app --reload
```

## Структура проекта

```
backend/
├── app/
│   ├── api/          # API эндпоинты
│   ├── core/         # Конфигурация и БД
│   ├── models/       # SQLAlchemy модели
│   ├── services/     # Бизнес-логика
│   └── main.py       # Точка входа
├── scripts/          # Утилиты
├── requirements.txt  # Зависимости
└── .env              # Конфигурация (создать вручную)
```

## Troubleshooting

### ModuleNotFoundError

Если видите ошибку `ModuleNotFoundError`, убедитесь что:
1. Виртуальное окружение активировано: `source venv/bin/activate`
2. Зависимости установлены: `pip install -r requirements.txt`

### Ошибка подключения к БД

Проверьте:
1. Правильность строки подключения в `.env`
2. Доступность Supabase проекта
3. Правильность пароля БД

