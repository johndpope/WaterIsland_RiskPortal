# Generated by Django 2.0.6 on 2018-12-11 16:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('risk', '0010_ess_idea_deal_key'),
    ]

    operations = [
        migrations.AddField(
            model_name='ess_idea',
            name='idea_balance_sheet',
            field=models.TextField(null=True),
        ),
    ]
