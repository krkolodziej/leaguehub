import pytest
from django.urls import reverse
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_health_endpoint_returns_ok():
    response = APIClient().get(reverse("health"))

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_openapi_schema_is_available():
    response = APIClient().get(reverse("schema"))

    assert response.status_code == 200
    assert response["Content-Type"].startswith("application/vnd.oai.openapi")
