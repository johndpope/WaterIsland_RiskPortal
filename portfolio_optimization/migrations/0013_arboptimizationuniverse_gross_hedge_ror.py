# Generated by Django 2.0.10 on 2019-07-09 09:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portfolio_optimization', '0012_auto_20190701_1449'),
    ]

    operations = [
        migrations.AddField(
            model_name='arboptimizationuniverse',
            name='gross_hedge_ror',
            field=models.FloatField(null=True),
        ),
    ]
