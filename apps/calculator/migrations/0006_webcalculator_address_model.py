# Generated by Django 2.2.4 on 2021-02-17 03:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('calculator', '0005_auto_20210222_2339'),
    ]

    operations = [
        migrations.AddField(
            model_name='webcalculator',
            name='base_specificity',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='webcalculator',
            name='street_name',
            field=models.CharField(blank=True, max_length=80, null=True),
        ),
        migrations.AddField(
            model_name='webcalculator',
            name='street_number',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AddField(
            model_name='webcalculator',
            name='street_type',
            field=models.CharField(blank=True, max_length=80, null=True),
        ),
        migrations.AddField(
            model_name='webcalculator',
            name='gnaf_id',
            field=models.CharField(blank=True, max_length=80, null=True),
        ),
    ]
