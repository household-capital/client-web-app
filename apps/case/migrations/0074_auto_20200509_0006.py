# Generated by Django 2.2.4 on 2020-05-08 14:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('case', '0073_auto_20200508_2229'),
    ]

    operations = [
        migrations.AlterField(
            model_name='loanpurposes',
            name='category',
            field=models.IntegerField(choices=[(5, 'CARE'), (1, 'TOP_UP'), (4, 'GIVE'), (3, 'LIVE'), (2, 'REFINANCE')]),
        ),
        migrations.AlterField(
            model_name='loanpurposes',
            name='intention',
            field=models.IntegerField(choices=[(1, 'INVESTMENT'), (6, 'TRANSPORT'), (2, 'CONTINGENCY'), (4, 'GIVE_TO_FAMILY'), (8, 'MORTGAGE'), (7, 'LUMP_SUM'), (5, 'RENOVATIONS'), (3, 'REGULAR_DRAWDOWN')]),
        ),
    ]
