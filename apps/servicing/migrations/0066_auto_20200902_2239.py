# Generated by Django 2.2.4 on 2020-09-02 12:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('servicing', '0065_auto_20200902_2236'),
    ]

    operations = [
        migrations.AddField(
            model_name='facilitypurposes',
            name='active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='facilitypurposes',
            name='contractDrawdowns',
            field=models.IntegerField(blank=True, default=0, null=True),
        ),
        migrations.AddField(
            model_name='facilitypurposes',
            name='planDrawdowns',
            field=models.IntegerField(blank=True, default=0, null=True),
        ),
        migrations.AlterField(
            model_name='facilitypurposes',
            name='category',
            field=models.IntegerField(choices=[(3, 'LIVE'), (2, 'REFINANCE'), (5, 'CARE'), (4, 'GIVE'), (1, 'TOP_UP')]),
        ),
        migrations.AlterField(
            model_name='facilitypurposes',
            name='intention',
            field=models.IntegerField(choices=[(3, 'REGULAR_DRAWDOWN'), (2, 'CONTINGENCY'), (7, 'LUMP_SUM'), (8, 'MORTGAGE'), (6, 'TRANSPORT_AND_TRAVEL'), (5, 'RENOVATIONS'), (4, 'GIVE_TO_FAMILY'), (1, 'INVESTMENT')]),
        ),
    ]
