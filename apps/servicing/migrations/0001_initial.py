# Generated by Django 2.2.4 on 2020-09-26 01:06

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Facility',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('facilityUID', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('originalCaseUID', models.UUIDField(unique=True)),
                ('meetingDate', models.DateTimeField(blank=True, null=True)),
                ('sfLoanName', models.CharField(max_length=80)),
                ('sfID', models.CharField(max_length=20, unique=True)),
                ('sfLoanID', models.CharField(blank=True, max_length=20, null=True)),
                ('sfAccountID', models.CharField(max_length=20)),
                ('sfReferrerAccount', models.CharField(blank=True, max_length=20, null=True)),
                ('amalID', models.CharField(max_length=20)),
                ('sfOriginatorID', models.CharField(max_length=20)),
                ('status', models.IntegerField(choices=[(0, 'Inactive'), (1, 'Active'), (2, 'Repaid'), (3, 'Suspended')])),
                ('settlementDate', models.DateTimeField(blank=True, null=True)),
                ('dischargeDate', models.DateTimeField(blank=True, null=True)),
                ('maxDrawdownDate', models.DateTimeField(blank=True, null=True)),
                ('maturityDate', models.DateTimeField(blank=True, null=True)),
                ('totalPurposeAmount', models.FloatField(default=0)),
                ('totalEstablishmentFee', models.FloatField(default=0)),
                ('totalLoanAmount', models.FloatField(default=0)),
                ('totalPlanPurposeAmount', models.FloatField(default=0)),
                ('totalPlanEstablishmentFee', models.FloatField(default=0)),
                ('totalPlanAmount', models.FloatField(default=0)),
                ('totalValuation', models.FloatField(blank=True, default=1, null=True)),
                ('establishmentFeeRate', models.FloatField(default=0)),
                ('approvedAmount', models.FloatField(default=0)),
                ('advancedAmount', models.FloatField(default=0)),
                ('currentBalance', models.FloatField(default=0)),
                ('currentLVR', models.FloatField(default=0)),
                ('bPayBillerCode', models.CharField(blank=True, max_length=20, null=True)),
                ('bPayReference', models.CharField(blank=True, max_length=20, null=True)),
                ('relationshipNotes', models.TextField(blank=True, null=True)),
                ('bsbNumber', models.CharField(blank=True, max_length=20, null=True)),
                ('bankAccountNumber', models.CharField(blank=True, max_length=20, null=True)),
                ('nextAnnualService', models.DateField(blank=True, null=True)),
                ('annualServiceNotification', models.BooleanField(default=False)),
                ('amalReconciliation', models.BooleanField(default=False)),
                ('amalBreach', models.BooleanField(default=False)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('owner', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'Facilities',
            },
        ),
        migrations.CreateModel(
            name='FacilityProperty',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sfPropertyID', models.CharField(max_length=20, unique=True)),
                ('street', models.CharField(blank=True, max_length=80, null=True)),
                ('suburb', models.CharField(blank=True, max_length=30, null=True)),
                ('state', models.IntegerField(blank=True, choices=[(0, 'NSW'), (1, 'VIC'), (2, 'ACT'), (3, 'QLD'), (4, 'SA'), (5, 'WA'), (6, 'TAS'), (7, 'NT')], null=True)),
                ('postcode', models.CharField(blank=True, max_length=4, null=True)),
                ('dwellingType', models.IntegerField(blank=True, choices=[(0, 'House'), (1, 'Apartment')], null=True)),
                ('insuranceCompany', models.CharField(blank=True, max_length=60, null=True)),
                ('insurancePolicy', models.CharField(blank=True, max_length=80, null=True)),
                ('insuranceExpiryDate', models.DateTimeField(blank=True, null=True)),
                ('insuredAmount', models.FloatField(blank=True, default=0, null=True)),
                ('facility', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='servicing.Facility')),
            ],
            options={
                'verbose_name_plural': 'Facility Property',
            },
        ),
        migrations.CreateModel(
            name='FacilityRoles',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sfContactID', models.CharField(max_length=20, unique=True)),
                ('role', models.IntegerField(choices=[(0, 'Principal Borrower'), (1, 'Secondary Borrower'), (2, 'Borrower'), (3, 'Nominated Occupant'), (4, 'Permitted Cohabitant'), (5, 'Power of Attorney'), (6, 'Authorised 3rd Party'), (7, 'Distribution Partner Contact'), (8, 'Adviser'), (9, 'Loan Originator'), (10, 'Loan Writer'), (11, 'Valuer'), (12, 'Executor'), (13, 'Solicitor')])),
                ('isContact', models.BooleanField(default=False)),
                ('isInformation', models.BooleanField(default=False)),
                ('isAuthorised', models.IntegerField(choices=[(0, 'No'), (1, 'Yes'), (2, 'Refer POA')], default=0)),
                ('lastName', models.CharField(blank=True, max_length=30, null=True)),
                ('firstName', models.CharField(blank=True, max_length=30, null=True)),
                ('preferredName', models.CharField(blank=True, max_length=30, null=True)),
                ('middleName', models.CharField(blank=True, max_length=30, null=True)),
                ('salutation', models.IntegerField(blank=True, choices=[(1, 'Mr.'), (2, 'Ms.'), (3, 'Mrs.'), (4, 'Dr.'), (5, 'Prof.')], null=True)),
                ('birthdate', models.DateField(blank=True, null=True)),
                ('gender', models.IntegerField(blank=True, choices=[(0, 'Female'), (1, 'Male')], null=True)),
                ('maritalStatus', models.IntegerField(blank=True, choices=[(1, 'Single'), (2, 'Married'), (3, 'Divorced'), (4, 'Widowed'), (5, 'Defacto')], null=True)),
                ('mobile', models.CharField(blank=True, max_length=20, null=True)),
                ('phone', models.CharField(blank=True, max_length=20, null=True)),
                ('email', models.CharField(blank=True, max_length=50, null=True)),
                ('street', models.CharField(blank=True, max_length=100, null=True)),
                ('suburb', models.CharField(blank=True, max_length=30, null=True)),
                ('state', models.IntegerField(blank=True, choices=[(0, 'NSW'), (1, 'VIC'), (2, 'ACT'), (3, 'QLD'), (4, 'SA'), (5, 'WA'), (6, 'TAS'), (7, 'NT')], null=True)),
                ('postcode', models.CharField(blank=True, max_length=4, null=True)),
                ('roleNotes', models.TextField(blank=True, null=True)),
                ('facility', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='servicing.Facility')),
            ],
            options={
                'verbose_name_plural': 'Facility Roles',
                'ordering': ('role',),
            },
        ),
        migrations.CreateModel(
            name='FacilityPurposes',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sfPurposeID', models.CharField(max_length=20, unique=True)),
                ('category', models.IntegerField(choices=[(3, 'Live'), (5, 'Care'), (1, 'Top Up'), (4, 'Give'), (2, 'Refinance')])),
                ('intention', models.IntegerField(choices=[(3, 'Regular Drawdown'), (5, 'Renovations'), (6, 'Transport and Travel'), (7, 'Lump Sum'), (2, 'Contingency'), (4, 'Give to Family'), (8, 'Mortgage'), (1, 'Investment')])),
                ('amount', models.FloatField(blank=True, default=0, null=True)),
                ('drawdownAmount', models.FloatField(blank=True, default=0, null=True)),
                ('drawdownFrequency', models.IntegerField(blank=True, choices=[(1, 'Fortnightly'), (2, 'Monthly')], null=True)),
                ('drawdownStartDate', models.DateTimeField(blank=True, null=True)),
                ('drawdownEndDate', models.DateTimeField(blank=True, null=True)),
                ('planAmount', models.FloatField(blank=True, default=0, null=True)),
                ('planPeriod', models.IntegerField(blank=True, default=0, null=True)),
                ('topUpBuffer', models.BooleanField(default=False)),
                ('description', models.TextField(blank=True, null=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('active', models.BooleanField(default=True)),
                ('contractDrawdowns', models.IntegerField(blank=True, default=0, null=True)),
                ('planDrawdowns', models.IntegerField(blank=True, default=0, null=True)),
                ('facility', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='servicing.Facility')),
            ],
            options={
                'verbose_name_plural': 'Facility Purposes',
            },
        ),
        migrations.CreateModel(
            name='FacilityPropertyVal',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('valuationAmount', models.FloatField(blank=True, default=0, null=True)),
                ('valuationDate', models.DateTimeField(blank=True, null=True)),
                ('valuationType', models.IntegerField(choices=[(0, 'Auto Valuation'), (1, 'Full Valuation'), (2, 'Rates Valuation')], default=0)),
                ('valuationCompany', models.CharField(blank=True, max_length=20, null=True)),
                ('valuerName', models.CharField(blank=True, max_length=40, null=True)),
                ('property', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='servicing.FacilityProperty')),
            ],
            options={
                'verbose_name_plural': 'Facility Property Valuation',
            },
        ),
        migrations.CreateModel(
            name='FacilityEvents',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('eventDate', models.DateTimeField()),
                ('eventType', models.IntegerField(choices=[(1, 'Loan Settlement'), (2, 'Loan Variation'), (3, 'Loan Repaid'), (4, 'Death of a Borrower'), (5, 'Repayment Event')])),
                ('eventNotes', models.TextField(blank=True, null=True)),
                ('facility', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='servicing.Facility')),
            ],
            options={
                'verbose_name_plural': 'Facility Events',
            },
        ),
        migrations.CreateModel(
            name='FacilityEnquiry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('otherEnquirerName', models.CharField(blank=True, max_length=60, null=True)),
                ('contactEmail', models.EmailField(blank=True, max_length=254, null=True)),
                ('contactPhone', models.CharField(blank=True, max_length=15, null=True)),
                ('actionNotes', models.TextField(blank=True, null=True)),
                ('actioned', models.BooleanField(choices=[(False, 'Open'), (True, 'Actioned')], default=False)),
                ('actionDate', models.DateTimeField(blank=True, null=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('actionedBy', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='actionedBy', to=settings.AUTH_USER_MODEL)),
                ('facility', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='servicing.Facility')),
                ('identifiedEnquirer', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='servicing.FacilityRoles')),
                ('owner', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'Facility Enquiries',
            },
        ),
        migrations.CreateModel(
            name='FacilityAnnual',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('annualUID', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('reviewDate', models.DateField()),
                ('contactEmail', models.EmailField(blank=True, max_length=254, null=True)),
                ('responseIP', models.CharField(blank=True, max_length=45, null=True)),
                ('responseDate', models.DateTimeField(blank=True, null=True)),
                ('choiceHouseholdConfirm', models.BooleanField(blank=True, null=True)),
                ('choiceHouseholdPersons', models.BooleanField(blank=True, null=True)),
                ('householdNotes', models.TextField(blank=True, null=True)),
                ('choiceInsuranceConfirm', models.BooleanField(blank=True, null=True)),
                ('choiceRatesConfirm', models.BooleanField(blank=True, null=True)),
                ('choiceRepairsConfirm', models.BooleanField(blank=True, null=True)),
                ('homeNotes', models.TextField(blank=True, null=True)),
                ('choiceUndrawnConfirm', models.BooleanField(blank=True, null=True)),
                ('choiceRegularConfirm', models.BooleanField(blank=True, null=True)),
                ('choiceCallbackConfirm', models.BooleanField(blank=True, null=True)),
                ('needNotes', models.TextField(blank=True, null=True)),
                ('reviewNotes', models.TextField(blank=True, null=True)),
                ('completed', models.BooleanField(default=False)),
                ('submitted', models.BooleanField(default=False)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('completedBy', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('facility', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='servicing.Facility')),
                ('identifiedContact', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='servicing.FacilityRoles')),
            ],
            options={
                'verbose_name_plural': 'Facility Annual Review',
            },
        ),
        migrations.CreateModel(
            name='FacilityAdditional',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('additionalUID', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('amountRequested', models.IntegerField(blank=True, default=0, null=True)),
                ('amountEstablishmentFee', models.FloatField(blank=True, default=0, null=True)),
                ('amountTotal', models.FloatField(blank=True, default=0, null=True)),
                ('establishmentFeeRate', models.FloatField(blank=True, default=0, null=True)),
                ('contactEmail', models.EmailField(blank=True, max_length=254, null=True)),
                ('requestedIP', models.CharField(blank=True, max_length=45, null=True)),
                ('requestedDate', models.DateTimeField(blank=True, null=True)),
                ('choicePurposes', models.BooleanField(default=False)),
                ('choiceNoMaterialChange', models.BooleanField(default=False)),
                ('submitted', models.BooleanField(default=False)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('completedBy', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('facility', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='servicing.Facility')),
                ('identifiedContact', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='servicing.FacilityRoles')),
            ],
            options={
                'verbose_name_plural': 'Facility Additional Drawdown',
            },
        ),
        migrations.CreateModel(
            name='FacilityTransactions',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.CharField(blank=True, max_length=120, null=True)),
                ('type', models.CharField(blank=True, max_length=30, null=True)),
                ('transactionDate', models.DateTimeField(blank=True, null=True)),
                ('effectiveDate', models.DateTimeField(blank=True, null=True)),
                ('tranRef', models.CharField(max_length=30)),
                ('debitAmount', models.FloatField(blank=True, default=0, null=True)),
                ('creditAmount', models.FloatField(blank=True, default=0, null=True)),
                ('balance', models.FloatField(blank=True, default=0, null=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('facility', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='servicing.Facility')),
            ],
            options={
                'verbose_name_plural': 'Facility Transactions',
                'unique_together': {('facility', 'tranRef')},
            },
        ),
    ]