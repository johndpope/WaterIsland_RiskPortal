from django.db import models

# Create your models here.


class EssDealTypeParameters(models.Model):
    deal_type = models.CharField(max_length=100, unique=True)
    long_probability = models.FloatField(null=True)
    long_irr = models.FloatField(null=True)
    long_max_risk = models.FloatField(null=True)
    long_max_size = models.FloatField(null=True)
    short_probability = models.FloatField(null=True)
    short_irr = models.FloatField(null=True)
    short_max_risk = models.FloatField(null=True)
    short_max_size = models.FloatField(null=True)


class NormalizedSizingByRiskAdjProb(models.Model):
    arb_max_risk = models.FloatField()
    win_probability = models.FloatField()
    lose_probability = models.FloatField()
    risk_adj_loss = models.FloatField()


class SoftCatalystNormalizedRiskSizing(models.Model):
    tier = models.CharField(max_length=10)
    win_probability = models.FloatField()
    lose_probability = models.FloatField()
    max_risk = models.FloatField()
    avg_position = models.FloatField()


class EssPotentialLongShorts(models.Model):
    ess_idea_id = models.IntegerField(null=False)
    Date = models.DateField(null=True)
    alpha_ticker = models.CharField(max_length=100)
    price = models.FloatField(null=True)
    pt_up = models.FloatField(null=True)
    pt_wic = models.FloatField(null=True)
    pt_down = models.FloatField(null=True)
    unaffected_date = models.DateField(null=True)
    expected_close = models.DateField(null=True)
    price_target_date = models.DateField(null=True)
    cix_index = models.CharField(max_length=50, null=True)
    category = models.CharField(max_length=100, null=True)
    catalyst = models.CharField(max_length=50, null=True)
    deal_type = models.CharField(max_length=50, null=True)
    catalyst_tier = models.CharField(max_length=10, null=True)
    gics_sector = models.CharField(max_length=100, null=True)
    hedges = models.CharField(max_length=10, null=True)
    lead_analyst = models.CharField(max_length=10, null=True)
    model_up = models.FloatField(null=True)
    model_wic = models.FloatField(null=True)
    model_down = models.FloatField(null=True)
    implied_probability = models.FloatField(null=True)
    return_risk = models.FloatField(null=True)
    gross_irr = models.FloatField(null=True)
    days_to_close = models.FloatField(null=True)
    ann_irr = models.FloatField(null=True)
    adj_ann_irr = models.FloatField(null=True)
    long_prob = models.FloatField(null=True)
    long_irr = models.FloatField(null=True)
    short_prob = models.FloatField(null=True)
    short_irr = models.FloatField(null=True)
    potential_long = models.CharField(max_length=10, null=True)
    potential_short = models.CharField(max_length=10, null=True)


class EssUniverseImpliedProbability(models.Model):
    Date = models.DateField()
    deal_type = models.CharField(max_length=100, null=True)
    implied_probability = models.FloatField(null=True)
    count = models.IntegerField(null=True)  # To count how many names in the avg. implied probability


# --------------------------- Merger Arbitrage Optimization Models -------------------------------------------

class ArbOptimizationUniverse(models.Model):
    date_updated = models.DateField()
    tradegroup = models.CharField(max_length=100)
    sleeve = models.CharField(max_length=50)
    bucket = models.CharField(max_length=50)
    catalyst = models.CharField(max_length=50, null=True)
    catalyst_rating = models.CharField(max_length=5, null=True)
    closing_date = models.DateField(null=True)
    target_ticker = models.CharField(max_length=100, null=True)
    long_short = models.CharField(max_length=50, null=True)
    target_last_price = models.FloatField(null=True)
    deal_value = models.FloatField(null=True)
    all_in_spread = models.FloatField(null=True)
    deal_downside = models.FloatField(null=True)
    days_to_close = models.IntegerField(null=True)
    pct_of_sleeve_current = models.FloatField(null=True)
    gross_ror = models.FloatField(null=True)
    ann_ror = models.FloatField(null=True)
    base_case_nav_impact = models.FloatField(null=True)
    risk_pct = models.FloatField(null=True)
    expected_vol = models.FloatField(null=True)






