# Generated by Django 2.2.4 on 2021-06-04 01:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('case', '0037_auto_20210601_1621'),
    ]

    operations = [
        migrations.AlterField(
            model_name='case',
            name='ineligible_reason',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
