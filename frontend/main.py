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
        label="Введите ваш Email",
        width=350,
        prefix_icon=ft.Icons.EMAIL,
    )

    password_input = ft.TextField(
        label="Пароль",
        password=True,
        can_reveal_password=False,
        width=350,
        prefix_icon=ft.Icons.LOCK,
    )

    status_text = ft.Text("", size=14)

    # ------------------------------------------------------------------
    # Дашборд
    # ------------------------------------------------------------------
    async def load_dashboard():
        # 1. Показать «Загрузка...»
        page.clean()
        page.vertical_alignment = ft.MainAxisAlignment.START

        loading = ft.Text("Загрузка ваших бронирований...", size=16)
        page.add(loading)                    # ← ВАЖНО: добавили на страницу
        page.update()

        # 2. Запрос к API
        try:
            headers = {"Authorization": f"Bearer {auth_token}"}
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{BACKEND_URL}/bookings/my", headers=headers
                )
        except Exception as ex:
            page.clean()
            page.add(
                ft.Text(
                    f"❌ Ошибка сети при получении данных: {ex}",
                    color=ft.Colors.RED_400,
                )
            )
            page.update()
            return

        # 3. Проверка HTTP-статуса
        page.clean()

        if response.status_code != 200:
            page.add(
                ft.Text(
                    f"🔴 Не удалось загрузить бронирования. "
                    f"Код: {response.status_code}",
                    color=ft.Colors.RED_400,
                )
            )
            page.update()
            return

        # 4. Заголовок
        bookings = response.json()

        page.add(
            ft.Text(
                "Мои бронирования",
                size=26,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.BLUE_400,
            )
        )
        page.add(ft.Container(height=20))

        # 5. Список или «пусто»
        if not bookings:
            page.add(
                ft.Text(
                    "У вас пока нет активных бронирований.",
                    size=16,
                    color=ft.Colors.SURFACE_VARIANT,
                )
            )
        else:
            for b in bookings:
                status = b.get("status") or "active"
                if status == "cancelled":
                    status_color = ft.Colors.RED_400
                elif status in ("completed", "done"):
                    status_color = ft.Colors.BLUE_400
                elif status in ("pending", "waiting"):
                    status_color = ft.Colors.ORANGE_400
                else:
                    status_color = ft.Colors.GREEN_400

                date_display = (
                    b.get("booking_date")
                    or b.get("start_time")
                    or "Дата не указана"
                )

                page.add(
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Text(
                                    f"📅 Дата и время: {date_display}",
                                    size=16,
                                    weight=ft.FontWeight.BOLD,
                                ),
                                ft.Text(
                                    f"ID Услуги: {b.get('service_id')} | "
                                    f"ID Мастера: {b.get('master_id')}",
                                    size=14,
                                    color=ft.Colors.ON_SURFACE_VARIANT,
                                ),
                                ft.Text(
                                    f"Статус: {status}",
                                    size=14,
                                    color=status_color,
                                ),
                            ]
                        ),
                        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                        padding=15,
                        border_radius=10,
                        width=500,
                        border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
                    )
                )

        # 6. Один финальный update
        page.update()

    # ------------------------------------------------------------------
    # Логин
    # ------------------------------------------------------------------
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
                response = await client.post(
                    f"{BACKEND_URL}/auth/login", data=login_data
                )

            if response.status_code == 200:
                auth_token = response.json().get("access_token")
                if not auth_token:
                    status_text.value = "Сервер не вернул токен доступа."
                    status_text.color = ft.Colors.RED_400
                    page.update()
                    return

                snack = ft.SnackBar(
                    content=ft.Text("Успешная авторизация!"),
                    bgcolor=ft.Colors.GREEN_400,
                    duration=2500,
                )
                page.overlay.append(snack)
                snack.open = True

                email_input.value = ""
                password_input.value = ""
                page.update()

                await load_dashboard()
                return
            else:
                error_detail = response.json().get(
                    "detail", "Неверный логин или пароль"
                )
                status_text.value = f"Ошибка! {error_detail}"
                status_text.color = ft.Colors.RED_400
        except Exception as ex:
            status_text.value = f"Ошибка сети: {ex}"
            status_text.color = ft.Colors.RED_400

        page.update()

    # ------------------------------------------------------------------
    # UI формы входа
    # ------------------------------------------------------------------
    login_button = ft.Button(
        content="Войти в личный кабинет",
        icon=ft.Icons.LOGIN,
        on_click=login_user,
        width=350,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
    )

    auth_card = ft.Container(
        content=ft.Column(
            [
                ft.Text(
                    "Вход в систему",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLUE_400,
                ),
                ft.Container(height=15),
                email_input,
                ft.Container(height=15),
                password_input,
                ft.Container(height=15),
                login_button,
                ft.Container(height=10),
                status_text,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
        padding=30,
        border_radius=16,
        border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
    )

    page.add(auth_card)


if __name__ == "__main__":
    ft.run(main, view=ft.AppView.WEB_BROWSER, port=8500)