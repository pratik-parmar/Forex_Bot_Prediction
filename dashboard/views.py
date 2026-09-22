
import logging
import requests

from django.conf import settings
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import (
    PasswordResetConfirmView,
    PasswordResetCompleteView,
    PasswordResetDoneView,
)
from django.core.exceptions import ImproperlyConfigured
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.views.decorators.http import require_http_methods
from django.shortcuts import render, redirect

import logging
import secrets
from datetime import timedelta

import requests

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password, check_password
from django.db import transaction, IntegrityError
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.http import (
    url_has_allowed_host_and_scheme,
    urlsafe_base64_decode,
    urlsafe_base64_encode,
)
from django.utils.encoding import force_bytes, force_str

from dashboard.forms import RegisterForm
from dashboard.models import EmailVerification
from dashboard.technical import calculate_technical_analysis
from data.market_data import get_market_candles
from dashboard.decorators import api_login_required


logger = logging.getLogger(__name__)


# =========================================================
# CONFIGURATION
# =========================================================

SUPPORTED_SYMBOLS = {"XAUUSD", "EURUSD", "GBPUSD", "BTCUSD"}

OTP_LENGTH = 6
OTP_EXPIRY_MINUTES = 10
OTP_MAX_ATTEMPTS = 5
OTP_RESEND_COOLDOWN_SECONDS = 60

BREVO_EMAIL_API_URL = "https://api.brevo.com/v3/smtp/email"
BREVO_API_TIMEOUT = 15


# =========================================================
# DASHBOARD
# =========================================================

@login_required
def dashboard_index(request):
    return render(request, "dashboard/index.html")


# =========================================================
# LOGIN
# =========================================================

def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard_index")

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            user = form.get_user()

            if not user.is_active:
                form.add_error(
                    None,
                    "Please verify your email before signing in."
                )
            else:
                login(request, user)

                next_url = (
                    request.POST.get("next")
                    or request.GET.get("next")
                )

                if next_url and url_has_allowed_host_and_scheme(
                    next_url,
                    allowed_hosts={request.get_host()},
                    require_https=request.is_secure(),
                ):
                    return redirect(next_url)

                return redirect("dashboard_index")

    else:
        form = AuthenticationForm()

    return render(
        request,
        "dashboard/login.html",
        {"form": form}
    )


# =========================================================
# BREVO HTTPS EMAIL API
# =========================================================

def _send_brevo_email(recipient_email, subject, text_content):
    """
    Send a transactional email using Brevo's HTTPS API.

    Requires these environment variables:
        BREVO_API_KEY
        BREVO_SENDER_EMAIL
        BREVO_SENDER_NAME (optional)
    """

    api_key = getattr(settings, "BREVO_API_KEY", "")
    sender_email = getattr(settings, "BREVO_SENDER_EMAIL", "")
    sender_name = getattr(
        settings,
        "BREVO_SENDER_NAME",
        "Forex Terminal"
    )

    if not api_key:
        raise RuntimeError("BREVO_API_KEY is not configured.")

    if not sender_email:
        raise RuntimeError("BREVO_SENDER_EMAIL is not configured.")

    payload = {
        "sender": {
            "name": sender_name,
            "email": sender_email,
        },
        "to": [
            {
                "email": recipient_email,
            }
        ],
        "subject": subject,
        "textContent": text_content,
    }

    headers = {
        "accept": "application/json",
        "api-key": api_key,
        "content-type": "application/json",
    }

    response = requests.post(
        BREVO_EMAIL_API_URL,
        json=payload,
        headers=headers,
        timeout=BREVO_API_TIMEOUT,
    )

    # Brevo normally returns HTTP 201 when the email is accepted.
    # Raise for HTTP errors so registration/resend can handle failure.
    if not response.ok:
        logger.error(
            "Brevo API returned HTTP %s while sending email.",
            response.status_code,
        )
        response.raise_for_status()

    logger.info(
        "Brevo accepted a transactional email for recipient=%s",
        recipient_email,
    )


# =========================================================
# ISSUE EMAIL OTP
# =========================================================

def _issue_email_otp(user, verification):
    """
    Generate an OTP, save its hash, and send it through Brevo API.

    Returns:
        (True, success_message) if accepted by Brevo.
        (False, cooldown_message) if resend cooldown is active.

    Raises an exception if sending fails.
    """

    now = timezone.now()

    # Prevent repeated OTP requests within the cooldown period.
    if verification.last_sent_at:
        elapsed = (
            now - verification.last_sent_at
        ).total_seconds()

        if elapsed < OTP_RESEND_COOLDOWN_SECONDS:
            return (
                False,
                "Please wait a minute before requesting another code."
            )

    # Generate a secure 6-digit OTP.
    otp = f"{secrets.randbelow(10 ** OTP_LENGTH):0{OTP_LENGTH}d}"

    verification.otp_hash = make_password(otp)
    verification.expires_at = now + timedelta(
        minutes=OTP_EXPIRY_MINUTES
    )
    verification.attempts = 0
    verification.last_sent_at = now

    verification.save(
        update_fields=[
            "otp_hash",
            "expires_at",
            "attempts",
            "last_sent_at",
        ]
    )

    try:
        _send_brevo_email(
            recipient_email=user.email,
            subject="Verify your Forex Terminal email",
            text_content=(
                f"Your Forex Terminal verification code is {otp}.\n\n"
                f"This code expires in {OTP_EXPIRY_MINUTES} minutes.\n\n"
                "If you did not request this, you can ignore this email."
            ),
        )

    except Exception:
        # Invalidate the OTP if Brevo rejects the API request
        # or the request fails.
        verification.otp_hash = ""
        verification.save(update_fields=["otp_hash"])

        # Do not log the OTP or API key.
        logger.exception(
            "Failed to send verification email for user_id=%s",
            user.pk,
        )

        raise

    return (
        True,
        "A verification code has been sent to your email."
    )


# =========================================================
# REGISTRATION
# =========================================================

def register_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard_index")

    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = None

            try:
                # Create the inactive user and OTP record.
                with transaction.atomic():
                    user = form.save(commit=False)
                    user.is_active = False
                    user.save()

                    verification = EmailVerification.objects.create(
                        user=user,
                        expires_at=(
                            timezone.now()
                            + timedelta(minutes=OTP_EXPIRY_MINUTES)
                        ),
                    )

            except IntegrityError:
                logger.warning(
                    "Registration failed due to a database uniqueness conflict."
                )

                messages.error(
                    request,
                    "An account with these details may already exist."
                )

                return render(
                    request,
                    "dashboard/register.html",
                    {"form": form},
                )

            # Send OTP after the database transaction commits.
            try:
                sent, message = _issue_email_otp(
                    user,
                    verification
                )

            except Exception:
                # Keep the account inactive. The user can retry
                # using the Resend code option.
                messages.error(
                    request,
                    "We couldn't send the verification email right now. "
                    "Please try Resend code in a minute."
                )

                return redirect(
                    "verify_email",
                    uidb64=urlsafe_base64_encode(
                        force_bytes(user.pk)
                    ),
                )

            if sent:
                messages.success(request, message)
            else:
                messages.warning(request, message)

            return redirect(
                "verify_email",
                uidb64=urlsafe_base64_encode(
                    force_bytes(user.pk)
                ),
            )

    else:
        form = RegisterForm()

    return render(
        request,
        "dashboard/register.html",
        {"form": form}
    )


# =========================================================
# GET USER FOR EMAIL VERIFICATION
# =========================================================

def _get_verification_user(uidb64):
    try:
        user_id = force_str(
            urlsafe_base64_decode(uidb64)
        )

        return User.objects.get(pk=user_id)

    except (
        TypeError,
        ValueError,
        OverflowError,
        User.DoesNotExist,
    ):
        return None


# =========================================================
# EMAIL VERIFICATION
# =========================================================

def verify_email_view(request, uidb64):
    user = _get_verification_user(uidb64)

    if user is None:
        messages.error(
            request,
            "Invalid verification request."
        )
        return redirect("register")

    if user.is_active:
        messages.info(
            request,
            "This account is already verified. Please sign in."
        )
        return redirect("login")

    try:
        verification = user.email_verification

    except EmailVerification.DoesNotExist:
        messages.error(
            request,
            "Verification request not found. Please register again."
        )
        return redirect("register")

    if request.method == "POST":

        # -------------------------
        # RESEND OTP
        # -------------------------
        if "resend" in request.POST:
            try:
                sent, message = _issue_email_otp(
                    user,
                    verification
                )

                if sent:
                    messages.success(request, message)
                else:
                    messages.warning(request, message)

            except Exception:
                messages.error(
                    request,
                    "Unable to send the email right now. "
                    "Please try again later."
                )

            return redirect(
                "verify_email",
                uidb64=uidb64
            )

        # -------------------------
        # VERIFY OTP
        # -------------------------
        code = request.POST.get(
            "otp",
            ""
        ).strip()

        if verification.attempts >= OTP_MAX_ATTEMPTS:
            messages.error(
                request,
                "Too many incorrect attempts. Request a new code."
            )

        elif not verification.otp_hash:
            messages.error(
                request,
                "No valid verification code is available. "
                "Please request a new one."
            )

        elif timezone.now() >= verification.expires_at:
            messages.error(
                request,
                "This code has expired. Request a new one."
            )

        else:
            verification.attempts += 1
            verification.save(
                update_fields=["attempts"]
            )

            if (
                len(code) == OTP_LENGTH
                and code.isdigit()
                and check_password(
                    code,
                    verification.otp_hash
                )
            ):
                with transaction.atomic():
                    user.is_active = True
                    user.save(update_fields=["is_active"])

                    verification.delete()

                messages.success(
                    request,
                    "Email verified. You can now sign in."
                )

                return redirect("login")

            messages.error(
                request,
                "Invalid verification code."
            )

    # Mask email address on the verification page.
    email_name, _, email_domain = user.email.partition("@")

    masked_email = (
        f"{email_name[:1]}***@{email_domain}"
        if email_domain
        else "your registered email"
    )

    return render(
        request,
        "dashboard/verify_email.html",
        {
            "email": masked_email,
            "uidb64": uidb64,
            "resend_wait_seconds": OTP_RESEND_COOLDOWN_SECONDS,
        },
    )


# =========================================================
# LOGOUT
# =========================================================

@login_required
def logout_view(request):
    logout(request)
    return redirect("login")


# =========================================================
# TECHNICAL ANALYSIS API
# =========================================================

@api_login_required
def technical_analysis(request):

    symbol = request.GET.get(
        "symbol",
        "XAUUSD"
    ).upper()

    timeframe = request.GET.get(
        "timeframe",
        "15"
    )

    if symbol not in SUPPORTED_SYMBOLS:
        return JsonResponse(
            {
                "success": False,
                "error": f"Unsupported symbol: {symbol}",
            },
            status=400
        )

    try:
        candles = get_market_candles(
            symbol=symbol,
            timeframe=timeframe
        )

        analysis = calculate_technical_analysis(
            candles,
            balance=150,
            risk_percent=1
        )

        analysis["success"] = True
        analysis["symbol"] = symbol
        analysis["timeframe"] = timeframe

        analysis["timeframe_label"] = {
            "1": "1m",
            "5": "5m",
            "15": "15m",
            "30": "30m",
            "60": "1H",
            "D": "1D",
        }.get(
            timeframe,
            timeframe
        )

        return JsonResponse(analysis)

    except Exception:
        logger.exception(
            "Technical analysis failed for symbol=%s timeframe=%s",
            symbol,
            timeframe,
        )

        return JsonResponse(
            {
                "success": False,
                "symbol": symbol,
                "error": "Unable to generate technical analysis right now.",
            },
            status=500
        )

# ==================================
# NEW PASSWORD RESET CODE STARTS HERE
# ==================================
logger = logging.getLogger(__name__)


class BrevoPasswordResetForm(PasswordResetForm):
    """
    Django password reset form that sends reset emails
    through Brevo's transactional email API.
    """

    def send_mail(
        self,
        subject_template_name,
        email_template_name,
        context,
        from_email,
        to_email,
        html_email_template_name=None,
    ):
        subject = render_to_string(
            subject_template_name, context
        ).strip()

        # Email subjects must be a single line.
        subject = " ".join(subject.splitlines())

        text_content = render_to_string(
            email_template_name, context
        )

        html_content = None

        if html_email_template_name:
            html_content = render_to_string(
                html_email_template_name, context
            )

        api_key = getattr(settings, "BREVO_API_KEY", None)
        sender_email = getattr(
            settings, "BREVO_SENDER_EMAIL", None
        )
        sender_name = getattr(
            settings, "BREVO_SENDER_NAME", "Forex Dashboard"
        )

        if not api_key or not sender_email:
            raise ImproperlyConfigured(
                "Brevo password reset email settings are missing."
            )

        payload = {
            "sender": {
                "name": sender_name,
                "email": sender_email,
            },
            "to": [
                {
                    "email": to_email,
                }
            ],
            "subject": subject,
            "textContent": text_content,
        }

        if html_content:
            payload["htmlContent"] = html_content

        response = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={
                "accept": "application/json",
                "api-key": api_key,
                "content-type": "application/json",
            },
            json=payload,
            timeout=15,
        )

        if response.status_code not in (200, 201, 202):
            # Do not log the reset URL, token, or API key.
            logger.error(
                "Brevo password reset email failed. Status: %s",
                response.status_code,
            )
            response.raise_for_status()


@require_http_methods(["GET", "POST"])
def password_reset_request(request):
    """
    Accept an email and send a reset link if it belongs
    to an active user with a usable password.
    """

    if request.method == "POST":
        form = BrevoPasswordResetForm(request.POST)

        if form.is_valid():
            try:
                form.save(
                request=request,
                use_https=request.is_secure(),
                from_email=settings.BREVO_SENDER_EMAIL,
                email_template_name=(
                    "dashboard/auth/password_reset_email.txt"
                ),
                subject_template_name=(
                    "dashboard/auth/password_reset_subject.txt"
                ),
                token_generator=default_token_generator,
                )

            except requests.RequestException:
                # Do not expose Brevo errors or account existence.
                logger.exception(
                    "Password reset email delivery failed."
                )

            return redirect("password_reset_done")

    else:
        form = BrevoPasswordResetForm()

    return render(
        request,
        "dashboard/auth/password_reset_form.html",
        {"form": form},
    )