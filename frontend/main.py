import flet as ft
import httpx

BACKEND_URL = "http://127.0.0.1:8000"

async def main(page: ft.Page):
    page.title = "Система бронирования | Авторизация"
    page.theme_mode = ft.ThemeMode.DARK
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    auth_token = None

    email_input = ft.TextField(
        label='Введите ваш Email',
        width=350,
        prefix_icon=ft.Icons.EMAIL
    )

    password_input = ft.TextField(
        label='Пароль',
        password=True,
        can_reveal_password=False,
        width=350,
        prefix_icon=ft.Icons.LOCK
    )

    status_text = ft.Text("", size=14)

    async def login_user(e):
        nonlocal auth_token
        status_text.value = "Проверка данных..."
        status_text.color = ft.Colors.BLUE_200
        page.update()

        login_data = {
            "username": email_input.value,
            "password": password_input.value,
        }
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(f"{BACKEND_URL}/auth/login", data=login_data)

            if response.status_code == 200:
                auth_token = response.json().get("access_token")
                status_text.value = "Успешная авторизации!"
                status_text.color = ft.Colors.GREEN_400

                email_input.value = ""
                password_input.value =""
            else:
                error_detail = response.json().get("detail", "Неверный логин или пароль")
                status_text.value = f"Ошибка! {error_detail}"
                status_text.color = ft.Colors.RED_400
        except Exception as ex:
            status_text.value=f"Ошибка сети: {ex}" # Обработка исключения
            status_text.color = ft.Colors.RED_400

        page.update()

    login_button = ft.Button(
        content="Войти в личный кабинет",
        icon=ft.Icons.LOGIN,
        on_click=login_user,
        width=350,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
    )

    auth_card = ft.Container(
        content=ft.Column(
            [
                ft.Text("Вход в систему",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.BLUE_400),
                ft.Container(height=15),
                email_input,
                ft.Container(height=15),
                password_input,
                ft.Container(height=15),
                login_button,
                ft.Container(height=10),
                status_text
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
        padding=30,
        border_radius=16,
        border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT)
    )

    page.add(auth_card)


if __name__ == "__main__":
    ft.run(main, view=ft.AppView.WEB_BROWSER, port=8500)