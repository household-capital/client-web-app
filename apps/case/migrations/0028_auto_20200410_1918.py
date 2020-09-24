# Generated by Django 2.2.4 on 2020-04-10 09:18

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('case', '0027_auto_20200408_2206'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='loan',
            name='incomeObjective',
        ),
        migrations.RemoveField(
            model_name='loan',
            name='topUpIncome',
        ),
        migrations.CreateModel(
            name='LoanPurposes',
            fields=[
                ('purposeID', models.AutoField(primary_key=True, serialize=False)),
                ('purposeUID', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('category', models.IntegerField(choices=[(3, 'Live'), (5, 'Care'), (4, 'Give'), (2, 'Refinance'), (1, 'Top Up')])),
                ('intention', models.IntegerField(choices=[(7, 'Lum Sum'), (1, 'Investment'), (8, 'Mortgage'), (5, 'Renovations'), (6, 'Transport, Travel, and Other'), (3, 'Regular Draw-down'), (2, 'Contingency'), (4, 'Give to Family')])),
                ('amount', models.FloatField(blank=True, default=0, null=True)),
                ('drawdownAmount', models.FloatField(blank=True, default=0, null=True)),
                ('drawdownFrequency', models.CharField(blank=True, max_length=20, null=True)),
                ('drawdownStartDate', models.DateTimeField(blank=True, null=True)),
                ('drawdownEndDate', models.DateTimeField(blank=True, null=True)),
                ('planAmount', models.FloatField(blank=True, default=0, null=True)),
                ('planPeriod', models.IntegerField(blank=True, default=0, null=True)),
                ('planDrawdowns', models.IntegerField(blank=True, default=0, null=True)),
                ('topUpBuffer', models.BooleanField(default=False)),
                ('description', models.TextField(blank=True, null=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('loan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='case.Loan')),
            ],
            options={
                'verbose_name_plural': 'Loan Purposes',
            },
        ),
    ]
