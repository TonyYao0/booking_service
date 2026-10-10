import flet as ft
import httpx
from datetime import datetime

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
    # Выход
    # ------------------------------------------------------------------
    async def logout_user(e):
        nonlocal auth_token
        auth_token = None

        snack = ft.SnackBar(
            content=ft.Text("🔒 Вы вышли из учетной записи"),
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            duration=2000,
        )
        page.overlay.append(snack)
        snack.open = True

        page.clean()
        page.vertical_alignment = ft.MainAxisAlignment.CENTER
        page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        page.add(auth_card)
        page.update()

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
        masters = []
        # --- 1. Загрузка данных ---
        bookings = []
        services = []
        async def cancel_booking(booking_id: int):
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    res = await client.delete(
                        f"{BACKEND_URL}/bookings/{booking_id}",
                        headers=headers,
                    )
                if res.status_code == 204:
                    snack = ft.SnackBar(
                        content=ft.Text("🗑️ Бронь отменена"),
                        bgcolor=ft.Colors.ORANGE_400,
                    )
                    page.overlay.append(snack)
                    snack.open = True
                    page.update()
                    await load_dashboard()
                else:
                    detail = res.json().get("detail", f"Код {res.status_code}")
                    snack = ft.SnackBar(
                        content=ft.Text(f"🔴 {detail}"),
                        bgcolor=ft.Colors.RED_400,
                    )
                    page.overlay.append(snack)
                    snack.open = True
                    page.update()
            except Exception as ex:
                snack = ft.SnackBar(
                    content=ft.Text(f"❌ Ошибка сети: {ex}"),
                    bgcolor=ft.Colors.RED_400,
                )
                page.overlay.append(snack)
                snack.open = True
                page.update()
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res_bookings = await client.get(
                    f"{BACKEND_URL}/bookings/my", headers=headers
                )
                res_services = await client.get(f"{BACKEND_URL}/services")
                res_masters = await client.get(f"{BACKEND_URL}/masters")

            # Токен истёк → на форму входа
            if res_bookings.status_code == 401:
                page.clean()
                page.vertical_alignment = ft.MainAxisAlignment.CENTER
                page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
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

            if res_services.status_code == 200:
                services = res_services.json()

            if res_masters.status_code == 200:
                masters = res_masters.json()
            # Заглушка
            else: 
                masters = [
                    {"id": 1, "full_name": "Алексей (Стрижки)"},
                    {"id": 2, "full_name": "Мария (Окрашивание)"},
                ]

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

        # --- Шапка ---
        header_row = ft.Row(
            [
                ft.Text(
                    "Личный кабинет клиента",
                    size=28,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLUE_400,
                ),
                ft.Button(
                    content="Выйти",
                    icon=ft.Icons.LOGOUT,
                    on_click=logout_user,
                    style=ft.ButtonStyle(color=ft.Colors.RED_400),
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

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
                booking_id = b.get("id")

                if status != "cancelled":
                    actions_row = ft.Row(
                        [
                            ft.Text(
                                f"Статус: {status}",
                                size=14,
                                color=status_color,
                            ),
                            ft.Container(expand=True),
                            ft.IconButton(
                                icon=ft.Icons.DELETE_OUTLINE,
                                icon_color=ft.Colors.RED_400,
                                tooltip="Отменить бронь",
                                on_click=lambda e, bid=booking_id: page.run_task(
                                    cancel_booking, bid
                                ),
                            ),
                        ],
                        width=420,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    )
                else:
                    actions_row = ft.Text(
                        f"Статус: {status}",
                        size=14,
                        color=status_color,
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
                                actions_row,
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
                    size=20,
                    weight=ft.FontWeight.BOLD,
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

        # выпадающий список мастеров
        master_dropdown = ft.Dropdown(
            label="Выберите мастера",
            width=350,
            options=[
                ft.DropdownOption(
                    key=str(m["id"]),
                    text=m["full_name"],
                )
                for m in masters
            ],
            value=str(masters[0]["id"]) if masters else None,
        )

        # выбор даты через DatePicker
        selected_date_str = "2026-10-20T14:00:00"

        date_button = ft.Button(
            content="Выбрать дату: 2026-10-20",
            icon=ft.Icons.CALENDAR_MONTH,
            width=350,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        )
        def handle_date_change(e):
            nonlocal selected_date_str
            if date_picker.value:
                chosen_date = date_picker.value.strftime("%Y-%m-%d")
                selected_date_str = f"{chosen_date}T14:00:00"
                date_button.content = f"Выбрать дату: {chosen_date}"
                page.update()

        date_picker = ft.DatePicker(
            first_date=datetime.now(),
            last_date=datetime(2027, 12, 31),
            on_change=handle_date_change,
        )
        page.overlay.append(date_picker)

        def open_date_picker(e):
            date_picker.open = True
            page.update()

        date_button.on_click = open_date_picker

        form_status = ft.Text("", size=14)

        # --- 4. Обработчик отправки формы ---
        async def create_booking(e):
            if not service_dropdown.value:
                form_status.value = "⚠️ Выберите услугу!"
                form_status.color = ft.Colors.ORANGE_400
                page.update()
                return
            if not master_dropdown.value:
                form_status.value = "⚠️ Выберите мастера!"
                form_status.color = ft.Colors.ORANGE_400
                page.update()
                return
            
            form_status.value = "Отправка записи..."
            form_status.color = ft.Colors.BLUE_200
            page.update()

            booking_payload = {
                # client_id бэкенд заменит на current_user.id
                "client_id": 0,
                "master_id": int(master_dropdown.value),
                "service_id": int(service_dropdown.value),
                "start_time": selected_date_str,
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
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.GREEN_400,
                    ),
                    ft.Container(height=10),
                    service_dropdown,
                    ft.Container(height=5),
                    master_dropdown,
                    ft.Container(height=5),
                    date_button,
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

        # --- Рабочая зона ---
        workspace_layout = ft.Row(
            [
                left_column,
                ft.Container(width=20),
                right_column,
            ],
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.START,
            expand=True,
        )

        # --- Главный контейнер ---
        main_layout = ft.Container(
            padding=30,
            content=ft.Column(
                [
                    header_row,
                    ft.Divider(height=20),
                    workspace_layout,
                ],
                expand=True,
            ),
            expand=True,
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

    # удаление бронирования

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