# Generated by Django 2.2.4 on 2020-08-23 04:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('case', '0139_auto_20200822_2046'),
    ]

    operations = [
        migrations.AlterField(
            model_name='case',
            name='salesChannel',
            field=models.IntegerField(blank=True, choices=[(11, 'Direct Acquisition'), (12, 'Partner'), (7, 'Broker'), (13, 'Adviser')], null=True),
        ),
        migrations.AlterField(
            model_name='loanpurposes',
            name='category',
            field=models.IntegerField(choices=[(4, 'GIVE'), (5, 'CARE'), (1, 'TOP_UP'), (3, 'LIVE'), (2, 'REFINANCE')]),
        ),
        migrations.AlterField(
            model_name='loanpurposes',
            name='intention',
            field=models.IntegerField(choices=[(3, 'REGULAR_DRAWDOWN'), (5, 'RENOVATIONS'), (2, 'CONTINGENCY'), (1, 'INVESTMENT'), (4, 'GIVE_TO_FAMILY'), (8, 'MORTGAGE'), (7, 'LUMP_SUM'), (6, 'TRANSPORT_AND_TRAVEL')]),
        ),
    ]
