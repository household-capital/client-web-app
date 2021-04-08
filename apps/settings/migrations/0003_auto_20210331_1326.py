# Generated by Django 2.2.4 on 2021-03-31 02:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('enquiry', '0010_auto_20210313_0134'),
        ('settings', '0002_auto_20210129_1204'),
    ]

    operations = [
        migrations.AddField(
            model_name='globalsettings',
            name='autocampaigns_CARE_ABOUT',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='autocampaigns_CARE_ABOUT', to='enquiry.MarketingCampaign'),
        ),
        migrations.AddField(
            model_name='globalsettings',
            name='autocampaigns_FACEBOOK',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='autocampaigns_FACEBOOK', to='enquiry.MarketingCampaign'),
        ),
        migrations.AddField(
            model_name='globalsettings',
            name='autocampaigns_LINKEDIN',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='autocampaigns_LINKEDIN', to='enquiry.MarketingCampaign'),
        ),
        migrations.AddField(
            model_name='globalsettings',
            name='autocampaigns_NATIONAL_SENIORS',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='autocampaigns_NATIONAL_SENIORS', to='enquiry.MarketingCampaign'),
        ),
        migrations.AddField(
            model_name='globalsettings',
            name='autocampaigns_STARTS_AT_60',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='autocampaigns_STARTS_AT_60', to='enquiry.MarketingCampaign'),
        ),
        migrations.AddField(
            model_name='globalsettings',
            name='autocampaigns_YOUR_LIFE_CHOICES',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='autocampaigns_YOUR_LIFE_CHOICES', to='enquiry.MarketingCampaign'),
        ),
    ]