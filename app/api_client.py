import httpx

BACKEND_URL = "http://127.0.0.1:8000"


async def login(email: str, password: str):
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{BACKEND_URL}/auth/login",
                data={"username": email, "password": password},
            )
        if resp.status_code == 200:
            return resp.json().get("access_token")
        return None
    except Exception:
        return None


async def get_services():
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{BACKEND_URL}/services")
        return resp.json() if resp.status_code == 200 else []
    except Exception:
        return []


async def get_masters():
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{BACKEND_URL}/masters")
        return resp.json() if resp.status_code == 200 else []
    except Exception:
        return []


async def create_booking(token, service_id, master_id, start_time):
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{BACKEND_URL}/bookings",
                json={
                    "client_id": 0,
                    "master_id": master_id,
                    "service_id": service_id,
                    "start_time": start_time,
                },
                headers={"Authorization": f"Bearer {token}"},
            )
        try:
            return resp.status_code, resp.json()
        except Exception:
            return resp.status_code, resp.text
    except Exception as ex:
        return 0, str(ex)


async def get_my_bookings(token):
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{BACKEND_URL}/bookings/my",
                headers={"Authorization": f"Bearer {token}"},
            )
        return resp.json() if resp.status_code == 200 else []
    except Exception:
        return []