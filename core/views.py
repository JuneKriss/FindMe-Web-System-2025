from django.shortcuts import render,redirect
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action 
from rest_framework.response import Response 
from rest_framework import status

#SERIALIZER
from .serializers import AccountSerializer , FamilySerializer, VolunteerSerializer
from .serializers import ReportSerializer, ReportMediaSerializer

#MODELS
from .models import Account, Family, Volunteer
from .models import ReportCase, ReportMedia

# API
class AccountViewSet(viewsets.ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'account_id' 

    def get_permissions(self):
        # Anyone can register
        if self.action == 'create':
            return [AllowAny()]
        return super().get_permissions()

    @action(detail=False, methods=['patch'], url_path='update-role')
    def update_role(self, request):
        role = request.data.get('role')
        if role not in ['family', 'volunteer']:
            return Response({'error': 'Invalid role'}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        user.role = role
        user.save(update_fields=['role'])

        return Response({'role': user.role}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], url_path='me')
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
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

def login(request):
    return render(request, 'login.html')

def dashboard(request):
    user_id = request.session.get('user_id')
    username = request.session.get('username')

    if not user_id:
        return redirect("login")  # Force login if no session

    return render(request, "dashboard.html", {"username": username})

def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        try:
            user = Account.objects.get(email=email)
        except Account.DoesNotExist:
            messages.error(request, "Account with this email does not exist")
            return render(request, "login.html")

        # Use check_password instead of authenticate
        if check_password(password, user.password):
            # Save user info in session
            request.session['user_id'] = user.account_id
            request.session['username'] = user.username
            return redirect("dashboard")  # Replace with your dashboard URL
        else:
            messages.error(request, "Invalid email or password")
            return render(request, "login.html")
    else:
        return render(request, "login.html")

