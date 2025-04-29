from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from core import models

User = get_user_model()

class SmartBottleSerializer(ModelSerializer):
    class Meta:
        model = models.SmartBottle
        fields = '__all__'


class UserSerializer(ModelSerializer):
    bottle = SmartBottleSerializer()

    class Meta:
        model = User
        fields = ['id', 'email', 'fullname', 'picture', 'weight',
                  'gender', 'creatine_intake', 'date_joined', 'bottle']
        

class UserLoginSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)
    email = serializers.EmailField()


class NotificationSerializer(ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = models.Notification
        fields = ['id', 'seen', 'date_created', 'user']


class CreatineProductSerializer(ModelSerializer):
    class Meta:
        model = models.CreatineProduct
        fields = ['id', 'company_name', 'product_name', 'picture',
                  'price', 'discount', 'size', 'link', 'partner_id']


class WaterConsumptionSerializer(ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = models.WaterConsumption
        fields = ['id', 'max_water_intake', 'user_water_intake',
                  'date_created', 'updated_at', 'user']
