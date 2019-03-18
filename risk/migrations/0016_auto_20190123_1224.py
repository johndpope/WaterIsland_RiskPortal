# Generated by Django 2.0.10 on 2019-01-23 12:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('risk', '0015_ess_idea_on_pt_balance_sheet'),
    ]

    operations = [
        migrations.AddField(
            model_name='ess_idea',
            name='how_to_adjust',
            field=models.CharField(default='cix', max_length=10, null=True),
        ),
        migrations.AddField(
            model_name='ess_idea',
            name='premium_format',
            field=models.CharField(default='dollar', max_length=10, null=True),
        ),
    ]