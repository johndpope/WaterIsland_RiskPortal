# Generated by Django 2.0.6 on 2018-12-07 17:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('risk', '0004_auto_20181207_1635'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='ess_idea',
            unique_together={('id', 'version_number')},
        ),
    ]
