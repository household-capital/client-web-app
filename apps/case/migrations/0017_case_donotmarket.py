# Generated by Django 2.2.4 on 2021-03-15 05:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('case', '0016_auto_20210420_1500'),
    ]

    operations = [
        migrations.AddField(
            model_name='case',
            name='doNotMarket',
            field=models.BooleanField(default=False),
        ),
    ]
