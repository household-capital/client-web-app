# Generated by Django 2.2.4 on 2020-05-03 05:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('case', '0063_auto_20200503_1514'),
    ]

    operations = [
        migrations.AlterField(
            model_name='loanpurposes',
            name='category',
            field=models.IntegerField(choices=[(1, 'TOP_UP'), (4, 'GIVE'), (2, 'REFINANCE'), (3, 'LIVE'), (5, 'CARE')]),
        ),
        migrations.AlterField(
            model_name='loanpurposes',
            name='intention',
            field=models.IntegerField(choices=[(7, 'LUMP_SUM'), (6, 'TRANSPORT'), (1, 'INVESTMENT'), (3, 'REGULAR_DRAWDOWN'), (2, 'CONTINGENCY'), (5, 'RENOVATIONS'), (8, 'MORTGAGE'), (4, 'GIVE_TO_FAMILY')]),
        ),
    ]
