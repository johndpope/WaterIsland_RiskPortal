# Generated by Django 2.0.10 on 2019-03-01 12:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('realtime_pnl_impacts', '0003_arbitrageytdperformance_catalyst_wic'),
    ]

    operations = [
        migrations.AddField(
            model_name='arbitrageytdperformance',
            name='fund_aum',
            field=models.FloatField(null=True),
        ),
        migrations.AddField(
            model_name='arbitrageytdperformance',
            name='pnl_bps',
            field=models.FloatField(null=True),
        ),
    ]
