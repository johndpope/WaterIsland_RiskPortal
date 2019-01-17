from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
# Create your models here.
class User(AbstractUser):
    phone_regex = RegexValidator(regex=r'^\d{10}$', message="Please enter a valid phone number (10 digits)")
    phone_number = models.CharField(validators=[phone_regex], max_length=17, blank=True)  # validators should be a list



