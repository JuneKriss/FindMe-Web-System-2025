import random
from django.shortcuts import render,redirect
from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from .models import Account, EmailVerificationCode
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from .serializers import AccountSerializer

# API
class AccountViewSet(viewsets.ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        return [IsAuthenticated()]

# API


# WEB

def login(request):
    return render(request, 'login.html')

def signup(request):
    return render(request, 'signup.html')

def signup_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")

        # Validation
        if Account.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return redirect("signup")
        if Account.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return redirect("signup")

        # Create inactive user
        user = Account.objects.create(
            username=username,
            email=email,
            password=make_password(password),  # hash password
            is_active=False
        )

        # Generate OTP
        otp_code = str(random.randint(100000, 999999))  # 6-digit code
        EmailVerificationCode.objects.create(user=user, code=otp_code)

        # Send email
        send_mail(
            "Verify your FindMe account",
            f"Your verification code is {otp_code}. It expires in 5 minutes.",
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )

        messages.info(request, "A verification code has been sent to your email address.")
        return redirect("verify-otp", user_id=user.account_id)

    return render(request, "signup.html")



def verify_code_view(request, user_id):
    try:
        user = Account.objects.get(account_id=user_id)
    except Account.DoesNotExist:
        messages.error(request, "Invalid user.")
        return redirect("signup")

    # Handle resend link click
    if request.GET.get("resend") == "true":
        # Generate new OTP
        otp_code = str(random.randint(100000, 999999))
        EmailVerificationCode.objects.create(user=user, code=otp_code)

        # Send email
        send_mail(
            "Verify your FindMe account",
            f"Your new verification code is {otp_code}. It expires in 5 minutes.",
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )

        messages.info(request, "A new verification code has been sent to your email address.")
        return render(request, "gmail_verification.html", {"user_id": user_id})

    if request.method == "POST":
        code = request.POST.get("code")

        try:
            otp_entry = EmailVerificationCode.objects.filter(
                user=user, code=code
            ).latest('created_at')

            if otp_entry.is_expired():
                resend_url = reverse("verify-otp", args=[user.account_id]) + "?resend=true"
                messages.error(
                    request,
                    f"Your verification code has expired. "
                    f"<a href='{resend_url}' class='poppins-regular verify-link'>Click here to resend</a>."
                )
                return render(request, "gmail_verification.html", {"user_id": user_id})

            # Activate user if code is valid
            user.is_active = True
            user.save()

            messages.success(request, "Your account has been verified! You can now log in.")
            return redirect("login-page")

        except EmailVerificationCode.DoesNotExist:
            messages.error(request, "Invalid code.")
            return redirect("verify-otp", user_id=user_id)

    return render(request, "gmail_verification.html", {"user_id": user_id})

def resend_code_view(request, user_id):
    try:
        user = Account.objects.get(account_id=user_id)
    except Account.DoesNotExist:
        messages.error(request, "Invalid user.")
        return redirect("signup")

    # Prevent spamming by checking if a code was recently sent
    recent_code = EmailVerificationCode.objects.filter(user=user).order_by('-created_at').first()
    if recent_code and recent_code.created_at > timezone.now() - timedelta(minutes=1):
        messages.info(request, "You can request a new code in a minute.")
        return redirect("verify-otp", user_id=user_id)

    # Generate and save new code
    otp_code = str(random.randint(100000, 999999))
    EmailVerificationCode.objects.create(user=user, code=otp_code)

    # Send email
    send_mail(
        "Verify your FindMe account",
        f"Here’s your new verification code: {otp_code}. It expires in 5 minutes.",
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )

    messages.info(request, "We’ve sent you a new verification code. Check your inbox!")
    return redirect("verify-otp", user_id=user_id)


def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        try:
            user = Account.objects.get(email=email)
        except Account.DoesNotExist:
            messages.error(request, "Account with this email does not exist")
            return render(request, "login.html")

        # Check if account is verified
        if not user.is_active:
            verify_url = reverse("verify-otp", args=[user.account_id]) + "?resend=true"
            messages.error(
                request,
                f"Your account is not verified. <a href='{verify_url}' class='poppins-regular verify-link'>Click here to verify</a>."
            )
            return render(request, "login.html")

        # Check password
        if check_password(password, user.password):
            request.session['user_id'] = user.account_id
            request.session['username'] = user.username
            return redirect("dashboard")
        else:
            messages.error(request, "Invalid email or password")
            return render(request, "login.html")
    else:
        return render(request, "login.html")

def logout_view(request):
    request.session.flush()  # clears all session data (user_id, username, etc.)
    return redirect("login")

def dashboard(request):
    user_id = request.session.get('user_id')

    if not user_id:
        return redirect("login")  # Force login if no session

    try:
        user = Account.objects.get(account_id=user_id)
    except Account.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect("login")

    return render(request, "dashboard.html", {"username": user.username})

def reports(request):
    user_id = request.session.get('user_id')

    if not user_id:
        return redirect("login")  # Force login if no session
    
    try:
        user = Account.objects.get(account_id=user_id)
    except Account.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect("login")

    return render(request, "dashboard.html", {"username": user.username})




