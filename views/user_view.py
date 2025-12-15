import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime


class UserView(ttk.Frame):
    def __init__(self, parent, user_controller, task_controller=None) -> None:
        super().__init__(parent)
        
        self.user_controller = user_controller
        self.task_controller = task_controller
        
        self.setup_view()
        self.create_widgets()
    
    def setup_view(self) -> None:
        """Настройка представления"""
        self.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
    
    def create_widgets(self) -> None:
        """Создание виджетов интерфейса"""
        # Панель управления
        control_frame = ttk.Frame(self)
        control_frame.grid(row=0, column=0, sticky=tk.EW, pady=(0, 10))
        
        # Кнопки управления
        ttk.Button(control_frame, text="Добавить пользователя", 
                  command=self.add_user).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="Обновить", 
                  command=self.refresh_users).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="Удалить выбранного", 
                  command=self.delete_selected).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="Показать задачи", 
                  command=self.show_user_tasks).pack(side=tk.LEFT, padx=2)
        
        # Панель фильтров
        filter_frame = ttk.Frame(control_frame)
        filter_frame.pack(side=tk.RIGHT, padx=2)
        
        # Фильтр по роли
        ttk.Label(filter_frame, text="Роль:").pack(side=tk.LEFT)
        self.role_filter_var = tk.StringVar(value="Все")
        role_combo = ttk.Combobox(filter_frame, textvariable=self.role_filter_var, 
                                 values=["Все", "admin", "manager", "developer"], 
                                 state="readonly", width=12)
        role_combo.pack(side=tk.LEFT, padx=2)
        role_combo.bind('<<ComboboxSelected>>', self.filter_users)
        
        # Таблица пользователей
        columns = ('id', 'username', 'email', 'role', 'reg_date', 'days_reg', 'tasks')
        self.user_tree = ttk.Treeview(self, columns=columns, show='headings', height=20)
        
        # Настройка колонок
        self.user_tree.heading('id', text='ID')
        self.user_tree.heading('username', text='Имя пользователя')
        self.user_tree.heading('email', text='Email')
        self.user_tree.heading('role', text='Роль')
        self.user_tree.heading('reg_date', text='Регистрация')
        self.user_tree.heading('days_reg', text='Дней')
        self.user_tree.heading('tasks', text='Задачи')
        
        self.user_tree.column('id', width=50, anchor=tk.CENTER)
        self.user_tree.column('username', width=150)
        self.user_tree.column('email', width=200)
        self.user_tree.column('role', width=100, anchor=tk.CENTER)
        self.user_tree.column('reg_date', width=100, anchor=tk.CENTER)
        self.user_tree.column('days_reg', width=60, anchor=tk.CENTER)
        self.user_tree.column('tasks', width=80, anchor=tk.CENTER)
        
        # Скроллбар
        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.user_tree.yview)
        self.user_tree.configure(yscrollcommand=scrollbar.set)
        
        # Размещение
        self.user_tree.grid(row=1, column=0, sticky=tk.NSEW, padx=(0, 5))
        scrollbar.grid(row=1, column=1, sticky=tk.NS)
        
        # Двойной клик для редактирования
        self.user_tree.bind('<Double-Button-1>', self.edit_user)
        
        # Детальная информация о пользователе
        self.detail_frame = ttk.LabelFrame(self, text="Детали пользователя", padding=10)
        self.detail_frame.grid(row=2, column=0, columnspan=2, sticky=tk.EW, pady=(10, 0))
        
        # Скрываем детальную информацию по умолчанию
        self.detail_frame.grid_remove()
        
        # Создаем виджеты для детальной информации
        self.create_detail_widgets()
        
        # Инициализация данных
        self.all_users = []
        self.refresh_users()
    
    def create_detail_widgets(self):
        """Создание виджетов для детальной информации о пользователе"""
        # Имя пользователя
        self.detail_username = ttk.Label(self.detail_frame, text="", font=('Arial', 12, 'bold'))
        self.detail_username.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        # Email
        ttk.Label(self.detail_frame, text="Email:", font=('Arial', 10, 'bold')).grid(
            row=1, column=0, sticky=tk.W, pady=2)
        self.detail_email = ttk.Label(self.detail_frame, text="")
        self.detail_email.grid(row=1, column=1, sticky=tk.W, pady=2, padx=(10, 0))
        
        # Роль
        ttk.Label(self.detail_frame, text="Роль:", font=('Arial', 10, 'bold')).grid(
            row=2, column=0, sticky=tk.W, pady=2)
        self.detail_role = ttk.Label(self.detail_frame, text="")
        self.detail_role.grid(row=2, column=1, sticky=tk.W, pady=2, padx=(10, 0))
        
        # Дата регистрации
        ttk.Label(self.detail_frame, text="Дата регистрации:", font=('Arial', 10, 'bold')).grid(
            row=3, column=0, sticky=tk.W, pady=2)
        self.detail_reg_date = ttk.Label(self.detail_frame, text="")
        self.detail_reg_date.grid(row=3, column=1, sticky=tk.W, pady=2, padx=(10, 0))
        
        # Дней в системе
        ttk.Label(self.detail_frame, text="В системе:", font=('Arial', 10, 'bold')).grid(
            row=4, column=0, sticky=tk.W, pady=2)
        self.detail_days_in_system = ttk.Label(self.detail_frame, text="")
        self.detail_days_in_system.grid(row=4, column=1, sticky=tk.W, pady=2, padx=(10, 0))
        
        # Статистика задач
        ttk.Label(self.detail_frame, text="Статистика задач:", font=('Arial', 10, 'bold')).grid(
            row=5, column=0, sticky=tk.W, pady=2)
        
        # Фрейм для статистики задач
        stats_frame = ttk.Frame(self.detail_frame)
        stats_frame.grid(row=5, column=1, sticky=tk.W, pady=2, padx=(10, 0))
        
        self.detail_tasks_total = ttk.Label(stats_frame, text="Всего: 0")
        self.detail_tasks_total.pack(anchor=tk.W)
        
        self.detail_tasks_completed = ttk.Label(stats_frame, text="Завершено: 0")
        self.detail_tasks_completed.pack(anchor=tk.W)
        
        self.detail_tasks_in_progress = ttk.Label(stats_frame, text="В работе: 0")
        self.detail_tasks_in_progress.pack(anchor=tk.W)
        
        self.detail_tasks_pending = ttk.Label(stats_frame, text="Ожидание: 0")
        self.detail_tasks_pending.pack(anchor=tk.W)
        
        self.detail_tasks_overdue = ttk.Label(stats_frame, text="Просрочено: 0")
        self.detail_tasks_overdue.pack(anchor=tk.W)
        
        # Кнопка закрыть детали
        ttk.Button(self.detail_frame, text="Закрыть", 
                  command=self.hide_details).grid(row=6, column=0, columnspan=2, pady=(10, 0))
    
    def refresh_users(self) -> None:
        """Обновить список пользователей"""
        # Очищаем дерево
        for item in self.user_tree.get_children():
            self.user_tree.delete(item)
        
        # Получаем всех пользователей
        self.all_users = self.user_controller.get_all_users()
        
        # Применяем фильтры
        filtered_users = self.apply_filters(self.all_users)
        
        # Заполняем дерево
        for user in filtered_users:
            # Получаем задачи пользователя
            tasks = []
            if self.task_controller:
                tasks = self.user_controller.get_user_tasks(user.id)
            
            total_tasks = len(tasks)
            
            # Форматируем дату
            reg_date = user.registration_date.strftime('%d.%m.%Y')
            
            # Определяем роль
            role_names = {'admin': 'Администратор', 'manager': 'Менеджер', 'developer': 'Разработчик'}
            role = role_names.get(user.role, user.role)
            
            # Рассчитываем дни с регистрации
            days_registered = 0
            if hasattr(user, 'get_days_since_registration'):
                days_registered = user.get_days_since_registration()
            else:
                now = datetime.now()
                days_registered = (now - user.registration_date).days
            
            self.user_tree.insert('', tk.END, values=(
                user.id,
                user.username,
                user.email,
                role,
                reg_date,
                days_registered,
                total_tasks
            ))
    
    def apply_filters(self, users):
        """Применить фильтры к списку пользователей"""
        filtered_users = users
        
        # Фильтр по роли
        role_filter = self.role_filter_var.get()
        if role_filter != "Все":
            filtered_users = [u for u in filtered_users if u.role == role_filter]
        
        return filtered_users
    
    def filter_users(self, event=None) -> None:
        """Фильтровать пользователей"""
        self.refresh_users()
    
    def show_developers(self) -> None:
        """Показать только разработчиков"""
        self.role_filter_var.set("developer")
        self.refresh_users()
    
    def show_managers(self) -> None:
        """Показать только менеджеров"""
        self.role_filter_var.set("manager")
        self.refresh_users()
    
    def show_admins(self) -> None:
        """Показать только администраторов"""
        self.role_filter_var.set("admin")
        self.refresh_users()
    
    def add_user(self) -> None:
        """Добавить нового пользователя"""
        dialog = UserDialog(self, self.user_controller)
        self.wait_window(dialog)
        if dialog.result:
            self.refresh_users()
    
    def edit_user(self, event) -> None:
        """Редактировать выбранного пользователя"""
        selection = self.user_tree.selection()
        if not selection:
            return
        
        item = self.user_tree.item(selection[0])
        user_id = item['values'][0]
        
        user = self.user_controller.get_user(user_id)
        if user:
            dialog = UserDialog(self, self.user_controller, user)
            self.wait_window(dialog)
            if dialog.result:
                self.refresh_users()
    
    def delete_selected(self) -> None:
        """Удалить выбранного пользователя"""
        selection = self.user_tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите пользователя для удаления")
            return
        
        item = self.user_tree.item(selection[0])
        user_id = item['values'][0]
        username = item['values'][1]
        
        if messagebox.askyesno("Подтверждение", f"Удалить пользователя '{username}'?"):
            success = self.user_controller.delete_user(user_id)
            if success:
                self.refresh_users()
                self.hide_details()  # Скрываем детали если они отображались
                messagebox.showinfo("Успех", f"Пользователь '{username}' удален")
            else:
                messagebox.showerror("Ошибка", 
                                   "Не удалось удалить пользователя. Возможно у него есть задачи.")
    
    def show_user_tasks(self) -> None:
        """Показать задачи выбранного пользователя"""
        selection = self.user_tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите пользователя")
            return
        
        item = self.user_tree.item(selection[0])
        user_id = item['values'][0]
        username = item['values'][1]
        
        if not self.task_controller:
            messagebox.showinfo("Информация", 
                              "Контроллер задач не подключен к представлению пользователей")
            return
        
        # Создаем диалог для просмотра задач пользователя
        tasks = self.user_controller.get_user_tasks(user_id)
        
        if not tasks:
            messagebox.showinfo("Задачи пользователя", 
                              f"У пользователя '{username}' нет задач")
            return
        
        # Показываем детальную информацию о пользователе
        self.show_user_details(user_id)
    
    def show_user_details(self, user_id):
        """Показать детальную информацию о пользователе"""
        user = self.user_controller.get_user(user_id)
        if not user:
            return
        
        # Получаем задачи пользователя
        tasks = []
        if self.task_controller:
            tasks = self.user_controller.get_user_tasks(user_id)
        
        total_tasks = len(tasks)
        completed_tasks = sum(1 for task in tasks if task.status == 'completed')
        in_progress_tasks = sum(1 for task in tasks if task.status == 'in_progress')
        pending_tasks = sum(1 for task in tasks if task.status == 'pending')
        overdue_tasks = sum(1 for task in tasks if task.is_overdue())
        
        # Обновляем детальную информацию
        self.detail_username.config(text=user.username)
        self.detail_email.config(text=user.email)
        
        # Роль
        role_names = {'admin': 'Администратор', 'manager': 'Менеджер', 'developer': 'Разработчик'}
        role = role_names.get(user.role, user.role)
        self.detail_role.config(text=role)
        
        # Дата регистрации
        reg_date = user.registration_date.strftime('%d.%m.%Y %H:%M')
        self.detail_reg_date.config(text=reg_date)
        
        # Дни в системе
        days_in_system = 0
        if hasattr(user, 'get_days_since_registration'):
            days_in_system = user.get_days_since_registration()
        else:
            now = datetime.now()
            days_in_system = (now - user.registration_date).days
        
        self.detail_days_in_system.config(text=f"{days_in_system} дней")
        
        # Статистика задач
        self.detail_tasks_total.config(text=f"Всего: {total_tasks}")
        self.detail_tasks_completed.config(text=f"Завершено: {completed_tasks}")
        self.detail_tasks_in_progress.config(text=f"В работе: {in_progress_tasks}")
        self.detail_tasks_pending.config(text=f"Ожидание: {pending_tasks}")
        self.detail_tasks_overdue.config(text=f"Просрочено: {overdue_tasks}")
        
        # Показываем фрейм с деталями
        self.detail_frame.grid()
    
    def hide_details(self):
        """Скрыть детальную информацию"""
        self.detail_frame.grid_remove()
    
    def on_user_selected(self, event):
        """Обработчик выбора пользователя в дереве"""
        selection = self.user_tree.selection()
        if not selection:
            self.hide_details()
            return
        
        item = self.user_tree.item(selection[0])
        user_id = item['values'][0]
        
        self.show_user_details(user_id)


class UserDialog(tk.Toplevel):
    """Диалог для добавления/редактирования пользователя"""
    
    def __init__(self, parent, user_controller, user=None):
        super().__init__(parent)
        self.user_controller = user_controller
        self.user = user  # Если None - добавление, иначе - редактирование
        self.result = False
        
        self.setup_dialog()
        self.create_widgets()
        
        if user:
            self.load_user_data()
    
    def setup_dialog(self):
        if self.user:
            self.title("Редактировать пользователя")
        else:
            self.title("Добавить пользователя")
        
        self.geometry("400x250")
        self.resizable(False, False)
        
        # Центрирование
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
        
        self.transient(self.master)
        self.grab_set()
    
    def create_widgets(self):
        # Основной фрейм
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Имя пользователя
        ttk.Label(main_frame, text="Имя пользователя:*").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.username_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.username_var, width=25).grid(row=0, column=1, pady=5, padx=(5, 0))
        
        # Email
        ttk.Label(main_frame, text="Email:*").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.email_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.email_var, width=25).grid(row=1, column=1, pady=5, padx=(5, 0))
        
        # Роль
        ttk.Label(main_frame, text="Роль:*").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.role_var = tk.StringVar(value="developer")
        role_combo = ttk.Combobox(main_frame, textvariable=self.role_var, 
                                 values=["admin", "manager", "developer"], 
                                 state="readonly", width=15)
        role_combo.grid(row=2, column=1, sticky=tk.W, pady=5, padx=(5, 0))
        
        # Кнопки
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)
        
        if self.user:
            ttk.Button(button_frame, text="Сохранить", command=self.save_user).pack(side=tk.LEFT, padx=5)
        else:
            ttk.Button(button_frame, text="Добавить", command=self.save_user).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Отмена", command=self.destroy).pack(side=tk.LEFT, padx=5)
    
    def load_user_data(self):
        """Загрузить данные пользователя в форму"""
        if not self.user:
            return
        
        self.username_var.set(self.user.username)
        self.email_var.set(self.user.email)
        self.role_var.set(self.user.role)
    
    def save_user(self):
        """Сохранить пользователя"""
        # Валидация данных
        username = self.username_var.get().strip()
        if not username:
            messagebox.showerror("Ошибка", "Введите имя пользователя")
            return
        
        if len(username) < 3:
            messagebox.showerror("Ошибка", "Имя пользователя должно содержать минимум 3 символа")
            return
        
        email = self.email_var.get().strip()
        if not email:
            messagebox.showerror("Ошибка", "Введите email")
            return
        
        # Проверяем валидность email
        if not self.is_valid_email(email):
            messagebox.showerror("Ошибка", "Некорректный email адрес")
            return
        
        role = self.role_var.get()
        if role not in ["admin", "manager", "developer"]:
            messagebox.showerror("Ошибка", "Выберите роль")
            return
        
        if self.user:
            # Обновление существующего пользователя
            success = self.user_controller.update_user(
                self.user.id,
                username=username,
                email=email,
                role=role
            )
            
            if success:
                self.result = True
                messagebox.showinfo("Успех", "Пользователь обновлен")
                self.destroy()
            else:
                messagebox.showerror("Ошибка", "Не удалось обновить пользователя")
        else:
            # Добавление нового пользователя
            user_id = self.user_controller.add_user(username, email, role)
            
            if user_id > 0:
                self.result = True
                messagebox.showinfo("Успех", f"Пользователь добавлен с ID {user_id}")
                self.destroy()
            else:
                messagebox.showerror("Ошибка", "Не удалось добавить пользователя")
    
    def is_valid_email(self, email):
        """Проверить валидность email"""
        # Простая проверка email
        if '@' not in email or '.' not in email:
            return False
        
        if email.count('@') != 1:
            return False
        
        local_part, domain = email.split('@')
        
        if not local_part or not domain:
            return False
        
        if '..' in email:
            return False
        
        return True