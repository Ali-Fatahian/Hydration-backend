from django.contrib.auth import get_user_model
from rest_framework import serializers
from core import models

User = get_user_model()

class SmartBottleSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SmartBottle
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    bottle = SmartBottleSerializer()

    class Meta:
        model = User
        fields = ['id', 'email', 'fullname', 'picture', 'weight', 'activity',
                  'gender', 'creatine_intake', 'date_joined', 'bottle']
        

class UserLoginSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)
    email = serializers.EmailField() # Uniqueness of email field causes issues when using ModelSerializer


class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'fullname', 'password']


class NotificationSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = models.Notification
        fields = ['id', 'message', 'seen', 'date_created', 'user']


class CreatineProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CreatineProduct
        fields = ['id', 'company_name', 'product_name', 'picture',
                  'price', 'discount', 'size', 'link', 'partner_id',
                  'description']


class WaterConsumptionSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.email')

    class Meta:
        model = models.WaterConsumption
        fields = ['id', 'max_water_intake', 'user_water_intake',
                  'date_created', 'updated_at', 'user']
