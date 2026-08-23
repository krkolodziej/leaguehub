import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User


@pytest.fixture
def csrf_client():
    client = APIClient(enforce_csrf_checks=True)
    response = client.get("/api/v1/auth/csrf/")
    assert response.status_code == 200
    client.credentials(HTTP_X_CSRFTOKEN=response.data["csrfToken"])
    return client


@pytest.mark.django_db
def test_register_logs_user_in_and_returns_public_user_data(csrf_client):
    response = csrf_client.post(
        "/api/v1/auth/register/",
        {
            "email": "alice@example.com",
            "password": "StrongPassword123!",
            "password_confirm": "StrongPassword123!",
            "first_name": "Alice",
        },
        format="json",
    )

    assert response.status_code == 201
    assert response.data["email"] == "alice@example.com"
    assert "password" not in response.data
    assert csrf_client.get("/api/v1/auth/me/").data["first_name"] == "Alice"


@pytest.mark.django_db
def test_login_requires_csrf_and_accepts_valid_credentials():
    User.objects.create_user("alice@example.com", password="StrongPassword123!")
    client = APIClient(enforce_csrf_checks=True)

    rejected = client.post(
        "/api/v1/auth/login/",
        {"email": "alice@example.com", "password": "StrongPassword123!"},
        format="json",
    )
    assert rejected.status_code == 403

    csrf_response = client.get("/api/v1/auth/csrf/")
    client.credentials(HTTP_X_CSRFTOKEN=csrf_response.data["csrfToken"])
    accepted = client.post(
        "/api/v1/auth/login/",
        {"email": "alice@example.com", "password": "StrongPassword123!"},
        format="json",
    )

    assert accepted.status_code == 200
    assert client.get("/api/v1/auth/me/").data["email"] == "alice@example.com"


@pytest.mark.django_db
def test_invalid_login_and_registration_validation():
    User.objects.create_user("alice@example.com", password="StrongPassword123!")
    client = APIClient(enforce_csrf_checks=True)
    csrf_response = client.get("/api/v1/auth/csrf/")
    client.credentials(HTTP_X_CSRFTOKEN=csrf_response.data["csrfToken"])

    invalid_login = client.post(
        "/api/v1/auth/login/",
        {"email": "alice@example.com", "password": "wrong-password"},
        format="json",
    )
    duplicate = client.post(
        "/api/v1/auth/register/",
        {
            "email": " ALICE@example.com ",
            "password": "StrongPassword123!",
            "password_confirm": "StrongPassword123!",
        },
        format="json",
    )
    mismatch = client.post(
        "/api/v1/auth/register/",
        {
            "email": "bob@example.com",
            "password": "StrongPassword123!",
            "password_confirm": "DifferentPassword123!",
        },
        format="json",
    )

    assert invalid_login.status_code == 400
    assert duplicate.status_code == 400
    assert mismatch.status_code == 400


@pytest.mark.django_db
def test_logout_clears_session_and_me_requires_authentication(csrf_client):
    User.objects.create_user("alice@example.com", password="StrongPassword123!")
    login_response = csrf_client.post(
        "/api/v1/auth/login/",
        {"email": "alice@example.com", "password": "StrongPassword123!"},
        format="json",
    )
    assert login_response.status_code == 200
    refreshed_csrf = csrf_client.get("/api/v1/auth/csrf/")
    csrf_client.credentials(HTTP_X_CSRFTOKEN=refreshed_csrf.data["csrfToken"])

    logout_response = csrf_client.post("/api/v1/auth/logout/", {}, format="json")

    assert logout_response.status_code == 204
    assert csrf_client.get("/api/v1/auth/me/").status_code == 401
