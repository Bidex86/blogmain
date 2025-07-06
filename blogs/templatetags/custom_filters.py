from django import template
import re

register = template.Library()

@register.filter(name='strip_outer_p')
def strip_outer_p(value):
    return re.sub(r'^<p>(.*?)</p>$', r'\1', value.strip(), flags=re.DOTALL)