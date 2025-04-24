from django.db import models
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


class CustomUserManager(BaseUserManager):
    def create_user(self, fullname, email, password, **extra_fields):
        if not email:
            raise ValueError(_("You must provide your email."))
        if not fullname:
            raise ValueError(_("You must provide your full name."))
        email = self.normalize_email(email)
        user = self.model(email=email, fullname=fullname, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, fullname, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))
        return self.create_user(fullname, email, password, **extra_fields)



class CustomUser(AbstractUser):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
    ]

    email = models.EmailField(_("email address"), unique=True)
    fullname = models.CharField(_("full name"), max_length=100)
    picture = models.ImageField(_('picture'), max_length=255, blank=True, null=True)
    weight = models.DecimalField(_('weight'), max_digits=3, decimal_places=2, blank=True, null=True)
    gender = models.CharField(_('gender'), max_length=6, choices=GENDER_CHOICES, blank=True, null=True)
    creatine_intake = models.DecimalField(_('creatine intake'), max_digits=2, decimal_places=1, blank=True, null=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)
    bottle = models.OneToOneField('SmartBottle', on_delete=models.CASCADE, null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ['fullname']

    objects = CustomUserManager()

    def __str__(self):
        return self.email


class SmartBottle(models.Model):
    name = models.CharField(_("bottle's name"), max_length=250) # Just for now
