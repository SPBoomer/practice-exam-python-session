from datetime import datetime


class Project:
    def __init__(self, name: str, description: str, 
                 start_date: datetime, end_date: datetime) -> None:
        self.id = None  # Будет установлен при сохранении в БД
        self.name = name
        self.description = description
        self.start_date = start_date
        self.end_date = end_date
        self.status = 'active'  # Статус по умолчанию
        
        # Валидация входных данных
        self._validate_inputs()
    
    def _validate_inputs(self) -> None:
        """Проверка корректности входных данных"""
        if not self.name or not self.name.strip():
            raise ValueError("Название проекта не может быть пустым")
        
        if not self.description or not self.description.strip():
            raise ValueError("Описание проекта не может быть пустым")
        
        if not isinstance(self.start_date, datetime):
            raise TypeError("start_date должен быть объектом datetime")
        
        if not isinstance(self.end_date, datetime):
            raise TypeError("end_date должен быть объектом datetime")
        
        if self.end_date <= self.start_date:
            raise ValueError("Дата окончания должна быть позже даты начала")
        
        if self.start_date > datetime.now():
            raise ValueError("Дата начала не может быть в будущем")
    
    def update_status(self, new_status: str) -> bool:
        valid_statuses = ['active', 'completed', 'on_hold']
        
        if new_status not in valid_statuses:
            print(f"Ошибка: недопустимый статус '{new_status}'. Допустимые значения: {valid_statuses}")
            return False
        
        if self.status == new_status:
            print(f"Статус уже установлен как '{new_status}'")
            return False
        
        old_status = self.status
        self.status = new_status
        
        print(f"Статус проекта '{self.name}' изменен: {old_status} -> {new_status}")
        return True
    
    def get_progress(self) -> float:
        now = datetime.now()
        
        # Если проект завершен, прогресс = 100%
        if self.status == 'completed':
            return 1.0
        
        # Если проект приостановлен, прогресс не меняется
        if self.status == 'on_hold':
            # Возвращаем текущий прогресс по времени
            return self._calculate_time_progress(now)
        
        # Рассчитываем прогресс по времени для активного проекта
        return self._calculate_time_progress(now)
    
    def _calculate_time_progress(self, current_time: datetime) -> float:
        # Общая длительность проекта в секундах
        total_duration = (self.end_date - self.start_date).total_seconds()
        
        if total_duration <= 0:
            return 0.0
        
        # Прошедшее время в секундах
        if current_time < self.start_date:
            elapsed_duration = 0
        elif current_time > self.end_date:
            elapsed_duration = total_duration
        else:
            elapsed_duration = (current_time - self.start_date).total_seconds()
        
        progress = elapsed_duration / total_duration
        return max(0.0, min(1.0, progress))  # Ограничиваем от 0 до 1
    
    def is_overdue(self) -> bool:
        now = datetime.now()
        if self.status == 'completed':
            return False
        return now > self.end_date
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'status': self.status,
            'progress': self.get_progress(),
            'is_overdue': self.is_overdue()
        }
    
    def __str__(self) -> str:
        """Строковое представление проекта"""
        status_names = {
            'active': 'Активный',
            'completed': 'Завершен',
            'on_hold': 'Приостановлен'
        }
        
        overdue = " (ПРОСРОЧЕН)" if self.is_overdue() else ""
        
        return (
            f"Проект #{self.id}: {self.name}{overdue}\n"
            f"Описание: {self.description}\n"
            f"Статус: {status_names.get(self.status, 'Неизвестно')}\n"
            f"Период: {self.start_date.strftime('%d.%m.%Y')} - {self.end_date.strftime('%d.%m.%Y')}\n"
            f"Прогресс: {self.get_progress() * 100:.1f}%"
        )
    
    def __repr__(self) -> str:
        """Представление для отладки"""
        return f"Project(id={self.id}, name='{self.name}', status='{self.status}')"