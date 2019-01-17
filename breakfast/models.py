from django.db import models
from accounts.models import User


# Create your models here.
import datetime
class BreakfastOrder(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    date = models.DateTimeField()
    order = models.CharField(max_length=500)
    status = models.CharField(max_length=12) #status should be confirmed/late