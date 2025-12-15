import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime


class TaskView(ttk.Frame):
    def __init__(self, parent, task_controller, project_controller, user_controller) -> None:
        super().__init__(parent)
        
        self.task_controller = task_controller
        self.project_controller = project_controller
        self.user_controller = user_controller
        
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
        ttk.Button(control_frame, text="Добавить задачу", 
                  command=self.add_task).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="Обновить", 
                  command=self.refresh_tasks).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="Удалить выбранную", 
                  command=self.delete_selected).pack(side=tk.LEFT, padx=2)
        
        # Панель фильтров и поиска
        filter_frame = ttk.Frame(control_frame)
        filter_frame.pack(side=tk.RIGHT, padx=2)
        
        # Поиск
        ttk.Label(filter_frame, text="Поиск:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(filter_frame, textvariable=self.search_var, width=20)
        search_entry.pack(side=tk.LEFT, padx=2)
        ttk.Button(filter_frame, text="Найти", 
                  command=self.search_tasks).pack(side=tk.LEFT, padx=2)
        
        # Фильтр по статусу
        ttk.Label(filter_frame, text="Статус:").pack(side=tk.LEFT, padx=(10, 2))
        self.status_filter_var = tk.StringVar(value="Все")
        status_combo = ttk.Combobox(filter_frame, textvariable=self.status_filter_var, 
                                   values=["Все", "pending", "in_progress", "completed"], 
                                   state="readonly", width=12)
        status_combo.pack(side=tk.LEFT, padx=2)
        status_combo.bind('<<ComboboxSelected>>', self.filter_tasks)
        
        # Фильтр по приоритету
        ttk.Label(filter_frame, text="Приоритет:").pack(side=tk.LEFT, padx=(10, 2))
        self.priority_filter_var = tk.StringVar(value="Все")
        priority_combo = ttk.Combobox(filter_frame, textvariable=self.priority_filter_var, 
                                     values=["Все", "Высокий", "Средний", "Низкий"], 
                                     state="readonly", width=10)
        priority_combo.pack(side=tk.LEFT, padx=2)
        priority_combo.bind('<<ComboboxSelected>>', self.filter_tasks)
        
        # Таблица задач
        columns = ('id', 'title', 'project', 'assignee', 'priority', 'status', 'due_date')
        self.task_tree = ttk.Treeview(self, columns=columns, show='headings', height=20)
        
        # Настройка колонок
        self.task_tree.heading('id', text='ID')
        self.task_tree.heading('title', text='Название')
        self.task_tree.heading('project', text='Проект')
        self.task_tree.heading('assignee', text='Исполнитель')
        self.task_tree.heading('priority', text='Приоритет')
        self.task_tree.heading('status', text='Статус')
        self.task_tree.heading('due_date', text='Срок')
        
        self.task_tree.column('id', width=50, anchor=tk.CENTER)
        self.task_tree.column('title', width=200)
        self.task_tree.column('project', width=150)
        self.task_tree.column('assignee', width=150)
        self.task_tree.column('priority', width=80, anchor=tk.CENTER)
        self.task_tree.column('status', width=100, anchor=tk.CENTER)
        self.task_tree.column('due_date', width=100, anchor=tk.CENTER)
        
        # Скроллбар
        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.task_tree.yview)
        self.task_tree.configure(yscrollcommand=scrollbar.set)
        
        # Размещение
        self.task_tree.grid(row=1, column=0, sticky=tk.NSEW, padx=(0, 5))
        scrollbar.grid(row=1, column=1, sticky=tk.NS)
        
        # Двойной клик для редактирования
        self.task_tree.bind('<Double-Button-1>', self.edit_task)
        
        # Статистика
        stats_frame = ttk.Frame(self)
        stats_frame.grid(row=2, column=0, columnspan=2, sticky=tk.EW, pady=(10, 0))
        
        self.stats_label = ttk.Label(stats_frame, text="Всего задач: 0")
        self.stats_label.pack(side=tk.LEFT)
        
        # Инициализация данных
        self.all_tasks = []
        self.refresh_tasks()
    
    def refresh_tasks(self) -> None:
        """Обновить список задач"""
        # Очищаем дерево
        for item in self.task_tree.get_children():
            self.task_tree.delete(item)
        
        # Получаем все задачи
        self.all_tasks = self.task_controller.get_all_tasks()
        
        # Применяем фильтры
        filtered_tasks = self.apply_filters(self.all_tasks)
        
        # Заполняем дерево
        for task in filtered_tasks:
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
        
        # Обновляем статистику
        self.update_stats(filtered_tasks)
    
    def apply_filters(self, tasks):
        """Применить фильтры к списку задач"""
        filtered_tasks = tasks
        
        # Фильтр по статусу
        status_filter = self.status_filter_var.get()
        if status_filter != "Все":
            filtered_tasks = [t for t in filtered_tasks if t.status == status_filter]
        
        # Фильтр по приоритету
        priority_filter = self.priority_filter_var.get()
        if priority_filter != "Все":
            priority_map = {"Высокий": 1, "Средний": 2, "Низкий": 3}
            priority_value = priority_map.get(priority_filter)
            if priority_value:
                filtered_tasks = [t for t in filtered_tasks if t.priority == priority_value]
        
        return filtered_tasks
    
    def update_stats(self, tasks):
        """Обновить статистику"""
        total_tasks = len(tasks)
        overdue_tasks = sum(1 for t in tasks if t.is_overdue() and t.status != 'completed')
        
        self.stats_label.config(
            text=f"Всего задач: {total_tasks} | Просрочено: {overdue_tasks}"
        )
    
    def search_tasks(self) -> None:
        """Поиск задач"""
        query = self.search_var.get().strip()
        if not query:
            messagebox.showwarning("Предупреждение", "Введите текст для поиска")
            return
        
        # Очищаем дерево
        for item in self.task_tree.get_children():
            self.task_tree.delete(item)
        
        # Выполняем поиск
        tasks = self.task_controller.search_tasks(query)
        
        # Применяем фильтры к результатам поиска
        filtered_tasks = self.apply_filters(tasks)
        
        # Заполняем дерево
        for task in filtered_tasks:
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
        
        self.update_stats(filtered_tasks)
        messagebox.showinfo("Поиск", f"Найдено {len(filtered_tasks)} задач")
    
    def filter_tasks(self, event=None) -> None:
        """Фильтровать задачи"""
        self.refresh_tasks()
    
    def add_task(self) -> None:
        """Добавить новую задачу"""
        dialog = TaskDialog(self, self.task_controller, 
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
            dialog = TaskDialog(self, self.task_controller, 
                               self.project_controller, self.user_controller, task)
            self.wait_window(dialog)
            if dialog.result:
                self.refresh_tasks()
    
    def delete_selected(self) -> None:
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
                messagebox.showinfo("Успех", f"Задача '{task_title}' удалена")
            else:
                messagebox.showerror("Ошибка", "Не удалось удалить задачу")
    
    def show_overdue_tasks(self) -> None:
        """Показать только просроченные задачи"""
        # Устанавливаем фильтр статуса на "Все" чтобы видеть все просроченные
        self.status_filter_var.set("Все")
        
        # Очищаем дерево
        for item in self.task_tree.get_children():
            self.task_tree.delete(item)
        
        # Получаем все задачи и фильтруем просроченные
        all_tasks = self.task_controller.get_all_tasks()
        overdue_tasks = [t for t in all_tasks if t.is_overdue() and t.status != 'completed']
        
        # Применяем другие фильтры
        filtered_tasks = self.apply_filters(overdue_tasks)
        
        # Заполняем дерево
        for task in filtered_tasks:
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
        
        self.update_stats(filtered_tasks)


class TaskDialog(tk.Toplevel):
    """Диалог для добавления/редактирования задачи"""
    
    def __init__(self, parent, task_controller, project_controller, user_controller, task=None):
        super().__init__(parent)
        self.task_controller = task_controller
        self.project_controller = project_controller
        self.user_controller = user_controller
        self.task = task  # Если None - добавление, иначе - редактирование
        self.result = False
        
        self.setup_dialog()
        self.create_widgets()
        
        if task:
            self.load_task_data()
    
    def setup_dialog(self):
        if self.task:
            self.title("Редактировать задачу")
        else:
            self.title("Добавить задачу")
        
        self.geometry("500x450")
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
        ttk.Label(main_frame, text="Название задачи:*").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.title_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.title_var, width=40).grid(row=0, column=1, pady=5, padx=(5, 0))
        
        # Описание
        ttk.Label(main_frame, text="Описание:*").grid(row=1, column=0, sticky=tk.NW, pady=5)
        self.description_text = tk.Text(main_frame, width=40, height=5)
        self.description_text.grid(row=1, column=1, pady=5, padx=(5, 0))
        
        # Приоритет
        ttk.Label(main_frame, text="Приоритет:*").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.priority_var = tk.IntVar(value=2)
        priority_combo = ttk.Combobox(main_frame, textvariable=self.priority_var, 
                                     values=[1, 2, 3], state="readonly", width=10)
        priority_combo.grid(row=2, column=1, sticky=tk.W, pady=5, padx=(5, 0))
        
        # Проект
        ttk.Label(main_frame, text="Проект:*").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.project_var = tk.StringVar()
        
        # Получаем список проектов
        projects = self.project_controller.get_all_projects()
        project_names = [p.name for p in projects]
        self.project_combo = ttk.Combobox(main_frame, textvariable=self.project_var, 
                                         values=project_names, state="readonly", width=37)
        self.project_combo.grid(row=3, column=1, sticky=tk.W, pady=5, padx=(5, 0))
        
        # Исполнитель
        ttk.Label(main_frame, text="Исполнитель:*").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.assignee_var = tk.StringVar()
        
        # Получаем список пользователей
        users = self.user_controller.get_all_users()
        user_names = [u.username for u in users]
        self.assignee_combo = ttk.Combobox(main_frame, textvariable=self.assignee_var, 
                                          values=user_names, state="readonly", width=37)
        self.assignee_combo.grid(row=4, column=1, sticky=tk.W, pady=5, padx=(5, 0))
        
        # Статус
        ttk.Label(main_frame, text="Статус:*").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.status_var = tk.StringVar(value="pending")
        status_combo = ttk.Combobox(main_frame, textvariable=self.status_var, 
                                   values=["pending", "in_progress", "completed"], 
                                   state="readonly", width=15)
        status_combo.grid(row=5, column=1, sticky=tk.W, pady=5, padx=(5, 0))
        
        # Срок
        ttk.Label(main_frame, text="Срок (дд.мм.гггг):*").grid(row=6, column=0, sticky=tk.W, pady=5)
        self.due_date_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.due_date_var, width=15).grid(row=6, column=1, sticky=tk.W, pady=5, padx=(5, 0))
        
        # Кнопки
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=7, column=0, columnspan=2, pady=20)
        
        if self.task:
            ttk.Button(button_frame, text="Сохранить", command=self.save_task).pack(side=tk.LEFT, padx=5)
        else:
            ttk.Button(button_frame, text="Добавить", command=self.save_task).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Отмена", command=self.destroy).pack(side=tk.LEFT, padx=5)
    
    def load_task_data(self):
        """Загрузить данные задачи в форму"""
        if not self.task:
            return
        
        self.title_var.set(self.task.title)
        self.description_text.delete("1.0", tk.END)
        self.description_text.insert("1.0", self.task.description)
        self.priority_var.set(self.task.priority)
        self.status_var.set(self.task.status)
        self.due_date_var.set(self.task.due_date.strftime("%d.%m.%Y"))
        
        # Устанавливаем проект
        project = self.project_controller.get_project(self.task.project_id)
        if project:
            self.project_var.set(project.name)
        
        # Устанавливаем исполнителя
        user = self.user_controller.get_user(self.task.assignee_id)
        if user:
            self.assignee_var.set(user.username)
    
    def save_task(self):
        """Сохранить задачу"""
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
        
        status = self.status_var.get()
        if status not in ["pending", "in_progress", "completed"]:
            messagebox.showerror("Ошибка", "Выберите статус")
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
        
        if self.task:
            # Обновление существующей задачи
            success = self.task_controller.update_task(
                self.task.id,
                title=title,
                description=description,
                priority=priority,
                due_date=due_date,
                project_id=project_id,
                assignee_id=assignee_id,
                status=status
            )
            
            if success:
                self.result = True
                messagebox.showinfo("Успех", "Задача обновлена")
                self.destroy()
            else:
                messagebox.showerror("Ошибка", "Не удалось обновить задачу")
        else:
            # Добавление новой задачи
            task_id = self.task_controller.add_task(
                title, description, priority, due_date, project_id, assignee_id
            )
            
            if task_id > 0:
                # Обновляем статус если он был изменен
                if status != "pending":
                    self.task_controller.update_task_status(task_id, status)
                
                self.result = True
                messagebox.showinfo("Успех", f"Задача добавлена с ID {task_id}")
                self.destroy()
            else:
                messagebox.showerror("Ошибка", "Не удалось добавить задачу")