from django.urls import path
from .views import (LoginAPIView, RegisterAPIView,
                    NotificationsListAPIView, TodayNotificationsListAPIView, 
                    NotificationDetailsAPIView, LatestNotificationDetailsAPIView,
                    WaterIntakeListCreatesAPIView, WaterIntakeDetailsAPIView,
                    UserRetrieveUpdateAPIView, RequestPasswordResetView,
                    PasswordResetConfirmView, CreatineProductListAPIView)

urlpatterns = [
    path('login', LoginAPIView.as_view(), name='login_api'),
    path('register', RegisterAPIView.as_view(), name='register_api'),
    path('notifications', NotificationsListAPIView.as_view(),
        name='notifications_list_api'),
    path('notifications/<int:pk>', NotificationDetailsAPIView.as_view(),
        name='notification_details_api'),
    path('latest_notification', LatestNotificationDetailsAPIView.as_view(),
        name='latest_notification_details_api'),
    path('today_notifications', TodayNotificationsListAPIView.as_view(),
        name='today_notifications_list_api'),
    path('water_intake', WaterIntakeListCreatesAPIView.as_view(),
        name='water_intake_api'),
    path('water_intake_details/<int:pk>', WaterIntakeDetailsAPIView.as_view(),
        name='water_intake_details_api'),
    path('users/<int:pk>', UserRetrieveUpdateAPIView.as_view(),
         name='user_retrieve_update_api'),
    path('password_reset', RequestPasswordResetView.as_view(),
        name='password_reset_api'),
    path('password_reset_confirm', PasswordResetConfirmView.as_view(),
        name='password_reset_confirm_api'),
    path('creatine_products', CreatineProductListAPIView.as_view(),
         name='creatine_product_list_api')
]
