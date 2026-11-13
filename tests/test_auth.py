from sqlalchemy import select

from app import db
from app.models import User
from tests import helpers


def _user_count(app):
    with app.app_context():
        return len(db.session.execute(select(User)).scalars().all())


def test_registration_creates_user_and_logs_in(client, app):
    response = helpers.register(client)

    assert response.status_code == 200
    assert "Weekly calendar" in response.get_data(as_text=True)

    with app.app_context():
        user = db.session.execute(
            select(User).where(User.email == "user@example.com")
        ).scalar_one_or_none()
        assert user is not None
        assert user.password_hash != "password123"
        assert user.check_password("password123")


def test_registration_rejects_invalid_email(client, app):
    token = helpers.get_csrf(client)
    response = client.post(
        "/auth/register",
        data={
            "email": "not-an-email",
            "password": "password123",
            "confirm_password": "password123",
            "csrf_token": token,
        },
        follow_redirects=True,
    )

    assert b"valid email" in response.data
    assert _user_count(app) == 0


def test_registration_rejects_mismatched_passwords(client, app):
    token = helpers.get_csrf(client)
    response = client.post(
        "/auth/register",
        data={
            "email": "user@example.com",
            "password": "password123",
            "confirm_password": "different123",
            "csrf_token": token,
        },
        follow_redirects=True,
    )

    assert b"Passwords do not match" in response.data
    assert _user_count(app) == 0


def test_registration_rejects_duplicate_email_case_insensitively(client, app):
    helpers.register(client, email="User@Example.com")
    helpers.logout(client)

    response = helpers.register(client, email="user@example.com")

    assert b"already exists" in response.data
    assert _user_count(app) == 1


def test_login_does_not_redirect_to_external_urls(client):
    helpers.register(client)
    helpers.logout(client)
    token = helpers.get_csrf(client)

    response = client.post(
        "/auth/login",
        data={
            "email": "user@example.com",
            "password": "password123",
            "csrf_token": token,
            "next": "//evil.example",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"] == "/calendar"


def test_login_success_and_incorrect_password(client):
    helpers.register(client)
    helpers.logout(client)

    bad = helpers.login(client, password="wrong-password")
    assert b"Invalid email or password" in bad.data

    good = helpers.login(client)
    assert "Weekly calendar" in good.get_data(as_text=True)


def test_logout_clears_session_and_protects_calendar(client):
    helpers.register(client)
    helpers.logout(client)

    response = client.get("/calendar")

    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_calendar_requires_login(client):
    response = client.get("/calendar")

    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_api_requires_login(client):
    response = client.get("/api/events")

    assert response.status_code == 401
    assert response.get_json()["error"] == "Authentication required."


def test_state_changing_request_requires_csrf(client):
    response = client.post("/api/events", json={"title": "No token"})

    assert response.status_code == 400
    assert "CSRF" in response.get_json()["error"]
