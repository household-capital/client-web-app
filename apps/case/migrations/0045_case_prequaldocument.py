# Generated by Django 2.2.4 on 2021-07-04 03:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('case', '0044_auto_20210625_1149'),
    ]

    operations = [
        migrations.AddField(
            model_name='case',
            name='preQualDocument',
            field=models.FileField(blank=True, max_length=150, null=True, upload_to=''),
        ),
    ]
