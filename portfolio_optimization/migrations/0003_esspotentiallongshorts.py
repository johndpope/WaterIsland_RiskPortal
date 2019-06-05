# Generated by Django 2.0.10 on 2019-06-04 16:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portfolio_optimization', '0002_normalizedsizingbyriskadjprob_softcatalystnormalizedrisksizing'),
    ]

    operations = [
        migrations.CreateModel(
            name='EssPotentialLongShorts',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('alpha_ticker', models.CharField(max_length=100)),
                ('price', models.FloatField(null=True)),
                ('pt_up', models.FloatField(null=True)),
                ('pt_wic', models.FloatField(null=True)),
                ('pt_down', models.FloatField(null=True)),
                ('unaffected_date', models.DateField(null=True)),
                ('expected_close', models.DateField(null=True)),
                ('price_target_date', models.DateField(null=True)),
                ('cix_index', models.CharField(max_length=50, null=True)),
                ('category', models.CharField(max_length=100, null=True)),
                ('catalyst', models.CharField(max_length=50, null=True)),
                ('deal_type', models.CharField(max_length=50, null=True)),
                ('catalyst_tier', models.CharField(max_length=10, null=True)),
                ('gics_sector', models.CharField(max_length=100, null=True)),
                ('hedges', models.CharField(max_length=10, null=True)),
                ('lead_analyst', models.CharField(max_length=10, null=True)),
                ('model_up', models.FloatField(null=True)),
                ('model_wic', models.FloatField(null=True)),
                ('model_down', models.FloatField(null=True)),
                ('implied_probability', models.FloatField(null=True)),
                ('return_risk', models.FloatField(null=True)),
                ('gross_irr', models.FloatField(null=True)),
                ('days_to_close', models.FloatField(null=True)),
                ('ann_irr', models.FloatField(null=True)),
                ('adj_ann_irr', models.FloatField(null=True)),
                ('long_prob', models.FloatField(null=True)),
                ('long_irr', models.FloatField(null=True)),
                ('short_prob', models.FloatField(null=True)),
                ('short_irr', models.FloatField(null=True)),
                ('potential_long', models.CharField(max_length=10, null=True)),
                ('potential_short', models.CharField(max_length=10, null=True)),
            ],
        ),
    ]
