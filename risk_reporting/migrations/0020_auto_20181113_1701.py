# Generated by Django 2.0.6 on 2018-11-13 17:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('risk_reporting', '0019_auto_20181113_1122'),
    ]

    operations = [
        migrations.AlterField(
            model_name='formulaebaseddownsides',
            name='BaseCaseOperation',
            field=models.CharField(max_length=5, null=True),
        ),
        migrations.AlterField(
            model_name='formulaebaseddownsides',
            name='OutlierOperation',
            field=models.CharField(max_length=5, null=True),
        ),
    ]
