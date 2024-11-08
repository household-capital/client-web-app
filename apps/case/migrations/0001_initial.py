# Generated by Django 2.2.4 on 2020-09-26 01:06

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Case',
            fields=[
                ('caseID', models.AutoField(primary_key=True, serialize=False)),
                ('caseUID', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('refCaseUID', models.UUIDField(blank=True, null=True)),
                ('refFacilityUID', models.UUIDField(blank=True, null=True)),
                ('appUID', models.UUIDField(blank=True, null=True)),
                ('caseStage', models.IntegerField(choices=[(0, 'Discovery'), (2, 'Meeting Held'), (4, 'Application'), (5, 'Documentation'), (6, 'Funded'), (3, 'Closed')])),
                ('appType', models.IntegerField(choices=[(0, 'Application'), (1, 'Variation')], default=0)),
                ('productType', models.IntegerField(blank=True, choices=[(0, 'Lump Sum'), (1, 'Income'), (2, 'Combination'), (3, 'Contingency 20K')], default=0, null=True)),
                ('caseDescription', models.CharField(max_length=60)),
                ('caseNotes', models.TextField(blank=True, null=True)),
                ('phoneNumber', models.CharField(blank=True, max_length=20, null=True)),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
                ('loanType', models.IntegerField(blank=True, choices=[(0, 'Single'), (1, 'Joint')], null=True)),
                ('clientType1', models.IntegerField(blank=True, choices=[(0, 'Borrower'), (1, 'Nominated Occupant'), (3, 'Permitted Cohabitant'), (2, 'Power of Attorney')], null=True)),
                ('salutation_1', models.IntegerField(blank=True, choices=[(1, 'Mr.'), (2, 'Ms.'), (3, 'Mrs.'), (4, 'Dr.'), (5, 'Prof.')], null=True)),
                ('middlename_1', models.CharField(blank=True, max_length=30, null=True)),
                ('maritalStatus_1', models.IntegerField(blank=True, choices=[(1, 'Single'), (2, 'Married'), (3, 'Divorced'), (4, 'Widowed'), (5, 'De Facto'), (6, 'Separated')], null=True)),
                ('surname_1', models.CharField(blank=True, max_length=30, null=True)),
                ('firstname_1', models.CharField(blank=True, max_length=30, null=True)),
                ('preferredName_1', models.CharField(blank=True, max_length=30, null=True)),
                ('birthdate_1', models.DateField(blank=True, null=True)),
                ('age_1', models.IntegerField(blank=True, null=True)),
                ('sex_1', models.IntegerField(blank=True, choices=[(0, 'Female'), (1, 'Male')], null=True)),
                ('clientType2', models.IntegerField(blank=True, choices=[(0, 'Borrower'), (1, 'Nominated Occupant'), (3, 'Permitted Cohabitant'), (2, 'Power of Attorney')], null=True)),
                ('salutation_2', models.IntegerField(blank=True, choices=[(1, 'Mr.'), (2, 'Ms.'), (3, 'Mrs.'), (4, 'Dr.'), (5, 'Prof.')], null=True)),
                ('middlename_2', models.CharField(blank=True, max_length=30, null=True)),
                ('maritalStatus_2', models.IntegerField(blank=True, choices=[(1, 'Single'), (2, 'Married'), (3, 'Divorced'), (4, 'Widowed'), (5, 'De Facto'), (6, 'Separated')], null=True)),
                ('surname_2', models.CharField(blank=True, max_length=30, null=True)),
                ('firstname_2', models.CharField(blank=True, max_length=30, null=True)),
                ('preferredName_2', models.CharField(blank=True, max_length=30, null=True)),
                ('birthdate_2', models.DateField(blank=True, null=True)),
                ('age_2', models.IntegerField(blank=True, null=True)),
                ('sex_2', models.IntegerField(blank=True, choices=[(0, 'Female'), (1, 'Male')], null=True)),
                ('superAmount', models.IntegerField(blank=True, null=True)),
                ('investmentLabel', models.IntegerField(choices=[(0, 'Superannuation'), (1, 'Shares / Managed Funds'), (2, 'Investment Property'), (3, 'Combined Investments')], default=0)),
                ('pensionType', models.IntegerField(choices=[(0, 'Full'), (1, 'Partial'), (2, 'None')], default=2)),
                ('pensionAmount', models.IntegerField(default=0)),
                ('mortgageDebt', models.IntegerField(blank=True, null=True)),
                ('street', models.CharField(blank=True, max_length=60, null=True)),
                ('suburb', models.CharField(blank=True, max_length=30, null=True)),
                ('postcode', models.IntegerField(blank=True, null=True)),
                ('state', models.IntegerField(blank=True, choices=[(0, 'NSW'), (1, 'VIC'), (2, 'ACT'), (3, 'QLD'), (4, 'SA'), (5, 'WA'), (6, 'TAS'), (7, 'NT')], null=True)),
                ('valuation', models.IntegerField(blank=True, null=True)),
                ('dwellingType', models.IntegerField(blank=True, choices=[(0, 'House'), (1, 'Apartment')], null=True)),
                ('propertyImage', models.ImageField(blank=True, null=True, upload_to='customerImages')),
                ('isReferPostcode', models.BooleanField(blank=True, null=True)),
                ('referPostcodeStatus', models.BooleanField(blank=True, null=True)),
                ('meetingDate', models.DateTimeField(blank=True, null=True)),
                ('isZoomMeeting', models.BooleanField(blank=True, default=False, null=True)),
                ('summaryDocument', models.FileField(blank=True, max_length=150, null=True, upload_to='customerReports')),
                ('summarySentDate', models.DateTimeField(blank=True, null=True)),
                ('summarySentRef', models.CharField(blank=True, max_length=30, null=True)),
                ('responsibleDocument', models.FileField(blank=True, max_length=150, null=True, upload_to='customerReports')),
                ('enquiryDocument', models.FileField(blank=True, max_length=150, null=True, upload_to='')),
                ('valuationDocument', models.FileField(blank=True, max_length=150, null=True, upload_to='customerDocuments')),
                ('titleDocument', models.FileField(blank=True, max_length=150, null=True, upload_to='customerDocuments')),
                ('titleRequest', models.BooleanField(blank=True, null=True)),
                ('lixiFile', models.FileField(blank=True, max_length=150, null=True, upload_to='')),
                ('applicationDocument', models.FileField(blank=True, max_length=150, null=True, upload_to='customerReports')),
                ('salesChannel', models.IntegerField(blank=True, choices=[(11, 'Direct Acquisition'), (12, 'Partner'), (7, 'Broker'), (13, 'Adviser')], null=True)),
                ('channelDetail', models.IntegerField(blank=True, choices=[(11, 'Web search'), (1, 'TV Advert'), (2, 'TV Advertorial'), (3, 'Radio'), (4, 'Word of mouth'), (6, 'Competitor'), (7, 'Direct mail'), (12, 'Direct Email'), (8, 'Facebook'), (9, 'LinkedIn'), (10, 'Your Life Choices'), (13, 'Starts at 60'), (14, 'Care About'), (16, 'Broker Referral'), (15, 'Broker Specialist'), (17, 'Financial Adviser'), (18, 'Age Care Adviser'), (100, 'Other')], null=True)),
                ('adviser', models.CharField(blank=True, max_length=60, null=True)),
                ('referralRepNo', models.CharField(blank=True, max_length=60, null=True)),
                ('sfLeadID', models.CharField(blank=True, max_length=20, null=True)),
                ('sfOpportunityID', models.CharField(blank=True, max_length=20, null=True)),
                ('sfLoanID', models.CharField(blank=True, max_length=20, null=True)),
                ('amalIdentifier', models.CharField(blank=True, max_length=40, null=True)),
                ('amalLoanID', models.CharField(blank=True, max_length=40, null=True)),
                ('enquiryCreateDate', models.DateTimeField(blank=True, null=True)),
                ('enqUID', models.UUIDField(blank=True, null=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('owner', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('referralCompany', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='accounts.Referer')),
            ],
            options={
                'verbose_name_plural': 'Case',
                'ordering': ('-updated',),
            },
        ),
        migrations.CreateModel(
            name='FundDetail',
            fields=[
                ('fundID', models.AutoField(primary_key=True, serialize=False)),
                ('fundName', models.CharField(max_length=30)),
                ('fundImage', models.ImageField(upload_to='fundImages')),
            ],
            options={
                'verbose_name_plural': 'Superfund Definitions',
                'ordering': ('fundName',),
            },
        ),
        migrations.CreateModel(
            name='Loan',
            fields=[
                ('localLoanID', models.AutoField(primary_key=True, serialize=False)),
                ('maxLVR', models.FloatField(default=0)),
                ('actualLVR', models.FloatField(blank=True, default=0, null=True)),
                ('protectedEquity', models.IntegerField(choices=[(0, '0%'), (5, '5%'), (10, '10%'), (15, '15%'), (20, '20%')], default=0)),
                ('detailedTitle', models.BooleanField(default=False)),
                ('isLowLVR', models.BooleanField(default=False)),
                ('purposeAmount', models.IntegerField(default=0)),
                ('establishmentFee', models.IntegerField(default=0)),
                ('totalLoanAmount', models.IntegerField(default=0)),
                ('planPurposeAmount', models.IntegerField(default=0)),
                ('planEstablishmentFee', models.IntegerField(default=0)),
                ('totalPlanAmount', models.IntegerField(default=0)),
                ('interestPayAmount', models.IntegerField(default=0)),
                ('interestPayPeriod', models.IntegerField(default=0)),
                ('annualPensionIncome', models.IntegerField(default=0)),
                ('choiceRetireAtHome', models.BooleanField(default=False)),
                ('choiceAvoidDownsizing', models.BooleanField(default=False)),
                ('choiceAccessFunds', models.BooleanField(default=False)),
                ('choiceTopUp', models.BooleanField(default=False)),
                ('choiceRefinance', models.BooleanField(default=False)),
                ('choiceGive', models.BooleanField(default=False)),
                ('choiceReserve', models.BooleanField(default=False)),
                ('choiceLive', models.BooleanField(default=False)),
                ('choiceCare', models.BooleanField(default=False)),
                ('choiceFuture', models.BooleanField(default=False)),
                ('choiceCenterlink', models.BooleanField(default=False)),
                ('choiceVariable', models.BooleanField(default=False)),
                ('consentPrivacy', models.BooleanField(default=False)),
                ('consentElectronic', models.BooleanField(default=False)),
                ('accruedInterest', models.IntegerField(blank=True, null=True)),
                ('orgTotalLoanAmount', models.IntegerField(default=0)),
                ('orgPurposeAmount', models.IntegerField(default=0)),
                ('orgEstablishmentFee', models.IntegerField(default=0)),
                ('variationTotalAmount', models.IntegerField(default=0)),
                ('variationPurposeAmount', models.IntegerField(default=0)),
                ('variationFeeAmount', models.IntegerField(default=0)),
                ('case', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='case.Case')),
            ],
            options={
                'verbose_name_plural': 'Case Loan Details',
            },
        ),
        migrations.CreateModel(
            name='ModelSetting',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('inflationRate', models.FloatField(blank=True, null=True)),
                ('housePriceInflation', models.FloatField(blank=True, null=True)),
                ('interestRate', models.FloatField(blank=True, null=True)),
                ('lendingMargin', models.FloatField(blank=True, null=True)),
                ('comparisonRateIncrement', models.FloatField(blank=True, null=True)),
                ('establishmentFeeRate', models.FloatField(blank=True, null=True)),
                ('case', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='case.Case')),
            ],
            options={
                'verbose_name_plural': 'Case Settings',
            },
        ),
        migrations.CreateModel(
            name='LossData',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('lossNotes', models.TextField(blank=True, null=True)),
                ('closeDate', models.DateField(blank=True, null=True)),
                ('closeReason', models.IntegerField(blank=True, choices=[(1, 'Age Restriction'), (2, 'Postcode Restriction'), (3, 'Below minimum loan amount'), (4, 'Credit History'), (5, 'Mortgage too Large'), (6, 'Short-term / Bridging Requirement'), (7, 'Tenants in common'), (8, 'Unsuitable Property'), (9, 'Unsuitable Purpose'), (10, 'Client Pursuing Alternative'), (11, 'Client went to Competitor'), (13, 'No further action by client'), (12, 'Other')], null=True)),
                ('followUpDate', models.DateField(blank=True, null=True)),
                ('followUpNotes', models.TextField(blank=True, null=True)),
                ('doNotMarket', models.BooleanField(default=False)),
                ('case', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='case.Case')),
            ],
            options={
                'verbose_name_plural': 'Case Loss Data',
            },
        ),
        migrations.CreateModel(
            name='LoanPurposes',
            fields=[
                ('purposeID', models.AutoField(primary_key=True, serialize=False)),
                ('purposeUID', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('active', models.BooleanField(default=True)),
                ('category', models.IntegerField(choices=[(3, 'LIVE'), (5, 'CARE'), (2, 'REFINANCE'), (1, 'TOP_UP'), (4, 'GIVE')])),
                ('intention', models.IntegerField(choices=[(3, 'REGULAR_DRAWDOWN'), (2, 'CONTINGENCY'), (8, 'MORTGAGE'), (1, 'INVESTMENT'), (5, 'RENOVATIONS'), (4, 'GIVE_TO_FAMILY'), (7, 'LUMP_SUM'), (6, 'TRANSPORT_AND_TRAVEL')])),
                ('amount', models.IntegerField(blank=True, default=0, null=True)),
                ('originalAmount', models.IntegerField(blank=True, default=0, null=True)),
                ('drawdownAmount', models.IntegerField(blank=True, default=0, null=True)),
                ('drawdownFrequency', models.IntegerField(blank=True, choices=[(1, 'Fortnightly'), (2, 'Monthly')], null=True)),
                ('drawdownStartDate', models.DateTimeField(blank=True, null=True)),
                ('drawdownEndDate', models.DateTimeField(blank=True, null=True)),
                ('contractDrawdowns', models.IntegerField(blank=True, default=0, null=True)),
                ('planDrawdowns', models.IntegerField(blank=True, default=0, null=True)),
                ('planAmount', models.IntegerField(blank=True, default=0, null=True)),
                ('planPeriod', models.IntegerField(blank=True, default=0, null=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('topUpBuffer', models.BooleanField(default=False)),
                ('loan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='case.Loan')),
            ],
            options={
                'verbose_name_plural': 'Case Loan Purposes',
            },
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
                ('choiceProduct', models.BooleanField(default=True)),
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
        migrations.CreateModel(
            name='FactFind',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('backgroundNotes', models.TextField(blank=True, null=True)),
                ('requirementsNotes', models.TextField(blank=True, null=True)),
                ('topUpNotes', models.TextField(blank=True, null=True)),
                ('refiNotes', models.TextField(blank=True, null=True)),
                ('liveNotes', models.TextField(blank=True, null=True)),
                ('giveNotes', models.TextField(blank=True, null=True)),
                ('careNotes', models.TextField(blank=True, null=True)),
                ('futureNotes', models.TextField(blank=True, null=True)),
                ('clientNotes', models.TextField(blank=True, null=True)),
                ('additionalNotes', models.TextField(blank=True, null=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('case', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='case.Case')),
            ],
            options={
                'verbose_name_plural': 'Case Fact Find',
            },
        ),
        migrations.AddField(
            model_name='case',
            name='superFund',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='case.FundDetail'),
        ),
    ]
