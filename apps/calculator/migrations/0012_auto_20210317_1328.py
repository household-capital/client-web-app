# Generated by Django 2.2.4 on 2021-03-17 02:28

from django.db import migrations
from apps.lib.site_Utilities import split_name


def calc_forwards_func(apps, schema_editor):
    # We get the model from the versioned app registry;
    # if we directly import it, it'll be the wrong version
    WebCalculator = apps.get_model("calculator", "WebCalculator")
    db_alias = schema_editor.connection.alias

    calcs = WebCalculator.objects.using(db_alias).all()
    for calc in calcs:
        calc.firstname, calc.lastname = split_name(calc.name)
        calc.save()


def calc_reverse_func(apps, schema_editor):
    WebCalculator = apps.get_model("calculator", "WebCalculator")
    db_alias = schema_editor.connection.alias

    calcs = WebCalculator.objects.using(db_alias).all()
    for calc in calcs:
        calc.firstname, calc.lastname = None, None
        calc.save()


def contact_forwards_func(apps, schema_editor):
    # We get the model from the versioned app registry;
    # if we directly import it, it'll be the wrong version
    WebContact = apps.get_model("calculator", "WebContact")
    db_alias = schema_editor.connection.alias

    contacts = WebContact.objects.using(db_alias).all()
    for contact in contacts:
        contact.firstname, contact.lastname = split_name(contact.name)
        contact.save()


def contact_reverse_func(apps, schema_editor):
    WebContact = apps.get_model("calculator", "WebContact")
    db_alias = schema_editor.connection.alias

    contacts = WebContact.objects.using(db_alias).all()
    for contact in contacts:
        contact.firstname, contact.lastname = None, None
        contact.save()


class Migration(migrations.Migration):

    dependencies = [
        ('calculator', '0011_auto_20210317_1326'),
    ]

    operations = [
        migrations.RunPython(calc_forwards_func, calc_reverse_func),
        migrations.RunPython(contact_forwards_func, contact_reverse_func),
    ]