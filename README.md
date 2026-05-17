# Архив кода — API для навигации по кодовой базе

REST-сервис на Python, который индексирует `.py`-файлы и позволяет искать функции и классы по имени или описанию.

---

## Схема базы данных

База данных — SQLite, файл `code_index.db`.

```sql
CREATE TABLE files (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    filename    TEXT NOT NULL UNIQUE,        -- имя файла (без пути)
    indexed_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE code_entities (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id     INTEGER NOT NULL,            -- ссылка на файл
    name        TEXT NOT NULL,               -- имя функции или класса
    entity_type TEXT NOT NULL                -- 'function' или 'class'
                CHECK(entity_type IN ('function', 'class')),
    start_line  INTEGER NOT NULL,            -- строка начала
    end_line    INTEGER NOT NULL,            -- строка конца
    docstring   TEXT,                        -- docstring или NULL
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
);

-- Индексы для ускорения поиска
CREATE INDEX idx_entity_name ON code_entities(name);
CREATE INDEX idx_entity_type ON code_entities(entity_type);
```

**Почему такая схема:**
- Две таблицы — нормальная форма: файл хранится один раз, все его сущности ссылаются на него через `file_id`.
- `ON DELETE CASCADE` — при удалении файла автоматически удаляются все его функции и классы.
- Индекс на `name` критически важен для поиска: без него `LIKE`-запрос по 100 000 записям работает линейно.
- Индекс на `entity_type` ускоряет фильтрацию `?type=function` / `?type=class`.

---

## Установка и запуск

```bash
# 1. Установить зависимости
pip install -r requirements.txt

# 2. Положить .py-файлы для индексации в папку data/
mkdir data
# ... скопировать файлы ...

# 3. Запустить индексатор
python indexer.py

# 4. Запустить API
python -m uvicorn main:app --reload
```

Swagger-документация: http://localhost:8000/docs

---

## Примеры запросов и ответов

### 1. Список всех проиндексированных файлов

```
GET /api/files
```

```json
[
  {
    "filename": "auth_service.py",
    "indexed_at": "2026-05-15 10:00:00",
    "function_count": 5,
    "class_count": 1,
    "total_entities": 6
  },
  {
    "filename": "user_repository.py",
    "indexed_at": "2026-05-15 10:00:01",
    "function_count": 4,
    "class_count": 1,
    "total_entities": 5
  }
]
```

---

### 2. Структура конкретного файла

```
GET /api/files/auth_service.py/structure
```

```json
{
  "filename": "auth_service.py",
  "entities": [
    {
      "name": "AuthService",
      "entity_type": "class",
      "start_line": 10,
      "end_line": 80,
      "docstring": "Сервис аутентификации пользователей."
    },
    {
      "name": "login",
      "entity_type": "function",
      "start_line": 20,
      "end_line": 45,
      "docstring": "Аутентификация по логину и паролю."
    }
  ]
}
```

Если файл не найден — возвращается `[]`.

---

### 3. Поиск по ключевому слову

```
GET /api/search?q=авторизация
```

```json
[
  {
    "filename": "auth_service.py",
    "name": "check_token",
    "entity_type": "function",
    "start_line": 50,
    "end_line": 65,
    "docstring": "Проверка токена авторизации."
  }
]
```

Если ничего не найдено — возвращается `[]`.

---

### 4. Поиск с фильтрацией по типу (бонус)

```
GET /api/search?q=user&type=class
```

```json
[
  {
    "filename": "user_repository.py",
    "name": "UserRepository",
    "entity_type": "class",
    "start_line": 5,
    "end_line": 60,
    "docstring": "Репозиторий для работы с пользователями."
  }
]
```

---

### 5. Сводная статистика (бонус)

```
GET /api/stats
```

```json
{
  "total_files": 30,
  "total_functions": 142,
  "total_classes": 38,
  "total_entities": 180
}
```
