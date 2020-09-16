# Generated by Django 2.2.4 on 2020-07-23 09:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('application', '0084_auto_20200722_2216'),
    ]

    operations = [
        migrations.AlterField(
            model_name='applicationpurposes',
            name='category',
            field=models.IntegerField(blank=True, choices=[(2, 'REFINANCE'), (1, 'TOP_UP'), (3, 'LIVE'), (5, 'CARE'), (4, 'GIVE')], null=True),
        ),
        migrations.AlterField(
            model_name='applicationpurposes',
            name='intention',
            field=models.IntegerField(blank=True, choices=[(1, 'INVESTMENT'), (2, 'CONTINGENCY'), (3, 'REGULAR_DRAWDOWN'), (6, 'TRANSPORT'), (4, 'GIVE_TO_FAMILY'), (5, 'RENOVATIONS'), (7, 'LUMP_SUM'), (8, 'MORTGAGE')], null=True),
        ),
    ]
