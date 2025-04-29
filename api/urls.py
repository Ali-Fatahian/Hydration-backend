from django.urls import path
from .views import LoginAPIView, RegisterAPIView, NotificationsListAPIView

urlpatterns = [
    path('login', LoginAPIView.as_view(), name='login_api'),
    path('register', RegisterAPIView.as_view(), name='register_api'),
    path('notifications', NotificationsListAPIView.as_view(),
        name='notifications_list_api'),
]
