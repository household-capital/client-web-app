from django import template

# CUSTOM TEMPLATE FILTER
register = template.Library()


def intval(value):
    return int(value)

register.filter('intval', intval)