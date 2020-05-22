# Generated by Django 2.2.4 on 2020-05-22 02:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('case', '0093_auto_20200516_1825'),
    ]

    operations = [
        migrations.AlterField(
            model_name='loanpurposes',
            name='category',
            field=models.IntegerField(choices=[(5, 'CARE'), (4, 'GIVE'), (3, 'LIVE'), (2, 'REFINANCE'), (1, 'TOP_UP')]),
        ),
        migrations.AlterField(
            model_name='loanpurposes',
            name='intention',
            field=models.IntegerField(choices=[(5, 'RENOVATIONS'), (8, 'MORTGAGE'), (4, 'GIVE_TO_FAMILY'), (1, 'INVESTMENT'), (6, 'TRANSPORT'), (7, 'LUMP_SUM'), (3, 'REGULAR_DRAWDOWN'), (2, 'CONTINGENCY')]),
        ),
    ]
