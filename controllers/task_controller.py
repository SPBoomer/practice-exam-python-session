
from typing import List, Optional
from datetime import datetime

from models.task import Task
from database.database_manager import DatabaseManager


class TaskController:
    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db = db_manager
    
    def add_task(self, title: str, description: str, priority: int, 
                 due_date: datetime, project_id: int, assignee_id: int) -> int:
        try:
            # Проверяем существование проекта и пользователя
            project = self.db.get_project_by_id(project_id)
            if not project:
                raise ValueError(f"Проект с ID {project_id} не найден")
            
            user = self.db.get_user_by_id(assignee_id)
            if not user:
                raise ValueError(f"Пользователь с ID {assignee_id} не найден")
            
            # Создаем объект задачи
            task = Task(
                title=title,
                description=description,
                priority=priority,
                due_date=due_date,
                project_id=project_id,
                assignee_id=assignee_id
            )
            
            # Сохраняем в базу данных
            task_id = self.db.add_task(task)
            print(f"Задача '{title}' успешно создана с ID {task_id}")
            return task_id
            
        except ValueError as e:
            print(f"Ошибка создания задачи: {e}")
            return -1
        except Exception as e:
            print(f"Неожиданная ошибка при создании задачи: {e}")
            return -1
    
    def get_task(self, task_id: int) -> Optional[Task]:
        task = self.db.get_task_by_id(task_id)
        if not task:
            print(f"Задача с ID {task_id} не найдена")
        return task
    
    def get_all_tasks(self) -> List[Task]:
        tasks = self.db.get_all_tasks()
        print(f"Найдено {len(tasks)} задач")
        return tasks
    
    def update_task(self, task_id: int, **kwargs) -> bool:
        # Проверяем существование задачи
        task = self.db.get_task_by_id(task_id)
        if not task:
            print(f"Задача с ID {task_id} не найдена")
            return False
        
        # Проверяем валидность новых значений
        try:
            if 'priority' in kwargs:
                priority = kwargs['priority']
                if priority not in [1, 2, 3]:
                    raise ValueError("Приоритет должен быть 1, 2 или 3")
            
            if 'status' in kwargs:
                status = kwargs['status']
                if status not in ['pending', 'in_progress', 'completed']:
                    raise ValueError("Статус должен быть 'pending', 'in_progress' или 'completed'")
            
            if 'project_id' in kwargs:
                project_id = kwargs['project_id']
                project = self.db.get_project_by_id(project_id)
                if not project:
                    raise ValueError(f"Проект с ID {project_id} не найден")
            
            if 'assignee_id' in kwargs:
                assignee_id = kwargs['assignee_id']
                user = self.db.get_user_by_id(assignee_id)
                if not user:
                    raise ValueError(f"Пользователь с ID {assignee_id} не найден")
            
            # Обновляем задачу в базе данных
            success = self.db.update_task(task_id, **kwargs)
            if success:
                print(f"Задача с ID {task_id} успешно обновлена")
            else:
                print(f"Ошибка при обновлении задачи с ID {task_id}")
            
            return success
            
        except ValueError as e:
            print(f"Ошибка обновления задачи: {e}")
            return False
        except Exception as e:
            print(f"Неожиданная ошибка при обновлении задачи: {e}")
            return False
    
    def delete_task(self, task_id: int) -> bool:
        # Проверяем существование задачи
        task = self.db.get_task_by_id(task_id)
        if not task:
            print(f"Задача с ID {task_id} не найдена")
            return False
        
        # Удаляем задачу
        success = self.db.delete_task(task_id)
        if success:
            print(f"Задача '{task.title}' (ID: {task_id}) успешно удалена")
        else:
            print(f"Ошибка при удалении задачи с ID {task_id}")
        
        return success
    
    def search_tasks(self, query: str) -> List[Task]:
        if not query or not query.strip():
            print("Поисковый запрос не может быть пустым")
            return []
        
        tasks = self.db.search_tasks(query)
        print(f"Найдено {len(tasks)} задач по запросу '{query}'")
        return tasks
    
    def update_task_status(self, task_id: int, new_status: str) -> bool:
        # Получаем задачу
        task = self.db.get_task_by_id(task_id)
        if not task:
            print(f"Задача с ID {task_id} не найдена")
            return False
        
        # Обновляем статус через метод объекта Task
        success = task.update_status(new_status)
        if not success:
            return False
        
        # Сохраняем изменения в базе данных
        return self.db.update_task(task_id, status=new_status)
    
    def get_overdue_tasks(self) -> List[Task]:
        all_tasks = self.db.get_all_tasks()
        overdue_tasks = [task for task in all_tasks if task.is_overdue()]
        
        print(f"Найдено {len(overdue_tasks)} просроченных задач")
        return overdue_tasks
    
    def get_tasks_by_project(self, project_id: int) -> List[Task]:
        # Проверяем существование проекта
        project = self.db.get_project_by_id(project_id)
        if not project:
            print(f"Проект с ID {project_id} не найден")
            return []
        
        tasks = self.db.get_tasks_by_project(project_id)
        print(f"Найдено {len(tasks)} задач в проекте '{project.name}'")
        return tasks
    
    def get_tasks_by_user(self, user_id: int) -> List[Task]:
        # Проверяем существование пользователя
        user = self.db.get_user_by_id(user_id)
        if not user:
            print(f"Пользователь с ID {user_id} не найден")
            return []
        
        tasks = self.db.get_tasks_by_user(user_id)
        print(f"Найдено {len(tasks)} задач для пользователя '{user.username}'")
        return tasks
    
    def get_task_statistics(self) -> dict:
        all_tasks = self.db.get_all_tasks()
        
        if not all_tasks:
            return {
                'total': 0,
                'by_status': {},
                'by_priority': {},
                'overdue': 0
            }
        
        # Статистика по статусам
        status_stats = {}
        for task in all_tasks:
            status_stats[task.status] = status_stats.get(task.status, 0) + 1
        
        # Статистика по приоритетам
        priority_stats = {}
        for task in all_tasks:
            priority_names = {1: 'high', 2: 'medium', 3: 'low'}
            priority_name = priority_names.get(task.priority, 'unknown')
            priority_stats[priority_name] = priority_stats.get(priority_name, 0) + 1
        
        # Количество просроченных задач
        overdue_count = sum(1 for task in all_tasks if task.is_overdue())
        
        return {
            'total': len(all_tasks),
            'by_status': status_stats,
            'by_priority': priority_stats,
            'overdue': overdue_count
        }
    
    def print_task_info(self, task_id: int) -> None:
        task = self.get_task(task_id)
        if task:
            print("\n" + "="*50)
            print(str(task))
            print("="*50)
    
    def print_tasks_list(self, tasks: List[Task], title: str = "Список задач") -> None:
        if not tasks:
            print(f"\n{title}: нет задач")
            return
        
        print(f"\n{title}:")
        print("-" * 80)
        print(f"{'ID':<5} {'Название':<25} {'Приоритет':<10} {'Статус':<15} {'Срок':<15} {'Проект':<10}")
        print("-" * 80)
        
        for task in tasks:
            priority_names = {1: 'Высокий', 2: 'Средний', 3: 'Низкий'}
            priority = priority_names.get(task.priority, 'Неизвестно')
            due_date = task.due_date.strftime('%d.%m.%Y')
            status = task.status
            
            # Добавляем пометку для просроченных задач
            if task.is_overdue():
                status += " (⚠)"
            
            print(f"{task.id:<5} {task.title[:23]:<25} {priority:<10} {status:<15} {due_date:<15} {task.project_id:<10}")
        
        print("-" * 80)
        print(f"Всего задач: {len(tasks)}")