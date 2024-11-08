# Generated by Django 2.2.4 on 2021-03-17 02:28

from django.db import migrations

#from config.celery import app


def forwards_func(apps, schema_editor):
    # We get the model from the versioned app registry;
    # if we directly import it, it'll be the wrong version
    Case = apps.get_model("case", "Case")
    db_alias = schema_editor.connection.alias

    cases = Case.objects.using(db_alias).all()
    for case in cases:
        case.firstname = case.firstname_1
        case.lastname = case.surname_1
        case.save()
        #app.send_task('Update_SF_Case_Lead', kwargs={'caseUID': str(case.caseUID)})


def reverse_func(apps, schema_editor):
    Case = apps.get_model("case", "Case")
    db_alias = schema_editor.connection.alias

    cases = Case.objects.using(db_alias).all()
    for case in cases:
        case.firstname = ''
        case.lastname = ''
        case.save()
        #app.send_task('Update_SF_Case_Lead', kwargs={'caseUID': str(case.caseUID)})


class Migration(migrations.Migration):

    dependencies = [
        ('case', '0021_auto_20210317_1326'),
    ]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
