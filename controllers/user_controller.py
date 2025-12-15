
from typing import List, Optional
from datetime import datetime

from models.user import User
from database.database_manager import DatabaseManager


class UserController:
    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db = db_manager
    
    def add_user(self, username: str, email: str, role: str) -> int:
        try:
            # Проверяем уникальность username и email
            existing_user_by_username = self.db.get_user_by_username(username)
            if existing_user_by_username:
                raise ValueError(f"Пользователь с именем '{username}' уже существует")
            
            existing_user_by_email = self.db.get_user_by_email(email)
            if existing_user_by_email:
                raise ValueError(f"Пользователь с email '{email}' уже существует")
            
            # Создаем объект пользователя
            user = User(
                username=username,
                email=email,
                role=role
            )
            
            # Сохраняем в базу данных
            user_id = self.db.add_user(user)
            print(f"Пользователь '{username}' успешно создан с ID {user_id}")
            return user_id
            
        except ValueError as e:
            print(f"Ошибка создания пользователя: {e}")
            return -1
        except Exception as e:
            print(f"Неожиданная ошибка при создании пользователя: {e}")
            return -1
    
    def get_user(self, user_id: int) -> Optional[User]:
        user = self.db.get_user_by_id(user_id)
        if not user:
            print(f"Пользователь с ID {user_id} не найден")
        return user
    
    def get_all_users(self) -> List[User]:
        users = self.db.get_all_users()
        print(f"Найдено {len(users)} пользователей")
        return users
    
    def update_user(self, user_id: int, **kwargs) -> bool:
        # Проверяем существование пользователя
        user = self.db.get_user_by_id(user_id)
        if not user:
            print(f"Пользователь с ID {user_id} не найден")
            return False
        
        # Проверяем валидность новых значений
        try:
            if 'username' in kwargs:
                new_username = kwargs['username']
                if new_username != user.username:
                    # Проверяем уникальность нового имени
                    existing_user = self.db.get_user_by_username(new_username)
                    if existing_user and existing_user.id != user_id:
                        raise ValueError(f"Пользователь с именем '{new_username}' уже существует")
            
            if 'email' in kwargs:
                new_email = kwargs['email']
                if new_email != user.email:
                    # Проверяем уникальность нового email
                    existing_user = self.db.get_user_by_email(new_email)
                    if existing_user and existing_user.id != user_id:
                        raise ValueError(f"Пользователь с email '{new_email}' уже существует")
                    
                    # Валидируем email
                    temp_user = User.__new__(User)
                    if not temp_user._is_valid_email(new_email):
                        raise ValueError(f"Некорректный email адрес: {new_email}")
            
            if 'role' in kwargs:
                new_role = kwargs['role']
                if new_role not in ['admin', 'manager', 'developer']:
                    raise ValueError("Роль должна быть 'admin', 'manager' или 'developer'")
            
            # Обновляем пользователя в базе данных
            success = self.db.update_user(user_id, **kwargs)
            if success:
                print(f"Пользователь с ID {user_id} успешно обновлен")
            else:
                print(f"Ошибка при обновлении пользователя с ID {user_id}")
            
            return success
            
        except ValueError as e:
            print(f"Ошибка обновления пользователя: {e}")
            return False
        except Exception as e:
            print(f"Неожиданная ошибка при обновлении пользователя: {e}")
            return False
    
    def delete_user(self, user_id: int) -> bool:
        # Проверяем существование пользователя
        user = self.db.get_user_by_id(user_id)
        if not user:
            print(f"Пользователь с ID {user_id} не найден")
            return False
        
        # Проверяем есть ли задачи у пользователя
        tasks = self.db.get_tasks_by_user(user_id)
        if tasks:
            print(f"Внимание: пользователь '{user.username}' имеет {len(tasks)} задач")
            print("Для удаления пользователя необходимо переназначить или удалить его задачи")
            return False
        
        # Удаляем пользователя
        success = self.db.delete_user(user_id)
        if success:
            print(f"Пользователь '{user.username}' (ID: {user_id}) успешно удален")
        else:
            print(f"Ошибка при удалении пользователя с ID {user_id}")
        
        return success
    
    def get_user_tasks(self, user_id: int) -> list:
        # Проверяем существование пользователя
        user = self.db.get_user_by_id(user_id)
        if not user:
            print(f"Пользователь с ID {user_id} не найден")
            return []
        
        # Получаем задачи пользователя
        tasks = self.db.get_tasks_by_user(user_id)
        print(f"Найдено {len(tasks)} задач для пользователя '{user.username}'")
        return tasks
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        user = self.db.get_user_by_username(username)
        if not user:
            print(f"Пользователь с именем '{username}' не найден")
        return user
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        user = self.db.get_user_by_email(email)
        if not user:
            print(f"Пользователь с email '{email}' не найден")
        return user
    
    def get_user_statistics(self, user_id: int) -> dict:
        # Получаем пользователя
        user = self.db.get_user_by_id(user_id)
        if not user:
            return {}
        
        # Получаем статистику из базы данных
        db_stats = self.db.get_user_statistics(user_id)
        
        # Получаем все задачи пользователя
        tasks = self.db.get_tasks_by_user(user_id)
        
        if not tasks:
            return {
                'username': user.username,
                'role': user.role,
                'registration_date': user.registration_date,
                'days_since_registration': user.get_days_since_registration() if hasattr(user, 'get_days_since_registration') else 0,
                'total_tasks': 0,
                'completed_tasks': 0,
                'in_progress_tasks': 0,
                'pending_tasks': 0,
                'overdue_tasks': 0
            }
        
        # Рассчитываем статистику
        task_stats = {
            'total_tasks': len(tasks),
            'completed_tasks': sum(1 for task in tasks if task.status == 'completed'),
            'in_progress_tasks': sum(1 for task in tasks if task.status == 'in_progress'),
            'pending_tasks': sum(1 for task in tasks if task.status == 'pending'),
            'overdue_tasks': sum(1 for task in tasks if task.is_overdue()),
        }
        
        return {
            'username': user.username,
            'role': user.role,
            'registration_date': user.registration_date,
            'days_since_registration': user.get_days_since_registration() if hasattr(user, 'get_days_since_registration') else 0,
            **task_stats
        }
    
    def print_user_info(self, user_id: int) -> None:
        user = self.get_user(user_id)
        if user:
            print("\n" + "="*50)
            print(str(user))
            print("="*50)
            
            # Выводим статистику
            stats = self.get_user_statistics(user_id)
            if stats:
                print(f"\nСтатистика задач:")
                print(f"  Всего задач: {stats.get('total_tasks', 0)}")
                print(f"  Завершено: {stats.get('completed_tasks', 0)}")
                print(f"  В работе: {stats.get('in_progress_tasks', 0)}")
                print(f"  Ожидание: {stats.get('pending_tasks', 0)}")
                print(f"  Просрочено: {stats.get('overdue_tasks', 0)}")
    
    def print_users_list(self, users: List[User], title: str = "Список пользователей") -> None:
        if not users:
            print(f"\n{title}: нет пользователей")
            return
        
        print(f"\n{title}:")
        print("-" * 90)
        print(f"{'ID':<5} {'Имя':<20} {'Email':<25} {'Роль':<15} {'Дата регистрации':<20} {'Дней':<6}")
        print("-" * 90)
        
        for user in users:
            role_names = {
                'admin': 'Администратор',
                'manager': 'Менеджер',
                'developer': 'Разработчик'
            }
            
            role = role_names.get(user.role, user.role)
            reg_date = user.registration_date.strftime('%d.%m.%Y')
            days_since = user.get_days_since_registration() if hasattr(user, 'get_days_since_registration') else 0
            
            print(f"{user.id:<5} {user.username:<20} {user.email[:23]:<25} {role:<15} {reg_date:<20} {days_since:<6}")
        
        print("-" * 90)
        print(f"Всего пользователей: {len(users)}")
    
    def get_users_by_role(self, role: str) -> List[User]:
        if role not in ['admin', 'manager', 'developer']:
            print(f"Недопустимая роль: {role}")
            return []
        
        all_users = self.db.get_all_users()
        filtered_users = [user for user in all_users if user.role == role]
        
        role_names = {
            'admin': 'администраторов',
            'manager': 'менеджеров',
            'developer': 'разработчиков'
        }
        
        print(f"Найдено {len(filtered_users)} {role_names.get(role, role)}")
        return filtered_users
    
    def get_developers(self) -> List[User]:
        return self.get_users_by_role('developer')
    
    def get_managers(self) -> List[User]:
        return self.get_users_by_role('manager')
    
    def get_admins(self) -> List[User]:
        return self.get_users_by_role('admin')
    
    def reassign_user_tasks(self, old_user_id: int, new_user_id: int) -> bool:
        # Проверяем существование пользователей
        old_user = self.db.get_user_by_id(old_user_id)
        if not old_user:
            print(f"Пользователь с ID {old_user_id} не найден")
            return False
        
        new_user = self.db.get_user_by_id(new_user_id)
        if not new_user:
            print(f"Пользователь с ID {new_user_id} не найден")
            return False
        
        # Получаем задачи текущего пользователя
        tasks = self.db.get_tasks_by_user(old_user_id)
        if not tasks:
            print(f"У пользователя '{old_user.username}' нет задач для переназначения")
            return True
        
        print(f"Переназначение {len(tasks)} задач от '{old_user.username}' к '{new_user.username}'...")
        
        # Переназначаем каждую задачу
        success_count = 0
        for task in tasks:
            success = self.db.update_task(task.id, assignee_id=new_user_id)
            if success:
                success_count += 1
        
        print(f"Успешно переназначено {success_count} из {len(tasks)} задач")
        return success_count == len(tasks)