# Generated by Django 2.2.4 on 2020-03-28 03:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('servicing', '0026_auto_20200328_1450'),
    ]

    operations = [
        migrations.RenameField(
            model_name='facilityroles',
            old_name='isPrimaryContact',
            new_name='isContact',
        ),
    ]
