# Generated by Django 2.2.4 on 2021-03-10 23:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('case', '0017_case_donotmarket'),
    ]

    operations = [
        migrations.AddField(
            model_name='lossdata',
            name='notProceedingReason',
            field=models.IntegerField(blank=True, choices=[(1, 'No further action by client'), (2, 'Doesn’t like Reverse Mortgages'), (3, 'Fees or interest rate too high'), (4, 'Other')], null=True),
        ),
        migrations.AlterField(
            model_name='lossdata',
            name='closeReason',
            field=models.IntegerField(blank=True, choices=[(1, 'Below minimum age'), (2, 'Invalid or rejected refer postcode'), (3, 'Below minimum loan amount'), (4, 'Above maximum loan amount'), (5, 'Refinance too large'), (6, 'Unsuitable purpose'), (7, 'Unsuitable property'), (8, 'Unsuitable title ownership'), (9, 'Deceased borrower'), (10, 'Not proceeding'), (11, 'Other')], null=True),
        ),
    ]
