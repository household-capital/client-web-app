# Generated by Django 2.1.7 on 2019-07-08 08:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('enquiry', '0005_enquiry_sfleadid'),
    ]

    operations = [
        migrations.AddField(
            model_name='enquiry',
            name='doNotMarket',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='enquiry',
            name='followUpNotes',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='enquiry',
            name='lossDate',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='enquiry',
            name='lossNotes',
            field=models.TextField(blank=True, null=True),
        ),
    ]
