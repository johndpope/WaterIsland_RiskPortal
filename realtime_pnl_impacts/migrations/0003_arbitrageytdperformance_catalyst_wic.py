# Generated by Django 2.0.10 on 2019-02-26 15:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('realtime_pnl_impacts', '0002_arbitrageytdperformance_fund'),
    ]

    operations = [
        migrations.AddField(
            model_name='arbitrageytdperformance',
            name='catalyst_wic',
            field=models.CharField(max_length=40, null=True),
        ),
    ]