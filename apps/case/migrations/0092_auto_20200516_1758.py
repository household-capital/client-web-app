# Generated by Django 2.2.4 on 2020-05-16 07:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('case', '0091_auto_20200516_1335'),
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
            field=models.IntegerField(choices=[(1, 'INVESTMENT'), (2, 'CONTINGENCY'), (8, 'MORTGAGE'), (7, 'LUMP_SUM'), (3, 'REGULAR_DRAWDOWN'), (4, 'GIVE_TO_FAMILY'), (6, 'TRANSPORT'), (5, 'RENOVATIONS')]),
        ),
    ]
