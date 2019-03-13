#Django Imports
from django import template


# CUSTOM TEMPLATE TAGS
def intval(value):
    return int(value)

# REGISTRATION
register = template.Library()
register.filter('intval', intval)