# Database Schema — Google Ads Video Platform

---

## 🧑 users

Пользователи системы.

| Поле | Тип | Комментарий |
|------|-----|-------------|
| id | UUID (PK) | Уникальный ID |
| email | TEXT | Email |
| name | TEXT | Имя (опц.) |
| created_at | TIMESTAMP | Дата регистрации |

---

## 🔌 integrations

Подключения к внешним сервисам.

| Поле | Тип | Комментарий |
|------|-----|-------------|
| id | UUID (PK) | Уникальный ID |
| user_id | UUID (FK → users.id) | Владелец |
| kind | ENUM: `youtube`, `gdrive`, `gads`, `telegram` | Тип интеграции |
| auth_data | JSONB | OAuth или API-токены (зашифровано) |
| is_valid | BOOLEAN | Валидность подключения |
| created_at | TIMESTAMP | Время создания |

---

## 📦 source_assets

Загруженные исходные видео (до рендера).

| Поле | Тип | Комментарий |
|------|-----|-------------|
| id | UUID (PK) | ID исходника |
| user_id | UUID (FK → users.id) | Владелец |
| original_filename | TEXT | Имя файла |
| storage_path | TEXT | Путь в Storage |
| duration_sec | FLOAT | Длительность |
| width | INT | Ширина |
| height | INT | Высота |
| fps | FLOAT | Частота кадров |
| created_at | TIMESTAMP | Дата загрузки |

---

## 🎞 video_versions

Сгенерированные версии видео: ориентации, уникализация.

| Поле | Тип | Комментарий |
|------|-----|-------------|
| id | UUID (PK) | |
| source_id | UUID (FK → source_assets.id) | Связь с исходником |
| orientation | ENUM: `square`, `portrait`, `landscape` | Формат |
| transform_profile | JSONB | Применённые модификации |
| storage_path_render | TEXT | Результат |
| duration_sec | FLOAT | Длительность |
| width | INT | Ширина |
| height | INT | Высота |
| fps | FLOAT | Кадры в секунду |
| created_at | TIMESTAMP | |

---

## 📺 youtube_uploads

История загрузок на YouTube.

| Поле | Тип | Комментарий |
|------|-----|-------------|
| id | UUID (PK) | |
| version_id | UUID (FK → video_versions.id) | Откуда |
| youtube_video_id | TEXT | ID видео |
| youtube_url | TEXT | Ссылка |
| title | TEXT | Название (опц.) |
| privacy | TEXT (default: `unlisted`) | Приватность |
| thumbnail_set | BOOLEAN | Установлен ли thumbnail |
| status | ENUM: `queued`, `success`, `error` | Статус загрузки |
| error_text | TEXT (nullable) | Ошибка |
| uploaded_at | TIMESTAMP | Время загрузки |

---

## 📊 ads_video_links

Связь видео с Google Ads сущностями.

| Поле | Тип | Комментарий |
|------|-----|-------------|
| id | UUID (PK) | |
| youtube_video_id | TEXT | Видео |
| gads_customer_id | TEXT | Аккаунт |
| campaign_id | TEXT | Кампания |
| ad_group_id | TEXT | Группа |
| asset_id | TEXT (nullable) | ID ассета (если был создан) |
| created_at | TIMESTAMP | |

---

## 🛡 moderation_checks

Результаты проверки модерации Google Ads.

| Поле | Тип | Комментарий |
|------|-----|-------------|
| id | UUID (PK) | |
| youtube_video_id | TEXT | Видео |
| gads_customer_id | TEXT | |
| campaign_id | TEXT | |
| ad_group_id | TEXT | |
| status | ENUM: `approved`, `limited`, `not_eligible`, `unknown` | Статус |
| checked_at | TIMESTAMP | Время запроса |
| raw_payload | JSONB | Полный ответ API |

---

## 📬 notifications

Лог уведомлений пользователям.

| Поле | Тип | Комментарий |
|------|-----|-------------|
| id | UUID (PK) | |
| type | ENUM: `moderation_alert` | Тип события |
| payload | JSONB | Контекст (видео, кампания, статус) |
| delivered_to | ENUM: `telegram` | Канал доставки |
| delivered_at | TIMESTAMP | |

---

# 🧩 Модал-креативы (v2)

## 🎨 modal_templates

Шаблоны модальных окон (UI-модалок).

| Поле | Тип | Комментарий |
|------|-----|-------------|
| id | UUID (PK) | |
| user_id | UUID (FK → users.id) | Автор |
| title_text | TEXT | Заголовок |
| message_text | TEXT | Основной текст |
| button_1_text | TEXT | Текст кнопки 1 |
| button_2_text | TEXT (nullable) | Текст кнопки 2 |
| theme | ENUM: `ios_light`, `ios_dark`, `custom` | Визуальный стиль |
| layout_json | JSONB | Расположение элементов |
| created_at | TIMESTAMP | |

---

## 🖼 modal_renders

Сгенерированные видео-модалки.

| Поле | Тип | Комментарий |
|------|-----|-------------|
| id | UUID (PK) | |
| template_id | UUID (FK → modal_templates.id) | Шаблон |
| gallery_images | JSONB | Список путей к 9 изображениям |
| audio_id | UUID (FK → audio_assets.id) | Звук |
| orientation | ENUM: `square`, `portrait`, `landscape` | Формат |
| render_path | TEXT | Путь к финальному видео |
| status | ENUM: `queued`, `rendering`, `success`, `error` | Статус рендера |
| error_text | TEXT (nullable) | Ошибка |
| created_at | TIMESTAMP | |

---

## 🔊 audio_assets

Звуковые эффекты для модалок.

| Поле | Тип | Комментарий |
|------|-----|-------------|
| id | UUID (PK) | |
| user_id | UUID (FK → users.id) | Принадлежит |
| file_path | TEXT | Путь к звуку |
| name | TEXT | Название |
| duration_sec | FLOAT | Длительность |
| created_at | TIMESTAMP | |

