import flet as ft
import os
from flet.security import encrypt, decrypt


class Task(ft.Column):
    def __init__(self, task_name, task_status_change, task_delete):
        super().__init__()
        self.completed = False
        self.task_name = task_name
        self.task_status_change = task_status_change
        self.task_delete = task_delete
        self.display_task = ft.Checkbox(
            value=False, label=self.task_name, on_change=self.status_changed
        )
        self.edit_name = ft.TextField(expand=1)

        self.display_view = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                self.display_task,
                ft.Row(
                    spacing=0,
                    controls=[
                        ft.IconButton(
                            icon=ft.icons.CREATE_OUTLINED,
                            tooltip="Editar Tarefa",
                            on_click=self.edit_clicked,
                        ),
                        ft.IconButton(
                            ft.icons.DELETE_OUTLINE,
                            tooltip="Remover tarefa",
                            on_click=self.delete_clicked,
                        ),
                    ],
                ),
            ],
        )

        self.edit_view = ft.Row(
            visible=False,
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                self.edit_name,
                ft.IconButton(
                    icon=ft.icons.DONE_OUTLINE_OUTLINED,
                    icon_color=ft.colors.GREEN,
                    tooltip="Update To-Do",
                    on_click=self.save_clicked,
                ),
            ],
        )
        self.controls = [self.display_view, self.edit_view]

    def edit_clicked(self, e):
        self.edit_name.value = self.display_task.label
        self.display_view.visible = False
        self.edit_view.visible = True
        self.update()

    def save_clicked(self, e):
        self.display_task.label = self.edit_name.value
        self.display_view.visible = True
        self.edit_view.visible = False
        self.update()

    def status_changed(self, e):
        self.completed = self.display_task.value
        self.task_status_change()

    def delete_clicked(self, e):
        self.task_delete(self)


class TodoApp(ft.Column):
    def __init__(self, saved_tasks):
        super().__init__()

        # Inicializar self.tasks com Task instances a partir de saved_tasks
        self.tasks = ft.Column()
        self.secret_key = os.getenv("chaveEncriptationsYau")
        if saved_tasks:
            for task in saved_tasks:
                new_task = Task(task['task_name'], self.task_status_change, self.task_delete)
                new_task.completed = task['completed']
                new_task.display_task.value = task['completed']
                self.tasks.controls.append(new_task)
        
        self.new_task = ft.TextField(
            hint_text="Adiciona tarefa aqui...", on_submit=self.add_clicked, expand=True
        )

        self.filter = ft.Tabs(
            scrollable=False,
            selected_index=0,
            on_change=self.tabs_changed,
            tabs=[ft.Tab(text="todos"), ft.Tab(text="ativos"), ft.Tab(text="completos")],
        )

        self.items_left = ft.Text("Faltam 0 itens")

        self.width = 600
        self.controls = [
            ft.Row(
                [ft.Text(value="Gestor de tarefas", theme_style=ft.TextThemeStyle.HEADLINE_MEDIUM)],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            ft.Row(
                controls=[
                    self.new_task,
                    ft.FloatingActionButton(
                        icon=ft.icons.ADD, on_click=self.add_clicked
                    ),
                ],
            ),
            ft.Column(
                spacing=25,
                controls=[
                    self.filter,
                    self.tasks,
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            self.items_left,
                            ft.OutlinedButton(
                                text="Limpar Completos", on_click=self.clear_clicked
                            ),
                        ],
                    ),
                ],
            ),
        ]

    def add_clicked(self, e):
        if self.new_task.value:
            task = Task(self.new_task.value, self.task_status_change, self.task_delete)
            self.tasks.controls.append(task)
            self.new_task.value = ""
            self.new_task.focus()
            self.update()
            self.save_tasks()

    def task_status_change(self):
        self.update()
        self.save_tasks()

    def task_delete(self, task):
        self.tasks.controls.remove(task)
        self.update()
        self.save_tasks()

    def tabs_changed(self, e):
        self.update()

    def clear_clicked(self, e):
        for task in self.tasks.controls[:]:
            if task.completed:
                self.task_delete(task)
        self.save_tasks()

    def before_update(self):
        status = self.filter.tabs[self.filter.selected_index].text
        count = 0
        for task in self.tasks.controls:
            task.visible = (
                status == "todos"
                or (status == "ativos" and task.completed == False)
                or (status == "completos" and task.completed)
            )
            if not task.completed:
                count += 1
        self.items_left.value = f"Faltam {count} itens"

    def save_tasks(self):

        tasks = [
            {"task_name": task.display_task.label, "completed": task.completed}
            for task in self.tasks.controls
        ]
        tasks_encrypted = encrypt(tasks, self.secret_key)
        self.page.client_storage.set("tasks", tasks_encrypted)


def main(page: ft.Page):

    secret_key = os.getenv("chaveEncriptationsYau")
    page.title = "Gestor de tarefas"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.scroll = ft.ScrollMode.ADAPTIVE

    # Carregar tarefas salvas
    saved_tasks = page.client_storage.get("tasks")
    print("saved_tasks:", saved_tasks)
    for task in saved_tasks:
        task["task_name"] = decrypt(task["task_name"], secret_key)
    
    saved_tasks_decrypted = decrypt(saved_tasks, secret_key)

    if saved_tasks_decrypted is None:
        saved_tasks_decrypted = []

    app = TodoApp(saved_tasks_decrypted)
    
    # Adicionar app à página
    page.add(app)


ft.app(main)
