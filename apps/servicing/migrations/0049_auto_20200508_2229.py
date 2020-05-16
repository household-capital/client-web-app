# Generated by Django 2.2.4 on 2020-05-08 12:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('servicing', '0048_auto_20200409_2104'),
    ]

    operations = [
        migrations.AlterField(
            model_name='facilityroles',
            name='role',
            field=models.IntegerField(choices=[(0, 'Principal Borrower'), (1, 'Secondary Borrower'), (2, 'Borrower'), (3, 'Nominated Occupant'), (4, 'Permitted Cohabitant'), (5, 'Power of Attorney'), (6, 'Authorised 3rd Party'), (7, 'Distribution Partner Contact'), (8, 'Adviser'), (9, 'Loan Originator'), (10, 'Loan Writer'), (11, 'Valuer'), (12, 'Executor'), (13, 'Solicitor')]),
        ),
    ]
