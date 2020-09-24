# Generated by Django 2.2.4 on 2020-05-06 03:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('case', '0070_auto_20200505_2352'),
    ]

    operations = [
        migrations.AlterField(
            model_name='loanpurposes',
            name='category',
            field=models.IntegerField(choices=[(3, 'LIVE'), (2, 'REFINANCE'), (1, 'TOP_UP'), (4, 'GIVE'), (5, 'CARE')]),
        ),
        migrations.AlterField(
            model_name='loanpurposes',
            name='intention',
            field=models.IntegerField(choices=[(7, 'LUMP_SUM'), (1, 'INVESTMENT'), (5, 'RENOVATIONS'), (3, 'REGULAR_DRAWDOWN'), (6, 'TRANSPORT'), (4, 'GIVE_TO_FAMILY'), (8, 'MORTGAGE'), (2, 'CONTINGENCY')]),
        ),
    ]
