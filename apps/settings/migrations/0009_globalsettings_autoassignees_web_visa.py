
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('settings', '0008_auto_20210906_1416'),
    ]

    operations = [
        migrations.AddField(
            model_name='globalsettings',
            name='autoassignees_web_visa',
            field=models.ManyToManyField(blank=True, limit_choices_to=models.Q(models.Q(('is_active', True), ('profile__isCreditRep', True), ('profile__calendlyUrl__isnull', False), models.Q(_negated=True, profile__calendlyUrl=''))), related_name='autoassignees_web_visa', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='globalsettings',
            name='autoassignees_web_visa_index',
            field=models.IntegerField(default=0),
        ),
    ]
