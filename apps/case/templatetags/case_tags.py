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

def bspkReferrer(arg):
    refList=['superannuation-and-retirement','retirement-planning','reverse-mortgages','aged-care-financing',
             'centrelink-pension-information','equity-mortgage-release','calculator']
    if arg==None:
        return ""

    for term in refList:
        if term in arg:
            return term
    return arg

def filename(value):
    return os.path.basename(value.file.name)

def upto(value, delimiter=','):
    return value.split(delimiter)[0]



# REGISTRATION
register = template.Library()
register.filter('intVal', intVal)
register.filter('intStr', intStr)
register.filter('intBlank', intBlank)
register.filter('strBlank', strBlank)
register.filter('bspkReferrer', bspkReferrer)
register.filter('shortUID', shortUID)
register.filter('filename', filename)
register.filter('upto', upto)