#Django Imports
from django import template


# CUSTOM TEMPLATE TAGS
def intval(value):
    return int(value)

def intStr(value):
    if value==None:
        return 0
    return "{:.0f}".format(value)

# REGISTRATION
register = template.Library()
register.filter('intval', intval)
register.filter('intStr', intStr)