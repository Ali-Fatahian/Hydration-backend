from django.contrib import admin
from . import models

admin.site.register(models.CustomUser)
admin.site.register(models.SmartBottle)
admin.site.register(models.Notification)
admin.site.register(models.CreatineProduct)
admin.site.register(models.WaterConsumption)
