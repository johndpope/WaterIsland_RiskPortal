from django.db import models


DEAL_BUCKET = (
    ('Catalyst-Driven Credit', 'Catalyst-Driven Credit'),
    ('Merger Related Credit', 'Merger Related Credit'),
    ('Relative Value Credit', 'Relative Value Credit'),
    ('Distressed', 'Distressed'),
    ('Yield to Call', 'Yield to Call'),
)

DEAL_STRATEGY_TYPE = (
    ('Refinancing', 'Refinancing'),
    ('Speculated M&A', 'Speculated M&A'),
    ('Merger Arbitrage', 'Merger Arbitrage'),
    ('Relative Value', 'Relative Value'),
    ('Definitive M&A', 'Definitive M&A'),
    ('Special Situation', 'Special Situation'),
    ('Levering', 'Levering'),
    ('Deep Value', 'Deep Value'),
    ('De-Levering', 'De-Levering'),
    ('Spin-off', 'Spin-off'),
)

CATALYST = (
    ('Hard', 'Hard'),
    ('Soft', 'Soft'),
)

CATALYST_TIER = (
    ('1', '1'),
    ('2', '2'),
    ('3', '3'),
)


class CreditIdea(models.Model):
    """
    Models for Credit Idea Database
    """
    id = models.AutoField(primary_key=True)
    analyst = models.CharField(max_length=100, null=True, blank=True)
    deal_bucket = models.CharField(null=True, blank=True, max_length=100, choices=DEAL_BUCKET)
    deal_strategy_type = models.CharField(null=True, blank=True, max_length=100, choices=DEAL_STRATEGY_TYPE)
    catalyst = models.CharField(null=True, blank=True, max_length=100, choices=CATALYST)
    catalyst_tier = models.CharField(null=True, blank=True, max_length=10, choices=CATALYST_TIER)
    target_sec_cusip = models.CharField(null=True, blank=True, max_length=50)
    coupon = models.CharField(null=True, blank=True, max_length=100)
    hedge_sec_cusip = models.CharField(null=True, blank=True, max_length=50)
    estimated_closing_date = models.DateField(null=True, blank=True)
    upside_price = models.FloatField(null=True, blank=True)
    downside_price = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    comments = models.TextField(null=True, blank=True)
