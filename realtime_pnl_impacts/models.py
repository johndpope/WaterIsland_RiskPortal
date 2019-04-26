from django.db import models


class ArbitrageYTDPerformance(models.Model):
    """ This Model is Deleted each night and refreshed with latest data """
    fund = models.CharField(max_length=100)
    sleeve = models.CharField(max_length=100, null=True)
    catalyst_wic = models.CharField(max_length=40, null=True) # Hard/Soft Catalyst
    tradegroup = models.CharField(max_length=120, null=False)
    long_short = models.CharField(max_length=10, null=True)
    inception_date = models.DateField(null=True)
    end_date = models.DateField(null=True)
    status = models.CharField(max_length=100, null=True)
    ytd_dollar = models.FloatField(null=True)
    fund_aum = models.FloatField(null=True)
    pnl_bps = models.FloatField(null=True)


class PnlMonitors(models.Model):
    fund = models.CharField(max_length=50)
    investable_assets = models.CharField(max_length=50)
    ann_gross_pnl_target_perc = models.CharField(max_length=50)
    gross_ytd_return = models.CharField(max_length=50)
    ytd_pnl_perc_target = models.CharField(max_length=50)
    time_passed = models.CharField(max_length=50)
    ann_gross_pnl_target_dollar = models.CharField(max_length=50)
    gross_ytd_pnl = models.CharField(max_length=50)
    ann_loss_budget_perc = models.CharField(max_length=50)
    ytd_total_loss_perc_budget = models.CharField(max_length=50)
    ann_loss_budget_dollar = models.CharField(max_length=50)
    ytd_closed_deal_losses = models.CharField(max_length=50)
    ytd_active_deal_losses = models.CharField(max_length=50)
    last_updated = models.DateField(auto_now_add=True)
