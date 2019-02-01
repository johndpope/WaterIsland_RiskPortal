from django.db import models

# Create your models here.


class SecurityMaster(models.Model):
    deal_name = models.CharField(max_length=200)
    cash_terms = models.FloatField(null=True)
    stock_terms = models.FloatField(null=True)
    number_of_target_dividends = models.CharField(max_length=100, null=True)
    number_of_acquirer_dividends = models.CharField(max_length=100, null=True)
    target_dividend_rate = models.CharField(max_length=100, null=True)
    acquirer_dividend_rate = models.CharField(max_length=100, null=True)
    closing_date = models.DateField(null=True)