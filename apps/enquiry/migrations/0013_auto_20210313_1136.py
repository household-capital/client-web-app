# Generated by Django 2.2.4 on 2021-03-13 00:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('enquiry', '0012_merge_20210313_1136'),
    ]

    operations = [
        migrations.AddField(
            model_name='enquiry',
            name='origin_id',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='enquiry',
            name='origin_timestamp',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]