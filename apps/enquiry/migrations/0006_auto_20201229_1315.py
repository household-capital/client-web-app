# Generated by Django 2.2.4 on 2020-12-29 02:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('enquiry', '0005_auto_20201222_1554'),
    ]

    operations = [
        migrations.AlterField(
            model_name='enquiry',
            name='name',
            field=models.CharField(blank=True, max_length=121, null=True),
        ),
    ]
