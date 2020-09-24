# Generated by Django 2.2.4 on 2020-04-08 12:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('case', '0026_delete_fundeddata'),
    ]

    operations = [
        migrations.AlterField(
            model_name='case',
            name='referralCompany',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='accounts.Referer'),
        ),
    ]
