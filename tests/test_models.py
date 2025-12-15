import pytest
import tempfile
import os
from datetime import datetime, timedelta

from models.task import Task
from models.project import Project
from models.user import User
from database.database_manager import DatabaseManager


class TestTaskModel:
    """Тесты для модели Task"""
    
    def test_task_creation(self):
        """Тест создания задачи с валидными данными"""
        due_date = datetime.now() + timedelta(days=7)
        
        task = Task(
            title="Тестовая задача",
            description="Описание тестовой задачи",
            priority=2,
            due_date=due_date,
            project_id=1,
            assignee_id=100
        )
        
        assert task.title == "Тестовая задача"
        assert task.description == "Описание тестовой задачи"
        assert task.priority == 2
        assert task.status == "pending"
        assert task.due_date == due_date
        assert task.project_id == 1
        assert task.assignee_id == 100
        assert task.id is None  # ID устанавливается при сохранении в БД
    
    def test_task_creation_invalid_priority(self):
        """Тест создания задачи с невалидным приоритетом"""
        due_date = datetime.now() + timedelta(days=7)
        
        with pytest.raises(ValueError, match="Приоритет должен быть 1, 2 или 3"):
            Task(
                title="Задача с неверным приоритетом",
                description="Описание",
                priority=5,  # Неверный приоритет
                due_date=due_date,
                project_id=1,
                assignee_id=100
            )
    
    def test_task_creation_empty_title(self):
        """Тест создания задачи с пустым названием"""
        due_date = datetime.now() + timedelta(days=7)
        
        with pytest.raises(ValueError, match="Название задачи не может быть пустым"):
            Task(
                title="",  # Пустое название
                description="Описание",
                priority=1,
                due_date=due_date,
                project_id=1,
                assignee_id=100
            )
    
    def test_task_creation_empty_description(self):
        """Тест создания задачи с пустым описанием"""
        due_date = datetime.now() + timedelta(days=7)
        
        with pytest.raises(ValueError, match="Описание задачи не может быть пустым"):
            Task(
                title="Задача",
                description="",  # Пустое описание
                priority=1,
                due_date=due_date,
                project_id=1,
                assignee_id=100
            )
    
    def test_task_creation_past_due_date(self):
        """Тест создания задачи с датой в прошлом"""
        past_date = datetime.now() - timedelta(days=1)
        
        with pytest.raises(ValueError, match="Срок выполнения не может быть в прошлом"):
            Task(
                title="Задача",
                description="Описание",
                priority=1,
                due_date=past_date,  # Дата в прошлом
                project_id=1,
                assignee_id=100
            )
    
    def test_task_update_status_valid(self):
        """Тест обновления статуса с валидными значениями"""
        due_date = datetime.now() + timedelta(days=7)
        task = Task("Тест", "Описание", 1, due_date, 1, 100)
        
        # Проверяем начальный статус
        assert task.status == "pending"
        
        # Обновляем статус
        result = task.update_status("in_progress")
        assert result is True
        assert task.status == "in_progress"
        
        # Еще одно обновление
        result = task.update_status("completed")
        assert result is True
        assert task.status == "completed"
    
    def test_task_update_status_invalid(self):
        """Тест обновления статуса с невалидным значением"""
        due_date = datetime.now() + timedelta(days=7)
        task = Task("Тест", "Описание", 1, due_date, 1, 100)
        
        # Пробуем установить неверный статус
        result = task.update_status("invalid_status")
        assert result is False
        assert task.status == "pending"  # Статус не должен измениться
    
    def test_task_update_status_same(self):
        """Тест обновления статуса на тот же самый"""
        due_date = datetime.now() + timedelta(days=7)
        task = Task("Тест", "Описание", 1, due_date, 1, 100)
        
        # Пробуем установить тот же статус
        result = task.update_status("pending")
        assert result is False
        assert task.status == "pending"
    
    def test_task_is_overdue_future(self):
        """Тест проверки просрочки для задачи в будущем"""
        future_date = datetime.now() + timedelta(days=1)
        task = Task("Тест", "Описание", 1, future_date, 1, 100)
        
        assert task.is_overdue() is False
    
    def test_task_is_overdue_past(self):
        """Тест проверки просрочки для задачи в прошлом"""
        # Создаем задачу с просроченным сроком
        past_date = datetime.now() - timedelta(days=1)
        
        # Используем обходной путь для создания задачи с прошлой датой
        task = Task.__new__(Task)
        task.id = None
        task.title = "Просроченная задача"
        task.description = "Описание"
        task.priority = 1
        task.status = "pending"
        task.due_date = past_date
        task.project_id = 1
        task.assignee_id = 100
        
        assert task.is_overdue() is True
    
    def test_task_is_overdue_completed(self):
        """Тест: завершенная задача не считается просроченной"""
        # Создаем завершенную задачу с просроченным сроком
        past_date = datetime.now() - timedelta(days=1)
        
        task = Task.__new__(Task)
        task.id = None
        task.title = "Завершенная просроченная задача"
        task.description = "Описание"
        task.priority = 1
        task.status = "completed"
        task.due_date = past_date
        task.project_id = 1
        task.assignee_id = 100
        
        assert task.is_overdue() is False
    
    def test_task_to_dict(self):
        """Тест преобразования задачи в словарь"""
        due_date = datetime.now() + timedelta(days=7)
        task = Task("Тест", "Описание", 2, due_date, 1, 100)
        task.id = 42  # Устанавливаем ID для теста
        
        result = task.to_dict()
        
        assert isinstance(result, dict)
        assert result['id'] == 42
        assert result['title'] == "Тест"
        assert result['description'] == "Описание"
        assert result['priority'] == 2
        assert result['status'] == "pending"
        assert result['due_date'] == due_date
        assert result['project_id'] == 1
        assert result['assignee_id'] == 100
        assert 'is_overdue' in result
        assert isinstance(result['is_overdue'], bool)
    
    def test_task_str_representation(self):
        """Тест строкового представления задачи"""
        due_date = datetime(2024, 12, 31, 23, 59)
        task = Task("Важная задача", "Очень важная", 1, due_date, 1, 100)
        task.id = 1
        
        str_repr = str(task)
        
        assert "Задача #1: Важная задача" in str_repr
        assert "Приоритет: Высокий (1)" in str_repr
        assert "Статус: pending" in str_repr
        assert "Срок: 31.12.2024 23:59" in str_repr
    
    def test_task_repr_representation(self):
        """Тест представления для отладки"""
        task = Task("Тест", "Описание", 1, datetime.now(), 1, 100)
        task.id = 5
        
        repr_str = repr(task)
        assert "Task(id=5" in repr_str
        assert "title='Тест'" in repr_str


class TestProjectModel:
    """Тесты для модели Project"""
    
    def test_project_creation(self):
        """Тест создания проекта с валидными данными"""
        start_date = datetime.now() - timedelta(days=10)
        end_date = start_date + timedelta(days=30)
        
        project = Project(
            name="Тестовый проект",
            description="Описание тестового проекта",
            start_date=start_date,
            end_date=end_date
        )
        
        assert project.name == "Тестовый проект"
        assert project.description == "Описание тестового проекта"
        assert project.start_date == start_date
        assert project.end_date == end_date
        assert project.status == "active"
        assert project.id is None  # ID устанавливается при сохранении в БД
    
    def test_project_creation_invalid_dates(self):
        """Тест создания проекта с датой окончания раньше начала"""
        start_date = datetime.now()
        end_date = start_date - timedelta(days=1)  # end_date раньше start_date
        
        with pytest.raises(ValueError, match="Дата окончания должна быть позже даты начала"):
            Project(
                name="Проект с неверными датами",
                description="Описание",
                start_date=start_date,
                end_date=end_date
            )
    
    def test_project_creation_future_start_date(self):
        """Тест создания проекта с датой начала в будущем"""
        start_date = datetime.now() + timedelta(days=10)
        end_date = start_date + timedelta(days=30)
        
        with pytest.raises(ValueError, match="Дата начала не может быть в будущем"):
            Project(
                name="Проект с будущей датой",
                description="Описание",
                start_date=start_date,
                end_date=end_date
            )
    
    def test_project_creation_empty_name(self):
        """Тест создания проекта с пустым названием"""
        start_date = datetime.now() - timedelta(days=10)
        end_date = start_date + timedelta(days=30)
        
        with pytest.raises(ValueError, match="Название проекта не может быть пустым"):
            Project(
                name="",  # Пустое название
                description="Описание",
                start_date=start_date,
                end_date=end_date
            )
    
    def test_project_creation_empty_description(self):
        """Тест создания проекта с пустым описанием"""
        start_date = datetime.now() - timedelta(days=10)
        end_date = start_date + timedelta(days=30)
        
        with pytest.raises(ValueError, match="Описание проекта не может быть пустым"):
            Project(
                name="Проект",
                description="",  # Пустое описание
                start_date=start_date,
                end_date=end_date
            )
    
    def test_project_update_status_valid(self):
        """Тест обновления статуса с валидными значениями"""
        start_date = datetime.now() - timedelta(days=10)
        end_date = start_date + timedelta(days=30)
        project = Project("Тест", "Описание", start_date, end_date)
        
        # Проверяем начальный статус
        assert project.status == "active"
        
        # Обновляем статус
        result = project.update_status("on_hold")
        assert result is True
        assert project.status == "on_hold"
        
        # Еще одно обновление
        result = project.update_status("completed")
        assert result is True
        assert project.status == "completed"
    
    def test_project_update_status_invalid(self):
        """Тест обновления статуса с невалидным значением"""
        start_date = datetime.now() - timedelta(days=10)
        end_date = start_date + timedelta(days=30)
        project = Project("Тест", "Описание", start_date, end_date)
        
        # Пробуем установить неверный статус
        result = project.update_status("invalid_status")
        assert result is False
        assert project.status == "active"  # Статус не должен измениться
    
    def test_project_get_progress_time_based(self):
        """Тест расчета прогресса на основе времени"""
        start_date = datetime.now() - timedelta(days=10)
        end_date = start_date + timedelta(days=30)  # Всего 30 дней
        
        project = Project("Тест", "Описание", start_date, end_date)
        
        # Прошло 10 из 30 дней = ~33.3%
        progress = project.get_progress()
        assert 0.0 <= progress <= 1.0
        # Допускаем небольшую погрешность из-за времени выполнения теста
        assert abs(progress - 0.333) < 0.1
    
    def test_project_get_progress_completed(self):
        """Тест прогресса завершенного проекта"""
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now() - timedelta(days=10)
        
        project = Project("Завершенный проект", "Описание", start_date, end_date)
        project.update_status("completed")
        
        # Завершенный проект всегда имеет прогресс 1.0
        progress = project.get_progress()
        assert progress == 1.0
    
    def test_project_get_progress_on_hold(self):
        """Тест прогресса приостановленного проекта"""
        start_date = datetime.now() - timedelta(days=10)
        end_date = start_date + timedelta(days=30)
        
        project = Project("Приостановленный проект", "Описание", start_date, end_date)
        project.update_status("on_hold")
        
        # Приостановленный проект также рассчитывает прогресс по времени
        progress = project.get_progress()
        assert 0.0 <= progress <= 1.0
    
    def test_project_is_overdue(self):
        """Тест проверки просрочки проекта"""
        # Активный проект с будущим сроком - не просрочен
        start_date = datetime.now() - timedelta(days=10)
        end_date = datetime.now() + timedelta(days=20)
        
        project = Project("Будущий проект", "Описание", start_date, end_date)
        assert project.is_overdue() is False
        
        # Проект с прошедшим сроком - просрочен
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now() - timedelta(days=1)
        
        # Чтобы создать проект с прошедшим сроком, временно отключим валидацию
        project = Project.__new__(Project)
        project.id = None
        project.name = "Просроченный проект"
        project.description = "Описание"
        project.start_date = start_date
        project.end_date = end_date
        project.status = "active"
        
        assert project.is_overdue() is True
    
    def test_project_is_overdue_completed(self):
        """Тест: завершенный проект не считается просроченным"""
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now() - timedelta(days=1)
        
        # Создаем завершенный проект с просроченным сроком
        project = Project.__new__(Project)
        project.id = None
        project.name = "Завершенный просроченный проект"
        project.description = "Описание"
        project.start_date = start_date
        project.end_date = end_date
        project.status = "completed"
        
        assert project.is_overdue() is False
    
    def test_project_to_dict(self):
        """Тест преобразования проекта в словарь"""
        start_date = datetime.now() - timedelta(days=10)
        end_date = start_date + timedelta(days=30)
        
        project = Project("Тест", "Описание", start_date, end_date)
        project.id = 42  # Устанавливаем ID для теста
        
        result = project.to_dict()
        
        assert isinstance(result, dict)
        assert result['id'] == 42
        assert result['name'] == "Тест"
        assert result['description'] == "Описание"
        assert result['start_date'] == start_date
        assert result['end_date'] == end_date
        assert result['status'] == "active"
        assert 'progress' in result
        assert isinstance(result['progress'], float)
        assert 'is_overdue' in result
        assert isinstance(result['is_overdue'], bool)
    
    def test_project_str_representation(self):
        """Тест строкового представления проекта"""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 12, 31)
        
        project = Project("Годовой проект", "Важный проект на год", start_date, end_date)
        project.id = 1
        
        str_repr = str(project)
        
        assert "Проект #1: Годовой проект" in str_repr
        assert "Статус: Активный" in str_repr
        assert "Период: 01.01.2024 - 31.12.2024" in str_repr
        assert "Прогресс:" in str_repr
    
    def test_project_repr_representation(self):
        """Тест представления для отладки"""
        start_date = datetime.now() - timedelta(days=10)
        end_date = start_date + timedelta(days=30)
        
        project = Project("Тест", "Описание", start_date, end_date)
        project.id = 5
        
        repr_str = repr(project)
        assert "Project(id=5" in repr_str
        assert "name='Тест'" in repr_str


class TestUserModel:
    """Тесты для модели User"""
    
    def test_user_creation(self):
        """Тест создания пользователя с валидными данными"""
        user = User(
            username="testuser",
            email="test@example.com",
            role="developer"
        )
        
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.role == "developer"
        assert isinstance(user.registration_date, datetime)
        assert user.id is None  # ID устанавливается при сохранении в БД
        
        # Проверяем вспомогательные методы
        assert user.is_developer() is True
        assert user.is_admin() is False
        assert user.is_manager() is False
    
    def test_user_creation_admin(self):
        """Тест создания администратора"""
        user = User("adminuser", "admin@example.com", "admin")
        
        assert user.is_admin() is True
        assert user.is_manager() is False
        assert user.is_developer() is False
    
    def test_user_creation_manager(self):
        """Тест создания менеджера"""
        user = User("manageruser", "manager@example.com", "manager")
        
        assert user.is_manager() is True
        assert user.is_admin() is False
        assert user.is_developer() is False
    
    def test_user_creation_short_username(self):
        """Тест создания пользователя с коротким именем"""
        with pytest.raises(ValueError, match="Имя пользователя должно содержать минимум 3 символа"):
            User("ab", "test@example.com", "developer")  # Слишком короткое
    
    def test_user_creation_empty_username(self):
        """Тест создания пользователя с пустым именем"""
        with pytest.raises(ValueError, match="Имя пользователя не может быть пустым"):
            User("   ", "test@example.com", "developer")  # Пустое
    
    def test_user_creation_long_username(self):
        """Тест создания пользователя с длинным именем"""
        long_username = "a" * 51  # 51 символ
        with pytest.raises(ValueError, match="Имя пользователя не может превышать 50 символов"):
            User(long_username, "test@example.com", "developer")
    
    def test_user_creation_invalid_email(self):
        """Тест создания пользователя с невалидным email"""
        with pytest.raises(ValueError, match="Некорректный email адрес"):
            User("testuser", "invalid-email", "developer")  # Некорректный email
    
    def test_user_creation_invalid_role(self):
        """Тест создания пользователя с невалидной ролью"""
        with pytest.raises(ValueError, match="Недопустимая роль"):
            User("testuser", "test@example.com", "invalid_role")  # Недопустимая роль
    
    def test_user_is_valid_email(self):
        """Тест метода проверки email"""
        user = User("testuser", "test@example.com", "developer")
        
        # Валидные email
        assert user._is_valid_email("user@example.com") is True
        assert user._is_valid_email("user.name@example.co.uk") is True
        assert user._is_valid_email("user123@sub.domain.com") is True
        
        # Невалидные email
        assert user._is_valid_email("invalid-email") is False
        assert user._is_valid_email("user@") is False
        assert user._is_valid_email("@example.com") is False
        assert user._is_valid_email("user@.com") is False
        assert user._is_valid_email("user..name@example.com") is False
        assert user._is_valid_email("") is False
        assert user._is_valid_email(None) is False
    
    def test_user_update_info_single_field(self):
        """Тест обновления одного поля"""
        user = User("olduser", "old@example.com", "developer")
        
        # Обновляем только имя
        user.update_info(username="newuser")
        assert user.username == "newuser"
        assert user.email == "old@example.com"
        assert user.role == "developer"
        
        # Обновляем только email
        user.update_info(email="new@example.com")
        assert user.username == "newuser"
        assert user.email == "new@example.com"
        assert user.role == "developer"
        
        # Обновляем только роль
        user.update_info(role="manager")
        assert user.username == "newuser"
        assert user.email == "new@example.com"
        assert user.role == "manager"
    
    def test_user_update_info_multiple_fields(self):
        """Тест обновления нескольких полей"""
        user = User("user1", "user1@example.com", "developer")
        
        # Обновляем все поля
        user.update_info(
            username="user2",
            email="user2@example.com",
            role="admin"
        )
        
        assert user.username == "user2"
        assert user.email == "user2@example.com"
        assert user.role == "admin"
        assert user.is_admin() is True
    
    def test_user_update_info_no_changes(self):
        """Тест обновления без изменений"""
        user = User("testuser", "test@example.com", "developer")
        
        # Пробуем обновить теми же значениями
        user.update_info(
            username="testuser",
            email="test@example.com",
            role="developer"
        )
        
        # Данные не должны измениться
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.role == "developer"
    
    def test_user_update_info_invalid_username(self):
        """Тест обновления с невалидным именем"""
        user = User("testuser", "test@example.com", "developer")
        
        with pytest.raises(ValueError, match="Имя пользователя должно содержать минимум 3 символа"):
            user.update_info(username="ab")  # Слишком короткое
    
    def test_user_update_info_invalid_email(self):
        """Тест обновления с невалидным email"""
        user = User("testuser", "test@example.com", "developer")
        
        with pytest.raises(ValueError, match="Некорректный email адрес"):
            user.update_info(email="invalid-email")
    
    def test_user_update_info_invalid_role(self):
        """Тест обновления с невалидной ролью"""
        user = User("testuser", "test@example.com", "developer")
        
        with pytest.raises(ValueError, match="Недопустимая роль"):
            user.update_info(role="invalid_role")
    
    def test_user_get_days_since_registration(self):
        """Тест получения дней с момента регистрации"""
        user = User.__new__(User)
        user.id = 1
        user.username = "testuser"
        user.email = "test@example.com"
        user.role = "developer"
        
        # Устанавливаем дату регистрации 10 дней назад
        user.registration_date = datetime.now() - timedelta(days=10)
        
        days = user.get_days_since_registration()
        assert isinstance(days, int)
        assert days == 10
    
    def test_user_to_dict(self):
        """Тест преобразования пользователя в словарь"""
        user = User.__new__(User)
        user.id = 1
        user.username = "testuser"
        user.email = "test@example.com"
        user.role = "developer"
        user.registration_date = datetime(2024, 1, 1)  # Фиксированная дата
        
        result = user.to_dict()
        
        assert isinstance(result, dict)
        assert result['id'] == 1
        assert result['username'] == "testuser"
        assert result['email'] == "test@example.com"
        assert result['role'] == "developer"
        assert result['registration_date'] == datetime(2024, 1, 1)
        assert result['is_admin'] is False
        assert result['is_manager'] is False
        assert result['is_developer'] is True
        assert 'days_since_registration' in result
        assert isinstance(result['days_since_registration'], int)
    
    def test_user_str_representation(self):
        """Тест строкового представления пользователя"""
        user = User.__new__(User)
        user.id = 42
        user.username = "john_doe"
        user.email = "john@example.com"
        user.role = "manager"
        user.registration_date = datetime(2024, 1, 1)
        
        str_repr = str(user)
        
        assert "Пользователь #42: john_doe" in str_repr
        assert "Email: john@example.com" in str_repr
        assert "Роль: Менеджер" in str_repr
        assert "Дата регистрации: 01.01.2024" in str_repr
    
    def test_user_repr_representation(self):
        """Тест представления для отладки"""
        user = User("testuser", "test@example.com", "developer")
        user.id = 5
        
        repr_str = repr(user)
        assert "User(id=5" in repr_str
        assert "username='testuser'" in repr_str


class TestIntegrationModels:
    """Интеграционные тесты моделей с базой данных"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db_manager = DatabaseManager(self.temp_db.name)
    
    def teardown_method(self):
        """Очистка после каждого теста"""
        self.db_manager.close()
        os.unlink(self.temp_db.name)
    
    def test_task_save_and_retrieve_from_db(self):
        """Тест сохранения и извлечения задачи из БД"""
        # Создаем тестовые данные
        user = User("testuser", "test@example.com", "developer")
        user_id = self.db_manager.add_user(user)
        
        start_date = datetime.now() - timedelta(days=10)
        end_date = start_date + timedelta(days=30)
        project = Project("Test Project", "Description", start_date, end_date)
        project_id = self.db_manager.add_project(project)
        
        # Создаем и сохраняем задачу
        due_date = datetime.now() + timedelta(days=7)
        task = Task("Test Task", "Task Description", 2, due_date, project_id, user_id)
        task_id = self.db_manager.add_task(task)
        
        # Извлекаем задачу из БД
        retrieved_task = self.db_manager.get_task_by_id(task_id)
        
        assert retrieved_task is not None
        assert retrieved_task.id == task_id
        assert retrieved_task.title == "Test Task"
        assert retrieved_task.description == "Task Description"
        assert retrieved_task.priority == 2
        assert retrieved_task.status == "pending"
        assert retrieved_task.project_id == project_id
        assert retrieved_task.assignee_id == user_id
    
    def test_project_save_and_retrieve_from_db(self):
        """Тест сохранения и извлечения проекта из БД"""
        # Создаем и сохраняем проект
        start_date = datetime.now() - timedelta(days=10)
        end_date = start_date + timedelta(days=30)
        project = Project("Test Project", "Project Description", start_date, end_date)
        project_id = self.db_manager.add_project(project)
        
        # Извлекаем проект из БД
        retrieved_project = self.db_manager.get_project_by_id(project_id)
        
        assert retrieved_project is not None
        assert retrieved_project.id == project_id
        assert retrieved_project.name == "Test Project"
        assert retrieved_project.description == "Project Description"
        assert retrieved_project.start_date == start_date
        assert retrieved_project.end_date == end_date
        assert retrieved_project.status == "active"
    
    def test_user_save_and_retrieve_from_db(self):
        """Тест сохранения и извлечения пользователя из БД"""
        # Создаем и сохраняем пользователя
        user = User("testuser", "test@example.com", "developer")
        user_id = self.db_manager.add_user(user)
        
        # Извлекаем пользователя из БД
        retrieved_user = self.db_manager.get_user_by_id(user_id)
        
        assert retrieved_user is not None
        assert retrieved_user.id == user_id
        assert retrieved_user.username == "testuser"
        assert retrieved_user.email == "test@example.com"
        assert retrieved_user.role == "developer"
        assert isinstance(retrieved_user.registration_date, datetime)
    
    def test_task_status_update_in_db(self):
        """Тест обновления статуса задачи в БД"""
        # Создаем тестовые данные
        user = User("testuser", "test@example.com", "developer")
        user_id = self.db_manager.add_user(user)
        
        start_date = datetime.now() - timedelta(days=10)
        end_date = start_date + timedelta(days=30)
        project = Project("Test Project", "Description", start_date, end_date)
        project_id = self.db_manager.add_project(project)
        
        # Создаем и сохраняем задачу
        due_date = datetime.now() + timedelta(days=7)
        task = Task("Test Task", "Description", 1, due_date, project_id, user_id)
        task_id = self.db_manager.add_task(task)
        
        # Обновляем статус задачи
        self.db_manager.update_task(task_id, status="in_progress")
        
        # Проверяем обновленный статус
        updated_task = self.db_manager.get_task_by_id(task_id)
        assert updated_task.status == "in_progress"
    
    def test_project_status_update_in_db(self):
        """Тест обновления статуса проекта в БД"""
        # Создаем и сохраняем проект
        start_date = datetime.now() - timedelta(days=10)
        end_date = start_date + timedelta(days=30)
        project = Project("Test Project", "Description", start_date, end_date)
        project_id = self.db_manager.add_project(project)
        
        # Обновляем статус проекта
        self.db_manager.update_project(project_id, status="completed")
        
        # Проверяем обновленный статус
        updated_project = self.db_manager.get_project_by_id(project_id)
        assert updated_project.status == "completed"
    
    def test_user_update_in_db(self):
        """Тест обновления пользователя в БД"""
        # Создаем и сохраняем пользователя
        user = User("olduser", "old@example.com", "developer")
        user_id = self.db_manager.add_user(user)
        
        # Обновляем пользователя
        self.db_manager.update_user(user_id, username="newuser", email="new@example.com", role="manager")
        
        # Проверяем обновленные данные
        updated_user = self.db_manager.get_user_by_id(user_id)
        assert updated_user.username == "newuser"
        assert updated_user.email == "new@example.com"
        assert updated_user.role == "manager"


if __name__ == "__main__":
    # Запуск тестов
    pytest.main([__file__, "-v"])