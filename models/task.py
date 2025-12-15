from datetime import datetime
from typing import Dict, Any


class Task:
    def __init__(self, title: str, description: str, priority: int, 
                 due_date: datetime, project_id: int, assignee_id: int) -> None:
        self.id = None  # Будет установлен при сохранении в БД
        self.title = title
        self.description = description
        self.priority = priority
        self.status = 'pending'  # Статус по умолчанию
        self.due_date = due_date
        self.project_id = project_id
        self.assignee_id = assignee_id
        
        # Валидация входных данных
        self._validate_inputs()
    
    def _validate_inputs(self) -> None:
        """Проверка корректности входных данных"""
        if not self.title or not self.title.strip():
            raise ValueError("Название задачи не может быть пустым")
        
        if not self.description or not self.description.strip():
            raise ValueError("Описание задачи не может быть пустым")
        
        if self.priority not in [1, 2, 3]:
            raise ValueError("Приоритет должен быть 1, 2 или 3")
        
        if not isinstance(self.due_date, datetime):
            raise TypeError("due_date должен быть объектом datetime")
        
        if self.due_date < datetime.now():
            raise ValueError("Срок выполнения не может быть в прошлом")
    
    def update_status(self, new_status: str) -> bool:

        valid_statuses = ['pending', 'in_progress', 'completed']
        
        if new_status not in valid_statuses:
            print(f"Ошибка: недопустимый статус '{new_status}'. Допустимые значения: {valid_statuses}")
            return False
        
        if self.status == new_status:
            print(f"Статус уже установлен как '{new_status}'")
            return False
        
        old_status = self.status
        self.status = new_status
        print(f"Статус задачи '{self.title}' изменен: {old_status} -> {new_status}")
        return True
    
    def is_overdue(self) -> bool:
        now = datetime.now()
        
        # Если задача уже завершена, она не считается просроченной
        if self.status == 'completed':
            return False
        
        return self.due_date < now
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'priority': self.priority,
            'status': self.status,
            'due_date': self.due_date,
            'project_id': self.project_id,
            'assignee_id': self.assignee_id,
            'is_overdue': self.is_overdue()
        }
    
    def __str__(self) -> str:
        """Строковое представление задачи"""
        priority_names = {
            1: 'Высокий',
            2: 'Средний', 
            3: 'Низкий'
        }
        
        overdue = " (ПРОСРОЧЕНА)" if self.is_overdue() else ""
        
        return (
            f"Задача #{self.id}: {self.title}{overdue}\n"
            f"Описание: {self.description}\n"
            f"Приоритет: {priority_names.get(self.priority, 'Неизвестно')} ({self.priority})\n"
            f"Статус: {self.status}\n"
            f"Срок: {self.due_date.strftime('%d.%m.%Y %H:%M')}\n"
            f"Проект: {self.project_id}, Исполнитель: {self.assignee_id}"
        )
    
    def __repr__(self) -> str:
        """Представление для отладки"""
        return f"Task(id={self.id}, title='{self.title}', status='{self.status}')"