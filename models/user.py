from datetime import datetime
import re


class User:
    def __init__(self, username: str, email: str, role: str) -> None:
        self.id = None  # Будет установлен при сохранении в БД
        self.username = username
        self.email = email
        self.role = role
        self.registration_date = datetime.now()
        
        # Валидация входных данных
        self._validate_inputs()
    
    def _validate_inputs(self) -> None:
        """Проверка корректности входных данных"""
        if not self.username or not self.username.strip():
            raise ValueError("Имя пользователя не может быть пустым")
        
        if len(self.username) < 3:
            raise ValueError("Имя пользователя должно содержать минимум 3 символа")
        
        if len(self.username) > 50:
            raise ValueError("Имя пользователя не может превышать 50 символов")
        
        if not self._is_valid_email(self.email):
            raise ValueError(f"Некорректный email адрес: {self.email}")
        
        valid_roles = ['admin', 'manager', 'developer']
        if self.role not in valid_roles:
            raise ValueError(f"Недопустимая роль '{self.role}'. Допустимые значения: {valid_roles}")
    
    def _is_valid_email(self, email: str) -> bool:

        if not email or not isinstance(email, str):
            return False
        
        # Паттерн для проверки email
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        # Проверяем соответствие паттерну
        if not re.match(pattern, email):
            return False
        
        # Дополнительные проверки
        if '..' in email:
            return False
        
        # Проверяем длину
        if len(email) > 254:
            return False
        
        return True
    
    def update_info(self, username: str = None, email: str = None, role: str = None) -> None:
        updated_fields = []
        
        # Обновление имени пользователя
        if username is not None:
            if not username.strip():
                raise ValueError("Имя пользователя не может быть пустым")
            
            if len(username) < 3:
                raise ValueError("Имя пользователя должно содержать минимум 3 символа")
            
            if len(username) > 50:
                raise ValueError("Имя пользователя не может превышать 50 символов")
            
            if self.username != username:
                self.username = username
                updated_fields.append('username')
        
        # Обновление email
        if email is not None:
            if not self._is_valid_email(email):
                raise ValueError(f"Некорректный email адрес: {email}")
            
            if self.email != email:
                self.email = email
                updated_fields.append('email')
        
        # Обновление роли
        if role is not None:
            valid_roles = ['admin', 'manager', 'developer']
            if role not in valid_roles:
                raise ValueError(f"Недопустимая роль '{role}'. Допустимые значения: {valid_roles}")
            
            if self.role != role:
                self.role = role
                updated_fields.append('role')
        
        # Выводим информацию об обновленных полях
        if updated_fields:
            print(f"Информация о пользователе обновлена: {', '.join(updated_fields)}")
        else:
            print("Нет изменений для обновления")
    
    def is_admin(self) -> bool:
        return self.role == 'admin'
    
    def is_manager(self) -> bool:
        return self.role == 'manager'
    
    def is_developer(self) -> bool:
        return self.role == 'developer'
    
    def get_days_since_registration(self) -> int:
        now = datetime.now()
        delta = now - self.registration_date
        return delta.days
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'registration_date': self.registration_date,
            'is_admin': self.is_admin(),
            'is_manager': self.is_manager(),
            'is_developer': self.is_developer(),
            'days_since_registration': self.get_days_since_registration()
        }
    
    def __str__(self) -> str:
        """Строковое представление пользователя"""
        role_names = {
            'admin': 'Администратор',
            'manager': 'Менеджер',
            'developer': 'Разработчик'
        }
        
        return (
            f"Пользователь #{self.id}: {self.username}\n"
            f"Email: {self.email}\n"
            f"Роль: {role_names.get(self.role, 'Неизвестно')}\n"
            f"Дата регистрации: {self.registration_date.strftime('%d.%m.%Y %H:%M')}\n"
            f"Зарегистрирован {self.get_days_since_registration()} дней назад"
        )
    
    def __repr__(self) -> str:
        """Представление для отладки"""
        return f"User(id={self.id}, username='{self.username}', role='{self.role}')"