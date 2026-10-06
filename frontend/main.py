import flet as ft
import httpx

BACKEND_URL = "http://127.0.0.1:8000"

async def main(page: ft.Page):
    page.title = "Система бронирования | Клиентская панель"
    page.theme_mode = ft.ThemeMode.DARK
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    title_text = ft.Text(
        "Добро пожаловать в сервис бронирования!",
        size=28,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.BLUE_400,
    )

    status_text = ft.Text(
        "Нажмите кнопку, чтобы проверить связь с FastAPI...",
        size=16,
    )

    async def check_api_connection(e):
        status_text.value = "Проверка связи..."
        status_text.color = None
        page.update()

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{BACKEND_URL}/services")

            if response.status_code == 200:
                services_count = len(response.json())
                status_text.value = f"Связь установлена! Получено услуг: {services_count}"
                status_text.color = ft.Colors.GREEN_400
            else:
                status_text.value = f"Сервер ответил ошибкой: {response.status_code}"
                status_text.color = ft.Colors.RED_400
        except Exception as ex:
            status_text.value = (
                "Не удалось связаться с FastAPI. "
                "Убедитесь, что сервер запущен!\n"
                f"Ошибка: {ex}"
            )
            status_text.color = ft.Colors.RED_400

        page.update()

    connect_button = ft.Button(
        content="Проверить соединение со службой API (FastAPI)",
        icon=ft.Icons.WIFI,  # Замена для отсутствующей CELL_TOWER
        on_click=check_api_connection,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
    )

    content_layout = ft.Column(
        [
            title_text,
            ft.Container(height=10),
            connect_button,
            ft.Container(height=10),
            status_text,
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )

    page.add(content_layout)

if __name__ == "__main__":
    ft.run(main, view=ft.AppView.WEB_BROWSER, port=8500)