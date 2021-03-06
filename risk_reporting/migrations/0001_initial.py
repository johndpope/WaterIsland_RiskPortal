# Generated by Django 2.0.13 on 2019-04-05 16:44

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ArbNAVImpacts',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('TradeDate', models.DateField()),
                ('FundCode', models.CharField(max_length=10)),
                ('TradeGroup', models.CharField(max_length=100)),
                ('Sleeve', models.CharField(max_length=100)),
                ('Bucket', models.CharField(max_length=100)),
                ('Underlying', models.CharField(max_length=100)),
                ('Ticker', models.CharField(max_length=100)),
                ('BloombergGlobalId', models.CharField(max_length=100, null=True)),
                ('SecType', models.CharField(max_length=10, null=True)),
                ('MarketCapCategory', models.CharField(max_length=100, null=True)),
                ('DealTermsCash', models.FloatField(null=True)),
                ('DealTermsStock', models.FloatField(null=True)),
                ('DealValue', models.FloatField(null=True)),
                ('DealClosingDate', models.DateField(null=True)),
                ('AlphaHedge', models.CharField(max_length=50)),
                ('NetMktVal', models.FloatField()),
                ('FxFactor', models.FloatField(null=True)),
                ('Capital', models.FloatField(null=True)),
                ('BaseCaseNavImpact', models.FloatField(null=True)),
                ('OutlierNavImpact', models.FloatField(null=True)),
                ('QTY', models.FloatField()),
                ('LongShort', models.CharField(max_length=20)),
                ('CatalystRating', models.FloatField(null=True)),
                ('NAV', models.FloatField(null=True)),
                ('Analyst', models.CharField(max_length=100, null=True)),
                ('PM_BASE_CASE', models.FloatField(null=True)),
                ('Outlier', models.FloatField(null=True)),
                ('StrikePrice', models.FloatField(null=True)),
                ('PutCall', models.CharField(max_length=20, null=True)),
                ('LastPrice', models.FloatField(null=True)),
                ('CurrMktVal', models.FloatField(null=True)),
                ('RiskLimit', models.FloatField()),
                ('PL_BASE_CASE', models.FloatField(null=True)),
                ('BASE_CASE_NAV_IMPACT', models.FloatField(null=True)),
                ('OUTLIER_PL', models.FloatField(null=True)),
                ('OUTLIER_NAV_IMPACT', models.FloatField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='DailyNAVImpacts',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('TradeGroup', models.CharField(max_length=100)),
                ('RiskLimit', models.FloatField()),
                ('LastUpdate', models.DateField(null=True)),
                ('BASE_CASE_NAV_IMPACT_AED', models.CharField(max_length=100)),
                ('BASE_CASE_NAV_IMPACT_ARB', models.CharField(max_length=100)),
                ('BASE_CASE_NAV_IMPACT_CAM', models.CharField(max_length=100)),
                ('BASE_CASE_NAV_IMPACT_LEV', models.CharField(max_length=100)),
                ('BASE_CASE_NAV_IMPACT_LG', models.CharField(max_length=100)),
                ('BASE_CASE_NAV_IMPACT_MACO', models.CharField(max_length=100)),
                ('BASE_CASE_NAV_IMPACT_TAQ', models.CharField(max_length=100)),
                ('BASE_CASE_NAV_IMPACT_WED', models.CharField(max_length=100, null=True)),
                ('BASE_CASE_NAV_IMPACT_WIC', models.CharField(max_length=100, null=True)),
                ('BASE_CASE_NAV_IMPACT_MALT', models.CharField(max_length=100, null=True)),
                ('OUTLIER_NAV_IMPACT_AED', models.CharField(max_length=100)),
                ('OUTLIER_NAV_IMPACT_ARB', models.CharField(max_length=100)),
                ('OUTLIER_NAV_IMPACT_CAM', models.CharField(max_length=100)),
                ('OUTLIER_NAV_IMPACT_LEV', models.CharField(max_length=100)),
                ('OUTLIER_NAV_IMPACT_LG', models.CharField(max_length=100)),
                ('OUTLIER_NAV_IMPACT_MACO', models.CharField(max_length=100)),
                ('OUTLIER_NAV_IMPACT_TAQ', models.CharField(max_length=100)),
                ('OUTLIER_NAV_IMPACT_WED', models.CharField(max_length=100, null=True)),
                ('OUTLIER_NAV_IMPACT_WIC', models.CharField(max_length=100, null=True)),
                ('OUTLIER_NAV_IMPACT_MALT', models.CharField(max_length=100, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='FormulaeBasedDownsides',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False, unique=True)),
                ('TradeGroup', models.CharField(max_length=100, null=True)),
                ('Underlying', models.CharField(max_length=100, null=True)),
                ('DealValue', models.FloatField(null=True)),
                ('TargetAcquirer', models.CharField(max_length=14, null=True)),
                ('Analyst', models.CharField(max_length=20, null=True)),
                ('OriginationDate', models.DateField(null=True)),
                ('LastUpdate', models.DateField(null=True)),
                ('LastPrice', models.FloatField(null=True)),
                ('IsExcluded', models.CharField(default='No', max_length=22)),
                ('RiskLimit', models.FloatField(null=True)),
                ('BaseCaseDownsideType', models.CharField(max_length=50, null=True)),
                ('BaseCaseReferenceDataPoint', models.CharField(max_length=50, null=True)),
                ('BaseCaseReferencePrice', models.CharField(max_length=50, null=True)),
                ('BaseCaseOperation', models.CharField(max_length=5, null=True)),
                ('BaseCaseCustomInput', models.CharField(max_length=50, null=True)),
                ('base_case', models.CharField(max_length=50, null=True)),
                ('base_case_notes', models.TextField(null=True)),
                ('cix_ticker', models.CharField(max_length=50, null=True)),
                ('OutlierDownsideType', models.CharField(max_length=50, null=True)),
                ('OutlierReferenceDataPoint', models.CharField(max_length=50, null=True)),
                ('OutlierReferencePrice', models.CharField(max_length=50, null=True)),
                ('OutlierOperation', models.CharField(max_length=5, null=True)),
                ('OutlierCustomInput', models.CharField(max_length=50, null=True)),
                ('outlier', models.CharField(max_length=50, null=True)),
                ('outlier_notes', models.TextField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='PositionLevelNAVImpacts',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('TradeGroup', models.CharField(max_length=300)),
                ('Ticker', models.CharField(max_length=200)),
                ('PM_BASE_CASE', models.FloatField(null=True)),
                ('Outlier', models.FloatField(null=True)),
                ('LastPrice', models.FloatField(null=True)),
                ('BASE_CASE_NAV_IMPACT_AED', models.FloatField(null=True)),
                ('BASE_CASE_NAV_IMPACT_ARB', models.FloatField(null=True)),
                ('BASE_CASE_NAV_IMPACT_CAM', models.FloatField(null=True)),
                ('BASE_CASE_NAV_IMPACT_LEV', models.FloatField(null=True)),
                ('BASE_CASE_NAV_IMPACT_LG', models.FloatField(null=True)),
                ('BASE_CASE_NAV_IMPACT_MACO', models.FloatField(null=True)),
                ('BASE_CASE_NAV_IMPACT_MALT', models.FloatField(null=True)),
                ('BASE_CASE_NAV_IMPACT_TAQ', models.FloatField(null=True)),
                ('OUTLIER_NAV_IMPACT_AED', models.FloatField(null=True)),
                ('OUTLIER_NAV_IMPACT_ARB', models.FloatField(null=True)),
                ('OUTLIER_NAV_IMPACT_CAM', models.FloatField(null=True)),
                ('OUTLIER_NAV_IMPACT_LEV', models.FloatField(null=True)),
                ('OUTLIER_NAV_IMPACT_LG', models.FloatField(null=True)),
                ('OUTLIER_NAV_IMPACT_MACO', models.FloatField(null=True)),
                ('OUTLIER_NAV_IMPACT_MALT', models.FloatField(null=True)),
                ('OUTLIER_NAV_IMPACT_TAQ', models.FloatField(null=True)),
                ('CALCULATED_ON', models.DateTimeField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='RiskAttributes',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('strategy', models.CharField(max_length=50)),
                ('underlying_ticker', models.CharField(max_length=30)),
                ('target_acquirer', models.CharField(max_length=8)),
                ('risk_limit', models.CharField(max_length=10, null=True)),
                ('currency', models.CharField(max_length=6)),
                ('underlying_current_price', models.FloatField(default=0)),
                ('downside_base_case', models.FloatField()),
                ('downside_outlier', models.FloatField()),
                ('analyst', models.CharField(max_length=10)),
                ('last_update_date', models.DateTimeField(default='1900-01-01', null=True)),
                ('notes', models.TextField(null=True)),
            ],
        ),
    ]
