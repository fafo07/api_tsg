from django.urls import path

from tsc_api.authn.views import LoginView, MeView

urlpatterns = [
    path('auth/login', LoginView.as_view(), name='auth-login'),
    path('auth/me', MeView.as_view(), name='auth-me'),
]
