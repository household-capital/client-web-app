# Generated by Django 2.2.4 on 2020-04-02 11:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('application', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='lowlvr',
            name='firstname_1',
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
        migrations.AddField(
            model_name='lowlvr',
            name='surname_1',
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
    ]
