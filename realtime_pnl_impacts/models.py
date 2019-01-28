from django.db import models

# Create your models here.


class ArbitrageYTDPerformance(models.Model):
    """ This Model is Deleted each night and refreshed with latest data """
    fund = models.CharField(max_length=100)
    sleeve = models.CharField(max_length=100, null=True)
    tradegroup = models.CharField(max_length=120, null=False)
    long_short = models.CharField(max_length=10, null=True)
    inception_date = models.DateField(null=True)
    end_date = models.DateField(null=True)
    status = models.CharField(max_length=100, null=True)
    ytd_dollar = models.FloatField(null=True)