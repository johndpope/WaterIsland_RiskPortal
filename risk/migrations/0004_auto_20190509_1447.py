# Generated by Django 2.0.13 on 2019-05-09 14:47

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('risk', '0003_auto_20190430_1116'),
    ]

    operations = [
        migrations.AddField(
            model_name='ma_deals',
            name='action_id',
            field=models.CharField(max_length=20, null=True),
        )
    ]
