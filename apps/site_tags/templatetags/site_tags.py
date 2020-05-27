#Python Imports
import os

#Django Imports
from django import template



# CUSTOM TEMPLATE TAGS

def intVal(value):
    if value==None:
        return 0
    return int(value)

def intStr(value):
    if value==None:
        return 0
    return "{:.0f}".format(value)

def intBlank(value):
    if value==None:
        return ""
    return "{:.0f}".format(value)

def strBlank(arg):
    if arg==None or arg=="None":
        return ""
    return arg

def shortUID(arg):
    return str(arg)[-12:]

def filename(value):
    return os.path.basename(value.file.name)

def upto(value, delimiter=','):
    return value.split(delimiter)[0]


def firstName(str):
    if " " not in str:
        return str

    firstname, surname = str.split(" ", 1)
    if len(firstname) > 0:
        return firstname
    else:
        return str

def getDictItem(dictionary, key):
    if dictionary:
        if key in dictionary:
            return dictionary[key]
    return ""

def yesNo(arg):
    if arg is not None:
        if arg == 1:
            return "Yes"
        elif arg == 0:
            return "No"
    return None

def percent(arg):
    if arg is not None:
        return arg * 100
    return None



# REGISTRATION
register = template.Library()
register.filter('intVal', intVal)
register.filter('intStr', intStr)
register.filter('intBlank', intBlank)
register.filter('strBlank', strBlank)
register.filter('shortUID', shortUID)
register.filter('filename', filename)
register.filter('upto', upto)
register.filter('firstName', firstName)
register.filter('getDictItem', getDictItem)
register.filter('yesNo', yesNo)
register.filter('percent', percent)