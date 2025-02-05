from django import template
from itertools import groupby as itertools_groupby
from operator import attrgetter

register = template.Library()

@register.filter(name="groupby")
def groupby_filter(queryset, attr):
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

@register.filter(name="remove_dot_prefix")
def remove_dot_prefix_filter(value):
    """
    Remove dot prefix from a string if it exists.
    """
    return value.split(".")[-1]

@register.filter(name="get_nested")
def get_nested_filter(dict, key):
    """
    Get a nested value from a dictionary.
    """
    return dict.get(key)