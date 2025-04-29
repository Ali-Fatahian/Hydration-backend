from django.contrib.auth import authenticate, get_user_model
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
from rest_framework.authtoken.models import Token
from . import serializers


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
