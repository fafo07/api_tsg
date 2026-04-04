from django.urls import path

from tsc_api.authn.views import ChangePasswordView, LoginView, MeView, RefreshView

urlpatterns = [
    path('auth/login', LoginView.as_view(), name='auth-login'),
    path('auth/refresh', RefreshView.as_view(), name='auth-refresh'),
    path('auth/me', MeView.as_view(), name='auth-me'),
    path('auth/change-password', ChangePasswordView.as_view(), name='auth-change-password'),
]
