# Generated by Django 2.2.4 on 2020-09-26 01:06

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Application',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('appUID', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('productType', models.IntegerField(choices=[(1, 'Income'), (3, 'Contingency 20K')], default=0)),
                ('name', models.CharField(blank=True, max_length=30, null=True)),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
                ('mobile', models.CharField(blank=True, max_length=20, null=True)),
                ('loanType', models.IntegerField(choices=[(0, 'Single'), (1, 'Joint')], default=1)),
                ('age_1', models.IntegerField(blank=True, null=True)),
                ('age_2', models.IntegerField(blank=True, null=True)),
                ('dwellingType', models.IntegerField(choices=[(0, 'House'), (1, 'Apartment')], default=True)),
                ('valuation', models.IntegerField(blank=True, null=True)),
                ('surname_1', models.CharField(blank=True, max_length=30, null=True)),
                ('firstname_1', models.CharField(blank=True, max_length=30, null=True)),
                ('birthdate_1', models.DateField(blank=True, null=True)),
                ('sex_1', models.IntegerField(blank=True, choices=[(0, 'Female'), (1, 'Male')], null=True)),
                ('salutation_1', models.IntegerField(blank=True, choices=[(1, 'Mr.'), (2, 'Ms.'), (3, 'Mrs.'), (4, 'Dr.'), (5, 'Prof.')], null=True)),
                ('surname_2', models.CharField(blank=True, max_length=30, null=True)),
                ('firstname_2', models.CharField(blank=True, max_length=30, null=True)),
                ('birthdate_2', models.DateField(blank=True, null=True)),
                ('sex_2', models.IntegerField(blank=True, choices=[(0, 'Female'), (1, 'Male')], null=True)),
                ('salutation_2', models.IntegerField(blank=True, choices=[(1, 'Mr.'), (2, 'Ms.'), (3, 'Mrs.'), (4, 'Dr.'), (5, 'Prof.')], null=True)),
                ('clientType2', models.IntegerField(blank=True, choices=[(0, 'Borrower'), (1, 'Nominated Occupant'), (3, 'Permitted Cohabitant')], null=True)),
                ('consentPrivacy', models.BooleanField(default=False)),
                ('consentElectronic', models.BooleanField(default=False)),
                ('bankBsbNumber', models.CharField(blank=True, max_length=7, null=True)),
                ('bankAccountName', models.CharField(blank=True, max_length=20, null=True)),
                ('bankAccountNumber', models.CharField(blank=True, max_length=12, null=True)),
                ('streetAddress', models.CharField(blank=True, max_length=80, null=True)),
                ('suburb', models.CharField(blank=True, max_length=40, null=True)),
                ('state', models.IntegerField(blank=True, choices=[(0, 'NSW'), (1, 'VIC'), (2, 'ACT'), (3, 'QLD'), (4, 'SA'), (5, 'WA'), (6, 'TAS'), (7, 'NT')], null=True)),
                ('postcode', models.IntegerField(blank=True, null=True)),
                ('status', models.BooleanField(default=True)),
                ('maxLoanAmount', models.IntegerField(blank=True, null=True)),
                ('maxDrawdownAmount', models.IntegerField(blank=True, null=True)),
                ('maxDrawdownMonthly', models.IntegerField(blank=True, null=True)),
                ('maxLVR', models.FloatField(blank=True, null=True)),
                ('actualLVR', models.FloatField(blank=True, null=True)),
                ('isLowLVR', models.BooleanField(default=False)),
                ('purposeAmount', models.IntegerField(default=0)),
                ('establishmentFee', models.IntegerField(default=0)),
                ('totalLoanAmount', models.IntegerField(default=0)),
                ('planPurposeAmount', models.IntegerField(default=0)),
                ('planEstablishmentFee', models.IntegerField(default=0)),
                ('totalPlanAmount', models.IntegerField(default=0)),
                ('summaryDocument', models.FileField(blank=True, max_length=150, null=True, upload_to='customerReports')),
                ('applicationDocument', models.FileField(blank=True, max_length=150, null=True, upload_to='customerReports')),
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
                ('choiceProduct', models.BooleanField(default=True)),
                ('choiceOtherNeeds', models.BooleanField(blank=True, null=True)),
                ('choiceMortgage', models.BooleanField(blank=True, null=True)),
                ('choiceOwnership', models.BooleanField(blank=True, null=True)),
                ('choiceOccupants', models.BooleanField(blank=True, null=True)),
                ('pin', models.IntegerField(blank=True, null=True)),
                ('pinExpiry', models.DateTimeField(blank=True, null=True)),
                ('appStatus', models.IntegerField(choices=[(0, 'Created'), (1, 'In-Progress'), (2, 'Expired'), (3, 'Submitted'), (4, 'Contact'), (5, 'Closed')], default=0)),
                ('summarySent', models.BooleanField(default=False)),
                ('summarySentDate', models.DateTimeField(blank=True, null=True)),
                ('summarySentRef', models.CharField(blank=True, max_length=30, null=True)),
                ('loanSummaryAmount', models.IntegerField(default=0)),
                ('signingName_1', models.CharField(blank=True, max_length=50, null=True)),
                ('signingName_2', models.CharField(blank=True, max_length=50, null=True)),
                ('signingDate', models.DateTimeField(blank=True, null=True)),
                ('ip_address', models.CharField(blank=True, max_length=60, null=True)),
                ('user_agent', models.CharField(blank=True, max_length=200, null=True)),
                ('followUpEmail', models.DateTimeField(blank=True, null=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name_plural': 'Application',
            },
        ),
        migrations.CreateModel(
            name='ApplicationPurposes',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.IntegerField(blank=True, choices=[(3, 'LIVE'), (5, 'CARE'), (2, 'REFINANCE'), (1, 'TOP_UP'), (4, 'GIVE')], null=True)),
                ('intention', models.IntegerField(blank=True, choices=[(3, 'REGULAR_DRAWDOWN'), (2, 'CONTINGENCY'), (8, 'MORTGAGE'), (1, 'INVESTMENT'), (5, 'RENOVATIONS'), (4, 'GIVE_TO_FAMILY'), (7, 'LUMP_SUM'), (6, 'TRANSPORT_AND_TRAVEL')], null=True)),
                ('amount', models.IntegerField(blank=True, default=0, null=True)),
                ('drawdownAmount', models.IntegerField(blank=True, default=0, null=True)),
                ('drawdownFrequency', models.IntegerField(choices=[(1, 'Fortnightly'), (2, 'Monthly')], default=2)),
                ('contractDrawdowns', models.IntegerField(blank=True, default=0, null=True)),
                ('planDrawdowns', models.IntegerField(blank=True, default=0, null=True)),
                ('planAmount', models.IntegerField(blank=True, default=0, null=True)),
                ('planPeriod', models.IntegerField(blank=True, default=0, null=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('application', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='application.Application')),
            ],
            options={
                'verbose_name_plural': 'Application Loan Purposes',
            },
        ),
        migrations.CreateModel(
            name='ApplicationDocuments',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('docUID', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('documentType', models.IntegerField(choices=[(1, 'Rates Notice'), (2, 'Insurance Certificate'), (3, 'Strata Levies'), (100, 'Other')])),
                ('document', models.FileField(max_length=150, upload_to='customerDocuments')),
                ('mimeType', models.CharField(blank=True, max_length=100, null=True)),
                ('ip_address', models.CharField(blank=True, max_length=60, null=True)),
                ('user_agent', models.CharField(blank=True, max_length=200, null=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('application', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='application.Application')),
            ],
            options={
                'verbose_name_plural': 'Application Documents',
            },
        ),
    ]
