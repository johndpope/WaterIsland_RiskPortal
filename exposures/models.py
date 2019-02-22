from django.db import models

# Create your models here.


class ExposuresSnapshot(models.Model):
    """ Time-series of Exposures for all Funds """

    date = models.DateField()
    fund = models.CharField(max_length=10)
    sleeve = models.CharField(max_length=30)
    bucket = models.CharField(max_length=30)
    tradegroup = models.CharField(max_length=100)
    longshort = models.CharField(max_length=10)
    alpha_exposure = models.FloatField(null=True)
    hedge_exposure = models.FloatField(null=True)
    net_exposure = models.FloatField(null=True)
    gross_exposure = models.FloatField(null=True)
    capital = models.FloatField(null=True)
    directional_equity_risk = models.FloatField(null=True)
    directional_credit_risk = models.FloatField(null=True)
    directional_ir_risk = models.FloatField(null=True)
