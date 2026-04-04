from django.contrib.auth.hashers import check_password, make_password
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from tsc_api.registry.models import RegistryUser


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        try:
            user = RegistryUser.objects.select_related('role').get(username=username)
        except RegistryUser.DoesNotExist as exc:
            raise serializers.ValidationError('Invalid credentials.') from exc

        if not user.is_active:
            raise serializers.ValidationError('User is inactive.')

        if not check_password(password, user.password_hash):
            raise serializers.ValidationError('Invalid credentials.')

        user.last_login_at = timezone.now()
        user.save(update_fields=['last_login_at'])

        refresh = RefreshToken()
        refresh['user_id'] = user.user_id
        refresh['username'] = user.username
        refresh['role'] = user.role.role_name

        attrs['user'] = user
        attrs['access'] = str(refresh.access_token)
        attrs['refresh'] = str(refresh)
        return attrs


class MeSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source='role.role_name', read_only=True)

    class Meta:
        model = RegistryUser
        fields = ('user_id', 'username', 'email', 'role', 'is_active', 'created_at', 'last_login_at')


class LoginResponseSerializer(serializers.Serializer):
    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, attrs):
        user = self.context['request'].user
        if not check_password(attrs['old_password'], user.password_hash):
            raise serializers.ValidationError({'old_password': 'Old password is incorrect.'})
        if attrs['old_password'] == attrs['new_password']:
            raise serializers.ValidationError({'new_password': 'New password must be different from old password.'})
        return attrs

    def save(self, **kwargs):
        user = self.context['request'].user
        user.password_hash = make_password(self.validated_data['new_password'])
        user.save(update_fields=['password_hash'])
        return user
