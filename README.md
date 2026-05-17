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
    "filename": "test1.py",
    "indexed_at": "2026-05-17 09:05:33",
    "function_count": 11,
    "class_count": 0,
    "total_entities": 11
  },
  {
    "filename": "test2.py",
    "indexed_at": "2026-05-17 09:05:33",
    "function_count": 12,
    "class_count": 4,
    "total_entities": 16
  },
  {
    "filename": "test3.py",
    "indexed_at": "2026-05-17 09:05:33",
    "function_count": 7,
    "class_count": 2,
    "total_entities": 9
  },
  {
    "filename": "test4.py",
    "indexed_at": "2026-05-17 09:05:33",
    "function_count": 1,
    "class_count": 0,
    "total_entities": 1
  }
]
```

---

### 2. Структура конкретного файла

```
GET /api/files/test3.py/structure
```

```json
{
  "filename": "test3.py",
  "entities": [
    {
      "name": "Task",
      "entity_type": "class",
      "start_line": 1,
      "end_line": 5,
      "docstring": null
    },
    {
      "name": "__init__",
      "entity_type": "function",
      "start_line": 2,
      "end_line": 5,
      "docstring": null
    },
    {
      "name": "Queue",
      "entity_type": "class",
      "start_line": 7,
      "end_line": 31,
      "docstring": null
    },
    {
      "name": "__init__",
      "entity_type": "function",
      "start_line": 8,
      "end_line": 9,
      "docstring": null
    },
    {
      "name": "enqueue",
      "entity_type": "function",
      "start_line": 11,
      "end_line": 12,
      "docstring": null
    },
    {
      "name": "dequeue",
      "entity_type": "function",
      "start_line": 14,
      "end_line": 17,
      "docstring": null
    },
    {
      "name": "front",
      "entity_type": "function",
      "start_line": 19,
      "end_line": 22,
      "docstring": null
    },
    {
      "name": "isEmpty",
      "entity_type": "function",
      "start_line": 24,
      "end_line": 25,
      "docstring": null
    },
    {
      "name": "printqueue",
      "entity_type": "function",
      "start_line": 27,
      "end_line": 31,
      "docstring": null
    }
  ]
}
```

Если файл не найден — возвращается `[]`.

---

### 3. Поиск по ключевому слову

```
GET /api/search?q=where
```

```json
[
    {
    "filename": "test2.py",
    "name": "where_through_N",
    "entity_type": "function",
    "start_line": 142,
    "end_line": 157,
    "docstring": null
  },
  {
    "filename": "test2.py",
    "name": "where_through_time",
    "entity_type": "function",
    "start_line": 159,
    "end_line": 176,
    "docstring": null
  }
]
```

Если ничего не найдено — возвращается `[]`.

---

### 4. Поиск с фильтрацией по типу (бонус)

```
GET /api/search?q=task&type=class
```

```json
[
  {
    "filename": "test3.py",
    "name": "Task",
    "entity_type": "class",
    "start_line": 1,
    "end_line": 5,
    "docstring": null
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
  "total_files": 4,
  "total_functions": 81,
  "total_classes": 14,
  "total_entities": 95
}
```
