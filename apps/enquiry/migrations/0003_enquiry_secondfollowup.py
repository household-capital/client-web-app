# Generated by Django 2.2.4 on 2019-11-07 14:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('enquiry', '0002_auto_20190926_1147'),
    ]

    operations = [
        migrations.AddField(
            model_name='enquiry',
            name='secondfollowUp',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
