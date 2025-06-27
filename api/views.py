from datetime import timedelta
from collections import defaultdict
import requests
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
from core.models import Notification, WaterConsumption, CreatineProduct
from .mixins import IsOwnerMixin

import random

User = get_user_model()
WEATHER_API_KEY = "1abd54e04598b27a08c1f65af2d7ff2a"
TOGETHER_API_KEY = "61af2e7656babc2a236f7b1602d5cb5a231d547da701b224273ddae2e114620b"
TOGETHER_MODEL = "mistralai/Mistral-7B-Instruct-v0.1"


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

    def post(self, request):
        now = timezone.localtime()
        start_of_today = datetime.combine(now.date(), time.min, tzinfo=now.tzinfo)
        intake_objs = WaterConsumption.objects.filter(user=self.request.user,
                                    date_created__gt=start_of_today)
        length = len(intake_objs)
        if length > 1 or length == 1:
            result_obj = intake_objs[length-1]
            if result_obj.max_water_intake == result_obj.user_water_intake: # Reached max, make a new one
                try:
                    user = self.request.user
                    temperature_celsius = request.data.get('temperature_celsius')
                    humidity_percent = int(request.data.get('humidity_percent'))
                    base = max(2000, user.weight * 35) if user.gender == "female" else max(2500, user.weight * 35)
                    temp_adjust = max(0, (int(temperature_celsius) - 20) * 10)
                    humidity_adjust = 200 if humidity_percent > 70 else 100 if humidity_percent >= 50 else 0
                    activity_map = {"low": 0, "moderate": 350, "high": 700}
                    activity_adjust = activity_map.get(user.activity, 0)
                    creatine_adjust = user.creatine_intake * 100

                    total_ml = round(base + temp_adjust + activity_adjust + creatine_adjust + humidity_adjust)
                    new_obj = WaterConsumption.objects.create(max_water_intake=total_ml, user=user)
                    



                    emoji = random.choice(["💧", "🥤", "🚰", "🫗", "🌊", "🏃‍♂️"])
                    prompt = (
                        f"A person weighs {user.weight}kg, is {user.gender}, exercises at a {user.activity} level, "
                        f"takes {user.creatine_intake}g creatine daily, and lives in {temperature_celsius}°C with {humidity_percent}% humidity. "
                        f"{emoji} Give a unique motivational hydration tip under 15 words."
                    )

                    together_response = requests.post(
                        "https://api.together.xyz/inference",
                        headers={
                            "Authorization": f"Bearer {TOGETHER_API_KEY}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": TOGETHER_MODEL,
                            "prompt": prompt,
                            "max_tokens": 50,
                            "temperature": 0.9,
                            "top_p": 0.95,
                            "repetition_penalty": 1.0
                        },
                        timeout=30
                    )

                    if together_response.status_code != 200:
                        return Response({'error': 'Together.ai error'}, status=status.HTTP_400_BAD_REQUEST)
                    else:
                        ai_data = together_response.json()
                        ai_advice = ai_data.get("output", {}).get("choices", [{}])[0].get("text", "").strip()
                        Notification.objects.create(message=ai_advice, user=self.request.user)
                    
                    serializer = serializers.WaterConsumptionSerializer(new_obj)
                    return Response({'message': serializer.data},
                                status=status.HTTP_201_CREATED)

                except Exception as e:
                    return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

            else:
                return Response({"error": "The current water intake has not finished"}, status=status.HTTP_400_BAD_REQUEST)   
        else: # If there are no objects for the day

            try:
                user = self.request.user
                temperature_celsius = request.data.get('temperature_celsius')
                humidity_percent = int(request.data.get('humidity_percent'))
                base = max(2000, user.weight * 35) if user.gender == "female" else max(2500, user.weight * 35)
                temp_adjust = max(0, (int(temperature_celsius) - 20) * 10)
                humidity_adjust = 200 if humidity_percent > 70 else 100 if humidity_percent >= 50 else 0
                activity_map = {"low": 0, "moderate": 350, "high": 700}
                activity_adjust = activity_map.get(user.activity, 0)
                creatine_adjust = user.creatine_intake * 100
                total_ml = round(base + temp_adjust + activity_adjust + creatine_adjust + humidity_adjust)
                new_obj_1 = WaterConsumption.objects.create(max_water_intake=total_ml, user=user)

                emoji = random.choice(["💧", "🥤", "🚰", "🫗", "🌊", "🏃‍♂️"])
                prompt = (
                    f"A person weighs {user.weight}kg, is {user.gender}, exercises at a {user.activity} level, "
                    f"takes {user.creatine_intake}g creatine daily, and lives in {temperature_celsius}°C with {humidity_percent}% humidity. "
                    f"{emoji} Give a unique motivational hydration tip under 15 words."
                )

                together_response = requests.post(
                    "https://api.together.xyz/inference",
                    headers={
                        "Authorization": f"Bearer {TOGETHER_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": TOGETHER_MODEL,
                        "prompt": prompt,
                        "max_tokens": 50,
                        "temperature": 0.9,
                        "top_p": 0.95,
                        "repetition_penalty": 1.0
                    },
                    timeout=30
                )

                if together_response.status_code != 200:
                    return Response({'error': 'Together.ai error'}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    ai_data = together_response.json()
                    ai_advice = ai_data.get("output", {}).get("choices", [{}])[0].get("text", "").strip()
                    Notification.objects.create(message=ai_advice, user=self.request.user)
                    
                serializer = serializers.WaterConsumptionSerializer(new_obj_1)
                return Response({'message': serializer.data},
                                status=status.HTTP_201_CREATED)

    #         insights = [
    #             f"Temperature: {temp_c}°C → +{temp_adjust}ml",
    #             f"Humidity: {humidity}% → +{humidity_adjust}ml",
    #             f"Activity level: {activity_level} → +{activity_adjust}ml",
    #             f"Creatine: {creatine_dosage}g → +{creatine_adjust}ml"
    #         ]

    #         summary = f"Estimated daily intake: ~{total_ml} ml."

            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class WaterIntakeDetailsAPIView(APIView, IsOwnerMixin):
    def patch(self, request, pk): # We only update the user's water intake
        instance = get_object_or_404(WaterConsumption, id=pk)
        serializer = serializers.WaterConsumptionSerializer(instance=instance,
                                                            data=request.data,
                                                            partial=True)
        self.check_object_permission(request, instance)
        serializer.is_valid(raise_exception=True)
        if serializer.validated_data['user_water_intake'] == instance.max_water_intake or serializer.validated_data['user_water_intake'] > instance.max_water_intake:
            instance.user_water_intake = instance.max_water_intake
        else:
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


class CreatineProductListAPIView(ListAPIView):
    queryset = CreatineProduct.objects.all()
    serializer_class = serializers.CreatineProductSerializer
    permission_classes = [permissions.IsAuthenticated]


# import requests
# import random
# from datetime import datetime
# from rest_framework.decorators import api_view
# from rest_framework.response import Response
# from rest_framework import status

# @api_view(["POST"])
# def hydration_goal(request):
#     try:
#         data = request.data
#         weight = float(data.get("weight"))
#         gender = data.get("gender", "").lower()
#         creatine_dosage = float(data.get("creatine_dosage"))
#         activity_level = data.get("activity_level", "").lower()
#         latitude = float(data.get("latitude"))
#         longitude = float(data.get("longitude"))

#         # Weather data
#         weather_url = (
#             f"http://api.openweathermap.org/data/2.5/weather?"
#             f"lat={latitude}&lon={longitude}&appid={WEATHER_API_KEY}&units=metric"
#         )
#         weather_response = requests.get(weather_url)
#         if weather_response.status_code != 200:
#             return Response({"error": "Weather API error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#         weather = weather_response.json()
#         temp_c = weather.get("main", {}).get("temp")
#         humidity = weather.get("main", {}).get("humidity")

#         if temp_c is None or humidity is None:
#             return Response({"error": "Missing weather data"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#         # Hydration calculation (EFSA-based)
#         base = max(2000, weight * 35) if gender == "female" else max(2500, weight * 35)
#         temp_adjust = max(0, (temp_c - 20) * 10)
#         activity_map = {"low": 0, "moderate": 350, "high": 700}
#         activity_adjust = activity_map.get(activity_level, 0)
#         creatine_adjust = creatine_dosage * 100
#         humidity_adjust = 200 if humidity > 70 else 100 if humidity >= 50 else 0

#         total_ml = round(base + temp_adjust + activity_adjust + creatine_adjust + humidity_adjust)

#         # AI advice generation
#         emoji = random.choice(["💧", "🥤", "🚰", "🫗", "🌊", "🏃‍♂️"])
#         prompt = (
#             f"A person weighs {weight}kg, is {gender}, exercises at a {activity_level} level, "
#             f"takes {creatine_dosage}g creatine daily, and lives in {temp_c}°C with {humidity}% humidity. "
#             f"{emoji} Give a unique motivational hydration tip under 15 words."
#         )

#         together_response = requests.post(
#             "https://api.together.xyz/inference",
#             headers={
#                 "Authorization": f"Bearer {TOGETHER_API_KEY}",
#                 "Content-Type": "application/json"
#             },
#             json={
#                 "model": TOGETHER_MODEL,
#                 "prompt": prompt,
#                 "max_tokens": 50,
#                 "temperature": 0.9,
#                 "top_p": 0.95,
#                 "repetition_penalty": 1.0
#             },
#             timeout=30
#         )

#         if together_response.status_code != 200:
#             ai_advice = f"⚠️ Together.ai error {together_response.status_code}"
#         else:
#             ai_data = together_response.json()
#             ai_advice = ai_data.get("output", {}).get("choices", [{}])[0].get("text", "").strip()

#         insights = [
#             f"Temperature: {temp_c}°C → +{temp_adjust}ml",
#             f"Humidity: {humidity}% → +{humidity_adjust}ml",
#             f"Activity level: {activity_level} → +{activity_adjust}ml",
#             f"Creatine: {creatine_dosage}g → +{creatine_adjust}ml"
#         ]

#         summary = f"Estimated daily intake: ~{total_ml} ml."

#         return Response({
#             "date": datetime.now().strftime("%Y-%m-%d"),
#             "temperature_c": temp_c,
#             "humidity_percent": humidity,
#             "hydration_goal_ml": total_ml,
#             "insight_summary": summary,
#             "insight_details": insights,
#             "ai_generated_advice": ai_advice
#         })

#     except Exception as e:
#         return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class WeatherInfoAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            latitude = float(request.query_params.get("latitude"))
            longitude = float(request.query_params.get("longitude"))

            weather_url = (
                f"http://api.openweathermap.org/data/2.5/weather?"
                f"lat={latitude}&lon={longitude}&appid={WEATHER_API_KEY}&units=metric"
            )
            weather_response = requests.get(weather_url)
            if weather_response.status_code != 200:
                return Response({"error": "Weather API error"}, status=status.HTTP_400_BAD_REQUEST)

            weather = weather_response.json()
            temp_c = weather.get("main", {}).get("temp")
            humidity = weather.get("main", {}).get("humidity")

            if temp_c is None or humidity is None:
                return Response({"error": "Missing weather data"}, status=status.HTTP_400_BAD_REQUEST)
            
            return Response({
                "temperature_celsius": temp_c,
                "humidity_percent": humidity
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
