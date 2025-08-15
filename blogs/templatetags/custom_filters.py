from django import template
import re
import os
from django.conf import settings

register = template.Library()

@register.filter(name='strip_outer_p')
def strip_outer_p(value):
    return re.sub(r'^<p>(.*?)</p>$', r'\1', value.strip(), flags=re.DOTALL)

register.filter
def exclude_ids(qs, id_list):
    try:
        ids = list(id_list or [])
    except TypeError:
        ids = []
    try:
        return qs.exclude(id__in=ids)
    except Exception:
        # If qs isn't a queryset (or something odd), just return it unchanged
        return qs


