# Generated by Django 2.2.4 on 2020-05-27 01:37

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('calculator', '0002_auto_20200427_2020'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='webcalculator',
            name='choiceMortgage',
        ),
        migrations.RemoveField(
            model_name='webcalculator',
            name='choiceOtherNeeds',
        ),
    ]
