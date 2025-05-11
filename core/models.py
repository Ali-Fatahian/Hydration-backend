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
    username = None

    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
    ]

    email = models.EmailField(_("email address"), unique=True)
    fullname = models.CharField(_("full name"), max_length=100)
    picture = models.ImageField(_('picture'), max_length=255,
                                 blank=True, null=True)
    weight = models.DecimalField(_('weight'), max_digits=5, decimal_places=2,
                                  blank=True, null=True)
    gender = models.CharField(_('gender'), max_length=6, choices=GENDER_CHOICES,
                               blank=True, null=True)
    creatine_intake = models.DecimalField(_('creatine intake'), 
                                          max_digits=2, decimal_places=1,
                                            blank=True, null=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)
    bottle = models.OneToOneField('SmartBottle', on_delete=models.CASCADE,
                                   null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ['fullname']

    objects = CustomUserManager()

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.email


class SmartBottle(models.Model):
    name = models.CharField(_("bottle's name"), max_length=250) # Just for now

    def __str__(self):
        return self.name


class Notification(models.Model):
    message = models.CharField(_('Message'), max_length=355)
    seen = models.BooleanField(_('Seen'), default=False)
    date_created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)

    def mark_as_seen(self):
        self.seen = True
        self.save(update_fields=['seen'])

    def __str__(self):
        return f'Notification {self.id} for user {self.user.email}'


class CreatineProduct(models.Model):
    SIZE_CHOICES = [
        ('100', '100'),
        ('200', '200'),
        ('400', '400'),
        ('500', '500'),
        ('1000', '1000'),
    ]

    company_name = models.CharField(_("Company's Name"), max_length=255)
    product_name = models.CharField(_("Product's Name"), max_length=255)
    picture = models.ImageField(_('Picture'), upload_to='creatines',
                                 max_length=255)
    price = models.DecimalField(_('Price'), max_digits=5, decimal_places=2)
    discount = models.DecimalField(_('Discount'), max_digits=3, decimal_places=1
                                   , blank=True, default=0, null=True)
    size = models.CharField(_('Size'), choices=SIZE_CHOICES,
                            max_length=4, default=200)
    link = models.URLField(_('Link'))
    partner_id = models.CharField(_('Partner ID'), max_length=255)
    description = models.TextField(_('Description'), max_length=355,
                                   blank=True, default='', null=True)

    def __str__(self):
        return f'Company: {self.company_name}, Product: {self.product_name}'


class WaterConsumption(models.Model):
    max_water_intake = models.DecimalField(_('Max Water Intake'), max_digits=4,
                                            decimal_places=0) # Our suggestion
    user_water_intake = models.DecimalField(_('User Water Intake'),
                                             max_digits=5, decimal_places=1,
                                             blank=True, default=0)
    date_created = models.DateTimeField(_('Date Created'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)

    def __str__(self):
        return f'User {self.user.email} water intake on {self.date_created}'
