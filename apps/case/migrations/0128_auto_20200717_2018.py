# Generated by Django 2.2.4 on 2020-07-17 10:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('case', '0127_auto_20200717_1302'),
    ]

    operations = [
        migrations.AlterField(
            model_name='loanpurposes',
            name='category',
            field=models.IntegerField(choices=[(3, 'LIVE'), (5, 'CARE'), (1, 'TOP_UP'), (2, 'REFINANCE'), (4, 'GIVE')]),
        ),
        migrations.AlterField(
            model_name='loanpurposes',
            name='intention',
            field=models.IntegerField(choices=[(4, 'GIVE_TO_FAMILY'), (3, 'REGULAR_DRAWDOWN'), (1, 'INVESTMENT'), (5, 'RENOVATIONS'), (7, 'LUMP_SUM'), (2, 'CONTINGENCY'), (6, 'TRANSPORT'), (8, 'MORTGAGE')]),
        ),
    ]
