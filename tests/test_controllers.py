
import pytest
import tempfile
import os
from datetime import datetime, timedelta

from database.database_manager import DatabaseManager
from controllers.task_controller import TaskController
from controllers.project_controller import ProjectController
from controllers.user_controller import UserController


class TestTaskControllerIntegration:
    """Интеграционные тесты для TaskController"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db_manager = DatabaseManager(self.temp_db.name)
        self.task_controller = TaskController(self.db_manager)
        
        # Создаем тестовые данные
        self._create_test_data()
    
    def teardown_method(self):
        """Очистка после каждого теста"""
        self.db_manager.close()
        os.unlink(self.temp_db.name)
    
    def _create_test_data(self):
        """Создание тестовых данных"""
        # Создаем пользователя
        self.user = self._create_test_user("testuser", "test@example.com", "developer")
        
        # Создаем проект
        self.project = self._create_test_project(
            "Test Project", 
            "Test project description",
            datetime.now() - timedelta(days=10),
            datetime.now() + timedelta(days=30)
        )
    
    def _create_test_user(self, username, email, role):
        """Создание тестового пользователя"""
        # Используем напрямую DatabaseManager для создания пользователя
        from models.user import User
        user = User(username, email, role)
        user_id = self.db_manager.add_user(user)
        user.id = user_id
        return user
    
    def _create_test_project(self, name, description, start_date, end_date):
        """Создание тестового проекта"""
        from models.project import Project
        project = Project(name, description, start_date, end_date)
        project_id = self.db_manager.add_project(project)
        project.id = project_id
        return project
    
    def test_add_task_success(self):
        """Тест успешного добавления задачи"""
        due_date = datetime.now() + timedelta(days=7)
        
        task_id = self.task_controller.add_task(
            title="Test Task",
            description="Task description",
            priority=2,
            due_date=due_date,
            project_id=self.project.id,
            assignee_id=self.user.id
        )
        
        assert task_id > 0
        
        # Проверяем что задача добавлена
        task = self.task_controller.get_task(task_id)
        assert task is not None
        assert task.title == "Test Task"
        assert task.description == "Task description"
        assert task.priority == 2
        assert task.project_id == self.project.id
        assert task.assignee_id == self.user.id
    
    def test_add_task_invalid_project(self):
        """Тест добавления задачи с несуществующим проектом"""
        due_date = datetime.now() + timedelta(days=7)
        
        task_id = self.task_controller.add_task(
            title="Test Task",
            description="Task description",
            priority=2,
            due_date=due_date,
            project_id=999,  # Несуществующий проект
            assignee_id=self.user.id
        )
        
        assert task_id == -1  # Должен вернуть -1 при ошибке
    
    def test_add_task_invalid_user(self):
        """Тест добавления задачи с несуществующим пользователем"""
        due_date = datetime.now() + timedelta(days=7)
        
        task_id = self.task_controller.add_task(
            title="Test Task",
            description="Task description",
            priority=2,
            due_date=due_date,
            project_id=self.project.id,
            assignee_id=999  # Несуществующий пользователь
        )
        
        assert task_id == -1  # Должен вернуть -1 при ошибке
    
    def test_get_task(self):
        """Тест получения задачи по ID"""
        # Сначала добавляем задачу
        due_date = datetime.now() + timedelta(days=7)
        
        task_id = self.task_controller.add_task(
            title="Task to get",
            description="Description",
            priority=1,
            due_date=due_date,
            project_id=self.project.id,
            assignee_id=self.user.id
        )
        
        # Получаем задачу
        task = self.task_controller.get_task(task_id)
        assert task is not None
        assert task.id == task_id
        assert task.title == "Task to get"
    
    def test_get_task_not_found(self):
        """Тест получения несуществующей задачи"""
        task = self.task_controller.get_task(999)
        assert task is None
    
    def test_get_all_tasks(self):
        """Тест получения всех задач"""
        # Добавляем несколько задач
        due_date = datetime.now() + timedelta(days=7)
        
        for i in range(3):
            self.task_controller.add_task(
                title=f"Task {i}",
                description=f"Description {i}",
                priority=2,
                due_date=due_date,
                project_id=self.project.id,
                assignee_id=self.user.id
            )
        
        # Получаем все задачи
        tasks = self.task_controller.get_all_tasks()
        assert len(tasks) == 3
        assert all(task.title.startswith("Task") for task in tasks)
    
    def test_update_task_success(self):
        """Тест успешного обновления задачи"""
        # Сначала добавляем задачу
        due_date = datetime.now() + timedelta(days=7)
        
        task_id = self.task_controller.add_task(
            title="Old title",
            description="Old description",
            priority=1,
            due_date=due_date,
            project_id=self.project.id,
            assignee_id=self.user.id
        )
        
        # Обновляем задачу
        success = self.task_controller.update_task(
            task_id,
            title="New title",
            description="New description",
            priority=2
        )
        
        assert success is True
        
        # Проверяем обновленные данные
        task = self.task_controller.get_task(task_id)
        assert task.title == "New title"
        assert task.description == "New description"
        assert task.priority == 2
    
    def test_update_task_invalid_status(self):
        """Тест обновления задачи с неверным статусом"""
        due_date = datetime.now() + timedelta(days=7)
        
        task_id = self.task_controller.add_task(
            title="Test Task",
            description="Description",
            priority=1,
            due_date=due_date,
            project_id=self.project.id,
            assignee_id=self.user.id
        )
        
        # Пробуем обновить с неверным статусом
        success = self.task_controller.update_task(
            task_id,
            status="invalid_status"
        )
        
        assert success is False
    
    def test_update_task_invalid_project(self):
        """Тест обновления задачи с несуществующим проектом"""
        due_date = datetime.now() + timedelta(days=7)
        
        task_id = self.task_controller.add_task(
            title="Test Task",
            description="Description",
            priority=1,
            due_date=due_date,
            project_id=self.project.id,
            assignee_id=self.user.id
        )
        
        # Пробуем обновить с несуществующим проектом
        success = self.task_controller.update_task(
            task_id,
            project_id=999
        )
        
        assert success is False
    
    def test_delete_task_success(self):
        """Тест успешного удаления задачи"""
        # Сначала добавляем задачу
        due_date = datetime.now() + timedelta(days=7)
        
        task_id = self.task_controller.add_task(
            title="Task to delete",
            description="Description",
            priority=1,
            due_date=due_date,
            project_id=self.project.id,
            assignee_id=self.user.id
        )
        
        # Удаляем задачу
        success = self.task_controller.delete_task(task_id)
        assert success is True
        
        # Проверяем что задача удалена
        task = self.task_controller.get_task(task_id)
        assert task is None
    
    def test_delete_task_not_found(self):
        """Тест удаления несуществующей задачи"""
        success = self.task_controller.delete_task(999)
        assert success is False
    
    def test_search_tasks(self):
        """Тест поиска задач"""
        # Добавляем задачи с разными названиями
        due_date = datetime.now() + timedelta(days=7)
        
        self.task_controller.add_task(
            title="Важная задача",
            description="Срочно сделать",
            priority=1,
            due_date=due_date,
            project_id=self.project.id,
            assignee_id=self.user.id
        )
        
        self.task_controller.add_task(
            title="Обычная задача",
            description="Сделать когда будет время",
            priority=2,
            due_date=due_date,
            project_id=self.project.id,
            assignee_id=self.user.id
        )
        
        self.task_controller.add_task(
            title="Другая задача",
            description="Важная информация",
            priority=3,
            due_date=due_date,
            project_id=self.project.id,
            assignee_id=self.user.id
        )
        
        # Ищем по названию
        tasks = self.task_controller.search_tasks("Важная")
        assert len(tasks) == 2  # Одна по названию, одна по описанию
        
        # Ищем по описанию
        tasks = self.task_controller.search_tasks("срочно")
        assert len(tasks) == 1
        assert tasks[0].title == "Важная задача"
    
    def test_update_task_status(self):
        """Тест обновления статуса задачи"""
        due_date = datetime.now() + timedelta(days=7)
        
        task_id = self.task_controller.add_task(
            title="Task for status update",
            description="Description",
            priority=1,
            due_date=due_date,
            project_id=self.project.id,
            assignee_id=self.user.id
        )
        
        # Проверяем начальный статус
        task = self.task_controller.get_task(task_id)
        assert task.status == "pending"
        
        # Обновляем статус
        success = self.task_controller.update_task_status(task_id, "in_progress")
        assert success is True
        
        # Проверяем обновленный статус
        task = self.task_controller.get_task(task_id)
        assert task.status == "in_progress"
        
        # Обновляем еще раз
        success = self.task_controller.update_task_status(task_id, "completed")
        assert success is True
        
        task = self.task_controller.get_task(task_id)
        assert task.status == "completed"
    
    def test_get_overdue_tasks(self):
        """Тест получения просроченных задач"""
        # Добавляем задачи с разными сроками
        now = datetime.now()
        
        # Просроченная задача (срок в прошлом)
        overdue_due_date = now - timedelta(days=1)
        overdue_task_id = self.task_controller.add_task(
            title="Overdue task",
            description="Already overdue",
            priority=1,
            due_date=overdue_due_date,
            project_id=self.project.id,
            assignee_id=self.user.id
        )
        
        # Непросроченная задача (срок в будущем)
        future_due_date = now + timedelta(days=1)
        future_task_id = self.task_controller.add_task(
            title="Future task",
            description="Not overdue",
            priority=2,
            due_date=future_due_date,
            project_id=self.project.id,
            assignee_id=self.user.id
        )
        
        # Завершенная задача с просроченным сроком
        completed_overdue_id = self.task_controller.add_task(
            title="Completed overdue task",
            description="Completed but was overdue",
            priority=3,
            due_date=overdue_due_date,
            project_id=self.project.id,
            assignee_id=self.user.id
        )
        
        # Устанавливаем статус completed для последней задачи
        self.task_controller.update_task_status(completed_overdue_id, "completed")
        
        # Получаем просроченные задачи
        overdue_tasks = self.task_controller.get_overdue_tasks()
        
        # Должна быть только одна просроченная незавершенная задача
        assert len(overdue_tasks) == 1
        assert overdue_tasks[0].id == overdue_task_id
        assert overdue_tasks[0].is_overdue() is True
    
    def test_get_tasks_by_project(self):
        """Тест получения задач по проекту"""
        # Создаем второй проект
        start_date = datetime.now() - timedelta(days=5)
        end_date = start_date + timedelta(days=20)
        project2 = self._create_test_project("Project 2", "Second project", start_date, end_date)
        
        due_date = datetime.now() + timedelta(days=7)
        
        # Добавляем задачи в разные проекты
        self.task_controller.add_task(
            title="Task for project 1",
            description="Desc",
            priority=1,
            due_date=due_date,
            project_id=self.project.id,
            assignee_id=self.user.id
        )
        
        self.task_controller.add_task(
            title="Another task for project 1",
            description="Desc",
            priority=2,
            due_date=due_date,
            project_id=self.project.id,
            assignee_id=self.user.id
        )
        
        self.task_controller.add_task(
            title="Task for project 2",
            description="Desc",
            priority=3,
            due_date=due_date,
            project_id=project2.id,
            assignee_id=self.user.id
        )
        
        # Получаем задачи проекта 1
        tasks_project1 = self.task_controller.get_tasks_by_project(self.project.id)
        assert len(tasks_project1) == 2
        assert all(task.project_id == self.project.id for task in tasks_project1)
        
        # Получаем задачи проекта 2
        tasks_project2 = self.task_controller.get_tasks_by_project(project2.id)
        assert len(tasks_project2) == 1
        assert all(task.project_id == project2.id for task in tasks_project2)
    
    def test_get_tasks_by_user(self):
        """Тест получения задач по пользователю"""
        # Создаем второго пользователя
        user2 = self._create_test_user("user2", "user2@example.com", "developer")
        
        due_date = datetime.now() + timedelta(days=7)
        
        # Добавляем задачи для разных пользователей
        self.task_controller.add_task(
            title="Task for user 1",
            description="Desc",
            priority=1,
            due_date=due_date,
            project_id=self.project.id,
            assignee_id=self.user.id
        )
        
        self.task_controller.add_task(
            title="Another task for user 1",
            description="Desc",
            priority=2,
            due_date=due_date,
            project_id=self.project.id,
            assignee_id=self.user.id
        )
        
        self.task_controller.add_task(
            title="Task for user 2",
            description="Desc",
            priority=3,
            due_date=due_date,
            project_id=self.project.id,
            assignee_id=user2.id
        )
        
        # Получаем задачи пользователя 1
        tasks_user1 = self.task_controller.get_tasks_by_user(self.user.id)
        assert len(tasks_user1) == 2
        assert all(task.assignee_id == self.user.id for task in tasks_user1)
        
        # Получаем задачи пользователя 2
        tasks_user2 = self.task_controller.get_tasks_by_user(user2.id)
        assert len(tasks_user2) == 1
        assert all(task.assignee_id == user2.id for task in tasks_user2)
    
    def test_get_task_statistics(self):
        """Тест получения статистики задач"""
        due_date = datetime.now() + timedelta(days=7)
        overdue_date = datetime.now() - timedelta(days=1)
        
        # Добавляем задачи с разными статусами и приоритетами
        self.task_controller.add_task(
            title="High priority pending",
            description="Desc",
            priority=1,
            due_date=due_date,
            project_id=self.project.id,
            assignee_id=self.user.id
        )
        
        self.task_controller.add_task(
            title="Medium priority in progress",
            description="Desc",
            priority=2,
            due_date=due_date,
            project_id=self.project.id,
            assignee_id=self.user.id
        )
        self.task_controller.update_task_status(2, "in_progress")
        
        self.task_controller.add_task(
            title="Low priority completed",
            description="Desc",
            priority=3,
            due_date=due_date,
            project_id=self.project.id,
            assignee_id=self.user.id
        )
        self.task_controller.update_task_status(3, "completed")
        
        self.task_controller.add_task(
            title="Overdue high priority",
            description="Desc",
            priority=1,
            due_date=overdue_date,
            project_id=self.project.id,
            assignee_id=self.user.id
        )
        
        # Получаем статистику
        stats = self.task_controller.get_task_statistics()
        
        assert stats['total'] == 4
        assert stats['by_status']['pending'] == 2  # 1 задача + 1 просроченная
        assert stats['by_status']['in_progress'] == 1
        assert stats['by_status']['completed'] == 1
        assert stats['by_priority']['high'] == 2
        assert stats['by_priority']['medium'] == 1
        assert stats['by_priority']['low'] == 1
        assert stats['overdue'] == 1


class TestProjectControllerIntegration:
    """Интеграционные тесты для ProjectController"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db_manager = DatabaseManager(self.temp_db.name)
        self.project_controller = ProjectController(self.db_manager)
    
    def teardown_method(self):
        """Очистка после каждого теста"""
        self.db_manager.close()
        os.unlink(self.temp_db.name)
    
    def test_add_project_success(self):
        """Тест успешного добавления проекта"""
        start_date = datetime.now() - timedelta(days=10)
        end_date = start_date + timedelta(days=30)
        
        project_id = self.project_controller.add_project(
            name="Test Project",
            description="Test project description",
            start_date=start_date,
            end_date=end_date
        )
        
        assert project_id > 0
        
        # Проверяем что проект добавлен
        project = self.project_controller.get_project(project_id)
        assert project is not None
        assert project.name == "Test Project"
        assert project.description == "Test project description"
        assert project.start_date == start_date
        assert project.end_date == end_date
        assert project.status == "active"
    
    def test_add_project_invalid_dates(self):
        """Тест добавления проекта с неверными датами"""
        start_date = datetime.now() + timedelta(days=10)  # Будущая дата начала
        end_date = start_date + timedelta(days=30)
        
        project_id = self.project_controller.add_project(
            name="Invalid Project",
            description="Description",
            start_date=start_date,
            end_date=end_date
        )
        
        assert project_id == -1  # Должен вернуть -1 при ошибке
    
    def test_get_project(self):
        """Тест получения проекта"""
        # Сначала добавляем проект
        start_date = datetime.now() - timedelta(days=10)
        end_date = start_date + timedelta(days=30)
        
        project_id = self.project_controller.add_project(
            name="Project to get",
            description="Description",
            start_date=start_date,
            end_date=end_date
        )
        
        # Получаем проект
        project = self.project_controller.get_project(project_id)
        assert project is not None
        assert project.id == project_id
        assert project.name == "Project to get"
    
    def test_get_project_not_found(self):
        """Тест получения несуществующего проекта"""
        project = self.project_controller.get_project(999)
        assert project is None
    
    def test_get_all_projects(self):
        """Тест получения всех проектов"""
        # Добавляем несколько проектов
        start_date = datetime.now() - timedelta(days=10)
        
        for i in range(3):
            self.project_controller.add_project(
                name=f"Project {i}",
                description=f"Description {i}",
                start_date=start_date,
                end_date=start_date + timedelta(days=30)
            )
        
        # Получаем все проекты
        projects = self.project_controller.get_all_projects()
        assert len(projects) == 3
        assert all(project.name.startswith("Project") for project in projects)
    
    def test_update_project_success(self):
        """Тест успешного обновления проекта"""
        # Сначала добавляем проект
        start_date = datetime.now() - timedelta(days=10)
        end_date = start_date + timedelta(days=30)
        
        project_id = self.project_controller.add_project(
            name="Old name",
            description="Old description",
            start_date=start_date,
            end_date=end_date
        )
        
        # Обновляем проект
        success = self.project_controller.update_project(
            project_id,
            name="New name",
            description="New description",
            status="on_hold"
        )
        
        assert success is True
        
        # Проверяем обновленные данные
        project = self.project_controller.get_project(project_id)
        assert project.name == "New name"
        assert project.description == "New description"
        assert project.status == "on_hold"
    
    def test_update_project_invalid_status(self):
        """Тест обновления проекта с неверным статусом"""
        start_date = datetime.now() - timedelta(days=10)
        end_date = start_date + timedelta(days=30)
        
        project_id = self.project_controller.add_project(
            name="Test Project",
            description="Description",
            start_date=start_date,
            end_date=end_date
        )
        
        # Пробуем обновить с неверным статусом
        success = self.project_controller.update_project(
            project_id,
            status="invalid_status"
        )
        
        assert success is False
    
    def test_update_project_invalid_dates(self):
        """Тест обновления проекта с неверными датами"""
        start_date = datetime.now() - timedelta(days=10)
        end_date = start_date + timedelta(days=30)
        
        project_id = self.project_controller.add_project(
            name="Test Project",
            description="Description",
            start_date=start_date,
            end_date=end_date
        )
        
        # Пробуем обновить с датой окончания раньше даты начала
        success = self.project_controller.update_project(
            project_id,
            end_date=start_date - timedelta(days=1)  # Раньше даты начала
        )
        
        assert success is False
    
    def test_delete_project_success(self):
        """Тест успешного удаления проекта"""
        # Сначала добавляем проект
        start_date = datetime.now() - timedelta(days=10)
        end_date = start_date + timedelta(days=30)
        
        project_id = self.project_controller.add_project(
            name="Project to delete",
            description="Description",
            start_date=start_date,
            end_date=end_date
        )
        
        # Удаляем проект
        success = self.project_controller.delete_project(project_id)
        assert success is True
        
        # Проверяем что проект удален
        project = self.project_controller.get_project(project_id)
        assert project is None
    
    def test_delete_project_with_tasks(self):
        """Тест удаления проекта с задачами"""
        # Сначала добавляем проект
        start_date = datetime.now() - timedelta(days=10)
        end_date = start_date + timedelta(days=30)
        
        project_id = self.project_controller.add_project(
            name="Project with tasks",
            description="Description",
            start_date=start_date,
            end_date=end_date
        )
        
        # Создаем контроллер задач
        task_controller = TaskController(self.db_manager)
        
        # Создаем пользователя
        from models.user import User
        user = User("testuser", "test@example.com", "developer")
        user_id = self.db_manager.add_user(user)
        
        # Добавляем задачу в проект
        due_date = datetime.now() + timedelta(days=7)
        task_controller.add_task(
            title="Task in project",
            description="Description",
            priority=1,
            due_date=due_date,
            project_id=project_id,
            assignee_id=user_id
        )
        
        # Удаляем проект (должен удалить и задачу)
        success = self.project_controller.delete_project(project_id)
        assert success is True
        
        # Проверяем что проект удален
        project = self.project_controller.get_project(project_id)
        assert project is None
        
        # Проверяем что задачи больше нет в списке всех задач
        tasks = task_controller.get_all_tasks()
        assert len(tasks) == 0
    
    def test_delete_project_not_found(self):
        """Тест удаления несуществующего проекта"""
        success = self.project_controller.delete_project(999)
        assert success is False
    
    def test_update_project_status(self):
        """Тест обновления статуса проекта"""
        start_date = datetime.now() - timedelta(days=10)
        end_date = start_date + timedelta(days=30)
        
        project_id = self.project_controller.add_project(
            name="Project for status update",
            description="Description",
            start_date=start_date,
            end_date=end_date
        )
        
        # Проверяем начальный статус
        project = self.project_controller.get_project(project_id)
        assert project.status == "active"
        
        # Обновляем статус
        success = self.project_controller.update_project_status(project_id, "on_hold")
        assert success is True
        
        # Проверяем обновленный статус
        project = self.project_controller.get_project(project_id)
        assert project.status == "on_hold"
        
        # Обновляем еще раз
        success = self.project_controller.update_project_status(project_id, "completed")
        assert success is True
        
        project = self.project_controller.get_project(project_id)
        assert project.status == "completed"
    
    def test_get_project_progress_empty(self):
        """Тест получения прогресса пустого проекта"""
        start_date = datetime.now() - timedelta(days=10)
        end_date = start_date + timedelta(days=30)
        
        project_id = self.project_controller.add_project(
            name="Empty project",
            description="No tasks",
            start_date=start_date,
            end_date=end_date
        )
        
        progress = self.project_controller.get_project_progress(project_id)
        assert 0.0 <= progress <= 1.0
        
        # Примерно 10/30 = 0.333
        assert abs(progress - 0.333) < 0.1
    
    def test_get_active_projects(self):
        """Тест получения активных проектов"""
        start_date = datetime.now() - timedelta(days=10)
        
        # Добавляем проекты с разными статусами
        active_id = self.project_controller.add_project(
            name="Active Project",
            description="Description",
            start_date=start_date,
            end_date=start_date + timedelta(days=30)
        )
        
        on_hold_id = self.project_controller.add_project(
            name="On Hold Project",
            description="Description",
            start_date=start_date,
            end_date=start_date + timedelta(days=30)
        )
        self.project_controller.update_project_status(on_hold_id, "on_hold")
        
        completed_id = self.project_controller.add_project(
            name="Completed Project",
            description="Description",
            start_date=start_date,
            end_date=start_date + timedelta(days=30)
        )
        self.project_controller.update_project_status(completed_id, "completed")
        
        # Получаем только активные проекты
        active_projects = self.project_controller.get_active_projects()
        assert len(active_projects) == 1
        assert active_projects[0].name == "Active Project"
        assert active_projects[0].status == "active"
    
    def test_get_completed_projects(self):
        """Тест получения завершенных проектов"""
        start_date = datetime.now() - timedelta(days=10)
        
        # Добавляем проекты с разными статусами
        self.project_controller.add_project(
            name="Active Project",
            description="Description",
            start_date=start_date,
            end_date=start_date + timedelta(days=30)
        )
        
        completed_id = self.project_controller.add_project(
            name="Completed Project",
            description="Description",
            start_date=start_date,
            end_date=start_date + timedelta(days=30)
        )
        self.project_controller.update_project_status(completed_id, "completed")
        
        # Получаем только завершенные проекты
        completed_projects = self.project_controller.get_completed_projects()
        assert len(completed_projects) == 1
        assert completed_projects[0].name == "Completed Project"
        assert completed_projects[0].status == "completed"
    
    def test_get_project_statistics(self):
        """Тест получения статистики проекта"""
        start_date = datetime.now() - timedelta(days=10)
        end_date = start_date + timedelta(days=30)
        
        project_id = self.project_controller.add_project(
            name="Project for stats",
            description="Description",
            start_date=start_date,
            end_date=end_date
        )
        
        # Создаем контроллер задач
        task_controller = TaskController(self.db_manager)
        
        # Создаем пользователя
        from models.user import User
        user = User("testuser", "test@example.com", "developer")
        user_id = self.db_manager.add_user(user)
        
        # Добавляем задачи с разными статусами
        due_date = datetime.now() + timedelta(days=7)
        
        task_controller.add_task(
            title="Completed task",
            description="Description",
            priority=1,
            due_date=due_date,
            project_id=project_id,
            assignee_id=user_id
        )
        task_controller.update_task_status(1, "completed")
        
        task_controller.add_task(
            title="In progress task",
            description="Description",
            priority=2,
            due_date=due_date,
            project_id=project_id,
            assignee_id=user_id
        )
        task_controller.update_task_status(2, "in_progress")
        
        task_controller.add_task(
            title="Pending task",
            description="Description",
            priority=3,
            due_date=due_date,
            project_id=project_id,
            assignee_id=user_id
        )
        
        # Добавляем просроченную задачу
        overdue_date = datetime.now() - timedelta(days=1)
        task_controller.add_task(
            title="Overdue task",
            description="Description",
            priority=1,
            due_date=overdue_date,
            project_id=project_id,
            assignee_id=user_id
        )
        
        # Получаем статистику
        stats = self.project_controller.get_project_statistics(project_id)
        
        assert stats['project_name'] == "Project for stats"
        assert stats['status'] == "active"
        assert stats['total_tasks'] == 4
        assert stats['completed_tasks'] == 1
        assert stats['in_progress_tasks'] == 1
        assert stats['pending_tasks'] == 2  # pending + overdue
        assert stats['overdue_tasks'] == 1
        assert 'progress' in stats
        assert 'is_overdue' in stats


class TestUserControllerIntegration:
    """Интеграционные тесты для UserController"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db_manager = DatabaseManager(self.temp_db.name)
        self.user_controller = UserController(self.db_manager)
    
    def teardown_method(self):
        """Очистка после каждого теста"""
        self.db_manager.close()
        os.unlink(self.temp_db.name)
    
    def test_add_user_success(self):
        """Тест успешного добавления пользователя"""
        user_id = self.user_controller.add_user(
            username="testuser",
            email="test@example.com",
            role="developer"
        )
        
        assert user_id > 0
        
        # Проверяем что пользователь добавлен
        user = self.user_controller.get_user(user_id)
        assert user is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.role == "developer"
        assert isinstance(user.registration_date, datetime)
    
    def test_add_user_duplicate_username(self):
        """Тест добавления пользователя с существующим именем"""
        # Сначала добавляем пользователя
        self.user_controller.add_user(
            username="existinguser",
            email="existing@example.com",
            role="developer"
        )
        
        # Пробуем добавить с тем же именем
        user_id = self.user_controller.add_user(
            username="existinguser",  # Дубликат
            email="new@example.com",
            role="developer"
        )
        
        assert user_id == -1  # Должен вернуть -1 при ошибке
    
    def test_add_user_duplicate_email(self):
        """Тест добавления пользователя с существующим email"""
        # Сначала добавляем пользователя
        self.user_controller.add_user(
            username="user1",
            email="test@example.com",
            role="developer"
        )
        
        # Пробуем добавить с тем же email
        user_id = self.user_controller.add_user(
            username="user2",
            email="test@example.com",  # Дубликат
            role="developer"
        )
        
        assert user_id == -1  # Должен вернуть -1 при ошибке
    
    def test_add_user_invalid_role(self):
        """Тест добавления пользователя с неверной ролью"""
        user_id = self.user_controller.add_user(
            username="testuser",
            email="test@example.com",
            role="invalid_role"  # Неверная роль
        )
        
        assert user_id == -1  # Должен вернуть -1 при ошибке
    
    def test_get_user(self):
        """Тест получения пользователя"""
        # Сначала добавляем пользователя
        user_id = self.user_controller.add_user(
            username="user_to_get",
            email="get@example.com",
            role="developer"
        )
        
        # Получаем пользователя
        user = self.user_controller.get_user(user_id)
        assert user is not None
        assert user.id == user_id
        assert user.username == "user_to_get"
    
    def test_get_user_not_found(self):
        """Тест получения несуществующего пользователя"""
        user = self.user_controller.get_user(999)
        assert user is None
    
    def test_get_all_users(self):
        """Тест получения всех пользователей"""
        # Добавляем нескольких пользователей
        self.user_controller.add_user("user1", "user1@example.com", "developer")
        self.user_controller.add_user("user2", "user2@example.com", "manager")
        self.user_controller.add_user("user3", "user3@example.com", "admin")
        
        # Получаем всех пользователей
        users = self.user_controller.get_all_users()
        assert len(users) == 3
        assert all(isinstance(user, ) for user in users)
        
        # Проверяем порядок (должен быть отсортирован по username)
        usernames = [user.username for user in users]
        assert usernames == ["user1", "user2", "user3"]
    
    def test_update_user_success(self):
        """Тест успешного обновления пользователя"""
        # Сначала добавляем пользователя
        user_id = self.user_controller.add_user(
            username="olduser",
            email="old@example.com",
            role="developer"
        )
        
        # Обновляем пользователя
        success = self.user_controller.update_user(
            user_id,
            username="newuser",
            email="new@example.com",
            role="manager"
        )
        
        assert success is True
        
        # Проверяем обновленные данные
        user = self.user_controller.get_user(user_id)
        assert user.username == "newuser"
        assert user.email == "new@example.com"
        assert user.role == "manager"
    
    def test_update_user_duplicate_username(self):
        """Тест обновления пользователя с существующим именем"""
        # Сначала добавляем двух пользователей
        self.user_controller.add_user("user1", "user1@example.com", "developer")
        user2_id = self.user_controller.add_user("user2", "user2@example.com", "developer")
        
        # Пробуем переименовать user2 в user1
        success = self.user_controller.update_user(
            user2_id,
            username="user1"  # Дубликат
        )
        
        assert success is False  # Должен вернуть False при ошибке
    
    def test_update_user_duplicate_email(self):
        """Тест обновления пользователя с существующим email"""
        # Сначала добавляем двух пользователей
        self.user_controller.add_user("user1", "user1@example.com", "developer")
        user2_id = self.user_controller.add_user("user2", "user2@example.com", "developer")
        
        # Пробуем изменить email user2 на email user1
        success = self.user_controller.update_user(
            user2_id,
            email="user1@example.com"  # Дубликат
        )
        
        assert success is False  # Должен вернуть False при ошибке
    
    def test_delete_user_success(self):
        """Тест успешного удаления пользователя"""
        # Сначала добавляем пользователя
        user_id = self.user_controller.add_user(
            username="user_to_delete",
            email="delete@example.com",
            role="developer"
        )
        
        # Удаляем пользователя
        success = self.user_controller.delete_user(user_id)
        assert success is True
        
        # Проверяем что пользователь удален
        user = self.user_controller.get_user(user_id)
        assert user is None
    
    def test_delete_user_with_tasks(self):
        """Тест удаления пользователя с задачами"""
        # Создаем пользователя
        user_id = self.user_controller.add_user(
            username="user_with_tasks",
            email="tasks@example.com",
            role="developer"
        )
        
        # Создаем контроллер проектов
        project_controller = ProjectController(self.db_manager)
        
        # Создаем проект
        start_date = datetime.now() - timedelta(days=10)
        end_date = start_date + timedelta(days=30)
        project_id = project_controller.add_project(
            "Test Project",
            "Description",
            start_date,
            end_date
        )
        
        # Создаем контроллер задач
        task_controller = TaskController(self.db_manager)
        
        # Добавляем задачу для пользователя
        due_date = datetime.now() + timedelta(days=7)
        task_controller.add_task(
            title="User's task",
            description="Description",
            priority=1,
            due_date=due_date,
            project_id=project_id,
            assignee_id=user_id
        )
        
        # Пробуем удалить пользователя (должно не получиться)
        success = self.user_controller.delete_user(user_id)
        assert success is False  # Нельзя удалить пользователя с задачами
        
        # Пользователь должен остаться в системе
        user = self.user_controller.get_user(user_id)
        assert user is not None
    
    def test_get_user_tasks(self):
        """Тест получения задач пользователя"""
        # Создаем пользователя
        user_id = self.user_controller.add_user(
            username="taskuser",
            email="taskuser@example.com",
            role="developer"
        )
        
        # Создаем контроллер проектов
        project_controller = ProjectController(self.db_manager)
        
        # Создаем проект
        start_date = datetime.now() - timedelta(days=10)
        end_date = start_date + timedelta(days=30)
        project_id = project_controller.add_project(
            "Test Project",
            "Description",
            start_date,
            end_date
        )
        
        # Создаем контроллер задач
        task_controller = TaskController(self.db_manager)
        
        # Добавляем задачи для пользователя
        due_date = datetime.now() + timedelta(days=7)
        
        task_controller.add_task(
            title="Task 1",
            description="Description",
            priority=1,
            due_date=due_date,
            project_id=project_id,
            assignee_id=user_id
        )
        
        task_controller.add_task(
            title="Task 2",
            description="Description",
            priority=2,
            due_date=due_date,
            project_id=project_id,
            assignee_id=user_id
        )
        
        # Получаем задачи пользователя
        tasks = self.user_controller.get_user_tasks(user_id)
        assert len(tasks) == 2
        assert all(task.assignee_id == user_id for task in tasks)
    
    def test_get_user_tasks_empty(self):
        """Тест получения задач пользователя без задач"""
        user_id = self.user_controller.add_user(
            username="emptytaskuser",
            email="empty@example.com",
            role="developer"
        )
        
        tasks = self.user_controller.get_user_tasks(user_id)
        assert len(tasks) == 0
    
    def test_get_users_by_role(self):
        """Тест получения пользователей по роли"""
        # Добавляем пользователей с разными ролями
        self.user_controller.add_user("dev1", "dev1@example.com", "developer")
        self.user_controller.add_user("dev2", "dev2@example.com", "developer")
        self.user_controller.add_user("manager1", "manager1@example.com", "manager")
        self.user_controller.add_user("admin1", "admin1@example.com", "admin")
        
        # Получаем разработчиков
        developers = self.user_controller.get_users_by_role("developer")
        assert len(developers) == 2
        assert all(user.role == "developer" for user in developers)
        
        # Получаем менеджеров
        managers = self.user_controller.get_users_by_role("manager")
        assert len(managers) == 1
        assert all(user.role == "manager" for user in managers)
        
        # Получаем администраторов
        admins = self.user_controller.get_users_by_role("admin")
        assert len(admins) == 1
        assert all(user.role == "admin" for user in admins)
    
    def test_get_user_statistics(self):
        """Тест получения статистики пользователя"""
        # Создаем пользователя
        user_id = self.user_controller.add_user(
            username="statsuser",
            email="stats@example.com",
            role="developer"
        )
        
        # Создаем контроллер проектов
        project_controller = ProjectController(self.db_manager)
        
        # Создаем проект
        start_date = datetime.now() - timedelta(days=10)
        end_date = start_date + timedelta(days=30)
        project_id = project_controller.add_project(
            "Test Project",
            "Description",
            start_date,
            end_date
        )
        
        # Создаем контроллер задач
        task_controller = TaskController(self.db_manager)
        
        # Добавляем задачи с разными статусами
        due_date = datetime.now() + timedelta(days=7)
        
        task_controller.add_task(
            title="Completed task",
            description="Description",
            priority=1,
            due_date=due_date,
            project_id=project_id,
            assignee_id=user_id
        )
        task_controller.update_task_status(1, "completed")
        
        task_controller.add_task(
            title="In progress task",
            description="Description",
            priority=2,
            due_date=due_date,
            project_id=project_id,
            assignee_id=user_id
        )
        task_controller.update_task_status(2, "in_progress")
        
        task_controller.add_task(
            title="Pending task",
            description="Description",
            priority=3,
            due_date=due_date,
            project_id=project_id,
            assignee_id=user_id
        )
        
        # Добавляем просроченную задачу
        overdue_date = datetime.now() - timedelta(days=1)
        task_controller.add_task(
            title="Overdue task",
            description="Description",
            priority=1,
            due_date=overdue_date,
            project_id=project_id,
            assignee_id=user_id
        )
        
        # Получаем статистику
        stats = self.user_controller.get_user_statistics(user_id)
        
        assert stats['username'] == "statsuser"
        assert stats['role'] == "developer"
        assert stats['total_tasks'] == 4
        assert stats['completed_tasks'] == 1
        assert stats['in_progress_tasks'] == 1
        assert stats['pending_tasks'] == 2  # pending + overdue
        assert stats['overdue_tasks'] == 1
        assert 'registration_date' in stats
        assert 'days_since_registration' in stats
    
    def test_reassign_user_tasks(self):
        """Тест переназначения задач пользователя"""
        # Создаем двух пользователей
        user1_id = self.user_controller.add_user("user1", "user1@example.com", "developer")
        user2_id = self.user_controller.add_user("user2", "user2@example.com", "developer")
        
        # Создаем контроллер проектов
        project_controller = ProjectController(self.db_manager)
        
        # Создаем проект
        start_date = datetime.now() - timedelta(days=10)
        end_date = start_date + timedelta(days=30)
        project_id = project_controller.add_project(
            "Test Project",
            "Description",
            start_date,
            end_date
        )
        
        # Создаем контроллер задач
        task_controller = TaskController(self.db_manager)
        
        # Добавляем задачи для первого пользователя
        due_date = datetime.now() + timedelta(days=7)
        
        for i in range(3):
            task_controller.add_task(
                title=f"Task {i}",
                description="Description",
                priority=1,
                due_date=due_date,
                project_id=project_id,
                assignee_id=user1_id
            )
        
        # Проверяем что у user1 есть задачи
        tasks_user1 = self.user_controller.get_user_tasks(user1_id)
        assert len(tasks_user1) == 3
        
        # Проверяем что у user2 нет задач
        tasks_user2 = self.user_controller.get_user_tasks(user2_id)
        assert len(tasks_user2) == 0
        
        # Переназначаем задачи от user1 к user2
        success = self.user_controller.reassign_user_tasks(user1_id, user2_id)
        assert success is True
        
        # Проверяем что у user1 теперь нет задач
        tasks_user1_after = self.user_controller.get_user_tasks(user1_id)
        assert len(tasks_user1_after) == 0
        
        # Проверяем что у user2 теперь есть задачи
        tasks_user2_after = self.user_controller.get_user_tasks(user2_id)
        assert len(tasks_user2_after) == 3


class TestControllersEdgeCases:
    """Тесты граничных случаев для контроллеров"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db_manager = DatabaseManager(self.temp_db.name)
        self.task_controller = TaskController(self.db_manager)
        self.project_controller = ProjectController(self.db_manager)
        self.user_controller = UserController(self.db_manager)
    
    def teardown_method(self):
        """Очистка после каждого теста"""
        self.db_manager.close()
        os.unlink(self.temp_db.name)
    
    def test_empty_database_operations(self):
        """Тест операций с пустой базой данных"""
        # Проверяем что можно получить пустые списки
        tasks = self.task_controller.get_all_tasks()
        assert tasks == []
        
        projects = self.project_controller.get_all_projects()
        assert projects == []
        
        users = self.user_controller.get_all_users()
        assert users == []
        
        # Проверяем поиск в пустой базе
        search_results = self.task_controller.search_tasks("something")
        assert search_results == []
        
        # Проверяем получение несуществующих элементов
        assert self.task_controller.get_task(1) is None
        assert self.project_controller.get_project(1) is None
        assert self.user_controller.get_user(1) is None
    
    def test_task_priority_boundaries(self):
        """Тест граничных значений приоритета задачи"""
        # Создаем пользователя и проект
        user_id = self.user_controller.add_user("testuser", "test@example.com", "developer")
        project_id = self.project_controller.add_project(
            "Test Project",
            "Description",
            datetime.now() - timedelta(days=10),
            datetime.now() + timedelta(days=30)
        )
        
        due_date = datetime.now() + timedelta(days=7)
        
        # Проверяем минимальное значение приоритета
        task_id1 = self.task_controller.add_task(
            title="Task 1",
            description="Description",
            priority=1,  # Минимальное значение
            due_date=due_date,
            project_id=project_id,
            assignee_id=user_id
        )
        assert task_id1 > 0
        
        # Проверяем максимальное значение приоритета
        task_id2 = self.task_controller.add_task(
            title="Task 2",
            description="Description",
            priority=3,  # Максимальное значение
            due_date=due_date,
            project_id=project_id,
            assignee_id=user_id
        )
        assert task_id2 > 0
        
        # Проверяем недопустимое значение приоритета
        task_id3 = self.task_controller.add_task(
            title="Task 3",
            description="Description",
            priority=0,  # Недопустимое значение
            due_date=due_date,
            project_id=project_id,
            assignee_id=user_id
        )
        assert task_id3 == -1  # Должен вернуть -1 при ошибке
    
    def test_task_status_boundaries(self):
        """Тест граничных значений статуса задачи"""
        # Создаем пользователя и проект
        user_id = self.user_controller.add_user("testuser", "test@example.com", "developer")
        project_id = self.project_controller.add_project(
            "Test Project",
            "Description",
            datetime.now() - timedelta(days=10),
            datetime.now() + timedelta(days=30)
        )
        
        due_date = datetime.now() + timedelta(days=7)
        
        # Создаем задачу
        task_id = self.task_controller.add_task(
            title="Test Task",
            description="Description",
            priority=2,
            due_date=due_date,
            project_id=project_id,
            assignee_id=user_id
        )
        
        # Проверяем все допустимые статусы
        valid_statuses = ["pending", "in_progress", "completed"]
        for status in valid_statuses:
            success = self.task_controller.update_task_status(task_id, status)
            assert success is True
            
            # Проверяем что статус установлен
            task = self.task_controller.get_task(task_id)
            assert task.status == status
        
        # Проверяем недопустимый статус
        success = self.task_controller.update_task_status(task_id, "invalid_status")
        assert success is False
    
    def test_project_status_boundaries(self):
        """Тест граничных значений статуса проекта"""
        # Создаем проект
        project_id = self.project_controller.add_project(
            "Test Project",
            "Description",
            datetime.now() - timedelta(days=10),
            datetime.now() + timedelta(days=30)
        )
        
        # Проверяем все допустимые статусы
        valid_statuses = ["active", "completed", "on_hold"]
        for status in valid_statuses:
            success = self.project_controller.update_project_status(project_id, status)
            assert success is True
            
            # Проверяем что статус установлен
            project = self.project_controller.get_project(project_id)
            assert project.status == status
        
        # Проверяем недопустимый статус
        success = self.project_controller.update_project_status(project_id, "invalid_status")
        assert success is False
    
    def test_user_role_boundaries(self):
        """Тест граничных значений роли пользователя"""
        # Проверяем все допустимые роли
        valid_roles = ["admin", "manager", "developer"]
        for role in valid_roles:
            user_id = self.user_controller.add_user(
                username=f"user_{role}",
                email=f"{role}@example.com",
                role=role
            )
            assert user_id > 0
            
            # Проверяем что роль установлена
            user = self.user_controller.get_user(user_id)
            assert user.role == role
        
        # Проверяем недопустимую роль
        user_id = self.user_controller.add_user(
            username="invalid_user",
            email="invalid@example.com",
            role="invalid_role"
        )
        assert user_id == -1  # Должен вернуть -1 при ошибке
    
    def test_concurrent_operations(self):
        """Тест конкурентных операций (последовательных)"""
        # Создаем несколько пользователей
        user_ids = []
        for i in range(5):
            user_id = self.user_controller.add_user(
                username=f"user{i}",
                email=f"user{i}@example.com",
                role="developer"
            )
            assert user_id > 0
            user_ids.append(user_id)
        
        # Создаем несколько проектов
        project_ids = []
        for i in range(3):
            project_id = self.project_controller.add_project(
                name=f"Project {i}",
                description=f"Description {i}",
                start_date=datetime.now() - timedelta(days=10),
                end_date=datetime.now() + timedelta(days=30)
            )
            assert project_id > 0
            project_ids.append(project_id)
        
        # Создаем несколько задач для разных пользователей и проектов
        task_ids = []
        for i in range(10):
            user_idx = i % len(user_ids)
            project_idx = i % len(project_ids)
            
            task_id = self.task_controller.add_task(
                title=f"Task {i}",
                description=f"Description {i}",
                priority=(i % 3) + 1,
                due_date=datetime.now() + timedelta(days=(i % 10) + 1),
                project_id=project_ids[project_idx],
                assignee_id=user_ids[user_idx]
            )
            assert task_id > 0
            task_ids.append(task_id)
        
        # Проверяем что все создалось правильно
        users = self.user_controller.get_all_users()
        assert len(users) == 5
        
        projects = self.project_controller.get_all_projects()
        assert len(projects) == 3
        
        tasks = self.task_controller.get_all_tasks()
        assert len(tasks) == 10
        
        # Обновляем несколько задач
        for i, task_id in enumerate(task_ids):
            if i % 2 == 0:  # Обновляем каждую вторую задачу
                success = self.task_controller.update_task_status(task_id, "in_progress")
                assert success is True
        
        # Удаляем несколько задач
        deleted_count = 0
        for i, task_id in enumerate(task_ids):
            if i % 3 == 0:  # Удаляем каждую третью задачу
                success = self.task_controller.delete_task(task_id)
                if success:
                    deleted_count += 1
        
        # Проверяем что задачи удалены
        tasks_after = self.task_controller.get_all_tasks()
        assert len(tasks_after) == 10 - deleted_count


if __name__ == "__main__":
    # Запуск тестов
    pytest.main([__file__, "-v"])