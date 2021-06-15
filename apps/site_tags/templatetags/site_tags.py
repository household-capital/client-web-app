#Python Imports
import os

#Django Imports
from django import template

from django_comments.templatetags.comments import RenderCommentListNode
# CUSTOM TEMPLATE TAGS

def modelMethod(obj, method_name, *args):
    method = getattr(obj, method_name)
    return method(*args)

# CUSTOM FILTERS

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
    try:
        return os.path.basename(value.file.name)
    except:
        return None

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

def roundNum(arg, ndigits):
    n = int(ndigits)
    return round(arg,n)


def active_enquiries(enquries):
    return enquries.filter(deleted_on__isnull=True).order_by('-timestamp') if enquries else []


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
register.filter('roundNum', roundNum)
register.filter('active_enquiries', active_enquiries)
register.simple_tag(modelMethod, name='modelMethod')



class CustomerRenderListNode(RenderCommentListNode):
    def get_queryset(self, context): 
        return super(CustomerRenderListNode, self).get_queryset(context).order_by('-submit_date')


@register.tag 
def render_comment_list_by_latest(parser, token):
    return CustomerRenderListNode.handle_token(parser, token)