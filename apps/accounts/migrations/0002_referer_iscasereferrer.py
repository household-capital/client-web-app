# Generated by Django 2.2.4 on 2020-03-17 11:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='referer',
            name='isCaseReferrer',
            field=models.BooleanField(default=False),
        ),
    ]
