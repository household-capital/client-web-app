# Generated by Django 2.2.4 on 2021-06-01 06:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('case', '0036_merge_20210531_1044'),
    ]

    operations = [
        migrations.AlterField(
            model_name='loan',
            name='product_type',
            field=models.CharField(blank=True, choices=[('HHC.RM.2018', 'HHC.RM.2018'), ('HHC.RM.2021', 'HHC.RM.2021')], max_length=11, null=True),
        ),
    ]