# Generated by Django 2.2.4 on 2020-03-16 03:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('case', '0019_auto_20200316_1127'),
    ]

    operations = [
        migrations.AddField(
            model_name='case',
            name='appType',
            field=models.IntegerField(choices=[(0, 'Application'), (1, 'Variation')], default=0),
        ),
    ]
