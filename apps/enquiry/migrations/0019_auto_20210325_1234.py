# Generated by Django 2.2.4 on 2021-03-25 01:34

from django.db import migrations
from config.celery import app
from django.contrib.contenttypes.models import ContentType
from django_comments.models import Comment
from django.utils import timezone


def forwards_func(apps, schema_editor):
    # We get the model from the versioned app registry;
    # if we directly import it, it'll be the wrong version
    Enquiry = apps.get_model("enquiry", "Enquiry")
    db_alias = schema_editor.connection.alias

    enquiries = Enquiry.objects.using(db_alias).all()
    for enquiry in enquiries:
        note = Comment(
            content_type=ContentType.objects.get_for_model(enquiry),
            object_pk=enquiry.id,
            user_name='Unknown',
            user_email='',
            user_url='',
            comment=enquiry.enquiryNotes,
            submit_date=timezone.now(),
            site_id=1,
            is_public=True,
            is_removed=False
        )
        note.save()
        app.send_task('SF_Sync_Enquiry_Notes', kwargs={'enqUID': str(enquiry.enqUID)})


def reverse_func(apps, schema_editor):
    db_alias = schema_editor.connection.alias
    Comment.objects.using(db_alias).all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('enquiry', '0018_enquiry_deleted_on'),
    ]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
