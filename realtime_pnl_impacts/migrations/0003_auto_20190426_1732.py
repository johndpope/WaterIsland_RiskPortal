# Generated by Django 2.0.13 on 2019-04-26 17:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('realtime_pnl_impacts', '0002_pnlmonitors'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pnlmonitors',
            name='last_updated',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]