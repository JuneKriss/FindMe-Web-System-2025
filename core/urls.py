from django.urls import path
from . import views

urlpatterns = [
    path('', views.login, name='login-page'),
    path("signup-page/", views.signup, name="signup-page"),
    path('dashboard/', views.dashboard, name='dashboard'),

    path('reports/', views.reports, name='reports'),
    path("reports/submit/", views.submit_report, name="submit_report"),

    path('cases/', views.cases, name='cases'),
    path('notifications/', views.notifications, name='notifications'),

    path("login/", views.login_view, name="login"),
    path('signup/', views.signup_view, name='signup'),
    path("logout/", views.logout_view, name="logout"),

    path('verify/<int:user_id>/', views.verify_code_view, name='verify-otp'),
    path('resend/<int:user_id>/', views.resend_code_view, name='resend-code'),
    
]