import random
from django.shortcuts import render,redirect
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
from django.db.models import Q


from rest_framework import viewsets, response, decorators, permissions
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action 
from rest_framework.response import Response 
from rest_framework import status

#SERIALIZER
from .serializers import AccountSerializer , FamilySerializer, VolunteerSerializer
from .serializers import ReportSerializer, ReportMediaSerializer
from .serializers import ReportMessageSerializer, SightingSerializer, SightingMediaSerializer

#MODELS
from .models import Account, Family, Volunteer, ReportCase, ReportMedia, EmailVerificationCode, ReportAssistance
from .models import ReportMessage, ReportSighting, SightingMedia

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
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # Default list view
        if user.role == "volunteer":
            # Return all reports (including ones they assist)
            return ReportCase.objects.exclude(reporter=user).order_by("-created_at")

        # Family sees only their own reports
        return ReportCase.objects.filter(reporter=user).order_by("-created_at")

    @action(detail=False, methods=['get'])
    def available(self, request):
        # Reports available for the volunteer to assist
        user = request.user
        if user.role != 'volunteer':
            return Response({'detail': 'Access denied.'}, status=403)

        reports = ReportCase.objects.filter(
            status='Verified'  # <-- Only verified reports
        ).exclude(
            reporter=user
        ).exclude(
            assistances__volunteer=user
        ).order_by('-created_at')

        serializer = self.get_serializer(reports, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def assist(self, request, pk=None):
        user = request.user
        report = self.get_object()

        if user.role != 'volunteer':
            return Response({'detail': 'Only volunteers can assist.'}, status=403)

        if report.reporter == user:
            return Response({'detail': 'You cannot assist your own report.'}, status=400)

        if ReportAssistance.objects.filter(report=report, volunteer=user, status='active').exists():
            return Response({'detail': 'You are already assisting this case.'}, status=400)

        ReportAssistance.objects.create(report=report, volunteer=user)
        report.status = 'In Progress'
        report.save(update_fields=['status'])

        return Response({'detail': 'You are now assisting this report.'})

    @action(detail=False, methods=['get'])
    def my_assisted(self, request):
        # Reports the volunteer is already assisting
        user = request.user
        if user.role != 'volunteer':
            return Response({'detail': 'Access denied.'}, status=403)
        
        reports = ReportCase.objects.filter(assistances__volunteer=user).distinct()
        serializer = self.get_serializer(reports, many=True)
        return Response(serializer.data)


class ReportMediaViewSet(viewsets.ModelViewSet):
    serializer_class = ReportMediaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ReportMedia.objects.filter(report__reporter=self.request.user)

    def perform_create(self, serializer):
        file = self.request.FILES.get("file")
        file_type = file.content_type if file else None
        serializer.save(file_type=file_type)

class ReportMessageViewSet(viewsets.ModelViewSet):
    serializer_class = ReportMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        report_id = self.request.query_params.get('report')
        if report_id:
            return ReportMessage.objects.filter(report_id=report_id).order_by('created_at')
        return ReportMessage.objects.none()
    
    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)

class SightingViewSet(viewsets.ModelViewSet):
    serializer_class = SightingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        report_id = self.request.query_params.get('report')
        if report_id:
            return ReportSighting.objects.filter(report_id=report_id).order_by('-created_at')
        return ReportSighting.objects.all().order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(volunteer=self.request.user)

class SightingMediaViewSet(viewsets.ModelViewSet):
    serializer_class = SightingMediaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SightingMedia.objects.filter(sighting__volunteer=self.request.user)

    def perform_create(self, serializer):
        file = self.request.FILES.get("file")
        file_type = file.content_type if file else None
        serializer.save(file_type=file_type)

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
        return redirect("login")

    try:
        user = Account.objects.get(account_id=user_id)
    except Account.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect("login")

    # Get all reports (latest first)
    all_reports = ReportCase.objects.select_related("reporter").order_by("-created_at")

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

        messages.success(request, "Report submitted successfully.")
        return redirect("reports")

    return redirect("reports")

def search_reports(request):
    query = request.GET.get("q", "").strip()
    sort = request.GET.get("sort", "created_at")
    filter_option = request.GET.get("filter", "").lower()

    reports = ReportCase.objects.all()

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
            "id": r.report_id,
            "full_name": r.full_name,
            "reporter": r.reporter.username,
            "status": r.status,
            "created_at": r.created_at.strftime("%B %d, %Y %I:%M %p"),
        })

    return JsonResponse({"results": results})

def update_report_status(request):
    if request.method == "POST":
        report_id = request.POST.get("report_id")
        status = request.POST.get("status")

        if not report_id:
            messages.error(request, "Report ID is missing.")
            return redirect("reports")

        try:
            report = ReportCase.objects.get(report_id=report_id)
        except ReportCase.DoesNotExist:
            messages.error(request, "Report not found.")
            return redirect("reports")

        # --- backend validation ---
        if not status:
            messages.error(request, "Please select a status.")
            return redirect("reports")

        valid_statuses = [choice[0] for choice in ReportCase.STATUS_CHOICES]
        if status not in valid_statuses:
            messages.error(request, "Invalid status.")
            return redirect("reports")

        # update
        report.status = status
        report.save()

        messages.success(request, f"Report status updated successfully.")
        return redirect("reports")

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

    return render(request, "cases.html", {"username": user.username})

def notifications(request):
    user_id = request.session.get('user_id')

    if not user_id:
        return redirect("login")  # Force login if no session
    
    try:
        user = Account.objects.get(account_id=user_id)
    except Account.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect("login")

    return render(request, "notifications.html", {"username": user.username})



