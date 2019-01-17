# Generated by Django 2.0.6 on 2018-12-07 11:31

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ESS_Idea',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('alpha_ticker', models.CharField(max_length=30)),
                ('price', models.FloatField()),
                ('pt_up', models.FloatField()),
                ('pt_wic', models.FloatField()),
                ('pt_down', models.FloatField()),
                ('unaffected_date', models.DateField()),
                ('expected_close', models.DateField()),
                ('gross_percentage', models.CharField(max_length=20)),
                ('ann_percentage', models.CharField(max_length=20)),
                ('hedged_volatility', models.CharField(max_length=20)),
                ('theoretical_sharpe', models.CharField(max_length=20)),
                ('implied_probability', models.CharField(max_length=20)),
                ('event_premium', models.CharField(max_length=20)),
                ('situation_overview', models.TextField()),
                ('company_overview', models.TextField()),
                ('bull_thesis', models.TextField()),
                ('our_thesis', models.TextField()),
                ('bear_thesis', models.TextField()),
                ('bull_thesis_model', models.FileField(upload_to='ESS_IDEA_MODELS/BULL_THESIS/%Y%m%d')),
                ('our_thesis_model', models.FileField(upload_to='ESS_IDEA_MODELS/OUR_THESIS/%Y%m%d')),
                ('bear_thesis_model', models.FileField(upload_to='ESS_IDEA_MODELS/BEAR_THESIS/%Y%m%d')),
                ('m_value', models.IntegerField(default=0)),
                ('o_value', models.IntegerField(default=0)),
                ('s_value', models.IntegerField(default=0)),
                ('a_value', models.IntegerField(default=0)),
                ('i_value', models.IntegerField(default=0)),
                ('c_value', models.IntegerField(default=0)),
                ('m_overview', models.TextField(default='N/A')),
                ('o_overview', models.TextField(default='N/A')),
                ('s_overview', models.TextField(default='N/A')),
                ('a_overview', models.TextField(default='N/A')),
                ('i_overview', models.TextField(default='N/A')),
                ('c_overview', models.TextField(default='N/A')),
                ('alpha_chart', models.TextField()),
                ('hedge_chart', models.TextField()),
                ('market_neutral_chart', models.TextField()),
                ('implied_probability_chart', models.TextField()),
                ('event_premium_chart', models.TextField()),
                ('valuator_multiple_chart', models.TextField()),
                ('ev_ebitda_chart_1bf', models.TextField()),
                ('ev_ebitda_chart_2bf', models.TextField()),
                ('ev_ebitda_chart_ltm', models.TextField()),
                ('ev_sales_chart_1bf', models.TextField()),
                ('ev_sales_chart_2bf', models.TextField()),
                ('ev_sales_chart_ltm', models.TextField()),
                ('p_eps_chart_1bf', models.TextField()),
                ('p_eps_chart_2bf', models.TextField()),
                ('p_eps_chart_ltm', models.TextField()),
                ('fcf_yield_chart', models.TextField()),
                ('price_target_date', models.DateField()),
                ('multiples_dictionary', models.TextField()),
                ('cix_index', models.CharField(max_length=100, null=True)),
                ('category', models.CharField(max_length=100, null=True)),
                ('catalyst', models.CharField(max_length=5, null=True)),
                ('deal_type', models.CharField(max_length=100, null=True)),
                ('catalyst_tier', models.CharField(max_length=5, null=True)),
                ('gics_sector', models.CharField(max_length=100, null=True)),
                ('hedges', models.CharField(max_length=5, null=True)),
                ('needs_downside_attention', models.IntegerField(null=True)),
                ('status', models.CharField(default='Backlogged', max_length=100, null=True)),
                ('lead_analyst', models.CharField(default='Unallocated', max_length=100, null=True)),
                ('version_number', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='ESS_Peers',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('version_number', models.IntegerField(default=-1)),
                ('ticker', models.CharField(max_length=30)),
                ('hedge_weight', models.FloatField()),
                ('ev_ebitda_chart_ltm', models.TextField()),
                ('ev_ebitda_chart_1bf', models.TextField()),
                ('ev_ebitda_chart_2bf', models.TextField()),
                ('ev_sales_chart_ltm', models.TextField()),
                ('ev_sales_chart_1bf', models.TextField()),
                ('ev_sales_chart_2bf', models.TextField()),
                ('p_eps_chart_ltm', models.TextField()),
                ('p_eps_chart_1bf', models.TextField()),
                ('p_eps_chart_2bf', models.TextField()),
                ('p_fcf_chart', models.TextField()),
                ('name', models.CharField(default='Unknown', max_length=150)),
                ('enterprise_value', models.TextField(default='N/A')),
                ('market_cap', models.TextField(default='N/A')),
                ('ev_ebitda_bf1', models.TextField(default='N/A')),
                ('ev_ebitda_bf2', models.TextField(default='N/A')),
                ('ev_sales_bf1', models.TextField(default='N/A')),
                ('ev_sales_bf2', models.TextField(default='N/A')),
                ('p_e_bf1', models.TextField(default='N/A')),
                ('p_e_bf2', models.TextField(default='N/A')),
                ('fcf_yield_bf1', models.TextField(default='N/A')),
                ('fcf_yield_bf2', models.TextField(default='N/A')),
            ],
        ),
        migrations.AddField(
            model_name='ess_idea',
            name='peers',
            field=models.ManyToManyField(to='risk.ESS_Peers'),
        ),
        migrations.AlterUniqueTogether(
            name='ess_idea',
            unique_together={('id', 'version_number')},
        ),
    ]
