
import sqlite3
from typing import List, Optional, Dict, Any
from datetime import datetime

from models.task import Task
from models.project import Project
from models.user import User


class DatabaseManager:
    def __init__(self, db_path: str = "tasks.db") -> None:
        self.db_path = db_path
        self.connection: Optional[sqlite3.Connection] = None
        self.connect()
    
    def connect(self) -> None:
        """Установить соединение с базой данных"""
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row  # Возвращать строки как словари
        self.create_tables()
    
    def close(self) -> None:
        """Закрыть соединение с базой данных"""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def __enter__(self):
        """Контекстный менеджер для использования with"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Закрытие соединения при выходе из контекста"""
        self.close()
    
    def execute_query(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        if not self.connection:
            self.connect()
        
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        self.connection.commit()
        return cursor
    
    def create_tables(self) -> None:
        """Создать все необходимые таблицы в базе данных"""
        # Таблица пользователей
        users_table = """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            role TEXT NOT NULL CHECK(role IN ('admin', 'manager', 'developer')),
            registration_date TIMESTAMP NOT NULL
        )
        """
        
        # Таблица проектов
        projects_table = """
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            start_date TIMESTAMP NOT NULL,
            end_date TIMESTAMP NOT NULL,
            status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'completed', 'on_hold'))
        )
        """
        
        # Таблица задач
        tasks_table = """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            priority INTEGER NOT NULL CHECK(priority IN (1, 2, 3)),
            status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'in_progress', 'completed')),
            due_date TIMESTAMP NOT NULL,
            project_id INTEGER NOT NULL,
            assignee_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
            FOREIGN KEY (assignee_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
        
        # Создаем таблицы
        self.execute_query(users_table)
        self.execute_query(projects_table)
        self.execute_query(tasks_table)
        
        # Создаем индексы для ускорения поиска
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_tasks_project ON tasks(project_id)",
            "CREATE INDEX IF NOT EXISTS idx_tasks_assignee ON tasks(assignee_id)",
            "CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)",
            "CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority)",
            "CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date)",
            "CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status)",
            "CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)"
        ]
        
        for index in indexes:
            try:
                self.execute_query(index)
            except:
                pass  # Игнорируем ошибки создания индексов
    
    # ========== Методы для работы с задачами ==========
    
    def add_task(self, task: Task) -> int:
        query = """
        INSERT INTO tasks (title, description, priority, status, due_date, project_id, assignee_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        cursor = self.execute_query(
            query,
            (
                task.title,
                task.description,
                task.priority,
                task.status,
                task.due_date.isoformat(),
                task.project_id,
                task.assignee_id
            )
        )
        
        task.id = cursor.lastrowid
        return task.id
    
    def get_task_by_id(self, task_id: int) -> Optional[Task]:
        query = "SELECT * FROM tasks WHERE id = ?"
        cursor = self.execute_query(query, (task_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        return self._row_to_task(dict(row))
    
    def get_all_tasks(self) -> List[Task]:
        query = "SELECT * FROM tasks ORDER BY due_date"
        cursor = self.execute_query(query)
        rows = cursor.fetchall()
        
        tasks = []
        for row in rows:
            tasks.append(self._row_to_task(dict(row)))
        
        return tasks
    
    def update_task(self, task_id: int, **kwargs) -> bool:
        if not kwargs:
            return False
        
        # Проверяем существование задачи
        task = self.get_task_by_id(task_id)
        if not task:
            return False
        
        # Формируем запрос обновления
        set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
        values = list(kwargs.values())
        
        # Конвертируем datetime в строку
        for i, (key, value) in enumerate(kwargs.items()):
            if isinstance(value, datetime):
                values[i] = value.isoformat()
        
        query = f"UPDATE tasks SET {set_clause} WHERE id = ?"
        values.append(task_id)
        
        try:
            self.execute_query(query, tuple(values))
            return True
        except sqlite3.Error:
            return False
    
    def delete_task(self, task_id: int) -> bool:
        query = "DELETE FROM tasks WHERE id = ?"
        
        try:
            cursor = self.execute_query(query, (task_id,))
            return cursor.rowcount > 0
        except sqlite3.Error:
            return False
    
    def search_tasks(self, query_text: str) -> List[Task]:
        search_pattern = f"%{query_text}%"
        query = """
        SELECT * FROM tasks 
        WHERE title LIKE ? OR description LIKE ?
        ORDER BY due_date
        """
        
        cursor = self.execute_query(query, (search_pattern, search_pattern))
        rows = cursor.fetchall()
        
        tasks = []
        for row in rows:
            tasks.append(self._row_to_task(dict(row)))
        
        return tasks
    
    def get_tasks_by_project(self, project_id: int) -> List[Task]:
        query = """
        SELECT * FROM tasks 
        WHERE project_id = ?
        ORDER BY priority, due_date
        """
        
        cursor = self.execute_query(query, (project_id,))
        rows = cursor.fetchall()
        
        tasks = []
        for row in rows:
            tasks.append(self._row_to_task(dict(row)))
        
        return tasks
    
    def get_tasks_by_user(self, user_id: int) -> List[Task]:
        query = """
        SELECT * FROM tasks 
        WHERE assignee_id = ?
        ORDER BY due_date, priority
        """
        
        cursor = self.execute_query(query, (user_id,))
        rows = cursor.fetchall()
        
        tasks = []
        for row in rows:
            tasks.append(self._row_to_task(dict(row)))
        
        return tasks
    
    def _row_to_task(self, row: Dict[str, Any]) -> Task:
        task = Task(
            title=row['title'],
            description=row['description'],
            priority=row['priority'],
            due_date=datetime.fromisoformat(row['due_date']),
            project_id=row['project_id'],
            assignee_id=row['assignee_id']
        )
        task.id = row['id']
        task.status = row['status']
        return task
    
    # ========== Методы для работы с проектами ==========
    
    def add_project(self, project: Project) -> int:
        query = """
        INSERT INTO projects (name, description, start_date, end_date, status)
        VALUES (?, ?, ?, ?, ?)
        """
        
        cursor = self.execute_query(
            query,
            (
                project.name,
                project.description,
                project.start_date.isoformat(),
                project.end_date.isoformat(),
                project.status
            )
        )
        
        project.id = cursor.lastrowid
        return project.id
    
    def get_project_by_id(self, project_id: int) -> Optional[Project]:
        query = "SELECT * FROM projects WHERE id = ?"
        cursor = self.execute_query(query, (project_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        return self._row_to_project(dict(row))
    
    def get_all_projects(self) -> List[Project]:
        query = "SELECT * FROM projects ORDER BY end_date"
        cursor = self.execute_query(query)
        rows = cursor.fetchall()
        
        projects = []
        for row in rows:
            projects.append(self._row_to_project(dict(row)))
        
        return projects
    
    def update_project(self, project_id: int, **kwargs) -> bool:
        if not kwargs:
            return False
        
        # Проверяем существование проекта
        project = self.get_project_by_id(project_id)
        if not project:
            return False
        
        # Формируем запрос обновления
        set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
        values = list(kwargs.values())
        
        # Конвертируем datetime в строку
        for i, (key, value) in enumerate(kwargs.items()):
            if isinstance(value, datetime):
                values[i] = value.isoformat()
        
        query = f"UPDATE projects SET {set_clause} WHERE id = ?"
        values.append(project_id)
        
        try:
            self.execute_query(query, tuple(values))
            return True
        except sqlite3.Error:
            return False
    
    def delete_project(self, project_id: int) -> bool:
        query = "DELETE FROM projects WHERE id = ?"
        
        try:
            cursor = self.execute_query(query, (project_id,))
            return cursor.rowcount > 0
        except sqlite3.Error:
            return False
    
    def _row_to_project(self, row: Dict[str, Any]) -> Project:
        project = Project(
            name=row['name'],
            description=row['description'],
            start_date=datetime.fromisoformat(row['start_date']),
            end_date=datetime.fromisoformat(row['end_date'])
        )
        project.id = row['id']
        project.status = row['status']
        return project
    
    # ========== Методы для работы с пользователями ==========
    
    def add_user(self, user: User) -> int:
        query = """
        INSERT INTO users (username, email, role, registration_date)
        VALUES (?, ?, ?, ?)
        """
        
        cursor = self.execute_query(
            query,
            (
                user.username,
                user.email,
                user.role,
                user.registration_date.isoformat()
            )
        )
        
        user.id = cursor.lastrowid
        return user.id
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        query = "SELECT * FROM users WHERE id = ?"
        cursor = self.execute_query(query, (user_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        return self._row_to_user(dict(row))
    
    def get_all_users(self) -> List[User]:
        query = "SELECT * FROM users ORDER BY username"
        cursor = self.execute_query(query)
        rows = cursor.fetchall()
        
        users = []
        for row in rows:
            users.append(self._row_to_user(dict(row)))
        
        return users
    
    def update_user(self, user_id: int, **kwargs) -> bool:
        if not kwargs:
            return False
        
        # Проверяем существование пользователя
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        # Формируем запрос обновления
        set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
        values = list(kwargs.values())
        
        # Конвертируем datetime в строку
        for i, (key, value) in enumerate(kwargs.items()):
            if isinstance(value, datetime):
                values[i] = value.isoformat()
        
        query = f"UPDATE users SET {set_clause} WHERE id = ?"
        values.append(user_id)
        
        try:
            self.execute_query(query, tuple(values))
            return True
        except sqlite3.Error:
            return False
    
    def delete_user(self, user_id: int) -> bool:
        query = "DELETE FROM users WHERE id = ?"
        
        try:
            cursor = self.execute_query(query, (user_id,))
            return cursor.rowcount > 0
        except sqlite3.Error:
            return False