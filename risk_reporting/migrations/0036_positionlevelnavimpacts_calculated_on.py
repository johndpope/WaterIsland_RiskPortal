# Generated by Django 2.0.10 on 2019-03-06 14:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('risk_reporting', '0035_positionlevelnavimpacts'),
    ]

    operations = [
        migrations.AddField(
            model_name='positionlevelnavimpacts',
            name='CALCULATED_ON',
            field=models.DateTimeField(null=True),
        ),
    ]