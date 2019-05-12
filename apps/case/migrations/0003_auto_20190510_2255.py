# Generated by Django 2.1.7 on 2019-05-10 12:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('case', '0002_auto_20190510_2231'),
    ]

    operations = [
        migrations.AlterField(
            model_name='case',
            name='salesChannel',
            field=models.IntegerField(choices=[(0, 'Independent Financial Advisers'), (1, 'Institutional Financial Advisers'), (2, 'Super Financial Advisers'), (3, 'Aged Care Advisers'), (4, 'Aged Care Provider/Consultants'), (5, 'Accountants'), (6, 'Centrelink Advisers'), (7, 'Brokers'), (8, 'Bank Referral'), (9, 'Refinance'), (10, 'Super Direct'), (11, 'Direct Acquisition')], default=11),
            preserve_default=False,
        ),
    ]
