# Generated by Django 2.0.6 on 2018-12-07 11:33

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('risk', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CreditDatabase',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('deal_name', models.CharField(max_length=100, null=True)),
                ('deal_bucket', models.CharField(max_length=100, null=True)),
                ('deal_strategy_type', models.CharField(max_length=100, null=True)),
                ('catalyst', models.CharField(max_length=100, null=True)),
                ('catalyst_tier', models.CharField(max_length=10, null=True)),
                ('target_security_cusip', models.CharField(max_length=100, null=True)),
                ('coupon', models.CharField(max_length=10, null=True)),
                ('hedge_security_cusip', models.CharField(max_length=100, null=True)),
                ('estimated_close_date', models.DateField(null=True)),
                ('upside_price', models.FloatField(null=True)),
                ('downside_price', models.FloatField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='MA_Deals',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('deal_name', models.CharField(max_length=100)),
                ('target_ticker', models.CharField(max_length=50)),
                ('acquirer_ticker', models.CharField(max_length=50)),
                ('target_last_price', models.CharField(default='0', max_length=10)),
                ('analyst', models.CharField(max_length=50)),
                ('created', models.DateField(default=None)),
                ('last_modified', models.DateTimeField(default=None)),
                ('is_complete', models.CharField(default=None, max_length=5)),
                ('deal_cash_terms', models.CharField(default=None, max_length=40)),
                ('deal_share_terms', models.FloatField(default=0)),
                ('status', models.CharField(default=None, max_length=40)),
                ('deal_value', models.CharField(default='0', max_length=10)),
                ('deal_upside', models.FloatField(default=0)),
                ('target_downside', models.FloatField(default=0)),
                ('acquirer_upside', models.FloatField(default=0, null=True)),
                ('fund', models.CharField(default='ARB', max_length=30)),
                ('fund_aum', models.CharField(default='0', max_length=20)),
                ('last_downside_update', models.DateTimeField(null=True)),
                ('catalyst', models.CharField(max_length=10, null=True)),
                ('catalyst_tier', models.CharField(max_length=10, null=True)),
                ('expected_closing_date', models.DateField(null=True)),
                ('target_dividends', models.FloatField(null=True)),
                ('acquirer_dividends', models.FloatField(null=True)),
                ('short_rebate', models.FloatField(null=True)),
                ('stub_cvr_value', models.FloatField(null=True)),
                ('fx_carry_percent', models.CharField(max_length=10, null=True)),
                ('loss_tolerance_percentage_of_limit', models.CharField(max_length=10, null=True)),
                ('unaffected_date', models.TextField(null=True)),
                ('cix_index', models.CharField(max_length=100, null=True)),
                ('cix_index_chart', models.TextField(null=True)),
                ('spread_index', models.CharField(max_length=100, null=True)),
                ('spread_index_chart', models.TextField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='MA_Deals_Lawyer_Reports',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('lawyer_report_date', models.DateField()),
                ('lawyer_report', models.TextField()),
                ('analyst_by', models.CharField(max_length=100)),
                ('analyst_rating', models.CharField(max_length=1)),
                ('deal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='risk.MA_Deals')),
            ],
        ),
        migrations.CreateModel(
            name='MA_Deals_Notes',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('note', models.TextField()),
                ('last_edited', models.DateTimeField()),
                ('deal', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='risk.MA_Deals')),
            ],
        ),
        migrations.CreateModel(
            name='MA_Deals_PeerSet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('peer', models.CharField(max_length=75)),
                ('ev_ebitda_chart_ltm', models.TextField()),
                ('ev_ebitda_chart_1bf', models.TextField()),
                ('ev_ebitda_chart_2bf', models.TextField()),
                ('pe_ratio_chart_ltm', models.TextField()),
                ('pe_ratio_chart_1bf', models.TextField()),
                ('pe_ratio_chart_2bf', models.TextField()),
                ('fcf_yield_chart', models.TextField()),
                ('deal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='risk.MA_Deals')),
            ],
        ),
        migrations.CreateModel(
            name='MA_Deals_Scenario_Analysis',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('break_scenario_df', models.TextField()),
                ('scenario_75_25', models.TextField()),
                ('scenario_change', models.FloatField()),
                ('break_change', models.FloatField()),
                ('scenario_change_55_45', models.FloatField()),
                ('scenario_55_45', models.TextField()),
                ('deal', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='risk.MA_Deals')),
            ],
        ),
        migrations.CreateModel(
            name='MA_Deals_WeeklyDownsideEstimates',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('week_no', models.IntegerField()),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('estimate', models.CharField(default='Not Entered', max_length=25)),
                ('comment', models.TextField(default='No Comment Entered')),
                ('analyst', models.CharField(max_length=100, null=True)),
                ('date_updated', models.DateField(null=True)),
                ('deal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='risk.MA_Deals')),
            ],
        ),
    ]
