import pytest

from apps.accounts.models import User


@pytest.mark.django_db
def test_create_user_normalizes_email_and_hashes_password():
    user = User.objects.create_user("  ALICE@Example.COM ", password="secret123")

    assert user.email == "alice@example.com"
    assert user.check_password("secret123")
    assert user.password != "secret123"
    assert user.created_at is not None
    assert user.updated_at is not None


@pytest.mark.django_db
def test_create_superuser_sets_required_flags():
    user = User.objects.create_superuser("admin@example.com", password="secret123")

    assert user.is_staff is True
    assert user.is_superuser is True
    assert user.is_active is True
