# Generated by Django 2.2.4 on 2021-03-13 06:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('application', '0007_auto_20201222_1544'),
    ]

    operations = [
        migrations.AddField(
            model_name='application',
            name='origin_id',
            field=models.CharField(blank=True, max_length=36, null=True),
        ),
        migrations.AddField(
            model_name='application',
            name='origin_timestamp',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='application',
            name='submissionOrigin',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
