# Generated by Django 2.2.4 on 2021-03-23 23:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('case', '0023_auto_20210317_1608'),
    ]

    operations = [
        migrations.AddField(
            model_name='case',
            name='deleted_on',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
