from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('calculator', '0016_auto_20210621_1706'),
    ]

    operations = [
        migrations.AddField(
            model_name='webcalculator',
            name='utm_source',
            field=models.CharField(max_length=256, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='webcontact',
            name='utm_medium',
            field=models.CharField(max_length=256, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='webcontact',
            name='utm_campaign',
            field=models.CharField(max_length=256, null=True, blank=True),
        ),
    ]
