# Generated by Django 2.2.4 on 2021-04-12 01:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('case', '0030_auto_20210412_0020'),
    ]

    operations = [
        migrations.AddField(
            model_name='case',
            name='followUp',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
