from django.urls import path
from . import views

urlpatterns = [
    path('', views.login, name='login-page'),
    path("signup-page/", views.signup, name="signup-page"),
    path('dashboard/', views.dashboard, name='dashboard'),

    path('reports/', views.reports, name='reports'),
    path("reports/submit/", views.submit_report, name="submit_report"),
    path("reports/search/", views.search_reports, name="search_reports"),
    path("reports/update-status/", views.update_report_status, name="update_report_status"),
    
    path('cases/', views.cases, name='cases'),
    path("cases/search/", views.search_cases, name="search_cases"),

    path("cases/closed/", views.closed_cases, name="closed_cases"),
    path("cases/closed/search/", views.search_closed_cases, name="search_closed_cases"),
    path('delete_report/', views.delete_report, name='delete_report'),

    path('notifications/', views.notifications, name='notifications'),
    path("notifications/mark-read/<int:notif_id>/", views.mark_notification_read, name="mark_notification_read"),
    path("notifications/delete/<int:notif_id>/", views.delete_notification, name="delete_notification"),
    path("notifications/count/", views.get_unread_count, name="get_unread_count"),

    path("login/", views.login_view, name="login"),
    path('signup/', views.signup_view, name='signup'),
    path("logout/", views.logout_view, name="logout"),

    path('verify/<int:user_id>/', views.verify_code_view, name='verify-otp'),
    path('resend/<int:user_id>/', views.resend_code_view, name='resend-code'),
    
]