# Generated by Django 2.2.4 on 2020-05-26 03:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('case', '0095_auto_20200526_1303'),
    ]

    operations = [
        migrations.AddField(
            model_name='case',
            name='enqUID',
            field=models.UUIDField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='loanpurposes',
            name='category',
            field=models.IntegerField(choices=[(3, 'LIVE'), (5, 'CARE'), (1, 'TOP_UP'), (2, 'REFINANCE'), (4, 'GIVE')]),
        ),
        migrations.AlterField(
            model_name='loanpurposes',
            name='intention',
            field=models.IntegerField(choices=[(8, 'MORTGAGE'), (7, 'LUMP_SUM'), (2, 'CONTINGENCY'), (3, 'REGULAR_DRAWDOWN'), (5, 'RENOVATIONS'), (1, 'INVESTMENT'), (6, 'TRANSPORT'), (4, 'GIVE_TO_FAMILY')]),
        ),
    ]
