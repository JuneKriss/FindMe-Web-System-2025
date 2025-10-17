import random
from django.shortcuts import render,redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.http import JsonResponse
import datetime
from datetime import timedelta
from django.http import JsonResponse
from django.db.models import Q, Count
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action 
from rest_framework.response import Response 
from rest_framework import status

#SERIALIZER
from .serializers import AccountSerializer , FamilySerializer, VolunteerSerializer
from .serializers import ReportSerializer, ReportMediaSerializer

#MODELS
from .models import Account, Family, Volunteer, ReportCase, ReportMedia, EmailVerificationCode, Notification, UserNotification

# API

import random
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Account, EmailVerificationCode
from .serializers import AccountSerializer


class AccountViewSet(viewsets.ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    lookup_field = "account_id"

    # --- Permissions ---
    def get_permissions(self):
        from rest_framework.permissions import AllowAny, IsAuthenticated
        if self.action in ["create", "verify_email", "resend_code"]:
            return [AllowAny()]
        return [IsAuthenticated()]

    # --- Register (override create) ---
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate OTP
        otp_code = str(random.randint(100000, 999999))
        EmailVerificationCode.objects.create(user=user, code=otp_code)

        # Send email
        send_mail(
            "Verify your FindMe account",
            f"Your verification code is {otp_code}. It expires in 5 minutes.",
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )

        return Response(
            {
                "message": "Account created. Verification code sent.",
                "account_id": user.account_id,
            },
            status=status.HTTP_201_CREATED,
        )

    # --- Verify OTP ---
    @action(detail=False, methods=["post"], url_path="verify-email")
    def verify_email(self, request):
        user_id = request.data.get("user_id")
        code = request.data.get("code")

        try:
            user = Account.objects.get(account_id=user_id)
        except Account.DoesNotExist:
            return Response({"error": "Invalid user"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            otp_entry = EmailVerificationCode.objects.filter(user=user, code=code).latest("created_at")
            if otp_entry.is_expired():
                return Response({"error": "Code expired"}, status=status.HTTP_400_BAD_REQUEST)

            user.is_active = True
            user.save()
            return Response({"success": "Account verified!"}, status=status.HTTP_200_OK)

        except EmailVerificationCode.DoesNotExist:
            return Response({"error": "Invalid code"}, status=status.HTTP_400_BAD_REQUEST)

    # --- Resend OTP ---
    @action(detail=False, methods=["post"], url_path="resend-code")
    def resend_code(self, request):
        user_id = request.data.get("user_id")

        try:
            user = Account.objects.get(account_id=user_id)
        except Account.DoesNotExist:
            return Response({"error": "Invalid user"}, status=status.HTTP_400_BAD_REQUEST)

        recent_code = EmailVerificationCode.objects.filter(user=user).order_by("-created_at").first()
        if recent_code and recent_code.created_at > timezone.now() - timedelta(minutes=1):
            return Response({"error": "Please wait before requesting a new code"}, status=status.HTTP_400_BAD_REQUEST)

        otp_code = str(random.randint(100000, 999999))
        EmailVerificationCode.objects.create(user=user, code=otp_code)

        send_mail(
            "Verify your FindMe account",
            f"Your new verification code is {otp_code}. It expires in 5 minutes.",
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )

        return Response({"success": "New code sent to your email."}, status=status.HTTP_200_OK)

    # --- Update Role ---
    @action(detail=False, methods=["patch"], url_path="update-role")
    def update_role(self, request):
        user = request.user
        role = request.data.get("role")

        if role not in ["family", "volunteer"]:
            return Response({"error": "Invalid role"}, status=status.HTTP_400_BAD_REQUEST)

        user.role = role
        user.save()

        return Response({"success": "Role updated", "role": user.role}, status=status.HTTP_200_OK)

    # --- Get Current User ---
    @action(detail=False, methods=["get"], url_path="me")
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    
class FamilyViewSet(viewsets.ModelViewSet):
    serializer_class = FamilySerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return Family.objects.filter(account=self.request.user)
    def perform_create(self, serializer):
        serializer.save(account=self.request.user)
    
class VolunteerViewSet(viewsets.ModelViewSet):
    serializer_class = VolunteerSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return Volunteer.objects.filter(account=self.request.user)
    def perform_create(self, serializer):
        serializer.save(account=self.request.user)

class ReportViewSet(viewsets.ModelViewSet):
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == "volunteer":
            # Volunteers see all reports
            return ReportCase.objects.all().order_by("-created_at")
        else:
            # Families only see their own reports
            return ReportCase.objects.filter(reporter=user).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(reporter=self.request.user)


class ReportMediaViewSet(viewsets.ModelViewSet):
    serializer_class = ReportMediaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ReportMedia.objects.filter(report__reporter=self.request.user)

    def perform_create(self, serializer):
        file = self.request.FILES.get("file")
        file_type = file.content_type if file else None
        serializer.save(file_type=file_type)

# API

# WEB

# Helper Functions
def create_notification(action, title, related_report=None, recipients=None):
    # Check for very recent duplicates (within 5 minutes)
    recent_cutoff = timezone.now() - timedelta(minutes=5)
    existing = Notification.objects.filter(
        related_report=related_report,
        action=action,
        title=title,
        created_at__gte=recent_cutoff,
    ).first()

    if existing:
        return  # skip very recent duplicates only

    # Create main notification
    notification = Notification.objects.create(
        action=action,
        title=title,
        related_report=related_report,
        created_at=timezone.now(),
    )

    # Default recipients: all police + reporter if applicable
    if recipients is None:
        recipients = list(Account.objects.filter(role="police"))
        if related_report and related_report.reporter not in recipients:
            recipients.append(related_report.reporter)

    # Create UserNotification entries efficiently
    UserNotification.objects.bulk_create([
        UserNotification(user=user, notification=notification)
        for user in recipients
    ])

def unread_notifications_count(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return {"unread_notifications_count": 0}
    try:
        user = Account.objects.get(account_id=user_id)
    except Account.DoesNotExist:
        return {"unread_notifications_count": 0}

    count = UserNotification.objects.filter(user=user, is_read=False).count()
    return {"unread_notifications_count": count}

def get_unread_count(request):
    user_id = request.session.get('user_id')
    if user_id:
        count = UserNotification.objects.filter(user_id=user_id, is_read=False, is_deleted=False).count()
        return JsonResponse({'count': count})
    return JsonResponse({'count': 0})
# Helper Functions

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
        return redirect("login")

    try:
        user = Account.objects.get(account_id=user_id)
    except Account.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect("login")

    # --- Safely fetch recent reports ---
    recent_reports = (
        ReportCase.objects.select_related("reporter")
        .prefetch_related("media")
        .filter(status__in=["Pending", "Rejected"])
        .order_by("-report_id")[:4]
    )

    recent_cases = (
        ReportCase.objects.select_related("reporter")
        .exclude(status__in=["Pending", "Rejected"])
        .order_by("-report_id")[:5]
    )

    # --- Reports per month (safe version) ---
    six_months_ago = timezone.now() - timedelta(days=180)
    monthly_reports = (
        ReportCase.objects.filter(created_at__gte=six_months_ago)
        .values("created_at")
    )

    # Convert manually, ignoring invalid datetimes
    from datetime import datetime
    months = {}
    for r in monthly_reports:
        dt = r["created_at"]
        if not dt or str(dt).startswith("0000-00-00"):
            continue  # skip invalid datetimes
        try:
            month_label = dt.strftime("%b %Y")
            months[month_label] = months.get(month_label, 0) + 1
        except Exception:
            continue

    months_list = list(months.keys())
    report_counts = list(months.values())

    # --- Counts ---
    total_reports = ReportCase.objects.count()
    active_cases = ReportCase.objects.filter(status__in=["Verified", "In Progress", "On Hold"]).count()
    total_users = Account.objects.count()
    resolved_cases = ReportCase.objects.filter(
        status__in=["Closed - Safe", "Closed - Deceased", "Closed - Unresolved"]
    ).count()
    
    context = {
        "username": user.username,
        "recent_reports": recent_reports,
        "recent_cases": recent_cases,
        "months": months_list,
        "report_counts": report_counts,
        "total_reports": total_reports,
        "active_cases": active_cases,
        "total_users": total_users,
        "resolved_cases": resolved_cases,
    }

    return render(request, "dashboard.html", context)

def reports(request):
    user_id = request.session.get('user_id')

    if not user_id:
        return redirect("login")

    try:
        user = Account.objects.get(account_id=user_id)
    except Account.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect("login")

    # Get all reports (latest first)
    all_reports = ReportCase.objects.select_related("reporter").order_by("-created_at").filter(status__in=["Pending", "Rejected"])

    # Pagination (10 per page)
    paginator = Paginator(all_reports, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "reports.html",
        {
            "username": user.username,
            "page_obj": page_obj,
            "paginator": paginator,
            "status_choices": ReportCase.STATUS_CHOICES, 
        }
    )

def submit_report(request):
    user_id = request.session.get("user_id")

    if not user_id:
        return redirect("login")

    try:
        user = Account.objects.get(account_id=user_id)
    except Account.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect("login")

    if request.method == "POST":
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        full_name = f"{first_name} {last_name}".strip()
        age = request.POST.get("age")
        gender = request.POST.get("gender")
        last_seen_date = request.POST.get("last_seen_date")
        last_seen_time = request.POST.get("last_seen_time")
        clothing = request.POST.get("clothing", "").strip()
        location = request.POST.get("location", "").strip()
        notes = request.POST.get("notes", "").strip()
        images = request.FILES.getlist("images")

        # --- backend validation ---
        if not full_name or not age or not gender or not last_seen_date:
            messages.error(request, "Please fill in all required fields.")
            return redirect("reports")

        # validate age
        try:
            age = int(age)
            if age <= 0:
                messages.error(request, "Age must be a positive number.")
                return redirect("reports")
        except ValueError:
            messages.error(request, "Please enter a valid age.")
            return redirect("reports")

        # validate date
        try:
            last_seen_date_obj = datetime.datetime.strptime(last_seen_date, "%Y-%m-%d").date()
            if last_seen_date_obj > datetime.date.today():
                messages.error(request, "Please provide a valid last seen date.")
                return redirect("reports")
        except ValueError:
            messages.error(request, "Invalid date format.")
            return redirect("reports")

        # validate images
        allowed_types = ["image/jpeg", "image/png", "image/jpg"]
        max_size_mb = 5
        for img in images:
            if img.content_type not in allowed_types:
                messages.error(request, f"Invalid file type: {img.name}. Only JPG and PNG allowed.")
                return redirect("reports")
            if img.size > max_size_mb * 1024 * 1024:
                messages.error(request, f"{img.name} is too large (max {max_size_mb}MB).")
                return redirect("reports")

        # create report
        report = ReportCase.objects.create(
            reporter=user,
            full_name=full_name,
            age=age,
            gender=gender,
            last_seen_date=last_seen_date,
            last_seen_time=last_seen_time if last_seen_time else None,
            last_seen_location=location,
            clothing=clothing,
            notes=notes,
        )

        # save images
        for img in images:
            ReportMedia.objects.create(
                report=report,
                file=img,
                file_type=img.content_type,
            )

        create_notification(
            action="report_created",
            title=f"{user.username} submitted a new missing person report for {report.full_name}.",
            related_report=report,
        )

        messages.success(request, "Report submitted successfully.")
        return redirect("reports")

    return redirect("reports")

def search_reports(request):
    query = request.GET.get("q", "").strip()
    sort = request.GET.get("sort", "created_at")
    filter_option = request.GET.get("filter", "").lower()

    reports = (
        ReportCase.objects.select_related("reporter")
        .filter(status__in=["Pending", "Rejected"])
    )

    if query:
        reports = reports.filter(
            Q(full_name__icontains=query) |
            Q(reporter__username__icontains=query) |
            Q(age__icontains=query) |
            Q(gender__icontains=query) |
            Q(last_seen_date__icontains=query) |
            Q(last_seen_time__icontains=query) |
            Q(last_seen_location__icontains=query) |
            Q(clothing__icontains=query) |
            Q(notes__icontains=query) |
            Q(status__icontains=query)
        )

    # sorting logic
    if sort == "id":
        reports = reports.order_by("report_id")
    elif sort == "date":
        reports = reports.order_by("-created_at")
    elif sort == "status":
        reports = reports.order_by("status")
    else:
        reports = reports.order_by("-created_at")

    #filter logic
    if filter_option and filter_option != "reset":
        reports = reports.filter(status__iexact=filter_option)

    # serialize results
    results = []
    for r in reports:
        results.append({
            "report_id": r.report_id,
            "full_name": r.full_name,
            "reporter": r.reporter.username if r.reporter else "Unknown",
            "status": r.status,
            "created_at": r.created_at.strftime("%B %d, %Y %I:%M %p") if r.created_at else "",
            "age": r.age,
            "gender": r.gender,
            "last_seen_date": r.last_seen_date.strftime("%Y-%m-%d") if r.last_seen_date else "",
            "last_seen_time": r.last_seen_time.strftime("%H:%M") if r.last_seen_time else "",
            "last_seen_location": r.last_seen_location,
            "clothing": r.clothing,
            "notes": r.notes or "",
            "media": [
                {
                    "url": m.file.url,
                    "type": m.file_type or "",
                    "id": m.media_id,
                }
                for m in r.media.all()
            ],
        })

    return JsonResponse({"results": results})

def update_report_status(request):
    if request.method == "POST":
        report_id = request.POST.get("report_id")
        status = request.POST.get("status")

        # Detect referring page
        referer = request.META.get("HTTP_REFERER", "")
        redirect_target = "reports"  # default

        if "cases/closed" in referer:  # match actual path
            redirect_target = "closed_cases"

        if not report_id:
            messages.error(request, "Report ID is missing.")
            return redirect(redirect_target)

        try:
            report = ReportCase.objects.get(report_id=report_id)
        except ReportCase.DoesNotExist:
            messages.error(request, "Report not found.")
            return redirect(redirect_target)

        if not status:
            messages.error(request, "Please select a status.")
            return redirect(redirect_target)

        valid_statuses = [choice[0] for choice in ReportCase.STATUS_CHOICES]
        if status not in valid_statuses:
            messages.error(request, "Invalid status.")
            return redirect(redirect_target)

        # Update report
        report.status = status
        report.save()

        create_notification(
            action="status_changed",
            title=f"The status of report #{report.report_id} has been changed to {status}.",
            related_report=report,
        )

        messages.success(request, "Report status updated successfully.")
        return redirect(redirect_target)

    return redirect("reports")

def cases(request):
    user_id = request.session.get('user_id')

    if not user_id:
        return redirect("login")  # Force login if no session
    
    try:
        user = Account.objects.get(account_id=user_id)
    except Account.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect("login")

    all_cases = (
        ReportCase.objects.select_related("reporter")
        .exclude(status__in=[
            "Pending",
            "Rejected",
            "Closed - Safe",
            "Closed - Deceased",
            "Closed - Unresolved",
        ])
        .order_by("-created_at")
    )

    paginator = Paginator(all_cases, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "cases.html",
        {
            "username": user.username,
            "page_obj": page_obj,
            "paginator": paginator,
        },
    )

def search_cases(request):
    query = request.GET.get("q", "").strip()
    sort = request.GET.get("sort", "created_at")
    filter_option = request.GET.get("filter", "").lower()

    # Exclude Pending, Rejected, and any Closed statuses
    reports = (
        ReportCase.objects.select_related("reporter")
        .exclude(
            status__in=[
                "Pending",
                "Rejected",
                "Closed - Safe",
                "Closed - Deceased",
                "Closed - Unresolved",
            ]
        )
    )

    # Search logic
    if query:
        reports = reports.filter(
            Q(full_name__icontains=query)
            | Q(reporter__username__icontains=query)
            | Q(age__icontains=query)
            | Q(gender__icontains=query)
            | Q(last_seen_date__icontains=query)
            | Q(last_seen_time__icontains=query)
            | Q(last_seen_location__icontains=query)
            | Q(clothing__icontains=query)
            | Q(notes__icontains=query)
            | Q(status__icontains=query)
        )

    # Sorting logic
    if sort == "id":
        reports = reports.order_by("report_id")
    elif sort == "date":
        reports = reports.order_by("-created_at")
    elif sort == "status":
        reports = reports.order_by("status")
    else:
        reports = reports.order_by("-created_at")

    # Filter logic
    if filter_option and filter_option != "reset":
        reports = reports.filter(status__iexact=filter_option)

    # Serialize results
    results = []
    for r in reports:
        results.append({
            "report_id": r.report_id,
            "full_name": r.full_name,
            "reporter": r.reporter.username if r.reporter else "Unknown",
            "status": r.status,
            "created_at": r.created_at.strftime("%B %d, %Y %I:%M %p") if r.created_at else "",
            "age": r.age,
            "gender": r.gender,
            "last_seen_date": r.last_seen_date.strftime("%Y-%m-%d") if r.last_seen_date else "",
            "last_seen_time": r.last_seen_time.strftime("%H:%M") if r.last_seen_time else "",
            "last_seen_location": r.last_seen_location,
            "clothing": r.clothing,
            "notes": r.notes or "",
            "media": [
                {
                    "url": m.file.url,
                    "type": m.file_type or "",
                    "id": m.media_id,
                }
                for m in r.media.all()
            ],
        })

    return JsonResponse({"results": results})

def closed_cases(request):
    user_id = request.session.get("user_id")

    if not user_id:
        return redirect("login")  # Force login if no session
    
    try:
        user = Account.objects.get(account_id=user_id)
    except Account.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect("login")

    # Only include closed cases
    closed_statuses = ["Closed - Safe", "Closed - Deceased", "Closed - Unresolved"]

    all_cases = (
        ReportCase.objects.select_related("reporter")
        .filter(status__in=closed_statuses)
        .order_by("-created_at")
    )

    paginator = Paginator(all_cases, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "closed_cases.html",
        {
            "username": user.username,
            "page_obj": page_obj,
            "paginator": paginator,
            "status_choices": ReportCase.STATUS_CHOICES, 
        },
    )

def search_closed_cases(request):
    q = request.GET.get("q", "").strip()
    filter_option = request.GET.get("filter", "").lower()
    sort_option = request.GET.get("sort", "").lower()

    closed_statuses = [
        "Closed - Safe",
        "Closed - Deceased",
        "Closed - Unresolved",
    ]

    cases = ReportCase.objects.select_related("reporter").filter(status__in=closed_statuses)

    if q:
        cases = cases.filter(
            Q(full_name__icontains=q) |
            Q(reporter__username__icontains=q)
        )

    if filter_option:
        if filter_option == "safe":
            cases = cases.filter(status="Closed - Safe")
        elif filter_option == "deceased":
            cases = cases.filter(status="Closed - Deceased")
        elif filter_option == "unresolved":
            cases = cases.filter(status="Closed - Unresolved")

    if sort_option == "id":
        cases = cases.order_by("report_id")
    elif sort_option == "date":
        cases = cases.order_by("-created_at")
    elif sort_option == "status":
        cases = cases.order_by("status")
    else:
        cases = cases.order_by("-created_at")

    data = [
        {
            "report_id": c.report_id,
            "full_name": c.full_name,
            "reporter": c.reporter.username,
            "created_at": c.created_at.strftime("%B %d, %Y %I:%M %p"),
            "status": c.status,
        }
        for c in cases
    ]

    return JsonResponse({"results": data})

@require_POST
def delete_report(request):
    report_id = request.POST.get("report_id")
    if not report_id:
        return JsonResponse({"success": False, "message": "Missing report ID."}, status=400)

    report = get_object_or_404(ReportCase, report_id=report_id)
    report.delete()
    return JsonResponse({"success": True, "message": "Report deleted successfully!"})


def notifications(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect("login")

    try:
        user = Account.objects.get(account_id=user_id)
    except Account.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect("login")

    user_notifications = (
        UserNotification.objects
        .filter(user=user, is_deleted=False)
        .select_related("notification")
        .order_by("-notification__created_at")
    )
    now = timezone.now()
    today = now.date()
    yesterday = today - timedelta(days=1)

    processed_notifications = []
    for user_notif in user_notifications:
        notif = user_notif.notification
        created = notif.created_at
        diff = now - created

        # Default formatted display
        if created.date() == today:
            seconds = diff.seconds
            if seconds < 60:
                display_time = "just now"
            elif seconds < 3600:
                minutes = seconds // 60
                display_time = f"{minutes} minute{'s' if minutes != 1 else ''} ago"
            else:
                hours = seconds // 3600
                display_time = f"{hours} hour{'s' if hours != 1 else ''} ago"

        elif created.date() == yesterday:
            display_time = "Yesterday"

        else:
            display_time = created.strftime("%b %d")  # e.g. "Oct 2"

        processed_notifications.append({
            "user_notif": user_notif,
            "notif": notif,
            "display_time": display_time,
        })

    # Group notifications (optional — like your HTML layout)
    grouped_notifications = {
        "today": [n for n in processed_notifications if n["notif"].created_at.date() == today],
        "yesterday": [n for n in processed_notifications if n["notif"].created_at.date() == yesterday],
        "earlier": [n for n in processed_notifications if n["notif"].created_at.date() < yesterday],
    }

    return render(request, "notifications.html", {
        "username": user.username,
        "grouped_notifications": grouped_notifications,
    })

@csrf_exempt
def mark_notification_read(request, notif_id):
    if request.method == "POST":
        user_id = request.session.get("user_id")
        if not user_id:
            return JsonResponse({"success": False, "message": "Not logged in"}, status=401)

        try:
            user_notif = UserNotification.objects.get(id=notif_id, user_id=user_id)
            user_notif.mark_as_read()
            return JsonResponse({"success": True})
        except UserNotification.DoesNotExist:
            return JsonResponse({"success": False, "message": "Notification not found"}, status=404)

    return JsonResponse({"success": False, "message": "Invalid request"}, status=400)

@csrf_exempt
def delete_notification(request, notif_id):
    if request.method == "POST":
        user_id = request.session.get("user_id")
        if not user_id:
            return JsonResponse({"success": False, "message": "Not logged in"}, status=401)

        try:
            user_notif = UserNotification.objects.get(id=notif_id, user_id=user_id)
            user_notif.mark_as_deleted()
            return JsonResponse({"success": True})
        except UserNotification.DoesNotExist:
            return JsonResponse({"success": False, "message": "Notification not found"}, status=404)

    return JsonResponse({"success": False, "message": "Invalid request"}, status=400)