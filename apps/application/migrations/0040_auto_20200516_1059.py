# Generated by Django 2.2.4 on 2020-05-16 00:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('application', '0039_auto_20200515_2208'),
    ]

    operations = [
        migrations.AddField(
            model_name='application',
            name='consentElectronic',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='application',
            name='consentPrivacy',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='applicationpurposes',
            name='category',
            field=models.IntegerField(blank=True, choices=[(2, 'REFINANCE'), (3, 'LIVE'), (5, 'CARE'), (4, 'GIVE'), (1, 'TOP_UP')], null=True),
        ),
        migrations.AlterField(
            model_name='applicationpurposes',
            name='intention',
            field=models.IntegerField(blank=True, choices=[(3, 'REGULAR_DRAWDOWN'), (4, 'GIVE_TO_FAMILY'), (5, 'RENOVATIONS'), (7, 'LUMP_SUM'), (8, 'MORTGAGE'), (2, 'CONTINGENCY'), (6, 'TRANSPORT'), (1, 'INVESTMENT')], null=True),
        ),
    ]
