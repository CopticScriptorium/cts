from django import template
from itertools import groupby as itertools_groupby
from operator import attrgetter

register = template.Library()

@register.filter
def groupby(queryset, attr):
    """
    Groups a queryset by the given attribute.
    Usage: queryset|group_by_attr:"attribute_name"
    """
    # Ensure attr is a string
    attr = str(attr)
    # Convert queryset to list
    items = list(queryset)
    # Create key function
    key_func = attrgetter(attr)
    # Sort items
    sorted_items = sorted(items, key=key_func)
    # Group items
    grouped = itertools_groupby(sorted_items, key_func)
    return [(key, list(group)) for key, group in grouped]

@register.filter(name="isinstance")
def isinstance_filter(val, instance_type):
    return isinstance(val, eval(instance_type))
