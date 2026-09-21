import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password, check_password
from django.core.mail import send_mail
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.http import (
    url_has_allowed_host_and_scheme,
    urlsafe_base64_decode,
    urlsafe_base64_encode,
)
from django.utils.encoding import force_bytes, force_str
from django.views.decorators.http import require_POST

from dashboard.forms import RegisterForm
from dashboard.models import EmailVerification
from dashboard.technical import calculate_technical_analysis
from data.market_data import get_market_candles
from dashboard.decorators import api_login_required


SUPPORTED_SYMBOLS = {"XAUUSD", "EURUSD", "GBPUSD", "BTCUSD"}

OTP_LENGTH = 6
OTP_EXPIRY_MINUTES = 10
OTP_MAX_ATTEMPTS = 5
OTP_RESEND_COOLDOWN_SECONDS = 60


@login_required
def dashboard_index(request):
    return render(request, "dashboard/index.html")


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard_index")

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            # Django's ModelBackend rejects inactive users.
            if not user.is_active:
                form.add_error(None, "Please verify your email before signing in.")
            else:
                login(request, user)
                next_url = request.POST.get("next") or request.GET.get("next")
                if next_url and url_has_allowed_host_and_scheme(
                    next_url,
                    allowed_hosts={request.get_host()},
                    require_https=request.is_secure(),
                ):
                    return redirect(next_url)
                return redirect("dashboard_index")
    else:
        form = AuthenticationForm(request)

    return render(request, "dashboard/login.html", {"form": form})


def _issue_email_otp(user, verification):
    now = timezone.now()

    if (
        verification.last_sent_at
        and (now - verification.last_sent_at).total_seconds()
        < OTP_RESEND_COOLDOWN_SECONDS
    ):
        return False, "Please wait a minute before requesting another code."

    otp = f"{secrets.randbelow(10 ** OTP_LENGTH):0{OTP_LENGTH}d}"
    verification.otp_hash = make_password(otp)
    verification.expires_at = now + timedelta(minutes=OTP_EXPIRY_MINUTES)
    verification.attempts = 0
    verification.last_sent_at = now
    verification.save(
        update_fields=[
            "otp_hash", "expires_at", "attempts", "last_sent_at"
        ]
    )

    try:
        send_mail(
            subject="Verify your email",
            message=(
                f"Your Forex Terminal verification code is {otp}. "
                f"It expires in {OTP_EXPIRY_MINUTES} minutes. "
                "If you did not request this, you can ignore this email."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
    except Exception:
        # Invalidate the code if the email provider rejected the message.
        verification.otp_hash = ""
        verification.save(update_fields=["otp_hash"])
        raise

    return True, "A verification code has been sent to your email."


def register_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard_index")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                user = form.save(commit=False)
                user.is_active = False
                user.save()
                verification = EmailVerification.objects.create(
                    user=user,
                    expires_at=timezone.now() + timedelta(minutes=OTP_EXPIRY_MINUTES),
                )

            try:
                _issue_email_otp(user, verification)
            except Exception:
                messages.error(
                    request,
                    "We couldn't send the verification email. "
                    "Please wait a minute, then use Resend code."
                )
                return redirect(
                    "verify_email",
                    uidb64=urlsafe_base64_encode(force_bytes(user.pk))
                )

            messages.info(
                request,
                "Account created. Enter the verification code sent to your email."
            )
            return redirect(
                "verify_email",
                uidb64=urlsafe_base64_encode(force_bytes(user.pk))
            )
    else:
        form = RegisterForm()

    return render(request, "dashboard/register.html", {"form": form})


def _get_verification_user(uidb64):
    try:
        user_id = force_str(urlsafe_base64_decode(uidb64))
        return User.objects.get(pk=user_id)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return None


def verify_email_view(request, uidb64):
    user = _get_verification_user(uidb64)
    if user is None:
        messages.error(request, "Invalid verification request.")
        return redirect("register")

    if user.is_active:
        messages.info(request, "This account is already verified. Please sign in.")
        return redirect("login")

    try:
        verification = user.email_verification
    except EmailVerification.DoesNotExist:
        messages.error(request, "Verification request not found. Please register again.")
        return redirect("register")

    if request.method == "POST":
        if "resend" in request.POST:
            try:
                sent, message = _issue_email_otp(user, verification)
                (messages.success if sent else messages.warning)(request, message)
            except Exception:
                messages.error(request, "Unable to send the email right now. Try again later.")
            return redirect("verify_email", uidb64=uidb64)

        code = request.POST.get("otp", "").strip()

        if verification.attempts >= OTP_MAX_ATTEMPTS:
            messages.error(request, "Too many incorrect attempts. Request a new code.")
        elif timezone.now() >= verification.expires_at:
            messages.error(request, "This code has expired. Request a new one.")
        else:
            verification.attempts += 1
            verification.save(update_fields=["attempts"])

            if len(code) == OTP_LENGTH and code.isdigit() and check_password(
                code, verification.otp_hash
            ):
                with transaction.atomic():
                    user.is_active = True
                    user.save(update_fields=["is_active"])
                    verification.delete()

                messages.success(request, "Email verified. You can now sign in.")
                return redirect("login")

            messages.error(request, "Invalid verification code.")

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
                "error": (
                    f"Unsupported symbol: {symbol}"
                )
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

        analysis["timeframe_label"] = (
            {
                "1": "1m",
                "5": "5m",
                "15": "15m",
                "30": "30m",
                "60": "1H",
                "D": "1D",
            }
            .get(
                timeframe,
                timeframe
            )
        )

        return JsonResponse(
            analysis
        )

    except Exception as error:

        return JsonResponse(
            {
                "success": False,
                "symbol": symbol,
                "error": str(error)
            },
            status=500
        )