# Generated by Django 2.2.4 on 2020-03-16 06:45

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('case', '0021_case_refcaseuid'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='case',
            name='dataCSV',
        ),
        migrations.RemoveField(
            model_name='case',
            name='dataDocument',
        ),
        migrations.RemoveField(
            model_name='case',
            name='electronicDocument',
        ),
        migrations.RemoveField(
            model_name='case',
            name='privacyDocument',
        ),
        migrations.RemoveField(
            model_name='case',
            name='solicitorInstruction',
        ),
        migrations.RemoveField(
            model_name='case',
            name='specialConditions',
        ),
        migrations.RemoveField(
            model_name='case',
            name='valuerContact',
        ),
        migrations.RemoveField(
            model_name='case',
            name='valuerEmail',
        ),
        migrations.RemoveField(
            model_name='case',
            name='valuerFirm',
        ),
        migrations.RemoveField(
            model_name='case',
            name='valuerInstruction',
        ),
    ]
