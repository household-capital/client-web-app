# Generated by Django 2.2.4 on 2020-05-29 05:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('application', '0050_auto_20200529_1422'),
    ]

    operations = [
        migrations.AddField(
            model_name='application',
            name='user_agent',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name='applicationpurposes',
            name='category',
            field=models.IntegerField(blank=True, choices=[(4, 'GIVE'), (3, 'LIVE'), (5, 'CARE'), (2, 'REFINANCE'), (1, 'TOP_UP')], null=True),
        ),
        migrations.AlterField(
            model_name='applicationpurposes',
            name='intention',
            field=models.IntegerField(blank=True, choices=[(8, 'MORTGAGE'), (4, 'GIVE_TO_FAMILY'), (6, 'TRANSPORT'), (3, 'REGULAR_DRAWDOWN'), (1, 'INVESTMENT'), (2, 'CONTINGENCY'), (7, 'LUMP_SUM'), (5, 'RENOVATIONS')], null=True),
        ),
    ]
