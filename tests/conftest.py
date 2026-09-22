import pytest
from django.contrib.auth import get_user_model


@pytest.fixture
def user(db):
    User = get_user_model()
    return User.objects.create_user(
        username="pytest_user",
        email="pytest.user@example.com",
        password="TestPass!234",
        is_active=True,
    )


@pytest.fixture
def inactive_user(db):
    User = get_user_model()
    return User.objects.create_user(
        username="inactive_user",
        email="inactive@example.com",
        password="TestPass!234",
        is_active=False,
    )
