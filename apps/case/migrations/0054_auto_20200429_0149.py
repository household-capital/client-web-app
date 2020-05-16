# Generated by Django 2.2.4 on 2020-04-28 15:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('case', '0053_auto_20200427_2314'),
    ]

    operations = [
        migrations.AlterField(
            model_name='loanpurposes',
            name='category',
            field=models.IntegerField(choices=[(4, 'GIVE'), (1, 'TOP_UP'), (5, 'CARE'), (2, 'REFINANCE'), (3, 'LIVE')]),
        ),
        migrations.AlterField(
            model_name='loanpurposes',
            name='intention',
            field=models.IntegerField(choices=[(6, 'TRANSPORT'), (3, 'REGULAR_DRAWDOWN'), (5, 'RENOVATIONS'), (2, 'CONTINGENCY'), (4, 'GIVE_TO_FAMILY'), (1, 'INVESTMENT'), (8, 'MORTGAGE'), (7, 'LUMP_SUM')]),
        ),
    ]
