from django import template

register = template.Library()

@register.filter
def as_widget(field, attrs):
    return field.as_widget(attrs=attrs)
