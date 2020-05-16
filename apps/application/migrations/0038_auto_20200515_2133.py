# Generated by Django 2.2.4 on 2020-05-15 11:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('application', '0037_auto_20200515_1856'),
    ]

    operations = [
        migrations.AddField(
            model_name='application',
            name='clientType2',
            field=models.IntegerField(blank=True, choices=[(0, 'Borrower'), (1, 'Nominated Occupant'), (3, 'Permitted Cohabitant')], null=True),
        ),
        migrations.AlterField(
            model_name='application',
            name='loanType',
            field=models.BooleanField(choices=[(0, 'Single'), (1, 'Joint')], default=True),
        ),
        migrations.AlterField(
            model_name='applicationpurposes',
            name='category',
            field=models.IntegerField(blank=True, choices=[(5, 'CARE'), (3, 'LIVE'), (2, 'REFINANCE'), (1, 'TOP_UP'), (4, 'GIVE')], null=True),
        ),
        migrations.AlterField(
            model_name='applicationpurposes',
            name='intention',
            field=models.IntegerField(blank=True, choices=[(3, 'REGULAR_DRAWDOWN'), (6, 'TRANSPORT'), (1, 'INVESTMENT'), (4, 'GIVE_TO_FAMILY'), (5, 'RENOVATIONS'), (7, 'LUMP_SUM'), (2, 'CONTINGENCY'), (8, 'MORTGAGE')], null=True),
        ),
    ]
