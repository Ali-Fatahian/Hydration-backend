from django.urls import path
from .views import (LoginAPIView, RegisterAPIView,
                    NotificationsListAPIView, WaterIntakeListCreatesAPIView,
                    WaterIntakeDetailsAPIView, UserRetrieveUpdateAPIView)

urlpatterns = [
    path('login', LoginAPIView.as_view(), name='login_api'),
    path('register', RegisterAPIView.as_view(), name='register_api'),
    path('notifications', NotificationsListAPIView.as_view(),
        name='notifications_list_api'),
    path('water_intake', WaterIntakeListCreatesAPIView.as_view(),
          name='water_intake_api'),
    path('water_intake_details/<int:pk>', WaterIntakeDetailsAPIView.as_view(),
          name='water_intake_details_api'),
    path('users/<int:pk>', UserRetrieveUpdateAPIView.as_view(),
         name='user_retrieve_update_api'),
]
