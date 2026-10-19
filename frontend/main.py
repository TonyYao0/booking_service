import flet as ft
import httpx
from datetime import datetime, time as dt_time

BACKEND_URL = "http://127.0.0.1:8000"


async def main(page: ft.Page):
    try:
        await _main_impl(page)
    except Exception as ex:
        import traceback
        traceback.print_exc()
        page.add(ft.Text(f"ERROR: {ex}", color=ft.Colors.RED_400))
        page.update()
        raise

async def _main_impl(page: ft.Page):
    page.title = "Система бронирования | Личный кабинет"
    page.theme_mode = ft.ThemeMode.DARK
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    WORK_START = dt_time(9, 0)
    WORK_END = dt_time(21, 0)

    auth_token = None
    user_name = ""
    user_role = ""

    # ------------------------------------------------------------------
    # Профиль пользователя
    # ------------------------------------------------------------------
    profile_email = ft.Text("", size=16, color=ft.Colors.ON_SURFACE_VARIANT)
    profile_name_input = ft.TextField(
        label="Имя и фамилия",
        width=350,
        prefix_icon=ft.Icons.PERSON,
    )
    profile_status = ft.Text("", size=14)

    pwd_current_input = ft.TextField(
        label="Текущий пароль",
        password=True,
        can_reveal_password=True,
        width=350,
        prefix_icon=ft.Icons.LOCK,
    )
    pwd_new_input = ft.TextField(
        label="Новый пароль (минимум 6 символов)",
        password=True,
        can_reveal_password=True,
        width=350,
        prefix_icon=ft.Icons.LOCK,
    )
    pwd_confirm_input = ft.TextField(
        label="Повторите новый пароль",
        password=True,
        can_reveal_password=True,
        width=350,
        prefix_icon=ft.Icons.LOCK,
    )
    pwd_status = ft.Text("", size=14)

    async def change_password(e):
        current = pwd_current_input.value or ""
        new = pwd_new_input.value or ""
        confirm = pwd_confirm_input.value or ""

        if not current:
            pwd_status.value = "⚠️ Введите текущий пароль"
            pwd_status.color = ft.Colors.ORANGE_400
            page.update()
            return

        if len(new) < 6:
            pwd_status.value = "⚠️ Новый пароль минимум 6 символов"
            pwd_status.color = ft.Colors.ORANGE_400
            page.update()
            return

        if new != confirm:
            pwd_status.value = "⚠️ Пароли не совпадают"
            pwd_status.color = ft.Colors.ORANGE_400
            page.update()
            return

        if new == current:
            pwd_status.value = "⚠️ Новый пароль совпадает с текущим"
            pwd_status.color = ft.Colors.ORANGE_400
            page.update()
            return

        pwd_status.value = "Сохранение..."
        pwd_status.color = ft.Colors.BLUE_200
        page.update()

        headers = {"Authorization": f"Bearer {auth_token}"}
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.patch(
                    f"{BACKEND_URL}/auth/me/password",
                    json={
                        "current_password": current,
                        "new_password": new,
                    },
                    headers=headers,
                )
            if resp.status_code == 200:
                pwd_current_input.value = ""
                pwd_new_input.value = ""
                pwd_confirm_input.value = ""
                pwd_status.value = ""
                snack = ft.SnackBar(
                    content=ft.Text("🔑 Пароль обновлён"),
                    bgcolor=ft.Colors.GREEN_400,
                    duration=2500,
                )
                page.overlay.append(snack)
                snack.open = True
                page.update()
                return
            else:
                detail = resp.json().get("detail", f"Код {resp.status_code}")
                pwd_status.value = f"🔴 {detail}"
                pwd_status.color = ft.Colors.RED_400
        except Exception as ex:
            pwd_status.value = f"❌ Ошибка сети: {ex}"
            pwd_status.color = ft.Colors.RED_400
        page.update()


    async def save_profile(e):
        new_name = (profile_name_input.value or "").strip()
        if len(new_name) < 2:
            profile_status.value = "⚠️ Имя должно быть минимум 2 символа"
            profile_status.color = ft.Colors.ORANGE_400
            page.update()
            return

        profile_status.value = "Сохранение..."
        profile_status.color = ft.Colors.BLUE_200
        page.update()

        headers = {"Authorization": f"Bearer {auth_token}"}
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.patch(
                    f"{BACKEND_URL}/auth/me",
                    json={"full_name": new_name},
                    headers=headers,
                )
            if resp.status_code == 200:
                nonlocal user_name
                user_name = new_name
                snack = ft.SnackBar(
                    content=ft.Text("✅ Профиль обновлён"),
                    bgcolor=ft.Colors.GREEN_400,
                    duration=2000,
                )
                page.overlay.append(snack)
                snack.open = True
                page.update()
                await load_dashboard()
                return
            else:
                detail = resp.json().get("detail", f"Код {resp.status_code}")
                profile_status.value = f"🔴 {detail}"
                profile_status.color = ft.Colors.RED_400
        except Exception as ex:
            profile_status.value = f"❌ Ошибка сети: {ex}"
            profile_status.color = ft.Colors.RED_400
        page.update()

    async def show_profile(e=None):
        profile_status.value = ""
        page.clean()
        page.vertical_alignment = ft.MainAxisAlignment.CENTER
        page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

        headers = {"Authorization": f"Bearer {auth_token}"}
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(
                    f"{BACKEND_URL}/auth/me", headers=headers
                )
            if resp.status_code == 200:
                me = resp.json()
                profile_email.value = me.get("email", "")
                profile_name_input.value = me.get("full_name", "")
            else:
                profile_email.value = "(не удалось загрузить)"
        except Exception as ex:
            profile_email.value = f"(ошибка: {ex})"

        profile_card = ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "Профиль",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.BLUE_400,
                    ),
                    ft.Container(height=15),
                    ft.Text("Email:", size=14, color=ft.Colors.ON_SURFACE_VARIANT),
                    profile_email,
                    ft.Container(height=15),
                    profile_name_input,
                    ft.Container(height=15),
                    ft.Button(
                        content="Сохранить",
                        icon=ft.Icons.SAVE,
                        on_click=save_profile,
                        width=350,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=8)
                        ),
                    ),
                    ft.Container(height=10),
                    profile_status,
                    ft.Divider(height=30),
                    ft.Text(
                        "Смена пароля",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.ORANGE_400,
                    ),
                    ft.Container(height=10),
                    pwd_current_input,
                    ft.Container(height=10),
                    pwd_new_input,
                    ft.Container(height=10),
                    pwd_confirm_input,
                    ft.Container(height=15),
                    ft.Button(
                        content="Сменить пароль",
                        icon=ft.Icons.KEY,
                        on_click=change_password,
                        width=350,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=8),
                            color=ft.Colors.ORANGE_400,
                        ),
                    ),
                    ft.Container(height=10),
                    pwd_status,
                    ft.Container(height=5),
                    ft.TextButton(
                        content="← Назад в кабинет",
                        on_click=lambda e: page.run_task(load_dashboard),
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            padding=30,
            border_radius=16,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
        )

        page.add(profile_card)
        page.update()
        

    def pretty_date(iso_str) -> str:
        if not iso_str or iso_str == "Дата не указана":
            return "Дата не указана"
        try:
            cleaned = iso_str.replace("Z", "+00:00")
            dt = datetime.fromisoformat(cleaned)
            return dt.strftime("%d.%m.%Y в %H:%M")
        except Exception:
            return iso_str
    # ------------------------------------------------------------------
    # Поля формы авторизации
    # ------------------------------------------------------------------
    # ------------------------------------------------------------------
    # Кабинет мастера
    # ------------------------------------------------------------------
    async def load_master_dashboard():
        page.clean()
        page.vertical_alignment = ft.MainAxisAlignment.START
        page.horizontal_alignment = ft.CrossAxisAlignment.START

        page.add(ft.Text("Загрузка записей...", size=16))
        page.update()

        headers = {"Authorization": f"Bearer {auth_token}"}
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(
                    f"{BACKEND_URL}/bookings/master", headers=headers
                )
            if res.status_code != 200:
                page.clean()
                page.add(
                    ft.Text(
                        f"🔴 Ошибка загрузки: {res.status_code}",
                        color=ft.Colors.RED_400,
                    )
                )
                page.update()
                return
            bookings = res.json()
        except Exception as ex:
            page.clean()
            page.add(ft.Text(f"❌ {ex}", color=ft.Colors.RED_400))
            page.update()
            return

        page.clean()

        welcome = (
            f"Кабинет мастера: {user_name}"
            if user_name
            else "Кабинет мастера"
        )
        header_row = ft.Row(
            [
                ft.Text(
                    welcome,
                    size=28,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.ORANGE_400,
                ),
                ft.Row(
                    [
                        ft.IconButton(
                            icon=ft.Icons.REFRESH,
                            icon_color=ft.Colors.BLUE_200,
                            tooltip="Обновить",
                            on_click=lambda e: page.run_task(load_master_dashboard),
                        ),
                        ft.Button(
                            content="Выйти",
                            icon=ft.Icons.LOGOUT,
                            on_click=logout_user,
                            style=ft.ButtonStyle(color=ft.Colors.RED_400),
                        ),
                    ],
                    spacing=5,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        async def set_status(booking_id: int, new_status: str):
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.patch(
                        f"{BACKEND_URL}/bookings/{booking_id}/status",
                        json={"status": new_status},
                        headers=headers,
                    )
                if resp.status_code == 200:
                    label = {
                        "confirmed": "✅ Бронь подтверждена",
                        "completed": "🏁 Бронь завершена",
                        "cancelled": "🗑️ Бронь отменена",
                    }.get(new_status, "Обновлено")
                    snack = ft.SnackBar(
                        content=ft.Text(label),
                        bgcolor=ft.Colors.GREEN_400,
                        duration=2000,
                    )
                    page.overlay.append(snack)
                    snack.open = True
                    page.update()
                    await load_master_dashboard()
                else:
                    detail = resp.json().get("detail", f"Код {resp.status_code}")
                    snack = ft.SnackBar(
                        content=ft.Text(f"🔴 {detail}"),
                        bgcolor=ft.Colors.RED_400,
                    )
                    page.overlay.append(snack)
                    snack.open = True
                    page.update()
            except Exception as ex:
                snack = ft.SnackBar(
                    content=ft.Text(f"❌ {ex}"),
                    bgcolor=ft.Colors.RED_400,
                )
                page.overlay.append(snack)
                snack.open = True
                page.update()

        bookings_container = ft.Column(
            spacing=15, scroll=ft.ScrollMode.AUTO, expand=True
        )

        if not bookings:
            bookings_container.controls.append(
                ft.Text(
                    "Пока нет записей к вам.",
                    size=16,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                )
            )
        else:
            for b in bookings:
                status = b.get("status") or "created"
                if status == "cancelled":
                    status_color = ft.Colors.RED_400
                elif status in ("completed", "done"):
                    status_color = ft.Colors.BLUE_400
                elif status == "confirmed":
                    status_color = ft.Colors.GREEN_400
                else:
                    status_color = ft.Colors.ORANGE_400

                date_display = b.get("start_time") or "Дата не указана"
                booking_id = b.get("id")

                action_buttons = []
                if status in ("created", "pending"):
                    action_buttons.append(
                        ft.Button(
                            content="Подтвердить",
                            icon=ft.Icons.CHECK,
                            on_click=lambda e, bid=booking_id: page.run_task(
                                set_status, bid, "confirmed"
                            ),
                            style=ft.ButtonStyle(
                                bgcolor=ft.Colors.GREEN_600,
                                color=ft.Colors.WHITE,
                            ),
                        )
                    )
                    action_buttons.append(
                        ft.Button(
                            content="Отменить",
                            icon=ft.Icons.CLOSE,
                            on_click=lambda e, bid=booking_id: page.run_task(
                                set_status, bid, "cancelled"
                            ),
                            style=ft.ButtonStyle(color=ft.Colors.RED_400),
                        )
                    )
                elif status == "confirmed":
                    action_buttons.append(
                        ft.Button(
                            content="Завершить",
                            icon=ft.Icons.DONE_ALL,
                            on_click=lambda e, bid=booking_id: page.run_task(
                                set_status, bid, "completed"
                            ),
                            style=ft.ButtonStyle(
                                bgcolor=ft.Colors.BLUE_600,
                                color=ft.Colors.WHITE,
                            ),
                        )
                    )
                    action_buttons.append(
                        ft.Button(
                            content="Отменить",
                            icon=ft.Icons.CLOSE,
                            on_click=lambda e, bid=booking_id: page.run_task(
                                set_status, bid, "cancelled"
                            ),
                            style=ft.ButtonStyle(color=ft.Colors.RED_400),
                        )
                    )

                actions_row = (
                    ft.Row(action_buttons, spacing=10)
                    if action_buttons
                    else ft.Text("—", color=ft.Colors.ON_SURFACE_VARIANT)
                )

                bookings_container.controls.append(
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Text(
                                    f"📅 {pretty_date(date_display)}",
                                    size=16,
                                    weight=ft.FontWeight.BOLD,
                                ),
                                ft.Text(
                                    f"Клиент: "
                                    f"{b.get('client_name') or b.get('client_id')}",
                                    size=14,
                                    color=ft.Colors.ON_SURFACE_VARIANT,
                                ),
                                ft.Text(
                                    f"Услуга: "
                                    f"{b.get('service_name') or b.get('service_id')}",
                                    size=14,
                                    color=ft.Colors.ON_SURFACE_VARIANT,
                                ),
                                ft.Row(
                                    [
                                        ft.Text(
                                            f"Статус: {status}",
                                            size=14,
                                            color=status_color,
                                        ),
                                        ft.Container(expand=True),
                                        actions_row,
                                    ],
                                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                            ]
                        ),
                        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                        padding=15,
                        border_radius=10,
                        width=700,
                        border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
                    )
                )

        main_layout = ft.Container(
            padding=30,
            content=ft.Column(
                [header_row, ft.Divider(height=20), bookings_container],
                expand=True,
            ),
            expand=True,
        )
        page.add(main_layout)
        page.update()

    # ------------------------------------------------------------------
    # Админ-панель
    # ------------------------------------------------------------------
    async def load_admin_dashboard():
        page.clean()
        page.vertical_alignment = ft.MainAxisAlignment.START
        page.horizontal_alignment = ft.CrossAxisAlignment.START

        page.add(ft.Text("Загрузка админ-панели...", size=16))
        page.update()

        headers = {"Authorization": f"Bearer {auth_token}"}
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res_services = await client.get(f"{BACKEND_URL}/services")
                res_all_services = await client.get(f"{BACKEND_URL}/services/all", headers=headers)
                res_users = await client.get(f"{BACKEND_URL}/users", headers=headers)
                res_bookings = await client.get(f"{BACKEND_URL}/bookings", headers=headers)

            if res_users.status_code != 200:
                page.clean()
                page.add(ft.Text(f"🔴 Ошибка доступа: {res_users.status_code}", color=ft.Colors.RED_400))
                page.update()
                return

            services = res_services.json() if res_services.status_code == 200 else []
            all_services = res_all_services.json() if res_all_services.status_code == 200 else services
            users = res_users.json()
            bookings = res_bookings.json() if res_bookings.status_code == 200 else []

            # Скрытые = есть в all, но нет в активных
            active_ids = {s["id"] for s in services}
            hidden_services = [s for s in all_services if s["id"] not in active_ids]

        except Exception as ex:
            page.clean()
            page.add(ft.Text(f"❌ {ex}", color=ft.Colors.RED_400))
            page.update()
            return

        page.clean()

        # --- Шапка ---
        header_row = ft.Row(
            [
                ft.Text(
                    f"Админ-панель: {user_name}",
                    size=28,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.PURPLE_400,
                ),
                ft.Row(
                    [
                        ft.IconButton(
                            icon=ft.Icons.REFRESH,
                            icon_color=ft.Colors.BLUE_200,
                            tooltip="Обновить",
                            on_click=lambda e: page.run_task(load_admin_dashboard),
                        ),
                        ft.Button(
                            content="Выйти",
                            icon=ft.Icons.LOGOUT,
                            on_click=logout_user,
                            style=ft.ButtonStyle(color=ft.Colors.RED_400),
                        ),
                    ],
                    spacing=5,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # --- Управление услугами ---
        async def create_service(e):
            name = (new_svc_name.value or "").strip()
            price_str = (new_svc_price.value or "").strip()
            duration_str = (new_svc_duration.value or "").strip()

            if len(name) < 2:
                svc_status.value = "⚠️ Название минимум 2 символа"
                svc_status.color = ft.Colors.ORANGE_400
                page.update()
                return
            try:
                price = int(price_str)
                duration = int(duration_str)
                if price < 0 or duration <= 0:
                    raise ValueError
            except ValueError:
                svc_status.value = "⚠️ Цена и длительность должны быть числами"
                svc_status.color = ft.Colors.ORANGE_400
                page.update()
                return

            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.post(
                        f"{BACKEND_URL}/services",
                        json={"name": name, "price": price, "duration_minutes": duration},
                        headers=headers,
                    )
                if resp.status_code == 201:
                    new_svc_name.value = ""
                    new_svc_price.value = ""
                    new_svc_duration.value = ""
                    snack = ft.SnackBar(content=ft.Text("✅ Услуга добавлена"), bgcolor=ft.Colors.GREEN_400)
                    page.overlay.append(snack)
                    snack.open = True
                    page.update()
                    await load_admin_dashboard()
                else:
                    svc_status.value = f"🔴 Ошибка: {resp.status_code}"
                    svc_status.color = ft.Colors.RED_400
                    page.update()
            except Exception as ex:
                svc_status.value = f"❌ {ex}"
                svc_status.color = ft.Colors.RED_400
                page.update()

        async def delete_service(svc_id: int):
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.delete(
                        f"{BACKEND_URL}/services/{svc_id}",
                        headers=headers,
                    )
                if resp.status_code == 204:
                    snack = ft.SnackBar(
                        content=ft.Text("🗑️ Услуга скрыта (можно восстановить)"),
                        bgcolor=ft.Colors.ORANGE_400,
                    )
                    page.overlay.append(snack)
                    snack.open = True
                    page.update()
                    await load_admin_dashboard()
                else:
                    try:
                        detail = resp.json().get("detail", f"Ошибка {resp.status_code}")
                    except Exception:
                        detail = f"Ошибка {resp.status_code}"
                    snack = ft.SnackBar(content=ft.Text(f"🔴 {detail}"), bgcolor=ft.Colors.RED_400)
                    page.overlay.append(snack)
                    snack.open = True
                    page.update()
            except Exception as ex:
                snack = ft.SnackBar(content=ft.Text(f"❌ {ex}"), bgcolor=ft.Colors.RED_400)
                page.overlay.append(snack)
                snack.open = True
                page.update()

        async def restore_service(svc_id: int):
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.post(
                        f"{BACKEND_URL}/services/{svc_id}/restore",
                        headers=headers,
                    )
                if resp.status_code == 200:
                    snack = ft.SnackBar(
                        content=ft.Text("♻️ Услуга восстановлена"),
                        bgcolor=ft.Colors.GREEN_400,
                    )
                    page.overlay.append(snack)
                    snack.open = True
                    page.update()
                    await load_admin_dashboard()
                else:
                    try:
                        detail = resp.json().get("detail", f"Ошибка {resp.status_code}")
                    except Exception:
                        detail = f"Ошибка {resp.status_code}"
                    snack = ft.SnackBar(content=ft.Text(f"🔴 {detail}"), bgcolor=ft.Colors.RED_400)
                    page.overlay.append(snack)
                    snack.open = True
                    page.update()
            except Exception as ex:
                snack = ft.SnackBar(content=ft.Text(f"❌ {ex}"), bgcolor=ft.Colors.RED_400)
                page.overlay.append(snack)
                snack.open = True
                page.update()

        def _hidden_section(hidden):
            """Секция скрытых услуг с кнопками восстановления."""
            col = ft.Column(spacing=8)
            if not hidden:
                col.controls.append(
                    ft.Text("Нет скрытых услуг", size=12, color=ft.Colors.ON_SURFACE_VARIANT)
                )
                return col

            col.controls.append(
                ft.Text(
                    f"Скрытые ({len(hidden)})",
                    size=14,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                )
            )
            for s in hidden:
                col.controls.append(
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Column(
                                    [
                                        ft.Text(
                                            s.get("name", "—"),
                                            size=14,
                                            weight=ft.FontWeight.BOLD,
                                            color=ft.Colors.ON_SURFACE_VARIANT,
                                        ),
                                        ft.Text(
                                            f"{s.get('price', 0)} руб. · {s.get('duration_minutes', 0)} мин",
                                            size=12,
                                            color=ft.Colors.ON_SURFACE_VARIANT,
                                        ),
                                    ],
                                    expand=True,
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.RESTORE,
                                    icon_color=ft.Colors.GREEN_400,
                                    tooltip="Восстановить",
                                    on_click=lambda e, sid=s.get("id"): page.run_task(restore_service, sid),
                                ),
                            ],
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
                        padding=10,
                        border_radius=8,
                        border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
                    )
                )
            return col
        
        services_list = ft.Column(
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
        if not services:
            services_list.controls.append(
                ft.Text("Нет услуг", color=ft.Colors.ON_SURFACE_VARIANT, size=14)
            )
        else:
            for s in services:
                services_list.controls.append(
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Column(
                                    [
                                        ft.Text(s.get("name", "—"), size=15, weight=ft.FontWeight.BOLD),
                                        ft.Text(
                                            f"{s.get('price', 0)} руб. · {s.get('duration_minutes', 0)} мин",
                                            size=13,
                                            color=ft.Colors.ON_SURFACE_VARIANT,
                                        ),
                                    ],
                                    expand=True,
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE_OUTLINE,
                                    icon_color=ft.Colors.RED_400,
                                    tooltip="Удалить",
                                    on_click=lambda e, sid=s.get("id"): page.run_task(delete_service, sid),
                                ),
                            ],
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
                        padding=12,
                        border_radius=8,
                        border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
                    )
                )

        new_svc_name = ft.TextField(label="Название услуги", width=240)
        new_svc_price = ft.TextField(label="Цена (руб.)", width=115)
        new_svc_duration = ft.TextField(label="Длит. (мин)", width=115)
        svc_status = ft.Text("", size=13)

        services_panel = ft.Container(
            content=ft.Column(
                [
                    ft.Text("Услуги", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_400),
                    ft.Container(height=10),
                    new_svc_name,
                    ft.Row([new_svc_price, new_svc_duration], spacing=10),
                    ft.Button(
                        content="Добавить услугу",
                        icon=ft.Icons.ADD,
                        on_click=create_service,
                        width=240,
                    ),
                    svc_status,
                    ft.Container(height=10),
                    services_list,
                    ft.Divider(height=20),
                    _hidden_section(hidden_services),
                ],
                expand=True,
            ),
            padding=20,
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            border_radius=12,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            expand=True,
        )

        # --- Пользователи ---
        users_list = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)
        if not users:
            users_list.controls.append(ft.Text("Нет пользователей", color=ft.Colors.ON_SURFACE_VARIANT))
        else:
            for u in users:
                role = (u.get("role") or "client").lower()
                role_color = (
                    ft.Colors.PURPLE_400 if role == "admin"
                    else ft.Colors.ORANGE_400 if role == "master"
                    else ft.Colors.BLUE_200
                )
                users_list.controls.append(
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Column(
                                    [
                                        ft.Text(u.get("full_name", "—"), size=14, weight=ft.FontWeight.BOLD),
                                        ft.Text(u.get("email", "—"), size=12, color=ft.Colors.ON_SURFACE_VARIANT),
                                    ],
                                    expand=True,
                                ),
                                ft.Text(role.upper(), size=12, color=role_color, weight=ft.FontWeight.BOLD),
                            ],
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
                        padding=10,
                        border_radius=8,
                    )
                )

        users_panel = ft.Container(
            content=ft.Column(
                [
                    ft.Text("Пользователи", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_400),
                    ft.Container(height=10),
                    users_list,
                ],
                expand=True,
            ),
            padding=20,
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            border_radius=12,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            expand=True,
        )

        # --- Брони ---
        bookings_list = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)
        if not bookings:
            bookings_list.controls.append(ft.Text("Нет броней", color=ft.Colors.ON_SURFACE_VARIANT))
        else:
            for b in bookings[:20]:
                status = b.get("status", "—")
                bookings_list.controls.append(
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Text(f"📅 {b.get('start_time', '—')}", size=13, weight=ft.FontWeight.BOLD),
                                ft.Text(
                                    f"Клиент #{b.get('client_id')} · Услуга #{b.get('service_id')} · Мастер #{b.get('master_id')}",
                                    size=12,
                                    color=ft.Colors.ON_SURFACE_VARIANT,
                                ),
                                ft.Text(f"Статус: {status}", size=12, color=ft.Colors.GREEN_400),
                            ]
                        ),
                        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
                        padding=10,
                        border_radius=8,
                    )
                )

        bookings_panel = ft.Container(
            content=ft.Column(
                [
                    ft.Text("Брони", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_400),
                    ft.Container(height=10),
                    bookings_list,
                ],
                expand=True,
            ),
            padding=20,
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            border_radius=12,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            expand=True,
        )

        workspace = ft.Column(
            [services_panel, users_panel, bookings_panel],
            spacing=15,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        main_layout = ft.Container(
            padding=20,
            content=ft.Column(
                [header_row, ft.Divider(height=20), workspace],
                expand=True,
            ),
            expand=True,
        )

        page.add(main_layout)
        page.update()

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
    # Поля формы регистрации
    # ------------------------------------------------------------------
    reg_email_input = ft.TextField(
        label="Email",
        width=350,
        prefix_icon=ft.Icons.EMAIL,
    )
    reg_full_name_input = ft.TextField(
        label="Имя и фамилия",
        width=350,
        prefix_icon=ft.Icons.PERSON,
    )
    reg_password_input = ft.TextField(
        label="Пароль (минимум 6 символов)",
        password=True,
        can_reveal_password=True,
        width=350,
        prefix_icon=ft.Icons.LOCK,
    )

    reg_password_confirm_input = ft.TextField(
        label="Повторите пароль",
        password=True,
        can_reveal_password=True,
        width=350,
        prefix_icon=ft.Icons.LOCK,
    )
    reg_status_text = ft.Text("", size=14)
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
        nonlocal user_name, user_role
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
        def confirm_cancel(booking_id: int, preview: str):
            """Диалог подтверждения перед удалением брони."""

            def close_dialog(_=None):
                dialog.open = False
                page.update()

            def do_cancel(_=None):
                dialog.open = False
                page.update()
                page.run_task(cancel_booking, booking_id)

            dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("Отмена бронирования"),
                content=ft.Text(
                    f"Вы уверены, что хотите отменить бронь?\n\n{preview}"
                ),
                actions=[
                    ft.TextButton(
                        content="Нет, оставить",
                        on_click=close_dialog,
                    ),
                    ft.TextButton(
                        content="Да, отменить",
                        on_click=do_cancel,
                        style=ft.ButtonStyle(color=ft.Colors.RED_400),
                    ),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )

            page.overlay.append(dialog)
            dialog.open = True
            page.update()


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
                res_me = await client.get(
                    f"{BACKEND_URL}/auth/me", headers=headers
                )

            # Имя пользователя для шапки
            if res_me.status_code == 200:
                me = res_me.json()
                user_name = me.get("full_name") or me.get("email", "")
                role_raw = me.get("role", "client")
                user_role = role_raw.split(".")[-1].lower() if "." in role_raw else role_raw.lower()
            if user_role == "master":
                await load_master_dashboard()
                return

            # Если админ — показываем админ-панель
            if user_role == "admin":
                await load_admin_dashboard()
                return
            

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
        service_names = {s["id"]: s["name"] for s in services}
        master_names = {m["id"]: m["full_name"] for m in masters}


        # --- Шапка ---
        welcome_text = (
            f"Привет, {user_name}!"
            if user_name
            else "Личный кабинет клиента"
        )
        header_row = ft.Row(
            [
                ft.Text(
                    welcome_text,
                    size=28,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLUE_400,
                ),
                ft.Row(
                    [
                        ft.IconButton(
                            icon=ft.Icons.PERSON_OUTLINE,
                            icon_color=ft.Colors.BLUE_200,
                            tooltip="Профиль",
                            on_click=show_profile,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.REFRESH,
                            icon_color=ft.Colors.BLUE_200,
                            tooltip="Обновить список",
                            on_click=lambda e: page.run_task(load_dashboard),
                        ),
                        ft.Button(
                            content="Выйти",
                            icon=ft.Icons.LOGOUT,
                            on_click=logout_user,
                            style=ft.ButtonStyle(color=ft.Colors.RED_400),
                        ),
                    ],
                    spacing=5,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
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
                    color=ft.Colors.ON_SURFACE_VARIANT,
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
                                on_click=lambda e, bid=booking_id, pv=pretty_date(date_display): confirm_cancel(bid, pv),
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
                                    f"📅 Дата и время: {pretty_date(date_display)}",
                                    size=16,
                                    weight=ft.FontWeight.BOLD,
                                ),
                                ft.Text(
                                    " · ".join(
                                        filter(None, [
                                            service_names.get(b.get("service_id")),
                                            master_names.get(b.get("master_id")),
                                        ])
                                    ) or f"Услуга #{b.get('service_id')} · Мастер #{b.get('master_id')}",
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
        selected_date_part = "2026-10-20"
        selected_time_part = "14:00"
        selected_date_str = f"{selected_date_part}T{selected_time_part}:00"

        def rebuild_datetime():
            nonlocal selected_date_str
            selected_date_str = f"{selected_date_part}T{selected_time_part}:00"

        date_button = ft.Button(
            content=f"Выбрать дату: {selected_date_part}",
            icon=ft.Icons.CALENDAR_MONTH,
            width=350,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        )

        time_button = ft.Button(
            content=f"Выбрать время: {selected_time_part}",
            icon=ft.Icons.ACCESS_TIME,
            width=350,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        )
        def handle_date_change(e):
            nonlocal selected_date_part
            if date_picker.value:
                selected_date_part = date_picker.value.strftime("%Y-%m-%d")
                date_button.content = f"Выбрать дату: {selected_date_part}"
                rebuild_datetime()
                page.update()
        page.overlay[:] = [
            c for c in page.overlay
            if not isinstance(c, (ft.DatePicker, ft.TimePicker))
        ]

        date_picker = ft.DatePicker(
            first_date=datetime.now(),
            last_date=datetime(2027, 12, 31),
            on_change=handle_date_change,
        )
        page.overlay.append(date_picker)

        def handle_time_change(e):
            nonlocal selected_time_part
            if not time_picker.value:
                return

            chosen = time_picker.value
            if not (WORK_START <= chosen <= WORK_END):
                snack = ft.SnackBar(
                    content=ft.Text(
                        f"⏰ Мы работаем с {WORK_START.strftime('%H:%M')} "
                        f"до {WORK_END.strftime('%H:%M')}"
                    ),
                    bgcolor=ft.Colors.ORANGE_400,
                    duration=3000,
                )
                page.overlay.append(snack)
                snack.open = True
                page.update()
                return

            selected_time_part = chosen.strftime("%H:%M")
            time_button.content = f"Выбрать время: {selected_time_part}"
            rebuild_datetime()
            page.update()

        time_picker = ft.TimePicker(
            value=dt_time(14, 0),
            on_change=handle_time_change,
        )
        page.overlay.append(time_picker)

        def open_date_picker(e):
            date_picker.open = True
            page.update()

        def open_time_picker(e):
            time_picker.open = True
            page.update()

        date_button.on_click = open_date_picker
        time_button.on_click = open_time_picker

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

        if not services or not masters:
            missing = []
            if not services:
                missing.append("услуги")
            if not masters:
                missing.append("мастера")

            right_column = ft.Container(
                content=ft.Column(
                    [
                        ft.Text(
                            "Запись временно недоступна",
                            size=18,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.ORANGE_400,
                        ),
                        ft.Container(height=10),
                        ft.Text(
                            f"В системе нет доступных: {' и '.join(missing)}.",
                            size=14,
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                        ft.Text(
                            "Обратитесь к администратору.",
                            size=14,
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                padding=30,
                width=390,
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
                border_radius=12,
                border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            )
        else:
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
                        ft.Container(height=5),
                        time_button,
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
    # Переключение между формами
    # ------------------------------------------------------------------
    async def show_login(e=None):
        page.clean()
        page.vertical_alignment = ft.MainAxisAlignment.CENTER
        page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        page.add(auth_card)
        page.update()

    async def show_register(e=None):
        reg_status_text.value = ""
        page.clean()
        page.vertical_alignment = ft.MainAxisAlignment.CENTER
        page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        page.add(register_card)
        page.update()

    # ------------------------------------------------------------------
    # Регистрация
    # ------------------------------------------------------------------
    async def register_user(e):
        email = (reg_email_input.value or "").strip()
        full_name = (reg_full_name_input.value or "").strip()
        password = reg_password_input.value or ""
        password_confirm = reg_password_confirm_input.value or ""

        # Валидация на фронте
        if not email or "@" not in email or "." not in email:
            reg_status_text.value = "⚠️ Введите корректный email"
            reg_status_text.color = ft.Colors.ORANGE_400
            page.update()
            return

        if len(full_name) < 2:
            reg_status_text.value = "⚠️ Имя должно быть минимум 2 символа"
            reg_status_text.color = ft.Colors.ORANGE_400
            page.update()
            return

        if len(password) < 6:
            reg_status_text.value = "⚠️ Пароль должен быть минимум 6 символов"
            reg_status_text.color = ft.Colors.ORANGE_400
            page.update()
            return

        if password != password_confirm:
            reg_status_text.value = "⚠️ Пароли не совпадают"
            reg_status_text.color = ft.Colors.ORANGE_400
            page.update()
            return

        reg_status_text.value = "Регистрация..."
        reg_status_text.color = ft.Colors.BLUE_200
        page.update()

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    f"{BACKEND_URL}/auth/register",
                    json={
                        "email": email,
                        "full_name": full_name,
                        "password": password,
                    },
                )

            if response.status_code == 201:
                snack = ft.SnackBar(
                    content=ft.Text("🎉 Регистрация успешна! Входим..."),
                    bgcolor=ft.Colors.GREEN_400,
                )
                page.overlay.append(snack)
                snack.open = True

                # Очищаем поля регистрации
                reg_email_input.value = ""
                reg_full_name_input.value = ""
                reg_password_input.value = ""
                reg_password_confirm_input.value = ""

                # Автоматический вход
                email_input.value = email
                password_input.value = password
                page.update()

                await login_user(None)
                return
            else:
                err = response.json().get("detail", "Ошибка регистрации")
                if isinstance(err, list):
                    err = "; ".join(
                        f"{e.get('loc', ['?'])[-1]}: {e.get('msg')}"
                        for e in err
                    )
                reg_status_text.value = f"🔴 {err}"
                reg_status_text.color = ft.Colors.RED_400
        except Exception as ex:
            reg_status_text.value = f"❌ Ошибка сети: {ex}"
            reg_status_text.color = ft.Colors.RED_400

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
                ft.Container(height=5),
                ft.TextButton(
                    content="Нет аккаунта? Зарегистрироваться",
                    on_click=show_register,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
        padding=30,
        border_radius=16,
        border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
    )
    # ------------------------------------------------------------------
    # Карточка регистрации
    # ------------------------------------------------------------------
    register_button = ft.Button(
        content="Зарегистрироваться",
        icon=ft.Icons.PERSON_ADD,
        on_click=register_user,
        width=350,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
    )

    register_card = ft.Container(
        content=ft.Column(
            [
                ft.Text(
                    "Регистрация",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.GREEN_400,
                ),
                ft.Container(height=15),
                reg_email_input,
                ft.Container(height=10),
                reg_full_name_input,
                ft.Container(height=10),
                reg_password_input,
                ft.Container(height=10),
                reg_password_confirm_input,
                ft.Container(height=15),
                register_button,
                ft.Container(height=10),
                reg_status_text,
                ft.Container(height=5),
                ft.TextButton(
                    content="Уже есть аккаунт? Войти",
                    on_click=show_login,
                ),
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
    page.update()

    # В фоне пытаемся восстановить сессию


if __name__ == "__main__":
    ft.run(main, view=ft.AppView.WEB_BROWSER, port=8500)