# Generated by Django 2.2.4 on 2021-01-06 13:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('calculator', '0003_auto_20201016_1922'),
    ]

    operations = [
        migrations.AlterField(
            model_name='webcalculator',
            name='name',
            field=models.CharField(blank=True, max_length=121, null=True),
        ),
    ]
