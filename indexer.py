"""
Индексатор Python-файлов.
Извлекает информацию о функциях и классах с помощью модуля ast
и сохраняет в базу данных SQLite.
"""

import ast
import sqlite3
import os
from pathlib import Path
from typing import List, Dict, Any


class CodeIndexer:
    """Класс для индексации Python-файлов и сохранения структуры в SQLite."""

    def __init__(self, db_path: str = "code_index.db"):
        """
        Инициализация индексатора.

        Args:
            db_path: Путь к файлу базы данных SQLite
        """
        self.db_path = db_path
        self.conn = None
        self.cursor = None

    def connect(self):
        """Установка соединения с базой данных."""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

    def close(self):
        """Закрытие соединения с базой данных."""
        if self.conn:
            self.conn.close()

    def create_tables(self):
        """Создание таблиц в базе данных, если они не существуют."""
        self.cursor.executescript('''
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL UNIQUE,
                indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS code_entities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                entity_type TEXT NOT NULL CHECK(entity_type IN ('function', 'class')),
                start_line INTEGER NOT NULL,
                end_line INTEGER NOT NULL,
                docstring TEXT,
                FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_entity_name
                ON code_entities(name);

            CREATE INDEX IF NOT EXISTS idx_entity_type
                ON code_entities(entity_type);
        ''')
        self.conn.commit()

    def extract_docstring(self, node: ast.AST) -> str:
        """
        Извлечение docstring из AST-узла.

        Args:
            node: AST-узел функции или класса

        Returns:
            Строка с docstring или None
        """
        return ast.get_docstring(node)

    def parse_file(self, filepath: str) -> Dict[str, Any]:
        """
        Парсинг Python-файла и извлечение структуры.

        Обходит только верхний уровень и тела классов, чтобы не дублировать
        вложенные функции (методы класса индексируются один раз — внутри класса).

        Args:
            filepath: Путь к Python-файлу

        Returns:
            Словарь с информацией о файле и его сущностях
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        tree = ast.parse(content)
        entities = []

        # ИСПРАВЛЕНИЕ: используем обход только верхнего уровня + тел классов
        # вместо ast.walk по всему дереву, чтобы избежать двойного счёта
        # вложенных функций. Методы класса всё равно попадают в индекс.
        def collect(nodes):
            for node in nodes:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    entities.append({
                        'name': node.name,
                        'entity_type': 'function',
                        'start_line': node.lineno,
                        'end_line': node.end_lineno,
                        'docstring': self.extract_docstring(node)
                    })
                    # Рекурсивно обходим тело функции для вложенных функций/классов
                    collect(node.body)
                elif isinstance(node, ast.ClassDef):
                    entities.append({
                        'name': node.name,
                        'entity_type': 'class',
                        'start_line': node.lineno,
                        'end_line': node.end_lineno,
                        'docstring': self.extract_docstring(node)
                    })
                    # Обходим тело класса для методов
                    collect(node.body)

        collect(tree.body)

        return {
            'filename': os.path.basename(filepath),
            'entities': entities
        }

    def save_to_db(self, file_data: Dict[str, Any]):
        """
        Сохранение данных о файле и его сущностях в базу данных.
        Старые данные об этом файле удаляются перед вставкой новых.

        Args:
            file_data: Словарь с данными о файле
        """
        # Удаляем старые данные о файле (CASCADE удалит и сущности)
        self.cursor.execute(
            'DELETE FROM files WHERE filename = ?',
            (file_data['filename'],)
        )

        # Вставляем информацию о файле
        self.cursor.execute(
            'INSERT INTO files (filename) VALUES (?)',
            (file_data['filename'],)
        )
        file_id = self.cursor.lastrowid

        # Вставляем все сущности пакетом
        self.cursor.executemany(
            '''INSERT INTO code_entities
               (file_id, name, entity_type, start_line, end_line, docstring)
               VALUES (?, ?, ?, ?, ?, ?)''',
            [
                (
                    file_id,
                    entity['name'],
                    entity['entity_type'],
                    entity['start_line'],
                    entity['end_line'],
                    entity['docstring']
                )
                for entity in file_data['entities']
            ]
        )

        self.conn.commit()

    def index_directory(self, directory: str = "data") -> Dict[str, int]:
        """
        Индексация всех Python-файлов в указанной директории.

        Args:
            directory: Путь к директории с .py файлами

        Returns:
            Словарь со статистикой индексации
        """
        self.connect()
        self.create_tables()

        # ИСПРАВЛЕНИЕ: убрана двойная очистка (DELETE FROM files/code_entities).
        # save_to_db уже удаляет старые записи конкретного файла через
        # DELETE FROM files WHERE filename = ?, поэтому глобальная очистка
        # здесь лишняя и мешает инкрементному переиндексированию.
        # Если нужна полная переиндексация — раскомментируйте строки ниже:
        # self.cursor.execute('DELETE FROM files')
        # self.conn.commit()

        py_files = list(Path(directory).glob('*.py'))

        if not py_files:
            print(f"Предупреждение: в директории '{directory}' нет .py файлов.")

        stats = {
            'total_files': 0,
            'total_functions': 0,
            'total_classes': 0
        }

        for py_file in py_files:
            try:
                file_data = self.parse_file(str(py_file))
                self.save_to_db(file_data)

                stats['total_files'] += 1
                stats['total_functions'] += sum(
                    1 for e in file_data['entities']
                    if e['entity_type'] == 'function'
                )
                stats['total_classes'] += sum(
                    1 for e in file_data['entities']
                    if e['entity_type'] == 'class'
                )

                print(f"✓ Проиндексирован: {py_file.name}")

            except SyntaxError as e:
                print(f"✗ Синтаксическая ошибка в {py_file.name}: {e}")
            except Exception as e:
                print(f"✗ Ошибка при индексации {py_file.name}: {e}")

        self.close()
        return stats


def main():
    """Запуск индексации."""
    indexer = CodeIndexer()
    stats = indexer.index_directory("data")

    print("\n=== Статистика индексации ===")
    print(f"Файлов обработано: {stats['total_files']}")
    print(f"Функций найдено:   {stats['total_functions']}")
    print(f"Классов найдено:   {stats['total_classes']}")


if __name__ == "__main__":
    main()
