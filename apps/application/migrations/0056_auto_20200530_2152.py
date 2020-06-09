# Generated by Django 2.2.4 on 2020-05-30 11:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('application', '0055_auto_20200530_2048'),
    ]

    operations = [
        migrations.AddField(
            model_name='applicationdocuments',
            name='mimeType',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='applicationpurposes',
            name='category',
            field=models.IntegerField(blank=True, choices=[(1, 'TOP_UP'), (5, 'CARE'), (3, 'LIVE'), (2, 'REFINANCE'), (4, 'GIVE')], null=True),
        ),
        migrations.AlterField(
            model_name='applicationpurposes',
            name='intention',
            field=models.IntegerField(blank=True, choices=[(7, 'LUMP_SUM'), (2, 'CONTINGENCY'), (5, 'RENOVATIONS'), (8, 'MORTGAGE'), (4, 'GIVE_TO_FAMILY'), (6, 'TRANSPORT'), (3, 'REGULAR_DRAWDOWN'), (1, 'INVESTMENT')], null=True),
        ),
    ]
