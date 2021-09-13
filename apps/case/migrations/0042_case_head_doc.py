# Generated by Django 2.2.4 on 2021-06-24 01:46

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('case', '0041_case_loan_rating'),
    ]

    operations = [
        migrations.AddField(
            model_name='case',
            name='head_doc',
            field=django.contrib.postgres.fields.jsonb.JSONField(default=dict),
        ),
    ]
