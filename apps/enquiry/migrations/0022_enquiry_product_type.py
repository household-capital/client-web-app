# Generated by Django 2.2.4 on 2021-06-02 00:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('enquiry', '0021_auto_20210528_1757'),
    ]

    operations = [
        migrations.AddField(
            model_name='enquiry',
            name='product_type',
            field=models.CharField(blank=True, choices=[('HHC.RM.2018', 'HHC.RM.2018'), ('HHC.RM.2021', 'HHC.RM.2021')], max_length=11, null=True),
        ),
    ]
