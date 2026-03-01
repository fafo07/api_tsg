from django.utils.translation import gettext_lazy as _
from rest_framework import authentication, exceptions
from rest_framework_simplejwt.authentication import JWTAuthentication

from tsc_api.registry.models import RegistryUser


class RegistryJWTAuthentication(authentication.BaseAuthentication):
    def __init__(self):
        self.jwt_auth = JWTAuthentication()

    def authenticate(self, request):
        validated = self.jwt_auth.authenticate(request)
        if not validated:
            return None
        token_user, token = validated
        user_id = token.get('user_id')
        if not user_id:
            raise exceptions.AuthenticationFailed(_('Invalid token payload.'))
        try:
            user = RegistryUser.objects.select_related('role').get(user_id=user_id, is_active=True)
        except RegistryUser.DoesNotExist as exc:
            raise exceptions.AuthenticationFailed(_('User inactive or not found.')) from exc
        return (user, token)
