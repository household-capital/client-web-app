# Generated by Django 2.2.4 on 2021-02-17 03:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('calculator', '0005_auto_20210202_1001'),
    ]

    operations = [
        migrations.AddField(
            model_name='webcalculator',
            name='gnaf_id',
            field=models.CharField(blank=True, max_length=80, null=True),
        ),
    ]