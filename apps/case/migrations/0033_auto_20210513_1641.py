# Generated by Django 2.2.4 on 2021-05-13 06:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('case', '0032_auto_20210510_1857'),
    ]

    operations = [
        migrations.AlterField(
            model_name='case',
            name='caseStage',
            field=models.IntegerField(choices=[(7, 'Unqualified / Lead created'), (8, 'Marketing Qualified'), (9, 'SQ - General Info'), (10, 'SQ - Brochure sent'), (11, 'SQ - Customer summary sent'), (12, 'SQ - Future call'), (14, 'SQ - No Answer'), (15, 'SQ - Voicemail'), (16, 'SQ - Email Sent'), (17, 'Meeting Booked'), (0, 'Discovery'), (18, 'Wait List'), (2, 'Meeting Held'), (4, 'Application'), (5, 'Documentation'), (6, 'Funded'), (3, 'Closed')]),
        ),
    ]