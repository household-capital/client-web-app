# Generated by Django 2.2.4 on 2021-06-04 00:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('enquiry', '0022_enquiry_product_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='enquiry',
            name='errorText',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
