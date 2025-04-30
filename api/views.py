from datetime import timedelta
from django.contrib.auth import authenticate, get_user_model
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import datetime, time
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.exceptions import ValidationError
from rest_framework.authtoken.models import Token
from . import serializers
from core.models import Notification, WaterConsumption
from .mixins import IsOwnerMixin


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


class WaterIntakeListCreatesAPIView(APIView, IsOwnerMixin):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.WaterConsumptionSerializer

    def get(self, request):
        user = self.request.user
        now = timezone.localtime()  # uses the current Django timezone
        start_of_today = datetime.combine(now.date(), time.min, tzinfo=now.tzinfo) # Timezone aware today's date
        intake_objs = WaterConsumption.objects.filter(user=user,
                                    date_created__gt=start_of_today)
        length = len(intake_objs)
        if length > 1 or length == 1: # If the user already reached maximum water intake and started another activity in the same day > 1
            result_obj = intake_objs[length-1]
            self.check_object_permission(request, result_obj)
            serializer = self.serializer_class(result_obj)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'There is no water intakes for today'}, 
                            status=status.HTTP_404_NOT_FOUND)

    def post(self, request): # supposed to be called by AI
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        max_intake = serializer.validated_data['max_water_intake']
        user = self.request.user
        WaterConsumption.objects.create(max_water_intake=max_intake, user=user)
        return Response({'message': 'Created successfully'},
                         status=status.HTTP_201_CREATED)


class WaterIntakeDetailsAPIView(APIView, IsOwnerMixin):
    def patch(self, request, pk): # We only update the user's water intake
        instance = get_object_or_404(WaterConsumption, id=pk)
        serializer = serializers.WaterConsumptionSerializer(instance=instance,
                                                            data=request.data,
                                                            partial=True)
        self.check_object_permission(request, instance)
        serializer.is_valid(raise_exception=True)
        instance.user_water_intake = serializer.validated_data['user_water_intake']
        try:
            instance.save()
        except:
            return Response({'error': 'Please enter the intake correctly'},
                            status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'message': 'Updated successfully'},
                        status=status.HTTP_200_OK)