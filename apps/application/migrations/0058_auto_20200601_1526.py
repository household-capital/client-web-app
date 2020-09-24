# Generated by Django 2.2.4 on 2020-06-01 05:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('application', '0057_auto_20200601_1212'),
    ]

    operations = [
        migrations.RenameField(
            model_name='application',
            old_name='loanSummarySent',
            new_name='summarySent',
        ),
        migrations.AddField(
            model_name='application',
            name='summarySentDate',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='application',
            name='summarySentRef',
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
        migrations.AlterField(
            model_name='applicationpurposes',
            name='category',
            field=models.IntegerField(blank=True, choices=[(4, 'GIVE'), (5, 'CARE'), (3, 'LIVE'), (2, 'REFINANCE'), (1, 'TOP_UP')], null=True),
        ),
        migrations.AlterField(
            model_name='applicationpurposes',
            name='intention',
            field=models.IntegerField(blank=True, choices=[(2, 'CONTINGENCY'), (5, 'RENOVATIONS'), (8, 'MORTGAGE'), (1, 'INVESTMENT'), (7, 'LUMP_SUM'), (6, 'TRANSPORT'), (4, 'GIVE_TO_FAMILY'), (3, 'REGULAR_DRAWDOWN')], null=True),
        ),
    ]
