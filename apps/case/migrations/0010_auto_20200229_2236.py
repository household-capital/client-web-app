# Generated by Django 2.2.4 on 2020-02-29 11:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('case', '0009_auto_20200229_2225'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='transactiondata',
            constraint=models.UniqueConstraint(fields=('case', 'tranRef'), name='case-tranRef constraint'),
        ),
    ]
