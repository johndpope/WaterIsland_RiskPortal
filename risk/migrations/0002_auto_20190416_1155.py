# Generated by Django 2.0.13 on 2019-04-16 11:55

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('risk', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ma_deals_risk_factors',
            name='is_iversion_deal_or_tax_avoidance',
        ),
        migrations.AddField(
            model_name='ma_deals_risk_factors',
            name='is_inversion_deal_or_tax_avoidance',
            field=models.CharField(blank=True, choices=[('No', 'No'), ('Yes', 'Yes')], max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='ess_idea',
            name='created_on',
            field=models.DateTimeField(default=datetime.datetime(2019, 4, 16, 11, 55, 39, 60573), null=True),
        ),
        migrations.AlterField(
            model_name='ma_deals_risk_factors',
            name='accc_actual_clearance',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='ma_deals_risk_factors',
            name='accc_expected_clearance',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='ma_deals_risk_factors',
            name='accc_requirement',
            field=models.CharField(blank=True, choices=[('Not required', 'Not required'), ('Required - Expected approval < 90 days', 'Required - Expected approval < 90 days'), ('Required - Expected approval > 90 days', 'Required - Expected approval > 90 days'), ('Required - Potential Block', 'Required - Potential Block')], max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='ma_deals_risk_factors',
            name='acquirer_becomes_target',
            field=models.CharField(blank=True, choices=[('Highly Unlikely', 'Highly Unlikely'), ('Unlikely', 'Unlikely'), ('Neutral', 'Neutral'), ('Likely', 'Likely'), ('Highly Likely', 'Highly Likely')], max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='ma_deals_risk_factors',
            name='acquirer_sh_vote_required',
            field=models.CharField(blank=True, choices=[('Not Required', 'Not Required'), ('Required', 'Required')], max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='ma_deals_risk_factors',
            name='activists_involved',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='ma_deals_risk_factors',
            name='cade_actual_clearance',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='ma_deals_risk_factors',
            name='cade_expected_clearance',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='ma_deals_risk_factors',
            name='cade_requirement',
            field=models.CharField(blank=True, choices=[('Not required', 'Not required'), ('Required - Expected approval < 60 days>', 'Required - Expected approval < 60 days>'), ('Required - Expected approval < 240 days>', 'Required - Expected approval < 240 days>'), ('Required - Expected approval < 330 days>', 'Required - Expected approval < 330 days>'), ('Required - Potential Block', 'Required - Potential Block')], max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='ma_deals_risk_factors',
            name='cifius_actual_clearance',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='ma_deals_risk_factors',
            name='cifius_expected_clearance',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='ma_deals_risk_factors',
            name='cifius_requirement',
            field=models.CharField(blank=True, choices=[('Not required', 'Not required'), ('Required - Expected 45 day approval', 'Required - Expected 45 day approval'), ('Required - Expected 75 day approval', 'Required - Expected 75 day approval'), ('Required - Potential Block', 'Required - Potential Block')], max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='ma_deals_risk_factors',
            name='commodity_risk',
            field=models.CharField(blank=True, choices=[('N/A', 'N/A'), ('Energy', 'Energy'), ('Metals', 'Metals'), ('Grains', 'Grains'), ('Other', 'Other')], max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='ma_deals_risk_factors',
            name='cyclical_industry',
            field=models.CharField(blank=True, choices=[('No', 'No'), ('Yes', 'Yes')], max_length=5, null=True),
        ),
        migrations.AlterField(
            model_name='ma_deals_risk_factors',
            name='deal_rationale',
            field=models.CharField(blank=True, choices=[('One of a kind asset', 'One of a kind asset'), ('Synergy', 'Synergy'), ('Market Share', 'Market Share'), ('Economy of Scale', 'Economy of Scale'), ('Taxation', 'Taxation'), ('Diversification', 'Diversification'), ('Vertical Integration', 'Vertical Integration')], max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='ma_deals_risk_factors',
            name='definiteness',
            field=models.CharField(blank=True, choices=[('Definitive Agreement', 'Definitive Agreement'), ('Agreement in Principle', 'Agreement in Principle')], max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='ma_deals_risk_factors',
            name='divestitures_required',
            field=models.CharField(blank=True, choices=[('Not Required', 'Not Required'), ('required', 'required')], max_length=15, null=True),
        ),
        migrations.AlterField(
            model_name='ma_deals_risk_factors',
            name='ec_actual_clearance',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='ma_deals_risk_factors',
            name='ec_expected_clearance',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='ma_deals_risk_factors',
            name='ec_requirement',
            field=models.CharField(blank=True, choices=[('Not required', 'Not required'), ('Required - Expected Phase I', 'Required - Expected Phase I'), ('Required - Expected Phase II', 'Required - Expected Phase II'), ('Required - Potential Block', 'Required - Potential Block')], max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='ma_deals_risk_factors',
            name='estimated_closing_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='ma_deals_risk_factors',
            name='estimated_market_share_acquirer',
            field=models.CharField(blank=True, choices=[('N/A', 'N/A'), ('0% - 10%', '0% - 10%'), ('11% - 20%', '11% - 20%'), ('20% - 30%', '20% - 30%'), ('30% - 40%', '30% - 40%'), ('40%+', '40%+')], max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='ma_deals_risk_factors',
            name='estimated_market_share_target',
            field=models.CharField(blank=True, choices=[('N/A', 'N/A'), ('0% - 10%', '0% - 10%'), ('11% - 20%', '11% - 20%'), ('20% - 30%', '20% - 30%'), ('30% - 40%', '30% - 40%'), ('40%+', '40%+')], max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='ma_deals_risk_factors',
            name='fair_valuation',
            field=models.CharField(blank=True, choices=[('N/A', 'N/A'), ('Fair', 'Fair'), ('Overvalued', 'Overvalued'), ('Undervalued', 'Undervalued')], max_length=30, null=True),
        ),
        migrations.AlterField(
            model_name='ma_deals_risk_factors',
            name='financing_percent_of_deal_value',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='ma_deals_risk_factors',
            name='go_shop',
            field=models.CharField(blank=True, choices=[('No', 'No'), ('Yes', 'Yes')], max_length=5, null=True),
        ),
        migrations.AlterField(
            model_name='ma_deals_risk_factors',
            name='hostile_friendly',
            field=models.CharField(blank=True, choices=[('Hostile', 'Hostile'), ('Friendly', 'Friendly')], max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='ma_deals_risk_factors',
            name='hsr_actual_clearance',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='ma_deals_risk_factors',
            name='hsr_expected_clearance',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='ma_deals_risk_factors',
            name='hsr_requirement',
            field=models.CharField(blank=True, choices=[('Not required', 'Not required'), ('Required - Expected Phase I', 'Required - Expected Phase I'), ('Required - Expected Phase II', 'Required - Expected Phase II'), ('Required - Potential Block', 'Required - Potential Block')], max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='ma_deals_risk_factors',
            name='investment_canada_actual_clearance',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='ma_deals_risk_factors',
            name='investment_canada_expected_clearance',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='ma_deals_risk_factors',
            name='investment_canada_requirement',
            field=models.CharField(blank=True, choices=[('Not required', 'Not required'), ('Required - Expected approval during initial review', 'Required - Expected approval during initial review'), ('Required - Expected approval following extended review', 'Required - Expected approval following extended review'), ('Required - Potential Block', 'Required - Potential Block')], max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='ma_deals_risk_factors',
            name='is_form_complete',
            field=models.CharField(blank=True, choices=[('No', 'No'), ('Yes', 'Yes')], max_length=5, null=True),
        ),
        migrations.AlterField(
            model_name='ma_deals_risk_factors',
            name='mofcom_actual_clearance',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='ma_deals_risk_factors',
            name='mofcom_expected_clearance',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='ma_deals_risk_factors',
            name='mofcom_requirement',
            field=models.CharField(blank=True, choices=[('Not required', 'Not required'), ('Required - Expected Phase I', 'Required - Expected Phase I'), ('Required - Expected Phase II', 'Required - Expected Phase II'), ('Required - Expected Phase III', 'Required - Expected Phase III'), ('Required - Potential Block', 'Required - Potential Block')], max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='ma_deals_risk_factors',
            name='other_country_regulatory_risk_one',
            field=models.CharField(blank=True, choices=[('Germany', 'Germany'), ('Japan', 'Japan'), ('France', 'France'), ('Italy', 'Italy'), ('Israel', 'Israel'), ('Russia', 'Russia'), ('Spain', 'Spain'), ('Mexico', 'Mexico'), ('Switzerland', 'Switzerland'), ('Sweden', 'Sweden'), ('Belgium', 'Belgium')], max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='ma_deals_risk_factors',
            name='other_country_regulatory_risk_two',
            field=models.CharField(blank=True, choices=[('N/A', 'N/A'), ('Germany', 'Germany'), ('Japan', 'Japan'), ('France', 'France'), ('Italy', 'Italy'), ('Israel', 'Israel'), ('Russia', 'Russia'), ('Spain', 'Spain'), ('Mexico', 'Mexico'), ('Switzerland', 'Switzerland'), ('Sweden', 'Sweden'), ('Belgium', 'Belgium')], max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='ma_deals_risk_factors',
            name='potential_bidding_war',
            field=models.CharField(blank=True, choices=[('Highly Unlikely', 'Highly Unlikely'), ('Unlikely', 'Unlikely'), ('Neutral', 'Neutral'), ('Likely', 'Likely'), ('Highly Likely', 'Highly Likely')], max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='ma_deals_risk_factors',
            name='premium_percentage',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='ma_deals_risk_factors',
            name='pro_forma_leverage',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='ma_deals_risk_factors',
            name='sec_actual_clearance',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='ma_deals_risk_factors',
            name='sec_expected_clearance',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='ma_deals_risk_factors',
            name='sec_requirement',
            field=models.CharField(blank=True, choices=[('Not required', 'Not required'), ('Required - Proxy Review', 'Required - Proxy Review'), ('Required - S4 for US Buyer', 'Required - S4 for US Buyer'), ('Required - S4 for Foreign Buyer', 'Required - S4 for Foreign Buyer')], max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='ma_deals_risk_factors',
            name='stock_cash',
            field=models.CharField(blank=True, choices=[('Cash Tender', 'Cash Tender'), ('Stock Exchange', 'Stock Exchange'), ('Scheme of an Arrangement', 'Scheme of an Arrangement'), ('Merger all Cash', 'Merger all Cash'), ('Merger with Stock Portion', 'Merger with Stock Portion')], max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='ma_deals_risk_factors',
            name='strategic_pe',
            field=models.CharField(blank=True, choices=[('Strategic', 'Strategic'), ('PE', 'PE')], max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='ma_deals_risk_factors',
            name='target_sh_vote_required_percentage',
            field=models.CharField(blank=True, choices=[('50', '50'), ('67', '67'), ('75', '75'), ('90', '90')], max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='ma_deals_risk_factors',
            name='termination_fee_for_acquirer',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='ma_deals_risk_factors',
            name='termination_fee_for_target',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
