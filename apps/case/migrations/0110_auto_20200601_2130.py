# Generated by Django 2.2.4 on 2020-06-01 11:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('case', '0109_auto_20200601_1939'),
    ]

    operations = [
        migrations.AlterField(
            model_name='loanpurposes',
            name='category',
            field=models.IntegerField(choices=[(4, 'GIVE'), (1, 'TOP_UP'), (2, 'REFINANCE'), (3, 'LIVE'), (5, 'CARE')]),
        ),
        migrations.AlterField(
            model_name='loanpurposes',
            name='intention',
            field=models.IntegerField(choices=[(3, 'REGULAR_DRAWDOWN'), (8, 'MORTGAGE'), (4, 'GIVE_TO_FAMILY'), (2, 'CONTINGENCY'), (5, 'RENOVATIONS'), (7, 'LUMP_SUM'), (1, 'INVESTMENT'), (6, 'TRANSPORT')]),
        ),
        migrations.CreateModel(
            name='LoanApplication',
            fields=[
                ('localAppID', models.AutoField(primary_key=True, serialize=False)),
                ('appUID', models.UUIDField(blank=True, null=True)),
                ('assetSaving', models.IntegerField(default=0)),
                ('assetVehicles', models.IntegerField(default=0)),
                ('assetOther', models.IntegerField(default=0)),
                ('liabLoans', models.IntegerField(default=0)),
                ('liabCards', models.IntegerField(default=0)),
                ('liabOther', models.IntegerField(default=0)),
                ('limitCards', models.IntegerField(default=0)),
                ('totalAnnualIncome', models.IntegerField(default=0)),
                ('incomePension', models.IntegerField(default=0)),
                ('incomePensionFreq', models.IntegerField(choices=[(3, 'Weekly'), (1, 'Fortnightly'), (2, 'Monthly'), (5, 'Annually')], default=1)),
                ('incomeSavings', models.IntegerField(default=0)),
                ('incomeSavingsFreq', models.IntegerField(choices=[(3, 'Weekly'), (1, 'Fortnightly'), (2, 'Monthly'), (5, 'Annually')], default=2)),
                ('incomeOther', models.IntegerField(default=0)),
                ('incomeOtherFreq', models.IntegerField(choices=[(3, 'Weekly'), (1, 'Fortnightly'), (2, 'Monthly'), (5, 'Annually')], default=2)),
                ('totalAnnualExpenses', models.IntegerField(default=0)),
                ('expenseHomeIns', models.IntegerField(default=0)),
                ('expenseHomeInsFreq', models.IntegerField(choices=[(3, 'Weekly'), (2, 'Monthly'), (4, 'Quarterly'), (5, 'Annually')], default=2)),
                ('expenseRates', models.IntegerField(default=0)),
                ('expenseRatesFreq', models.IntegerField(choices=[(3, 'Weekly'), (2, 'Monthly'), (4, 'Quarterly'), (5, 'Annually')], default=4)),
                ('expenseGroceries', models.IntegerField(default=0)),
                ('expenseGroceriesFreq', models.IntegerField(choices=[(3, 'Weekly'), (2, 'Monthly'), (4, 'Quarterly'), (5, 'Annually')], default=3)),
                ('expenseUtilities', models.IntegerField(default=0)),
                ('expenseUtilitiesFreq', models.IntegerField(choices=[(3, 'Weekly'), (2, 'Monthly'), (4, 'Quarterly'), (5, 'Annually')], default=4)),
                ('expenseMedical', models.IntegerField(default=0)),
                ('expenseMedicalFreq', models.IntegerField(choices=[(3, 'Weekly'), (2, 'Monthly'), (4, 'Quarterly'), (5, 'Annually')], default=2)),
                ('expenseTransport', models.IntegerField(default=0)),
                ('expenseTransportFreq', models.IntegerField(choices=[(3, 'Weekly'), (2, 'Monthly'), (4, 'Quarterly'), (5, 'Annually')], default=2)),
                ('expenseRepay', models.IntegerField(default=0)),
                ('expenseRepayFreq', models.IntegerField(choices=[(3, 'Weekly'), (2, 'Monthly'), (4, 'Quarterly'), (5, 'Annually')], default=2)),
                ('expenseOther', models.IntegerField(default=0)),
                ('expenseOtherFreq', models.IntegerField(choices=[(3, 'Weekly'), (2, 'Monthly'), (4, 'Quarterly'), (5, 'Annually')], default=2)),
                ('choiceIncome', models.BooleanField(default=True)),
                ('choiceOtherNeeds', models.BooleanField(blank=True, null=True)),
                ('choiceMortgage', models.BooleanField(blank=True, null=True)),
                ('choiceOwnership', models.BooleanField(blank=True, null=True)),
                ('choiceOccupants', models.BooleanField(blank=True, null=True)),
                ('bankBsbNumber', models.CharField(blank=True, max_length=7, null=True)),
                ('bankAccountName', models.CharField(blank=True, max_length=20, null=True)),
                ('bankAccountNumber', models.CharField(blank=True, max_length=12, null=True)),
                ('signingName_1', models.CharField(blank=True, max_length=50, null=True)),
                ('signingName_2', models.CharField(blank=True, max_length=50, null=True)),
                ('signingDate', models.DateTimeField(blank=True, null=True)),
                ('ip_address', models.CharField(blank=True, max_length=60, null=True)),
                ('user_agent', models.CharField(blank=True, max_length=200, null=True)),
                ('loan', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='case.Loan')),
            ],
            options={
                'verbose_name_plural': 'Case Loan Application',
            },
        ),
    ]
