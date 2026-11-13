import json
import re


def get_csrf(client):
    client.get("/auth/login")
    with client.session_transaction() as session:
        return session.get("csrf_token")


def register(client, email="user@example.com", password="password123"):
    token = get_csrf(client)
    return client.post(
        "/auth/register",
        data={
            "email": email,
            "password": password,
            "confirm_password": password,
            "csrf_token": token,
        },
        follow_redirects=True,
    )


def login(client, email="user@example.com", password="password123"):
    token = get_csrf(client)
    return client.post(
        "/auth/login",
        data={"email": email, "password": password, "csrf_token": token},
        follow_redirects=True,
    )


def logout(client):
    token = get_csrf(client)
    return client.post(
        "/auth/logout",
        data={"csrf_token": token},
        follow_redirects=True,
    )


def api_headers(client):
    return {"X-CSRF-Token": get_csrf(client)}


def create_event(client, **overrides):
    payload = {
        "title": "Team meeting",
        "description": "Weekly sync",
        "start_date": "2026-11-10",
        "start_time": "10:00",
        "end_date": "2026-11-10",
        "end_time": "11:00",
    }
    payload.update(overrides)
    return client.post("/api/events", json=payload, headers=api_headers(client))


def calendar_data(client, start=None):
    url = "/calendar"
    if start:
        url += "?start=" + start
    response = client.get(url)
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    match = re.search(
        r'<script id="calendar-data" type="application/json">(.*?)</script>',
        html,
        re.S,
    )
    assert match is not None
    return json.loads(match.group(1))
