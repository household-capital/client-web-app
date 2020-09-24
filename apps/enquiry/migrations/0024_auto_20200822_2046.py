# Generated by Django 2.2.4 on 2020-08-22 10:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('enquiry', '0023_enquiry_mortgagedebt'),
    ]

    operations = [
        migrations.AlterField(
            model_name='enquiry',
            name='marketingSource',
            field=models.IntegerField(blank=True, choices=[(11, 'Web search'), (1, 'TV Advert'), (2, 'TV Advertorial'), (3, 'Radio'), (4, 'Word of mouth'), (6, 'Competitor'), (7, 'Direct mail'), (12, 'Direct Email'), (8, 'Facebook'), (9, 'LinkedIn'), (10, 'Your Life Choices'), (13, 'Starts at 60'), (14, 'Care About'), (16, 'Broker Referral'), (15, 'Broker Specialist'), (17, 'Financial Adviser'), (18, 'Age Care Adviser'), (100, 'Other')], null=True),
        ),
        migrations.AlterField(
            model_name='enquiry',
            name='referrer',
            field=models.IntegerField(choices=[(0, 'Phone'), (1, 'Email'), (3, 'Web'), (6, 'Social'), (2, 'Calculator'), (5, 'Partner'), (4, 'Broker'), (7, 'Adviser'), (100, 'Other')]),
        ),
    ]
