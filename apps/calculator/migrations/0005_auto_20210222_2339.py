# Generated by Django 2.2.4 on 2021-02-22 12:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('calculator', '0004_auto_20210107_0003'),
    ]

    operations = [
        migrations.AddField(
            model_name='webcalculator',
            name='requestedCallback',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='webcalculator',
            name='submissionOrigin',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
