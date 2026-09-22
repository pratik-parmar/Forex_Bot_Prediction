import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

from dashboard.models import EmailVerification


pytestmark = pytest.mark.django_db
User = get_user_model()


def test_login_page_loads(client):
    response = client.get(reverse("login"))
    assert response.status_code == 200
    assert b"Forex Terminal" in response.content


def test_active_user_can_log_in(client, user):
    response = client.post(
        reverse("login"),
        {"username": user.username, "password": "TestPass!234"},
    )
    assert response.status_code == 302
    assert response.url == reverse("dashboard_index")


def test_invalid_password_does_not_log_in(client, user):
    response = client.post(
        reverse("login"),
        {"username": user.username, "password": "wrong-password"},
    )
    assert response.status_code == 200
    assert "_auth_user_id" not in client.session


def test_inactive_user_cannot_log_in(client, inactive_user):
    response = client.post(
        reverse("login"),
        {"username": inactive_user.username, "password": "TestPass!234"},
    )
    assert response.status_code == 200
    assert "_auth_user_id" not in client.session


def test_dashboard_requires_login(client):
    response = client.get(reverse("dashboard_index"))
    assert response.status_code == 302
    assert reverse("login") in response.url


def test_authenticated_user_can_open_dashboard(client, user):
    client.force_login(user)
    response = client.get(reverse("dashboard_index"))
    assert response.status_code == 200


def test_logout_clears_session(client, user):
    client.force_login(user)
    response = client.get(reverse("logout"))
    assert response.status_code == 302
    assert "_auth_user_id" not in client.session


def test_registration_get_loads(client):
    response = client.get(reverse("register"))
    assert response.status_code == 200


def test_registration_creates_inactive_account_and_verification(client, monkeypatch):
    from dashboard import views

    monkeypatch.setattr(
        views,
        "_issue_email_otp",
        lambda user, verification: (True, "OTP sent"),
    )
    response = client.post(
        reverse("register"),
        {
            "username": "newpytestuser",
            "email": "newpytest@example.com",
            "password1": "StrongTestPass!234",
            "password2": "StrongTestPass!234",
        },
    )

    assert response.status_code == 302
    created = User.objects.get(username="newpytestuser")
    assert created.is_active is False
    assert EmailVerification.objects.filter(user=created).exists()


def test_registration_rejects_duplicate_email(client, user):
    response = client.post(
        reverse("register"),
        {
            "username": "different_user",
            "email": user.email.upper(),
            "password1": "StrongTestPass!234",
            "password2": "StrongTestPass!234",
        },
    )
    assert response.status_code == 200
    assert not User.objects.filter(username="different_user").exists()


def test_email_verification_accepts_correct_otp(client, monkeypatch):
    from django.contrib.auth.hashers import make_password

    account = User.objects.create_user(
        username="otp_user",
        email="otp.user@example.com",
        password="StrongTestPass!234",
        is_active=False,
    )
    verification = EmailVerification.objects.create(
        user=account,
        otp_hash=make_password("123456"),
        expires_at=timezone.now() + timezone.timedelta(minutes=5),
    )
    uidb64 = urlsafe_base64_encode(force_bytes(account.pk))

    response = client.post(
        reverse("verify_email", kwargs={"uidb64": uidb64}),
        {"otp": "123456"},
    )

    account.refresh_from_db()
    assert response.status_code == 302
    assert account.is_active is True
    assert not EmailVerification.objects.filter(pk=verification.pk).exists()


def test_email_verification_rejects_wrong_otp(client):
    from django.contrib.auth.hashers import make_password

    account = User.objects.create_user(
        username="otp_wrong_user",
        email="wrong.otp@example.com",
        password="StrongTestPass!234",
        is_active=False,
    )
    EmailVerification.objects.create(
        user=account,
        otp_hash=make_password("123456"),
        expires_at=timezone.now() + timezone.timedelta(minutes=5),
    )
    uidb64 = urlsafe_base64_encode(force_bytes(account.pk))

    response = client.post(
        reverse("verify_email", kwargs={"uidb64": uidb64}),
        {"otp": "000000"},
    )

    account.refresh_from_db()
    assert response.status_code == 200
    assert account.is_active is False
