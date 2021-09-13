# Generated by Django 2.2.4 on 2020-09-26 01:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('case', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='loanpurposes',
            name='category',
            field=models.IntegerField(choices=[(1, 'TOP_UP'), (5, 'CARE'), (3, 'LIVE'), (2, 'REFINANCE'), (4, 'GIVE')]),
        ),
        migrations.AlterField(
            model_name='loanpurposes',
            name='intention',
            field=models.IntegerField(choices=[(8, 'MORTGAGE'), (3, 'REGULAR_DRAWDOWN'), (7, 'LUMP_SUM'), (5, 'RENOVATIONS'), (2, 'CONTINGENCY'), (4, 'GIVE_TO_FAMILY'), (1, 'INVESTMENT'), (6, 'TRANSPORT_AND_TRAVEL')]),
        ),
    ]
