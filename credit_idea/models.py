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
    arb_tradegroup = models.CharField(max_length=100, null=True)
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


class CreditIdeaDetails(models.Model):
    credit_idea = models.OneToOneField(CreditIdea, on_delete=models.CASCADE, primary_key=True)
    nav_pct_impact = models.FloatField(null=True, blank=True)
    topping_big_upside = models.FloatField(null=True, blank=True)
    base_case_downside = models.FloatField(null=True, blank=True)
    base_case_downside_type = models.CharField(null=True, blank=True, max_length=50)
    outlier_downside = models.FloatField(null=True, blank=True)
    outlier_downside_type = models.CharField(null=True, blank=True, max_length=50)
    target_ticker = models.CharField(null=True, blank=True, max_length=20)
    acq_ticker = models.CharField(null=True, blank=True, max_length=20)
    cash_consideration = models.FloatField(null=True, blank=True)
    share_consideration = models.FloatField(null=True, blank=True)
    deal_value = models.FloatField(null=True, blank=True)
    target_dividend = models.FloatField(null=True, blank=True)
    acq_dividend = models.FloatField(null=True, blank=True)
    fund_assets = models.FloatField(null=True, blank=True)
    float_so = models.FloatField(null=True, blank=True)
    acq_pb_rate = models.FloatField(null=True, blank=True)
    target_pb_rate = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class CreditIdeaScenario(models.Model):
    credit_idea = models.ForeignKey(CreditIdea, on_delete=models.CASCADE)
    scenario = models.CharField(null=True, blank=True, max_length=50)
    last_price = models.FloatField(null=True, blank=True, default=0)
    dividends = models.FloatField(null=True, blank=True, default=0)
    rebate = models.FloatField(null=True, blank=True, default=0)
    hedge = models.FloatField(null=True, blank=True, default=0)
    deal_value = models.FloatField(null=True, blank=True, default=0)
    spread = models.FloatField(null=True, blank=True, default=0)
    gross_pct = models.FloatField(null=True, blank=True, default=0)
    annual_pct = models.FloatField(null=True, blank=True, default=0)
    days_to_close = models.IntegerField(null=True, blank=True, default=0)
    dollars_to_make = models.FloatField(null=True, blank=True, default=0)
    dollars_to_lose = models.FloatField(null=True, blank=True, default=0)
    implied_prob = models.FloatField(null=True, blank=True, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    estimated_closing_date = models.DateField(null=True, blank=True)
