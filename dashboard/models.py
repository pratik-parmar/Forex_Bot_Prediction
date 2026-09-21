from django.db import models

# Create your models here.
from django.conf import settings
from django.db import models


class EmailVerification(models.Model):
    """Stores only a hash of a short-lived email verification code."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="email_verification",
    )
    otp_hash = models.CharField(max_length=128, blank=True)
    expires_at = models.DateTimeField()
    attempts = models.PositiveSmallIntegerField(default=0)
    last_sent_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Email verification for user_id={self.user_id}"
