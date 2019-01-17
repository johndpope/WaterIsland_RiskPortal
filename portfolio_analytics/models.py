from django.db import models

# Create your models here.
class DealUniverse(models.Model):
    ''' Model to represent all the unique deals taken from all the funds. Should be updated daily. '''
    id = models.AutoField(primary_key=True)
    deal_name = models.CharField(max_length=100)
    sleeve = models.CharField(max_length=50)
    bucket = models.CharField(max_length=50)
    closing_date = models.DateField(null=True)
    ticker = models.CharField(max_length=100, null=True)
    price = models.FloatField(null=True)
    downside = models.FloatField(null=True)
    upside = models.FloatField(null=True)
    pm_base_case = models.FloatField(null=True)
    deal_value = models.FloatField(null=True)
    catalyst_rating = models.IntegerField(null=True)
    origination_date = models.DateField(null=True)
    duration = models.IntegerField(null=True)
    sector = models.CharField(max_length=100)
    industry = models.CharField(max_length=100)
    risk_limit = models.FloatField(null=True)