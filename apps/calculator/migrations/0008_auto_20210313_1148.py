# Generated by Django 2.2.4 on 2021-03-13 00:48

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('calculator', '0007_auto_20210313_1147'),
    ]

    operations = [
        migrations.RenameField(
            model_name='webcontact',
            old_name='sourceID',
            new_name='origin_id',
        ),
    ]
