import flet as ft
import httpx

BACKEND_URL = "http://127.0.0.1:8000"


async def main(page: ft.Page):
    page.title = "Система бронирования | Личный кабинет"
    page.theme_mode = ft.ThemeMode.DARK
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    auth_token = None

    # ------------------------------------------------------------------
    # Поля формы авторизации
    # ------------------------------------------------------------------
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
    # Личный кабинет
    # ------------------------------------------------------------------
    async def load_dashboard():
        page.clean()
        page.vertical_alignment = ft.MainAxisAlignment.START
        page.horizontal_alignment = ft.CrossAxisAlignment.START

        page.add(ft.Text("Загрузка личного кабинета...", size=16))
        page.update()

        headers = {"Authorization": f"Bearer {auth_token}"}

        # --- 1. Загрузка данных ---
        bookings = []
        services = []
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res_bookings = await client.get(
                    f"{BACKEND_URL}/bookings/my", headers=headers
                )
                res_services = await client.get(f"{BACKEND_URL}/services")

            # 1a. Токен истёк → на форму входа
            if res_bookings.status_code == 401:
                page.clean()
                page.add(
                    ft.Text(
                        "🔒 Сессия истекла. Войдите заново.",
                        color=ft.Colors.ORANGE_400,
                        size=16,
                    ),
                    ft.Container(height=15),
                    auth_card,
                )
                page.update()
                return

            # 1b. Прочие ошибки броней
            if res_bookings.status_code != 200:
                page.clean()
                page.add(
                    ft.Text(
                        f"🔴 Не удалось загрузить бронирования. "
                        f"Код: {res_bookings.status_code}",
                        color=ft.Colors.RED_400,
                    )
                )
                page.update()
                return

            bookings = res_bookings.json()

            # 1c. Услуги — не критично, если упали
            if res_services.status_code == 200:
                services = res_services.json()

        except Exception as ex:
            page.clean()
            page.add(
                ft.Text(
                    f"❌ Ошибка сети при загрузке кабинета: {ex}",
                    color=ft.Colors.RED_400,
                )
            )
            page.update()
            return

        page.clean()

        # --- 2. Левая колонка: список броней ---
        bookings_container = ft.Column(
            spacing=15, scroll=ft.ScrollMode.AUTO, expand=True
        )

        if not bookings:
            bookings_container.controls.append(
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

                bookings_container.controls.append(
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
                        width=450,
                        border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
                    )
                )

        left_column = ft.Column(
            [
                ft.Text(
                    "Мои бронирования",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLUE_400,
                ),
                ft.Container(height=10),
                bookings_container,
            ],
            expand=True,
        )

        # --- 3. Правая колонка: форма новой записи ---
        service_dropdown = ft.Dropdown(
            label="Выберите услугу",
            width=350,
            options=[
                ft.DropdownOption(
                    key=str(s["id"]),
                    text=f"{s['name']} ({s['price']} руб.)",
                )
                for s in services
            ],
        )

        master_input = ft.TextField(
            label="ID Мастера",
            width=350,
            value="1",
            prefix_icon=ft.Icons.PERSON,
        )

        datetime_input = ft.TextField(
            label="Дата и время (ГГГГ-ММ-ДДTЧЧ:ММ:СС)",
            width=350,
            value="2026-10-20T14:00:00",
            prefix_icon=ft.Icons.CALENDAR_MONTH,
        )

        form_status = ft.Text("", size=14)

        # --- 4. Обработчик отправки формы ---
        async def create_booking(e):
            if not service_dropdown.value:
                form_status.value = "⚠️ Выберите услугу!"
                form_status.color = ft.Colors.ORANGE_400
                page.update()
                return

            form_status.value = "Отправка записи..."
            form_status.color = ft.Colors.BLUE_200
            page.update()

            booking_payload = {
                "client_id": 4,
                "master_id": int(master_input.value),
                "service_id": int(service_dropdown.value),
                "start_time": datetime_input.value,
            }

            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.post(
                        f"{BACKEND_URL}/bookings",
                        json=booking_payload,
                        headers=headers,
                    )

                if response.status_code == 201:
                    snack = ft.SnackBar(
                        content=ft.Text("🎉 Вы успешно записались!"),
                        bgcolor=ft.Colors.GREEN_400,
                    )
                    page.overlay.append(snack)
                    snack.open = True
                    page.update()

                    await load_dashboard()
                    return
                else:
                    err = response.json().get("detail", "Ошибка валидации")
                    if isinstance(err, list):
                        err = "; ".join(
                            f"{e.get('loc', ['?'])[-1]}: {e.get('msg')}"
                            for e in err
                        )
                    form_status.value = f"🔴 Ошибка: {err}"
                    form_status.color = ft.Colors.RED_400
            except Exception as ex:
                form_status.value = f"❌ Ошибка сети: {ex}"
                form_status.color = ft.Colors.RED_400

            page.update()

        right_column = ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "Записаться на услугу",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.GREEN_400,
                    ),
                    ft.Container(height=10),
                    service_dropdown,
                    ft.Container(height=5),
                    master_input,
                    ft.Container(height=5),
                    datetime_input,
                    ft.Container(height=10),
                    ft.Button(
                        content="Подтвердить запись",
                        icon=ft.Icons.CHECK,
                        on_click=create_booking,
                        width=350,
                    ),
                    ft.Container(height=5),
                    form_status,
                ]
            ),
            padding=20,
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
            border_radius=12,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
        )

        # --- 5. Общий layout ---
        main_layout = ft.Container(
            padding=30,
            content=ft.Row(
                [
                    left_column,
                    ft.Container(width=20),
                    right_column,
                ],
                alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.START,
                expand=True,
            ),
        )

        page.add(main_layout)
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
                received_token = response.json().get("access_token")
                if not received_token:
                    status_text.value = "Сервер не вернул токен."
                    status_text.color = ft.Colors.RED_400
                    page.update()
                    return

                auth_token = received_token

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