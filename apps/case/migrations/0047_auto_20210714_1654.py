# Generated by Django 2.2.4 on 2021-07-14 06:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('case', '0046_auto_20210714_1207'),
    ]

    operations = [
        migrations.AlterField(
            model_name='case',
            name='channelDetail',
            field=models.IntegerField(blank=True, choices=[(11, 'Web search'), (1, 'TV Advert'), (2, 'TV Advertorial'), (3, 'Radio'), (4, 'Word of mouth'), (6, 'Competitor'), (7, 'Direct mail'), (12, 'Direct Email'), (8, 'Facebook'), (20, 'Facebook Interactive'), (21, 'Facebook Calculator'), (9, 'LinkedIn'), (22, 'Google Ads Mobile'), (10, 'Your Life Choices'), (19, 'National Seniors'), (13, 'Starts at 60'), (14, 'Care About'), (16, 'Broker Referral'), (15, 'Broker Specialist'), (17, 'Financial Adviser'), (18, 'Age Care Adviser'), (100, 'Other')], null=True),
        ),
        migrations.AlterField(
            model_name='case',
            name='referrer',
            field=models.IntegerField(choices=[(-1, 'Unassigned'), (0, 'Phone'), (1, 'Email'), (3, 'Web'), (6, 'Social'), (2, 'Calculator'), (5, 'Partner'), (4, 'Broker'), (7, 'Adviser'), (8, 'Pre Qualification'), (9, 'Search'), (100, 'Other')], default=-1),
        ),
    ]
