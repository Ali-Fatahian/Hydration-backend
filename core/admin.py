from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from . import models
from .forms import CustomUserCreationForm, CustomUserChangeForm

class CustomUserAdmin(UserAdmin):
    model = models.CustomUser
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    list_display = ['email', 'fullname', 'is_active', 'is_staff']
    list_filter = ['is_active', 'is_staff']
    search_fields = ['email', 'fullname']
    ordering = ['email']

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('fullname', 'gender', 'picture', 'weight', 'creatine_intake')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
        (_('Smart Bottle'), {'fields': ('bottle',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'fullname', 'is_active', 'is_staff'),
        }),
    )


admin.site.register(models.CustomUser, CustomUserAdmin)
admin.site.register(models.SmartBottle)
admin.site.register(models.Notification)
admin.site.register(models.CreatineProduct)
admin.site.register(models.WaterConsumption)