# Generated by Django 2.2.4 on 2019-11-04 07:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('case', '0006_auto_20191102_1440'),
    ]

    operations = [
        migrations.AddField(
            model_name='case',
            name='maritalStatus_1',
            field=models.IntegerField(blank=True, choices=[(1, 'Mr.'), (2, 'Ms.'), (3, 'Mrs.'), (4, 'Dr.'), (5, 'Prof.')], null=True),
        ),
        migrations.AddField(
            model_name='case',
            name='maritalStatus_2',
            field=models.IntegerField(blank=True, choices=[(1, 'Mr.'), (2, 'Ms.'), (3, 'Mrs.'), (4, 'Dr.'), (5, 'Prof.')], null=True),
        ),
        migrations.AddField(
            model_name='case',
            name='middlename_1',
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
        migrations.AddField(
            model_name='case',
            name='middlename_2',
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
        migrations.AddField(
            model_name='case',
            name='salutation_1',
            field=models.IntegerField(blank=True, choices=[(1, 'Mr.'), (2, 'Ms.'), (3, 'Mrs.'), (4, 'Dr.'), (5, 'Prof.')], null=True),
        ),
        migrations.AddField(
            model_name='case',
            name='salutation_2',
            field=models.IntegerField(blank=True, choices=[(1, 'Mr.'), (2, 'Ms.'), (3, 'Mrs.'), (4, 'Dr.'), (5, 'Prof.')], null=True),
        ),
        migrations.AlterField(
            model_name='case',
            name='caseType',
            field=models.IntegerField(choices=[(0, 'Discovery'), (2, 'Meeting Held'), (4, 'Application'), (5, 'Documentation'), (6, 'Funded'), (3, 'Closed')]),
        ),
    ]
