# Generated by Django 2.2.4 on 2021-04-15 04:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('enquiry', '0010_auto_20210313_0134'),
    ]

    operations = [
        migrations.AlterField(
            model_name='enquiry',
            name='enquiryStage',
            field=models.IntegerField(blank=True, choices=[(1, 'General Information'), (2, 'Brochure Sent'), (3, 'Customer Summary Sent'), (4, 'Discovery Meeting'), (5, 'Loan Interview'), (6, 'Live Transfer'), (7, 'Duplicate'), (8, 'Future Call'), (15, 'More time to think'), (9, 'Did not Qualify'), (10, 'Not Proceeding'), (11, 'Follow-up: No Answer'), (12, 'Follow-up: Voicemail'), (13, 'Initial: No Answer'), (14, 'NVN: Email Sent'), (16, 'Wait List')], null=True),
        ),
    ]
