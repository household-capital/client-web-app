# Generated by Django 2.2.4 on 2021-06-24 01:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('enquiry', '0025_enquiry_head_doc'),
    ]

    operations = [
        migrations.AlterField(
            model_name='enquiry',
            name='referrer',
            field=models.IntegerField(choices=[(0, 'Phone'), (1, 'Email'), (3, 'Web'), (6, 'Social'), (2, 'Calculator'), (5, 'Partner'), (4, 'Broker'), (7, 'Adviser'), (8, 'Pre Qualification'), (100, 'Other')]),
        ),
    ]
