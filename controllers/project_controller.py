
from typing import List, Optional
from datetime import datetime

from models.project import Project
from database.database_manager import DatabaseManager


class ProjectController:
    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db = db_manager
    
    def add_project(self, name: str, description: str, 
                   start_date: datetime, end_date: datetime) -> int:
        try:
            # Создаем объект проекта
            project = Project(
                name=name,
                description=description,
                start_date=start_date,
                end_date=end_date
            )
            
            # Сохраняем в базу данных
            project_id = self.db.add_project(project)
            print(f"Проект '{name}' успешно создан с ID {project_id}")
            return project_id
            
        except ValueError as e:
            print(f"Ошибка создания проекта: {e}")
            return -1
        except Exception as e:
            print(f"Неожиданная ошибка при создании проекта: {e}")
            return -1
    
    def get_project(self, project_id: int) -> Optional[Project]:
        project = self.db.get_project_by_id(project_id)
        if not project:
            print(f"Проект с ID {project_id} не найден")
        return project
    
    def get_all_projects(self) -> List[Project]:
        projects = self.db.get_all_projects()
        print(f"Найдено {len(projects)} проектов")
        return projects
    
    def update_project(self, project_id: int, **kwargs) -> bool:
        # Проверяем существование проекта
        project = self.db.get_project_by_id(project_id)
        if not project:
            print(f"Проект с ID {project_id} не найден")
            return False
        
        # Проверяем валидность новых значений
        try:
            if 'status' in kwargs:
                status = kwargs['status']
                if status not in ['active', 'completed', 'on_hold']:
                    raise ValueError("Статус должен быть 'active', 'completed' или 'on_hold'")
            
            if 'start_date' in kwargs and 'end_date' in kwargs:
                start_date = kwargs['start_date']
                end_date = kwargs['end_date']
                if end_date <= start_date:
                    raise ValueError("Дата окончания должна быть позже даты начала")
            elif 'start_date' in kwargs:
                start_date = kwargs['start_date']
                if start_date > project.end_date:
                    raise ValueError("Дата начала не может быть позже даты окончания")
            elif 'end_date' in kwargs:
                end_date = kwargs['end_date']
                if end_date <= project.start_date:
                    raise ValueError("Дата окончания должна быть позже даты начала")
            
            # Обновляем проект в базе данных
            success = self.db.update_project(project_id, **kwargs)
            if success:
                print(f"Проект с ID {project_id} успешно обновлен")
            else:
                print(f"Ошибка при обновлении проекта с ID {project_id}")
            
            return success
            
        except ValueError as e:
            print(f"Ошибка обновления проекта: {e}")
            return False
        except Exception as e:
            print(f"Неожиданная ошибка при обновлении проекта: {e}")
            return False
    
    def delete_project(self, project_id: int) -> bool:
        # Проверяем существование проекта
        project = self.db.get_project_by_id(project_id)
        if not project:
            print(f"Проект с ID {project_id} не найдена")
            return False
        
        # Проверяем есть ли задачи в проекте
        tasks = self.db.get_tasks_by_project(project_id)
        if tasks:
            print(f"Внимание: проект '{project.name}' содержит {len(tasks)} задач")
            print("Задачи будут удалены вместе с проектом")
        
        # Удаляем проект
        success = self.db.delete_project(project_id)
        if success:
            print(f"Проект '{project.name}' (ID: {project_id}) успешно удален")
        else:
            print(f"Ошибка при удалении проекта с ID {project_id}")
        
        return success
    
    def update_project_status(self, project_id: int, new_status: str) -> bool:
        # Получаем проект
        project = self.db.get_project_by_id(project_id)
        if not project:
            print(f"Проект с ID {project_id} не найден")
            return False
        
        # Обновляем статус через метод объекта Project
        success = project.update_status(new_status)
        if not success:
            return False
        
        # Сохраняем изменения в базе данных
        return self.db.update_project(project_id, status=new_status)
    
    def get_project_progress(self, project_id: int) -> float:
        # Получаем проект
        project = self.db.get_project_by_id(project_id)
        if not project:
            print(f"Проект с ID {project_id} не найден")
            return -1.0
        
        # Получаем задачи проекта для точного расчета прогресса
        tasks = self.db.get_tasks_by_project(project_id)
        
        if tasks:
            # Рассчитываем прогресс на основе задач
            total_tasks = len(tasks)
            completed_tasks = sum(1 for task in tasks if task.status == 'completed')
            
            progress = project.get_progress()
            print(f"Прогресс проекта '{project.name}': {progress * 100:.1f}% "
                  f"({completed_tasks}/{total_tasks} задач завершено)")
        else:
            # Рассчитываем только на основе времени
            progress = project.get_progress()
            print(f"Прогресс проекта '{project.name}': {progress * 100:.1f}%")
        
        return progress
    
    def get_project_statistics(self, project_id: int) -> dict:
        # Получаем проект
        project = self.db.get_project_by_id(project_id)
        if not project:
            return {}
        
        # Получаем статистику из базы данных
        db_stats = self.db.get_project_statistics(project_id)
        
        # Получаем все задачи проекта
        tasks = self.db.get_tasks_by_project(project_id)
        
        if not tasks:
            return {
                'project_name': project.name,
                'status': project.status,
                'progress': project.get_progress(),
                'total_tasks': 0,
                'completed_tasks': 0,
                'in_progress_tasks': 0,
                'pending_tasks': 0,
                'overdue_tasks': 0,
                'days_remaining': project.get_days_remaining() if hasattr(project, 'get_days_remaining') else 0,
                'is_overdue': project.is_overdue() if hasattr(project, 'is_overdue') else False
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
            'project_name': project.name,
            'status': project.status,
            'progress': project.get_progress(),
            **task_stats,
            'days_remaining': project.get_days_remaining() if hasattr(project, 'get_days_remaining') else 0,
            'is_overdue': project.is_overdue() if hasattr(project, 'is_overdue') else False
        }
    
    def print_project_info(self, project_id: int) -> None:
        project = self.get_project(project_id)
        if project:
            print("\n" + "="*50)
            print(str(project))
            print("="*50)
            
            # Выводим статистику
            stats = self.get_project_statistics(project_id)
            if stats:
                print(f"\nСтатистика:")
                print(f"  Всего задач: {stats.get('total_tasks', 0)}")
                print(f"  Завершено: {stats.get('completed_tasks', 0)}")
                print(f"  В работе: {stats.get('in_progress_tasks', 0)}")
                print(f"  Ожидание: {stats.get('pending_tasks', 0)}")
                print(f"  Просрочено: {stats.get('overdue_tasks', 0)}")
    
    def print_projects_list(self, projects: List[Project], title: str = "Список проектов") -> None:
        if not projects:
            print(f"\n{title}: нет проектов")
            return
        
        print(f"\n{title}:")
        print("-" * 120)
        print(f"{'ID':<5} {'Название':<25} {'Статус':<12} {'Начало':<12} {'Окончание':<12} {'Прогресс':<10} {'Дней':<6} {'Задачи':<8}")
        print("-" * 120)
        
        for project in projects:
            # Получаем статистику для каждого проекта
            tasks = self.db.get_tasks_by_project(project.id)
            total_tasks = len(tasks)
            completed_tasks = sum(1 for task in tasks if task.status == 'completed')
            
            # Форматируем данные
            status_names = {
                'active': 'Активный',
                'completed': 'Завершен',
                'on_hold': 'Приостановлен'
            }
            
            status = status_names.get(project.status, project.status)
            start_date = project.start_date.strftime('%d.%m.%Y')
            end_date = project.end_date.strftime('%d.%m.%Y')
            progress = project.get_progress() * 100
            
            # Расчет дней до окончания
            now = datetime.now()
            if project.end_date > now:
                days_remaining = (project.end_date - now).days
                days_str = f"+{days_remaining}"
            else:
                days_remaining = (now - project.end_date).days
                days_str = f"-{days_remaining}"
            
            # Добавляем пометку для просроченных проектов
            if hasattr(project, 'is_overdue') and project.is_overdue() and project.status != 'completed':
                status += " (⚠)"
            
            print(f"{project.id:<5} {project.name[:23]:<25} {status:<12} {start_date:<12} {end_date:<12} "
                  f"{progress:>6.1f}% {days_str:>6} {completed_tasks:>3}/{total_tasks:<4}")
        
        print("-" * 120)
        print(f"Всего проектов: {len(projects)}")
    
    def get_active_projects(self) -> List[Project]:
        all_projects = self.db.get_all_projects()
        active_projects = [p for p in all_projects if p.status == 'active']
        print(f"Найдено {len(active_projects)} активных проектов")
        return active_projects
    
    def get_completed_projects(self) -> List[Project]:
        all_projects = self.db.get_all_projects()
        completed_projects = [p for p in all_projects if p.status == 'completed']
        print(f"Найдено {len(completed_projects)} завершенных проектов")
        return completed_projects
    
    def get_overdue_projects(self) -> List[Project]:
        all_projects = self.db.get_all_projects()
        overdue_projects = []
        
        for project in all_projects:
            if hasattr(project, 'is_overdue') and project.is_overdue() and project.status != 'completed':
                overdue_projects.append(project)
        
        print(f"Найдено {len(overdue_projects)} просроченных проектов")
        return overdue_projects