# Generated by Django 2.0.6 on 2018-10-30 09:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portfolio_analytics', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dealuniverse',
            name='id',
            field=models.AutoField(primary_key=True, serialize=False),
        ),
    ]
