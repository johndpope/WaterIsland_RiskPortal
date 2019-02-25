import os
from django.db import models

class MA_Deals(models.Model):

    ''' Model to hold Merger ARb Deals '''
    id = models.AutoField(primary_key=True)
    deal_name = models.CharField(max_length=100)
    target_ticker = models.CharField(max_length=50)
    acquirer_ticker = models.CharField(max_length=50)
    target_last_price = models.CharField(max_length=10, default='0')
    analyst = models.CharField(max_length=50)
    created = models.DateField(default=None)
    last_modified = models.DateField(default=None)
    is_complete = models.CharField(default=None, max_length=5)
    deal_cash_terms = models.CharField(max_length=40,default=None)
    deal_share_terms = models.FloatField(default=0)
    status = models.CharField(max_length=40, default=None)
    deal_value = models.CharField(max_length=10, default='0')
    deal_upside = models.FloatField(default=0)
    target_downside = models.FloatField(default=0)
    acquirer_upside = models.FloatField(null=True, default=0)
    fund = models.CharField(max_length=30, default='ARB')
    fund_aum = models.CharField(max_length=20, default='0')
    last_downside_update = models.DateField(null=True)
    catalyst = models.CharField(max_length=10, null=True)  # Hard/Soft
    catalyst_tier = models.CharField(max_length=10, null=True)  # 1,2,3
    expected_closing_date = models.DateField(null=True)
    target_dividends = models.FloatField(null=True)
    acquirer_dividends = models.FloatField(null=True)
    short_rebate = models.FloatField(null=True)
    stub_cvr_value = models.FloatField(null=True)
    fx_carry_percent = models.CharField(max_length=10,null=True) #eg 2%
    loss_tolerance_percentage_of_limit = models.CharField(max_length=10, null=True)
    unaffected_date = models.TextField(null=True)
    cix_index = models.CharField(max_length=100, null=True)
    cix_index_chart = models.TextField(null=True)
    spread_index = models.CharField(max_length=100, null=True)
    spread_index_chart = models.TextField(null=True)
    archived = models.BooleanField(default=False)

    def __str__(self):
        return self.deal_name + ' By-'+self.analyst


class MA_Deals_WeeklyDownsideEstimates(models.Model):
    ''' Model for current and historical Downside estimates '''
    week_no = models.IntegerField()
    start_date = models.DateField()
    end_date = models.DateField()
    deal = models.ForeignKey(MA_Deals, on_delete=models.CASCADE)
    estimate = models.CharField(max_length=25, default='Not Entered')
    comment = models.TextField(default='No Comment Entered')
    analyst = models.CharField(max_length=100, null=True)
    date_updated = models.DateField(null=True)
    def __str__(self):
        return str(self.week_no)



class MA_Deals_Lawyer_Reports(models.Model):
    deal = models.ForeignKey(MA_Deals, on_delete=models.CASCADE)
    lawyer_report_date = models.DateField()
    lawyer_report = models.TextField()
    analyst_by = models.CharField(max_length=100)
    analyst_rating = models.CharField(max_length=1)



class MA_Deals_PeerSet(models.Model):
    deal = models.ForeignKey(MA_Deals, on_delete=models.CASCADE)
    peer = models.CharField(max_length=75)
    ev_ebitda_chart_ltm = models.TextField()
    ev_ebitda_chart_1bf = models.TextField()
    ev_ebitda_chart_2bf = models.TextField()
    ev_sales_chart_ltm = models.TextField()
    ev_sales_chart_1bf = models.TextField()
    ev_sales_chart_2bf = models.TextField()
    pe_ratio_chart_ltm = models.TextField()
    pe_ratio_chart_1bf = models.TextField()
    pe_ratio_chart_2bf = models.TextField()
    fcf_yield_chart = models.TextField()    #JSON representaion of charts


class MA_Deals_Scenario_Analysis(models.Model):
    deal = models.OneToOneField(MA_Deals, on_delete=models.CASCADE)
    break_scenario_df = models.TextField()
    scenario_75_25 = models.TextField()
    scenario_change = models.FloatField()
    break_change = models.FloatField()
    scenario_change_55_45 = models.FloatField()
    scenario_55_45 = models.TextField()



class MA_Deals_Notes(models.Model):
    deal = models.OneToOneField(MA_Deals, on_delete=models.CASCADE)
    note = models.TextField()
    last_edited = models.DateTimeField() # when was the note created...?


class ESS_Peers(models.Model):
    ''' Model for Peer Valuation '''
    class Meta:
        unique_together = (('id', 'version_number'),)

    version_number = models.IntegerField(default=0)
    ticker = models.CharField(max_length=30)
    hedge_weight = models.FloatField() #Max 100 only
    ev_ebitda_chart_ltm = models.TextField()
    ev_ebitda_chart_1bf = models.TextField()
    ev_ebitda_chart_2bf = models.TextField()

    ev_sales_chart_ltm = models.TextField()
    ev_sales_chart_1bf = models.TextField()
    ev_sales_chart_2bf = models.TextField()

    p_eps_chart_ltm = models.TextField()
    p_eps_chart_1bf = models.TextField()
    p_eps_chart_2bf = models.TextField()
    p_fcf_chart = models.TextField()
    name = models.CharField(max_length=150, default='Unknown')
    enterprise_value = models.TextField(default='N/A')
    market_cap = models.TextField(default='N/A')
    ev_ebitda_bf1 = models.TextField(default='N/A')
    ev_ebitda_bf2 = models.TextField(default='N/A')\

    ev_sales_bf1 = models.TextField(default='N/A')
    ev_sales_bf2 = models.TextField(default='N/A')
    p_e_bf1 = models.TextField(default='N/A')
    p_e_bf2 = models.TextField(default='N/A')
    fcf_yield_bf1 = models.TextField(default='N/A')
    fcf_yield_bf2 = models.TextField(default='N/A')
    ess_idea_id = models.ForeignKey('ESS_Idea', on_delete=models.CASCADE, null=True)


    def __str__(self):
        return self.ticker + '-' + str(self.hedge_weight)


class ESS_Idea_Upside_Downside_Change_Records(models.Model):
    ess_idea_id = models.ForeignKey('ESS_Idea', on_delete=models.CASCADE)
    deal_key = models.IntegerField(null=True) #DealKey reflecting a deal
    pt_up = models.FloatField(null=True)
    pt_wic = models.FloatField(null=True)
    pt_down = models.FloatField(null=True)
    date_updated = models.DateField(null=False) #Updated Record shouldn't be Null


class ESS_Idea_BullFileUploads(models.Model):
    ess_idea_id = models.ForeignKey('ESS_Idea', on_delete=models.CASCADE)
    deal_key = models.IntegerField(null=True)  # DealKey reflecting a deal
    bull_thesis_model = models.FileField(null=True, upload_to='ESS_IDEA_DB_FILES/BULL_THESIS_FILES')
    uploaded_at = models.DateField(null=True)

    def filename(self):
        return os.path.basename(self.bull_thesis_model.name)


class ESS_Idea_OurFileUploads(models.Model):
    ess_idea_id = models.ForeignKey('ESS_Idea', on_delete=models.CASCADE)
    deal_key = models.IntegerField(null=True)  # DealKey reflecting a deal
    our_thesis_model = models.FileField(null=True, upload_to='ESS_IDEA_DB_FILES/OUR_THESIS_FILES')
    uploaded_at = models.DateField(null=True)

    def filename(self):
        return os.path.basename(self.our_thesis_model.name)

class ESS_Idea_BearFileUploads(models.Model):
    ess_idea_id = models.ForeignKey('ESS_Idea', on_delete=models.CASCADE)
    deal_key = models.IntegerField(null=True)  # DealKey reflecting a deal
    bear_thesis_model = models.FileField(null=True, upload_to='ESS_IDEA_DB_FILES/BEAR_THESIS_FILES')
    uploaded_at = models.DateField(null=True)

    def filename(self):
        return os.path.basename(self.bear_thesis_model.name)

class ESS_Idea(models.Model):
    class Meta:
        unique_together = (('id', 'version_number'))
        get_latest_by = 'version_number'

    deal_key = models.IntegerField(null=False)
    alpha_ticker = models.CharField(max_length=30) #30 sufficient for ticker length
    price = models.FloatField()
    pt_up = models.FloatField()
    pt_wic = models.FloatField()
    pt_down = models.FloatField()
    unaffected_date = models.DateField()
    expected_close = models.DateField()
    gross_percentage = models.CharField(max_length=20)
    ann_percentage = models.CharField(max_length=20)
    hedged_volatility = models.CharField(max_length=20)
    theoretical_sharpe = models.CharField(max_length=20)
    implied_probability = models.CharField(max_length=20)
    event_premium = models.CharField(max_length=20)
    situation_overview = models.TextField()
    company_overview = models.TextField()
    bull_thesis = models.TextField()
    our_thesis = models.TextField()
    bear_thesis = models.TextField()
    m_value = models.IntegerField(default=0)
    o_value = models.IntegerField(default=0)
    s_value = models.IntegerField(default=0)
    a_value = models.IntegerField(default=0)
    i_value = models.IntegerField(default=0)
    c_value = models.IntegerField(default=0)
    m_overview = models.TextField(default='N/A')
    o_overview = models.TextField(default='N/A')
    s_overview = models.TextField(default='N/A')
    a_overview = models.TextField(default='N/A')
    i_overview = models.TextField(default='N/A')
    c_overview = models.TextField(default='N/A')
    alpha_chart = models.TextField()
    hedge_chart = models.TextField()
    market_neutral_chart = models.TextField()
    implied_probability_chart = models.TextField()
    event_premium_chart = models.TextField()
    valuator_multiple_chart = models.TextField()
    ev_ebitda_chart_1bf = models.TextField()
    ev_ebitda_chart_2bf = models.TextField()
    ev_ebitda_chart_ltm = models.TextField()

    ev_sales_chart_1bf = models.TextField()
    ev_sales_chart_2bf = models.TextField()
    ev_sales_chart_ltm = models.TextField()

    p_eps_chart_1bf = models.TextField()
    p_eps_chart_2bf = models.TextField()
    p_eps_chart_ltm = models.TextField()
    fcf_yield_chart = models.TextField()
    price_target_date = models.DateField()
    multiples_dictionary = models.TextField()  # Save Multiples and Weight as Dictionary
    cix_index = models.CharField(max_length=100, null=True)
    category = models.CharField(max_length=100, null=True)
    catalyst = models.CharField(max_length=5, null=True)
    deal_type = models.CharField(max_length=100, null=True)
    catalyst_tier = models.CharField(max_length=5, null=True)
    gics_sector = models.CharField(max_length=100, null=True)
    hedges = models.CharField(max_length=5, null=True) # Yes/No field
    needs_downside_attention = models.IntegerField(null=True)  # Indicated whether downside needs to be revised...
    status = models.CharField(max_length=100, null=True, default='Backlogged')
    lead_analyst = models.CharField(max_length=100, null=True, default='Unallocated')  # Analyst working on the deal
    version_number = models.IntegerField(default=0)
    idea_balance_sheet = models.TextField(null=True)  # This field reflects the Balance Sheet Adjustments.
    on_pt_balance_sheet = models.TextField(null=True)  # This field reflects the Adjustments on Price Target Date
    pt_up_check = models.CharField(max_length=10, null=True)
    pt_down_check = models.CharField(max_length=10, null=True)
    pt_wic_check = models.CharField(max_length=10, null=True)
    how_to_adjust = models.CharField(max_length=10, null=True, default='cix')   # CIX or Regression
    premium_format = models.CharField(max_length=10, null=True, default='dollar')  # Dollar or Percentage

class CreditDatabase(models.Model):
    id = models.AutoField(primary_key=True)
    deal_name = models.CharField(max_length=100, null=True)
    deal_bucket = models.CharField(max_length=100, null=True)  # populated through drop down
    deal_strategy_type = models.CharField(max_length=100, null=True)  # Populated through drop-down
    catalyst = models.CharField(max_length=100, null=True)
    catalyst_tier = models.CharField(max_length=10, null=True)
    target_security_cusip = models.CharField(max_length=100, null=True)
    coupon = models.CharField(max_length=10, null=True)
    hedge_security_cusip = models.CharField(max_length=100, null=True)
    estimated_close_date = models.DateField(null=True)
    upside_price = models.FloatField(null=True)
    downside_price = models.FloatField(null=True)
