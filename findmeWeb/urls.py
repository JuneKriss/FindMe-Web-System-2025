"""
URL configuration for findmeWeb project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView, TokenRefreshView
)
from django.conf import settings
from django.conf.urls.static import static

# API
from core.views import AccountViewSet, FamilyViewSet, VolunteerViewSet
from core.views import ReportViewSet, ReportMediaViewSet

router = DefaultRouter()
router.register(r'accounts', AccountViewSet, basename='accounts')
router.register(r'family', FamilyViewSet, basename='family')
router.register(r'volunteer', VolunteerViewSet, basename='volunteer')
router.register(r'reports', ReportViewSet, basename='reports')
router.register(r'reportMedia', ReportMediaViewSet, basename='reportMedia')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('', include('core.urls')),
    path("__reload__/", include("django_browser_reload.urls")),
]

# 👇 This makes /media/ URLs work in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
