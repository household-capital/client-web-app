# Generated by Django 2.2.4 on 2021-02-05 02:12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('case', '0010_auto_20210113_1117'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='factfind',
            name='is_protected_equity',
        ),
        migrations.RemoveField(
            model_name='factfind',
            name='protected_equity',
        ),
    ]