from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from tsc_api.authn.serializers import LoginResponseSerializer, LoginSerializer, MeSerializer


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    @extend_schema(request=LoginSerializer, responses={200: LoginResponseSerializer}, auth=[])
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(
            {
                'access': serializer.validated_data['access'],
                'refresh': serializer.validated_data['refresh'],
            },
            status=status.HTTP_200_OK,
        )


class MeView(APIView):
    @extend_schema(responses={200: MeSerializer})
    def get(self, request):
        return Response(MeSerializer(request.user).data)
