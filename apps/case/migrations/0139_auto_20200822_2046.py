# Generated by Django 2.2.4 on 2020-08-22 10:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('case', '0138_auto_20200819_2120'),
    ]

    operations = [
        migrations.AddField(
            model_name='case',
            name='channelDetail',
            field=models.IntegerField(blank=True, choices=[(11, 'Web search'), (1, 'TV Advert'), (2, 'TV Advertorial'), (3, 'Radio'), (4, 'Word of mouth'), (6, 'Competitor'), (7, 'Direct mail'), (12, 'Direct Email'), (8, 'Facebook'), (9, 'LinkedIn'), (10, 'Your Life Choices'), (13, 'Starts at 60'), (14, 'Care About'), (16, 'Broker Referral'), (15, 'Broker Specialist'), (17, 'Financial Adviser'), (18, 'Age Care Adviser'), (100, 'Other')], null=True),
        ),
        migrations.AlterField(
            model_name='case',
            name='salesChannel',
            field=models.IntegerField(blank=True, choices=[(11, 'Direct'), (12, 'Partner'), (7, 'Broker'), (13, 'Adviser')], null=True),
        ),
        migrations.AlterField(
            model_name='loanpurposes',
            name='category',
            field=models.IntegerField(choices=[(3, 'LIVE'), (2, 'REFINANCE'), (5, 'CARE'), (4, 'GIVE'), (1, 'TOP_UP')]),
        ),
        migrations.AlterField(
            model_name='loanpurposes',
            name='intention',
            field=models.IntegerField(choices=[(3, 'REGULAR_DRAWDOWN'), (5, 'RENOVATIONS'), (1, 'INVESTMENT'), (2, 'CONTINGENCY'), (4, 'GIVE_TO_FAMILY'), (7, 'LUMP_SUM'), (6, 'TRANSPORT_AND_TRAVEL'), (8, 'MORTGAGE')]),
        ),
    ]
