from django.shortcuts import render,redirect
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action 
from rest_framework.response import Response 
from rest_framework import status

#SERIALIZER
from .serializers import AccountSerializer
from .serializers import ReportSerializer

#MODELS
from .models import Account
from .models import ReportCase

# API
class AccountViewSet(viewsets.ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'account_id'  # <-- add this

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
    

class ReportViewSet(viewsets.ModelViewSet):
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Only return reports created by the logged-in user
        return ReportCase.objects.filter(reporter=self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        # Reporter is handled in serializer.create(), so this is optional
        serializer.save()

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

