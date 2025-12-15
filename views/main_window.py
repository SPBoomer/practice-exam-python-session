import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import sys
import os

# Добавляем пути для импорта модулей
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from controllers.task_controller import TaskController
from controllers.project_controller import ProjectController
from controllers.user_controller import UserController
from database.database_manager import DatabaseManager


class MainWindow(tk.Tk):
    def __init__(self, db_manager) -> None:
        super().__init__()
        
        self.db_manager = db_manager
        
        # Инициализация контроллеров
        self.task_controller = TaskController(db_manager)
        self.project_controller = ProjectController(db_manager)
        self.user_controller = UserController(db_manager)
        
        self.setup_window()
        self.create_menu()
        self.create_widgets()
    
    def setup_window(self) -> None:
        """Настройка окна приложения"""
        self.title("Система управления задачами")
        self.geometry("1200x700")
        self.minsize(1000, 600)
        
        # Центрирование окна
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
        
        # Стиль
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Конфигурация цветов
        self.configure(bg='#f0f0f0')
    
    def create_menu(self) -> None:
        """Создание меню приложения"""
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        
        # Меню "Файл"
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Файл", menu=file_menu)
        file_menu.add_command(label="Обновить данные", command=self.refresh_all)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.quit)
        
        # Меню "Задачи"
        task_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Задачи", menu=task_menu)
        task_menu.add_command(label="Новая задача", command=self.show_add_task_dialog)
        task_menu.add_command(label="Просроченные задачи", command=self.show_overdue_tasks)
        task_menu.add_separator()
        task_menu.add_command(label="Статистика задач", command=self.show_task_statistics)
        
        # Меню "Проекты"
        project_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Проекты", menu=project_menu)
        project_menu.add_command(label="Новый проект", command=self.show_add_project_dialog)
        project_menu.add_command(label="Активные проекты", command=self.show_active_projects)
        project_menu.add_command(label="Просроченные проекты", command=self.show_overdue_projects)
        project_menu.add_separator()
        project_menu.add_command(label="Статистика проектов", command=self.show_project_statistics)
        
        # Меню "Пользователи"
        user_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Пользователи", menu=user_menu)
        user_menu.add_command(label="Новый пользователь", command=self.show_add_user_dialog)
        user_menu.add_command(label="Все разработчики", command=self.show_developers)
        user_menu.add_command(label="Все менеджеры", command=self.show_managers)
        user_menu.add_separator()
        user_menu.add_command(label="Статистика пользователей", command=self.show_user_statistics)
        
        # Меню "Справка"
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Справка", menu=help_menu)
        help_menu.add_command(label="О программе", command=self.show_about)
    
    def create_widgets(self) -> None:
        """Создание виджетов интерфейса"""
        # Создаем Notebook для вкладок
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Создаем фреймы для вкладок
        self.task_frame = ttk.Frame(self.notebook)
        self.project_frame = ttk.Frame(self.notebook)
        self.user_frame = ttk.Frame(self.notebook)
        
        self.notebook.add(self.task_frame, text="Задачи")
        self.notebook.add(self.project_frame, text="Проекты")
        self.notebook.add(self.user_frame, text="Пользователи")
        
        # Инициализируем содержимое вкладок
        self.init_task_tab()
        self.init_project_tab()
        self.init_user_tab()
        
        # Статус бар
        self.status_bar = tk.Label(self, text="Готово", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Обновляем данные при запуске
        self.refresh_all()
    
    def init_task_tab(self) -> None:
        """Инициализация вкладки задач"""
        # Панель управления задачами
        control_frame = ttk.Frame(self.task_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(control_frame, text="Добавить задачу", 
                  command=self.show_add_task_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="Обновить", 
                  command=self.refresh_tasks).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="Удалить выбранную", 
                  command=self.delete_selected_task).pack(side=tk.LEFT, padx=2)
        
        # Поле поиска
        search_frame = ttk.Frame(control_frame)
        search_frame.pack(side=tk.RIGHT, padx=2)
        ttk.Label(search_frame, text="Поиск:").pack(side=tk.LEFT)
        self.task_search_var = tk.StringVar()
        self.task_search_entry = ttk.Entry(search_frame, textvariable=self.task_search_var, width=20)
        self.task_search_entry.pack(side=tk.LEFT, padx=2)
        ttk.Button(search_frame, text="Найти", 
                  command=self.search_tasks).pack(side=tk.LEFT)
        
        # Создаем Treeview для отображения задач
        columns = ('id', 'title', 'project', 'assignee', 'priority', 'status', 'due_date')
        self.task_tree = ttk.Treeview(self.task_frame, columns=columns, show='headings', height=20)
        
        # Настройка колонок
        self.task_tree.heading('id', text='ID')
        self.task_tree.heading('title', text='Название')
        self.task_tree.heading('project', text='Проект')
        self.task_tree.heading('assignee', text='Исполнитель')
        self.task_tree.heading('priority', text='Приоритет')
        self.task_tree.heading('status', text='Статус')
        self.task_tree.heading('due_date', text='Срок')
        
        self.task_tree.column('id', width=50)
        self.task_tree.column('title', width=200)
        self.task_tree.column('project', width=150)
        self.task_tree.column('assignee', width=150)
        self.task_tree.column('priority', width=80)
        self.task_tree.column('status', width=100)
        self.task_tree.column('due_date', width=100)
        
        # Скроллбар
        task_scrollbar = ttk.Scrollbar(self.task_frame, orient=tk.VERTICAL, command=self.task_tree.yview)
        self.task_tree.configure(yscrollcommand=task_scrollbar.set)
        
        # Размещение
        self.task_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0), pady=5)
        task_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        
        # Двойной клик для редактирования
        self.task_tree.bind('<Double-Button-1>', self.edit_task)
    
    def init_project_tab(self) -> None:
        """Инициализация вкладки проектов"""
        # Панель управления проектами
        control_frame = ttk.Frame(self.project_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(control_frame, text="Добавить проект", 
                  command=self.show_add_project_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="Обновить", 
                  command=self.refresh_projects).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="Удалить выбранный", 
                  command=self.delete_selected_project).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="Показать задачи", 
                  command=self.show_project_tasks).pack(side=tk.LEFT, padx=2)
        
        # Создаем Treeview для отображения проектов
        columns = ('id', 'name', 'status', 'start_date', 'end_date', 'progress', 'tasks')
        self.project_tree = ttk.Treeview(self.project_frame, columns=columns, show='headings', height=20)
        
        # Настройка колонок
        self.project_tree.heading('id', text='ID')
        self.project_tree.heading('name', text='Название')
        self.project_tree.heading('status', text='Статус')
        self.project_tree.heading('start_date', text='Начало')
        self.project_tree.heading('end_date', text='Окончание')
        self.project_tree.heading('progress', text='Прогресс')
        self.project_tree.heading('tasks', text='Задачи')
        
        self.project_tree.column('id', width=50)
        self.project_tree.column('name', width=200)
        self.project_tree.column('status', width=100)
        self.project_tree.column('start_date', width=100)
        self.project_tree.column('end_date', width=100)
        self.project_tree.column('progress', width=80)
        self.project_tree.column('tasks', width=80)
        
        # Скроллбар
        project_scrollbar = ttk.Scrollbar(self.project_frame, orient=tk.VERTICAL, command=self.project_tree.yview)
        self.project_tree.configure(yscrollcommand=project_scrollbar.set)
        
        # Размещение
        self.project_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0), pady=5)
        project_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        
        # Двойной клик для редактирования
        self.project_tree.bind('<Double-Button-1>', self.edit_project)
    
    def init_user_tab(self) -> None:
        """Инициализация вкладки пользователей"""
        # Панель управления пользователями
        control_frame = ttk.Frame(self.user_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(control_frame, text="Добавить пользователя", 
                  command=self.show_add_user_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="Обновить", 
                  command=self.refresh_users).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="Удалить выбранного", 
                  command=self.delete_selected_user).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="Показать задачи", 
                  command=self.show_user_tasks).pack(side=tk.LEFT, padx=2)
        
        # Фильтр по ролям
        filter_frame = ttk.Frame(control_frame)
        filter_frame.pack(side=tk.RIGHT, padx=2)
        ttk.Label(filter_frame, text="Роль:").pack(side=tk.LEFT)
        self.role_filter_var = tk.StringVar(value="Все")
        role_combo = ttk.Combobox(filter_frame, textvariable=self.role_filter_var, 
                                 values=["Все", "admin", "manager", "developer"], 
                                 state="readonly", width=10)
        role_combo.pack(side=tk.LEFT, padx=2)
        role_combo.bind('<<ComboboxSelected>>', self.filter_users_by_role)
        
        # Создаем Treeview для отображения пользователей
        columns = ('id', 'username', 'email', 'role', 'reg_date', 'tasks')
        self.user_tree = ttk.Treeview(self.user_frame, columns=columns, show='headings', height=20)
        
        # Настройка колонок
        self.user_tree.heading('id', text='ID')
        self.user_tree.heading('username', text='Имя')
        self.user_tree.heading('email', text='Email')
        self.user_tree.heading('role', text='Роль')
        self.user_tree.heading('reg_date', text='Регистрация')
        self.user_tree.heading('tasks', text='Задачи')
        
        self.user_tree.column('id', width=50)
        self.user_tree.column('username', width=150)
        self.user_tree.column('email', width=200)
        self.user_tree.column('role', width=100)
        self.user_tree.column('reg_date', width=100)
        self.user_tree.column('tasks', width=80)
        
        # Скроллбар
        user_scrollbar = ttk.Scrollbar(self.user_frame, orient=tk.VERTICAL, command=self.user_tree.yview)
        self.user_tree.configure(yscrollcommand=user_scrollbar.set)
        
        # Размещение
        self.user_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0), pady=5)
        user_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        
        # Двойной клик для редактирования
        self.user_tree.bind('<Double-Button-1>', self.edit_user)
    
    # ========== Методы для работы с задачами ==========
    
    def refresh_tasks(self) -> None:
        """Обновить список задач"""
        # Очищаем дерево
        for item in self.task_tree.get_children():
            self.task_tree.delete(item)
        
        # Получаем все задачи
        tasks = self.task_controller.get_all_tasks()
        
        # Заполняем дерево
        for task in tasks:
            # Получаем название проекта
            project = self.project_controller.get_project(task.project_id)
            project_name = project.name if project else f"Проект {task.project_id}"
            
            # Получаем имя исполнителя
            user = self.user_controller.get_user(task.assignee_id)
            assignee_name = user.username if user else f"Пользователь {task.assignee_id}"
            
            # Определяем приоритет
            priority_names = {1: "Высокий", 2: "Средний", 3: "Низкий"}
            priority = priority_names.get(task.priority, "Неизвестно")
            
            # Форматируем дату
            due_date = task.due_date.strftime('%d.%m.%Y')
            
            # Добавляем пометку для просроченных задач
            status = task.status
            if task.is_overdue() and status != 'completed':
                status += " (⚠)"
            
            self.task_tree.insert('', tk.END, values=(
                task.id,
                task.title,
                project_name,
                assignee_name,
                priority,
                status,
                due_date
            ))
        
        self.update_status(f"Загружено {len(tasks)} задач")
    
    def search_tasks(self) -> None:
        """Поиск задач"""
        query = self.task_search_var.get().strip()
        if not query:
            messagebox.showwarning("Предупреждение", "Введите текст для поиска")
            return
        
        # Очищаем дерево
        for item in self.task_tree.get_children():
            self.task_tree.delete(item)
        
        # Выполняем поиск
        tasks = self.task_controller.search_tasks(query)
        
        # Заполняем дерево
        for task in tasks:
            project = self.project_controller.get_project(task.project_id)
            project_name = project.name if project else f"Проект {task.project_id}"
            
            user = self.user_controller.get_user(task.assignee_id)
            assignee_name = user.username if user else f"Пользователь {task.assignee_id}"
            
            priority_names = {1: "Высокий", 2: "Средний", 3: "Низкий"}
            priority = priority_names.get(task.priority, "Неизвестно")
            
            due_date = task.due_date.strftime('%d.%m.%Y')
            
            status = task.status
            if task.is_overdue() and status != 'completed':
                status += " (⚠)"
            
            self.task_tree.insert('', tk.END, values=(
                task.id,
                task.title,
                project_name,
                assignee_name,
                priority,
                status,
                due_date
            ))
        
        self.update_status(f"Найдено {len(tasks)} задач по запросу '{query}'")
    
    def show_add_task_dialog(self) -> None:
        """Показать диалог добавления задачи"""
        dialog = AddTaskDialog(self, self.task_controller, 
                              self.project_controller, self.user_controller)
        self.wait_window(dialog)
        if dialog.result:
            self.refresh_tasks()
    
    def edit_task(self, event) -> None:
        """Редактировать выбранную задачу"""
        selection = self.task_tree.selection()
        if not selection:
            return
        
        item = self.task_tree.item(selection[0])
        task_id = item['values'][0]
        
        task = self.task_controller.get_task(task_id)
        if task:
            dialog = EditTaskDialog(self, self.task_controller, 
                                   self.project_controller, self.user_controller, task)
            self.wait_window(dialog)
            if dialog.result:
                self.refresh_tasks()
    
    def delete_selected_task(self) -> None:
        """Удалить выбранную задачу"""
        selection = self.task_tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите задачу для удаления")
            return
        
        item = self.task_tree.item(selection[0])
        task_id = item['values'][0]
        task_title = item['values'][1]
        
        if messagebox.askyesno("Подтверждение", f"Удалить задачу '{task_title}'?"):
            success = self.task_controller.delete_task(task_id)
            if success:
                self.refresh_tasks()
                self.update_status(f"Задача '{task_title}' удалена")
            else:
                messagebox.showerror("Ошибка", "Не удалось удалить задачу")
    
    def show_overdue_tasks(self) -> None:
        """Показать просроченные задачи"""
        # Переключаемся на вкладку задач
        self.notebook.select(self.task_frame)
        
        # Очищаем дерево
        for item in self.task_tree.get_children():
            self.task_tree.delete(item)
        
        # Получаем просроченные задачи
        overdue_tasks = self.task_controller.get_overdue_tasks()
        
        # Заполняем дерево
        for task in overdue_tasks:
            project = self.project_controller.get_project(task.project_id)
            project_name = project.name if project else f"Проект {task.project_id}"
            
            user = self.user_controller.get_user(task.assignee_id)
            assignee_name = user.username if user else f"Пользователь {task.assignee_id}"
            
            priority_names = {1: "Высокий", 2: "Средний", 3: "Низкий"}
            priority = priority_names.get(task.priority, "Неизвестно")
            
            due_date = task.due_date.strftime('%d.%m.%Y')
            
            self.task_tree.insert('', tk.END, values=(
                task.id,
                task.title,
                project_name,
                assignee_name,
                priority,
                task.status + " (⚠)",
                due_date
            ))
        
        self.update_status(f"Найдено {len(overdue_tasks)} просроченных задач")
    
    def show_task_statistics(self) -> None:
        """Показать статистику задач"""
        stats = self.task_controller.get_task_statistics()
        
        message = f"""
Статистика задач:
----------------
Всего задач: {stats['total']}

По статусам:
  • Ожидание: {stats['by_status'].get('pending', 0)}
  • В работе: {stats['by_status'].get('in_progress', 0)}
  • Завершено: {stats['by_status'].get('completed', 0)}

По приоритетам:
  • Высокий: {stats['by_priority'].get('high', 0)}
  • Средний: {stats['by_priority'].get('medium', 0)}
  • Низкий: {stats['by_priority'].get('low', 0)}

Просроченных задач: {stats['overdue']}
        """
        
        messagebox.showinfo("Статистика задач", message)
    
    # ========== Методы для работы с проектами ==========
    
    def refresh_projects(self) -> None:
        """Обновить список проектов"""
        # Очищаем дерево
        for item in self.project_tree.get_children():
            self.project_tree.delete(item)
        
        # Получаем все проекты
        projects = self.project_controller.get_all_projects()
        
        # Заполняем дерево
        for project in projects:
            # Получаем задачи проекта
            tasks = self.task_controller.get_tasks_by_project(project.id)
            total_tasks = len(tasks)
            completed_tasks = sum(1 for task in tasks if task.status == 'completed')
            
            # Форматируем даты
            start_date = project.start_date.strftime('%d.%m.%Y')
            end_date = project.end_date.strftime('%d.%m.%Y')
            
            # Рассчитываем прогресс
            progress = project.get_progress() * 100
            
            # Определяем статус
            status_names = {'active': 'Активный', 'completed': 'Завершен', 'on_hold': 'Приостановлен'}
            status = status_names.get(project.status, project.status)
            
            # Добавляем пометку для просроченных проектов
            if hasattr(project, 'is_overdue') and project.is_overdue() and project.status != 'completed':
                status += " (⚠)"
            
            self.project_tree.insert('', tk.END, values=(
                project.id,
                project.name,
                status,
                start_date,
                end_date,
                f"{progress:.1f}%",
                f"{completed_tasks}/{total_tasks}"
            ))
        
        self.update_status(f"Загружено {len(projects)} проектов")
    
    def show_add_project_dialog(self) -> None:
        """Показать диалог добавления проекта"""
        dialog = AddProjectDialog(self, self.project_controller)
        self.wait_window(dialog)
        if dialog.result:
            self.refresh_projects()
    
    def edit_project(self, event) -> None:
        """Редактировать выбранный проект"""
        selection = self.project_tree.selection()
        if not selection:
            return
        
        item = self.project_tree.item(selection[0])
        project_id = item['values'][0]
        
        project = self.project_controller.get_project(project_id)
        if project:
            dialog = EditProjectDialog(self, self.project_controller, project)
            self.wait_window(dialog)
            if dialog.result:
                self.refresh_projects()
    
    def delete_selected_project(self) -> None:
        """Удалить выбранный проект"""
        selection = self.project_tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите проект для удаления")
            return
        
        item = self.project_tree.item(selection[0])
        project_id = item['values'][0]
        project_name = item['values'][1]
        
        if messagebox.askyesno("Подтверждение", f"Удалить проект '{project_name}'?\nВсе задачи проекта также будут удалены."):
            success = self.project_controller.delete_project(project_id)
            if success:
                self.refresh_projects()
                self.refresh_tasks()  # Обновляем задачи, так как некоторые могли быть удалены
                self.update_status(f"Проект '{project_name}' удален")
            else:
                messagebox.showerror("Ошибка", "Не удалось удалить проект")
    
    def show_project_tasks(self) -> None:
        """Показать задачи выбранного проекта"""
        selection = self.project_tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите проект")
            return
        
        item = self.project_tree.item(selection[0])
        project_id = item['values'][0]
        project_name = item['values'][1]
        
        # Переключаемся на вкладку задач
        self.notebook.select(self.task_frame)
        
        # Очищаем дерево
        for item in self.task_tree.get_children():
            self.task_tree.delete(item)
        
        # Получаем задачи проекта
        tasks = self.task_controller.get_tasks_by_project(project_id)
        
        # Заполняем дерево
        for task in tasks:
            user = self.user_controller.get_user(task.assignee_id)
            assignee_name = user.username if user else f"Пользователь {task.assignee_id}"
            
            priority_names = {1: "Высокий", 2: "Средний", 3: "Низкий"}
            priority = priority_names.get(task.priority, "Неизвестно")
            
            due_date = task.due_date.strftime('%d.%m.%Y')
            
            status = task.status
            if task.is_overdue() and status != 'completed':
                status += " (⚠)"
            
            self.task_tree.insert('', tk.END, values=(
                task.id,
                task.title,
                project_name,
                assignee_name,
                priority,
                status,
                due_date
            ))
        
        self.update_status(f"Найдено {len(tasks)} задач в проекте '{project_name}'")
    
    def show_active_projects(self) -> None:
        """Показать активные проекты"""
        # Переключаемся на вкладку проектов
        self.notebook.select(self.project_frame)
        
        # Очищаем дерево
        for item in self.project_tree.get_children():
            self.project_tree.delete(item)
        
        # Получаем активные проекты
        active_projects = self.project_controller.get_active_projects()
        
        # Заполняем дерево
        for project in active_projects:
            tasks = self.task_controller.get_tasks_by_project(project.id)
            total_tasks = len(tasks)
            completed_tasks = sum(1 for task in tasks if task.status == 'completed')
            
            start_date = project.start_date.strftime('%d.%m.%Y')
            end_date = project.end_date.strftime('%d.%m.%Y')
            progress = project.get_progress() * 100
            
            status = "Активный"
            if hasattr(project, 'is_overdue') and project.is_overdue():
                status += " (⚠)"
            
            self.project_tree.insert('', tk.END, values=(
                project.id,
                project.name,
                status,
                start_date,
                end_date,
                f"{progress:.1f}%",
                f"{completed_tasks}/{total_tasks}"
            ))
        
        self.update_status(f"Найдено {len(active_projects)} активных проектов")
    
    def show_overdue_projects(self) -> None:
        """Показать просроченные проекты"""
        # Переключаемся на вкладку проектов
        self.notebook.select(self.project_frame)
        
        # Очищаем дерево
        for item in self.project_tree.get_children():
            self.project_tree.delete(item)
        
        # Получаем просроченные проекты
        overdue_projects = self.project_controller.get_overdue_projects()
        
        # Заполняем дерево
        for project in overdue_projects:
            tasks = self.task_controller.get_tasks_by_project(project.id)
            total_tasks = len(tasks)
            completed_tasks = sum(1 for task in tasks if task.status == 'completed')
            
            start_date = project.start_date.strftime('%d.%m.%Y')
            end_date = project.end_date.strftime('%d.%m.%Y')
            progress = project.get_progress() * 100
            
            status_names = {'active': 'Активный', 'completed': 'Завершен', 'on_hold': 'Приостановлен'}
            status = status_names.get(project.status, project.status) + " (⚠)"
            
            self.project_tree.insert('', tk.END, values=(
                project.id,
                project.name,
                status,
                start_date,
                end_date,
                f"{progress:.1f}%",
                f"{completed_tasks}/{total_tasks}"
            ))
        
        self.update_status(f"Найдено {len(overdue_projects)} просроченных проектов")
    
    def show_project_statistics(self) -> None:
        """Показать статистику проектов"""
        projects = self.project_controller.get_all_projects()
        
        if not projects:
            messagebox.showinfo("Статистика проектов", "Нет проектов для отображения статистики")
            return
        
        # Собираем статистику
        total_projects = len(projects)
        active_projects = sum(1 for p in projects if p.status == 'active')
        completed_projects = sum(1 for p in projects if p.status == 'completed')
        on_hold_projects = sum(1 for p in projects if p.status == 'on_hold')
        overdue_projects = sum(1 for p in projects if hasattr(p, 'is_overdue') and p.is_overdue() and p.status != 'completed')
        
        # Считаем средний прогресс
        total_progress = sum(p.get_progress() * 100 for p in projects)
        avg_progress = total_progress / total_projects if total_projects > 0 else 0
        
        message = f"""
Статистика проектов:
-------------------
Всего проектов: {total_projects}

По статусам:
  • Активные: {active_projects}
  • Завершенные: {completed_projects}
  • Приостановленные: {on_hold_projects}

Просроченных проектов: {overdue_projects}

Средний прогресс: {avg_progress:.1f}%
        """
        
        messagebox.showinfo("Статистика проектов", message)
    
    # ========== Методы для работы с пользователями ==========
    
    def refresh_users(self) -> None:
        """Обновить список пользователей"""
        # Очищаем дерево
        for item in self.user_tree.get_children():
            self.user_tree.delete(item)
        
        # Получаем всех пользователей
        users = self.user_controller.get_all_users()
        
        # Фильтруем по роли если нужно
        role_filter = self.role_filter_var.get()
        if role_filter != "Все":
            users = [user for user in users if user.role == role_filter]
        
        # Заполняем дерево
        for user in users:
            # Получаем задачи пользователя
            tasks = self.user_controller.get_user_tasks(user.id)
            total_tasks = len(tasks)
            
            # Форматируем дату
            reg_date = user.registration_date.strftime('%d.%m.%Y')
            
            # Определяем роль
            role_names = {'admin': 'Администратор', 'manager': 'Менеджер', 'developer': 'Разработчик'}
            role = role_names.get(user.role, user.role)
            
            self.user_tree.insert('', tk.END, values=(
                user.id,
                user.username,
                user.email,
                role,
                reg_date,
                total_tasks
            ))
        
        self.update_status(f"Загружено {len(users)} пользователей")
    
    def filter_users_by_role(self, event=None) -> None:
        """Фильтровать пользователей по роли"""
        self.refresh_users()
    
    def show_add_user_dialog(self) -> None:
        """Показать диалог добавления пользователя"""
        dialog = AddUserDialog(self, self.user_controller)
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
            dialog = EditUserDialog(self, self.user_controller, user)
            self.wait_window(dialog)
            if dialog.result:
                self.refresh_users()
    
    def delete_selected_user(self) -> None:
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
                self.refresh_tasks()  # Обновляем задачи
                self.update_status(f"Пользователь '{username}' удален")
            else:
                messagebox.showerror("Ошибка", "Не удалось удалить пользователя. Возможно у него есть задачи.")
    
    def show_user_tasks(self) -> None:
        """Показать задачи выбранного пользователя"""
        selection = self.user_tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите пользователя")
            return
        
        item = self.user_tree.item(selection[0])
        user_id = item['values'][0]
        username = item['values'][1]
        
        # Переключаемся на вкладку задач
        self.notebook.select(self.task_frame)
        
        # Очищаем дерево
        for item in self.task_tree.get_children():
            self.task_tree.delete(item)
        
        # Получаем задачи пользователя
        tasks = self.user_controller.get_user_tasks(user_id)
        
        # Заполняем дерево
        for task in tasks:
            project = self.project_controller.get_project(task.project_id)
            project_name = project.name if project else f"Проект {task.project_id}"
            
            priority_names = {1: "Высокий", 2: "Средний", 3: "Низкий"}
            priority = priority_names.get(task.priority, "Неизвестно")
            
            due_date = task.due_date.strftime('%d.%m.%Y')
            
            status = task.status
            if task.is_overdue() and status != 'completed':
                status += " (⚠)"
            
            self.task_tree.insert('', tk.END, values=(
                task.id,
                task.title,
                project_name,
                username,
                priority,
                status,
                due_date
            ))
        
        self.update_status(f"Найдено {len(tasks)} задач пользователя '{username}'")
    
    def show_developers(self) -> None:
        """Показать всех разработчиков"""
        # Переключаемся на вкладку пользователей
        self.notebook.select(self.user_frame)
        
        # Устанавливаем фильтр
        self.role_filter_var.set("developer")
        self.refresh_users()
    
    def show_managers(self) -> None:
        """Показать всех менеджеров"""
        # Переключаемся на вкладку пользователей
        self.notebook.select(self.user_frame)
        
        # Устанавливаем фильтр
        self.role_filter_var.set("manager")
        self.refresh_users()
    
    def show_user_statistics(self) -> None:
        """Показать статистику пользователей"""
        users = self.user_controller.get_all_users()
        
        if not users:
            messagebox.showinfo("Статистика пользователей", "Нет пользователей для отображения статистики")
            return
        
        # Собираем статистику
        total_users = len(users)
        admins = sum(1 for u in users if u.role == 'admin')
        managers = sum(1 for u in users if u.role == 'manager')
        developers = sum(1 for u in users if u.role == 'developer')
        
        # Считаем среднее количество дней с регистрации
        if hasattr(users[0], 'get_days_since_registration'):
            total_days = sum(u.get_days_since_registration() for u in users)
            avg_days = total_days / total_users if total_users > 0 else 0
            days_str = f"\nСреднее время в системе: {avg_days:.1f} дней"
        else:
            days_str = ""
        
        message = f"""
Статистика пользователей:
------------------------
Всего пользователей: {total_users}

По ролям:
  • Администраторы: {admins}
  • Менеджеры: {managers}
  • Разработчики: {developers}
{days_str}
        """
        
        messagebox.showinfo("Статистика пользователей", message)
    
    # ========== Общие методы ==========
    
    def refresh_all(self) -> None:
        """Обновить все данные"""
        self.refresh_tasks()
        self.refresh_projects()
        self.refresh_users()
        self.update_status("Все данные обновлены")
    
    def update_status(self, message: str) -> None:
        """Обновить статус бар"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_bar.config(text=f"[{timestamp}] {message}")
    
    def show_about(self) -> None:
        """Показать информацию о программе"""
        messagebox.showinfo("О программе", 
                          "Система управления задачами\n\n"
                          "Версия 1.0\n"
                          "Архитектура MVC\n"
                          "Python 3.8+, SQLite, Tkinter")
    
    def run(self) -> None:
        """Запустить главное окно"""
        self.mainloop()


# ========== Диалоговые окна ==========

class AddTaskDialog(tk.Toplevel):
    """Диалог добавления новой задачи"""
    
    def __init__(self, parent, task_controller, project_controller, user_controller):
        super().__init__(parent)
        self.task_controller = task_controller
        self.project_controller = project_controller
        self.user_controller = user_controller
        self.result = False
        
        self.setup_dialog()
        self.create_widgets()
    
    def setup_dialog(self):
        self.title("Добавить задачу")
        self.geometry("500x400")
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
        
        # Название
        ttk.Label(main_frame, text="Название задачи:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.title_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.title_var, width=40).grid(row=0, column=1, pady=5, padx=(5, 0))
        
        # Описание
        ttk.Label(main_frame, text="Описание:").grid(row=1, column=0, sticky=tk.NW, pady=5)
        self.description_text = tk.Text(main_frame, width=40, height=5)
        self.description_text.grid(row=1, column=1, pady=5, padx=(5, 0))
        
        # Приоритет
        ttk.Label(main_frame, text="Приоритет:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.priority_var = tk.IntVar(value=2)
        ttk.Combobox(main_frame, textvariable=self.priority_var, 
                    values=[1, 2, 3], state="readonly", width=10).grid(row=2, column=1, sticky=tk.W, pady=5, padx=(5, 0))
        
        # Проект
        ttk.Label(main_frame, text="Проект:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.project_var = tk.StringVar()
        projects = self.project_controller.get_all_projects()
        project_names = [p.name for p in projects]
        self.project_combo = ttk.Combobox(main_frame, textvariable=self.project_var, 
                                         values=project_names, state="readonly", width=37)
        self.project_combo.grid(row=3, column=1, sticky=tk.W, pady=5, padx=(5, 0))
        
        # Исполнитель
        ttk.Label(main_frame, text="Исполнитель:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.assignee_var = tk.StringVar()
        users = self.user_controller.get_all_users()
        user_names = [u.username for u in users]
        self.assignee_combo = ttk.Combobox(main_frame, textvariable=self.assignee_var, 
                                          values=user_names, state="readonly", width=37)
        self.assignee_combo.grid(row=4, column=1, sticky=tk.W, pady=5, padx=(5, 0))
        
        # Срок
        ttk.Label(main_frame, text="Срок (дд.мм.гггг):").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.due_date_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.due_date_var, width=15).grid(row=5, column=1, sticky=tk.W, pady=5, padx=(5, 0))
        
        # Кнопки
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="Добавить", command=self.add_task).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Отмена", command=self.destroy).pack(side=tk.LEFT, padx=5)
    
    def add_task(self):
        # Валидация данных
        title = self.title_var.get().strip()
        if not title:
            messagebox.showerror("Ошибка", "Введите название задачи")
            return
        
        description = self.description_text.get("1.0", tk.END).strip()
        if not description:
            messagebox.showerror("Ошибка", "Введите описание задачи")
            return
        
        priority = self.priority_var.get()
        if priority not in [1, 2, 3]:
            messagebox.showerror("Ошибка", "Выберите приоритет (1-3)")
            return
        
        project_name = self.project_var.get()
        if not project_name:
            messagebox.showerror("Ошибка", "Выберите проект")
            return
        
        assignee_name = self.assignee_var.get()
        if not assignee_name:
            messagebox.showerror("Ошибка", "Выберите исполнителя")
            return
        
        due_date_str = self.due_date_var.get().strip()
        if not due_date_str:
            messagebox.showerror("Ошибка", "Введите срок выполнения")
            return
        
        # Парсинг даты
        try:
            due_date = datetime.strptime(due_date_str, "%d.%m.%Y")
        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат даты. Используйте дд.мм.гггг")
            return
        
        # Получаем ID проекта и пользователя
        projects = self.project_controller.get_all_projects()
        project_id = None
        for p in projects:
            if p.name == project_name:
                project_id = p.id
                break
        
        users = self.user_controller.get_all_users()
        assignee_id = None
        for u in users:
            if u.username == assignee_name:
                assignee_id = u.id
                break
        
        if not project_id or not assignee_id:
            messagebox.showerror("Ошибка", "Не удалось найти проект или пользователя")
            return
        
        # Добавляем задачу
        task_id = self.task_controller.add_task(title, description, priority, due_date, project_id, assignee_id)
        
        if task_id > 0:
            self.result = True
            messagebox.showinfo("Успех", f"Задача добавлена с ID {task_id}")
            self.destroy()
        else:
            messagebox.showerror("Ошибка", "Не удалось добавить задачу")


class EditTaskDialog(AddTaskDialog):
    """Диалог редактирования задачи"""
    
    def __init__(self, parent, task_controller, project_controller, user_controller, task):
        self.task = task
        super().__init__(parent, task_controller, project_controller, user_controller)
        self.title("Редактировать задачу")
        self.load_task_data()
    
    def load_task_data(self):
        # Заполняем поля данными задачи
        self.title_var.set(self.task.title)
        self.description_text.delete("1.0", tk.END)
        self.description_text.insert("1.0", self.task.description)
        self.priority_var.set(self.task.priority)
        
        # Устанавливаем проект
        project = self.project_controller.get_project(self.task.project_id)
        if project:
            self.project_var.set(project.name)
        
        # Устанавливаем исполнителя
        user = self.user_controller.get_user(self.task.assignee_id)
        if user:
            self.assignee_var.set(user.username)
        
        # Устанавливаем дату
        self.due_date_var.set(self.task.due_date.strftime("%d.%m.%Y"))
    
    def add_task(self):
        # Переопределяем для обновления задачи
        title = self.title_var.get().strip()
        if not title:
            messagebox.showerror("Ошибка", "Введите название задачи")
            return
        
        description = self.description_text.get("1.0", tk.END).strip()
        if not description:
            messagebox.showerror("Ошибка", "Введите описание задачи")
            return
        
        priority = self.priority_var.get()
        if priority not in [1, 2, 3]:
            messagebox.showerror("Ошибка", "Выберите приоритет (1-3)")
            return
        
        project_name = self.project_var.get()
        if not project_name:
            messagebox.showerror("Ошибка", "Выберите проект")
            return
        
        assignee_name = self.assignee_var.get()
        if not assignee_name:
            messagebox.showerror("Ошибка", "Выберите исполнителя")
            return
        
        due_date_str = self.due_date_var.get().strip()
        if not due_date_str:
            messagebox.showerror("Ошибка", "Введите срок выполнения")
            return
        
        # Парсинг даты
        try:
            due_date = datetime.strptime(due_date_str, "%d.%m.%Y")
        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат даты. Используйте дд.мм.гггг")
            return
        
        # Получаем ID проекта и пользователя
        projects = self.project_controller.get_all_projects()
        project_id = None
        for p in projects:
            if p.name == project_name:
                project_id = p.id
                break
        
        users = self.user_controller.get_all_users()
        assignee_id = None
        for u in users:
            if u.username == assignee_name:
                assignee_id = u.id
                break
        
        if not project_id or not assignee_id:
            messagebox.showerror("Ошибка", "Не удалось найти проект или пользователя")
            return
        
        # Обновляем задачу
        success = self.task_controller.update_task(
            self.task.id,
            title=title,
            description=description,
            priority=priority,
            due_date=due_date,
            project_id=project_id,
            assignee_id=assignee_id
        )
        
        if success:
            self.result = True
            messagebox.showinfo("Успех", "Задача обновлена")
            self.destroy()
        else:
            messagebox.showerror("Ошибка", "Не удалось обновить задачу")


class AddProjectDialog(tk.Toplevel):
    """Диалог добавления нового проекта"""
    
    def __init__(self, parent, project_controller):
        super().__init__(parent)
        self.project_controller = project_controller
        self.result = False
        
        self.setup_dialog()
        self.create_widgets()
    
    def setup_dialog(self):
        self.title("Добавить проект")
        self.geometry("400x300")
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
        
        # Название
        ttk.Label(main_frame, text="Название проекта:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.name_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.name_var, width=30).grid(row=0, column=1, pady=5, padx=(5, 0))
        
        # Описание
        ttk.Label(main_frame, text="Описание:").grid(row=1, column=0, sticky=tk.NW, pady=5)
        self.description_text = tk.Text(main_frame, width=30, height=4)
        self.description_text.grid(row=1, column=1, pady=5, padx=(5, 0))
        
        # Дата начала
        ttk.Label(main_frame, text="Дата начала (дд.мм.гггг):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.start_date_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.start_date_var, width=15).grid(row=2, column=1, sticky=tk.W, pady=5, padx=(5, 0))
        
        # Дата окончания
        ttk.Label(main_frame, text="Дата окончания (дд.мм.гггг):").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.end_date_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.end_date_var, width=15).grid(row=3, column=1, sticky=tk.W, pady=5, padx=(5, 0))
        
        # Кнопки
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="Добавить", command=self.add_project).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Отмена", command=self.destroy).pack(side=tk.LEFT, padx=5)
    
    def add_project(self):
        # Валидация данных
        name = self.name_var.get().strip()
        if not name:
            messagebox.showerror("Ошибка", "Введите название проекта")
            return
        
        description = self.description_text.get("1.0", tk.END).strip()
        if not description:
            messagebox.showerror("Ошибка", "Введите описание проекта")
            return
        
        start_date_str = self.start_date_var.get().strip()
        if not start_date_str:
            messagebox.showerror("Ошибка", "Введите дату начала")
            return
        
        end_date_str = self.end_date_var.get().strip()
        if not end_date_str:
            messagebox.showerror("Ошибка", "Введите дату окончания")
            return
        
        # Парсинг дат
        try:
            start_date = datetime.strptime(start_date_str, "%d.%m.%Y")
        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат даты начала. Используйте дд.мм.гггг")
            return
        
        try:
            end_date = datetime.strptime(end_date_str, "%d.%m.%Y")
        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат даты окончания. Используйте дд.мм.гггг")
            return
        
        # Проверяем что дата окончания позже даты начала
        if end_date <= start_date:
            messagebox.showerror("Ошибка", "Дата окончания должна быть позже даты начала")
            return
        
        # Добавляем проект
        project_id = self.project_controller.add_project(name, description, start_date, end_date)
        
        if project_id > 0:
            self.result = True
            messagebox.showinfo("Успех", f"Проект добавлен с ID {project_id}")
            self.destroy()
        else:
            messagebox.showerror("Ошибка", "Не удалось добавить проект")


class EditProjectDialog(AddProjectDialog):
    """Диалог редактирования проекта"""
    
    def __init__(self, parent, project_controller, project):
        self.project = project
        super().__init__(parent, project_controller)
        self.title("Редактировать проект")
        self.load_project_data()
    
    def load_project_data(self):
        # Заполняем поля данными проекта
        self.name_var.set(self.project.name)
        self.description_text.delete("1.0", tk.END)
        self.description_text.insert("1.0", self.project.description)
        self.start_date_var.set(self.project.start_date.strftime("%d.%m.%Y"))
        self.end_date_var.set(self.project.end_date.strftime("%d.%m.%Y"))
    
    def add_project(self):
        # Переопределяем для обновления проекта
        name = self.name_var.get().strip()
        if not name:
            messagebox.showerror("Ошибка", "Введите название проекта")
            return
        
        description = self.description_text.get("1.0", tk.END).strip()
        if not description:
            messagebox.showerror("Ошибка", "Введите описание проекта")
            return
        
        start_date_str = self.start_date_var.get().strip()
        if not start_date_str:
            messagebox.showerror("Ошибка", "Введите дату начала")
            return
        
        end_date_str = self.end_date_var.get().strip()
        if not end_date_str:
            messagebox.showerror("Ошибка", "Введите дату окончания")
            return
        
        # Парсинг дат
        try:
            start_date = datetime.strptime(start_date_str, "%d.%m.%Y")
        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат даты начала. Используйте дд.мм.гггг")
            return
        
        try:
            end_date = datetime.strptime(end_date_str, "%d.%m.%Y")
        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат даты окончания. Используйте дд.мм.гггг")
            return
        
        # Проверяем что дата окончания позже даты начала
        if end_date <= start_date:
            messagebox.showerror("Ошибка", "Дата окончания должна быть позже даты начала")
            return
        
        # Обновляем проект
        success = self.project_controller.update_project(
            self.project.id,
            name=name,
            description=description,
            start_date=start_date,
            end_date=end_date
        )
        
        if success:
            self.result = True
            messagebox.showinfo("Успех", "Проект обновлен")
            self.destroy()
        else:
            messagebox.showerror("Ошибка", "Не удалось обновить проект")


class AddUserDialog(tk.Toplevel):
    """Диалог добавления нового пользователя"""
    
    def __init__(self, parent, user_controller):
        super().__init__(parent)
        self.user_controller = user_controller
        self.result = False
        
        self.setup_dialog()
        self.create_widgets()
    
    def setup_dialog(self):
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
        ttk.Label(main_frame, text="Имя пользователя:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.username_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.username_var, width=25).grid(row=0, column=1, pady=5, padx=(5, 0))
        
        # Email
        ttk.Label(main_frame, text="Email:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.email_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.email_var, width=25).grid(row=1, column=1, pady=5, padx=(5, 0))
        
        # Роль
        ttk.Label(main_frame, text="Роль:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.role_var = tk.StringVar(value="developer")
        ttk.Combobox(main_frame, textvariable=self.role_var, 
                    values=["admin", "manager", "developer"], 
                    state="readonly", width=15).grid(row=2, column=1, sticky=tk.W, pady=5, padx=(5, 0))
        
        # Кнопки
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="Добавить", command=self.add_user).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Отмена", command=self.destroy).pack(side=tk.LEFT, padx=5)
    
    def add_user(self):
        # Валидация данных
        username = self.username_var.get().strip()
        if not username:
            messagebox.showerror("Ошибка", "Введите имя пользователя")
            return
        
        email = self.email_var.get().strip()
        if not email:
            messagebox.showerror("Ошибка", "Введите email")
            return
        
        role = self.role_var.get()
        if role not in ["admin", "manager", "developer"]:
            messagebox.showerror("Ошибка", "Выберите роль")
            return
        
        # Добавляем пользователя
        user_id = self.user_controller.add_user(username, email, role)
        
        if user_id > 0:
            self.result = True
            messagebox.showinfo("Успех", f"Пользователь добавлен с ID {user_id}")
            self.destroy()
        else:
            messagebox.showerror("Ошибка", "Не удалось добавить пользователя")


class EditUserDialog(AddUserDialog):
    """Диалог редактирования пользователя"""
    
    def __init__(self, parent, user_controller, user):
        self.user = user
        super().__init__(parent, user_controller)
        self.title("Редактировать пользователя")
        self.load_user_data()
    
    def load_user_data(self):
        # Заполняем поля данными пользователя
        self.username_var.set(self.user.username)
        self.email_var.set(self.user.email)
        self.role_var.set(self.user.role)
    
    def add_user(self):
        # Переопределяем для обновления пользователя
        username = self.username_var.get().strip()
        if not username:
            messagebox.showerror("Ошибка", "Введите имя пользователя")
            return
        
        email = self.email_var.get().strip()
        if not email:
            messagebox.showerror("Ошибка", "Введите email")
            return
        
        role = self.role_var.get()
        if role not in ["admin", "manager", "developer"]:
            messagebox.showerror("Ошибка", "Выберите роль")
            return
        
        # Обновляем пользователя
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
