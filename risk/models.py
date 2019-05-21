import datetime
import os
import uuid

from django.db import models

# from custom_storages import get_custom_path_filename

class MA_Deals(models.Model):
    ''' Model to hold Merger ARb Deals '''
    id = models.AutoField(primary_key=True)
    action_id = models.CharField(max_length=20, null=True)
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



DEFINITENESS_CHOICES = (
    ('Definitive Agreement', 'Definitive Agreement'),
    ('Agreement in Principle', 'Agreement in Principle'),
)

HOSTILE_CHOICES = (
    ('Hostile', 'Hostile'),
    ('Friendly', 'Friendly'),
)

STRATEGIC_CHOICES = (
    ('Strategic', 'Strategic'),
    ('PE', 'PE'),
)

DEAL_RATIONALE_CHOICES = (
    ('One of a kind asset', 'One of a kind asset'),
    ('Synergy', 'Synergy'),
    ('Market Share', 'Market Share'),
    ('Economy of Scale', 'Economy of Scale'),
    ('Taxation', 'Taxation'),
    ('Diversification', 'Diversification'),
    ('Vertical Integration', 'Vertical Integration'),
)

STOCK_CASH_CHOICES = (
    ('Cash Tender', 'Cash Tender'),
    ('Stock Exchange', 'Stock Exchange'),
    ('Scheme of an Arrangement', 'Scheme of an Arrangement'),
    ('Merger all Cash', 'Merger all Cash'),
    ('Merger with Stock Portion', 'Merger with Stock Portion'),
)

GO_SHOP_CHOICES = (
    ('No', 'No'),
    ('Yes', 'Yes'),
)

DIVESTITURES_CHOICES = (
    ('Not Required', 'Not Required'),
    ('required', 'required'),
)

FAIR_VALUATION_CHOICES = (
    ('N/A', 'N/A'),
    ('Fair', 'Fair'),
    ('Overvalued', 'Overvalued'),
    ('Undervalued', 'Undervalued'),
)

CYCLINCAL_INDUSTRY_CHOICES = (
    ('No', 'No'),
    ('Yes', 'Yes'),
)

SEC_REQUIREMENT_CHOICES = (
    ('Not required', 'Not required'),
    ('Required - Proxy Review', 'Required - Proxy Review'),
    ('Required - S4 for US Buyer', 'Required - S4 for US Buyer'),
    ('Required - S4 for Foreign Buyer', 'Required - S4 for Foreign Buyer'),
)

HSR_REQUIREMENT_CHOICES = (
    ('Not required', 'Not required'),
    ('Required - Expected Phase I', 'Required - Expected Phase I'),
    ('Required - Expected Phase II', 'Required - Expected Phase II'),
    ('Required - Potential Block', 'Required - Potential Block'),
)

MOFCOM_REQUIREMENT_CHOICES = (
    ('Not required', 'Not required'),
    ('Required - Expected Phase I', 'Required - Expected Phase I'),
    ('Required - Expected Phase II', 'Required - Expected Phase II'),
    ('Required - Expected Phase III', 'Required - Expected Phase III'),
    ('Required - Potential Block', 'Required - Potential Block'),
)

CIFIUS_REPLACEMENT_CHOICES = (
    ('Not required', 'Not required'),
    ('Required - Expected 45 day approval', 'Required - Expected 45 day approval'),
    ('Required - Expected 75 day approval', 'Required - Expected 75 day approval'),
    ('Required - Potential Block', 'Required - Potential Block'),
)

EC_REQUIREMENT_CHOICES = (
    ('Not required', 'Not required'),
    ('Required - Expected Phase I', 'Required - Expected Phase I'),
    ('Required - Expected Phase II', 'Required - Expected Phase II'),
    ('Required - Potential Block', 'Required - Potential Block'),
)

ACCC_REQUIREMENT_CHOICES = (
    ('Not required', 'Not required'),
    ('Required - Expected approval < 90 days', 'Required - Expected approval < 90 days'),
    ('Required - Expected approval > 90 days', 'Required - Expected approval > 90 days'),
    ('Required - Potential Block', 'Required - Potential Block'),
)

INVESTMENT_CA_REQUIREMENT_CHOICES = (
    ('Not required', 'Not required'),
    ('Required - Expected approval during initial review', 'Required - Expected approval during initial review'),
    ('Required - Expected approval following extended review', 'Required - Expected approval following extended review'),
    ('Required - Potential Block', 'Required - Potential Block'),
)

CADE_REQUIREMENT_CHOICES = (
    ('Not required', 'Not required'),
    ('Required - Expected approval < 60 days>', 'Required - Expected approval < 60 days>'),
    ('Required - Expected approval < 240 days>', 'Required - Expected approval < 240 days>'),
    ('Required - Expected approval < 330 days>', 'Required - Expected approval < 330 days>'),
    ('Required - Potential Block', 'Required - Potential Block'),
)

COUNTRY_RISK_ONE_CHOICES = (
    ('Germany', 'Germany'),
    ('Japan', 'Japan'),
    ('France', 'France'),
    ('Italy', 'Italy'),
    ('Israel', 'Israel'),
    ('Russia', 'Russia'),
    ('Spain', 'Spain'),
    ('Mexico', 'Mexico'),
    ('Switzerland', 'Switzerland'),
    ('Sweden', 'Sweden'),
    ('Belgium', 'Belgium'),
)

COUNTRY_RISK_TWO_CHOICES = (
    ('N/A', 'N/A'),
    ('Germany', 'Germany'),
    ('Japan', 'Japan'),
    ('France', 'France'),
    ('Italy', 'Italy'),
    ('Israel', 'Israel'),
    ('Russia', 'Russia'),
    ('Spain', 'Spain'),
    ('Mexico', 'Mexico'),
    ('Switzerland', 'Switzerland'),
    ('Sweden', 'Sweden'),
    ('Belgium', 'Belgium')
)

ACQUIRER_SH_VOTE_CHOICES = (
    ('Not Required', 'Not Required'),
    ('Required', 'Required'),
)

TARGET_SH_VOTE_CHOICES = (
    ('50', '50'),
    ('67', '67'),
    ('75', '75'),
    ('90', '90'),
)

ACQUIRER_BECOMES_TARGET_CHOICES = (
    ('Highly Unlikely', 'Highly Unlikely'),
    ('Unlikely', 'Unlikely'),
    ('Neutral', 'Neutral'),
    ('Likely', 'Likely'),
    ('Highly Likely', 'Highly Likely'),
)

POTENTIAL_BIDDING_CHOICES = (
    ('Highly Unlikely', 'Highly Unlikely'),
    ('Unlikely', 'Unlikely'),
    ('Neutral', 'Neutral'),
    ('Likely', 'Likely'),
    ('Highly Likely', 'Highly Likely'),
)

COMMODITY_RISK_CHOICES = (
    ('N/A', 'N/A'),
    ('Energy', 'Energy'),
    ('Metals', 'Metals'),
    ('Grains', 'Grains'),
    ('Other', 'Other'),
)

ESTIMATED_MARKET_SHARE_TARGET_CHOICES = (
    ('N/A', 'N/A'),
    ('0% - 10%', '0% - 10%'),
    ('11% - 20%', '11% - 20%'),
    ('20% - 30%', '20% - 30%'),
    ('30% - 40%', '30% - 40%'),
    ('40%+', '40%+'),
)

ESTIMATED_MARKET_SHARE_ACQUIRER_CHOICES = (
    ('N/A', 'N/A'),
    ('0% - 10%', '0% - 10%'),
    ('11% - 20%', '11% - 20%'),
    ('20% - 30%', '20% - 30%'),
    ('30% - 40%', '30% - 40%'),
    ('40%+', '40%+'),
)

INVERSION_DEAL_CHOICES = (
    ('No', 'No'),
    ('Yes', 'Yes'),
)

FORM_COMPLETE = (
    ('No', 'No'),
    ('Yes', 'Yes'),
)


class MA_Deals_Risk_Factors(models.Model):
    """
    Models for MA Deals Risk Factors
    """
    deal = models.ForeignKey(MA_Deals, on_delete=models.CASCADE)
    definiteness = models.CharField(null=True, blank=True, max_length=100, choices=DEFINITENESS_CHOICES)
    hostile_friendly = models.CharField(null=True, blank=True, max_length=10, choices=HOSTILE_CHOICES)
    strategic_pe = models.CharField(null=True, blank=True, max_length=10, choices=STRATEGIC_CHOICES)
    deal_rationale = models.CharField(null=True, blank=True, max_length=100, choices=DEAL_RATIONALE_CHOICES)
    premium_percentage = models.CharField(null=True, blank=True, max_length=10)
    stock_cash = models.CharField(null=True, blank=True, max_length=100, choices=STOCK_CASH_CHOICES)
    financing_percent_of_deal_value = models.CharField(null=True, blank=True, max_length=10)
    pro_forma_leverage = models.CharField(null=True, blank=True, max_length=50)
    estimated_closing_date = models.DateField(null=True, blank=True)
    go_shop = models.CharField(null=True, blank=True, max_length=5, choices=GO_SHOP_CHOICES)
    divestitures_required = models.CharField(null=True, blank=True, max_length=15, choices=DIVESTITURES_CHOICES)
    termination_fee_for_acquirer = models.FloatField(null=True, blank=True)
    termination_fee_for_target = models.FloatField(null=True, blank=True)
    fair_valuation = models.CharField(null=True, blank=True, max_length=30, choices=FAIR_VALUATION_CHOICES)
    cyclical_industry = models.CharField(null=True, blank=True, max_length=5, choices=CYCLINCAL_INDUSTRY_CHOICES)
    sec_requirement = models.CharField(null=True, blank=True, max_length=50, choices=SEC_REQUIREMENT_CHOICES)
    sec_expected_clearance = models.DateField(null=True, blank=True)
    sec_actual_clearance = models.DateField(null=True, blank=True)
    hsr_requirement = models.CharField(null=True, blank=True, max_length=50, choices=HSR_REQUIREMENT_CHOICES)
    hsr_expected_clearance = models.DateField(null=True, blank=True)
    hsr_actual_clearance = models.DateField(null=True, blank=True)
    mofcom_requirement = models.CharField(null=True, blank=True, max_length=50, choices=MOFCOM_REQUIREMENT_CHOICES)
    mofcom_expected_clearance = models.DateField(null=True, blank=True)
    mofcom_actual_clearance = models.DateField(null=True, blank=True)
    cifius_requirement = models.CharField(null=True, blank=True, max_length=50, choices=CIFIUS_REPLACEMENT_CHOICES)
    cifius_expected_clearance = models.DateField(null=True, blank=True)
    cifius_actual_clearance = models.DateField(null=True, blank=True)
    ec_requirement = models.CharField(null=True, blank=True, max_length=50, choices=EC_REQUIREMENT_CHOICES)
    ec_expected_clearance = models.DateField(null=True, blank=True)
    ec_actual_clearance = models.DateField(null=True, blank=True)
    accc_requirement = models.CharField(null=True, blank=True, max_length=50, choices=ACCC_REQUIREMENT_CHOICES)
    accc_expected_clearance = models.DateField(null=True, blank=True)
    accc_actual_clearance = models.DateField(null=True, blank=True)
    investment_canada_requirement = models.CharField(null=True, blank=True, max_length=50, choices=INVESTMENT_CA_REQUIREMENT_CHOICES)
    investment_canada_expected_clearance = models.DateField(null=True, blank=True)
    investment_canada_actual_clearance = models.DateField(null=True, blank=True)
    cade_requirement = models.CharField(null=True, blank=True, max_length=50, choices=CADE_REQUIREMENT_CHOICES)
    cade_expected_clearance = models.DateField(null=True, blank=True)
    cade_actual_clearance = models.DateField(null=True, blank=True)
    other_country_regulatory_risk_one = models.CharField(null=True, blank=True, max_length=50, choices=COUNTRY_RISK_ONE_CHOICES)
    other_country_regulatory_risk_two = models.CharField(null=True, blank=True, max_length=50, choices=COUNTRY_RISK_TWO_CHOICES)
    acquirer_sh_vote_required = models.CharField(null=True, blank=True, max_length=50, choices=ACQUIRER_SH_VOTE_CHOICES)
    target_sh_vote_required_percentage = models.CharField(null=True, blank=True, max_length=100, choices=TARGET_SH_VOTE_CHOICES)
    acquirer_becomes_target = models.CharField(null=True, blank=True, max_length=50, choices=ACQUIRER_BECOMES_TARGET_CHOICES)
    potential_bidding_war = models.CharField(null=True, blank=True, max_length=50, choices=POTENTIAL_BIDDING_CHOICES)
    commodity_risk = models.CharField(null=True, blank=True, max_length=50, choices=COMMODITY_RISK_CHOICES)
    estimated_market_share_acquirer = models.CharField(null=True, blank=True, max_length=50, choices=ESTIMATED_MARKET_SHARE_ACQUIRER_CHOICES)
    estimated_market_share_target = models.CharField(null=True, blank=True, max_length=50, choices=ESTIMATED_MARKET_SHARE_TARGET_CHOICES)
    is_inversion_deal_or_tax_avoidance = models.CharField(null=True, blank=True, max_length=10, choices=INVERSION_DEAL_CHOICES)
    activists_involved = models.TextField(null=True, blank=True)
    is_form_complete = models.CharField(null=True, blank=True, max_length=5, choices=FORM_COMPLETE)


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
    lawyer_report_date = models.DateField(null=True)
    lawyer_report = models.TextField(null=True)
    analyst_by = models.CharField(max_length=100, null=True)
    title = models.TextField(null=True)


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
    date_updated = models.DateTimeField(null=False) #Updated Record shouldn't be Null


def get_bullfile_path_filename(instance, filename):
    path = "ESS_IDEA_DB_FILES/BULL_THESIS_FILES"
    file_split = filename.split('.')
    ext = file_split[-1]
    filename = file_split[0]
    filename = '{filename}_{uuid}.{ext}'.format(filename=filename, uuid=str(uuid.uuid4()), ext=ext)
    return os.path.join(path, filename)

class ESS_Idea_BullFileUploads(models.Model):
    ess_idea_id = models.ForeignKey('ESS_Idea', on_delete=models.CASCADE)
    deal_key = models.IntegerField(null=True)  # DealKey reflecting a deal
    bull_thesis_model = models.FileField(null=True, upload_to=get_bullfile_path_filename)
    original_filename = models.CharField(default='filename', max_length=100)
    uploaded_at = models.DateField(null=True)

    def filename(self):
        return self.original_filename


def get_ourfile_path_filename(instance, filename):
    path = 'ESS_IDEA_DB_FILES/OUR_THESIS_FILES'
    file_split = filename.split('.')
    ext = file_split[-1]
    filename = file_split[0]
    filename = '{filename}_{uuid}.{ext}'.format(filename=filename, uuid=str(uuid.uuid4()), ext=ext)
    return os.path.join(path, filename)

class ESS_Idea_OurFileUploads(models.Model):
    ess_idea_id = models.ForeignKey('ESS_Idea', on_delete=models.CASCADE)
    deal_key = models.IntegerField(null=True)  # DealKey reflecting a deal
    our_thesis_model = models.FileField(null=True, upload_to=get_ourfile_path_filename)
    original_filename = models.CharField(default='filename', max_length=100)
    uploaded_at = models.DateField(null=True)

    def filename(self):
        return self.original_filename


def get_bearfile_path_filename(instance, filename):
    path = 'ESS_IDEA_DB_FILES/BEAR_THESIS_FILES'
    file_split = filename.split('.')
    ext = file_split[-1]
    filename = file_split[0]
    filename = '{filename}_{uuid}.{ext}'.format(filename=filename, uuid=str(uuid.uuid4()), ext=ext)
    return os.path.join(path, filename)


class ESS_Idea_BearFileUploads(models.Model):
    ess_idea_id = models.ForeignKey('ESS_Idea', on_delete=models.CASCADE)
    deal_key = models.IntegerField(null=True)  # DealKey reflecting a deal
    bear_thesis_model = models.FileField(null=True, upload_to=get_bearfile_path_filename)
    original_filename = models.CharField(default='filename', max_length=100)
    uploaded_at = models.DateField(null=True)

    def filename(self):
        return self.original_filename


class EssIdeaAdjustmentsInformation(models.Model):
    ess_idea_id = models.ForeignKey('ESS_Idea', on_delete=models.CASCADE)
    deal_key = models.IntegerField(null=True)  # DealKey reflecting a deal
    regression_results = models.TextField(null=True)
    regression_calculations = models.TextField(null=True)
    cix_calculations = models.TextField(null=True)
    calculated_on = models.DateField(null=True)


class EssBalanceSheets(models.Model):
    ess_idea_id = models.ForeignKey('ESS_Idea', on_delete=models.CASCADE)
    deal_key = models.IntegerField(null=True)  # DealKey reflecting a deal
    upside_balance_sheet = models.TextField(null=True)  # This field reflects the Upside Balance Sheet Adjustments.
    wic_balance_sheet = models.TextField(null=True)  # This field reflects the WIC Balance Sheet Adjustments.
    downside_balance_sheet = models.TextField(null=True)  # This field reflects the Downside Balance Sheet Adjustments.
    adjust_up_bs_with_bloomberg = models.CharField(default='Yes', max_length=5)  # If No, then Do not add with Bloomberg
    adjust_wic_bs_with_bloomberg = models.CharField(default='Yes', max_length=5)  # If No, then Do not add with Bloomberg
    adjust_down_bs_with_bloomberg = models.CharField(default='Yes', max_length=5)  # If No, then Do not add with Bloomberg


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

    pt_up_check = models.CharField(max_length=10, null=True)
    pt_down_check = models.CharField(max_length=10, null=True)
    pt_wic_check = models.CharField(max_length=10, null=True)
    how_to_adjust = models.CharField(max_length=10, null=True, default='cix')   # CIX or Regression
    premium_format = models.CharField(max_length=10, null=True, default='dollar')  # Dollar or Percentage
    created_on = models.DateTimeField(null=True, default=datetime.datetime.now())


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
