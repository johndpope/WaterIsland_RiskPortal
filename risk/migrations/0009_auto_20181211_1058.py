# Generated by Django 2.0.6 on 2018-12-11 10:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('risk', '0008_auto_20181210_1132'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='ess_idea',
            options={'get_latest_by': 'version_number'},
        ),
    ]
