# Generated by Django 2.1.7 on 2019-07-01 09:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_profile_calendlyurl'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='salesforceID',
            field=models.CharField(blank=True, max_length=18, null=True),
        ),
    ]
