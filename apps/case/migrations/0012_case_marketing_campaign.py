# Generated by Django 2.2.4 on 2021-02-16 23:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('enquiry', '0007_auto_20210217_1030'),
        ('case', '0011_auto_20210205_1312'),
    ]

    operations = [
        migrations.AddField(
            model_name='case',
            name='marketing_campaign',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='enquiry.MarketingCampaign'),
        ),
    ]
