# Generated by Django 2.2.4 on 2020-06-05 09:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('enquiry', '0011_auto_20200603_0945'),
    ]

    operations = [
        migrations.AlterField(
            model_name='enquiry',
            name='productType',
            field=models.IntegerField(blank=True, choices=[(0, 'Multi Purpose'), (1, 'Single Income'), (2, 'Single 20K')], default=0, null=True),
        ),
    ]
