# Generated by Django 2.0.10 on 2019-02-26 14:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('risk_reporting', '0032_auto_20190226_1128'),
    ]

    operations = [
        migrations.AlterField(
            model_name='formulaebaseddownsides',
            name='IsExcluded',
            field=models.CharField(default='No', max_length=22),
        ),
    ]