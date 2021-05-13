# Generated by Django 2.2.4 on 2021-05-10 08:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('case', '0029_case_followup'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lossdata',
            name='closeReason',
            field=models.IntegerField(blank=True, choices=[(31, 'Below minimum age'), (32, 'Invalid or rejected refer postcode'), (33, 'Below minimum loan amount'), (34, 'Above maximum loan amount'), (35, 'Refinance too large'), (9, 'Unsuitable purpose'), (8, 'Unsuitable property'), (38, 'Unsuitable title ownership'), (39, 'Deceased borrower'), (40, 'Not proceeding'), (41, 'Doesn’t like Reverse Mortgages'), (43, 'Fees or interest rate too high'), (12, 'Other'), (1, 'Age Restriction'), (2, 'Postcode Restriction'), (3, 'Below minimum loan amount'), (4, 'Credit History'), (5, 'Mortgage too Large'), (6, 'Short-term / Bridging Requirement'), (7, 'Tenants in common'), (10, 'Client Pursuing Alternative'), (11, 'Client went to Competitor'), (13, 'No further action by client')], null=True),
        ),
    ]