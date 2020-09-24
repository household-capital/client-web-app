# Generated by Django 2.2.4 on 2020-06-01 09:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('application', '0058_auto_20200601_1526'),
    ]

    operations = [
        migrations.AddField(
            model_name='application',
            name='isLowLVR',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='applicationpurposes',
            name='category',
            field=models.IntegerField(blank=True, choices=[(1, 'TOP_UP'), (5, 'CARE'), (4, 'GIVE'), (3, 'LIVE'), (2, 'REFINANCE')], null=True),
        ),
        migrations.AlterField(
            model_name='applicationpurposes',
            name='intention',
            field=models.IntegerField(blank=True, choices=[(4, 'GIVE_TO_FAMILY'), (3, 'REGULAR_DRAWDOWN'), (6, 'TRANSPORT'), (5, 'RENOVATIONS'), (8, 'MORTGAGE'), (7, 'LUMP_SUM'), (1, 'INVESTMENT'), (2, 'CONTINGENCY')], null=True),
        ),
    ]
