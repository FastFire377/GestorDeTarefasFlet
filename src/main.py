import flet as ft
import os
import json
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from flet.security import encrypt, decrypt

AUTH_URL = "https://github.com/login/oauth/authorize"
TOKEN_URL = "https://github.com/login/oauth/access_token"
CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "Ov23liC7fvBOl99Nbrab")
CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "b0f46f2b54b999f97e4888bce1cce30f3d5ada")

REDIRECT_URI = "http://localhost:8000/callback"

def get_auth_code():
    class AuthHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            query = urlparse(self.path).query
            params = parse_qs(query)
            if "code" in params:
                self.server.auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h1>Authentication successful. You can close this window.</h1>")

    server = HTTPServer(("localhost", 8000), AuthHandler)
    webbrowser.open(f"{AUTH_URL}?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}")
    server.handle_request()
    return server.auth_code


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

    def save_tasks(self):
        tasks = [
            {"task_name": encrypt(task.display_task.label, self.secret_key), "completed": task.completed}
            for task in self.tasks.controls
        ]
        self.page.client_storage.set("tasks", tasks)


def main(page: ft.Page):
    auth_code = get_auth_code()
    if not auth_code:
        page.add(ft.Text("Falha na autenticação. Tente novamente."))
        return

    secret_key = os.getenv("chaveEncriptationsYau")
    page.title = "Gestor de tarefas"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.scroll = ft.ScrollMode.ADAPTIVE

    saved_tasks = page.client_storage.get("tasks")
    if saved_tasks:
        for task in saved_tasks:
            task["task_name"] = decrypt(task["task_name"], secret_key)

    app = TodoApp(saved_tasks if saved_tasks else [])
    page.add(app)


ft.app(main)
