# Generated by Django 2.2.4 on 2020-05-03 05:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_sessionlog'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sessionlog',
            name='description',
            field=models.CharField(blank=True, max_length=60, null=True),
        ),
    ]
