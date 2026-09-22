import pytest
import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse
from django.test import override_settings
from unittest.mock import Mock

from dashboard.views import BrevoPasswordResetForm


pytestmark = pytest.mark.django_db


def test_password_reset_form_page_loads(client):
    response = client.get(reverse("password_reset"))
    # This also verifies that the configured template path is resolvable.
    assert response.status_code == 200


def test_password_reset_unknown_email_shows_generic_confirmation(client):
    response = client.post(
        reverse("password_reset"),
        {"email": "not-a-real-account@example.com"},
    )
    assert response.status_code == 302
    assert response.url == reverse("password_reset_done")


def test_brevo_reset_form_requires_api_configuration():
    form = BrevoPasswordResetForm({"email": "person@example.com"})
    assert form.is_valid()

    with override_settings(BREVO_API_KEY="", BREVO_SENDER_EMAIL=""):
        with pytest.raises(ImproperlyConfigured):
            form.send_mail(
                "subject.txt",
                "email.txt",
                {},
                None,
                "person@example.com",
            )


def test_brevo_reset_form_posts_email_to_brevo(monkeypatch):
    from dashboard import views

    monkeypatch.setattr(
        views,
        "render_to_string",
        lambda template, context: (
            "Reset your password" if template == "subject.txt"
            else "Use this reset link"
        ),
    )
    fake_response = Mock(status_code=201)
    monkeypatch.setattr(views.requests, "post", Mock(return_value=fake_response))

    with override_settings(
        BREVO_API_KEY="test-key",
        BREVO_SENDER_EMAIL="verified@example.com",
        BREVO_SENDER_NAME="Forex Terminal",
    ):
        form = BrevoPasswordResetForm({"email": "person@example.com"})
        assert form.is_valid()
        form.send_mail(
            "subject.txt",
            "email.txt",
            {},
            None,
            "person@example.com",
        )

    call = views.requests.post.call_args
    assert call.args[0] == "https://api.brevo.com/v3/smtp/email"
    assert call.kwargs["headers"]["api-key"] == "test-key"
    assert call.kwargs["json"]["to"] == [{"email": "person@example.com"}]
    assert call.kwargs["json"]["sender"]["email"] == "verified@example.com"


def test_password_reset_confirm_and_complete_routes_exist(client):
    confirm = reverse(
        "password_reset_confirm",
        kwargs={"uidb64": "MQ", "token": "invalid-token"},
    )
    response = client.get(confirm)
    # Invalid token should render the invalid-link state, not a server error.
    assert response.status_code == 200

    complete = client.get(reverse("password_reset_complete"))
    assert complete.status_code == 200
