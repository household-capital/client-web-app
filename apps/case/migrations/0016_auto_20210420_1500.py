# Generated by Django 2.2.4 on 2021-04-20 05:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('case', '0015_auto_20210415_1433'),
    ]

    operations = [
        migrations.AlterField(
            model_name='case',
            name='caseStage',
            field=models.IntegerField(choices=[(0, 'Discovery'), (18, 'Wait List'), (2, 'Meeting Held'), (4, 'Application'), (5, 'Documentation'), (6, 'Funded'), (3, 'Closed')]),
        ),
    ]