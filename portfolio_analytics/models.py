from django.db import models


class DealUniverse(models.Model):
    ''' Model to represent all the unique deals taken from all the funds. Should be updated daily. '''
    id = models.AutoField(primary_key=True)
    deal_name = models.CharField(max_length=100)
    sleeve = models.CharField(max_length=50)
    bucket = models.CharField(max_length=50)
    catalyst_type = models.CharField(max_length=50)
    catalyst_rating = models.IntegerField(null=True)
    closing_date = models.DateField(null=True)
    target_ticker = models.CharField(max_length=100, null=True)
    long_short = models.CharField(max_length=100)
    target_last_price = models.FloatField(null=True, blank=True)
    upside = models.FloatField(null=True)
    spread = models.FloatField(null=True)
    ask_px = models.CharField(max_length=100, null=True)
    days = models.IntegerField(null=True) 
    gross_ror = models.FloatField(null=True)
    ann_ror = models.FloatField(null=True)
    risk_percent = models.FloatField(null=True)
    ann_risk = models.FloatField(null=True)
    imp_prob = models.IntegerField(null=True)
    prob_adj_arr = models.IntegerField(null=True)
    return_risk = models.FloatField(null=True)
    imp_return_risk = models.FloatField(null=True)
    note = models.CharField(max_length=100, null=True)
    last_updated = models.DateTimeField(auto_now_add=True)
