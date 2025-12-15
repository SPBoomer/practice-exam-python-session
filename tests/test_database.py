import pytest
import tempfile
import os
import sqlite3
from datetime import datetime, timedelta

from database.database_manager import DatabaseManager
from models.task import Task
from models.project import Project
from models.user import User


class TestDatabaseCreation:
    """Тесты создания базы данных и таблиц"""
    
    def test_database_connection(self):
        """Тест соединения с базой данных"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            db_path = temp_db.name
        
        try:
            db = DatabaseManager(db_path)
            assert db.connection is not None
            assert os.path.exists(db_path)
            
            # Проверяем что можно выполнять запросы
            cursor = db.execute_query("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1
            
            db.close()
            assert db.connection is None
            
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    def test_create_tables(self):
        """Тест создания таблиц"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            db_path = temp_db.name
        
        try:
            db = DatabaseManager(db_path)
            
            # Проверяем что таблицы созданы
            cursor = db.execute_query(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = [row['name'] for row in cursor.fetchall()]
            
            assert 'users' in tables
            assert 'projects' in tables
            assert 'tasks' in tables
            
            # Проверяем структуру таблицы users
            cursor = db.execute_query("PRAGMA table_info(users)")
            users_columns = {row['name']: row['type'] for row in cursor.fetchall()}
            
            assert 'id' in users_columns
            assert 'username' in users_columns
            assert 'email' in users_columns
            assert 'role' in users_columns
            assert 'registration_date' in users_columns
            
            # Проверяем структуру таблицы projects
            cursor = db.execute_query("PRAGMA table_info(projects)")
            projects_columns = {row['name']: row['type'] for row in cursor.fetchall()}
            
            assert 'id' in projects_columns
            assert 'name' in projects_columns
            assert 'description' in projects_columns
            assert 'start_date' in projects_columns
            assert 'end_date' in projects_columns
            assert 'status' in projects_columns
            
            # Проверяем структуру таблицы tasks
            cursor = db.execute_query("PRAGMA table_info(tasks)")
            tasks_columns = {row['name']: row['type'] for row in cursor.fetchall()}
            
            assert 'id' in tasks_columns
            assert 'title' in tasks_columns
            assert 'description' in tasks_columns
            assert 'priority' in tasks_columns
            assert 'status' in tasks_columns
            assert 'due_date' in tasks_columns
            assert 'project_id' in tasks_columns
            assert 'assignee_id' in tasks_columns
            
            db.close()
            
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    def test_table_constraints(self):
        """Тест ограничений таблиц"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            db_path = temp_db.name
        
        try:
            db = DatabaseManager(db_path)
            
            # Проверяем ограничения таблицы users
            cursor = db.execute_query(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name='users'"
            )
            users_sql = cursor.fetchone()['sql'].lower()
            
            assert 'primary key' in users_sql
            assert 'unique' in users_sql
            assert 'check' in users_sql  # Для ролей
            
            # Проверяем ограничения таблицы projects
            cursor = db.execute_query(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name='projects'"
            )
            projects_sql = cursor.fetchone()['sql'].lower()
            
            assert 'primary key' in projects_sql
            assert 'check' in projects_sql  # Для статусов
            
            # Проверяем ограничения таблицы tasks
            cursor = db.execute_query(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name='tasks'"
            )
            tasks_sql = cursor.fetchone()['sql'].lower()
            
            assert 'primary key' in tasks_sql
            assert 'foreign key' in tasks_sql  # Внешние ключи
            assert 'check' in tasks_sql  # Для приоритетов и статусов
            
            db.close()
            
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    def test_foreign_key_constraints(self):
        """Тест ограничений внешних ключей"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            db_path = temp_db.name
        
        try:
            db = DatabaseManager(db_path)
            
            # Включаем проверку внешних ключей
            db.execute_query("PRAGMA foreign_keys = ON")
            
            # Создаем пользователя
            user = User("testuser", "test@example.com", "developer")
            user_id = db.add_user(user)
            
            # Пытаемся создать задачу с несуществующим проектом (должна быть ошибка)
            task = Task(
                title="Test Task",
                description="Description",
                priority=1,
                due_date=datetime.now() + timedelta(days=7),
                project_id=999,  # Несуществующий проект
                assignee_id=user_id
            )
            
            with pytest.raises(sqlite3.IntegrityError):
                db.add_task(task)
            
            db.close()
            
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    def test_indexes_creation(self):
        """Тест создания индексов"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            db_path = temp_db.name
        
        try:
            db = DatabaseManager(db_path)
            
            # Проверяем что индексы созданы
            cursor = db.execute_query(
                "SELECT name FROM sqlite_master WHERE type='index'"
            )
            indexes = [row['name'] for row in cursor.fetchall()]
            
            # Проверяем основные индексы
            expected_indexes = [
                'idx_tasks_project',
                'idx_tasks_assignee',
                'idx_tasks_status',
                'idx_tasks_priority',
                'idx_tasks_due_date'
            ]
            
            for index in expected_indexes:
                assert any(index in idx for idx in indexes), f"Индекс {index} не найден"
            
            db.close()
            
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)


class TestDatabaseCRUDOperations:
    """Тесты CRUD операций в базе данных"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db_path = self.temp_db.name
        self.db = DatabaseManager(self.db_path)
    
    def teardown_method(self):
        """Очистка после каждого теста"""
        self.db.close()
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def test_user_crud_operations(self):
        """Тест CRUD операций для пользователей"""
        # Create - Создание
        user1 = User("user1", "user1@example.com", "developer")
        user1_id = self.db.add_user(user1)
        assert user1_id == 1
        assert user1.id == 1
        
        user2 = User("user2", "user2@example.com", "manager")
        user2_id = self.db.add_user(user2)
        assert user2_id == 2
        assert user2.id == 2
        
        # Read - Чтение
        retrieved_user1 = self.db.get_user_by_id(user1_id)
        assert retrieved_user1 is not None
        assert retrieved_user1.username == "user1"
        assert retrieved_user1.email == "user1@example.com"
        assert retrieved_user1.role == "developer"
        
        retrieved_user2 = self.db.get_user_by_id(user2_id)
        assert retrieved_user2.username == "user2"
        
        # Получение по имени и email
        user_by_username = self.db.get_user_by_username("user1")
        assert user_by_username.id == user1_id
        
        user_by_email = self.db.get_user_by_email("user2@example.com")
        assert user_by_email.id == user2_id
        
        # Получение всех пользователей
        all_users = self.db.get_all_users()
        assert len(all_users) == 2
        
        # Update - Обновление
        success = self.db.update_user(user1_id, username="updated_user", role="admin")
        assert success is True
        
        updated_user = self.db.get_user_by_id(user1_id)
        assert updated_user.username == "updated_user"
        assert updated_user.role == "admin"
        
        # Delete - Удаление
        success = self.db.delete_user(user2_id)
        assert success is True
        
        deleted_user = self.db.get_user_by_id(user2_id)
        assert deleted_user is None
        
        # Проверяем что остался только один пользователь
        remaining_users = self.db.get_all_users()
        assert len(remaining_users) == 1
        assert remaining_users[0].username == "updated_user"
    
    def test_project_crud_operations(self):
        """Тест CRUD операций для проектов"""
        # Create - Создание
        start_date = datetime.now() - timedelta(days=10)
        end_date = start_date + timedelta(days=30)
        
        project1 = Project("Project 1", "First project", start_date, end_date)
        project1_id = self.db.add_project(project1)
        assert project1_id == 1
        assert project1.id == 1
        
        project2 = Project("Project 2", "Second project", start_date, end_date + timedelta(days=10))
        project2_id = self.db.add_project(project2)
        assert project2_id == 2
        
        # Read - Чтение
        retrieved_project1 = self.db.get_project_by_id(project1_id)
        assert retrieved_project1 is not None
        assert retrieved_project1.name == "Project 1"
        assert retrieved_project1.description == "First project"
        assert retrieved_project1.status == "active"
        
        # Получение всех проектов
        all_projects = self.db.get_all_projects()
        assert len(all_projects) == 2
        
        # Update - Обновление
        success = self.db.update_project(
            project1_id, 
            name="Updated Project", 
            status="on_hold"
        )
        assert success is True
        
        updated_project = self.db.get_project_by_id(project1_id)
        assert updated_project.name == "Updated Project"
        assert updated_project.status == "on_hold"
        
        # Delete - Удаление
        success = self.db.delete_project(project2_id)
        assert success is True
        
        deleted_project = self.db.get_project_by_id(project2_id)
        assert deleted_project is None
        
        # Проверяем что остался только один проект
        remaining_projects = self.db.get_all_projects()
        assert len(remaining_projects) == 1
        assert remaining_projects[0].name == "Updated Project"
    
    def test_task_crud_operations(self):
        """Тест CRUD операций для задач"""
        # Создаем тестовые данные
        user = User("taskuser", "taskuser@example.com", "developer")
        user_id = self.db.add_user(user)
        
        start_date = datetime.now() - timedelta(days=10)
        end_date = start_date + timedelta(days=30)
        project = Project("Task Project", "Project for tasks", start_date, end_date)
        project_id = self.db.add_project(project)
        
        # Create - Создание
        due_date1 = datetime.now() + timedelta(days=7)
        task1 = Task("Task 1", "First task", 1, due_date1, project_id, user_id)
        task1_id = self.db.add_task(task1)
        assert task1_id == 1
        assert task1.id == 1
        
        due_date2 = datetime.now() + timedelta(days=14)
        task2 = Task("Task 2", "Second task", 2, due_date2, project_id, user_id)
        task2_id = self.db.add_task(task2)
        assert task2_id == 2
        
        # Read - Чтение
        retrieved_task1 = self.db.get_task_by_id(task1_id)
        assert retrieved_task1 is not None
        assert retrieved_task1.title == "Task 1"
        assert retrieved_task1.description == "First task"
        assert retrieved_task1.priority == 1
        assert retrieved_task1.status == "pending"
        assert retrieved_task1.project_id == project_id
        assert retrieved_task1.assignee_id == user_id
        
        # Получение всех задач
        all_tasks = self.db.get_all_tasks()
        assert len(all_tasks) == 2
        
        # Update - Обновление
        success = self.db.update_task(
            task1_id,
            title="Updated Task",
            priority=3,
            status="in_progress"
        )
        assert success is True
        
        updated_task = self.db.get_task_by_id(task1_id)
        assert updated_task.title == "Updated Task"
        assert updated_task.priority == 3
        assert updated_task.status == "in_progress"
        
        # Delete - Удаление
        success = self.db.delete_task(task2_id)
        assert success is True
        
        deleted_task = self.db.get_task_by_id(task2_id)
        assert deleted_task is None
        
        # Проверяем что осталась только одна задача
        remaining_tasks = self.db.get_all_tasks()
        assert len(remaining_tasks) == 1
        assert remaining_tasks[0].title == "Updated Task"
    
    def test_search_tasks_operation(self):
        """Тест операции поиска задач"""
        # Создаем тестовые данные
        user = User("searchuser", "search@example.com", "developer")
        user_id = self.db.add_user(user)
        
        project = Project("Search Project", "Project for search", 
                         datetime.now() - timedelta(days=10),
                         datetime.now() + timedelta(days=30))
        project_id = self.db.add_project(project)
        
        # Создаем задачи с разными названиями и описаниями
        due_date = datetime.now() + timedelta(days=7)
        
        task1 = Task("Важная задача", "Срочно сделать", 1, due_date, project_id, user_id)
        self.db.add_task(task1)
        
        task2 = Task("Обычная задача", "Сделать когда будет время", 2, due_date, project_id, user_id)
        self.db.add_task(task2)
        
        task3 = Task("Другая задача", "Важная информация", 3, due_date, project_id, user_id)
        self.db.add_task(task3)
        
        # Ищем по названию
        tasks = self.db.search_tasks("Важная")
        assert len(tasks) == 2  # task1 и task3
        
        # Ищем по описанию
        tasks = self.db.search_tasks("срочно")
        assert len(tasks) == 1
        assert tasks[0].title == "Важная задача"
        
        # Ищем по частичному совпадению
        tasks = self.db.search_tasks("зада")
        assert len(tasks) == 3  # Все задачи
        
        # Ищем несуществующее
        tasks = self.db.search_tasks("несуществующее")
        assert len(tasks) == 0
    
    def test_get_tasks_by_project_operation(self):
        """Тест получения задач по проекту"""
        # Создаем тестовые данные
        user = User("projectuser", "project@example.com", "developer")
        user_id = self.db.add_user(user)
        
        # Создаем два проекта
        project1 = Project("Project 1", "First project",
                          datetime.now() - timedelta(days=10),
                          datetime.now() + timedelta(days=30))
        project1_id = self.db.add_project(project1)
        
        project2 = Project("Project 2", "Second project",
                          datetime.now() - timedelta(days=5),
                          datetime.now() + timedelta(days=20))
        project2_id = self.db.add_project(project2)
        
        # Добавляем задачи в оба проекта
        due_date = datetime.now() + timedelta(days=7)
        
        task1 = Task("Task for Project 1", "Description", 1, due_date, project1_id, user_id)
        self.db.add_task(task1)
        
        task2 = Task("Another task for Project 1", "Description", 2, due_date, project1_id, user_id)
        self.db.add_task(task2)
        
        task3 = Task("Task for Project 2", "Description", 3, due_date, project2_id, user_id)
        self.db.add_task(task3)
        
        # Получаем задачи проекта 1
        tasks_project1 = self.db.get_tasks_by_project(project1_id)
        assert len(tasks_project1) == 2
        assert all(task.project_id == project1_id for task in tasks_project1)
        
        # Получаем задачи проекта 2
        tasks_project2 = self.db.get_tasks_by_project(project2_id)
        assert len(tasks_project2) == 1
        assert tasks_project2[0].project_id == project2_id
    
    def test_get_tasks_by_user_operation(self):
        """Тест получения задач по пользователю"""
        # Создаем двух пользователей
        user1 = User("user1", "user1@example.com", "developer")
        user1_id = self.db.add_user(user1)
        
        user2 = User("user2", "user2@example.com", "developer")
        user2_id = self.db.add_user(user2)
        
        # Создаем проект
        project = Project("User Project", "Project for users",
                         datetime.now() - timedelta(days=10),
                         datetime.now() + timedelta(days=30))
        project_id = self.db.add_project(project)
        
        # Добавляем задачи для обоих пользователей
        due_date = datetime.now() + timedelta(days=7)
        
        task1 = Task("Task for User 1", "Description", 1, due_date, project_id, user1_id)
        self.db.add_task(task1)
        
        task2 = Task("Another task for User 1", "Description", 2, due_date, project_id, user1_id)
        self.db.add_task(task2)
        
        task3 = Task("Task for User 2", "Description", 3, due_date, project_id, user2_id)
        self.db.add_task(task3)
        
        # Получаем задачи пользователя 1
        tasks_user1 = self.db.get_tasks_by_user(user1_id)
        assert len(tasks_user1) == 2
        assert all(task.assignee_id == user1_id for task in tasks_user1)
        
        # Получаем задачи пользователя 2
        tasks_user2 = self.db.get_tasks_by_user(user2_id)
        assert len(tasks_user2) == 1
        assert tasks_user2[0].assignee_id == user2_id


class TestDatabaseIntegrity:
    """Тесты целостности данных в базе данных"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db_path = self.temp_db.name
        self.db = DatabaseManager(self.db_path)
        
        # Включаем проверку внешних ключей
        self.db.execute_query("PRAGMA foreign_keys = ON")
    
    def teardown_method(self):
        """Очистка после каждого теста"""
        self.db.close()
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def test_user_uniqueness_constraints(self):
        """Тест ограничений уникальности для пользователей"""
        # Создаем первого пользователя
        user1 = User("uniqueuser", "unique@example.com", "developer")
        self.db.add_user(user1)
        
        # Пытаемся создать пользователя с тем же именем (должна быть ошибка)
        user2 = User("uniqueuser", "different@example.com", "developer")
        
        with pytest.raises(sqlite3.IntegrityError):
            self.db.add_user(user2)
        
        # Пытаемся создать пользователя с тем же email (должна быть ошибка)
        user3 = User("differentuser", "unique@example.com", "developer")
        
        with pytest.raises(sqlite3.IntegrityError):
            self.db.add_user(user3)
    
    def test_project_foreign_key_integrity(self):
        """Тест целостности внешних ключей для проектов"""
        # Создаем пользователя
        user = User("integrityuser", "integrity@example.com", "developer")
        user_id = self.db.add_user(user)
        
        # Пытаемся создать задачу с несуществующим проектом
        task = Task(
            title="Test Task",
            description="Description",
            priority=1,
            due_date=datetime.now() + timedelta(days=7),
            project_id=999,  # Несуществующий проект
            assignee_id=user_id
        )
        
        with pytest.raises(sqlite3.IntegrityError):
            self.db.add_task(task)
    
    def test_user_foreign_key_integrity(self):
        """Тест целостности внешних ключей для пользователей"""
        # Создаем проект
        project = Project(
            "Integrity Project",
            "Project for integrity tests",
            datetime.now() - timedelta(days=10),
            datetime.now() + timedelta(days=30)
        )
        project_id = self.db.add_project(project)
        
        # Пытаемся создать задачу с несуществующим пользователем
        task = Task(
            title="Test Task",
            description="Description",
            priority=1,
            due_date=datetime.now() + timedelta(days=7),
            project_id=project_id,
            assignee_id=999  # Несуществующий пользователь
        )
        
        with pytest.raises(sqlite3.IntegrityError):
            self.db.add_task(task)
    
    def test_cascade_delete_project(self):
        """Тест каскадного удаления при удалении проекта"""
        # Создаем пользователя и проект
        user = User("cascadeuser", "cascade@example.com", "developer")
        user_id = self.db.add_user(user)
        
        project = Project(
            "Cascade Project",
            "Project for cascade tests",
            datetime.now() - timedelta(days=10),
            datetime.now() + timedelta(days=30)
        )
        project_id = self.db.add_project(project)
        
        # Создаем несколько задач в проекте
        due_date = datetime.now() + timedelta(days=7)
        
        for i in range(3):
            task = Task(
                title=f"Task {i}",
                description=f"Description {i}",
                priority=1,
                due_date=due_date,
                project_id=project_id,
                assignee_id=user_id
            )
            self.db.add_task(task)
        
        # Проверяем что задачи созданы
        tasks_before = self.db.get_all_tasks()
        assert len(tasks_before) == 3
        
        # Удаляем проект
        success = self.db.delete_project(project_id)
        assert success is True
        
        # Проверяем что проект удален
        deleted_project = self.db.get_project_by_id(project_id)
        assert deleted_project is None
        
        # Проверяем что задачи также удалены (каскадное удаление)
        tasks_after = self.db.get_all_tasks()
        assert len(tasks_after) == 0
    
    def test_check_constraints(self):
        """Тест проверочных ограничений (CHECK constraints)"""
        # Тест ограничения роли пользователя
        with pytest.raises(sqlite3.IntegrityError):
            # Пытаемся создать пользователя с недопустимой ролью
            # Используем прямое выполнение SQL, так как User валидирует роль
            self.db.execute_query(
                "INSERT INTO users (username, email, role, registration_date) "
                "VALUES ('test', 'test@example.com', 'invalid_role', datetime('now'))"
            )
        
        # Тест ограничения приоритета задачи
        # Создаем пользователя и проект
        user = User("checkuser", "check@example.com", "developer")
        user_id = self.db.add_user(user)
        
        project = Project(
            "Check Project",
            "Project for check tests",
            datetime.now() - timedelta(days=10),
            datetime.now() + timedelta(days=30)
        )
        project_id = self.db.add_project(project)
        
        with pytest.raises(sqlite3.IntegrityError):
            # Пытаемся создать задачу с недопустимым приоритетом
            # Используем прямое выполнение SQL
            self.db.execute_query(
                "INSERT INTO tasks (title, description, priority, status, due_date, project_id, assignee_id) "
                "VALUES ('Test', 'Description', 5, 'pending', datetime('now', '+7 days'), ?, ?)",
                (project_id, user_id)
            )
        
        # Тест ограничения статуса задачи
        with pytest.raises(sqlite3.IntegrityError):
            # Пытаемся создать задачу с недопустимым статусом
            self.db.execute_query(
                "INSERT INTO tasks (title, description, priority, status, due_date, project_id, assignee_id) "
                "VALUES ('Test', 'Description', 1, 'invalid_status', datetime('now', '+7 days'), ?, ?)",
                (project_id, user_id)
            )
        
        # Тест ограничения статуса проекта
        with pytest.raises(sqlite3.IntegrityError):
            # Пытаемся создать проект с недопустимым статусом
            self.db.execute_query(
                "INSERT INTO projects (name, description, start_date, end_date, status) "
                "VALUES ('Test', 'Description', datetime('now'), datetime('now', '+30 days'), 'invalid_status')"
            )
    
    def test_data_type_integrity(self):
        """Тест целостности типов данных"""
        # Создаем пользователя
        user = User("typeuser", "type@example.com", "developer")
        user_id = self.db.add_user(user)
        
        project = Project(
            "Type Project",
            "Project for type tests",
            datetime.now() - timedelta(days=10),
            datetime.now() + timedelta(days=30)
        )
        project_id = self.db.add_project(project)
        
        # Пытаемся вставить данные неправильного типа
        with pytest.raises(sqlite3.IntegrityError):
            # Пытаемся вставить строку вместо числа для приоритета
            self.db.execute_query(
                "INSERT INTO tasks (title, description, priority, status, due_date, project_id, assignee_id) "
                "VALUES ('Test', 'Description', 'not_a_number', 'pending', datetime('now', '+7 days'), ?, ?)",
                (project_id, user_id)
            )
    
    def test_transaction_integrity(self):
        """Тест целостности транзакций"""
        # Начинаем транзакцию
        self.db.connection.execute("BEGIN TRANSACTION")
        
        try:
            # Создаем пользователя
            user = User("transactionuser", "transaction@example.com", "developer")
            user_id = self.db.add_user(user)
            
            # Создаем проект
            project = Project(
                "Transaction Project",
                "Project for transaction tests",
                datetime.now() - timedelta(days=10),
                datetime.now() + timedelta(days=30)
            )
            project_id = self.db.add_project(project)
            
            # Откатываем транзакцию
            self.db.connection.execute("ROLLBACK")
            
        except:
            self.db.connection.execute("ROLLBACK")
            raise
        
        # Проверяем что данные не сохранились после отката
        users = self.db.get_all_users()
        projects = self.db.get_all_projects()
        
        assert len(users) == 0
        assert len(projects) == 0
        
        # Тест успешной транзакции
        self.db.connection.execute("BEGIN TRANSACTION")
        
        try:
            user = User("successuser", "success@example.com", "developer")
            self.db.add_user(user)
            
            self.db.connection.execute("COMMIT")
            
        except:
            self.db.connection.execute("ROLLBACK")
            raise
        
        # Проверяем что данные сохранились после коммита
        users = self.db.get_all_users()
        assert len(users) == 1


class TestDatabaseStatistics:
    """Тесты статистических операций в базе данных"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db_path = self.temp_db.name
        self.db = DatabaseManager(self.db_path)
        
        # Создаем тестовые данные
        self._create_test_data()
    
    def teardown_method(self):
        """Очистка после каждого теста"""
        self.db.close()
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def _create_test_data(self):
        """Создание тестовых данных для статистики"""
        # Создаем пользователей
        self.user1 = User("statsuser1", "stats1@example.com", "developer")
        self.user1_id = self.db.add_user(self.user1)
        
        self.user2 = User("statsuser2", "stats2@example.com", "manager")
        self.user2_id = self.db.add_user(self.user2)
        
        # Создаем проекты
        start_date = datetime.now() - timedelta(days=30)
        
        self.project1 = Project(
            "Stats Project 1",
            "First project for stats",
            start_date,
            start_date + timedelta(days=60)
        )
        self.project1_id = self.db.add_project(self.project1)
        
        self.project2 = Project(
            "Stats Project 2",
            "Second project for stats",
            start_date + timedelta(days=10),
            start_date + timedelta(days=40)
        )
        self.project2_id = self.db.add_project(self.project2)
        
        # Создаем задачи с разными статусами и приоритетами
        now = datetime.now()
        
        # Задачи для проекта 1
        self.db.add_task(Task(
            "Completed Task 1", "Description", 1, now - timedelta(days=5),
            self.project1_id, self.user1_id
        ))
        self.db.update_task(1, status="completed")
        
        self.db.add_task(Task(
            "In Progress Task 1", "Description", 2, now + timedelta(days=5),
            self.project1_id, self.user1_id
        ))
        self.db.update_task(2, status="in_progress")
        
        self.db.add_task(Task(
            "Pending Task 1", "Description", 3, now + timedelta(days=10),
            self.project1_id, self.user1_id
        ))
        
        self.db.add_task(Task(
            "Overdue Task 1", "Description", 1, now - timedelta(days=1),
            self.project1_id, self.user2_id
        ))
        
        # Задачи для проекта 2
        self.db.add_task(Task(
            "Completed Task 2", "Description", 2, now - timedelta(days=3),
            self.project2_id, self.user2_id
        ))
        self.db.update_task(5, status="completed")
        
        self.db.add_task(Task(
            "Pending Task 2", "Description", 1, now + timedelta(days=7),
            self.project2_id, self.user1_id
        ))
    
    def test_get_project_statistics(self):
        """Тест получения статистики по проекту"""
        # Получаем статистику для проекта 1
        stats1 = self.db.get_project_statistics(self.project1_id)
        
        assert stats1['total_tasks'] == 4
        assert stats1['completed_tasks'] == 1
        assert stats1['in_progress_tasks'] == 1
        assert stats1['pending_tasks'] == 2  # pending + overdue
        assert stats1['overdue_tasks'] == 1
        
        # Получаем статистику для проекта 2
        stats2 = self.db.get_project_statistics(self.project2_id)
        
        assert stats2['total_tasks'] == 2
        assert stats2['completed_tasks'] == 1
        assert stats2['pending_tasks'] == 1
        assert stats2['overdue_tasks'] == 0
    
    def test_get_user_statistics(self):
        """Тест получения статистики по пользователю"""
        # Получаем статистику для пользователя 1
        stats1 = self.db.get_user_statistics(self.user1_id)
        
        assert stats1['total_tasks'] == 3  # 3 задачи у пользователя 1
        assert stats1['completed_tasks'] == 1
        assert stats1['in_progress_tasks'] == 1
        assert stats1['pending_tasks'] == 1
        assert stats1['overdue_tasks'] == 0
        
        # Получаем статистику для пользователя 2
        stats2 = self.db.get_user_statistics(self.user2_id)
        
        assert stats2['total_tasks'] == 3  # 3 задачи у пользователя 2
        assert stats2['completed_tasks'] == 1
        assert stats2['pending_tasks'] == 2  # pending + overdue
        assert stats2['overdue_tasks'] == 1
    
    def test_empty_statistics(self):
        """Тест статистики для несуществующих записей"""
        # Статистика для несуществующего проекта
        stats = self.db.get_project_statistics(999)
        assert stats == {}  # Должен вернуть пустой словарь
        
        # Статистика для несуществующего пользователя
        stats = self.db.get_user_statistics(999)
        assert stats == {}  # Должен вернуть пустой словарь


class TestDatabasePerformance:
    """Тесты производительности базы данных"""
    
    def test_bulk_insert_performance(self):
        """Тест производительности массовой вставки"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            db_path = temp_db.name
        
        try:
            db = DatabaseManager(db_path)
            
            # Создаем одного пользователя и один проект
            user = User("bulkuser", "bulk@example.com", "developer")
            user_id = db.add_user(user)
            
            project = Project(
                "Bulk Project",
                "Project for bulk operations",
                datetime.now() - timedelta(days=10),
                datetime.now() + timedelta(days=30)
            )
            project_id = db.add_project(project)
            
            # Массовая вставка задач
            start_time = datetime.now()
            
            for i in range(100):  # 100 задач
                task = Task(
                    title=f"Bulk Task {i}",
                    description=f"Description {i}",
                    priority=(i % 3) + 1,
                    due_date=datetime.now() + timedelta(days=i % 30),
                    project_id=project_id,
                    assignee_id=user_id
                )
                db.add_task(task)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Проверяем что все задачи созданы
            tasks = db.get_all_tasks()
            assert len(tasks) == 100
            
            # Проверяем что операция выполнилась за разумное время
            # (менее 10 секунд для 100 записей)
            assert duration < 10.0
            
            db.close()
            
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    def test_search_performance(self):
        """Тест производительности поиска"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            db_path = temp_db.name
        
        try:
            db = DatabaseManager(db_path)
            
            # Создаем тестовые данные
            user = User("searchperfuser", "searchperf@example.com", "developer")
            user_id = db.add_user(user)
            
            project = Project(
                "Search Perf Project",
                "Project for search performance",
                datetime.now() - timedelta(days=10),
                datetime.now() + timedelta(days=30)
            )
            project_id = db.add_project(project)
            
            # Создаем задачи с разными названиями
            for i in range(50):
                task = Task(
                    title=f"Task {i} with unique name",
                    description=f"Description for task {i}",
                    priority=(i % 3) + 1,
                    due_date=datetime.now() + timedelta(days=i % 30),
                    project_id=project_id,
                    assignee_id=user_id
                )
                db.add_task(task)
            
            # Тестируем производительность поиска
            start_time = datetime.now()
            
            # Выполняем несколько поисковых запросов
            for i in range(10):
                results = db.search_tasks(f"Task {i}")
                # Не проверяем количество результатов, только что запрос выполняется
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Проверяем что поиск выполнился за разумное время
            # (менее 5 секунд для 10 запросов)
            assert duration < 5.0
            
            db.close()
            
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)


if __name__ == "__main__":
    # Запуск тестов
    pytest.main([__file__, "-v"])