# Generated by Django 2.0.6 on 2018-11-02 13:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('risk_reporting', '0009_dailynavimpacts'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dailynavimpacts',
            name='BASE_CASE_NAV_IMPACT_AED',
            field=models.CharField(max_length=10),
        ),
        migrations.AlterField(
            model_name='dailynavimpacts',
            name='BASE_CASE_NAV_IMPACT_ARB',
            field=models.CharField(max_length=10),
        ),
        migrations.AlterField(
            model_name='dailynavimpacts',
            name='BASE_CASE_NAV_IMPACT_CAM',
            field=models.CharField(max_length=10),
        ),
        migrations.AlterField(
            model_name='dailynavimpacts',
            name='BASE_CASE_NAV_IMPACT_LEV',
            field=models.CharField(max_length=10),
        ),
        migrations.AlterField(
            model_name='dailynavimpacts',
            name='BASE_CASE_NAV_IMPACT_LG',
            field=models.CharField(max_length=10),
        ),
        migrations.AlterField(
            model_name='dailynavimpacts',
            name='BASE_CASE_NAV_IMPACT_MACO',
            field=models.CharField(max_length=10),
        ),
        migrations.AlterField(
            model_name='dailynavimpacts',
            name='BASE_CASE_NAV_IMPACT_TAQ',
            field=models.CharField(max_length=10),
        ),
        migrations.AlterField(
            model_name='dailynavimpacts',
            name='BASE_CASE_NAV_IMPACT_WED',
            field=models.CharField(max_length=10),
        ),
        migrations.AlterField(
            model_name='dailynavimpacts',
            name='BASE_CASE_NAV_IMPACT_WIC',
            field=models.CharField(max_length=10),
        ),
        migrations.AlterField(
            model_name='dailynavimpacts',
            name='OUTLIER_NAV_IMPACT_AED',
            field=models.CharField(max_length=10),
        ),
        migrations.AlterField(
            model_name='dailynavimpacts',
            name='OUTLIER_NAV_IMPACT_ARB',
            field=models.CharField(max_length=10),
        ),
        migrations.AlterField(
            model_name='dailynavimpacts',
            name='OUTLIER_NAV_IMPACT_CAM',
            field=models.CharField(max_length=10),
        ),
        migrations.AlterField(
            model_name='dailynavimpacts',
            name='OUTLIER_NAV_IMPACT_LEV',
            field=models.CharField(max_length=10),
        ),
        migrations.AlterField(
            model_name='dailynavimpacts',
            name='OUTLIER_NAV_IMPACT_LG',
            field=models.CharField(max_length=10),
        ),
        migrations.AlterField(
            model_name='dailynavimpacts',
            name='OUTLIER_NAV_IMPACT_MACO',
            field=models.CharField(max_length=10),
        ),
        migrations.AlterField(
            model_name='dailynavimpacts',
            name='OUTLIER_NAV_IMPACT_TAQ',
            field=models.CharField(max_length=10),
        ),
        migrations.AlterField(
            model_name='dailynavimpacts',
            name='OUTLIER_NAV_IMPACT_WED',
            field=models.CharField(max_length=10),
        ),
        migrations.AlterField(
            model_name='dailynavimpacts',
            name='OUTLIER_NAV_IMPACT_WIC',
            field=models.CharField(max_length=10),
        ),
    ]
