import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime


class ProjectView(ttk.Frame):
    def __init__(self, parent, project_controller, task_controller=None) -> None:
        super().__init__(parent)
        
        self.project_controller = project_controller
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
        ttk.Button(control_frame, text="Добавить проект", 
                  command=self.add_project).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="Обновить", 
                  command=self.refresh_projects).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="Удалить выбранный", 
                  command=self.delete_selected).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="Показать задачи", 
                  command=self.show_project_tasks).pack(side=tk.LEFT, padx=2)
        
        # Панель фильтров
        filter_frame = ttk.Frame(control_frame)
        filter_frame.pack(side=tk.RIGHT, padx=2)
        
        # Фильтр по статусу
        ttk.Label(filter_frame, text="Статус:").pack(side=tk.LEFT)
        self.status_filter_var = tk.StringVar(value="Все")
        status_combo = ttk.Combobox(filter_frame, textvariable=self.status_filter_var, 
                                   values=["Все", "active", "completed", "on_hold"], 
                                   state="readonly", width=12)
        status_combo.pack(side=tk.LEFT, padx=2)
        status_combo.bind('<<ComboboxSelected>>', self.filter_projects)
        
        # Кнопка для просроченных проектов
        ttk.Button(filter_frame, text="Просроченные", 
                  command=self.show_overdue_projects).pack(side=tk.LEFT, padx=(10, 2))
        
        # Таблица проектов
        columns = ('id', 'name', 'status', 'start_date', 'end_date', 'progress', 'tasks', 'days_left')
        self.project_tree = ttk.Treeview(self, columns=columns, show='headings', height=20)
        
        # Настройка колонок
        self.project_tree.heading('id', text='ID')
        self.project_tree.heading('name', text='Название')
        self.project_tree.heading('status', text='Статус')
        self.project_tree.heading('start_date', text='Начало')
        self.project_tree.heading('end_date', text='Окончание')
        self.project_tree.heading('progress', text='Прогресс')
        self.project_tree.heading('tasks', text='Задачи')
        self.project_tree.heading('days_left', text='Дней')
        
        self.project_tree.column('id', width=50, anchor=tk.CENTER)
        self.project_tree.column('name', width=200)
        self.project_tree.column('status', width=100, anchor=tk.CENTER)
        self.project_tree.column('start_date', width=100, anchor=tk.CENTER)
        self.project_tree.column('end_date', width=100, anchor=tk.CENTER)
        self.project_tree.column('progress', width=80, anchor=tk.CENTER)
        self.project_tree.column('tasks', width=80, anchor=tk.CENTER)
        self.project_tree.column('days_left', width=60, anchor=tk.CENTER)
        
        # Скроллбар
        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.project_tree.yview)
        self.project_tree.configure(yscrollcommand=scrollbar.set)
        
        # Размещение
        self.project_tree.grid(row=1, column=0, sticky=tk.NSEW, padx=(0, 5))
        scrollbar.grid(row=1, column=1, sticky=tk.NS)
        
        # Двойной клик для редактирования
        self.project_tree.bind('<Double-Button-1>', self.edit_project)
        
        # Детальная информация о проекте
        self.detail_frame = ttk.LabelFrame(self, text="Детали проекта", padding=10)
        self.detail_frame.grid(row=2, column=0, columnspan=2, sticky=tk.EW, pady=(10, 0))
        
        # Скрываем детальную информацию по умолчанию
        self.detail_frame.grid_remove()
        
        # Создаем виджеты для детальной информации
        self.create_detail_widgets()
        
        # Инициализация данных
        self.all_projects = []
        self.refresh_projects()
    
    def create_detail_widgets(self):
        """Создание виджетов для детальной информации о проекте"""
        # Название проекта
        self.detail_name = ttk.Label(self.detail_frame, text="", font=('Arial', 12, 'bold'))
        self.detail_name.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        # Описание
        ttk.Label(self.detail_frame, text="Описание:", font=('Arial', 10, 'bold')).grid(
            row=1, column=0, sticky=tk.W, pady=2)
        self.detail_description = ttk.Label(self.detail_frame, text="", wraplength=500)
        self.detail_description.grid(row=1, column=1, sticky=tk.W, pady=2, padx=(10, 0))
        
        # Статус
        ttk.Label(self.detail_frame, text="Статус:", font=('Arial', 10, 'bold')).grid(
            row=2, column=0, sticky=tk.W, pady=2)
        self.detail_status = ttk.Label(self.detail_frame, text="")
        self.detail_status.grid(row=2, column=1, sticky=tk.W, pady=2, padx=(10, 0))
        
        # Даты
        ttk.Label(self.detail_frame, text="Период:", font=('Arial', 10, 'bold')).grid(
            row=3, column=0, sticky=tk.W, pady=2)
        self.detail_dates = ttk.Label(self.detail_frame, text="")
        self.detail_dates.grid(row=3, column=1, sticky=tk.W, pady=2, padx=(10, 0))
        
        # Прогресс
        ttk.Label(self.detail_frame, text="Прогресс:", font=('Arial', 10, 'bold')).grid(
            row=4, column=0, sticky=tk.W, pady=2)
        
        # Прогресс бар и метка
        progress_frame = ttk.Frame(self.detail_frame)
        progress_frame.grid(row=4, column=1, sticky=tk.W, pady=2, padx=(10, 0))
        
        self.progress_bar = ttk.Progressbar(progress_frame, length=200, mode='determinate')
        self.progress_bar.pack(side=tk.LEFT)
        
        self.progress_label = ttk.Label(progress_frame, text="")
        self.progress_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Статистика задач
        ttk.Label(self.detail_frame, text="Задачи:", font=('Arial', 10, 'bold')).grid(
            row=5, column=0, sticky=tk.W, pady=2)
        self.detail_tasks = ttk.Label(self.detail_frame, text="")
        self.detail_tasks.grid(row=5, column=1, sticky=tk.W, pady=2, padx=(10, 0))
        
        # Дней осталось
        ttk.Label(self.detail_frame, text="Дней осталось:", font=('Arial', 10, 'bold')).grid(
            row=6, column=0, sticky=tk.W, pady=2)
        self.detail_days_left = ttk.Label(self.detail_frame, text="")
        self.detail_days_left.grid(row=6, column=1, sticky=tk.W, pady=2, padx=(10, 0))
        
        # Кнопка закрыть детали
        ttk.Button(self.detail_frame, text="Закрыть", 
                  command=self.hide_details).grid(row=7, column=0, columnspan=2, pady=(10, 0))
    
    def refresh_projects(self) -> None:
        """Обновить список проектов"""
        # Очищаем дерево
        for item in self.project_tree.get_children():
            self.project_tree.delete(item)
        
        # Получаем все проекты
        self.all_projects = self.project_controller.get_all_projects()
        
        # Применяем фильтры
        filtered_projects = self.apply_filters(self.all_projects)
        
        # Заполняем дерево
        for project in filtered_projects:
            # Получаем задачи проекта
            tasks = []
            if self.task_controller:
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
            
            # Рассчитываем дни до окончания
            now = datetime.now()
            if hasattr(project, 'get_days_remaining'):
                days_left = project.get_days_remaining()
            else:
                if project.end_date > now:
                    days_left = (project.end_date - now).days
                else:
                    days_left = -(now - project.end_date).days
            
            # Форматируем дни
            if days_left > 0:
                days_str = f"+{days_left}"
            elif days_left < 0:
                days_str = f"-{abs(days_left)}"
            else:
                days_str = "0"
            
            # Добавляем пометку для просроченных проектов
            if hasattr(project, 'is_overdue') and project.is_overdue() and project.status != 'completed':
                status += " (⚠)"
                days_str += " (⚠)"
            
            self.project_tree.insert('', tk.END, values=(
                project.id,
                project.name,
                status,
                start_date,
                end_date,
                f"{progress:.1f}%",
                f"{completed_tasks}/{total_tasks}",
                days_str
            ))
    
    def apply_filters(self, projects):
        """Применить фильтры к списку проектов"""
        filtered_projects = projects
        
        # Фильтр по статусу
        status_filter = self.status_filter_var.get()
        if status_filter != "Все":
            filtered_projects = [p for p in filtered_projects if p.status == status_filter]
        
        return filtered_projects
    
    def filter_projects(self, event=None) -> None:
        """Фильтровать проекты"""
        self.refresh_projects()
    
    def show_overdue_projects(self) -> None:
        """Показать просроченные проекты"""
        # Устанавливаем фильтр статуса на "Все" чтобы видеть все просроченные
        self.status_filter_var.set("Все")
        
        # Очищаем дерево
        for item in self.project_tree.get_children():
            self.project_tree.delete(item)
        
        # Получаем все проекты и фильтруем просроченные
        all_projects = self.project_controller.get_all_projects()
        
        overdue_projects = []
        for project in all_projects:
            if hasattr(project, 'is_overdue') and project.is_overdue() and project.status != 'completed':
                overdue_projects.append(project)
        
        # Применяем другие фильтры
        filtered_projects = self.apply_filters(overdue_projects)
        
        # Заполняем дерево
        for project in filtered_projects:
            tasks = []
            if self.task_controller:
                tasks = self.task_controller.get_tasks_by_project(project.id)
            
            total_tasks = len(tasks)
            completed_tasks = sum(1 for task in tasks if task.status == 'completed')
            
            start_date = project.start_date.strftime('%d.%m.%Y')
            end_date = project.end_date.strftime('%d.%m.%Y')
            progress = project.get_progress() * 100
            
            status_names = {'active': 'Активный', 'completed': 'Завершен', 'on_hold': 'Приостановлен'}
            status = status_names.get(project.status, project.status) + " (⚠)"
            
            # Рассчитываем дни до окончания
            now = datetime.now()
            if hasattr(project, 'get_days_remaining'):
                days_left = project.get_days_remaining()
            else:
                days_left = -(now - project.end_date).days
            
            days_str = f"-{abs(days_left)} (⚠)"
            
            self.project_tree.insert('', tk.END, values=(
                project.id,
                project.name,
                status,
                start_date,
                end_date,
                f"{progress:.1f}%",
                f"{completed_tasks}/{total_tasks}",
                days_str
            ))
    
    def add_project(self) -> None:
        """Добавить новый проект"""
        dialog = ProjectDialog(self, self.project_controller)
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
            dialog = ProjectDialog(self, self.project_controller, project)
            self.wait_window(dialog)
            if dialog.result:
                self.refresh_projects()
    
    def delete_selected(self) -> None:
        """Удалить выбранный проект"""
        selection = self.project_tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите проект для удаления")
            return
        
        item = self.project_tree.item(selection[0])
        project_id = item['values'][0]
        project_name = item['values'][1]
        
        if messagebox.askyesno("Подтверждение", 
                              f"Удалить проект '{project_name}'?\nВсе задачи проекта также будут удалены."):
            success = self.project_controller.delete_project(project_id)
            if success:
                self.refresh_projects()
                self.hide_details()  # Скрываем детали если они отображались
                messagebox.showinfo("Успех", f"Проект '{project_name}' удален")
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
        
        if not self.task_controller:
            messagebox.showinfo("Информация", 
                              "Контроллер задач не подключен к представлению проектов")
            return
        
        # Создаем диалог для просмотра задач проекта
        tasks = self.task_controller.get_tasks_by_project(project_id)
        
        if not tasks:
            messagebox.showinfo("Задачи проекта", 
                              f"В проекте '{project_name}' нет задач")
            return
        
        # Показываем детальную информацию о проекте
        self.show_project_details(project_id)
    
    def show_project_details(self, project_id):
        """Показать детальную информацию о проекте"""
        project = self.project_controller.get_project(project_id)
        if not project:
            return
        
        # Получаем задачи проекта
        tasks = []
        if self.task_controller:
            tasks = self.task_controller.get_tasks_by_project(project_id)
        
        total_tasks = len(tasks)
        completed_tasks = sum(1 for task in tasks if task.status == 'completed')
        in_progress_tasks = sum(1 for task in tasks if task.status == 'in_progress')
        pending_tasks = sum(1 for task in tasks if task.status == 'pending')
        overdue_tasks = sum(1 for task in tasks if task.is_overdue())
        
        # Обновляем детальную информацию
        self.detail_name.config(text=project.name)
        self.detail_description.config(text=project.description)
        
        # Статус
        status_names = {'active': 'Активный', 'completed': 'Завершен', 'on_hold': 'Приостановлен'}
        status = status_names.get(project.status, project.status)
        if hasattr(project, 'is_overdue') and project.is_overdue() and project.status != 'completed':
            status += " (ПРОСРОЧЕН)"
        self.detail_status.config(text=status)
        
        # Даты
        start_date = project.start_date.strftime('%d.%m.%Y')
        end_date = project.end_date.strftime('%d.%m.%Y')
        self.detail_dates.config(text=f"{start_date} - {end_date}")
        
        # Прогресс
        progress = project.get_progress() * 100
        self.progress_bar['value'] = progress
        self.progress_label.config(text=f"{progress:.1f}%")
        
        # Задачи
        tasks_text = f"Всего: {total_tasks} | "
        tasks_text += f"Завершено: {completed_tasks} | "
        tasks_text += f"В работе: {in_progress_tasks} | "
        tasks_text += f"Ожидание: {pending_tasks}"
        
        if overdue_tasks > 0:
            tasks_text += f" | Просрочено: {overdue_tasks}"
        
        self.detail_tasks.config(text=tasks_text)
        
        # Дни до окончания
        now = datetime.now()
        if hasattr(project, 'get_days_remaining'):
            days_left = project.get_days_remaining()
        else:
            if project.end_date > now:
                days_left = (project.end_date - now).days
            else:
                days_left = -(now - project.end_date).days
        
        if days_left > 0:
            days_text = f"{days_left} дней до окончания"
        elif days_left < 0:
            days_text = f"Просрочен на {abs(days_left)} дней"
        else:
            days_text = "Заканчивается сегодня"
        
        self.detail_days_left.config(text=days_text)
        
        # Показываем фрейм с деталями
        self.detail_frame.grid()
    
    def hide_details(self):
        """Скрыть детальную информацию"""
        self.detail_frame.grid_remove()
    
    def on_project_selected(self, event):
        """Обработчик выбора проекта в дереве"""
        selection = self.project_tree.selection()
        if not selection:
            self.hide_details()
            return
        
        item = self.project_tree.item(selection[0])
        project_id = item['values'][0]
        
        self.show_project_details(project_id)


class ProjectDialog(tk.Toplevel):
    """Диалог для добавления/редактирования проекта"""
    
    def __init__(self, parent, project_controller, project=None):
        super().__init__(parent)
        self.project_controller = project_controller
        self.project = project  # Если None - добавление, иначе - редактирование
        self.result = False
        
        self.setup_dialog()
        self.create_widgets()
        
        if project:
            self.load_project_data()
    
    def setup_dialog(self):
        if self.project:
            self.title("Редактировать проект")
        else:
            self.title("Добавить проект")
        
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
        ttk.Label(main_frame, text="Название проекта:*").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.name_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.name_var, width=40).grid(row=0, column=1, pady=5, padx=(5, 0))
        
        # Описание
        ttk.Label(main_frame, text="Описание:*").grid(row=1, column=0, sticky=tk.NW, pady=5)
        self.description_text = tk.Text(main_frame, width=40, height=4)
        self.description_text.grid(row=1, column=1, pady=5, padx=(5, 0))
        
        # Дата начала
        ttk.Label(main_frame, text="Дата начала (дд.мм.гггг):*").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.start_date_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.start_date_var, width=15).grid(row=2, column=1, sticky=tk.W, pady=5, padx=(5, 0))
        
        # Дата окончания
        ttk.Label(main_frame, text="Дата окончания (дд.мм.гггг):*").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.end_date_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.end_date_var, width=15).grid(row=3, column=1, sticky=tk.W, pady=5, padx=(5, 0))
        
        # Статус (только для редактирования)
        if self.project:
            ttk.Label(main_frame, text="Статус:*").grid(row=4, column=0, sticky=tk.W, pady=5)
            self.status_var = tk.StringVar(value="active")
            status_combo = ttk.Combobox(main_frame, textvariable=self.status_var, 
                                       values=["active", "completed", "on_hold"], 
                                       state="readonly", width=15)
            status_combo.grid(row=4, column=1, sticky=tk.W, pady=5, padx=(5, 0))
            self.row_offset = 1  # Смещение для кнопок
        else:
            self.row_offset = 0
        
        # Кнопки
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5 + self.row_offset, column=0, columnspan=2, pady=20)
        
        if self.project:
            ttk.Button(button_frame, text="Сохранить", command=self.save_project).pack(side=tk.LEFT, padx=5)
        else:
            ttk.Button(button_frame, text="Добавить", command=self.save_project).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Отмена", command=self.destroy).pack(side=tk.LEFT, padx=5)
    
    def load_project_data(self):
        """Загрузить данные проекта в форму"""
        if not self.project:
            return
        
        self.name_var.set(self.project.name)
        self.description_text.delete("1.0", tk.END)
        self.description_text.insert("1.0", self.project.description)
        self.start_date_var.set(self.project.start_date.strftime("%d.%m.%Y"))
        self.end_date_var.set(self.project.end_date.strftime("%d.%m.%Y"))
        
        if hasattr(self, 'status_var'):
            self.status_var.set(self.project.status)
    
    def save_project(self):
        """Сохранить проект"""
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
        
        if self.project:
            # Обновление существующего проекта
            update_data = {
                'name': name,
                'description': description,
                'start_date': start_date,
                'end_date': end_date
            }
            
            # Добавляем статус если он есть
            if hasattr(self, 'status_var'):
                status = self.status_var.get()
                if status in ["active", "completed", "on_hold"]:
                    update_data['status'] = status
            
            success = self.project_controller.update_project(self.project.id, **update_data)
            
            if success:
                self.result = True
                messagebox.showinfo("Успех", "Проект обновлен")
                self.destroy()
            else:
                messagebox.showerror("Ошибка", "Не удалось обновить проект")
        else:
            # Добавление нового проекта
            project_id = self.project_controller.add_project(name, description, start_date, end_date)
            
            if project_id > 0:
                self.result = True
                messagebox.showinfo("Успех", f"Проект добавлен с ID {project_id}")
                self.destroy()
            else:
                messagebox.showerror("Ошибка", "Не удалось добавить проект")