# Generated by Django 2.2.4 on 2021-06-11 06:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('case', '0039_auto_20210610_1033'),
    ]

    operations = [
        migrations.AddField(
            model_name='case',
            name='lead_needs_action',
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
    ]
