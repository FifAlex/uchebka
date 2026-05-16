"""
REST API для навигации по кодовой базе.
Предоставляет эндпоинты для получения информации о файлах и поиска функций/классов.
"""

import sqlite3
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI(
    title="Архив кода API",
    description="API для навигации по кодовой базе",
    version="1.0.0"
)

DATABASE = "code_index.db"

# Допустимые типы сущностей для фильтрации
VALID_ENTITY_TYPES = {"function", "class"}


def get_db_connection():
    """Создание соединения с базой данных."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


@app.get("/")
async def root():
    """Корневой эндпоинт."""
    return {
        "message": "API для навигации по кодовой базе",
        "docs": "/docs"
    }


@app.get("/api/files")
async def list_files():
    """
    Получение списка всех проиндексированных файлов
    с количеством функций и классов в каждом.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT
            f.filename,
            f.indexed_at,
            COUNT(CASE WHEN ce.entity_type = 'function' THEN 1 END) AS function_count,
            COUNT(CASE WHEN ce.entity_type = 'class'    THEN 1 END) AS class_count,
            COUNT(ce.id) AS total_entities
        FROM files f
        LEFT JOIN code_entities ce ON f.id = ce.file_id
        GROUP BY f.id, f.filename, f.indexed_at
        ORDER BY f.filename
    ''')

    files = [
        {
            "filename": row["filename"],
            "indexed_at": row["indexed_at"],
            "function_count": row["function_count"],
            "class_count": row["class_count"],
            "total_entities": row["total_entities"]
        }
        for row in cursor.fetchall()
    ]

    conn.close()
    return files  # Пустой список [] если файлов нет — это корректный ответ


@app.get("/api/files/{filename}/structure")
async def get_file_structure(filename: str):
    """
    Получение полной структуры файла:
    все функции и классы с номерами строк и docstring.
    Возвращает [], если файл не найден.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT id FROM files WHERE filename = ?', (filename,))
    file_row = cursor.fetchone()

    # ИСПРАВЛЕНИЕ: раньше при отсутствии файла возвращался [],
    # а при наличии — словарь {}. Теперь оба случая возвращают
    # согласованный тип: [] или {"filename": ..., "entities": [...]}.
    if not file_row:
        conn.close()
        return []

    cursor.execute('''
        SELECT name, entity_type, start_line, end_line, docstring
        FROM code_entities
        WHERE file_id = ?
        ORDER BY start_line
    ''', (file_row["id"],))

    entities = [
        {
            "name": row["name"],
            "entity_type": row["entity_type"],
            "start_line": row["start_line"],
            "end_line": row["end_line"],
            "docstring": row["docstring"] if row["docstring"] else None
        }
        for row in cursor.fetchall()
    ]

    conn.close()

    # Файл существует, но в нём нет сущностей — тоже валидный случай
    return {
        "filename": filename,
        "entities": entities
    }


@app.get("/api/search")
async def search_entities(
    q: str = Query(..., description="Ключевое слово для поиска"),
    type: Optional[str] = Query(
        None,
        description="Фильтр по типу: 'function' или 'class'"  # БОНУС 1
    )
):
    """
    Поиск функций и классов по имени или описанию (docstring).
    Поиск регистронезависимый.

    - **q** — обязательное ключевое слово
    - **type** — необязательный фильтр: `function` или `class`
    """
    # БОНУС 1: валидация параметра type
    if type is not None and type not in VALID_ENTITY_TYPES:
        return JSONResponse(
            status_code=400,
            content={
                "detail": f"Недопустимый тип '{type}'. "
                          f"Допустимые значения: {sorted(VALID_ENTITY_TYPES)}"
            }
        )

    conn = get_db_connection()
    cursor = conn.cursor()

    search_term = f"%{q}%"

    # БОНУС 1: добавляем фильтрацию по entity_type если передан параметр ?type=
    if type is not None:
        cursor.execute('''
            SELECT
                f.filename,
                ce.name,
                ce.entity_type,
                ce.start_line,
                ce.end_line,
                ce.docstring
            FROM code_entities ce
            JOIN files f ON ce.file_id = f.id
            WHERE (
                LOWER(ce.name) LIKE LOWER(?)
                OR LOWER(COALESCE(ce.docstring, '')) LIKE LOWER(?)
            )
            AND ce.entity_type = ?
            ORDER BY f.filename, ce.start_line
        ''', (search_term, search_term, type))
    else:
        cursor.execute('''
            SELECT
                f.filename,
                ce.name,
                ce.entity_type,
                ce.start_line,
                ce.end_line,
                ce.docstring
            FROM code_entities ce
            JOIN files f ON ce.file_id = f.id
            WHERE
                LOWER(ce.name) LIKE LOWER(?)
                OR LOWER(COALESCE(ce.docstring, '')) LIKE LOWER(?)
            ORDER BY f.filename, ce.start_line
        ''', (search_term, search_term))

    results = [
        {
            "filename": row["filename"],
            "name": row["name"],
            "entity_type": row["entity_type"],
            "start_line": row["start_line"],
            "end_line": row["end_line"],
            "docstring": row["docstring"] if row["docstring"] else None
        }
        for row in cursor.fetchall()
    ]

    conn.close()
    return results  # [] если ничего не найдено — не 500, а пустой список


# БОНУС 2: эндпоинт со сводной статистикой
@app.get("/api/stats")
async def get_stats():
    """
    Сводная статистика по всей индексированной кодовой базе:
    количество файлов, функций и классов.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) AS cnt FROM files')
    total_files = cursor.fetchone()["cnt"]

    cursor.execute(
        "SELECT COUNT(*) AS cnt FROM code_entities WHERE entity_type = 'function'"
    )
    total_functions = cursor.fetchone()["cnt"]

    cursor.execute(
        "SELECT COUNT(*) AS cnt FROM code_entities WHERE entity_type = 'class'"
    )
    total_classes = cursor.fetchone()["cnt"]

    conn.close()

    return {
        "total_files": total_files,
        "total_functions": total_functions,
        "total_classes": total_classes,
        "total_entities": total_functions + total_classes
    }


# ИСПРАВЛЕНИЕ: убран глобальный exception_handler(404).
# Он перехватывал ВСЕ 404, включая системные (например /docs при ошибках),
# и возвращал им [] с кодом 200, что нарушало работу Swagger UI.
# Каждый эндпоинт теперь сам возвращает [] при пустом результате.


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
