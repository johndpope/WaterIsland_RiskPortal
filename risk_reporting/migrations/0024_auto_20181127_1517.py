# Generated by Django 2.0.6 on 2018-11-27 15:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('risk_reporting', '0023_auto_20181127_1416'),
    ]

    operations = [
        migrations.AlterField(
            model_name='formulaebaseddownsides',
            name='id',
            field=models.AutoField(primary_key=True, serialize=False, unique=True),
        ),
    ]
