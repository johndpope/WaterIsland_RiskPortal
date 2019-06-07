import os
from django.db import models

# Create your models here.

class RiskAttributes(models.Model):
    strategy = models.CharField(max_length=50) # Denotes the Tradegroup
    underlying_ticker = models.CharField(max_length=30) #Underlying deal ticker
    target_acquirer = models.CharField(max_length=8) #denotes whether current is target/acquirer if position is hedged
    risk_limit = models.CharField(max_length=10, null=True) # Risk limit for the Deal
    currency = models.CharField(max_length=6) #Curreny notation (eg USD)
    underlying_current_price = models.FloatField(default=0) #Live price of the underlying ticker
    downside_base_case = models.FloatField()
    downside_outlier = models.FloatField()
    analyst = models.CharField(max_length=10) #Allocated analyst
    last_update_date = models.DateTimeField(default='1900-01-01', null=True) #Datetime stamp of the last downside update
    notes = models.TextField(null=True) #Specific notes for each Tradegroup by analyst

class ArbNAVImpacts(models.Model):
    ''' This model is to be updated via a scheduled Celery Job every 15 mins from Market open to close..'''
    TradeDate = models.DateField()
    FundCode = models.CharField(max_length=10)
    TradeGroup = models.CharField(max_length=100)
    Sleeve = models.CharField(max_length=100)
    Bucket = models.CharField(max_length=100)
    Underlying = models.CharField(max_length=100)
    Ticker = models.CharField(max_length=100)
    BloombergGlobalId = models.CharField(max_length=100, null=True)
    SecType = models.CharField(max_length=10, null=True)
    MarketCapCategory = models.CharField(max_length=100, null=True)
    DealTermsCash = models.FloatField(null=True)
    DealTermsStock = models.FloatField(null=True)
    DealValue = models.FloatField(null=True)
    DealClosingDate = models.DateField(null=True)
    AlphaHedge = models.CharField(max_length=50)
    NetMktVal = models.FloatField()
    FxFactor = models.FloatField(null=True)
    Capital  = models.FloatField(null=True)
    BaseCaseNavImpact = models.FloatField(null=True)
    OutlierNavImpact = models.FloatField(null=True)
    QTY = models.FloatField()
    LongShort = models.CharField(max_length=20)
    CatalystRating = models.FloatField(null=True)
    NAV = models.FloatField(null=True)
    Analyst = models.CharField(max_length=100, null=True)
    PM_BASE_CASE = models.FloatField(null=True)
    Outlier = models.FloatField(null=True)
    StrikePrice = models.FloatField(null=True)
    PutCall = models.CharField(max_length=20, null=True)
    LastPrice = models.FloatField(null=True)
    CurrMktVal = models.FloatField(null=True)
    RiskLimit = models.FloatField()
    PL_BASE_CASE = models.FloatField(null=True)
    BASE_CASE_NAV_IMPACT = models.FloatField(null=True)
    OUTLIER_PL = models.FloatField(null=True)
    OUTLIER_NAV_IMPACT = models.FloatField(null=True)


class DailyNAVImpacts(models.Model):
    ''' Model to Store latest NAV Impacts for each TradeGroup '''
    TradeGroup = models.CharField(max_length=100)
    RiskLimit = models.FloatField()
    LastUpdate = models.DateField(null=True) # Reflects the date on which the underlying formula was updated
    BASE_CASE_NAV_IMPACT_AED = models.CharField(max_length=100)
    BASE_CASE_NAV_IMPACT_ARB = models.CharField(max_length=100)
    BASE_CASE_NAV_IMPACT_CAM = models.CharField(max_length=100)
    BASE_CASE_NAV_IMPACT_LEV = models.CharField(max_length=100)
    BASE_CASE_NAV_IMPACT_LG = models.CharField(max_length=100)
    BASE_CASE_NAV_IMPACT_MACO = models.CharField(max_length=100)
    BASE_CASE_NAV_IMPACT_TAQ = models.CharField(max_length=100)
    BASE_CASE_NAV_IMPACT_WED = models.CharField(max_length=100, null=True)
    BASE_CASE_NAV_IMPACT_WIC = models.CharField(max_length=100, null=True)
    BASE_CASE_NAV_IMPACT_MALT = models.CharField(max_length=100, null=True)
    OUTLIER_NAV_IMPACT_AED = models.CharField(max_length=100)
    OUTLIER_NAV_IMPACT_ARB = models.CharField(max_length=100)
    OUTLIER_NAV_IMPACT_CAM = models.CharField(max_length=100)
    OUTLIER_NAV_IMPACT_LEV = models.CharField(max_length=100)
    OUTLIER_NAV_IMPACT_LG = models.CharField(max_length=100)
    OUTLIER_NAV_IMPACT_MACO = models.CharField(max_length=100)
    OUTLIER_NAV_IMPACT_TAQ = models.CharField(max_length=100)
    OUTLIER_NAV_IMPACT_WED = models.CharField(max_length=100, null=True)
    OUTLIER_NAV_IMPACT_WIC = models.CharField(max_length=100, null=True)
    OUTLIER_NAV_IMPACT_MALT = models.CharField(max_length=100, null=True)

class FormulaeBasedDownsides(models.Model):
    id = models.IntegerField(primary_key=True,unique=True)
    TradeGroup = models.CharField(max_length=100, null=True)
    Underlying = models.CharField(max_length=100, null=True)
    DealValue = models.FloatField(null=True)
    TargetAcquirer = models.CharField(max_length=14, null=True)
    Analyst = models.CharField(max_length=20, null=True)
    OriginationDate = models.DateField(null=True)
    LastUpdate = models.DateField(null=True)
    LastPrice = models.FloatField(null=True)
    IsExcluded = models.CharField(max_length=22, default='No') #Denote by Yes/No
    RiskLimit = models.FloatField(null=True)
    BaseCaseDownsideType = models.CharField(max_length=50, null=True) #Store the downside type
    BaseCaseReferenceDataPoint = models.CharField(max_length=50, null=True) #Based on Downside Type
    BaseCaseReferencePrice = models.CharField(max_length=50, null=True) #Based on Downside Type
    BaseCaseOperation = models.CharField(max_length=5, null=True) # +,-,*,/
    BaseCaseCustomInput = models.CharField(max_length=50, null=True)
    base_case = models.CharField(max_length=50, null=True) #Based on Downside Type
    base_case_notes = models.TextField(null=True)
    cix_ticker = models.CharField(max_length=50, null=True)
    OutlierDownsideType = models.CharField(max_length=50, null=True)  # Store the downside type
    OutlierReferenceDataPoint = models.CharField(max_length=50, null=True)  # Based on Downside Type
    OutlierReferencePrice = models.CharField(max_length=50, null=True)  # Based on Downside Type
    OutlierOperation = models.CharField(max_length=5, null=True)  # +,-,*,/
    OutlierCustomInput = models.CharField(max_length=50, null=True)
    outlier = models.CharField(max_length=50, null=True)  # Based on Downside Type
    outlier_notes = models.TextField(null=True)


class CreditDealsUpsideDownside(models.Model):
    id = models.IntegerField(primary_key=True,unique=True)
    tradegroup = models.CharField(max_length=100, null=True)
    ticker = models.CharField(max_length=100, null=True)
    analyst = models.CharField(max_length=20, null=True)
    origination_date = models.DateField(null=True)
    last_update = models.DateField(null=True)
    spread_index = models.CharField(max_length=50, null=True)
    deal_value = models.FloatField(null=True, blank=True)
    last_price = models.FloatField(null=True, blank=True)
    is_excluded = models.CharField(max_length=22, default='No')
    risk_limit = models.FloatField(null=True, blank=True)
    downside_type = models.CharField(max_length=50, null=True)
    downside = models.CharField(max_length=50, null=True, blank=True)
    downside_notes = models.TextField(null=True)
    upside_type = models.CharField(max_length=50, null=True)
    upside = models.CharField(max_length=50, null=True, blank=True)
    upside_notes = models.TextField(null=True)


class PositionLevelNAVImpacts(models.Model):
    TradeGroup = models.CharField(max_length=300)
    Ticker = models.CharField(max_length=200)
    PM_BASE_CASE = models.FloatField(null=True)
    Outlier = models.FloatField(null=True)
    LastPrice = models.FloatField(null=True)
    BASE_CASE_NAV_IMPACT_AED = models.FloatField(null=True)
    BASE_CASE_NAV_IMPACT_ARB = models.FloatField(null=True)
    BASE_CASE_NAV_IMPACT_CAM = models.FloatField(null=True)
    BASE_CASE_NAV_IMPACT_LEV = models.FloatField(null=True)
    BASE_CASE_NAV_IMPACT_LG = models.FloatField(null=True)
    BASE_CASE_NAV_IMPACT_MACO = models.FloatField(null=True)
    BASE_CASE_NAV_IMPACT_MALT = models.FloatField(null=True)
    BASE_CASE_NAV_IMPACT_TAQ = models.FloatField(null=True)
    OUTLIER_NAV_IMPACT_AED = models.FloatField(null=True)
    OUTLIER_NAV_IMPACT_ARB = models.FloatField(null=True)
    OUTLIER_NAV_IMPACT_CAM = models.FloatField(null=True)
    OUTLIER_NAV_IMPACT_LEV = models.FloatField(null=True)
    OUTLIER_NAV_IMPACT_LG = models.FloatField(null=True)
    OUTLIER_NAV_IMPACT_MACO = models.FloatField(null=True)
    OUTLIER_NAV_IMPACT_MALT = models.FloatField(null=True)
    OUTLIER_NAV_IMPACT_TAQ = models.FloatField(null=True)
    CALCULATED_ON = models.DateTimeField(null=True)
