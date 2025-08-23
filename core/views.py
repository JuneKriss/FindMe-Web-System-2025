from django.shortcuts import render
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone

def login(request):
    return render(request, 'login.html')

def dashboard(request):
    return render(request, 'dashboard.html')

def ping(request):
    return JsonResponse({'ok': True, 'time': timezone.now().isoformat()})
