# Generated by Django 2.2.4 on 2021-03-18 10:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('calculator', '0013_auto_20210318_2115'),
    ]

    operations = [
        migrations.AlterField(
            model_name='webcalculator',
            name='raw_name',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
    ]