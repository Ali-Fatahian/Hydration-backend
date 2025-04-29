from datetime import timedelta
from django.contrib.auth import authenticate, get_user_model
from django.utils import timezone
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.exceptions import ValidationError
from rest_framework.authtoken.models import Token
from . import serializers
from core.models import Notification


class LoginAPIView(APIView):
    def post(self, request):
        serializer = serializers.UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        user = authenticate(request, email=email, password=password)

        if user is not None:
            token, _ = Token.objects.get_or_create(user=user)
            return Response({'token': token.key}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid credentials'},
                             status=status.HTTP_400_BAD_REQUEST)


class RegisterAPIView(APIView):
    def post(self, request):
        serializer = serializers.UserRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        fullname = serializer.validated_data['fullname']
        password = serializer.validated_data['password']

        try:
            get_user_model().objects.create_user(email=email,
                                                fullname=fullname,
                                                password=password)
            return Response({'message': 'User was successfully created'}, 
                            status=status.HTTP_201_CREATED)
            
        except ValidationError: # Existing email
            return Response({'error': 'This email already exists'}, 
                            status=status.HTTP_400_BAD_REQUEST)


class NotificationsListAPIView(ListAPIView):
    serializer_class = serializers.NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self): # Last week's notifications
        user = self.request.user
        eight_days_ago = timezone.now() - timedelta(days=8)
        notifications = Notification.objects.filter(user=user,
                                            date_created__gt=eight_days_ago)
        return notifications
