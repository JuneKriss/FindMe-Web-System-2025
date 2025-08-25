from django.shortcuts import render,redirect
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from .models import Account


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

