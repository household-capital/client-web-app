# Generated by Django 2.2.4 on 2021-03-03 02:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('case', '0013_auto_20210210_1119'),
    ]

    operations = [
        migrations.AddField(
            model_name='case',
            name='doNotMarket',
            field=models.BooleanField(default=False),
        ),
    ]