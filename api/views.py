from datetime import timedelta
from collections import defaultdict
from django.contrib.auth import authenticate, get_user_model
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import datetime, time
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import (ListAPIView, RetrieveUpdateAPIView,
                                     RetrieveAPIView)
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.authtoken.models import Token
from . import serializers
from core.models import Notification, WaterConsumption
from .mixins import IsOwnerMixin

User = get_user_model()


class LoginAPIView(APIView):
    def post(self, request):
        serializer = serializers.UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        user = authenticate(request, email=email, password=password)

        if user is not None:
            token, _ = Token.objects.get_or_create(user=user)
            return Response({'token': token.key, 'id' : user.id}, status=status.HTTP_200_OK)
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


class NotificationsListAPIView(APIView):
    """Notifications History"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request): # Last week's notifications
        user = self.request.user
        eight_days_ago = timezone.now() - timedelta(days=8)
        now = timezone.localtime()
        start_of_today = datetime.combine(now.date(), time.min, tzinfo=now.tzinfo)
        notifications = Notification.objects.filter(user=user,
        date_created__gte=eight_days_ago,
        date_created__lt=start_of_today).order_by('-date_created')
        
        grouped = defaultdict(list) # Put notifications made in the same day in one group

        for notif in notifications:
            date_str = notif.date_created.date().isoformat()
            grouped[date_str].append(serializers.NotificationSerializer(notif).data)

        return Response(grouped)
    

class TodayNotificationsListAPIView(ListAPIView):
    """Notification Summary"""

    serializer_class = serializers.NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        now = timezone.localtime()
        start_of_today = datetime.combine(now.date(), time.min, tzinfo=now.tzinfo)
        notifications = Notification.objects.filter(user=user,
                                            date_created__gt=start_of_today)
        return notifications
    

class NotificationDetailsAPIView(APIView, IsOwnerMixin):
    def patch(self, request, pk):
        instance = get_object_or_404(Notification, id=pk)
        serializer = serializers.NotificationSerializer(instance=instance,
                                                            data=request.data,
                                                            partial=True)
        self.check_object_permission(request, instance)
        serializer.is_valid(raise_exception=True)
        instance.seen = serializer.validated_data['seen']
        try:
            instance.save()
        except:
            return Response({'error': 'Invalid data'},
                            status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'message': 'Updated successfully'},
                        status=status.HTTP_200_OK)
        

class LatestNotificationDetailsAPIView(RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.NotificationSerializer

    def get_object(self):
        return Notification.objects.filter(user=
        self.request.user).order_by('-date_created').first()


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


class UserRetrieveUpdateAPIView(RetrieveUpdateAPIView):
    queryset = get_user_model().objects.all()
    serializer_class = serializers.UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        obj = super().get_object()
        if obj != self.request.user:
            raise PermissionDenied('You do not have permission to access this object.')
        return obj

    def update(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj != self.request.user:
            raise PermissionDenied('You do not have permission to access this object.')
        return super().update(request, *args, **kwargs)


class RequestPasswordResetView(APIView):
    def post(self, request):
        email = request.data.get('email')
        try:
            user = User.objects.get(email=email)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = PasswordResetTokenGenerator().make_token(user)
            reset_link = f"myapp://PasswordResetConfirm?uid={uid}&token={token}"
            # reset_link = f"http://localhost:8081/PasswordResetConfirm?uid={uid}&token={token}" For browser or sim

            # Send email
            send_mail(
                'Reset Your Password',
                f'Click the link to reset your password: {reset_link}',
                'no-reply@hydrationIQ.com',
                [user.email],
                fail_silently=False,
            )

            return Response({'message': 'Reset link sent to your email'}, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)


class PasswordResetConfirmView(APIView):
    def post(self, request):
        uid = request.data.get('uid')
        token = request.data.get('token')
        new_password = request.data.get('password')

        try:
            uid = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=uid)

            if PasswordResetTokenGenerator().check_token(user, token):
                user.set_password(new_password)
                user.save()
                return Response({'message': 'Password reset successful'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Invalid or expired token'}, status=status.HTTP_400_BAD_REQUEST)

        except (User.DoesNotExist, ValueError, TypeError):
            return Response({'error': 'Invalid request'}, status=status.HTTP_400_BAD_REQUEST)
