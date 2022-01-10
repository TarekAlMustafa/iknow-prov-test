from knox.models import AuthToken
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from .serializers import CreateUserSerializer, LoginUserSerializer, UserSerializer, OrganizationSerializer
from planthub.users.models import Organization

User = get_user_model()

class RegistrationAPI(generics.GenericAPIView):
    serializer_class = CreateUserSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if User.objects.filter(email=request.data['email']).exists():
            raise ValidationError("A user with this email already exists.")
        user = serializer.save()
        return Response({
            "user": CreateUserSerializer(user, context=self.get_serializer_context()).data,
            "token": AuthToken.objects.create(user)[1]
        })


class LoginAPI(generics.GenericAPIView):
    serializer_class = LoginUserSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        print(serializer)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data
        print(user)
        return Response({
            "user": CreateUserSerializer(user, context=self.get_serializer_context()).data,
            "token": AuthToken.objects.create(user)[1]
        })


class UserApi(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated, ]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

class OrganizationAPI(generics.GenericAPIView):
    def get_object(self):
        return Organization.objects.all()

    def get(self, request):
        organizations = self.get_object()
        print(organizations)
        serializer = OrganizationSerializer(organizations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
